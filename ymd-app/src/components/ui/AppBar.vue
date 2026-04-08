<template>
  <view class="appbar" :class="{ elevated }">
    <view class="row">
      <view class="side left">
        <slot name="left">
          <text v-if="back" class="back" @click="handleBack">‹</text>
        </slot>
      </view>
      <view class="center">
        <text class="title">{{ title }}</text>
      </view>
      <view class="side right">
        <slot name="right">
          <text v-if="actionText" class="action" @click="emit('action')">{{ actionText }}</text>
        </slot>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string;
    actionText?: string;
    back?: boolean;
    elevated?: boolean;
  }>(),
  {
    back: false,
    elevated: true,
  }
);

const emit = defineEmits<{
  (e: 'action'): void;
}>();

const handleBack = () => {
  uni.navigateBack({ delta: 1 });
};
</script>

<style scoped lang="scss">
.appbar {
  position: sticky;
  top: 0;
  z-index: 50;
  padding-top: env(safe-area-inset-top);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  background: rgba(247, 250, 251, 0.86);
}

.appbar.elevated {
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}

.row {
  height: 44px;
  display: flex;
  align-items: center;
  padding: 0 $ymd-v2-space-3;
}

.side {
  width: 72px;
  display: flex;
  align-items: center;
}

.left {
  justify-content: flex-start;
}

.right {
  justify-content: flex-end;
}

.center {
  flex: 1;
  display: flex;
  justify-content: center;
  min-width: 0;
}

.title {
  font-size: $ymd-v2-font-lg;
  font-weight: 900;
  color: $ymd-v2-color-text;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action {
  font-size: $ymd-v2-font-sm;
  font-weight: 800;
  color: $ymd-v2-color-brand;
  padding: 8px 10px;
  border-radius: $ymd-v2-radius-pill;
  background: $ymd-v2-color-soft;
  border: 1px solid rgba(18, 200, 192, 0.2);
}

.back {
  font-size: 26px;
  line-height: 26px;
  padding: 8px 10px;
  border-radius: $ymd-v2-radius-pill;
  color: $ymd-v2-color-text;
}
</style>
