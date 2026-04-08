<template>
  <view class="page ymd-page">
    <image class="hero" src="/static/placeholder/cover-coliving-v2.png" mode="aspectFill" />
    <view class="card">
      <text class="title">空间详情</text>
      <text class="sub">空间 ID：{{ idText }}</text>
      <view class="divider"></view>
      <view class="kv">
        <text class="k">位置</text>
        <text class="v">待完善</text>
      </view>
      <view class="kv">
        <text class="k">房型</text>
        <text class="v">待完善</text>
      </view>
      <view class="kv">
        <text class="k">价格</text>
        <text class="v">待完善</text>
      </view>
      <view class="divider"></view>
      <text class="desc">
        这里是共居空间详情占位页。后续可接入真实房源数据、可用日期、下单与客服等功能。
      </text>
      <button class="cta ymd-btn" @click="handleAction">咨询</button>
    </view>

    <view v-if="inquiryVisible" class="modal-mask" @click="closeInquiry">
      <view class="modal" @click.stop>
        <view class="modal-hd">
          <text class="modal-title">提交咨询</text>
          <text class="modal-close" @click="closeInquiry">×</text>
        </view>
        <view class="modal-bd">
          <view class="field">
            <text class="label">联系人（可选）</text>
            <input class="input" v-model="form.contact_name" type="text" placeholder="怎么称呼您" />
          </view>
          <view class="field">
            <text class="label">手机号</text>
            <input class="input" v-model="form.contact_phone" type="number" placeholder="请输入手机号" />
          </view>
          <view class="field">
            <text class="label">留言</text>
            <textarea
              class="textarea"
              v-model="form.message"
              placeholder="请描述您的需求（入住时间、预算、人数等）"
              maxlength="1000"
            />
          </view>

          <view v-if="submitError" class="error">
            <text class="error-text">{{ submitError }}</text>
          </view>
        </view>
        <view class="modal-ft">
          <button class="btn ghost" :disabled="submitLoading" @click="closeInquiry">取消</button>
          <button class="btn ymd-btn" :loading="submitLoading" :disabled="submitLoading" @click="submitInquiry">
            提交
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { request } from '../../utils/request';

const id = ref<string>('');
const idText = computed(() => id.value || '--');

onLoad((query) => {
  id.value = (query?.id as string) || (query?.space_id as string) || '';
});

const customerWeChat = computed(() => (import.meta.env.VITE_YMD_CUSTOMER_WECHAT || '').trim());
const customerPhone = computed(() => (import.meta.env.VITE_YMD_CUSTOMER_PHONE || '').trim());

const inquiryVisible = ref(false);
const submitLoading = ref(false);
const submitError = ref('');

const form = reactive({
  contact_name: '',
  contact_phone: '',
  message: '',
});

const resetForm = () => {
  form.contact_name = '';
  form.contact_phone = '';
  form.message = '';
  submitError.value = '';
};

const closeInquiry = () => {
  if (submitLoading.value) return;
  inquiryVisible.value = false;
  resetForm();
};

const openInquiry = () => {
  submitError.value = '';
  inquiryVisible.value = true;
};

const handleAction = () => {
  const actions: Array<{ key: 'form' | 'wechat' | 'phone'; label: string }> = [{ key: 'form', label: '提交咨询' }];
  if (customerWeChat.value) actions.push({ key: 'wechat', label: '复制客服微信' });
  if (customerPhone.value) actions.push({ key: 'phone', label: '拨打电话' });

  if (actions.length === 1) {
    openInquiry();
    return;
  }

  uni.showActionSheet({
    itemList: actions.map((a) => a.label),
    success: async (res) => {
      const action = actions[res.tapIndex];
      if (!action) return;
      if (action.key === 'form') {
        openInquiry();
        return;
      }
      if (action.key === 'wechat') {
        const wx = customerWeChat.value;
        if (!wx) return;
        uni.setClipboardData({
          data: wx,
          success: () => {
            uni.showToast({ title: '已复制', icon: 'none' });
          },
        });
        return;
      }
      if (action.key === 'phone') {
        const phone = customerPhone.value;
        if (!phone) return;
        uni.makePhoneCall({
          phoneNumber: phone,
          fail: () => {
            uni.showToast({ title: '拨号失败', icon: 'none' });
          },
        });
      }
    },
  });
};

const normalizePhone = (v: string) => v.replace(/\s+/g, '').trim();
const isMobilePhone = (v: string) => /^1[3-9]\d{9}$/.test(v);

const submitInquiry = async () => {
  const spaceId = id.value.trim();
  if (!spaceId) {
    uni.showToast({ title: '缺少空间 ID', icon: 'none' });
    return;
  }

  const phone = normalizePhone(form.contact_phone);
  const msg = form.message.trim();

  if (!phone) {
    uni.showToast({ title: '请输入手机号', icon: 'none' });
    return;
  }
  if (!isMobilePhone(phone)) {
    uni.showToast({ title: '手机号格式不正确', icon: 'none' });
    return;
  }
  if (!msg) {
    uni.showToast({ title: '请输入留言', icon: 'none' });
    return;
  }

  submitLoading.value = true;
  submitError.value = '';
  try {
    await request({
      url: `/coliving/spaces/${encodeURIComponent(spaceId)}/inquiries`,
      method: 'POST',
      data: {
        contact_name: form.contact_name.trim() || null,
        contact_phone: phone,
        message: msg,
      },
    });
    uni.showToast({ title: '提交成功', icon: 'success' });
    setTimeout(() => {
      closeInquiry();
    }, 350);
  } catch (err: any) {
    const detail = err?.data?.detail || err?.errMsg || '提交失败，请稍后重试';
    submitError.value = String(detail);
  } finally {
    submitLoading.value = false;
  }
};
</script>

<style scoped lang="scss">
.page { padding: $ymd-space-3 $ymd-space-3 28px; }
.hero { width: 100%; height: 180px; border-radius: $ymd-radius-lg; box-shadow: $ymd-shadow-sm; }
.card { margin-top: 12px; background: $ymd-color-card; border: 1px solid $ymd-color-line; border-radius: $ymd-radius-lg; padding: 14px; box-shadow: $ymd-shadow-xs; }
.title { font-size: 18px; font-weight: 800; color: $ymd-color-text; }
.sub { margin-top: 6px; font-size: $ymd-font-sm; color: $ymd-color-muted; }
.divider { height: 1px; background: $ymd-color-line; margin: 14px 0; }
.kv { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; }
.k { font-size: 13px; color: $ymd-color-muted; }
.v { font-size: 13px; color: $ymd-color-text; font-weight: 700; }
.desc { font-size: 13px; color: $ymd-color-text; opacity: .78; line-height: 20px; }
.cta { margin-top: 14px; border-radius: $ymd-radius-md; height: 44px; line-height: 44px; font-weight: 700; }

.modal-mask { position: fixed; top: 0; right: 0; bottom: 0; left: 0; background: rgba(15, 23, 42, .48); display: flex; align-items: flex-end; justify-content: center; padding: 14px; z-index: 999; }
.modal { width: 100%; max-width: 520px; background: $ymd-color-card; border: 1px solid $ymd-color-line; border-radius: $ymd-radius-lg; box-shadow: $ymd-shadow-sm; overflow: hidden; }
.modal-hd { display: flex; align-items: center; justify-content: space-between; padding: 14px; border-bottom: 1px solid $ymd-color-line; }
.modal-title { font-size: 16px; font-weight: 900; color: $ymd-color-text; }
.modal-close { width: 28px; height: 28px; line-height: 28px; text-align: center; font-size: 20px; color: $ymd-color-muted; }
.modal-bd { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.field { display: flex; flex-direction: column; gap: 8px; }
.label { font-size: $ymd-font-sm; color: $ymd-color-text; font-weight: 700; }
.input { background: rgba(15, 23, 42, 0.04); border-radius: $ymd-radius-md; padding: 12px; font-size: 14px; }
.textarea { background: rgba(15, 23, 42, 0.04); border-radius: $ymd-radius-md; padding: 12px; font-size: 14px; min-height: 92px; width: 100%; box-sizing: border-box; }
.error { background: rgba(239, 68, 68, .08); border: 1px solid rgba(239, 68, 68, .22); border-radius: $ymd-radius-md; padding: 10px 12px; }
.error-text { font-size: 12px; color: #dc2626; font-weight: 700; }
.modal-ft { display: flex; gap: 10px; padding: 14px; border-top: 1px solid $ymd-color-line; }
.btn { flex: 1; border-radius: $ymd-radius-md; height: 44px; line-height: 44px; font-weight: 800; }
.ghost { background: rgba(15, 23, 42, 0.04); color: $ymd-color-text; }
</style>
