<template>
  <view class="page ymd-page">
    <view class="card">
      <view class="empty">
        <image class="empty-img" :src="TESTDATA_IMAGES.emptyListV2" mode="aspectFit" />
        <text class="empty-title">暂无订单</text>
        <text class="empty-sub">订单体系正在完善中，先去看看活动和共居吧</text>
      </view>
      <view class="actions">
        <button class="btn ymd-btn" @click="goEvents">去看看活动</button>
        <button class="btn ymd-btn ghost" @click="goColiving">去看看共居</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app';
import { useUserStore } from '@/store/user';
import { TESTDATA_IMAGES } from '@/constants/testdataImages';

const userStore = useUserStore();

onShow(() => {
  if (!userStore.token) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    uni.navigateTo({ url: '/pages/auth/login' });
  }
});

const goEvents = () => {
  uni.switchTab({ url: '/pages/events/index' });
};

const goColiving = () => {
  uni.switchTab({ url: '/pages/coliving/index' });
};
</script>

<style scoped lang="scss">
.page { padding: $ymd-space-3 $ymd-space-3 28px; }
.card { background: $ymd-color-card; border: 1px solid $ymd-color-line; border-radius: $ymd-radius-lg; box-shadow: $ymd-shadow-xs; padding: 18px 14px; }
.empty { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 10px 0 6px; }
.empty-img { width: 160px; height: 120px; opacity: .92; }
.empty-title { font-size: 16px; font-weight: 900; color: $ymd-color-text; }
.empty-sub { font-size: 12px; color: $ymd-color-muted; text-align: center; line-height: 18px; }
.actions { margin-top: 14px; display: flex; flex-direction: column; gap: 10px; }
.btn { border-radius: $ymd-radius-md; height: 44px; line-height: 44px; font-weight: 800; }
</style>
