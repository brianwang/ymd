<template>
  <view class="ymd-page">
    <AppBar title="探索活动" action-text="我的" @action="goMy" />
    <view class="ymd-container ymd-page-inner">
      <swiper class="hero" circular autoplay :interval="3500" :duration="400">
        <swiper-item v-for="b in banners" :key="b.id">
          <view class="hero-item" @click="handleBannerClick(b)">
            <image class="hero-img" :src="b.image" mode="aspectFill" />
            <view class="hero-mask"></view>
            <view class="hero-text">
              <text class="hero-title">{{ b.title }}</text>
              <text class="hero-sub">{{ b.sub }}</text>
            </view>
          </view>
        </swiper-item>
      </swiper>

      <view class="ymd-section">
        <SectionHeader title="快速筛选" />
        <scroll-view scroll-x class="pills">
          <view class="pills-inner">
            <view v-for="c in categories" :key="c" class="pill" :class="{ active: category === c }" @click="category = c">
              <text class="pill-text">{{ c }}</text>
            </view>
          </view>
        </scroll-view>
        <scroll-view scroll-x class="pills">
          <view class="pills-inner">
            <view v-for="t in timeRanges" :key="t" class="pill" :class="{ active: timeRange === t }" @click="timeRange = t">
              <text class="pill-text">{{ t }}</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <view class="ymd-section">
        <SectionHeader title="推荐活动" action-text="查看全部" @action="resetFilters" />
        <scroll-view scroll-x class="reco">
          <view class="reco-inner">
            <Card v-for="e in recommended" :key="e.id" class="reco-card" pressable @click="goDetail(e.id)">
              <image class="reco-img" :src="e.cover" mode="aspectFill" />
              <view class="reco-meta">
                <text class="reco-title">{{ e.title }}</text>
                <text class="reco-sub">{{ e.city }} · {{ e.dateText }}</text>
              </view>
            </Card>
          </view>
        </scroll-view>
      </view>

      <view class="ymd-section">
        <SectionHeader title="活动列表">
          <template #sub>
            <text class="count">{{ filteredEvents.length }} 个</text>
          </template>
        </SectionHeader>

        <view v-if="status === 'loading'">
          <Card class="sk-card">
            <Skeleton height="150px" border-radius="18px" />
            <view class="sk-body">
              <Skeleton height="16px" />
              <Skeleton height="12px" width="72%" />
              <view class="sk-tags">
                <Skeleton height="22px" width="56px" border-radius="999px" />
                <Skeleton height="22px" width="60px" border-radius="999px" />
                <Skeleton height="22px" width="64px" border-radius="999px" />
              </view>
            </view>
          </Card>
          <Card class="sk-card">
            <Skeleton height="150px" border-radius="18px" />
            <view class="sk-body">
              <Skeleton height="16px" />
              <Skeleton height="12px" width="62%" />
              <view class="sk-tags">
                <Skeleton height="22px" width="52px" border-radius="999px" />
                <Skeleton height="22px" width="66px" border-radius="999px" />
              </view>
            </view>
          </Card>
        </view>

        <EmptyState
          v-else-if="status === 'error'"
          :image="TESTDATA_IMAGES.emptyErrorV2"
          title="加载失败"
          :desc="errorText || '请稍后再试'"
          action-text="重试"
          @action="reload"
        />
        <EmptyState
          v-else-if="filteredEvents.length === 0"
          :image="TESTDATA_IMAGES.emptyListV2"
          title="暂无活动"
          desc="换个筛选试试"
          action-text="重置筛选"
          @action="resetFilters"
        />
        <view v-else class="list">
          <Card v-for="e in filteredEvents" :key="e.id" class="event" pressable @click="goDetail(e.id)">
            <image class="event-cover" :src="e.cover" mode="aspectFill" />
            <view class="event-body">
              <text class="event-title">{{ e.title }}</text>
              <view class="event-row">
                <text class="event-sub">{{ e.city }} · {{ e.dateText }}</text>
                <text class="event-price">{{ e.priceText }}</text>
              </view>
              <view class="tags">
                <view v-for="t in e.tags" :key="t" class="tag">
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
import { request } from '@/utils/request';
import AppBar from '@/components/ui/AppBar.vue';
import SectionHeader from '@/components/ui/SectionHeader.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import Skeleton from '@/components/ui/Skeleton.vue';
import Card from '@/components/ui/Card.vue';
import { TESTDATA_IMAGES } from '@/constants/testdataImages';

type PageStatus = 'loading' | 'ready' | 'error';

type Banner = {
  id: number;
  title: string;
  sub: string;
  image: string;
  eventId?: number;
};

type EventItem = {
  id: number;
  title: string;
  city: string;
  category: string;
  date: string;
  cover: string;
  priceText: string;
  tags: string[];
};

const banners = ref<Banner[]>([
  { id: 1, title: '游牧岛 · 城市活动季', sub: '共创 / 分享 / 同行', image: TESTDATA_IMAGES.bannerV2_1 },
  { id: 2, title: '周末城市漫游', sub: '咖啡巡游 / 轻社交 / 结伴出发', image: TESTDATA_IMAGES.bannerV2_2 },
  { id: 3, title: '共居体验日', sub: '看房 + 体验 + 组队入住', image: TESTDATA_IMAGES.bannerV2_3 },
]);

const categories = ['全部', '共创', '分享', '运动', '城市漫游'];
const timeRanges = ['全部', '本周', '本月'];

const category = ref<string>('全部');
const timeRange = ref<string>('全部');

const status = ref<PageStatus>('loading');
const errorText = ref<string>('');

const allEvents = ref<EventItem[]>([]);

const enrich = (e: EventItem) => {
  const dt = new Date(e.date);
  const dateText = `${dt.getMonth() + 1}月${dt.getDate()}日`;
  return { ...e, dateText };
};

const list = computed(() => allEvents.value.map(enrich));

const recommended = computed(() => list.value.slice(0, 6));

const filteredEvents = computed(() => {
  const now = new Date();
  const startOfWeek = new Date(now);
  startOfWeek.setDate(now.getDate() - ((now.getDay() + 6) % 7));
  startOfWeek.setHours(0, 0, 0, 0);

  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  startOfMonth.setHours(0, 0, 0, 0);

  return list.value.filter((e) => {
    const okCategory = category.value === '全部' ? true : e.category === category.value;
    const dt = new Date(e.date);
    const okTime =
      timeRange.value === '全部'
        ? true
        : timeRange.value === '本周'
          ? dt >= startOfWeek
          : dt >= startOfMonth;
    return okCategory && okTime;
  });
});

const reload = async () => {
  status.value = 'loading';
  errorText.value = '';
  try {
    const data: any[] = (await request({ url: '/events', method: 'GET' })) as any[];
    allEvents.value = (data || []).map((it) => ({
      id: it.id,
      title: it.title,
      city: it.city,
      category: it.category,
      date: it.start_at,
      cover: it.cover_url || TESTDATA_IMAGES.coverEventsV2,
      priceText: '免费',
      tags: [it.category],
    }));
    status.value = 'ready';
  } catch (e: any) {
    status.value = 'error';
    errorText.value = e?.message || '请稍后再试';
  }
};

const resetFilters = () => {
  category.value = '全部';
  timeRange.value = '全部';
};

const goDetail = (id: number) => {
  uni.navigateTo({ url: `/pages/events/detail?id=${id}` });
};

const goMy = () => {
  uni.navigateTo({ url: '/pages/events/my' });
};

const handleBannerClick = (b: Banner) => {
  if (b.eventId) goDetail(b.eventId);
};

onShow(() => {
  if (status.value === 'loading') reload();
});
</script>

<style scoped lang="scss">
.hero { height: 150px; border-radius: $ymd-v2-radius-xl; overflow: hidden; box-shadow: $ymd-v2-shadow-sm; }
.hero-item { height: 150px; position: relative; border-radius: $ymd-v2-radius-xl; overflow: hidden; }
.hero-img { width: 100%; height: 150px; }
.hero-mask { position: absolute; left: 0; right: 0; top: 0; bottom: 0; background: linear-gradient(180deg, rgba(0,0,0,.04), rgba(0,0,0,.58)); }
.hero-text { position: absolute; left: 14px; right: 14px; bottom: 12px; display: flex; flex-direction: column; }
.hero-title { color: rgba(255,255,255,.98); font-size: 18px; font-weight: 900; letter-spacing: .2px; }
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
.event { overflow: hidden; }
.event-cover { width: 100%; height: 156px; }
.event-body { padding: 12px 12px 14px; display: flex; flex-direction: column; gap: 8px; }
.event-title { font-size: 16px; font-weight: 900; color: $ymd-v2-color-text; line-height: 22px; }
.event-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.event-sub { font-size: $ymd-v2-font-sm; color: $ymd-v2-color-muted; }
.event-price { font-size: $ymd-v2-font-sm; color: $ymd-v2-color-brand; font-weight: 900; white-space: nowrap; }
.tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag { padding: 4px 9px; background: rgba(18, 200, 192, 0.10); border-radius: $ymd-v2-radius-pill; border: 1px solid rgba(18, 200, 192, 0.22); }
.tag-text { font-size: $ymd-v2-font-xs; color: $ymd-v2-color-muted; font-weight: 700; }

.sk-card { overflow: hidden; margin-bottom: 10px; }
.sk-body { padding: 12px 12px 14px; display: flex; flex-direction: column; gap: 10px; }
.sk-tags { display: flex; gap: 8px; }
</style>
