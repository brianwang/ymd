<template>
  <view class="page">
    <view v-if="post" class="post">
      <view class="post-content">{{ post.content }}</view>
      <view v-if="post.image_urls && post.image_urls.length" class="imgs">
        <image
          v-for="(url, idx) in post.image_urls"
          :key="url + '-' + idx"
          class="img"
          :src="url"
          mode="aspectFill"
          @click.stop="preview(post.image_urls, idx)"
        />
      </view>
      <view class="actions">
        <button
          class="like-btn"
          size="mini"
          :loading="likeLoading"
          :disabled="likeLoading"
          @click="toggleLike"
        >
          {{ post.liked_by_me ? '已赞' : '点赞' }} {{ post.like_count }}
        </button>
        <text class="meta">{{ formatTime(post.created_at) }}</text>
        <text class="meta">评论 {{ post.comment_count }}</text>
      </view>
    </view>

    <view class="comments">
      <view class="section-title">评论</view>
      <view v-if="comments.length === 0 && !commentsLoading" class="empty">暂无评论</view>
      <view v-for="c in comments" :key="c.id" class="comment">
        <view class="comment-content">{{ c.content }}</view>
        <view class="comment-meta">{{ formatTime(c.created_at) }}</view>
      </view>
      <view v-if="commentsLoading && comments.length" class="loading">加载中...</view>
    </view>

    <view class="composer">
      <input
        v-model="commentText"
        class="input"
        placeholder="写下评论..."
        confirm-type="send"
        @confirm="submitComment"
      />
      <button
        class="send"
        size="mini"
        :disabled="submittingComment || !commentText.trim()"
        :loading="submittingComment"
        @click="submitComment"
      >
        发送
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
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

type CommentOut = {
  id: number;
  post_id: number;
  user_id: number;
  content: string;
  created_at: string;
};

type LikeToggleOut = {
  liked: boolean;
  like_count: number;
  comment_count: number;
};

const postId = ref<number | null>(null);
const post = ref<PostOut | null>(null);
const comments = ref<CommentOut[]>([]);
const commentsLoading = ref(false);
const likeLoading = ref(false);
const commentText = ref('');
const submittingComment = ref(false);

const pad = (n: number) => String(n).padStart(2, '0');
const formatTime = (value: string) => {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

const loadPost = async () => {
  if (!postId.value) return;
  post.value = (await request({ url: `/posts/${postId.value}` })) as PostOut;
};

const loadComments = async () => {
  if (!postId.value) return;
  commentsLoading.value = true;
  try {
    comments.value = (await request({
      url: `/posts/${postId.value}/comments`,
      data: { limit: 50, offset: 0 },
    })) as CommentOut[];
  } finally {
    commentsLoading.value = false;
  }
};

const toggleLike = async () => {
  if (!postId.value || !post.value) return;
  if (likeLoading.value) return;
  likeLoading.value = true;
  try {
    const data = (await request({
      url: `/posts/${postId.value}/like`,
      method: 'POST',
    })) as LikeToggleOut;
    post.value = {
      ...post.value,
      liked_by_me: data.liked,
      like_count: data.like_count,
      comment_count: data.comment_count,
    };
  } finally {
    likeLoading.value = false;
  }
};

const submitComment = async () => {
  if (!postId.value || !post.value) return;
  const text = commentText.value.trim();
  if (!text) return;
  if (submittingComment.value) return;
  submittingComment.value = true;
  try {
    const data = (await request({
      url: `/posts/${postId.value}/comments`,
      method: 'POST',
      data: { content: text },
    })) as CommentOut;
    comments.value = comments.value.concat(data);
    commentText.value = '';
    post.value = { ...post.value, comment_count: post.value.comment_count + 1 };
  } finally {
    submittingComment.value = false;
  }
};

const preview = (urls: string[], current: number) => {
  uni.previewImage({ urls, current });
};

onLoad(async (options) => {
  const id = Number((options as any)?.id);
  if (!id) {
    uni.showToast({ title: '参数错误', icon: 'none' });
    return;
  }
  postId.value = id;
  await loadPost();
  await loadComments();
});
</script>

<style>
.page {
  padding: 16rpx 16rpx 120rpx;
}
.post {
  background: #fff;
  border-radius: 16rpx;
  padding: 20rpx;
}
.post-content {
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
.actions {
  margin-top: 16rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.like-btn {
  height: 56rpx;
  line-height: 56rpx;
  padding: 0 20rpx;
  background: #f7f7f7;
  color: #111;
}
.like-btn[disabled] {
  opacity: 0.6;
}
.meta {
  font-size: 24rpx;
  color: #666;
}
.comments {
  margin-top: 16rpx;
  background: #fff;
  border-radius: 16rpx;
  padding: 20rpx;
}
.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #111;
  margin-bottom: 12rpx;
}
.comment {
  padding: 14rpx 0;
  border-top: 1rpx solid #f0f0f0;
}
.comment:first-child {
  border-top: 0;
  padding-top: 0;
}
.comment-content {
  font-size: 28rpx;
  line-height: 40rpx;
  color: #111;
  white-space: pre-wrap;
  word-break: break-all;
}
.comment-meta {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #888;
}
.empty {
  padding: 28rpx 0;
  text-align: center;
  color: #888;
  font-size: 26rpx;
}
.loading {
  padding: 16rpx 0 0;
  text-align: center;
  color: #888;
  font-size: 24rpx;
}
.composer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 16rpx;
  background: #fff;
  border-top: 1rpx solid #f0f0f0;
  display: flex;
  gap: 12rpx;
  align-items: center;
}
.input {
  flex: 1;
  height: 72rpx;
  background: #f7f7f7;
  border-radius: 12rpx;
  padding: 0 16rpx;
  font-size: 28rpx;
}
.send {
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 22rpx;
  background: #007aff;
  color: #fff;
}
</style>
