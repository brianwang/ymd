<template>
  <view class="head">
    <view class="left">
      <text class="title">{{ title }}</text>
      <slot name="sub" />
    </view>
    <view class="right">
      <slot name="right">
        <text v-if="actionText" class="action" @click="emit('action')">{{ actionText }}</text>
      </slot>
    </view>
  </view>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  actionText?: string;
}>();

const emit = defineEmits<{
  (e: 'action'): void;
}>();
</script>

<style scoped lang="scss">
.head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: $ymd-v2-space-2;
}

.left {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.title {
  font-size: $ymd-v2-font-lg;
  font-weight: 900;
  color: $ymd-v2-color-text;
  line-height: 1.2;
}

.right {
  display: flex;
  align-items: center;
}

.action {
  font-size: $ymd-v2-font-sm;
  color: $ymd-v2-color-muted;
  padding: 6px 10px;
  border-radius: $ymd-v2-radius-pill;
  background: rgba(15, 23, 42, 0.04);
}
</style>
