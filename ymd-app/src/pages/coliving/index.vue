<template>
  <view class="ymd-page">
    <AppBar title="共居空间" action-text="全部城市" @action="city = '全部'" />
    <view class="ymd-container ymd-page-inner">
      <view class="hero" @click="city = '全部'">
        <image class="hero-img" src="/static/banner/banner-v2-2.png" mode="aspectFill" />
        <view class="hero-mask"></view>
        <view class="hero-text">
          <text class="hero-title">找到你的下一段驻留</text>
          <text class="hero-sub">安静工位 / 高速网络 / 结伴同行</text>
        </view>
      </view>

      <view class="ymd-section">
        <SectionHeader title="城市选择" />
        <scroll-view scroll-x class="pills">
          <view class="pills-inner">
            <view v-for="c in cities" :key="c" class="pill" :class="{ active: city === c }" @click="city = c">
              <text class="pill-text">{{ c }}</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <view class="ymd-section">
        <SectionHeader title="推荐空间" />
        <scroll-view scroll-x class="reco">
          <view class="reco-inner">
            <Card v-for="s in recommended" :key="s.id" class="reco-card" pressable @click="goDetail(s.id)">
              <image class="reco-img" :src="s.cover" mode="aspectFill" />
              <view class="reco-meta">
                <text class="reco-title">{{ s.name }}</text>
                <text class="reco-sub">{{ s.city }} · {{ s.priceText }}</text>
              </view>
            </Card>
          </view>
        </scroll-view>
      </view>

      <view class="ymd-section">
        <SectionHeader title="空间列表">
          <template #sub>
            <text class="count">{{ filteredSpaces.length }} 个</text>
          </template>
        </SectionHeader>

        <view v-if="status === 'loading'">
          <Card class="sk-card">
            <Skeleton height="150px" border-radius="18px" />
            <view class="sk-body">
              <Skeleton height="16px" />
              <Skeleton height="12px" width="66%" />
              <view class="sk-tags">
                <Skeleton height="22px" width="56px" border-radius="999px" />
                <Skeleton height="22px" width="64px" border-radius="999px" />
                <Skeleton height="22px" width="58px" border-radius="999px" />
              </view>
            </view>
          </Card>
          <Card class="sk-card">
            <Skeleton height="150px" border-radius="18px" />
            <view class="sk-body">
              <Skeleton height="16px" />
              <Skeleton height="12px" width="58%" />
              <view class="sk-tags">
                <Skeleton height="22px" width="52px" border-radius="999px" />
                <Skeleton height="22px" width="70px" border-radius="999px" />
              </view>
            </view>
          </Card>
        </view>

        <EmptyState
          v-else-if="status === 'error'"
          image="/static/empty/empty-error-v2.png"
          title="加载失败"
          :desc="errorText || '请稍后再试'"
          action-text="重试"
          @action="reload"
        />
        <EmptyState
          v-else-if="filteredSpaces.length === 0"
          image="/static/empty/empty-list-v2.png"
          title="暂无空间"
          desc="换个城市看看"
          action-text="查看全部"
          @action="city = '全部'"
        />
        <view v-else class="list">
          <Card v-for="s in filteredSpaces" :key="s.id" class="space" pressable @click="goDetail(s.id)">
            <image class="space-cover" :src="s.cover" mode="aspectFill" />
            <view class="space-body">
              <view class="space-head">
                <text class="space-title">{{ s.name }}</text>
                <text class="space-price">{{ s.priceText }}</text>
              </view>
              <text class="space-sub">{{ s.city }} · {{ s.distanceText }}</text>
              <view class="tags">
                <view v-for="t in s.tags" :key="t" class="tag">
                  <text class="tag-text">{{ t }}</text>
                </view>
              </view>
            </view>
          </Card>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import AppBar from '@/components/ui/AppBar.vue';
import SectionHeader from '@/components/ui/SectionHeader.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import Skeleton from '@/components/ui/Skeleton.vue';
import Card from '@/components/ui/Card.vue';

type PageStatus = 'loading' | 'ready' | 'error';

type SpaceItem = {
  id: number;
  name: string;
  city: string;
  cover: string;
  priceText: string;
  distanceText: string;
  tags: string[];
};

const cities = ['全部', '上海', '杭州', '成都', '深圳', '厦门'];
const city = ref<string>('全部');

const status = ref<PageStatus>('loading');
const errorText = ref<string>('');
const allSpaces = ref<SpaceItem[]>([]);

const recommended = computed(() => allSpaces.value.slice(0, 6));

const filteredSpaces = computed(() => {
  return allSpaces.value.filter((s) => (city.value === '全部' ? true : s.city === city.value));
});

const seed = () => {
  allSpaces.value = [
    { id: 201, name: '海边共居 · 日出工位', city: '厦门', cover: '/static/placeholder/cover-coliving-v2.png', priceText: '¥199/晚', distanceText: '地铁 5 分钟', tags: ['海边', '安静', '高速网络'] },
    { id: 202, name: '城市共居 · 极简公寓', city: '上海', cover: '/static/placeholder/cover-coliving-v2.png', priceText: '¥259/晚', distanceText: '市中心', tags: ['通勤友好', '独立卫浴', '共享厨房'] },
    { id: 203, name: '山间共居 · 轻度躺平', city: '成都', cover: '/static/placeholder/cover-coliving-v2.png', priceText: '¥169/晚', distanceText: '打车 15 分钟', tags: ['自然', '冥想', '宠物友好'] },
    { id: 204, name: '湖畔共居 · 深度专注', city: '杭州', cover: '/static/placeholder/cover-coliving-v2.png', priceText: '¥189/晚', distanceText: '公交 10 分钟', tags: ['专注', '会议室', '咖啡吧'] },
    { id: 205, name: '热带共居 · 运动社群', city: '深圳', cover: '/static/placeholder/cover-coliving-v2.png', priceText: '¥229/晚', distanceText: '公园旁', tags: ['健身', '社群', '夜跑'] },
  ];
};

const reload = async () => {
  status.value = 'loading';
  errorText.value = '';
  try {
    await new Promise((r) => setTimeout(r, 150));
    seed();
    status.value = 'ready';
  } catch (e: any) {
    status.value = 'error';
    errorText.value = e?.message || '请稍后再试';
  }
};

const goDetail = (id: number) => {
  uni.navigateTo({ url: `/pages/coliving/detail?id=${id}` });
};

onShow(() => {
  if (status.value === 'loading') reload();
});
</script>

<style scoped lang="scss">
.hero { height: 150px; border-radius: $ymd-v2-radius-xl; overflow: hidden; position: relative; box-shadow: $ymd-v2-shadow-sm; }
.hero-img { width: 100%; height: 150px; }
.hero-mask { position: absolute; left: 0; right: 0; top: 0; bottom: 0; background: linear-gradient(180deg, rgba(0,0,0,.04), rgba(0,0,0,.6)); }
.hero-text { position: absolute; left: 14px; right: 14px; bottom: 12px; display: flex; flex-direction: column; }
.hero-title { color: rgba(255,255,255,.98); font-size: 18px; font-weight: 900; }
.hero-sub { color: rgba(255,255,255,.9); font-size: 12px; margin-top: 4px; }

.pills { width: 100%; }
.pills-inner { display: flex; gap: 8px; padding-bottom: 8px; }
.pill { padding: 8px 12px; background: rgba(255,255,255,.92); border-radius: $ymd-v2-radius-pill; border: 1px solid $ymd-v2-color-line; }
.pill.active { background: $ymd-v2-color-brand; border-color: $ymd-v2-color-brand; }
.pill-text { font-size: $ymd-v2-font-sm; color: $ymd-v2-color-text; font-weight: 700; }
.pill.active .pill-text { color: #fff; }

.reco { width: 100%; }
.reco-inner { display: flex; gap: 10px; padding-bottom: 6px; }
.reco-card { width: 170px; overflow: hidden; }
.reco-img { width: 160px; height: 96px; }
.reco-meta { padding: 10px 12px 12px; display: flex; flex-direction: column; gap: 4px; }
.reco-title { font-size: 15px; font-weight: 900; color: $ymd-v2-color-text; line-height: 20px; }
.reco-sub { font-size: $ymd-v2-font-sm; color: $ymd-v2-color-muted; }

.count { font-size: $ymd-v2-font-sm; color: $ymd-v2-color-muted; }

.list { display: flex; flex-direction: column; gap: 10px; }
.space { overflow: hidden; }
.space-cover { width: 100%; height: 156px; }
.space-body { padding: 12px 12px 14px; display: flex; flex-direction: column; gap: 8px; }
.space-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.space-title { font-size: 16px; font-weight: 900; color: $ymd-v2-color-text; line-height: 22px; flex: 1; }
.space-price { font-size: $ymd-v2-font-sm; color: $ymd-v2-color-brand; font-weight: 900; white-space: nowrap; }
.space-sub { font-size: $ymd-v2-font-sm; color: $ymd-v2-color-muted; }
.tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag { padding: 4px 9px; background: rgba(18, 200, 192, 0.10); border-radius: $ymd-v2-radius-pill; border: 1px solid rgba(18, 200, 192, 0.22); }
.tag-text { font-size: $ymd-v2-font-xs; color: $ymd-v2-color-muted; font-weight: 700; }

.sk-card { overflow: hidden; margin-bottom: 10px; }
.sk-body { padding: 12px 12px 14px; display: flex; flex-direction: column; gap: 10px; }
.sk-tags { display: flex; gap: 8px; }
</style>
