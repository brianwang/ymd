<template>
  <view class="ymd-page">
    <AppBar title="积分中心" back action-text="邀请" @action="goInvitePoster" />
    <view class="ymd-container ymd-page-inner">
      <Card class="balance-card">
        <view class="balance-top">
          <text class="balance-label">当前积分</text>
          <text class="nickname">{{ nickname }}</text>
        </view>
        <view class="balance">
          <text class="balance-num">{{ points }}</text>
          <text class="balance-unit">分</text>
        </view>
      </Card>

      <view class="ymd-section">
        <SectionHeader title="任务中心" />
        <Card class="task-card">
          <view class="task-row">
            <view class="task-left">
              <text class="task-title">每日签到</text>
              <text class="task-sub">+{{ taskSignInDelta }} 积分</text>
            </view>
            <button class="task-btn ymd-btn" size="mini" :disabled="loading || taskSignInAwarded" @click="signIn">
              {{ taskSignInAwarded ? '已完成' : '去签到' }}
            </button>
          </view>
          <Divider inset />
          <view class="task-row">
            <view class="task-left">
              <text class="task-title">发布首帖</text>
              <text class="task-sub">+{{ taskFirstPostDelta }} 积分</text>
            </view>
            <button class="task-btn ymd-btn ghost" size="mini" :disabled="loading || taskFirstPostAwarded" @click="firstPost">
              {{ taskFirstPostAwarded ? '已完成' : '领取奖励' }}
            </button>
          </view>
          <Divider inset />
          <view class="task-row">
            <view class="task-left">
              <text class="task-title">邀请好友</text>
              <text class="task-sub">生成邀请海报分享给好友</text>
            </view>
            <button class="task-btn ymd-btn ghost" size="mini" :disabled="loading" @click="goInvitePoster">去邀请</button>
          </view>
        </Card>
      </view>

      <view class="ymd-section">
        <SectionHeader title="积分流水" />
        <Card class="list">
          <EmptyState
            v-if="!loading && ledger.length === 0"
            image="/static/empty/empty-list-v2.png"
            title="暂无流水"
            desc="完成任务后会在这里看到记录"
          />
          <view v-else>
            <view class="item" v-for="it in ledger" :key="it.id">
              <view class="left">
                <text class="event">{{ eventLabel(it.event_type) }}</text>
                <text class="time">{{ formatTime(it.created_at) }}</text>
              </view>
              <text class="delta" :class="{ plus: it.delta > 0, minus: it.delta < 0 }">
                {{ it.delta > 0 ? `+${it.delta}` : `${it.delta}` }}
              </text>
            </view>
            <view class="footer" v-if="ledger.length > 0">
              <text v-if="loading">加载中...</text>
              <text v-else-if="finished">没有更多了</text>
              <text v-else>上拉加载更多</text>
            </view>
          </view>
        </Card>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app';
import { request } from '../../utils/request';
import { useUserStore } from '../../store/user';
import AppBar from '@/components/ui/AppBar.vue';
import Card from '@/components/ui/Card.vue';
import Divider from '@/components/ui/Divider.vue';
import SectionHeader from '@/components/ui/SectionHeader.vue';
import EmptyState from '@/components/ui/EmptyState.vue';

type LedgerItem = {
  id: number;
  event_type: string;
  biz_key: string;
  delta: number;
  created_at: string;
};

type TaskItem = {
  key: string;
  title: string;
  awarded: boolean;
  delta: number;
};

const userStore = useUserStore();

const points = ref(0);
const nickname = ref('数字游民');
const ledger = ref<LedgerItem[]>([]);
const tasks = ref<TaskItem[]>([]);
const loading = ref(false);
const finished = ref(false);
const limit = 20;
const offset = ref(0);

const eventLabel = (eventType: string) => {
  const map: Record<string, string> = {
    sign_in: '每日签到',
    first_post: '发布首帖',
    post_reward: '发帖奖励',
    comment_reward: '评论奖励',
    invite_reward_inviter: '邀请奖励(邀请人)',
    invite_reward_invitee: '邀请奖励(被邀请)',
    admin: '系统调整',
  };
  return map[eventType] || eventType;
};

const formatTime = (iso: string) => {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const pad = (n: number) => `${n}`.padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

const loadUser = async () => {
  const me: any = await request({ url: '/users/me', method: 'GET' });
  points.value = me?.points || 0;
  nickname.value = me?.nickname || '数字游民';
  userStore.setUserInfo(me);
};

const loadLedger = async (reset = false) => {
  if (loading.value) return;
  if (!reset && finished.value) return;
  loading.value = true;
  try {
    if (reset) {
      offset.value = 0;
      finished.value = false;
    }
    const res: any = await request({
      url: '/points/ledger',
      method: 'GET',
      data: { limit, offset: offset.value },
    });
    const arr: LedgerItem[] = Array.isArray(res) ? res : (res?.items || []);
    ledger.value = reset ? arr : [...ledger.value, ...arr];
    offset.value += arr.length;
    if (arr.length < limit) finished.value = true;
  } finally {
    loading.value = false;
  }
};

const loadTasks = async () => {
  const res: any = await request({ url: '/points/tasks', method: 'GET' });
  tasks.value = Array.isArray(res) ? res : [];
};

const taskSignInAwarded = computed(() => tasks.value.find(t => t.key === 'sign_in')?.awarded ?? false);
const taskSignInDelta = computed(() => tasks.value.find(t => t.key === 'sign_in')?.delta ?? 0);
const taskFirstPostAwarded = computed(() => tasks.value.find(t => t.key === 'first_post')?.awarded ?? false);
const taskFirstPostDelta = computed(() => tasks.value.find(t => t.key === 'first_post')?.delta ?? 0);

const signIn = async () => {
  if (!userStore.token) return;
  loading.value = true;
  try {
    const res: any = await request({ url: '/points/sign-in', method: 'POST' });
    points.value = res?.points ?? points.value;
    await Promise.all([loadLedger(true), loadTasks()]);
    uni.showToast({ title: res?.awarded ? `+${res?.delta || 0} 积分` : '今日已签到', icon: 'none' });
  } finally {
    loading.value = false;
  }
};

const firstPost = async () => {
  if (!userStore.token) return;
  loading.value = true;
  try {
    const res: any = await request({ url: '/points/first-post', method: 'POST' });
    points.value = res?.points ?? points.value;
    await Promise.all([loadLedger(true), loadTasks()]);
    uni.showToast({ title: res?.awarded ? `+${res?.delta || 0} 积分` : '已领取过', icon: 'none' });
  } finally {
    loading.value = false;
  }
};

const goInvitePoster = () => {
  uni.navigateTo({ url: '/pages/invite-poster/index' });
};

const refreshAll = async () => {
  if (!userStore.token) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    uni.switchTab({ url: '/pages/profile/index' });
    return;
  }
  await Promise.all([loadUser(), loadLedger(true), loadTasks()]);
};

onShow(() => {
  refreshAll();
});

onPullDownRefresh(async () => {
  await refreshAll();
  uni.stopPullDownRefresh();
});

onReachBottom(() => {
  loadLedger(false);
});
</script>

<style scoped lang="scss">
.balance-card { padding: 18px; box-shadow: $ymd-v2-shadow-sm; background: linear-gradient(180deg, rgba(109, 94, 252, 0.10), rgba(255,255,255, 0.92)); }
.balance-top { display: flex; justify-content: space-between; align-items: center; }
.balance-label { font-size: $ymd-v2-font-sm; color: $ymd-v2-color-muted; font-weight: 800; }
.nickname { font-size: $ymd-v2-font-md; color: $ymd-v2-color-text; font-weight: 900; }
.balance { margin-top: 14px; display: flex; align-items: baseline; }
.balance-num { font-size: 46px; font-weight: 950; color: $ymd-v2-color-text; line-height: 1; }
.balance-unit { margin-left: 6px; font-size: $ymd-v2-font-sm; color: $ymd-v2-color-muted; }

.task-card { overflow: hidden; }
.task-row { display: flex; align-items: center; justify-content: space-between; padding: 14px 14px; }
.task-left { display: flex; flex-direction: column; }
.task-title { font-size: 15px; color: $ymd-v2-color-text; font-weight: 900; }
.task-sub { margin-top: 6px; font-size: $ymd-v2-font-sm; color: $ymd-v2-color-muted; }
.task-btn { font-size: 12px; padding: 0 14px; height: 34px; line-height: 34px; }
.list { overflow: hidden; padding: 14px; }
.item { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid $ymd-v2-color-line; }
.item:last-child { border-bottom: none; }
.left { display: flex; flex-direction: column; }
.event { font-size: 15px; color: $ymd-v2-color-text; font-weight: 900; }
.time { margin-top: 6px; font-size: $ymd-v2-font-sm; color: $ymd-v2-color-muted; }
.delta { font-size: 16px; font-weight: 600; }
.plus { color: $ymd-v2-color-success; font-weight: 900; }
.minus { color: $ymd-v2-color-danger; font-weight: 900; }
.footer { padding: 12px 0 0; text-align: center; color: $ymd-v2-color-muted; font-size: 12px; }
</style>
