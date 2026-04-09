<template>
  <view class="ymd-page">
    <AppBar title="我的" />
    <view class="ymd-container ymd-page-inner">
      <Card class="profile" pressable @click="goMyProfile">
        <view class="profile-main">
          <image class="avatar" :src="avatarSrc" mode="aspectFill" />
          <view class="info">
            <text class="nickname">{{ nicknameText }}</text>
            <text class="meta">{{ metaText }}</text>
          </view>
        </view>
        <view class="badges" v-if="userStore.token">
          <view class="badge">
            <text class="badge-k">积分</text>
            <text class="badge-v">{{ userStore.userInfo?.points || 0 }}</text>
          </view>
          <view class="badge" v-if="userStore.userInfo?.email">
            <text class="badge-k">邮箱</text>
            <text class="badge-v">{{ userStore.userInfo?.email }}</text>
          </view>
          <view class="badge warn" v-else>
            <text class="badge-k">邮箱</text>
            <text class="badge-v">未绑定</text>
          </view>
        </view>
      </Card>

      <Card class="account" v-if="!userStore.token">
        <view class="account-hint">
          <text class="hint-title">登录后体验完整功能</text>
          <text class="hint-sub">同步资料、积分、报名记录</text>
        </view>
        <button class="account-btn ymd-btn" @click="handleWxLogin">微信一键登录</button>
        <view class="account-row">
          <button class="account-btn ymd-btn ghost" @click="goEmailLogin">邮箱登录</button>
          <button class="account-btn ymd-btn ghost" @click="goEmailRegister">邮箱注册</button>
        </view>
      </Card>
      <Card class="account" v-else-if="!userStore.userInfo?.email">
        <view class="account-hint">
          <text class="hint-title">建议绑定邮箱</text>
          <text class="hint-sub">用于跨设备登录与找回账号</text>
        </view>
        <button class="account-btn ymd-btn" @click="goBindEmail">去绑定</button>
      </Card>

      <view class="ymd-section">
        <SectionHeader title="功能入口" />
        <Card class="menu">
          <view class="menu-item" hover-class="tap" hover-stay-time="70" @click="goMyEvents">
            <text class="menu-text">我的活动</text>
            <text class="arrow">›</text>
          </view>
          <Divider inset />
          <view class="menu-item" hover-class="tap" hover-stay-time="70" @click="goMyOrders">
            <text class="menu-text">我的订单</text>
            <text class="arrow">›</text>
          </view>
          <Divider inset v-if="userStore.token && !userStore.userInfo?.email" />
          <view
            class="menu-item"
            v-if="userStore.token && !userStore.userInfo?.email"
            hover-class="tap"
            hover-stay-time="70"
            @click="goBindEmail"
          >
            <text class="menu-text">绑定邮箱</text>
            <text class="arrow">›</text>
          </view>
          <Divider inset />
          <view class="menu-item" hover-class="tap" hover-stay-time="70" @click="handlePoints">
            <text class="menu-text">积分中心</text>
            <text class="arrow">›</text>
          </view>
          <Divider inset />
          <view class="menu-item" hover-class="tap" hover-stay-time="70" @click="handleInvitePoster">
            <text class="menu-text">邀请海报</text>
            <text class="arrow">›</text>
          </view>
          <Divider inset v-if="userStore.token" />
          <view class="menu-item danger" v-if="userStore.token" hover-class="tap" hover-stay-time="70" @click="handleLogout">
            <text class="menu-text logout">退出登录</text>
            <text class="arrow">›</text>
          </view>
        </Card>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useUserStore } from '../../store/user';
import { request } from '../../utils/request';
import { onShow } from '@dcloudio/uni-app';
import AppBar from '@/components/ui/AppBar.vue';
import Card from '@/components/ui/Card.vue';
import Divider from '@/components/ui/Divider.vue';
import SectionHeader from '@/components/ui/SectionHeader.vue';
import { TESTDATA_IMAGES } from '@/constants/testdataImages';

const userStore = useUserStore();

const avatarSrc = computed(() => userStore.userInfo?.avatar_url || TESTDATA_IMAGES.avatarV2);
const nicknameText = computed(() => {
  if (!userStore.token) return '未登录';
  return userStore.userInfo?.nickname || '数字游民';
});
const metaText = computed(() => {
  if (!userStore.token) return '登录后可同步积分与资料';
  return '欢迎回来';
});

const handleWxLogin = () => {
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
  uni.showModal({
    title: '确认退出',
    content: '退出后将无法同步资料与报名记录',
    confirmText: '退出',
    cancelText: '取消',
    success: (r) => {
      if (!r.confirm) return;
      userStore.logout();
    },
  });
};

const goEmailRegister = () => {
  uni.navigateTo({ url: '/pages/auth/register' });
};

const goEmailLogin = () => {
  uni.navigateTo({ url: '/pages/auth/login' });
};

const goBindEmail = () => {
  if (!userStore.token) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    return;
  }
  uni.navigateTo({ url: '/pages/auth/bind-email' });
};

const goMyEvents = () => {
  if (!userStore.token) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    uni.navigateTo({ url: '/pages/auth/login' });
    return;
  }
  uni.navigateTo({ url: '/pages/events/my' });
};

const goMyOrders = () => {
  if (!userStore.token) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    uni.navigateTo({ url: '/pages/auth/login' });
    return;
  }
  uni.navigateTo({ url: '/pages/orders/index' });
};

const goMyProfile = async () => {
  if (!userStore.token) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    return;
  }
  let id = Number((userStore.userInfo as any)?.id);
  if (!id) {
    try {
      const me: any = await request({ url: '/users/me', method: 'GET' });
      userStore.setUserInfo(me);
      id = Number(me?.id);
    } catch {}
  }
  if (!id) {
    uni.showToast({ title: '用户信息异常', icon: 'none' });
    return;
  }
  uni.navigateTo({ url: `/pages/user/profile?id=${id}` });
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

<style scoped lang="scss">
.profile { padding: 14px; overflow: hidden; background: linear-gradient(180deg, rgba(18, 200, 192, 0.08), rgba(255,255,255, 0.92)); }
.profile-main { display: flex; align-items: center; gap: 12px; }
.avatar {
  width: 64px;
  height: 64px;
  border-radius: 32px;
  background: rgba(15, 23, 42, 0.04);
  border: 2px solid rgba(255, 255, 255, .9);
}
.info { flex: 1; display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.nickname { font-size: 18px; font-weight: 900; color: $ymd-v2-color-text; }
.meta { font-size: 12px; color: $ymd-v2-color-muted; }

.badges { margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px; }
.badge { display: flex; align-items: baseline; gap: 8px; padding: 8px 10px; border-radius: $ymd-v2-radius-md; background: rgba(255,255,255,0.86); border: 1px solid rgba(15, 23, 42, 0.06); }
.badge.warn { border-color: rgba(245, 158, 11, 0.22); background: rgba(245, 158, 11, 0.08); }
.badge-k { font-size: 11px; color: $ymd-v2-color-muted; font-weight: 800; }
.badge-v { font-size: 12px; color: $ymd-v2-color-text; font-weight: 900; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.account { margin-top: 12px; padding: 14px; }
.account-row { display: flex; gap: 10px; margin-top: 10px; }
.account-btn { flex: 1; border-radius: $ymd-radius-md; height: 44px; line-height: 44px; font-weight: 700; }
.account-hint { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.hint-title { font-size: $ymd-v2-font-md; font-weight: 900; color: $ymd-v2-color-text; }
.hint-sub { font-size: $ymd-v2-font-sm; color: $ymd-v2-color-muted; }

.menu { overflow: hidden; }
.menu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 14px;
}
.menu-text { font-size: 14px; color: $ymd-v2-color-text; font-weight: 900; }
.arrow { font-size: 16px; color: rgba(100, 116, 139, .9); }
.tap { background: rgba(15, 23, 42, 0.04); }
.danger .menu-text { color: $uni-color-error; }
.logout { color: $uni-color-error; font-weight: 800; }
</style>
