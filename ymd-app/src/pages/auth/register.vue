<template>
  <view class="page ymd-page">
    <view class="card">
      <text class="title">邮箱注册</text>
      <text class="sub">注册后自动登录</text>

      <view class="form">
        <view class="field">
          <text class="label">邮箱</text>
          <input class="input" v-model="email" type="text" placeholder="name@example.com" />
        </view>
        <view class="field">
          <text class="label">密码</text>
          <input class="input" v-model="password" type="password" placeholder="至少 6 位" />
        </view>
        <view class="field">
          <text class="label">确认密码</text>
          <input class="input" v-model="password2" type="password" placeholder="再次输入密码" />
        </view>

        <button class="btn ymd-btn" :loading="loading" @click="submit">注册</button>

        <view class="link-row">
          <text class="link" @click="goLogin">已有账号？去登录</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { request } from '../../utils/request';
import { useUserStore } from '../../store/user';

const userStore = useUserStore();

const email = ref('');
const password = ref('');
const password2 = ref('');
const loading = ref(false);

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
    const data: any = await request({
      url: '/auth/register',
      method: 'POST',
      data: { email: e, password: password.value },
    });
    userStore.setToken(data.access_token);
    const me: any = await request({ url: '/users/me', method: 'GET' });
    userStore.setUserInfo(me);
    uni.showToast({ title: '注册成功', icon: 'success' });
    setTimeout(() => {
      uni.switchTab({ url: '/pages/profile/index' });
    }, 400);
  } catch (err) {
    console.error(err);
  } finally {
    loading.value = false;
  }
};

const goLogin = () => {
  uni.redirectTo({ url: '/pages/auth/login' });
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
.link-row { display: flex; justify-content: center; padding-top: 4px; }
.link { font-size: 12px; color: $ymd-color-primary; font-weight: 700; }
</style>
