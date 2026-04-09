<template>
  <view class="ymd-page">
    <AppBar title="我的活动" back action-text="刷新" @action="reload" />
    <view class="ymd-container ymd-page-inner page">
      <EmptyState
        v-if="errorText"
        :image="TESTDATA_IMAGES.emptyErrorV2"
        title="加载失败"
        :desc="errorText"
        action-text="重试"
        @action="reload"
      />
      <EmptyState
        v-else-if="loading"
        :image="TESTDATA_IMAGES.emptyListV2"
        title="加载中..."
      />
      <EmptyState
        v-else-if="items.length === 0"
        :image="TESTDATA_IMAGES.emptyListV2"
        title="暂无报名记录"
        desc="去看看有哪些活动正在发生"
        action-text="去看看活动"
        @action="goExplore"
      />

      <view v-else class="list">
        <Card
          v-for="it in items"
          :key="it.registration_id"
          class="item"
          pressable
          @click="goDetail(it.event.id)"
        >
          <image class="cover" :src="it.event.cover_url || TESTDATA_IMAGES.coverEventsV2" mode="aspectFill" />
          <view class="body">
            <text class="it-title">{{ it.event.title }}</text>
            <text class="it-sub">{{ (it.event.city || '未知城市') + ' · ' + formatTime(it.event.start_at) }}</text>
            <view class="row">
              <text class="pill" :class="it.status === 'registered' ? 'on' : 'off'">
                {{ it.status === 'registered' ? '已报名' : '已取消' }}
              </text>
              <button
                v-if="it.status === 'registered'"
                class="act ymd-btn ghost"
                size="mini"
                @click.stop="cancel(it.event.id)"
              >
                取消报名
              </button>
            </view>
          </view>
        </Card>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app';
import { ref } from 'vue';
import { request } from '@/utils/request';
import { useUserStore } from '@/store/user';
import AppBar from '@/components/ui/AppBar.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import Card from '@/components/ui/Card.vue';
import { TESTDATA_IMAGES } from '@/constants/testdataImages';

const userStore = useUserStore();

type RegistrationStatus = 'registered' | 'canceled' | 'none' | string;
type EventListItem = {
  id: number;
  title: string;
  city?: string | null;
  start_at: string;
  cover_url?: string | null;
};
type MyRegistrationItem = {
  registration_id: number;
  status: RegistrationStatus;
  created_at: string;
  canceled_at?: string | null;
  event: EventListItem;
};

const items = ref<MyRegistrationItem[]>([]);
const loading = ref(false);
const errorText = ref('');

const formatTime = (raw: string) => {
  const dt = new Date(raw);
  if (Number.isNaN(dt.getTime())) return raw;
  return dt.toLocaleString();
};

const reload = async () => {
  if (!userStore.token) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    uni.navigateTo({ url: '/pages/auth/login' });
    return;
  }
  loading.value = true;
  errorText.value = '';
  try {
    items.value = (await request({ url: '/users/me/event-registrations', method: 'GET' })) as MyRegistrationItem[];
  } catch (e: any) {
    errorText.value = e?.message || '加载失败';
    items.value = [];
  } finally {
    loading.value = false;
  }
};

const goDetail = (id: number) => {
  uni.navigateTo({ url: `/pages/events/detail?id=${id}` });
};

const goExplore = () => {
  uni.switchTab({ url: '/pages/events/index' });
};

const cancel = (eventId: number) => {
  uni.showModal({
    title: '确认取消报名',
    content: '取消后可再次报名（若名额允许）',
    confirmText: '取消报名',
    cancelText: '我再想想',
    success: async (r) => {
      if (!r.confirm) return;
      try {
        await request({ url: `/events/${eventId}/registrations/me`, method: 'DELETE' });
        uni.showToast({ title: '已取消', icon: 'success' });
        await reload();
      } catch (e: any) {
        uni.showToast({ title: e?.data?.detail || e?.message || '取消失败', icon: 'none' });
      }
    },
  });
};

onShow(reload);
onPullDownRefresh(async () => {
  await reload();
  uni.stopPullDownRefresh();
});
</script>

<style scoped lang="scss">
.page { padding-bottom: 28px; }
.list { display: flex; flex-direction: column; gap: 10px; }
.item { display: flex; gap: 12px; padding: 12px; }
.cover { width: 92px; height: 72px; border-radius: $ymd-v2-radius-md; background: rgba(15, 23, 42, 0.04); }
.body { flex: 1; display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.it-title { font-size: 15px; font-weight: 900; color: $ymd-v2-color-text; }
.it-sub { font-size: 12px; color: $ymd-v2-color-muted; }
.row { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }
.muted { font-size: 12px; color: $ymd-v2-color-muted; }
.pill { padding: 3px 8px; border-radius: 999px; font-size: 12px; border: 1px solid $ymd-v2-color-line; }
.pill.on { background: rgba(18, 200, 192, .12); border-color: rgba(18, 200, 192, .4); color: $ymd-v2-color-brand; font-weight: 800; }
.pill.off { background: rgba(239, 68, 68, .10); border-color: rgba(239, 68, 68, .35); color: $uni-color-error; font-weight: 700; }
.act { height: 30px; line-height: 30px; padding: 0 12px; border-radius: $ymd-radius-md; font-weight: 800; }
</style>
