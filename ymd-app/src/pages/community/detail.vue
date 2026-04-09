<template>
  <view class="ymd-page">
    <AppBar title="帖子详情" back></AppBar>
    <view class="ymd-container ymd-page-inner page">
      <Card v-if="post" class="post">
        <view class="post-head" @click="goUser(post.user_id)">
          <image class="avatar" :src="post.author?.avatar_url || TESTDATA_IMAGES.avatarV2" mode="aspectFill" />
          <view class="head-main">
            <text class="name">{{ post.author?.nickname || `用户 #${post.user_id}` }}</text>
            <text class="time">{{ formatTime(post.created_at) }}</text>
          </view>
          <view class="head-actions" @click.stop="noop">
            <button
              v-if="canDelete"
              class="del-btn ymd-btn ghost"
              size="mini"
              :loading="deleting"
              :disabled="deleting"
              @click="deletePost"
            >
              删除
            </button>
          </view>
        </view>
        <view class="post-content">{{ post.content }}</view>
        <PostMedia mode="detail" :media="post.media" :image-urls="post.image_urls" />
        <view class="actions-bar">
          <view class="action-item" :class="{ disabled: likeLoading }" @click.stop="toggleLike">
            <text class="icon" :class="{ 'liked': post.liked_by_me }">{{ post.liked_by_me ? '♥' : '♡' }}</text>
            <text class="count">{{ post.like_count || '点赞' }}</text>
          </view>
          <view class="action-item" :class="{ disabled: favLoading }" @click.stop="toggleFavorite">
            <text class="icon" :class="{ 'favorited': post.favorited_by_me }">{{ post.favorited_by_me ? '★' : '☆' }}</text>
            <text class="count">{{ post.favorite_count || '收藏' }}</text>
          </view>
          <view class="action-item" @click.stop="focusComment">
            <text class="icon">💬</text>
            <text class="count">{{ post.comment_count || '评论' }}</text>
          </view>
          <button class="action-item share-btn" open-type="share" @click.stop="trackShare" plain>
            <text class="icon">↗</text>
            <text class="count">{{ post.share_count || '转发' }}</text>
          </button>
        </view>
      </Card>
      <Card v-else class="post sk">
        <view class="sk-head">
          <Skeleton width="36px" height="36px" border-radius="18px"></Skeleton>
          <view class="sk-head-main">
            <Skeleton width="140px" height="14px"></Skeleton>
            <Skeleton width="100px" height="12px"></Skeleton>
          </view>
        </view>
        <view class="sk-body">
          <Skeleton height="14px"></Skeleton>
          <Skeleton height="14px" width="76%"></Skeleton>
          <Skeleton height="110px" border-radius="14px"></Skeleton>
        </view>
      </Card>

      <Card class="comments">
        <SectionHeader title="评论"></SectionHeader>
        <EmptyState
          v-if="comments.length === 0 && !commentsLoading"
          :image="TESTDATA_IMAGES.emptyListV2"
          title="暂无评论"
          desc="说点什么，让讨论开始"
        ></EmptyState>
        <view v-else>
          <view v-for="c in comments" :key="c.id" class="comment">
            <view class="comment-content">{{ c.content }}</view>
            <view class="comment-meta">{{ formatTime(c.created_at) }}</view>
          </view>
          <view v-if="commentsLoading && comments.length" class="loading">加载中...</view>
        </view>
      </Card>
    </view>

    <view class="composer">
      <view class="ymd-container composer-inner">
        <input
          v-model="commentText"
          class="input"
          placeholder="写下评论..."
          confirm-type="send"
          :focus="isInputFocused"
          @blur="isInputFocused = false"
          @confirm="submitComment"
        />
        <button
          class="send ymd-btn"
          size="mini"
          :disabled="submittingComment || !commentText.trim()"
          :loading="submittingComment"
          @click="submitComment"
        >
          发送
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { ensureLoggedIn, request } from '@/utils/request';
import { useUserStore } from '@/store/user';
import AppBar from '@/components/ui/AppBar.vue';
import Card from '@/components/ui/Card.vue';
import SectionHeader from '@/components/ui/SectionHeader.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import Skeleton from '@/components/ui/Skeleton.vue';
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
const favLoading = ref(false);
const commentText = ref('');
const isInputFocused = ref(false);
const submittingComment = ref(false);
const deleting = ref(false);
const userStore = useUserStore();

const canDelete = computed(() => {
  const meId = (userStore.userInfo as any)?.id;
  if (!meId || !post.value) return false;
  return meId === post.value.user_id;
});

const noop = () => {};

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
  if (!ensureLoggedIn()) return;
  if (likeLoading.value) return;
  likeLoading.value = true;
  let prevState: { liked: boolean; like_count: number; comment_count: number } | null = null;
  try {
    const optimisticLiked = !post.value.liked_by_me;
    prevState = {
      liked: post.value.liked_by_me,
      like_count: post.value.like_count,
      comment_count: post.value.comment_count,
    };
    post.value = {
      ...post.value,
      liked_by_me: optimisticLiked,
      like_count: Math.max(0, post.value.like_count + (optimisticLiked ? 1 : -1)),
    };
    const data = (await request({
      url: `/posts/${postId.value}/like`,
      method: optimisticLiked ? 'POST' : 'DELETE',
    })) as LikeToggleOut;
    post.value = {
      ...post.value,
      liked_by_me: data.liked,
      like_count: data.like_count,
      comment_count: data.comment_count,
    };
  } catch {
    if (post.value && prevState) {
      post.value = {
        ...post.value,
        liked_by_me: prevState.liked,
        like_count: prevState.like_count,
        comment_count: prevState.comment_count,
      };
    }
  } finally {
    likeLoading.value = false;
  }
};

const submitComment = async () => {
  if (!postId.value || !post.value) return;
  if (!ensureLoggedIn()) return;
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

const goUser = (userId: number) => {
  uni.navigateTo({ url: `/pages/user/profile?id=${userId}` });
};

const focusComment = () => {
  isInputFocused.value = true;
};

const toggleFavorite = async () => {
  if (!postId.value || !post.value) return;
  if (!ensureLoggedIn()) return;
  if (favLoading.value) return;
  favLoading.value = true;
  let prevState: { favorited: boolean; favorite_count: number } | null = null;
  try {
    const optimisticFav = !post.value.favorited_by_me;
    prevState = {
      favorited: post.value.favorited_by_me,
      favorite_count: post.value.favorite_count,
    };
    post.value = {
      ...post.value,
      favorited_by_me: optimisticFav,
      favorite_count: Math.max(0, post.value.favorite_count + (optimisticFav ? 1 : -1)),
    };
    const data = (await request({
      url: `/posts/${postId.value}/favorite/toggle`,
      method: 'POST',
    })) as { favorited: boolean; favorite_count: number };
    post.value = {
      ...post.value,
      favorited_by_me: data.favorited,
      favorite_count: data.favorite_count,
    };
  } catch {
    if (post.value && prevState) {
      post.value = {
        ...post.value,
        favorited_by_me: prevState.favorited,
        favorite_count: prevState.favorite_count,
      };
    }
  } finally {
    favLoading.value = false;
  }
};

const trackShare = async () => {
  if (!postId.value || !post.value) return;
  try {
    const data = (await request({
      url: `/posts/${postId.value}/share`,
      method: 'POST',
    })) as { share_count: number };
    post.value = {
      ...post.value,
      share_count: data.share_count,
    };
  } catch (e) {
    // 忽略错误
  }
};

const deletePost = async () => {
  if (!postId.value) return;
  if (!ensureLoggedIn()) return;
  if (deleting.value) return;
  uni.showModal({
    title: '确认删除',
    content: '删除后不可恢复，确定删除？',
    confirmText: '删除',
    confirmColor: '#DC2626',
    success: async (res) => {
      if (!res.confirm) return;
      deleting.value = true;
      try {
        await request({ url: `/posts/${postId.value}`, method: 'DELETE' });
        uni.showToast({ title: '已删除', icon: 'success' });
        setTimeout(() => {
          uni.navigateBack();
        }, 300);
      } finally {
        deleting.value = false;
      }
    },
  });
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

<style lang="scss">
.page { padding-bottom: 90px; }
.post {
  padding: 14px;
}
.post-head {
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
  flex: 1;
}
.name { font-size: 13px; font-weight: 900; color: $ymd-v2-color-text; }
.time { font-size: 12px; color: $ymd-v2-color-muted; }
.head-actions { display: flex; align-items: center; }
.del-btn { height: 34px; line-height: 34px; padding: 0 14px; font-size: 12px; }
.post-content {
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
.meta {
  font-size: 12px;
  color: $ymd-v2-color-muted;
}
.comments {
  margin-top: 12px;
  padding: 14px;
}
.comment {
  padding: 10px 0;
  border-top: 1px solid $ymd-v2-color-line;
}
.comment:first-child {
  border-top: 0;
  padding-top: 0;
}
.comment-content {
  font-size: 14px;
  line-height: 20px;
  color: $ymd-v2-color-text;
  white-space: pre-wrap;
  word-break: break-all;
}
.comment-meta {
  margin-top: 6px;
  font-size: 12px;
  color: $ymd-v2-color-muted;
}
.loading {
  padding: 12px 0 0;
  text-align: center;
  color: $ymd-v2-color-muted;
  font-size: 12px;
}
.composer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 12px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(15, 23, 42, 0.08);
}
.composer-inner {
  display: flex;
  gap: 10px;
  align-items: center;
  padding-left: 0;
  padding-right: 0;
}
.input {
  flex: 1;
  height: 40px;
  background: rgba(15, 23, 42, 0.04);
  border-radius: $ymd-v2-radius-md;
  padding: 0 12px;
  font-size: 14px;
}
.send {
  height: 40px;
  line-height: 40px;
  padding: 0 14px;
  font-size: 12px;
  font-weight: 800;
}

.sk { padding: 14px; }
.sk-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.sk-head-main { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.sk-body { display: flex; flex-direction: column; gap: 10px; }
</style>
