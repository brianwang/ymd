<template>
  <view class="divider" :class="{ inset }" />
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    inset?: boolean;
  }>(),
  {
    inset: false,
  }
);
</script>

<style scoped lang="scss">
.divider {
  height: 1px;
  background: $ymd-v2-color-line;
  width: 100%;
}

.inset {
  width: calc(100% - 28px);
  margin-left: 14px;
}
</style>
