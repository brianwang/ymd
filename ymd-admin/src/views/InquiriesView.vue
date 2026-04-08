<template>
  <div class="card adm-panel">
    <div class="adm-panel-head bordered">
      <div>
        <div class="adm-hint">空间咨询线索列表，支持筛选与跟进标记</div>
        <div class="adm-filters">
          <select v-model="status" class="input f sm">
            <option value="">全部状态</option>
            <option value="new">新线索</option>
            <option value="contacted">已联系</option>
            <option value="closed">已关闭</option>
          </select>
          <input v-model="keyword" class="input f" placeholder="关键字：姓名/手机号/留言/备注/ID/space_id" @keyup.enter="applyFilters" />
          <button class="btn primary" :disabled="loading" @click="applyFilters">筛选</button>
          <button class="btn" :disabled="loading" @click="resetFilters">重置</button>
        </div>
        <div class="adm-hint" style="margin-top: 8px;">{{ rangeText }}</div>
      </div>
      <div class="adm-actions">
        <button class="btn ghost" :disabled="loading" @click="reload">刷新</button>
        <button class="btn" :disabled="loading || offset === 0" @click="prev">上一页</button>
        <button class="btn" :disabled="loading || offset + limit >= total" @click="next">下一页</button>
      </div>
    </div>

    <div v-if="error" class="adm-state error">{{ error }}</div>
    <div v-else-if="loading" class="adm-state">加载中…</div>
    <div v-else-if="items.length === 0" class="adm-state">暂无咨询线索</div>

    <div v-else class="adm-table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th style="width: 72px;">ID</th>
            <th style="width: 90px;">SpaceID</th>
            <th style="width: 140px;">联系人</th>
            <th style="width: 150px;">手机号</th>
            <th style="width: 130px;">状态</th>
            <th style="width: 170px;">创建时间</th>
            <th style="width: 420px;">备注</th>
            <th style="width: 200px;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="it in items" :key="it.id">
            <td>{{ it.id }}</td>
            <td>{{ it.space_id }}</td>
            <td>{{ it.contact_name || '-' }}</td>
            <td>{{ it.contact_phone }}</td>
            <td>
              <select v-model="drafts[it.id].status" class="input s" :disabled="savingId === it.id">
                <option value="new">新线索</option>
                <option value="contacted">已联系</option>
                <option value="closed">已关闭</option>
              </select>
            </td>
            <td>{{ formatTime(it.created_at) }}</td>
            <td>
              <textarea v-model="drafts[it.id].admin_note" class="input note" :disabled="savingId === it.id" rows="2" />
            </td>
            <td>
              <div class="ops">
                <button class="btn primary" :disabled="savingId === it.id || !isDirty(it)" @click="save(it)">
                  {{ savingId === it.id ? '保存中…' : '保存' }}
                </button>
                <button class="btn ghost" :disabled="savingId === it.id || !isDirty(it)" @click="resetRow(it)">撤销</button>
              </div>
              <div v-if="rowErrors[it.id]" class="row-err">{{ rowErrors[it.id] }}</div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { api } from '../utils/request';

type InquiryStatus = 'new' | 'contacted' | 'closed';

type Inquiry = {
  id: number;
  space_id: number;
  contact_name: string | null;
  contact_phone: string;
  status: InquiryStatus;
  created_at: string;
  admin_note: string | null;
};

type InquiryListOut = {
  total: number;
  limit: number;
  offset: number;
  items: Inquiry[];
};

const items = ref<Inquiry[]>([]);
const total = ref(0);
const loading = ref(false);
const error = ref('');
const savingId = ref<number | null>(null);

const limit = 50;
const offset = ref(0);
const status = ref('');
const keyword = ref('');

const drafts = ref<Record<number, { status: InquiryStatus; admin_note: string }>>({});
const rowErrors = ref<Record<number, string>>({});

const rangeText = computed(() => {
  if (total.value === 0) return '共 0 条';
  const start = Math.min(total.value, offset.value + 1);
  const end = Math.min(total.value, offset.value + items.value.length);
  return `共 ${total.value} 条，显示 ${start}-${end}`;
});

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
  if (status.value) params.set('status', status.value);
  if (keyword.value.trim()) params.set('keyword', keyword.value.trim());
  return params.toString();
};

const syncDrafts = (list: Inquiry[]) => {
  const next: Record<number, { status: InquiryStatus; admin_note: string }> = {};
  for (const it of list) {
    next[it.id] = { status: it.status, admin_note: it.admin_note || '' };
  }
  drafts.value = next;
  rowErrors.value = {};
};

const fetchList = async () => {
  loading.value = true;
  error.value = '';
  try {
    const data = await api<InquiryListOut>(`/admin/coliving/inquiries?${buildQuery()}`);
    items.value = data.items;
    total.value = data.total;
    syncDrafts(data.items);
  } catch (err: any) {
    error.value = err?.message || '加载失败';
    items.value = [];
    total.value = 0;
    drafts.value = {};
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

const resetFilters = async () => {
  status.value = '';
  keyword.value = '';
  offset.value = 0;
  await fetchList();
};

const normalizeNote = (v: string | null | undefined) => (v || '').trim();

const isDirty = (it: Inquiry) => {
  const d = drafts.value[it.id];
  if (!d) return false;
  return d.status !== it.status || normalizeNote(d.admin_note) !== normalizeNote(it.admin_note);
};

const resetRow = (it: Inquiry) => {
  drafts.value[it.id] = { status: it.status, admin_note: it.admin_note || '' };
  rowErrors.value = { ...rowErrors.value, [it.id]: '' };
};

const save = async (it: Inquiry) => {
  const d = drafts.value[it.id];
  if (!d) return;

  const payload: any = {};
  const noteChanged = normalizeNote(d.admin_note) !== normalizeNote(it.admin_note);
  const statusChanged = d.status !== it.status;

  if (statusChanged) payload.status = d.status;
  if (noteChanged) payload.admin_note = normalizeNote(d.admin_note) ? normalizeNote(d.admin_note) : null;
  if (noteChanged && payload.status == null) payload.status = d.status;
  if (Object.keys(payload).length === 0) return;

  savingId.value = it.id;
  rowErrors.value = { ...rowErrors.value, [it.id]: '' };
  try {
    const updated = await api<Inquiry>(`/admin/coliving/inquiries/${it.id}`, { method: 'PATCH', body: payload });
    items.value = items.value.map((x) => (x.id === it.id ? updated : x));
    drafts.value[it.id] = { status: updated.status, admin_note: updated.admin_note || '' };
  } catch (err: any) {
    rowErrors.value = { ...rowErrors.value, [it.id]: err?.message || '保存失败' };
  } finally {
    savingId.value = null;
  }
};

onMounted(fetchList);
</script>

<style scoped>
.f { width: 320px; }
.f.sm { width: 140px; }
.s { width: 120px; }
.note { height: auto; min-height: 44px; padding: 8px 12px; resize: vertical; }
.ops { display: flex; gap: 8px; align-items: center; }
.row-err { margin-top: 6px; font-size: 12px; color: var(--danger); }
</style>
