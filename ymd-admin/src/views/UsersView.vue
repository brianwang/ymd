<template>
  <div class="card adm-panel">
    <div class="adm-panel-head bordered">
      <div>
        <div class="adm-hint">支持启用/禁用、管理员权限与积分管理</div>
        <div class="adm-filters">
          <input v-model="q" class="input f" placeholder="邮箱 / OpenID / 昵称" @keyup.enter="applyFilters" />
          <select v-model="isActive" class="input f sm">
            <option value="">全部状态</option>
            <option value="true">启用</option>
            <option value="false">禁用</option>
          </select>
          <select v-model="isSuperuser" class="input f sm">
            <option value="">全部角色</option>
            <option value="true">管理员</option>
            <option value="false">非管理员</option>
          </select>
          <button class="btn primary" :disabled="loading" @click="applyFilters">筛选</button>
          <button class="btn" :disabled="loading" @click="resetFilters">重置</button>
        </div>
      </div>
      <div class="adm-actions">
        <button class="btn ghost" :disabled="loading" @click="reload">刷新</button>
        <button class="btn" :disabled="loading || offset === 0" @click="prev">上一页</button>
        <button class="btn" :disabled="loading || users.length < limit" @click="next">下一页</button>
      </div>
    </div>

    <div v-if="error" class="adm-state error">{{ error }}</div>
    <div v-else-if="loading" class="adm-state">加载中…</div>

    <div v-else class="adm-table-wrap">
      <table class="table">
      <thead>
        <tr>
          <th style="width: 72px;">ID</th>
          <th style="width: 220px;">邮箱</th>
          <th style="width: 220px;">OpenID</th>
          <th>昵称</th>
          <th style="width: 110px;">状态</th>
          <th style="width: 90px;">管理员</th>
          <th style="width: 90px;">积分</th>
          <th style="width: 280px;">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in users" :key="u.id">
          <td>{{ u.id }}</td>
          <td>{{ u.email || '-' }}</td>
          <td>{{ u.open_id || '-' }}</td>
          <td>{{ u.nickname || '-' }}</td>
          <td>
            <span class="pill" :class="u.is_active ? 'on' : 'off'">{{ u.is_active ? '启用' : '禁用' }}</span>
          </td>
          <td>
            <span class="pill" :class="u.is_superuser ? 'on' : ''">{{ u.is_superuser ? '是' : '否' }}</span>
          </td>
          <td>{{ u.points }}</td>
          <td>
            <div class="ops">
              <button class="btn" :disabled="loadingRowId === u.id" @click="toggleActive(u)">
                {{ u.is_active ? '禁用' : '启用' }}
              </button>

              <details class="adm-menu" :data-user="u.id">
                <summary class="btn ghost">更多</summary>
                <div class="adm-menu-panel card">
                  <button class="btn ghost adm-menu-item" :disabled="loadingRowId === u.id" @click="toggleSuperuser(u, $event)">
                    {{ u.is_superuser ? '取消管理员' : '设为管理员' }}
                  </button>
                  <button class="btn ghost adm-menu-item" :disabled="loadingRowId === u.id" @click="adjustPoints(u, $event)">调积分</button>
                  <button class="btn ghost adm-menu-item" :disabled="loadingRowId === u.id" @click="openLedger(u, $event)">积分流水</button>
                </div>
              </details>
            </div>
          </td>
        </tr>
      </tbody>
      </table>
    </div>

    <div v-if="ledgerOpen" class="modal" @click.self="closeLedger">
      <div class="modal-card card">
        <div class="modal-head">
          <div class="modal-title">积分流水</div>
          <button class="btn ghost" @click="closeLedger">关闭</button>
        </div>
        <div class="modal-body">
          <div class="adm-hint" style="margin-bottom: 12px;">用户 ID：{{ ledgerUserId }}</div>
          <div v-if="ledgerError" class="adm-state error">{{ ledgerError }}</div>
          <div v-else-if="ledgerLoading" class="adm-state">加载中…</div>
          <div v-else class="adm-table-wrap" style="margin-top: 0;">
            <table class="table">
              <thead>
                <tr>
                  <th style="width: 72px;">ID</th>
                  <th style="width: 160px;">时间</th>
                  <th style="width: 160px;">类型</th>
                  <th style="width: 90px;">变化</th>
                  <th>BizKey</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="it in ledgerItems" :key="it.id">
                  <td>{{ it.id }}</td>
                  <td>{{ formatTime(it.created_at) }}</td>
                  <td>{{ it.event_type }}</td>
                  <td>
                    <span class="pill" :class="it.delta >= 0 ? 'on' : 'off'">{{ it.delta }}</span>
                  </td>
                  <td><div class="biz">{{ it.biz_key }}</div></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="modal-foot">
          <button class="btn ghost" :disabled="ledgerLoading" @click="fetchLedger">刷新</button>
          <button class="btn" :disabled="ledgerLoading || ledgerOffset === 0" @click="ledgerPrev">上一页</button>
          <button class="btn" :disabled="ledgerLoading || ledgerItems.length < ledgerLimit" @click="ledgerNext">下一页</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { api } from '../utils/request';

type AdminUser = {
  id: number;
  email: string | null;
  open_id: string | null;
  nickname: string | null;
  is_active: boolean;
  is_superuser: boolean;
  points: number;
};

const users = ref<AdminUser[]>([]);
const loading = ref(false);
const error = ref('');
const loadingRowId = ref<number | null>(null);

const limit = 50;
const offset = ref(0);

const q = ref('');
const isActive = ref('');
const isSuperuser = ref('');

type LedgerItem = {
  id: number;
  event_type: string;
  biz_key: string;
  delta: number;
  created_at: string;
};

const ledgerOpen = ref(false);
const ledgerUserId = ref<number | null>(null);
const ledgerItems = ref<LedgerItem[]>([]);
const ledgerLoading = ref(false);
const ledgerError = ref('');
const ledgerLimit = 50;
const ledgerOffset = ref(0);

const buildQuery = () => {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset.value),
  });
  if (q.value.trim()) params.set('q', q.value.trim());
  if (isActive.value) params.set('is_active', isActive.value);
  if (isSuperuser.value) params.set('is_superuser', isSuperuser.value);
  return params.toString();
};

const fetchUsers = async () => {
  loading.value = true;
  error.value = '';
  try {
    const qs = buildQuery();
    users.value = await api<AdminUser[]>(`/admin/users?${qs}`);
  } catch (err: any) {
    error.value = err?.message || '加载失败';
  } finally {
    loading.value = false;
  }
};

const reload = async () => {
  await fetchUsers();
};

const prev = async () => {
  offset.value = Math.max(0, offset.value - limit);
  await fetchUsers();
};

const next = async () => {
  offset.value = offset.value + limit;
  await fetchUsers();
};

const applyFilters = async () => {
  offset.value = 0;
  await fetchUsers();
};

const resetFilters = async () => {
  q.value = '';
  isActive.value = '';
  isSuperuser.value = '';
  offset.value = 0;
  await fetchUsers();
};

const closeDetails = (evt: Event) => {
  const el = evt.target as HTMLElement | null;
  const details = el?.closest?.('details') as HTMLDetailsElement | null;
  details?.removeAttribute('open');
};

const toggleActive = async (u: AdminUser) => {
  loadingRowId.value = u.id;
  try {
    const updated = await api<AdminUser>(`/admin/users/${u.id}/active`, {
      method: 'PATCH',
      body: { is_active: !u.is_active },
    });
    users.value = users.value.map((it) => (it.id === u.id ? updated : it));
  } catch (err: any) {
    window.alert(err?.message || '操作失败');
  } finally {
    loadingRowId.value = null;
  }
};

const toggleSuperuser = async (u: AdminUser, evt?: Event) => {
  if (evt) closeDetails(evt);
  loadingRowId.value = u.id;
  try {
    const updated = await api<AdminUser>(`/admin/users/${u.id}/superuser`, {
      method: 'PATCH',
      body: { is_superuser: !u.is_superuser },
    });
    users.value = users.value.map((it) => (it.id === u.id ? updated : it));
  } catch (err: any) {
    window.alert(err?.message || '操作失败');
  } finally {
    loadingRowId.value = null;
  }
};

const adjustPoints = async (u: AdminUser, evt?: Event) => {
  if (evt) closeDetails(evt);
  const raw = window.prompt(`调整用户 ${u.id} 的积分（可负数）`, '10');
  if (raw == null) return;
  const delta = Number(raw);
  if (!Number.isFinite(delta) || Number.isNaN(delta) || !Number.isInteger(delta)) {
    window.alert('请输入整数');
    return;
  }
  loadingRowId.value = u.id;
  try {
    const res = await api<{ user_id: number; delta: number; points: number }>(`/admin/users/${u.id}/points-adjust`, {
      method: 'POST',
      body: { delta },
    });
    users.value = users.value.map((it) => (it.id === u.id ? { ...it, points: res.points } : it));
  } catch (err: any) {
    window.alert(err?.message || '操作失败');
  } finally {
    loadingRowId.value = null;
  }
};

const formatTime = (raw: string) => {
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return raw;
  return d.toLocaleString();
};

const openLedger = async (u: AdminUser, evt?: Event) => {
  if (evt) closeDetails(evt);
  ledgerUserId.value = u.id;
  ledgerOffset.value = 0;
  ledgerOpen.value = true;
  await fetchLedger();
};

const closeLedger = () => {
  ledgerOpen.value = false;
  ledgerUserId.value = null;
  ledgerItems.value = [];
  ledgerError.value = '';
  ledgerLoading.value = false;
  ledgerOffset.value = 0;
};

const fetchLedger = async () => {
  if (ledgerUserId.value == null) return;
  ledgerLoading.value = true;
  ledgerError.value = '';
  try {
    const params = new URLSearchParams({
      limit: String(ledgerLimit),
      offset: String(ledgerOffset.value),
    });
    ledgerItems.value = await api<LedgerItem[]>(`/admin/users/${ledgerUserId.value}/ledger?${params.toString()}`);
  } catch (err: any) {
    ledgerError.value = err?.message || '加载失败';
  } finally {
    ledgerLoading.value = false;
  }
};

const ledgerPrev = async () => {
  ledgerOffset.value = Math.max(0, ledgerOffset.value - ledgerLimit);
  await fetchLedger();
};

const ledgerNext = async () => {
  ledgerOffset.value = ledgerOffset.value + ledgerLimit;
  await fetchLedger();
};

onMounted(fetchUsers);
</script>

<style scoped>
.ops { display: flex; gap: var(--space-2); align-items: center; }
.f { width: 280px; }
.f.sm { width: 140px; }
.biz { max-width: 560px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.adm-menu-panel { padding: var(--space-2); }
</style>
