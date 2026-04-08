<template>
  <view class="container">
    <view class="user-info">
      <view class="avatar-wrap">
        <image class="avatar" :src="userStore.userInfo?.avatar_url || '/static/logo.png'" mode="aspectFill" />
      </view>
      <view class="info-text" v-if="userStore.token">
        <text class="nickname">{{ userStore.userInfo?.nickname || '数字游民' }}</text>
        <text class="points">游牧积分: {{ userStore.userInfo?.points || 0 }}</text>
      </view>
      <view class="info-text" v-else @click="handleLogin">
        <text class="nickname">点击登录/注册</text>
      </view>
    </view>
    <view class="menu-list">
      <view class="menu-item">
        <text>我的活动</text>
      </view>
      <view class="menu-item">
        <text>我的订单</text>
      </view>
      <view class="menu-item" @click="handleEditProfile">
        <text>编辑个人资料</text>
      </view>
      <view class="menu-item" @click="handlePoints">
        <text>积分中心</text>
      </view>
      <view class="menu-item" @click="handleInvitePoster">
        <text>邀请海报</text>
      </view>
      <view class="menu-item" v-if="userStore.token" @click="handleLogout">
        <text class="logout">退出登录</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useUserStore } from '../../store/user';
import { request } from '../../utils/request';
import { onShow } from '@dcloudio/uni-app';

const userStore = useUserStore();

const handleLogin = () => {
  uni.login({
    provider: 'weixin',
    success: async (res) => {
      try {
        const inviterIdRaw = uni.getStorageSync('inviter_id');
        const inviter_id = inviterIdRaw ? Number(inviterIdRaw) : undefined;
        const data: any = await request({
          url: '/auth/wx-login',
          method: 'POST',
          data: { code: res.code, inviter_id }
        });
        userStore.setToken(data.access_token);
        uni.removeStorageSync('inviter_id');
        
        const userInfoData: any = await request({
          url: '/users/me',
          method: 'GET'
        });
        userStore.setUserInfo(userInfoData);
        uni.showToast({ title: '登录成功', icon: 'success' });
      } catch (err) {
        console.error(err);
      }
    }
  });
};

const handleLogout = () => {
  userStore.logout();
};

const handleEditProfile = () => {
  if (!userStore.token) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    return;
  }
  uni.showToast({ title: '编辑资料开发中', icon: 'none' });
};

const handlePoints = () => {
  if (!userStore.token) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    return;
  }
  uni.navigateTo({ url: '/pages/points/index' });
};

const handleInvitePoster = () => {
  if (!userStore.token) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    return;
  }
  uni.navigateTo({ url: '/pages/invite-poster/index' });
};

onShow(() => {
  if (userStore.token) {
    request({
      url: '/users/me',
      method: 'GET'
    }).then(res => {
      userStore.setUserInfo(res);
    }).catch(() => {});
  }
});
</script>

<style scoped>
.container { padding: 20px; }
.user-info { display: flex; align-items: center; margin-bottom: 40px; }
.avatar { width: 80px; height: 80px; border-radius: 40px; margin-right: 20px; }
.info-text { display: flex; flex-direction: column; }
.nickname { font-size: 20px; font-weight: bold; margin-bottom: 5px; }
.points { font-size: 14px; color: #666; }
.menu-item { padding: 15px 0; border-bottom: 1px solid #eee; }
.logout { color: red; }
</style>
