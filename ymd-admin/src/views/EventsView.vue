<template>
  <div class="card adm-panel">
    <div class="adm-panel-head bordered">
      <div>
        <div class="adm-hint">创建、编辑、发布活动，并查看报名名单</div>
        <div class="adm-filters">
          <input v-model="q" class="input f" placeholder="标题 / 城市 / 分类" @keyup.enter="applyFilters" />
          <select v-model="isPublished" class="input f sm">
            <option value="">全部状态</option>
            <option value="true">已发布</option>
            <option value="false">未发布</option>
          </select>
          <button class="btn primary" :disabled="loading" @click="applyFilters">筛选</button>
          <button class="btn" :disabled="loading" @click="resetFilters">重置</button>
        </div>
      </div>
      <div class="adm-actions">
        <button class="btn primary" :disabled="loading" @click="openCreate">新建活动</button>
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
          <th>标题</th>
          <th style="width: 110px;">城市</th>
          <th style="width: 110px;">分类</th>
          <th style="width: 170px;">开始时间</th>
          <th style="width: 170px;">报名截止</th>
          <th style="width: 120px;">名额</th>
          <th style="width: 100px;">发布</th>
          <th style="width: 360px;">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="it in items" :key="it.id">
          <td>{{ it.id }}</td>
          <td>{{ it.title }}</td>
          <td>{{ it.city }}</td>
          <td>{{ it.category }}</td>
          <td>{{ formatTime(it.start_at) }}</td>
          <td>{{ formatTime(it.signup_deadline_at) }}</td>
          <td>{{ capacityText(it) }}</td>
          <td>
            <span class="pill" :class="it.is_published ? 'on' : 'off'">{{ it.is_published ? '已发布' : '未发布' }}</span>
          </td>
          <td>
            <div class="ops">
              <button class="btn" :disabled="loadingRowId === it.id" @click="openEdit(it)">编辑</button>
              <button class="btn" :disabled="loadingRowId === it.id" @click="togglePublish(it)">
                {{ it.is_published ? '下架' : '发布' }}
              </button>
              <button class="btn" :disabled="loadingRowId === it.id" @click="openRegistrations(it)">报名名单</button>
            </div>
          </td>
        </tr>
      </tbody>
      </table>
    </div>

    <div v-if="modalOpen" class="modal">
      <div class="modal-card card">
        <div class="modal-head">
          <div class="modal-title">{{ editingId == null ? '新建活动' : `编辑活动 #${editingId}` }}</div>
          <button class="btn ghost" :disabled="saving" @click="closeModal">关闭</button>
        </div>
        <div class="modal-body">
          <div class="grid">
            <label class="lbl">
              <div class="lbl-t">标题</div>
              <input v-model="form.title" class="input" />
            </label>
            <label class="lbl">
              <div class="lbl-t">分类</div>
              <input v-model="form.category" class="input" />
            </label>
            <label class="lbl">
              <div class="lbl-t">城市</div>
              <input v-model="form.city" class="input" />
            </label>
            <label class="lbl">
              <div class="lbl-t">地址</div>
              <input v-model="form.address" class="input" />
            </label>
            <label class="lbl">
              <div class="lbl-t">封面 URL</div>
              <input v-model="form.cover_url" class="input" />
            </label>
            <label class="lbl">
              <div class="lbl-t">名额（空=无限）</div>
              <input v-model="form.capacity" class="input" type="number" />
            </label>
            <label class="lbl">
              <div class="lbl-t">开始时间</div>
              <input v-model="form.start_at" class="input" type="datetime-local" />
            </label>
            <label class="lbl">
              <div class="lbl-t">结束时间（可空）</div>
              <input v-model="form.end_at" class="input" type="datetime-local" />
            </label>
            <label class="lbl">
              <div class="lbl-t">报名截止</div>
              <input v-model="form.signup_deadline_at" class="input" type="datetime-local" />
            </label>
          </div>

          <label class="lbl">
            <div class="lbl-t">简介</div>
            <textarea v-model="form.summary" class="ta" rows="3" />
          </label>
          <label class="lbl">
            <div class="lbl-t">详情</div>
            <textarea v-model="form.content" class="ta" rows="6" />
          </label>
        </div>
        <div class="modal-foot">
          <button class="btn primary" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { api } from '../utils/request';

type AdminEvent = {
  id: number;
  title: string;
  category: string;
  city: string;
  address: string | null;
  cover_url: string | null;
  summary: string | null;
  content: string | null;
  start_at: string;
  end_at: string | null;
  signup_deadline_at: string;
  capacity: number | null;
  registered_count: number;
  is_published: boolean;
  published_at: string | null;
};

const router = useRouter();

const items = ref<AdminEvent[]>([]);
const loading = ref(false);
const error = ref('');
const loadingRowId = ref<number | null>(null);

const limit = 50;
const offset = ref(0);
const q = ref('');
const isPublished = ref('');

const modalOpen = ref(false);
const saving = ref(false);
const editingId = ref<number | null>(null);
const form = ref({
  title: '',
  category: '',
  city: '',
  address: '',
  cover_url: '',
  summary: '',
  content: '',
  start_at: '',
  end_at: '',
  signup_deadline_at: '',
  capacity: '',
});

const toLocalInput = (raw: string | null | undefined) => {
  if (!raw) return '';
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return '';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

const fromLocalInputToISO = (raw: string) => {
  if (!raw) return null;
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
};

const formatTime = (raw: string) => {
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return raw;
  return d.toLocaleString();
};

const capacityText = (it: AdminEvent) => {
  if (it.capacity == null) return `${it.registered_count}/∞`;
  return `${it.registered_count}/${it.capacity}`;
};

const buildQuery = () => {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset.value),
  });
  if (q.value.trim()) params.set('q', q.value.trim());
  if (isPublished.value) params.set('is_published', isPublished.value);
  return params.toString();
};

const fetchList = async () => {
  loading.value = true;
  error.value = '';
  try {
    items.value = await api<AdminEvent[]>(`/admin/events?${buildQuery()}`);
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

const resetFilters = async () => {
  q.value = '';
  isPublished.value = '';
  offset.value = 0;
  await fetchList();
};

const openCreate = () => {
  editingId.value = null;
  const now = new Date();
  const start = new Date(now.getTime() + 86400000);
  const deadline = new Date(start.getTime() - 3600000);
  form.value = {
    title: '',
    category: '',
    city: '',
    address: '',
    cover_url: '',
    summary: '',
    content: '',
    start_at: toLocalInput(start.toISOString()),
    end_at: '',
    signup_deadline_at: toLocalInput(deadline.toISOString()),
    capacity: '',
  };
  modalOpen.value = true;
};

const openEdit = (it: AdminEvent) => {
  editingId.value = it.id;
  form.value = {
    title: it.title,
    category: it.category,
    city: it.city,
    address: it.address || '',
    cover_url: it.cover_url || '',
    summary: it.summary || '',
    content: it.content || '',
    start_at: toLocalInput(it.start_at),
    end_at: toLocalInput(it.end_at || ''),
    signup_deadline_at: toLocalInput(it.signup_deadline_at),
    capacity: it.capacity == null ? '' : String(it.capacity),
  };
  modalOpen.value = true;
};

const closeModal = () => {
  modalOpen.value = false;
  saving.value = false;
  editingId.value = null;
};

const save = async () => {
  const payload: any = {
    title: form.value.title.trim(),
    category: form.value.category.trim(),
    city: form.value.city.trim(),
    address: form.value.address.trim() || null,
    cover_url: form.value.cover_url.trim() || null,
    summary: form.value.summary || null,
    content: form.value.content || null,
    start_at: fromLocalInputToISO(form.value.start_at),
    end_at: fromLocalInputToISO(form.value.end_at),
    signup_deadline_at: fromLocalInputToISO(form.value.signup_deadline_at),
    capacity: form.value.capacity === '' ? null : Number(form.value.capacity),
  };

  if (!payload.title || !payload.category || !payload.city) {
    window.alert('标题/分类/城市必填');
    return;
  }
  if (!payload.start_at || !payload.signup_deadline_at) {
    window.alert('开始时间/报名截止必填');
    return;
  }
  if (payload.capacity != null && (!Number.isFinite(payload.capacity) || payload.capacity < 0)) {
    window.alert('名额需为非负整数或留空');
    return;
  }

  saving.value = true;
  try {
    if (editingId.value == null) {
      const created = await api<AdminEvent>('/admin/events', { method: 'POST', body: payload });
      items.value = [created, ...items.value];
    } else {
      const updated = await api<AdminEvent>(`/admin/events/${editingId.value}`, { method: 'PUT', body: payload });
      items.value = items.value.map((it) => (it.id === updated.id ? updated : it));
    }
    closeModal();
  } catch (err: any) {
    window.alert(err?.message || '保存失败');
  } finally {
    saving.value = false;
  }
};

const togglePublish = async (it: AdminEvent) => {
  loadingRowId.value = it.id;
  try {
    const updated = await api<AdminEvent>(`/admin/events/${it.id}/publish`, {
      method: 'PATCH',
      body: { is_published: !it.is_published },
    });
    items.value = items.value.map((x) => (x.id === updated.id ? updated : x));
  } catch (err: any) {
    window.alert(err?.message || '操作失败');
  } finally {
    loadingRowId.value = null;
  }
};

const openRegistrations = async (it: AdminEvent) => {
  await router.push(`/events/${it.id}/registrations`);
};

onMounted(fetchList);
</script>

<style scoped>
.f { width: 260px; }
.f.sm { width: 130px; }
.ops { display: flex; gap: 8px; flex-wrap: wrap; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.lbl { display: flex; flex-direction: column; gap: 6px; }
.lbl-t { font-size: 12px; color: var(--muted); }
.ta { width: 100%; border: 1px solid var(--border); border-radius: 12px; padding: 10px; background: #fff; color: inherit; resize: vertical; }
</style>
