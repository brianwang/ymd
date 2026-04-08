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
        image="/static/empty/empty-error-v2.png"
        title="网络开小差了"
        :desc="errorText || '请稍后重试'"
        action-text="重试"
        @action="fetchPosts(true)"
      />
      <EmptyState
        v-else-if="posts.length === 0"
        image="/static/empty/empty-list-v2.png"
        title="还没有内容"
        desc="发布第一条动态，开始你的游牧记录"
        action-text="去发帖"
        @action="goCreate"
      />

      <view v-else class="list">
        <Card v-for="item in posts" :key="item.id" class="post" pressable @click="goDetail(item.id)">
          <view class="head" @click.stop="goUser(item.user_id)">
            <image class="avatar" :src="item.author?.avatar_url || '/static/placeholder/avatar-v2.png'" mode="aspectFill" />
            <view class="head-main">
              <text class="name">{{ item.author?.nickname || `用户 #${item.user_id}` }}</text>
              <text class="time">{{ formatTime(item.created_at) }}</text>
            </view>
          </view>
          <view class="content">{{ item.content }}</view>
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
            <button
              class="like-btn ymd-btn ghost"
              size="mini"
              :loading="!!likeLoadingMap[item.id]"
              :disabled="!!likeLoadingMap[item.id]"
              @click.stop="toggleLike(item)"
            >
              {{ item.liked_by_me ? '已赞' : '点赞' }} {{ item.like_count }}
            </button>
            <text class="meta-item">评 {{ item.comment_count }}</text>
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
.meta {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: $ymd-v2-color-muted;
  font-size: 12px;
}
.like-btn {
  height: 34px;
  line-height: 34px;
  padding: 0 14px;
  font-size: 12px;
  font-weight: 800;
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
