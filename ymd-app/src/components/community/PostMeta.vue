<template>
  <view v-if="hasAny" class="post-meta">
    <view v-if="locationName" class="row location">
      <text class="loc-icon">📍</text>
      <text class="loc-text">{{ locationName }}</text>
    </view>

    <view v-if="normalizedTags.length" class="row tags">
      <text v-for="t in normalizedTags" :key="t" class="tag">#{{ t }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type PostLocation = {
  name: string;
  address?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  raw?: any;
};

const props = defineProps<{
  location?: PostLocation | null;
  tags?: string[] | null;
}>();

const locationName = computed(() => {
  const name = props.location?.name;
  return typeof name === 'string' && name.trim() ? name.trim() : '';
});

const normalizedTags = computed(() => {
  const tags = Array.isArray(props.tags) ? props.tags : [];
  const out: string[] = [];
  for (const t of tags) {
    const v = typeof t === 'string' ? t.trim() : '';
    if (!v) continue;
    if (out.includes(v)) continue;
    out.push(v);
  }
  return out;
});

const hasAny = computed(() => !!locationName.value || normalizedTags.value.length > 0);
</script>

<style scoped lang="scss">
.post-meta {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  color: $ymd-v2-color-muted;
  font-size: 12px;
}

.loc-icon {
  font-size: 12px;
  line-height: 12px;
}

.loc-text {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag {
  color: $ymd-v2-color-accent-2;
  font-weight: 700;
}
</style>
