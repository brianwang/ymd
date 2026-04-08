<template>
  <view class="wrap">
    <image v-if="image" class="illus" :src="image" mode="widthFix" />
    <text class="title">{{ title }}</text>
    <text v-if="desc" class="desc">{{ desc }}</text>
    <view v-if="$slots.actions || actionText" class="actions">
      <slot name="actions">
        <button class="btn ymd-btn" size="mini" @click="emit('action')">{{ actionText }}</button>
      </slot>
    </view>
  </view>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    image?: string;
    title: string;
    desc?: string;
    actionText?: string;
  }>(),
  {
    image: '',
    desc: '',
    actionText: '',
  }
);

const emit = defineEmits<{
  (e: 'action'): void;
}>();
</script>

<style scoped lang="scss">
.wrap {
  background: $ymd-v2-color-surface;
  border: 1px solid $ymd-v2-color-line;
  border-radius: $ymd-v2-radius-lg;
  box-shadow: $ymd-v2-shadow-xs;
  padding: 18px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.illus {
  width: 170px;
}

.title {
  font-size: $ymd-v2-font-md;
  font-weight: 900;
  color: $ymd-v2-color-text;
}

.desc {
  font-size: $ymd-v2-font-sm;
  color: $ymd-v2-color-muted;
  text-align: center;
}

.actions {
  margin-top: 4px;
}

.btn {
  padding: 0 14px;
  height: 34px;
  line-height: 34px;
  font-size: 12px;
  border-radius: $ymd-v2-radius-pill;
}
</style>
