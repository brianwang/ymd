<template>
  <view class="page ymd-page">
    <image class="hero" :src="event?.cover_url || '/static/placeholder/cover-events-v2.png'" mode="aspectFill" />
    <view class="card">
      <text class="title">{{ event?.title || '活动详情' }}</text>
      <text class="sub" v-if="event">{{ event.city }} · {{ dateText }}</text>
      <text class="sub" v-else>活动 ID：{{ idText }}</text>
      <view v-if="event" class="status">
        <text class="pill" :class="statusClass">{{ statusText }}</text>
        <text class="status-sub">{{ statusSub }}</text>
      </view>
      <view class="divider"></view>

      <view v-if="loading" class="state"><text class="state-text">加载中...</text></view>
      <view v-else-if="errorText" class="state"><text class="state-text">{{ errorText }}</text></view>

      <view class="kv">
        <text class="k">时间</text>
        <text class="v">{{ timeText }}</text>
      </view>
      <view class="kv">
        <text class="k">地点</text>
        <text class="v">{{ placeText }}</text>
      </view>
      <view class="kv">
        <text class="k">名额</text>
        <text class="v">{{ capacityText }}</text>
      </view>
      <view class="kv">
        <text class="k">报名截止</text>
        <text class="v">{{ deadlineText }}</text>
      </view>
      <view class="divider"></view>
      <text class="desc">{{ event?.summary || event?.content || '暂无详情' }}</text>

      <view class="divider"></view>
      <view v-if="myStatus === 'registered'" class="registered">
        <button class="cta ymd-btn ghost danger" :disabled="loading" @click="cancelRegistration">取消报名</button>
      </view>
      <view v-else class="signup">
        <view class="field">
          <text class="label">姓名</text>
          <input class="input" v-model="formName" placeholder="请输入姓名" placeholder-class="ph" />
        </view>
        <view class="field">
          <text class="label">手机号</text>
          <input class="input" v-model="formPhone" placeholder="请输入手机号" placeholder-class="ph" type="number" />
        </view>
        <view class="field">
          <text class="label">备注（可选）</text>
          <textarea class="textarea" v-model="formRemark" placeholder="如：到场时间/特殊需求" placeholder-class="ph" />
        </view>
        <button class="cta ymd-btn" :disabled="ctaDisabled || loading" @click="submitRegistration">{{ ctaText }}</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import { request } from '@/utils/request';
import { useUserStore } from '@/store/user';

const id = ref<string>('');

const event = ref<any | null>(null);
const loading = ref(false);
const errorText = ref('');

const userStore = useUserStore();

const formName = ref('');
const formPhone = ref('');
const formRemark = ref('');

const idText = computed(() => id.value || '--');

onLoad((query) => {
  id.value = (query?.id as string) || '';
  syncDefaultForm();
  fetchDetail();
});

onShow(() => {
  syncDefaultForm();
  if (id.value) fetchDetail();
});

const syncDefaultForm = () => {
  const n = String(userStore.userInfo?.nickname || '').trim();
  if (!formName.value && n) formName.value = n;
};

const fetchDetail = async () => {
  if (!id.value) return;
  loading.value = true;
  errorText.value = '';
  try {
    event.value = await request({ url: `/events/${id.value}`, method: 'GET' });
  } catch (e: any) {
    errorText.value = e?.message || '加载失败';
    event.value = null;
  } finally {
    loading.value = false;
  }
};

const dateText = computed(() => {
  const raw = event.value?.start_at;
  if (!raw) return '';
  const dt = new Date(raw);
  if (Number.isNaN(dt.getTime())) return raw;
  return `${dt.getMonth() + 1}月${dt.getDate()}日`;
});

const timeText = computed(() => {
  const raw = event.value?.start_at;
  if (!raw) return '--';
  const dt = new Date(raw);
  if (Number.isNaN(dt.getTime())) return raw;
  return dt.toLocaleString();
});

const placeText = computed(() => {
  if (!event.value) return '--';
  const city = event.value.city || '';
  const address = event.value.address || '';
  return address ? `${city} · ${address}` : city || '--';
});

const capacityText = computed(() => {
  if (!event.value) return '--';
  const cap = event.value.capacity;
  const cnt = event.value.registered_count;
  if (cap == null) return `${cnt} 已报名`;
  return `${cnt}/${cap}`;
});

const deadlineText = computed(() => {
  const raw = event.value?.signup_deadline_at;
  if (!raw) return '--';
  const dt = new Date(raw);
  if (Number.isNaN(dt.getTime())) return raw;
  return dt.toLocaleString();
});

const isFull = computed(() => {
  if (!event.value) return false;
  const cap = event.value.capacity;
  if (cap == null) return false;
  return Number(event.value.registered_count) >= Number(cap);
});

const isClosed = computed(() => {
  const raw = event.value?.signup_deadline_at;
  if (!raw) return false;
  const t = new Date(raw).getTime();
  if (Number.isNaN(t)) return false;
  return t < Date.now();
});

const myStatus = computed(() => String(event.value?.my_registration_status || 'none'));

const statusText = computed(() => {
  if (!userStore.token) return '未登录';
  if (myStatus.value === 'registered') return '已报名';
  if (myStatus.value === 'canceled') return '已取消';
  return '未报名';
});

const statusClass = computed(() => {
  if (!userStore.token) return 'muted';
  if (myStatus.value === 'registered') return 'on';
  if (myStatus.value === 'canceled') return 'off';
  return 'muted';
});

const statusSub = computed(() => {
  if (!userStore.token) return '登录后可报名与查看状态';
  if (myStatus.value === 'registered') return '如需修改信息，可取消后重新提交';
  if (myStatus.value === 'canceled') return '可重新报名（若名额允许）';
  return '填写信息即可完成报名';
});

const ctaText = computed(() => {
  if (!userStore.token) return '登录后报名';
  if (isClosed.value) return '报名已截止';
  if (isFull.value) return '已满员';
  return '提交报名';
});

const ctaDisabled = computed(() => {
  if (!userStore.token) return false;
  if (myStatus.value === 'registered') return true;
  return isClosed.value || isFull.value;
});

const ensureLogin = () => {
  if (userStore.token) return true;
  uni.showToast({ title: '请先登录', icon: 'none' });
  uni.navigateTo({ url: '/pages/auth/login' });
  return false;
};

const submitRegistration = async () => {
  if (!id.value) return;
  if (!ensureLogin()) return;
  if (ctaDisabled.value) return;
  const name = formName.value.trim();
  const phone = formPhone.value.trim();
  const remark = formRemark.value.trim();
  if (!name) {
    uni.showToast({ title: '请输入姓名', icon: 'none' });
    return;
  }
  if (!phone) {
    uni.showToast({ title: '请输入手机号', icon: 'none' });
    return;
  }
  try {
    await request({
      url: `/events/${id.value}/registrations`,
      method: 'POST',
      data: { name, phone, remark: remark ? remark : undefined },
    });
    uni.showToast({ title: '报名成功', icon: 'success' });
    await fetchDetail();
  } catch (e: any) {
    uni.showToast({ title: e?.data?.detail || e?.message || '报名失败', icon: 'none' });
  }
};

const cancelRegistration = async () => {
  if (!id.value) return;
  if (!ensureLogin()) return;
  uni.showModal({
    title: '确认取消报名',
    content: '取消后可再次报名（若名额允许）',
    confirmText: '取消报名',
    cancelText: '我再想想',
    success: async (r) => {
      if (!r.confirm) return;
      try {
        await request({ url: `/events/${id.value}/registrations/me`, method: 'DELETE' });
        uni.showToast({ title: '已取消', icon: 'success' });
        await fetchDetail();
      } catch (e: any) {
        uni.showToast({ title: e?.data?.detail || e?.message || '取消失败', icon: 'none' });
      }
    },
  });
};
</script>

<style scoped lang="scss">
.page { padding: $ymd-space-3 $ymd-space-3 28px; }
.hero { width: 100%; height: 180px; border-radius: $ymd-radius-lg; box-shadow: $ymd-shadow-sm; }
.card { margin-top: 12px; background: $ymd-color-card; border: 1px solid $ymd-color-line; border-radius: $ymd-radius-lg; padding: 14px; box-shadow: $ymd-shadow-xs; }
.title { font-size: 18px; font-weight: 800; color: $ymd-color-text; }
.sub { margin-top: 6px; font-size: $ymd-font-sm; color: $ymd-color-muted; }
.status { display: flex; align-items: center; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
.pill { padding: 4px 10px; border-radius: $ymd-radius-pill; font-size: 12px; border: 1px solid $ymd-color-line; }
.pill.on { background: rgba(24, 210, 202, .12); border-color: rgba(24, 210, 202, .4); color: $ymd-color-primary; font-weight: 800; }
.pill.off { background: rgba(239, 68, 68, .10); border-color: rgba(239, 68, 68, .35); color: $uni-color-error; font-weight: 800; }
.pill.muted { background: rgba(15, 23, 42, 0.04); color: $ymd-color-muted; }
.status-sub { font-size: 12px; color: $ymd-color-muted; }
.divider { height: 1px; background: $ymd-color-line; margin: 14px 0; }
.kv { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; }
.k { font-size: 13px; color: $ymd-color-muted; }
.v { font-size: 13px; color: $ymd-color-text; font-weight: 700; }
.desc { font-size: 13px; color: $ymd-color-text; opacity: .78; line-height: 20px; }
.signup { display: flex; flex-direction: column; gap: 10px; }
.registered { display: flex; }
.field { display: flex; flex-direction: column; gap: 8px; }
.label { font-size: 12px; color: $ymd-color-muted; font-weight: 700; }
.input {
  height: 44px;
  line-height: 44px;
  border-radius: $ymd-radius-md;
  border: 1px solid $ymd-color-line;
  padding: 0 12px;
  font-size: 14px;
  color: $ymd-color-text;
  background: rgba(15, 23, 42, 0.02);
}
.textarea {
  min-height: 82px;
  border-radius: $ymd-radius-md;
  border: 1px solid $ymd-color-line;
  padding: 10px 12px;
  font-size: 14px;
  color: $ymd-color-text;
  background: rgba(15, 23, 42, 0.02);
}
.ph { color: rgba(100, 116, 139, .7); }
.cta { margin-top: 8px; border-radius: $ymd-radius-md; height: 44px; line-height: 44px; font-weight: 800; }
.danger { color: $uni-color-error; }
.state { padding: 8px 0; }
.state-text { font-size: 12px; color: $ymd-color-muted; }
</style>
