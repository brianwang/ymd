<template>
  <view class="ymd-page">
    <AppBar title="社区" action-text="发帖" @action="goCreate" />
    <view class="ymd-container ymd-page-inner">
      <view v-if="status === 'loading' && posts.length === 0" class="sk">
        <Card class="sk-card">
          <view class="sk-head">
            <Skeleton width="36px" height="36px" border-radius="18px" />
            <view class="sk-head-main">
              <Skeleton width="120px" height="14px" />
              <Skeleton width="90px" height="12px" />
            </view>
          </view>
          <view class="sk-body">
            <Skeleton height="14px" />
            <Skeleton height="14px" width="80%" />
            <Skeleton height="110px" border-radius="14px" />
          </view>
        </Card>
        <Card class="sk-card">
          <view class="sk-head">
            <Skeleton width="36px" height="36px" border-radius="18px" />
            <view class="sk-head-main">
              <Skeleton width="140px" height="14px" />
              <Skeleton width="110px" height="12px" />
            </view>
          </view>
          <view class="sk-body">
            <Skeleton height="14px" />
            <Skeleton height="14px" width="74%" />
          </view>
        </Card>
      </view>

      <EmptyState
        v-else-if="status === 'error'"
        :image="TESTDATA_IMAGES.emptyErrorV2"
        title="网络开小差了"
        :desc="errorText || '请稍后重试'"
        action-text="重试"
        @action="fetchPosts(true)"
      />
      <EmptyState
        v-else-if="posts.length === 0"
        :image="TESTDATA_IMAGES.emptyListV2"
        title="还没有内容"
        desc="发布第一条动态，开始你的游牧记录"
        action-text="去发帖"
        @action="goCreate"
      />

      <view v-else class="list">
        <Card v-for="item in posts" :key="item.id" class="post" pressable @click="goDetail(item.id)">
          <view class="head" @click.stop="goUser(item.user_id)">
            <image class="avatar" :src="item.author?.avatar_url || TESTDATA_IMAGES.avatarV2" mode="aspectFill" />
            <view class="head-main">
              <text class="name">{{ item.author?.nickname || `用户 #${item.user_id}` }}</text>
              <text class="time">{{ formatTime(item.created_at) }}</text>
            </view>
          </view>
          <view class="content">{{ item.content }}</view>
          <PostMedia mode="feed" :media="item.media" :image-urls="item.image_urls" />
          <view class="actions-bar">
            <view class="action-item" :class="{ disabled: !!likeLoadingMap[item.id] }" @click.stop="toggleLike(item)">
              <text class="icon" :class="{ 'liked': item.liked_by_me }">{{ item.liked_by_me ? '♥' : '♡' }}</text>
              <text class="count">{{ item.like_count || '点赞' }}</text>
            </view>
            <view class="action-item" :class="{ disabled: !!favLoadingMap[item.id] }" @click.stop="toggleFavorite(item)">
              <text class="icon" :class="{ 'favorited': item.favorited_by_me }">{{ item.favorited_by_me ? '★' : '☆' }}</text>
              <text class="count">{{ item.favorite_count || '收藏' }}</text>
            </view>
            <view class="action-item" @click.stop="goDetail(item.id)">
              <text class="icon">💬</text>
              <text class="count">{{ item.comment_count || '评论' }}</text>
            </view>
            <button class="action-item share-btn" open-type="share" @click.stop="trackShare(item)">
              <text class="icon">↗</text>
              <text class="count">{{ item.share_count || '转发' }}</text>
            </button>
          </view>
        </Card>
      </view>

      <view v-if="loading && posts.length" class="loading">加载中...</view>
      <view v-else-if="finished && posts.length" class="loading">没有更多了</view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app';
import { ensureLoggedIn, request } from '@/utils/request';
import AppBar from '@/components/ui/AppBar.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import Skeleton from '@/components/ui/Skeleton.vue';
import Card from '@/components/ui/Card.vue';
import PostMedia, { type PostMediaItem } from '@/components/community/PostMedia.vue';
import { TESTDATA_IMAGES } from '@/constants/testdataImages';

type PostOut = {
  id: number;
  user_id: number;
  content: string;
  image_urls: string[];
  media?: PostMediaItem[] | null;
  like_count: number;
  comment_count: number;
  favorite_count: number;
  share_count: number;
  created_at: string;
  updated_at?: string | null;
  liked_by_me: boolean;
  favorited_by_me: boolean;
  author?: {
    id: number;
    nickname?: string | null;
    avatar_url?: string | null;
  } | null;
};

const posts = ref<PostOut[]>([]);
const limit = 20;
const offset = ref(0);
const loading = ref(false);
const finished = ref(false);
const status = ref<'loading' | 'ready' | 'error'>('loading');
const errorText = ref('');
const likeLoadingMap = ref<Record<number, boolean>>({});
const favLoadingMap = ref<Record<number, boolean>>({});

const formatTime = (value: string) => {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

const fetchPosts = async (reset = false) => {
  if (loading.value) return;
  if (finished.value && !reset) return;
  loading.value = true;
  if (reset) status.value = 'loading';
  try {
    const nextOffset = reset ? 0 : offset.value;
    const data = (await request({
      url: '/posts',
      data: { limit, offset: nextOffset },
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

const goCreate = () => {
  if (!ensureLoggedIn()) return;
  uni.navigateTo({ url: '/pages/community/create' });
};

const goDetail = (id: number) => {
  uni.navigateTo({ url: `/pages/community/detail?id=${id}` });
};

const goUser = (userId: number) => {
  uni.navigateTo({ url: `/pages/user/profile?id=${userId}` });
};

const toggleLike = async (item: PostOut) => {
  if (!ensureLoggedIn()) return;
  if (likeLoadingMap.value[item.id]) return;
  likeLoadingMap.value = { ...likeLoadingMap.value, [item.id]: true };
  const optimisticLiked = !item.liked_by_me;
  const optimisticCount = Math.max(0, item.like_count + (optimisticLiked ? 1 : -1));
  const prev = { liked: item.liked_by_me, like_count: item.like_count };
  item.liked_by_me = optimisticLiked;
  item.like_count = optimisticCount;
  try {
    const data = (await request({
      url: `/posts/${item.id}/like`,
      method: optimisticLiked ? 'POST' : 'DELETE',
    })) as { liked: boolean; like_count: number; comment_count: number };
    item.liked_by_me = data.liked;
    item.like_count = data.like_count;
    item.comment_count = data.comment_count;
  } catch {
    item.liked_by_me = prev.liked;
    item.like_count = prev.like_count;
  } finally {
    const { [item.id]: _, ...rest } = likeLoadingMap.value;
    likeLoadingMap.value = rest;
  }
};

const toggleFavorite = async (item: PostOut) => {
  if (!ensureLoggedIn()) return;
  if (favLoadingMap.value[item.id]) return;
  favLoadingMap.value = { ...favLoadingMap.value, [item.id]: true };
  const optimisticFav = !item.favorited_by_me;
  const optimisticCount = Math.max(0, item.favorite_count + (optimisticFav ? 1 : -1));
  const prev = { favorited: item.favorited_by_me, favorite_count: item.favorite_count };
  item.favorited_by_me = optimisticFav;
  item.favorite_count = optimisticCount;
  try {
    const data = (await request({
      url: `/posts/${item.id}/favorite/toggle`,
      method: 'POST',
    })) as { favorited: boolean; favorite_count: number };
    item.favorited_by_me = data.favorited;
    item.favorite_count = data.favorite_count;
  } catch {
    item.favorited_by_me = prev.favorited;
    item.favorite_count = prev.favorite_count;
  } finally {
    const { [item.id]: _, ...rest } = favLoadingMap.value;
    favLoadingMap.value = rest;
  }
};

const trackShare = async (item: PostOut) => {
  // 仅在前端发送转发埋点
  try {
    const data = (await request({
      url: `/posts/${item.id}/share`,
      method: 'POST',
    })) as { share_count: number };
    item.share_count = data.share_count;
  } catch (e) {
    // 忽略错误，避免阻断转发
  }
};

onShow(() => {
  finished.value = false;
  offset.value = 0;
  fetchPosts(true);
});

onPullDownRefresh(async () => {
  finished.value = false;
  offset.value = 0;
  await fetchPosts(true);
  uni.stopPullDownRefresh();
});

onReachBottom(() => {
  fetchPosts(false);
});
</script>

<style lang="scss">
.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.post {
  padding: 14px;
}
.head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.04);
}
.head-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.name {
  font-size: 13px;
  font-weight: 900;
  color: $ymd-v2-color-text;
}
.time {
  font-size: 12px;
  color: $ymd-v2-color-muted;
}
.content {
  font-size: 15px;
  line-height: 22px;
  color: $ymd-v2-color-text;
  white-space: pre-wrap;
  word-break: break-all;
}
.imgs {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.img {
  width: 104px;
  height: 104px;
  border-radius: $ymd-v2-radius-md;
  background: rgba(15, 23, 42, 0.04);
}
.actions-bar {
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid rgba(15, 23, 42, 0.04);
  padding-top: 10px;
}
.action-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: $ymd-v2-color-muted;
  font-size: 13px;
  padding: 4px 8px;
  transition: all 0.2s;
}
.action-item.disabled {
  opacity: 0.5;
}
.action-item .icon {
  font-size: 16px;
  line-height: 16px;
}
.action-item .icon.liked {
  color: $ymd-v2-color-accent-2;
}
.action-item .icon.favorited {
  color: #f59e0b;
}
.share-btn {
  margin: 0;
  padding: 0;
  background: transparent;
  line-height: normal;
  border: none !important;
}
.share-btn::after {
  display: none;
}
.loading {
  padding: 14px 0 28px;
  text-align: center;
  color: $ymd-v2-color-muted;
  font-size: 12px;
}
.sk-card { padding: 14px; margin-bottom: 12px; }
.sk-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.sk-head-main { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.sk-body { display: flex; flex-direction: column; gap: 10px; }
</style>
