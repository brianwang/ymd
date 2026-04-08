<template>
  <view class="container">
    <view class="preview" v-if="posterPath">
      <image class="poster" :src="posterPath" mode="widthFix" />
    </view>
    <view class="preview" v-else>
      <view class="placeholder">
        <text v-if="loading">生成中...</text>
        <text v-else>点击生成邀请海报</text>
      </view>
    </view>

    <view class="btns">
      <button class="btn primary" :disabled="loading" @click="generate">生成海报</button>
      <button class="btn" :disabled="loading || !posterPath" @click="save">保存到相册</button>
    </view>

    <canvas
      canvas-id="posterCanvas"
      id="posterCanvas"
      class="canvas"
      :style="{ width: canvasStyleW, height: canvasStyleH }"
    />
  </view>
</template>

<script setup lang="ts">
import { computed, getCurrentInstance, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { request } from '../../utils/request';
import { useUserStore } from '../../store/user';

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
  ctx.setFillStyle('#ffffff');
  ctx.fillRect(0, 0, canvasW, canvasH);

  ctx.setFillStyle('#111111');
  ctx.setFontSize(34);
  ctx.fillText('邀请好友，一起游牧', 40, 90);

  ctx.setFillStyle('#666666');
  ctx.setFontSize(22);
  ctx.fillText(`昵称：${userNickname.value}`, 40, 140);
  ctx.fillText(`积分：${userPoints.value}`, 40, 175);

  const qrSize = 320;
  const qrX = Math.floor((canvasW - qrSize) / 2);
  const qrY = 240;

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

  ctx.setFillStyle('#111111');
  ctx.setFontSize(20);
  ctx.fillText('扫码加入游牧岛', 220, qrY + qrSize + 55);

  ctx.setFillStyle('#999999');
  ctx.setFontSize(16);
  ctx.fillText('海报保存后发给好友或分享到朋友圈', 150, qrY + qrSize + 92);

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

<style scoped>
.container { padding: 16px; }
.preview { background: #fff; border-radius: 12px; padding: 12px; box-shadow: 0 6px 18px rgba(0,0,0,0.06); }
.poster { width: 100%; border-radius: 10px; }
.placeholder { height: 420px; display: flex; justify-content: center; align-items: center; color: #999; }
.btns { margin-top: 14px; display: flex; gap: 10px; }
.btn { flex: 1; font-size: 14px; }
.primary { background: #007AFF; color: #fff; }
.canvas { position: fixed; left: -9999px; top: -9999px; }
</style>
