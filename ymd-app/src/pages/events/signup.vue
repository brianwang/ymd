<template>
  <view class="page ymd-page">
    <view class="card">
      <text class="title">活动报名</text>
      <text class="sub">请填写报名信息</text>

      <view class="form">
        <view class="field">
          <text class="label">姓名</text>
          <input class="input" v-model="name" type="text" placeholder="请输入姓名" />
        </view>
        <view class="field">
          <text class="label">手机号</text>
          <input class="input" v-model="phone" type="number" placeholder="请输入手机号" />
        </view>
        <view class="field">
          <text class="label">备注</text>
          <input class="input" v-model="remark" type="text" placeholder="可填写特殊需求/备注" />
        </view>

        <button class="btn ymd-btn" :loading="loading" @click="submit">提交报名</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { request } from '@/utils/request';
import { useUserStore } from '@/store/user';

const userStore = useUserStore();

const eventId = ref<string>('');
const name = ref('');
const phone = ref('');
const remark = ref('');
const loading = ref(false);

onLoad((query) => {
  eventId.value = (query?.id as string) || '';
});

const submit = async () => {
  if (!userStore.token) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    uni.navigateTo({ url: '/pages/auth/login' });
    return;
  }
  const n = name.value.trim();
  const p = phone.value.trim();
  const r = remark.value.trim();
  if (!n) {
    uni.showToast({ title: '请输入姓名', icon: 'none' });
    return;
  }
  if (!p) {
    uni.showToast({ title: '请输入手机号', icon: 'none' });
    return;
  }
  if (!eventId.value) {
    uni.showToast({ title: '活动参数错误', icon: 'none' });
    return;
  }

  loading.value = true;
  try {
    await request({
      url: `/events/${eventId.value}/registrations`,
      method: 'POST',
      data: { name: n, phone: p, remark: r || undefined },
    });
    uni.showToast({ title: '报名成功', icon: 'success' });
    setTimeout(() => {
      uni.navigateBack();
    }, 400);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '报名失败', icon: 'none' });
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped lang="scss">
.page { padding: $ymd-space-3 $ymd-space-3 28px; }
.card { background: $ymd-color-card; border: 1px solid $ymd-color-line; border-radius: $ymd-radius-lg; padding: 16px; box-shadow: $ymd-shadow-xs; }
.title { font-size: 18px; font-weight: 800; color: $ymd-color-text; }
.sub { margin-top: 6px; font-size: 12px; color: $ymd-color-muted; }
.form { margin-top: 14px; display: flex; flex-direction: column; gap: 12px; }
.field { display: flex; flex-direction: column; gap: 8px; }
.label { font-size: 12px; color: $ymd-color-muted; }
.input { background: $ymd-color-soft; border-radius: $ymd-radius-md; padding: 12px; font-size: 14px; }
.btn { margin-top: 6px; border-radius: $ymd-radius-md; height: 44px; line-height: 44px; font-weight: 700; }
</style>

