<template>
  <view class="sk" :style="{ width, height, borderRadius }" />
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    width?: string;
    height?: string;
    borderRadius?: string;
  }>(),
  {
    width: '100%',
    height: '14px',
    borderRadius: '12px',
  }
);
</script>

<style scoped lang="scss">
.sk {
  position: relative;
  overflow: hidden;
  background: rgba(15, 23, 42, 0.06);
}

.sk::after {
  content: '';
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0),
    rgba(255, 255, 255, 0.55),
    rgba(255, 255, 255, 0)
  );
  animation: shimmer 1.2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
</style>
