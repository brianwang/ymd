<template>
  <view class="ymd-page">
    <AppBar title="邀请海报" back />
    <view class="ymd-container ymd-page-inner">
      <Card class="preview" v-if="posterPath">
        <image class="poster" :src="posterPath" mode="widthFix" />
      </Card>
      <Card class="preview" v-else>
        <view class="placeholder">
          <image class="placeholder-bg" src="/static/placeholder/poster-bg-v2.png" mode="aspectFill" />
          <view class="placeholder-mask"></view>
          <text v-if="loading">生成中...</text>
          <text v-else>点击生成邀请海报</text>
        </view>
      </Card>

      <view class="btns">
        <button class="btn ymd-btn" :disabled="loading" @click="generate">生成海报</button>
        <button class="btn ymd-btn ghost" :disabled="loading || !posterPath" @click="save">保存到相册</button>
      </view>

      <canvas
        canvas-id="posterCanvas"
        id="posterCanvas"
        class="canvas"
        :style="{ width: canvasStyleW, height: canvasStyleH }"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, getCurrentInstance, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { request } from '../../utils/request';
import { useUserStore } from '../../store/user';
import AppBar from '@/components/ui/AppBar.vue';
import Card from '@/components/ui/Card.vue';

const userStore = useUserStore();
const instance = getCurrentInstance();

const loading = ref(false);
const posterPath = ref('');
const userNickname = ref('数字游民');
const userPoints = ref(0);
const qrBase64 = ref('');

const canvasW = 600;
const canvasH = 860;
const canvasStyleW = computed(() => `${canvasW / 2}px`);
const canvasStyleH = computed(() => `${canvasH / 2}px`);

const base64ToArrayBuffer = (base64: string) => {
  const fn = (uni as any).base64ToArrayBuffer;
  if (typeof fn === 'function') return fn(base64);
  const bin = atob(base64);
  const len = bin.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i += 1) bytes[i] = bin.charCodeAt(i);
  return bytes.buffer;
};

const base64ToPath = async (base64: string) => {
  const raw = base64.startsWith('data:') ? base64.split(',')[1] || '' : base64;
  const dataUrl = base64.startsWith('data:') ? base64 : `data:image/png;base64,${raw}`;
  const fsm = (uni as any).getFileSystemManager?.();
  const userDataPath = (uni as any).env?.USER_DATA_PATH;
  if (fsm && userDataPath) {
    const filePath = `${userDataPath}/invite_qrcode_${Date.now()}.png`;
    const buffer = base64ToArrayBuffer(raw);
    await new Promise<void>((resolve, reject) => {
      fsm.writeFile({
        filePath,
        data: buffer,
        success: () => resolve(),
        fail: (e: any) => reject(e),
      });
    });
    return filePath;
  }
  return dataUrl;
};

const fetchMe = async () => {
  const me: any = await request({ url: '/users/me', method: 'GET' });
  userNickname.value = me?.nickname || '数字游民';
  userPoints.value = me?.points || 0;
  userStore.setUserInfo(me);
};

const fetchQr = async () => {
  const res: any = await request({ url: '/users/invite/qrcode', method: 'GET' });
  qrBase64.value = res?.png_base64 || '';
};

const canvasToTemp = async () => {
  return new Promise<string>((resolve, reject) => {
    uni.canvasToTempFilePath(
      {
        canvasId: 'posterCanvas',
        width: canvasW,
        height: canvasH,
        destWidth: canvasW,
        destHeight: canvasH,
        fileType: 'png',
        success: (r) => resolve(r.tempFilePath),
        fail: (e) => reject(e),
      },
      instance as any
    );
  });
};

const drawPoster = async () => {
  const ctx = uni.createCanvasContext('posterCanvas', instance as any);
  ctx.setFillStyle('#F7FAFB');
  ctx.fillRect(0, 0, canvasW, canvasH);

  const g = (ctx as any).createLinearGradient(0, 0, canvasW, 180);
  g.addColorStop(0, '#12C8C0');
  g.addColorStop(1, '#6D5EFC');
  (ctx as any).setFillStyle(g);
  ctx.fillRect(0, 0, canvasW, 210);

  ctx.setFillStyle('rgba(255,255,255,0.96)');
  ctx.setFontSize(36);
  ctx.fillText('邀请好友，一起游牧', 40, 92);

  ctx.setFillStyle('rgba(255,255,255,0.92)');
  ctx.setFontSize(20);
  ctx.fillText(`昵称：${userNickname.value}`, 40, 140);
  ctx.fillText(`积分：${userPoints.value}`, 40, 172);

  const qrSize = 320;
  const qrX = Math.floor((canvasW - qrSize) / 2);
  const qrY = 270;

  const qrPath = await base64ToPath(qrBase64.value);
  await new Promise<void>((resolve, reject) => {
    uni.getImageInfo({
      src: qrPath,
      success: (img) => {
        ctx.drawImage(img.path, qrX, qrY, qrSize, qrSize);
        resolve();
      },
      fail: (e) => reject(e),
    });
  });

  ctx.setFillStyle('#0B1220');
  ctx.setFontSize(20);
  ctx.fillText('扫码加入游牧岛', 220, qrY + qrSize + 55);

  ctx.setFillStyle('#64748B');
  ctx.setFontSize(16);
  ctx.fillText('保存后发给好友或分享到朋友圈', 170, qrY + qrSize + 92);

  await new Promise<void>((resolve) => {
    ctx.draw(false, () => resolve());
  });
};

const generate = async () => {
  if (!userStore.token) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    uni.switchTab({ url: '/pages/profile/index' });
    return;
  }
  loading.value = true;
  try {
    posterPath.value = '';
    await Promise.all([fetchMe(), fetchQr()]);
    if (!qrBase64.value) {
      uni.showToast({ title: '获取二维码失败', icon: 'none' });
      return;
    }
    await drawPoster();
    posterPath.value = await canvasToTemp();
  } finally {
    loading.value = false;
  }
};

const save = async () => {
  if (!posterPath.value) return;
  try {
    await new Promise<void>((resolve, reject) => {
      uni.saveImageToPhotosAlbum({
        filePath: posterPath.value,
        success: () => resolve(),
        fail: (e) => reject(e),
      });
    });
    uni.showToast({ title: '已保存到相册', icon: 'success' });
  } catch (e: any) {
    uni.showModal({
      title: '无法保存',
      content: '请在设置中允许保存到相册后重试',
      success: (r) => {
        if (r.confirm) uni.openSetting({});
      },
    });
  }
};

onShow(() => {
  if (userStore.token && !posterPath.value && !loading.value) generate();
});
</script>

<style scoped lang="scss">
.preview { padding: 12px; overflow: hidden; box-shadow: $ymd-v2-shadow-sm; }
.poster { width: 100%; border-radius: $ymd-v2-radius-md; }
.placeholder { height: 420px; position: relative; display: flex; justify-content: center; align-items: center; color: rgba(255,255,255,0.95); font-weight: 800; }
.placeholder-bg { position: absolute; inset: 0; width: 100%; height: 100%; }
.placeholder-mask { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(0,0,0,.10), rgba(0,0,0,.42)); }
.placeholder text { position: relative; z-index: 1; }
.btns { margin-top: 14px; display: flex; gap: 10px; }
.btn { flex: 1; font-size: 14px; height: 44px; line-height: 44px; font-weight: 700; border-radius: $ymd-radius-md; }
.canvas { position: fixed; left: -9999px; top: -9999px; }
</style>
