<template>
  <div class="card adm-panel">
    <div class="adm-panel-head bordered">
      <div>
        <div class="adm-hint">活动 #{{ eventId }} 报名名单</div>
        <div class="adm-filters">
          <select v-model="statusFilter" class="input f sm">
            <option value="">全部</option>
            <option value="registered">已报名</option>
            <option value="canceled">已取消</option>
          </select>
          <button class="btn primary" :disabled="loading" @click="applyFilters">筛选</button>
        </div>
      </div>
      <div class="adm-actions">
        <button class="btn" :disabled="loading" @click="back">返回</button>
        <button class="btn ghost" :disabled="loading" @click="reload">刷新</button>
        <button class="btn" :disabled="loading || offset === 0" @click="prev">上一页</button>
        <button class="btn" :disabled="loading || items.length < limit" @click="next">下一页</button>
      </div>
    </div>

    <div v-if="error" class="adm-state error">{{ error }}</div>
    <div v-else-if="loading" class="adm-state">加载中…</div>

    <div v-else class="adm-table-wrap">
      <table class="table">
      <thead>
        <tr>
          <th style="width: 72px;">ID</th>
          <th style="width: 90px;">用户ID</th>
          <th style="width: 120px;">姓名</th>
          <th style="width: 150px;">手机号</th>
          <th>备注</th>
          <th style="width: 110px;">状态</th>
          <th style="width: 170px;">报名时间</th>
          <th style="width: 170px;">取消时间</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="it in items" :key="it.id">
          <td>{{ it.id }}</td>
          <td>{{ it.user_id }}</td>
          <td>{{ it.name }}</td>
          <td>{{ it.phone }}</td>
          <td><div class="remark">{{ it.remark || '-' }}</div></td>
          <td>
            <span class="pill" :class="it.status === 'registered' ? 'on' : 'off'">
              {{ it.status === 'registered' ? '已报名' : '已取消' }}
            </span>
          </td>
          <td>{{ formatTime(it.created_at) }}</td>
          <td>{{ it.canceled_at ? formatTime(it.canceled_at) : '-' }}</td>
        </tr>
      </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { api } from '../utils/request';

type Registration = {
  id: number;
  event_id: number;
  user_id: number;
  name: string;
  phone: string;
  remark: string | null;
  status: string;
  created_at: string;
  canceled_at: string | null;
};

const route = useRoute();
const router = useRouter();

const eventId = String(route.params.id || '');

const items = ref<Registration[]>([]);
const loading = ref(false);
const error = ref('');

const limit = 200;
const offset = ref(0);
const statusFilter = ref('');

const formatTime = (raw: string) => {
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return raw;
  return d.toLocaleString();
};

const buildQuery = () => {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset.value),
  });
  if (statusFilter.value) params.set('status', statusFilter.value);
  return params.toString();
};

const fetchList = async () => {
  loading.value = true;
  error.value = '';
  try {
    items.value = await api<Registration[]>(`/admin/events/${eventId}/registrations?${buildQuery()}`);
  } catch (err: any) {
    error.value = err?.message || '加载失败';
  } finally {
    loading.value = false;
  }
};

const reload = async () => {
  await fetchList();
};

const prev = async () => {
  offset.value = Math.max(0, offset.value - limit);
  await fetchList();
};

const next = async () => {
  offset.value = offset.value + limit;
  await fetchList();
};

const applyFilters = async () => {
  offset.value = 0;
  await fetchList();
};

const back = async () => {
  await router.push('/events');
};

onMounted(fetchList);
</script>

<style scoped>
.f.sm { width: 160px; }
.remark { max-width: 520px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
