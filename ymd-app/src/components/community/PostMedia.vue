<template>
  <!-- Video Preview (Feed) -->
  <view v-if="previewKind === 'video' && videoItem" class="video-preview">
    <image
      v-if="videoItem.cover_url"
      class="video-cover"
      :src="videoItem.cover_url"
      mode="aspectFill"
    />
    <view v-else class="video-cover placeholder">
      <u-icon name="play-circle-fill" size="48" color="rgba(15,23,42,0.2)"></u-icon>
    </view>
    <view class="video-play-icon">
      <u-icon name="play-circle-fill" size="48" color="rgba(255,255,255,0.8)"></u-icon>
    </view>
    <view class="video-badge">
      <text class="video-badge-text">{{ formatDuration(videoItem.duration) }}</text>
    </view>
  </view>

  <!-- Images (Feed) -->
  <view v-else-if="previewKind === 'images' && imageUrls.length" class="imgs-grid" :class="gridClass(imageUrls.length)">
    <image
      v-for="(url, idx) in imageUrls"
      :key="url + '-' + idx"
      class="img-item"
      :src="url"
      :mode="imageUrls.length === 1 ? 'widthFix' : 'aspectFill'"
      @click.stop="previewImages(idx)"
    />
  </view>

  <!-- Audio Preview (Feed) -->
  <view v-else-if="previewKind === 'audio' && audioItem" class="audio-preview">
    <PostAudioPlayer :src="audioItem.url" :title="audioItem.name || '音频'" :duration="audioItem.duration" />
  </view>

  <!-- Detail Mode -->
  <view v-else-if="mode === 'detail' && normalized.length" class="detail">
    <view v-for="(it, idx) in videos" :key="'video-' + it.url + '-' + idx" class="detail-item">
      <video class="video-player" :src="it.url" :poster="it.cover_url || ''" controls></video>
    </view>

    <view v-if="detailImageUrls.length" class="imgs-grid" :class="gridClass(detailImageUrls.length)">
      <image
        v-for="(url, idx) in detailImageUrls"
        :key="url + '-' + idx"
        class="img-item"
        :src="url"
        :mode="detailImageUrls.length === 1 ? 'widthFix' : 'aspectFill'"
        @click.stop="previewImages(idx)"
      />
    </view>

    <view v-for="(it, idx) in audios" :key="'audio-' + it.url + '-' + idx" class="detail-item">
      <PostAudioPlayer :src="it.url" :title="it.name || '音频'" :duration="it.duration" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import PostAudioPlayer from './PostAudioPlayer.vue';

export type PostMediaItem = {
  type: 'image' | 'video' | 'audio';
  url: string;
  cover_url?: string | null;
  duration?: number | null;
  name?: string | null;
};

const props = defineProps<{
  mode?: 'feed' | 'detail';
  media?: PostMediaItem[] | null;
  imageUrls?: string[] | null;
}>();

const mode = computed(() => props.mode || 'feed');

const normalized = computed<PostMediaItem[]>(() => {
  const m = Array.isArray(props.media) ? props.media.filter((x) => x && x.type && x.url) : [];
  if (m.length) return m;
  const imgs = Array.isArray(props.imageUrls) ? props.imageUrls.filter(Boolean) : [];
  return imgs.map((url) => ({ type: 'image', url }));
});

const imageUrls = computed(() => normalized.value.filter((x) => x.type === 'image').map((x) => x.url));
const videoItem = computed(() => normalized.value.find((x) => x.type === 'video') || null);
const audioItem = computed(() => normalized.value.find((x) => x.type === 'audio') || null);
const videos = computed(() => normalized.value.filter((x) => x.type === 'video'));
const audios = computed(() => normalized.value.filter((x) => x.type === 'audio'));
const detailImageUrls = computed(() => imageUrls.value);

const previewKind = computed(() => {
  if (mode.value === 'detail') return 'detail';
  if (videoItem.value) return 'video';
  if (imageUrls.value.length) return 'images';
  if (audioItem.value) return 'audio';
  return 'none';
});

const formatDuration = (sec?: number | null) => {
  if (!sec || !Number.isFinite(sec)) return '00:00';
  const v = Math.max(0, Math.floor(sec));
  const m = Math.floor(v / 60);
  const s = v % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
};

const previewImages = (current: number) => {
  const urls = imageUrls.value;
  if (!urls.length) return;
  uni.previewImage({ urls, current });
};

const gridClass = (count: number) => {
  if (count === 1) return 'grid-1';
  if (count === 2 || count === 4) return 'grid-2';
  return 'grid-3';
};
</script>

<style lang="scss" scoped>
.imgs-grid {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

/* 1张图：大图展示，最大宽度约占屏幕 70% */
.grid-1 {
  .img-item {
    width: 70%;
    max-height: 240px;
    border-radius: $ymd-v2-radius-md;
    background: rgba(15, 23, 42, 0.04);
  }
}

/* 2张图或4张图：2x2 排版 */
.grid-2 {
  width: 70%; /* 限制容器宽度以强制折行 */
  .img-item {
    width: calc(50% - 2px);
    aspect-ratio: 1 / 1;
    border-radius: $ymd-v2-radius-md;
    background: rgba(15, 23, 42, 0.04);
  }
}

/* 其他张图（3,5,6,7,8,9）：3x3 九宫格 */
.grid-3 {
  .img-item {
    width: calc(33.333% - 2.666px);
    aspect-ratio: 1 / 1;
    border-radius: $ymd-v2-radius-md;
    background: rgba(15, 23, 42, 0.04);
  }
}

.video-preview {
  margin-top: 12px;
  position: relative;
  border-radius: $ymd-v2-radius-md;
  overflow: hidden;
  background: rgba(15, 23, 42, 0.04);
  width: 70%;
  aspect-ratio: 16 / 9;
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
  right: 6px;
  bottom: 6px;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.55);
}
.video-badge-text {
  font-size: 11px;
  color: #fff;
  font-weight: 800;
}

.audio-preview {
  margin-top: 12px;
}

.detail {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.detail-item {
  width: 100%;
}
.video-player {
  width: 100%;
  height: 220px;
  border-radius: $ymd-v2-radius-md;
  background: rgba(15, 23, 42, 0.04);
}
</style>
