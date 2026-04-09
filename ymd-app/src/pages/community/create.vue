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

      <view class="meta-editor">
        <view class="meta-row" @click="chooseLocation">
          <text class="meta-icon">📍</text>
          <text class="meta-label">{{ location?.name ? location.name : '添加位置' }}</text>
          <view v-if="location" class="meta-right" @click.stop="clearLocation">
            <text class="meta-clear">移除</text>
          </view>
        </view>

        <view class="meta-row tags-row" @click="focusTagInput">
          <text class="meta-icon">🏷</text>
          <view class="tags-wrap">
            <view v-if="mergedTags.length === 0" class="tags-placeholder">
              <text class="tags-placeholder-text">添加标签（正文里的 #标签 会自动识别）</text>
            </view>
            <view v-else class="tags-chips">
              <view v-for="t in manualTags" :key="'m-' + t" class="tag-chip tag-chip-manual" @click.stop="removeManualTag(t)">
                <text class="tag-text">#{{ t }}</text>
                <text class="tag-x">×</text>
              </view>
              <view v-for="t in parsedTags" :key="'p-' + t" class="tag-chip tag-chip-parsed">
                <text class="tag-text">#{{ t }}</text>
              </view>
            </view>
            <input
              ref="tagInputRef"
              v-model="tagInput"
              class="tag-input"
              placeholder="输入标签，回车添加"
              confirm-type="done"
              :maxlength="24"
              @confirm="addTagFromInput"
            />
          </view>
          <view class="meta-right">
            <text class="tags-count" :class="{ danger: mergedTags.length > 10 }">{{ mergedTags.length }}/10</text>
          </view>
        </view>
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

    <view v-if="isRecording" class="recording-panel">
      <view class="recording-inner ymd-container">
        <view class="rec-left">
          <view class="rec-dot"></view>
          <text class="rec-text">录音中 {{ formatDuration(recordSec) }}</text>
        </view>
        <view class="rec-actions">
          <button class="rec-btn ymd-btn ghost" size="mini" @click="cancelRecording">取消</button>
          <button class="rec-btn ymd-btn" size="mini" @click="stopRecording">停止</button>
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
        <view class="icon-btn" :class="{ disabled: !canPickAudio || isRecording }" @click="onAudioAction">
          <u-icon name="mic" size="28" :color="canPickAudio ? '#334155' : '#cbd5e1'"></u-icon>
        </view>
      </view>
      <button class="submit-btn ymd-btn" :loading="submitting" :disabled="submitting || isRecording || (!content.trim() && !hasMedia)" @click="submit">发布</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount } from 'vue';
import { BASE_URL, ensureLoggedIn, request } from '@/utils/request';
import AppBar from '@/components/ui/AppBar.vue';
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

type PostLocation = {
  name: string;
  address?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  raw?: any;
};

const content = ref('');
const images = ref<LocalImage[]>([]);
const video = ref<LocalVideo | null>(null);
const audio = ref<LocalAudio | null>(null);
const location = ref<PostLocation | null>(null);
const manualTags = ref<string[]>([]);
const tagInput = ref('');
const tagInputRef = ref<any>(null);

const submitting = ref(false);
const isRecording = ref(false);
const recordSec = ref(0);
let recordTimer: any = null;
let recorder: any = null;
let cancelNextStop = false;

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

const normalizeTag = (tag: string) => {
  const raw = String(tag || '').trim();
  const noHash = raw.startsWith('#') ? raw.slice(1).trim() : raw;
  // 仅 ASCII 字母小写化
  return noHash.replace(/[A-Z]/g, (c) => c.toLowerCase());
};

const TAG_ALLOWED_RE = /^[0-9A-Za-z_\u4e00-\u9fff·-]+$/;

const extractHashtagsFromContent = (text: string) => {
  const out: string[] = [];
  const s = text || '';
  // 兼容：部分 JS 引擎不支持 lookbehind，因此用 RegExp 构造并降级
  let re: RegExp;
  try {
    re = new RegExp('(?<![0-9A-Za-z_])#([0-9A-Za-z_\\u4e00-\\u9fff·-]{1,64})', 'g');
  } catch {
    re = /#([0-9A-Za-z_\u4e00-\u9fff·-]{1,64})/g;
  }
  const matches = s.matchAll(re);
  for (const m of matches) {
    const v = normalizeTag(m?.[1] || '');
    if (!v) continue;
    if (out.includes(v)) continue;
    out.push(v);
  }
  return out;
};

const parsedTags = computed(() => extractHashtagsFromContent(content.value));

const mergedTags = computed(() => {
  const merged: string[] = [];
  const push = (t: string) => {
    const v = normalizeTag(t);
    if (!v) return;
    if (merged.includes(v)) return;
    merged.push(v);
  };
  for (const t of manualTags.value) push(t);
  for (const t of parsedTags.value) push(t);
  return merged;
});

const validateOneTag = (t: string) => {
  if (!t) return '标签不能为空';
  if (t.length > 20) return '标签过长：单个最多 20 个字符';
  if (!TAG_ALLOWED_RE.test(t)) return '标签包含非法字符：仅支持中文/英文/数字/下划线/连字符';
  return '';
};

const addTagFromInput = () => {
  const v = normalizeTag(tagInput.value);
  if (!v) return;
  const err = validateOneTag(v);
  if (err) {
    uni.showToast({ title: err, icon: 'none' });
    return;
  }
  if (mergedTags.value.includes(v)) {
    tagInput.value = '';
    return;
  }
  if (mergedTags.value.length >= 10) {
    uni.showToast({ title: '标签数量过多：最多支持 10 个（含正文 #标签）', icon: 'none' });
    return;
  }
  manualTags.value = manualTags.value.concat(v);
  tagInput.value = '';
};

const removeManualTag = (t: string) => {
  manualTags.value = manualTags.value.filter((x) => x !== t);
};

const focusTagInput = () => {
  try {
    tagInputRef.value?.focus?.();
  } catch {}
};

const chooseLocation = () => {
  if (!ensureLoggedIn()) return;
  const choose = (uni as any).chooseLocation;
  if (typeof choose !== 'function') {
    uni.showToast({ title: '当前环境不支持选择位置', icon: 'none' });
    return;
  }
  choose({
    success: (res: any) => {
      const name = String(res?.name || '').trim();
      if (!name) return;
      location.value = {
        name,
        address: res?.address ? String(res.address) : null,
        latitude: typeof res?.latitude === 'number' ? res.latitude : null,
        longitude: typeof res?.longitude === 'number' ? res.longitude : null,
        raw: res || null,
      };
    },
    fail: () => {
      // 用户取消/权限失败：不提示
    },
  });
};

const clearLocation = () => {
  location.value = null;
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

const initRecorder = () => {
  if (recorder) return;
  const getter = (uni as any).getRecorderManager;
  if (typeof getter !== 'function') return;
  recorder = getter();
  recorder.onStop(async (res: any) => {
    if (recordTimer) {
      clearInterval(recordTimer);
      recordTimer = null;
    }
    const tempFilePath = res?.tempFilePath;
    const cancelled = cancelNextStop;
    cancelNextStop = false;
    isRecording.value = false;

    if (cancelled) return;
    if (!tempFilePath) return;
    audio.value = { path: tempFilePath, name: '语音', uploading: false, duration: null };
    // 以探测为准；探测失败则使用录制计时
    const d = await probeAudioDuration(tempFilePath);
    audio.value.duration = d ?? recordSec.value ?? null;
  });
  recorder.onError(() => {
    if (recordTimer) {
      clearInterval(recordTimer);
      recordTimer = null;
    }
    isRecording.value = false;
    cancelNextStop = false;
    uni.showToast({ title: '录音失败，请检查权限', icon: 'none' });
  });
};

const startRecording = () => {
  if (!ensureLoggedIn()) return;
  if (!canPickAudio.value) {
    uni.showToast({ title: '只能选择一种媒体类型', icon: 'none' });
    return;
  }
  const run = () => {
    initRecorder();
    if (!recorder) {
      uni.showToast({ title: '当前环境不支持录音', icon: 'none' });
      return;
    }
    if (isRecording.value) return;
    recordSec.value = 0;
    isRecording.value = true;
    cancelNextStop = false;
    recordTimer = setInterval(() => {
      recordSec.value += 1;
    }, 1000);
    try {
      recorder.start({
        duration: 60 * 1000,
        format: 'mp3',
      });
    } catch {
      if (recordTimer) {
        clearInterval(recordTimer);
        recordTimer = null;
      }
      isRecording.value = false;
      uni.showToast({ title: '无法开始录音', icon: 'none' });
    }
  };
  if (audio.value) {
    uni.showModal({
      title: '替换语音',
      content: '已选择音频，是否替换为新录制的语音？',
      success: (r) => {
        if (r.confirm) run();
      },
    });
    return;
  }
  run();
};

const stopRecording = () => {
  if (!recorder || !isRecording.value) return;
  try {
    recorder.stop();
  } catch {}
};

const cancelRecording = () => {
  if (!recorder || !isRecording.value) return;
  cancelNextStop = true;
  try {
    recorder.stop();
  } catch {}
};

const onAudioAction = () => {
  if (!ensureLoggedIn()) return;
  if (!canPickAudio.value) {
    uni.showToast({ title: '只能选择一种媒体类型', icon: 'none' });
    return;
  }
  const canRecord = typeof (uni as any).getRecorderManager === 'function';
  const items = canRecord ? ['录制语音', '选择音频文件'] : ['选择音频文件'];
  uni.showActionSheet({
    itemList: items,
    success: (res) => {
      const idx = res.tapIndex;
      if (canRecord) {
        if (idx === 0) startRecording();
        else pickAudio();
      } else {
        if (idx === 0) pickAudio();
      }
    },
  });
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
  if (mergedTags.value.length > 10) {
    uni.showToast({ title: '标签数量过多：最多支持 10 个（含正文 #标签）', icon: 'none' });
    return;
  }
  for (const t of mergedTags.value) {
    const err = validateOneTag(t);
    if (err) {
      uni.showToast({ title: err, icon: 'none' });
      return;
    }
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
      data: {
        content: content.value.trim(),
        media,
        image_urls: imageUrls,
        location: location.value
          ? {
              name: location.value.name,
              address: location.value.address || null,
              latitude: location.value.latitude ?? null,
              longitude: location.value.longitude ?? null,
              raw: location.value.raw || null,
            }
          : null,
        // 显式 tags 仅提交“手动添加”的部分；正文 #标签 由后端解析合并
        tags: manualTags.value,
      },
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

onBeforeUnmount(() => {
  try {
    if (recordTimer) clearInterval(recordTimer);
  } catch {}
  recordTimer = null;
  // recorderManager 无 destroy API，避免解绑带来的兼容问题
});
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

.meta-editor {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.meta-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: $ymd-v2-radius-md;
  background: rgba(15, 23, 42, 0.03);
}
.meta-icon {
  width: 18px;
  font-size: 14px;
  line-height: 18px;
  margin-top: 2px;
}
.meta-label {
  flex: 1;
  font-size: 13px;
  line-height: 18px;
  color: $ymd-v2-color-text;
}
.meta-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.meta-clear {
  font-size: 12px;
  color: $ymd-v2-color-muted;
}

.tags-row {
  align-items: flex-start;
}
.tags-wrap {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.tags-placeholder-text {
  font-size: 12px;
  color: $ymd-v2-color-muted;
}
.tags-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  line-height: 16px;
}
.tag-chip-manual {
  background: rgba(99, 102, 241, 0.10);
  color: $ymd-v2-color-accent-2;
}
.tag-chip-parsed {
  background: rgba(15, 23, 42, 0.06);
  color: $ymd-v2-color-muted;
}
.tag-text {
  font-weight: 700;
}
.tag-x {
  font-size: 14px;
  line-height: 14px;
  opacity: 0.8;
}
.tag-input {
  min-width: 120px;
  height: 28px;
  padding: 0 8px;
  font-size: 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.9);
  color: $ymd-v2-color-text;
}
.tags-count {
  font-size: 12px;
  color: $ymd-v2-color-muted;
}
.tags-count.danger {
  color: #dc2626;
  font-weight: 800;
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

.recording-panel {
  position: fixed;
  left: 0;
  right: 0;
  bottom: calc(56px + env(safe-area-inset-bottom));
  padding: 0 16px;
  z-index: 50;
}
.recording-inner {
  padding: 10px 12px;
  border-radius: $ymd-v2-radius-md;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(15, 23, 42, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.rec-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.rec-dot {
  width: 8px;
  height: 8px;
  border-radius: 4px;
  background: #ef4444;
}
.rec-text {
  font-size: 13px;
  color: $ymd-v2-color-text;
  font-weight: 800;
}
.rec-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.rec-btn {
  height: 34px;
  line-height: 34px;
  padding: 0 14px;
  font-size: 12px;
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
