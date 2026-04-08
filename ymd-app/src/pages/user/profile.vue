<template>
  <view class="page ymd-page">
    <view class="card" v-if="profile">
      <view class="profile-row">
        <image v-if="profile.avatar_url" class="avatar" :src="profile.avatar_url" mode="aspectFill" />
        <view class="info">
          <text class="name">{{ profile.nickname || `用户 #${profile.id}` }}</text>
          <text class="sub">ID: {{ profile.id }}</text>
        </view>
        <view class="actions" v-if="!isMe">
          <button
            class="follow-btn ymd-btn"
            size="mini"
            :loading="followLoading"
            :disabled="followLoading"
            @click="toggleFollow"
          >
            {{ profile.viewer_is_following ? '已关注' : '关注' }}
          </button>
        </view>
      </view>
    </view>

    <view v-if="status === 'loading' && posts.length === 0" class="state">
      <image class="state-illus" src="/static/empty/empty-list-v2.png" mode="widthFix" />
      <text class="state-title">加载中...</text>
    </view>
    <view v-else-if="status === 'error'" class="state">
      <image class="state-illus" src="/static/empty/empty-error-v2.png" mode="widthFix" />
      <text class="state-title">网络开小差了</text>
      <text class="state-sub">{{ errorText || '请稍后重试' }}</text>
      <view class="state-actions">
        <button class="state-btn ymd-btn" size="mini" @click="reload">重试</button>
      </view>
    </view>
    <view v-else-if="posts.length === 0" class="state">
      <image class="state-illus" src="/static/empty/empty-list-v2.png" mode="widthFix" />
      <text class="state-title">还没有内容</text>
      <text class="state-sub">Ta 还没有发布动态</text>
    </view>

    <view class="list">
      <view v-for="item in posts" :key="item.id" class="post" @click="goDetail(item.id)">
        <view class="post-content">{{ item.content }}</view>
        <view v-if="item.image_urls && item.image_urls.length" class="imgs">
          <image
            v-for="(url, idx) in item.image_urls"
            :key="url + '-' + idx"
            class="img"
            :src="url"
            mode="aspectFill"
          />
        </view>
        <view class="meta">
          <text class="meta-item">{{ formatTime(item.created_at) }}</text>
          <text class="meta-item">赞 {{ item.like_count }}</text>
          <text class="meta-item">评 {{ item.comment_count }}</text>
        </view>
      </view>
    </view>

    <view v-if="loading && posts.length" class="loading">加载中...</view>
    <view v-else-if="finished && posts.length" class="loading">没有更多了</view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { onLoad, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app';
import { ensureLoggedIn, request } from '@/utils/request';
import { useUserStore } from '@/store/user';

type UserProfileOut = {
  id: number;
  nickname?: string | null;
  avatar_url?: string | null;
  viewer_is_following: boolean;
};

type PostOut = {
  id: number;
  user_id: number;
  content: string;
  image_urls: string[];
  like_count: number;
  comment_count: number;
  created_at: string;
  updated_at?: string | null;
  liked_by_me: boolean;
};

const userStore = useUserStore();
const userId = ref<number | null>(null);
const profile = ref<UserProfileOut | null>(null);
const followLoading = ref(false);

const posts = ref<PostOut[]>([]);
const limit = 20;
const offset = ref(0);
const loading = ref(false);
const finished = ref(false);
const status = ref<'loading' | 'ready' | 'error'>('loading');
const errorText = ref('');

const isMe = computed(() => {
  const meId = (userStore.userInfo as any)?.id;
  if (!meId || !userId.value) return false;
  return meId === userId.value;
});

const pad = (n: number) => String(n).padStart(2, '0');
const formatTime = (value: string) => {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

const loadProfile = async () => {
  if (!userId.value) return;
  profile.value = (await request({ url: `/users/${userId.value}` })) as UserProfileOut;
};

const fetchPosts = async (reset = false) => {
  if (!userId.value) return;
  if (loading.value) return;
  if (finished.value && !reset) return;
  loading.value = true;
  if (reset) status.value = 'loading';
  try {
    const nextOffset = reset ? 0 : offset.value;
    const data = (await request({
      url: '/posts',
      data: { limit, offset: nextOffset, user_id: userId.value },
    })) as PostOut[];
    posts.value = reset ? data : posts.value.concat(data);
    offset.value = nextOffset + data.length;
    finished.value = data.length < limit;
    status.value = 'ready';
    errorText.value = '';
  } catch (e: any) {
    status.value = 'error';
    errorText.value = e?.message || '加载失败';
  } finally {
    loading.value = false;
  }
};

const reload = async () => {
  finished.value = false;
  offset.value = 0;
  await loadProfile();
  await fetchPosts(true);
};

const toggleFollow = async () => {
  if (!userId.value || !profile.value) return;
  if (!ensureLoggedIn()) return;
  if (followLoading.value) return;
  followLoading.value = true;
  const target = userId.value;
  const optimistic = !profile.value.viewer_is_following;
  const prev = profile.value.viewer_is_following;
  profile.value = { ...profile.value, viewer_is_following: optimistic };
  try {
    const data = (await request({
      url: `/users/${target}/follow`,
      method: optimistic ? 'POST' : 'DELETE',
    })) as { target_user_id: number; viewer_is_following: boolean };
    profile.value = { ...profile.value, viewer_is_following: data.viewer_is_following };
  } catch {
    profile.value = { ...profile.value, viewer_is_following: prev };
  } finally {
    followLoading.value = false;
  }
};

const goDetail = (id: number) => {
  uni.navigateTo({ url: `/pages/community/detail?id=${id}` });
};

onLoad(async (options) => {
  const id = Number((options as any)?.id);
  if (!id) {
    uni.showToast({ title: '参数错误', icon: 'none' });
    return;
  }
  userId.value = id;
  await reload();
});

onPullDownRefresh(async () => {
  await reload();
  uni.stopPullDownRefresh();
});

onReachBottom(() => {
  fetchPosts(false);
});
</script>

<style lang="scss">
.page { padding: $ymd-space-3; }
.card { background: $ymd-color-card; border: 1px solid $ymd-color-line; border-radius: $ymd-radius-lg; padding: 14px; box-shadow: $ymd-shadow-xs; }
.profile-row { display: flex; align-items: center; gap: 12px; }
.avatar { width: 44px; height: 44px; border-radius: 22px; background: rgba(15, 23, 42, 0.04); }
.info { flex: 1; display: flex; flex-direction: column; gap: 3px; }
.name { font-size: 15px; font-weight: 900; color: $ymd-color-text; }
.sub { font-size: 12px; color: $ymd-color-muted; }
.follow-btn { height: 34px; line-height: 34px; padding: 0 14px; font-size: 12px; }

.list { margin-top: 12px; display: flex; flex-direction: column; gap: 12px; }
.post { background: $ymd-color-card; border-radius: $ymd-radius-lg; padding: 14px; border: 1px solid $ymd-color-line; box-shadow: $ymd-shadow-xs; }
.post-content { font-size: 15px; line-height: 22px; color: $ymd-color-text; white-space: pre-wrap; word-break: break-all; }
.imgs { margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px; }
.img { width: 104px; height: 104px; border-radius: $ymd-radius-md; background: rgba(15, 23, 42, 0.04); }
.meta { margin-top: 12px; display: flex; align-items: center; gap: 10px; color: $ymd-color-muted; font-size: 12px; }
.loading { padding: 14px 0 28px; text-align: center; color: $ymd-color-muted; font-size: 12px; }
.state { margin-top: 12px; background: $ymd-color-card; border: 1px solid $ymd-color-line; border-radius: $ymd-radius-lg; padding: 18px; display: flex; flex-direction: column; gap: 8px; align-items: center; box-shadow: $ymd-shadow-xs; }
.state-illus { width: 180px; }
.state-title { font-size: $ymd-font-md; font-weight: 800; color: $ymd-color-text; }
.state-sub { font-size: $ymd-font-sm; color: $ymd-color-muted; text-align: center; }
.state-actions { margin-top: 4px; }
.state-btn { padding: 0 14px; height: 34px; line-height: 34px; font-size: 12px; }
</style>
