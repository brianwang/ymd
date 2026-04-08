<template>
  <view class="page ymd-page">
    <view class="card">
      <text class="title">绑定邮箱</text>
      <text class="sub">为当前账号设置邮箱与密码</text>

      <view class="form">
        <view class="field">
          <text class="label">邮箱</text>
          <input class="input" v-model="email" type="text" placeholder="name@example.com" />
        </view>
        <view class="field">
          <text class="label">设置密码</text>
          <input class="input" v-model="password" type="password" placeholder="至少 6 位" />
        </view>
        <view class="field">
          <text class="label">确认密码</text>
          <input class="input" v-model="password2" type="password" placeholder="再次输入密码" />
        </view>

        <button class="btn ymd-btn" :loading="loading" @click="submit">绑定</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app';
import { ref } from 'vue';
import { request } from '../../utils/request';
import { useUserStore } from '../../store/user';

const userStore = useUserStore();

const email = ref('');
const password = ref('');
const password2 = ref('');
const loading = ref(false);

onShow(() => {
  if (!userStore.token) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    setTimeout(() => uni.navigateTo({ url: '/pages/auth/login' }), 400);
    return;
  }
  email.value = userStore.userInfo?.email || '';
});

const submit = async () => {
  const e = email.value.trim();
  if (!e) {
    uni.showToast({ title: '请输入邮箱', icon: 'none' });
    return;
  }
  if (!password.value || password.value.length < 6) {
    uni.showToast({ title: '密码至少 6 位', icon: 'none' });
    return;
  }
  if (password.value !== password2.value) {
    uni.showToast({ title: '两次密码不一致', icon: 'none' });
    return;
  }

  loading.value = true;
  try {
    const user: any = await request({
      url: '/users/bind-email',
      method: 'POST',
      data: { email: e, password: password.value },
    });
    userStore.setUserInfo(user);
    uni.showToast({ title: '绑定成功', icon: 'success' });
    setTimeout(() => {
      uni.switchTab({ url: '/pages/profile/index' });
    }, 400);
  } catch (err) {
    console.error(err);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped lang="scss">
.page { padding: 18px $ymd-space-3 28px; }
.card { background: $ymd-color-card; border: 1px solid $ymd-color-line; border-radius: $ymd-radius-lg; padding: 16px; box-shadow: $ymd-shadow-xs; }
.title { font-size: 18px; font-weight: 900; color: $ymd-color-text; }
.sub { margin-top: 6px; font-size: $ymd-font-sm; color: $ymd-color-muted; }
.form { margin-top: 14px; display: flex; flex-direction: column; gap: 12px; }
.field { display: flex; flex-direction: column; gap: 8px; }
.label { font-size: $ymd-font-sm; color: $ymd-color-text; font-weight: 700; }
.input { background: rgba(15, 23, 42, 0.04); border-radius: $ymd-radius-md; padding: 12px; font-size: 14px; }
.btn { border-radius: $ymd-radius-md; margin-top: 4px; height: 44px; line-height: 44px; font-weight: 800; }
</style>
