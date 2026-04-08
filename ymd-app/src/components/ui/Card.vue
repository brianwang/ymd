<template>
  <view class="card" :class="{ pressable }" hover-class="tap" hover-stay-time="70">
    <slot />
  </view>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    pressable?: boolean;
  }>(),
  {
    pressable: false,
  }
);
</script>

<style scoped lang="scss">
.card {
  background: $ymd-v2-color-surface;
  border: 1px solid $ymd-v2-color-line;
  border-radius: $ymd-v2-radius-lg;
  box-shadow: $ymd-v2-shadow-xs;
}

.pressable {
  overflow: hidden;
}

.tap {
  background: rgba(15, 23, 42, 0.03);
}
</style>
