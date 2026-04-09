<template>
  <view class="audio" @click.stop="noop">
    <view class="left">
      <view class="title">{{ title || '音频' }}</view>
      <view class="sub">
        <text class="time">{{ formatTime(currentTime) }}</text>
        <text class="sep">/</text>
        <text class="time">{{ formatTime(resolvedDuration) }}</text>
      </view>
    </view>
    <view class="right">
      <button class="btn ymd-btn ghost" size="mini" :disabled="loading" :loading="loading" @click.stop="toggle">
        <text class="icon">{{ playing ? '暂停' : '播放' }}</text>
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';

const props = defineProps<{
  src: string;
  title?: string | null;
  duration?: number | null;
}>();

const noop = () => {};

const playing = ref(false);
const loading = ref(false);
const currentTime = ref(0);
const innerDuration = ref<number | null>(null);

let ctx: UniApp.InnerAudioContext | null = null;
let canplayTimer: any = null;

const resolvedDuration = computed(() => {
  const d = typeof props.duration === 'number' && Number.isFinite(props.duration) ? props.duration : null;
  return d ?? innerDuration.value ?? 0;
});

const formatTime = (sec: number) => {
  const v = Number.isFinite(sec) ? Math.max(0, Math.floor(sec)) : 0;
  const m = Math.floor(v / 60);
  const s = v % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
};

const cleanup = () => {
  if (canplayTimer) {
    clearTimeout(canplayTimer);
    canplayTimer = null;
  }
  if (ctx) {
    try {
      ctx.stop();
      ctx.destroy();
    } catch {}
    ctx = null;
  }
  playing.value = false;
  loading.value = false;
  currentTime.value = 0;
  innerDuration.value = null;
};

const init = () => {
  cleanup();
  if (!props.src) return;
  ctx = uni.createInnerAudioContext();
  ctx.autoplay = false;
  ctx.src = props.src;
  loading.value = true;

  ctx.onCanplay(() => {
    // duration 可能需要延后才能拿到
    canplayTimer = setTimeout(() => {
      if (!ctx) return;
      const d = Number((ctx as any).duration);
      if (Number.isFinite(d) && d > 0) innerDuration.value = d;
      loading.value = false;
    }, 200);
  });
  ctx.onPlay(() => {
    playing.value = true;
    loading.value = false;
  });
  ctx.onPause(() => {
    playing.value = false;
  });
  ctx.onStop(() => {
    playing.value = false;
    currentTime.value = 0;
  });
  ctx.onEnded(() => {
    playing.value = false;
    currentTime.value = 0;
  });
  ctx.onTimeUpdate(() => {
    if (!ctx) return;
    const t = Number((ctx as any).currentTime);
    if (Number.isFinite(t)) currentTime.value = t;
  });
  ctx.onError(() => {
    loading.value = false;
    playing.value = false;
    uni.showToast({ title: '音频播放失败', icon: 'none' });
  });
};

const toggle = async () => {
  if (!ctx) init();
  if (!ctx) return;
  try {
    if (playing.value) ctx.pause();
    else ctx.play();
  } catch {
    uni.showToast({ title: '音频播放失败', icon: 'none' });
  }
};

onMounted(() => init());
watch(
  () => props.src,
  () => init(),
);
onBeforeUnmount(() => cleanup());
</script>

<style lang="scss" scoped>
.audio {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border-radius: $ymd-v2-radius-md;
  border: 1px solid $ymd-v2-color-line;
  background: rgba(15, 23, 42, 0.02);
}
.left {
  flex: 1;
  min-width: 0;
}
.title {
  font-size: 13px;
  font-weight: 900;
  color: $ymd-v2-color-text;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sub {
  margin-top: 4px;
  font-size: 12px;
  color: $ymd-v2-color-muted;
  display: flex;
  align-items: center;
  gap: 6px;
}
.sep {
  opacity: 0.6;
}
.btn {
  height: 32px;
  line-height: 32px;
  padding: 0 12px;
  font-size: 12px;
  font-weight: 800;
}
</style>
