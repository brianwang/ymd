<template>
  <view class="page">
    <view class="topbar">
      <text class="title">社区动态</text>
      <button class="create-btn" size="mini" @click="goCreate">发帖</button>
    </view>

    <view v-if="posts.length === 0 && !loading" class="empty">暂无内容</view>

    <view class="list">
      <view v-for="item in posts" :key="item.id" class="card" @click="goDetail(item.id)">
        <view class="card-content">{{ item.content }}</view>
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
          <text v-if="item.liked_by_me" class="liked">已赞</text>
        </view>
      </view>
    </view>

    <view v-if="loading && posts.length" class="loading">加载中...</view>
    <view v-else-if="finished && posts.length" class="loading">没有更多了</view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app';
import { request } from '@/utils/request';

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

const posts = ref<PostOut[]>([]);
const limit = 20;
const offset = ref(0);
const loading = ref(false);
const finished = ref(false);

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
  try {
    const nextOffset = reset ? 0 : offset.value;
    const data = (await request({
      url: '/posts',
      data: { limit, offset: nextOffset },
    })) as PostOut[];
    posts.value = reset ? data : posts.value.concat(data);
    offset.value = nextOffset + data.length;
    finished.value = data.length < limit;
  } finally {
    loading.value = false;
  }
};

const goCreate = () => {
  uni.navigateTo({ url: '/pages/community/create' });
};

const goDetail = (id: number) => {
  uni.navigateTo({ url: `/pages/community/detail?id=${id}` });
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

<style>
.page {
  padding: 16rpx;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8rpx 0 16rpx;
}
.title {
  font-size: 32rpx;
  font-weight: 600;
}
.create-btn {
  height: 56rpx;
  line-height: 56rpx;
  padding: 0 20rpx;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}
.card {
  background: #fff;
  border-radius: 16rpx;
  padding: 20rpx;
}
.card-content {
  font-size: 30rpx;
  line-height: 44rpx;
  color: #111;
  white-space: pre-wrap;
  word-break: break-all;
}
.imgs {
  margin-top: 16rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}
.img {
  width: 210rpx;
  height: 210rpx;
  border-radius: 12rpx;
  background: #f2f2f2;
}
.meta {
  margin-top: 16rpx;
  display: flex;
  align-items: center;
  gap: 18rpx;
  color: #666;
  font-size: 24rpx;
}
.liked {
  color: #007aff;
}
.loading {
  padding: 20rpx 0 40rpx;
  text-align: center;
  color: #888;
  font-size: 24rpx;
}
.empty {
  padding: 60rpx 0;
  text-align: center;
  color: #888;
  font-size: 28rpx;
}
</style>
