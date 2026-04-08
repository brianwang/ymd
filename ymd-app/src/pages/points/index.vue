<template>
  <view class="container">
    <view class="card">
      <view class="card-top">
        <text class="title">积分余额</text>
        <text class="nickname">{{ nickname }}</text>
      </view>
      <view class="balance">
        <text class="balance-num">{{ points }}</text>
        <text class="balance-unit">分</text>
      </view>
    </view>

    <view class="section-title">任务中心</view>
    <view class="task-card">
      <view class="task-row">
        <view class="task-left">
          <text class="task-title">每日签到</text>
          <text class="task-sub">+{{ taskSignInDelta }} 积分</text>
        </view>
        <button class="task-btn primary" size="mini" :disabled="loading || taskSignInAwarded" @click="signIn">
          {{ taskSignInAwarded ? '已完成' : '去签到' }}
        </button>
      </view>
      <view class="task-row">
        <view class="task-left">
          <text class="task-title">发布首帖</text>
          <text class="task-sub">+{{ taskFirstPostDelta }} 积分</text>
        </view>
        <button class="task-btn" size="mini" :disabled="loading || taskFirstPostAwarded" @click="firstPost">
          {{ taskFirstPostAwarded ? '已完成' : '领取奖励' }}
        </button>
      </view>
      <view class="task-row">
        <view class="task-left">
          <text class="task-title">邀请好友</text>
          <text class="task-sub">生成邀请海报分享给好友</text>
        </view>
        <button class="task-btn" size="mini" :disabled="loading" @click="goInvitePoster">去邀请</button>
      </view>
    </view>

    <view class="section-title">积分流水</view>
    <view class="list">
      <view class="item" v-for="it in ledger" :key="it.id">
        <view class="left">
          <text class="event">{{ eventLabel(it.event_type) }}</text>
          <text class="time">{{ formatTime(it.created_at) }}</text>
        </view>
        <text class="delta" :class="{ plus: it.delta > 0, minus: it.delta < 0 }">
          {{ it.delta > 0 ? `+${it.delta}` : `${it.delta}` }}
        </text>
      </view>
      <view class="empty" v-if="!loading && ledger.length === 0">
        <text>暂无流水</text>
      </view>
      <view class="footer" v-if="ledger.length > 0">
        <text v-if="loading">加载中...</text>
        <text v-else-if="finished">没有更多了</text>
        <text v-else>上拉加载更多</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app';
import { request } from '../../utils/request';
import { useUserStore } from '../../store/user';

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

<style scoped>
.container { padding: 16px; }
.card { background: #fff; border-radius: 12px; padding: 18px; box-shadow: 0 6px 18px rgba(0,0,0,0.06); }
.card-top { display: flex; justify-content: space-between; align-items: center; }
.title { font-size: 14px; color: #666; }
.nickname { font-size: 14px; color: #333; }
.balance { margin-top: 14px; display: flex; align-items: baseline; }
.balance-num { font-size: 40px; font-weight: 700; color: #111; line-height: 1; }
.balance-unit { margin-left: 6px; font-size: 14px; color: #666; }
.task-card { background: #fff; border-radius: 12px; overflow: hidden; }
.task-row { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; border-bottom: 1px solid #f2f2f2; }
.task-row:last-child { border-bottom: none; }
.task-left { display: flex; flex-direction: column; }
.task-title { font-size: 15px; color: #111; }
.task-sub { margin-top: 6px; font-size: 12px; color: #999; }
.task-btn { font-size: 12px; }
.primary { background: #007AFF; color: #fff; }
.section-title { margin-top: 18px; margin-bottom: 10px; font-size: 14px; color: #666; }
.list { background: #fff; border-radius: 12px; overflow: hidden; }
.item { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; border-bottom: 1px solid #f2f2f2; }
.item:last-child { border-bottom: none; }
.left { display: flex; flex-direction: column; }
.event { font-size: 15px; color: #111; }
.time { margin-top: 6px; font-size: 12px; color: #999; }
.delta { font-size: 16px; font-weight: 600; }
.plus { color: #16a34a; }
.minus { color: #ef4444; }
.empty { padding: 24px 0; text-align: center; color: #999; }
.footer { padding: 12px 0; text-align: center; color: #999; font-size: 12px; }
</style>
