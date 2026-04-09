<template>
  <div class="card adm-panel">
    <div class="adm-panel-head bordered">
      <div>
        <div class="adm-hint">支持筛选与删除（会同时清理评论与点赞）</div>
        <div class="adm-filters">
          <input v-model="q" class="input f" placeholder="内容关键词" @keyup.enter="applyFilters" />
          <input v-model="userIdRaw" class="input f sm" placeholder="用户ID" @keyup.enter="applyFilters" />
          <input v-model="startDate" class="input f md" type="date" />
          <input v-model="endDate" class="input f md" type="date" />
          <button class="btn primary" :disabled="loading" @click="applyFilters">筛选</button>
          <button class="btn" :disabled="loading" @click="resetFilters">重置</button>
        </div>
      </div>
      <div class="adm-actions">
        <button class="btn ghost" :disabled="loading" @click="reload">刷新</button>
        <button class="btn" :disabled="loading || offset === 0" @click="prev">上一页</button>
        <button class="btn" :disabled="loading || posts.length < limit" @click="next">下一页</button>
      </div>
    </div>

    <div v-if="error" class="adm-state error">{{ error }}</div>
    <div v-else-if="loading" class="adm-state">加载中…</div>

    <div v-else class="adm-table-wrap">
      <table class="table">
      <thead>
        <tr>
          <th style="width: 72px;">ID</th>
          <th style="width: 90px;">用户</th>
          <th>内容</th>
          <th style="width: 90px;">点赞</th>
          <th style="width: 90px;">收藏</th>
          <th style="width: 90px;">转发</th>
          <th style="width: 90px;">评论</th>
          <th style="width: 140px;">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in posts" :key="p.id">
          <td>{{ p.id }}</td>
          <td>{{ p.user_id }}</td>
          <td>
            <div class="content">{{ p.content }}</div>
          </td>
          <td>{{ p.like_count }}</td>
          <td>{{ p.favorite_count }}</td>
          <td>{{ p.share_count }}</td>
          <td>{{ p.comment_count }}</td>
          <td>
            <button class="btn danger" :disabled="loadingRowId === p.id" @click="remove(p)">删除</button>
          </td>
        </tr>
      </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { api } from '../utils/request';

type AdminPost = {
  id: number;
  user_id: number;
  content: string;
  like_count: number;
  favorite_count: number;
  share_count: number;
  comment_count: number;
};

const posts = ref<AdminPost[]>([]);
const loading = ref(false);
const error = ref('');
const loadingRowId = ref<number | null>(null);

const limit = 50;
const offset = ref(0);

const q = ref('');
const userIdRaw = ref('');
const startDate = ref('');
const endDate = ref('');

const parseOptionalInt = (raw: string) => {
  const s = raw.trim();
  if (!s) return undefined;
  const n = Number(s);
  if (!Number.isInteger(n) || n <= 0) return null;
  return n;
};

const buildQuery = () => {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset.value),
  });
  if (q.value.trim()) params.set('q', q.value.trim());

  const userId = parseOptionalInt(userIdRaw.value);
  if (userId === null) throw new Error('用户ID 请输入正整数');
  if (userId !== undefined) params.set('user_id', String(userId));

  if (startDate.value) params.set('start_at', `${startDate.value}T00:00:00Z`);
  if (endDate.value) params.set('end_at', `${endDate.value}T23:59:59Z`);
  return params.toString();
};

const fetchPosts = async () => {
  loading.value = true;
  error.value = '';
  try {
    const qs = buildQuery();
    posts.value = await api<AdminPost[]>(`/admin/posts?${qs}`);
  } catch (err: any) {
    error.value = err?.message || '加载失败';
  } finally {
    loading.value = false;
  }
};

const reload = async () => {
  await fetchPosts();
};

const prev = async () => {
  offset.value = Math.max(0, offset.value - limit);
  await fetchPosts();
};

const next = async () => {
  offset.value = offset.value + limit;
  await fetchPosts();
};

const applyFilters = async () => {
  offset.value = 0;
  await fetchPosts();
};

const resetFilters = async () => {
  q.value = '';
  userIdRaw.value = '';
  startDate.value = '';
  endDate.value = '';
  offset.value = 0;
  await fetchPosts();
};

const remove = async (p: AdminPost) => {
  const ok = window.confirm(`确认删除帖子 ${p.id}？`);
  if (!ok) return;
  loadingRowId.value = p.id;
  try {
    await api(`/admin/posts/${p.id}`, { method: 'DELETE' });
    posts.value = posts.value.filter((it) => it.id !== p.id);
  } catch (err: any) {
    window.alert(err?.message || '删除失败');
  } finally {
    loadingRowId.value = null;
  }
};

onMounted(fetchPosts);
</script>

<style scoped>
.content { white-space: pre-wrap; word-break: break-word; line-height: 18px; }
.f { width: 280px; }
.f.sm { width: 140px; }
.f.md { width: 170px; }
</style>
