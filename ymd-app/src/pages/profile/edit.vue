<template>
  <view class="page ymd-page">
    <view class="card head">
      <view class="avatar-area" @click="chooseAvatar" hover-class="tap" hover-stay-time="70">
        <image class="avatar" :src="avatarPreview" mode="aspectFill" />
        <view class="avatar-mask">
          <text class="avatar-tip">更换头像</text>
        </view>
      </view>
      <view class="form">
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
        <view class="hint">
          <text class="hint-text">昵称将用于活动报名与社区展示</text>
        </view>
      </view>
    </view>

    <view v-if="errorText" class="error card">
      <text class="error-text">{{ errorText }}</text>
    </view>

    <button class="save ymd-btn" :disabled="saving" @click="save">
      {{ saving ? '保存中...' : '保存' }}
    </button>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import { BASE_URL, request } from '@/utils/request';
import { useUserStore } from '@/store/user';
import { TESTDATA_IMAGES } from '@/constants/testdataImages';

const userStore = useUserStore();

const nickname = ref('');
const phone = ref('');
const avatarLocalPath = ref('');
const avatarRemoteUrl = ref('');
const saving = ref(false);
const errorText = ref('');

const avatarPreview = computed(() => avatarLocalPath.value || avatarRemoteUrl.value || TESTDATA_IMAGES.logo);

const syncFromStore = () => {
  nickname.value = String(userStore.userInfo?.nickname || '');
  phone.value = String(userStore.userInfo?.phone || '');
  avatarRemoteUrl.value = String(userStore.userInfo?.avatar_url || '');
};

const ensureLogin = () => {
  if (userStore.token) return true;
  uni.showToast({ title: '请先登录', icon: 'none' });
  uni.navigateTo({ url: '/pages/auth/login' });
  return false;
};

onLoad(() => {
  if (!ensureLogin()) return;
  syncFromStore();
});

onShow(async () => {
  if (!userStore.token) return;
  try {
    const me = await request({ url: '/users/me', method: 'GET' });
    userStore.setUserInfo(me);
    syncFromStore();
  } catch {}
});

const chooseAvatar = () => {
  if (!ensureLogin()) return;
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

const save = async () => {
  if (!ensureLogin()) return;
  const v = validateNickname(nickname.value);
  if (!v.ok) {
    errorText.value = v.msg;
    uni.showToast({ title: v.msg, icon: 'none' });
    return;
  }
  const p = validatePhone(phone.value);
  if (!p.ok) {
    errorText.value = p.msg;
    uni.showToast({ title: p.msg, icon: 'none' });
    return;
  }
  saving.value = true;
  errorText.value = '';
  try {
    let avatarUrl = avatarRemoteUrl.value;
    if (avatarLocalPath.value) {
      avatarUrl = await uploadAvatar(avatarLocalPath.value);
    }
    const updated = await request({
      url: '/users/me',
      method: 'PUT',
      data: { nickname: v.value, avatar_url: avatarUrl, phone: p.value },
    });
    userStore.setUserInfo(updated);
    uni.showToast({ title: '保存成功', icon: 'success' });
    uni.navigateBack();
  } catch (e: any) {
    const msg = e?.data?.detail || e?.message || '保存失败';
    errorText.value = String(msg);
    uni.showToast({ title: String(msg), icon: 'none' });
  } finally {
    saving.value = false;
  }
};
</script>

<style scoped lang="scss">
.page { padding: $ymd-space-3 $ymd-space-3 28px; }
.card { background: $ymd-color-card; border: 1px solid $ymd-color-line; border-radius: $ymd-radius-lg; box-shadow: $ymd-shadow-xs; }
.head { padding: 14px; display: flex; gap: 14px; align-items: center; }
.avatar-area { width: 88px; height: 88px; border-radius: 44px; overflow: hidden; position: relative; }
.avatar { width: 88px; height: 88px; border-radius: 44px; background: rgba(15, 23, 42, 0.04); }
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
.form { flex: 1; display: flex; flex-direction: column; gap: 10px; }
.field { display: flex; flex-direction: column; gap: 8px; }
.label { font-size: 12px; color: $ymd-color-muted; font-weight: 700; }
.input {
  height: 44px;
  line-height: 44px;
  border-radius: $ymd-radius-md;
  border: 1px solid $ymd-color-line;
  padding: 0 12px;
  font-size: 14px;
  color: $ymd-color-text;
  background: rgba(15, 23, 42, 0.02);
}
.ph { color: rgba(100, 116, 139, .7); }
.hint { margin-top: -4px; }
.hint-text { font-size: 11px; color: $ymd-color-muted; }
.error { margin-top: 12px; padding: 12px 14px; }
.error-text { font-size: 12px; color: $uni-color-error; font-weight: 700; }
.save { margin-top: 14px; border-radius: $ymd-radius-md; height: 46px; line-height: 46px; font-weight: 800; }
.tap { opacity: .88; }
</style>
