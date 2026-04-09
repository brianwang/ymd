<template>
  <view class="ymd-page create-page">
    <AppBar title="发帖" back />
    <view class="ymd-container ymd-page-inner content-area">
      <view class="field">
        <textarea
          v-model="content"
          class="textarea"
          placeholder="分享点什么..."
          maxlength="1000"
          :auto-height="false"
        />
      </view>

      <view class="preview-area">
        <view v-if="images.length > 0" class="imgs-grid">
          <view v-for="(it, idx) in images" :key="it.path" class="img-item">
            <image class="img" :src="it.path" mode="aspectFill" />
            <view class="img-mask" v-if="it.uploading">
              <text class="img-mask-text">上传中</text>
            </view>
            <view class="remove" @click.stop="removeImage(idx)">×</view>
          </view>
          <view v-if="images.length < 9" class="add-img" @click="pickImages">
            <u-icon name="plus" size="24" color="#94a3b8"></u-icon>
          </view>
        </view>

        <view v-if="video" class="video-card">
          <image v-if="video.thumbPath" class="video-cover" :src="video.thumbPath" mode="aspectFill" />
          <view v-else class="video-cover placeholder">
            <u-icon name="play-circle-fill" size="48" color="rgba(15,23,42,0.2)"></u-icon>
          </view>
          <view class="video-play-icon" v-if="video.thumbPath">
            <u-icon name="play-circle-fill" size="48" color="rgba(255,255,255,0.8)"></u-icon>
          </view>
          <view class="video-badge">
            <text class="video-badge-text">{{ formatDuration(video.duration) }}</text>
          </view>
          <view class="img-mask" v-if="video.uploading || video.uploadingCover">
            <text class="img-mask-text">上传中</text>
          </view>
          <view class="remove" @click.stop="removeVideo">×</view>
        </view>

        <view v-if="audio" class="audio-card">
          <PostAudioPlayer :src="audio.path" :title="audio.name" :duration="audio.duration" />
          <view class="img-mask" v-if="audio.uploading">
            <text class="img-mask-text">上传中</text>
          </view>
          <view class="remove audio-remove" @click.stop="removeAudio">×</view>
        </view>
      </view>
    </view>

    <!-- 底部工具栏 -->
    <view class="bottom-toolbar">
      <view class="toolbar-icons">
        <view class="icon-btn" :class="{ disabled: !canPickImage }" @click="pickImages">
          <u-icon name="photo" size="28" :color="canPickImage ? '#334155' : '#cbd5e1'"></u-icon>
        </view>
        <view class="icon-btn" :class="{ disabled: !canPickVideo }" @click="pickVideo">
          <u-icon name="play-circle" size="28" :color="canPickVideo ? '#334155' : '#cbd5e1'"></u-icon>
        </view>
        <view class="icon-btn" :class="{ disabled: !canPickAudio }" @click="pickAudio">
          <u-icon name="mic" size="28" :color="canPickAudio ? '#334155' : '#cbd5e1'"></u-icon>
        </view>
      </view>
      <button class="submit-btn ymd-btn" :loading="submitting" :disabled="submitting || (!content.trim() && !hasMedia)" @click="submit">发布</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { BASE_URL, ensureLoggedIn, request } from '@/utils/request';
import AppBar from '@/components/ui/AppBar.vue';
import Card from '@/components/ui/Card.vue';
import PostAudioPlayer from '@/components/community/PostAudioPlayer.vue';

type LocalImage = {
  path: string;
  uploading: boolean;
  url?: string;
};

type LocalVideo = {
  path: string;
  thumbPath?: string;
  uploading: boolean;
  uploadingCover: boolean;
  url?: string;
  coverUrl?: string;
  duration?: number;
};

type LocalAudio = {
  path: string;
  name: string;
  uploading: boolean;
  url?: string;
  duration?: number | null;
};

const content = ref('');
const images = ref<LocalImage[]>([]);
const video = ref<LocalVideo | null>(null);
const audio = ref<LocalAudio | null>(null);
const submitting = ref(false);

const canPickImage = computed(() => !video.value && !audio.value);
const canPickVideo = computed(() => images.value.length === 0 && !audio.value);
const canPickAudio = computed(() => images.value.length === 0 && !video.value);
const hasMedia = computed(() => images.value.length > 0 || !!video.value || !!audio.value);

const pickImages = () => {
  if (!ensureLoggedIn()) return;
  if (!canPickImage.value) {
    uni.showToast({ title: '只能选择一种媒体类型', icon: 'none' });
    return;
  }
  uni.chooseImage({
    count: 9 - images.value.length,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const paths = (res.tempFilePaths || []) as string[];
      const next = paths.map((p: string) => ({ path: p, uploading: false })) as LocalImage[];
      images.value = images.value.concat(next);
    },
  });
};

const removeImage = (index: number) => {
  images.value.splice(index, 1);
};

const formatDuration = (sec?: number | null) => {
  if (!sec || !Number.isFinite(sec)) return '00:00';
  const v = Math.max(0, Math.floor(sec));
  const m = Math.floor(v / 60);
  const s = v % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
};

const pickVideo = () => {
  if (!ensureLoggedIn()) return;
  if (!canPickVideo.value) {
    uni.showToast({ title: '只能选择一种媒体类型', icon: 'none' });
    return;
  }
  const run = () => {
    uni.chooseVideo({
      sourceType: ['album', 'camera'],
      compressed: true,
      success: (res: any) => {
        const p = res?.tempFilePath;
        if (!p) return;
        video.value = {
          path: p,
          thumbPath: res?.thumbTempFilePath,
          duration: typeof res?.duration === 'number' ? res.duration : undefined,
          uploading: false,
          uploadingCover: false,
        };
      },
    });
  };
  if (video.value) {
    uni.showModal({
      title: '替换视频',
      content: '已选择视频，是否替换？',
      success: (r) => {
        if (r.confirm) run();
      },
    });
    return;
  }
  run();
};

const probeAudioDuration = (src: string) => {
  return new Promise<number | null>((resolve) => {
    try {
      const ctx = uni.createInnerAudioContext();
      ctx.autoplay = false;
      ctx.src = src;
      let done = false;
      const finish = (v: number | null) => {
        if (done) return;
        done = true;
        try {
          ctx.stop();
          ctx.destroy();
        } catch {}
        resolve(v);
      };
      const timer = setTimeout(() => finish(null), 1500);
      ctx.onCanplay(() => {
        setTimeout(() => {
          clearTimeout(timer);
          const d = Number((ctx as any).duration);
          finish(Number.isFinite(d) && d > 0 ? d : null);
        }, 200);
      });
      ctx.onError(() => {
        clearTimeout(timer);
        finish(null);
      });
    } catch {
      resolve(null);
    }
  });
};

const pickAudio = () => {
  if (!ensureLoggedIn()) return;
  if (!canPickAudio.value) {
    uni.showToast({ title: '只能选择一种媒体类型', icon: 'none' });
    return;
  }
  const run = () => {
    const uniAny = uni as any;
    const choose = uniAny.chooseFile || uniAny.chooseMessageFile;
    if (!choose) {
      uni.showToast({ title: '当前环境不支持选择音频', icon: 'none' });
      return;
    }
    choose({
      count: 1,
      extension: ['mp3', 'm4a', 'wav', 'aac', 'ogg', 'flac'],
      success: async (res: any) => {
        const f = res?.tempFiles?.[0];
        const p = f?.path || f?.tempFilePath;
        if (!p) return;
        const name = String(f?.name || '音频');
        audio.value = { path: p, name, uploading: false, duration: null };
        audio.value.duration = await probeAudioDuration(p);
      },
    });
  };
  if (audio.value) {
    uni.showModal({
      title: '替换音频',
      content: '已选择音频，是否替换？',
      success: (r) => {
        if (r.confirm) run();
      },
    });
    return;
  }
  run();
};

const removeVideo = () => {
  video.value = null;
};

const removeAudio = () => {
  audio.value = null;
};

const uploadOne = (filePath: string) => {
  return new Promise<string>((resolve, reject) => {
    const token = uni.getStorageSync('token');
    uni.uploadFile({
      url: BASE_URL + '/media/upload',
      filePath,
      name: 'file',
      header: {
        Authorization: token ? `Bearer ${token}` : '',
      },
      success: (res) => {
        try {
          const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data;
          if (!data?.url) throw new Error('invalid response');
          resolve(data.url);
        } catch (e) {
          reject(e);
        }
      },
      fail: (err) => reject(err),
    });
  });
};

const submit = async () => {
  if (!ensureLoggedIn()) return;
  if (submitting.value) return;
  if (!content.value.trim() && images.value.length === 0 && !video.value && !audio.value) {
    uni.showToast({ title: '请输入内容或选择媒体', icon: 'none' });
    return;
  }
  submitting.value = true;
  uni.showLoading({ title: '发布中' });
  try {
    const imageUrls: string[] = [];
    for (const it of images.value) {
      if (it.url) {
        imageUrls.push(it.url);
        continue;
      }
      it.uploading = true;
      const url = await uploadOne(it.path);
      it.url = url;
      it.uploading = false;
      imageUrls.push(url);
    }

    let videoUrl = video.value?.url || '';
    let videoCoverUrl = video.value?.coverUrl || '';
    if (video.value) {
      if (!videoUrl) {
        video.value.uploading = true;
        videoUrl = await uploadOne(video.value.path);
        video.value.url = videoUrl;
        video.value.uploading = false;
      }
      if (video.value.thumbPath && !videoCoverUrl) {
        video.value.uploadingCover = true;
        videoCoverUrl = await uploadOne(video.value.thumbPath);
        video.value.coverUrl = videoCoverUrl;
        video.value.uploadingCover = false;
      }
    }

    let audioUrl = audio.value?.url || '';
    if (audio.value && !audioUrl) {
      audio.value.uploading = true;
      audioUrl = await uploadOne(audio.value.path);
      audio.value.url = audioUrl;
      audio.value.uploading = false;
    }

    const media: Array<any> = [];
    for (const url of imageUrls) media.push({ type: 'image', url });
    if (videoUrl) {
      media.push({
        type: 'video',
        url: videoUrl,
        cover_url: videoCoverUrl || null,
        duration: video.value?.duration ?? null,
      });
    }
    if (audioUrl) {
      media.push({
        type: 'audio',
        url: audioUrl,
        name: audio.value?.name || null,
        duration: audio.value?.duration ?? null,
      });
    }

    await request({
      url: '/posts',
      method: 'POST',
      data: { content: content.value.trim(), media, image_urls: imageUrls },
    });
    uni.hideLoading();
    uni.showToast({ title: '发布成功', icon: 'success' });
    setTimeout(() => {
      uni.navigateBack();
    }, 300);
  } catch (e) {
    uni.hideLoading();
  } finally {
    submitting.value = false;
    images.value = images.value.map((it) => ({ ...it, uploading: false }));
    if (video.value) {
      video.value = { ...video.value, uploading: false, uploadingCover: false };
    }
    if (audio.value) {
      audio.value = { ...audio.value, uploading: false };
    }
  }
};
</script>

<style lang="scss">
.create-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #fff; /* 纯白背景适合发帖页 */
}
.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow-y: auto;
}
.field {
  width: 100%;
}
.textarea {
  width: 100%;
  height: 160px;
  font-size: 16px;
  line-height: 1.5;
  color: $ymd-v2-color-text;
}
.preview-area {
  margin-top: 16px;
  padding-bottom: 20px;
}
.imgs-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.img-item, .add-img {
  width: calc(33.333% - 5.333px);
  aspect-ratio: 1 / 1;
  position: relative;
}
.img {
  width: 100%;
  height: 100%;
  border-radius: $ymd-v2-radius-md;
  background: rgba(15, 23, 42, 0.04);
}
.img-mask {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  border-radius: $ymd-v2-radius-md;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
}
.img-mask-text {
  color: #fff;
  font-size: 12px;
}
.remove {
  position: absolute;
  right: 4px;
  top: 4px;
  width: 20px;
  height: 20px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  text-align: center;
  line-height: 18px;
  font-size: 16px;
  z-index: 10;
}
.add-img {
  border-radius: $ymd-v2-radius-md;
  background: rgba(15, 23, 42, 0.04);
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-card {
  position: relative;
  width: 70%;
  aspect-ratio: 16 / 9;
  border-radius: $ymd-v2-radius-md;
  overflow: hidden;
  background: rgba(15, 23, 42, 0.04);
}
.video-cover {
  width: 100%;
  height: 100%;
}
.video-play-icon {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
}
.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
}
.video-badge {
  position: absolute;
  right: 8px;
  bottom: 8px;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.55);
}
.video-badge-text {
  font-size: 11px;
  color: #fff;
  font-weight: 800;
}

.audio-card {
  position: relative;
  width: 100%;
}
.audio-remove {
  right: 0px;
  top: -10px;
}

.bottom-toolbar {
  border-top: 1px solid $ymd-v2-color-line;
  padding: 10px 16px;
  padding-bottom: calc(10px + env(safe-area-inset-bottom));
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
}
.toolbar-icons {
  display: flex;
  align-items: center;
  gap: 20px;
}
.icon-btn {
  padding: 4px;
}
.icon-btn.disabled {
  opacity: 0.5;
}
.submit-btn {
  margin: 0;
  height: 36px;
  line-height: 36px;
  padding: 0 20px;
  font-weight: 800;
  border-radius: 18px;
  font-size: 14px;
}
</style>
