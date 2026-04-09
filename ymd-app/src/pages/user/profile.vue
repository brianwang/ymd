<template>
  <view class="ymd-page">
    <AppBar :title="pageTitle" back />
    <view class="ymd-container ymd-page-inner">
      <Card v-if="pageStatus === 'loading' && !profile" class="profile sk">
        <view class="profile-row">
          <Skeleton width="44px" height="44px" border-radius="22px" />
          <view class="info">
            <Skeleton width="140px" height="14px" />
            <Skeleton width="90px" height="12px" />
          </view>
          <Skeleton width="84px" height="34px" border-radius="999px" />
        </view>
      </Card>

      <Card v-else-if="profile" class="profile">
        <view class="profile-row">
          <image class="avatar" :src="displayAvatar" mode="aspectFill" />
          <view class="info">
            <text class="name">{{ displayName }}</text>
            <text class="sub">ID: {{ profile.id }}</text>
          </view>
          <view v-if="!isMe" class="actions">
            <button
              class="follow-btn ymd-btn"
              :class="{ ghost: profile.viewer_is_following }"
              size="mini"
              :loading="followLoading"
              :disabled="followLoading"
              @click="toggleFollow"
            >
              {{ profile.viewer_is_following ? '已关注' : '关注' }}
            </button>
          </view>
        </view>
      </Card>

      <Card v-if="profile && isMe" class="me-edit">
        <view class="field">
          <text class="label">头像</text>
          <view class="avatar-area" @click="chooseAvatar" hover-class="tap" hover-stay-time="70">
            <image class="avatar-lg" :src="avatarPreview" mode="aspectFill" />
            <view class="avatar-mask">
              <text class="avatar-tip">更换头像</text>
            </view>
          </view>
        </view>
        <view class="field">
          <text class="label">昵称</text>
          <input
            class="input"
            v-model="nickname"
            maxlength="20"
            placeholder="请输入昵称（2-20字）"
            placeholder-class="ph"
          />
        </view>
        <view class="field">
          <text class="label">手机号</text>
          <input
            class="input"
            v-model="phone"
            maxlength="11"
            type="number"
            placeholder="请输入手机号（11位）"
            placeholder-class="ph"
          />
        </view>
        <view v-if="editErrorText" class="error">
          <text class="error-text">{{ editErrorText }}</text>
        </view>
        <button class="save ymd-btn" :disabled="saving" @click="saveProfile">
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </Card>

      <EmptyState
        v-if="pageStatus === 'error'"
        :image="TESTDATA_IMAGES.emptyErrorV2"
        title="网络开小差了"
        :desc="errorText || '请稍后重试'"
        action-text="重试"
        @action="reload"
      />

      <view v-else class="ymd-section">
        <SectionHeader :title="feedTitle" />

        <view v-if="pageStatus === 'loading' && posts.length === 0" class="sk-list">
          <Card class="post sk">
            <Skeleton height="14px" />
            <Skeleton height="14px" width="70%" />
            <Skeleton height="110px" border-radius="14px" />
          </Card>
          <Card class="post sk">
            <Skeleton height="14px" />
            <Skeleton height="14px" width="78%" />
          </Card>
        </view>

        <EmptyState
          v-else-if="pageStatus === 'ready' && posts.length === 0"
          :image="TESTDATA_IMAGES.emptyListV2"
          title="还没有内容"
          :desc="emptyDesc"
        />

        <view v-else class="list">
          <Card v-for="item in posts" :key="item.id" class="post" pressable @click="goDetail(item.id)">
            <view class="post-content">{{ item.content }}</view>
            <PostMedia mode="feed" :media="item.media" :image-urls="item.image_urls" />
            <view class="meta">
              <text class="meta-item">{{ formatTime(item.created_at) }}</text>
              <text class="meta-item">赞 {{ item.like_count }}</text>
              <text class="meta-item">评 {{ item.comment_count }}</text>
            </view>
          </Card>
        </view>

        <view v-if="loading && posts.length" class="loading">加载中...</view>
        <view v-else-if="finished && posts.length" class="loading">没有更多了</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { onLoad, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app';
import { BASE_URL, ensureLoggedIn, request } from '@/utils/request';
import { useUserStore } from '@/store/user';
import AppBar from '@/components/ui/AppBar.vue';
import Card from '@/components/ui/Card.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import SectionHeader from '@/components/ui/SectionHeader.vue';
import Skeleton from '@/components/ui/Skeleton.vue';
import PostMedia, { type PostMediaItem } from '@/components/community/PostMedia.vue';
import { TESTDATA_IMAGES } from '@/constants/testdataImages';

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
  media?: PostMediaItem[] | null;
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
const pageStatus = ref<'loading' | 'ready' | 'error'>('loading');
const errorText = ref('');

const isMe = computed(() => {
  const meId = (userStore.userInfo as any)?.id;
  if (!meId || !userId.value) return false;
  return meId === userId.value;
});

const pageTitle = computed(() => (isMe.value ? '我的主页' : '用户主页'));
const feedTitle = computed(() => (isMe.value ? '我的动态' : 'Ta 的动态'));
const emptyDesc = computed(() => (isMe.value ? '你还没有发布动态' : 'Ta 还没有发布动态'));
const displayAvatar = computed(() => {
  if (isMe.value) return String((userStore.userInfo as any)?.avatar_url || profile.value?.avatar_url || TESTDATA_IMAGES.avatarV2);
  return String(profile.value?.avatar_url || TESTDATA_IMAGES.avatarV2);
});
const displayName = computed(() => {
  if (!profile.value) return '';
  if (isMe.value) return String((userStore.userInfo as any)?.nickname || profile.value.nickname || `用户 #${profile.value.id}`);
  return String(profile.value.nickname || `用户 #${profile.value.id}`);
});

const nickname = ref('');
const phone = ref('');
const avatarLocalPath = ref('');
const avatarRemoteUrl = ref('');
const saving = ref(false);
const editErrorText = ref('');

const avatarPreview = computed(() => avatarLocalPath.value || avatarRemoteUrl.value || TESTDATA_IMAGES.avatarV2);

const syncFromStore = () => {
  nickname.value = String((userStore.userInfo as any)?.nickname || '');
  phone.value = String((userStore.userInfo as any)?.phone || '');
  avatarRemoteUrl.value = String((userStore.userInfo as any)?.avatar_url || '');
};

const ensureLoginForEdit = () => {
  if (userStore.token) return true;
  uni.showToast({ title: '请先登录', icon: 'none' });
  uni.navigateTo({ url: '/pages/auth/login' });
  return false;
};

const loadMeDetail = async () => {
  if (!isMe.value) return;
  if (!userStore.token) return;
  const me = await request({ url: '/users/me', method: 'GET' });
  userStore.setUserInfo(me);
  syncFromStore();
};

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
  try {
    const nextOffset = reset ? 0 : offset.value;
    const data = (await request({
      url: '/posts',
      data: { limit, offset: nextOffset, user_id: userId.value },
    })) as PostOut[];
    posts.value = reset ? data : posts.value.concat(data);
    offset.value = nextOffset + data.length;
    finished.value = data.length < limit;
  } catch (e: any) {
    throw e;
  } finally {
    loading.value = false;
  }
};

const reload = async () => {
  finished.value = false;
  offset.value = 0;
  pageStatus.value = 'loading';
  errorText.value = '';
  try {
    await Promise.all([loadProfile(), fetchPosts(true), loadMeDetail()]);
    pageStatus.value = 'ready';
  } catch (e: any) {
    pageStatus.value = 'error';
    errorText.value = e?.message || '加载失败';
  }
};

const chooseAvatar = () => {
  if (!ensureLoginForEdit()) return;
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const p = res.tempFilePaths?.[0];
      if (p) avatarLocalPath.value = p;
    },
  });
};

const uploadAvatar = (filePath: string) => {
  return new Promise<string>((resolve, reject) => {
    uni.uploadFile({
      url: `${BASE_URL}/media/upload`,
      filePath,
      name: 'file',
      header: {
        Authorization: userStore.token ? `Bearer ${userStore.token}` : '',
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            const parsed = JSON.parse(res.data || '{}') as { url?: string };
            if (parsed?.url) resolve(parsed.url);
            else reject(new Error('上传失败'));
          } catch {
            reject(new Error('上传失败'));
          }
        } else {
          reject(new Error('上传失败'));
        }
      },
      fail: () => reject(new Error('网络异常')),
    });
  });
};

const validateNickname = (raw: string) => {
  const v = raw.trim();
  if (!v) return { ok: false, value: v, msg: '昵称不能为空' };
  if (v.length < 2 || v.length > 20) return { ok: false, value: v, msg: '昵称长度需为 2-20 字' };
  return { ok: true, value: v, msg: '' };
};

const validatePhone = (raw: string) => {
  const v = raw.trim();
  if (!v) return { ok: true, value: '', msg: '' };
  if (!/^\d{11}$/.test(v)) return { ok: false, value: v, msg: '手机号需为 11 位数字' };
  return { ok: true, value: v, msg: '' };
};

const saveProfile = async () => {
  if (!ensureLoginForEdit()) return;
  const v = validateNickname(nickname.value);
  if (!v.ok) {
    editErrorText.value = v.msg;
    uni.showToast({ title: v.msg, icon: 'none' });
    return;
  }
  const p = validatePhone(phone.value);
  if (!p.ok) {
    editErrorText.value = p.msg;
    uni.showToast({ title: p.msg, icon: 'none' });
    return;
  }
  saving.value = true;
  editErrorText.value = '';
  try {
    let avatarUrl = avatarRemoteUrl.value;
    if (avatarLocalPath.value) {
      avatarUrl = await uploadAvatar(avatarLocalPath.value);
    }
    const updated: any = await request({
      url: '/users/me',
      method: 'PUT',
      data: { nickname: v.value, avatar_url: avatarUrl, phone: p.value },
    });
    userStore.setUserInfo(updated);
    avatarLocalPath.value = '';
    syncFromStore();
    if (profile.value) {
      profile.value = { ...profile.value, nickname: updated?.nickname ?? profile.value.nickname, avatar_url: updated?.avatar_url ?? profile.value.avatar_url };
    }
    uni.showToast({ title: '保存成功', icon: 'success' });
  } catch (e: any) {
    const msg = e?.data?.detail || e?.message || '保存失败';
    editErrorText.value = String(msg);
    uni.showToast({ title: String(msg), icon: 'none' });
  } finally {
    saving.value = false;
  }
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
    uni.showToast({ title: '操作失败，请重试', icon: 'none' });
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
.profile { padding: 14px; }
.profile-row { display: flex; align-items: center; gap: 12px; }
.avatar { width: 44px; height: 44px; border-radius: 22px; background: rgba(15, 23, 42, 0.04); }
.info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.name { font-size: 15px; font-weight: 900; color: $ymd-v2-color-text; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sub { font-size: 12px; color: $ymd-v2-color-muted; }
.follow-btn { height: 34px; line-height: 34px; padding: 0 14px; font-size: 12px; font-weight: 800; }

.me-edit { margin-top: 12px; padding: 14px; }
.field { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
.field:first-child { margin-top: 0; }
.label { font-size: 12px; color: $ymd-v2-color-muted; font-weight: 800; }
.avatar-area { width: 88px; height: 88px; border-radius: 44px; overflow: hidden; position: relative; }
.avatar-lg { width: 88px; height: 88px; border-radius: 44px; background: rgba(15, 23, 42, 0.04); }
.avatar-mask {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 30px;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
}
.avatar-tip { font-size: 11px; color: #fff; font-weight: 700; }
.input {
  height: 44px;
  line-height: 44px;
  border-radius: $ymd-v2-radius-md;
  border: 1px solid rgba(15, 23, 42, 0.10);
  padding: 0 12px;
  font-size: 14px;
  color: $ymd-v2-color-text;
  background: rgba(15, 23, 42, 0.02);
}
.ph { color: rgba(100, 116, 139, .7); }
.error { margin-top: 12px; padding: 10px 12px; border-radius: $ymd-v2-radius-md; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.18); }
.error-text { font-size: 12px; color: rgba(239, 68, 68, 1); font-weight: 700; }
.save { margin-top: 14px; border-radius: $ymd-v2-radius-md; height: 46px; line-height: 46px; font-weight: 800; }
.tap { opacity: .88; }

.sk { padding: 14px; }
.sk-list { display: flex; flex-direction: column; gap: 12px; }

.list { display: flex; flex-direction: column; gap: 12px; }
.post { padding: 14px; }
.post-content { font-size: 15px; line-height: 22px; color: $ymd-v2-color-text; white-space: pre-wrap; word-break: break-all; }
.meta { margin-top: 12px; display: flex; align-items: center; gap: 10px; color: $ymd-v2-color-muted; font-size: 12px; }
.loading { padding: 14px 0 28px; text-align: center; color: $ymd-v2-color-muted; font-size: 12px; }
</style>
