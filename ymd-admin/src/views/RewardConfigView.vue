<template>
  <div class="card adm-panel">
    <div class="adm-panel-head bordered">
      <div>
        <div class="adm-hint">配置积分奖励参数（保存后立即生效）</div>
      </div>
      <div class="adm-actions">
        <button class="btn ghost" :disabled="loading || saving" @click="reload">重载</button>
      </div>
    </div>

    <div v-if="error" class="adm-state error">{{ error }}</div>
    <div v-else-if="loading" class="adm-state">加载中…</div>

    <div v-else class="cfg">
      <div class="cfg-groups">
        <div v-for="g in groups" :key="g.title" class="card cfg-group">
          <div class="cfg-group-head">
            <div class="cfg-group-title">{{ g.title }}</div>
            <div class="cfg-group-sub">{{ g.sub }}</div>
          </div>
          <div class="cfg-grid">
            <label v-for="f in g.fields" :key="f.key" class="adm-field">
              <div class="adm-label">{{ f.label }}</div>
              <input class="input" type="number" v-model="form[f.key]" />
            </label>
          </div>
        </div>
      </div>

      <div class="cfg-foot">
        <div class="cfg-foot-left">
          <span class="adm-hint">修改后请点击保存</span>
        </div>
        <div class="cfg-foot-right">
          <button class="btn" :disabled="loading || saving" @click="reload">取消</button>
          <button class="btn primary" :disabled="loading || saving" @click="save">
            {{ saving ? '保存中…' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { api } from '../utils/request';

type RewardConfig = {
  sign_in_points: number;
  inviter_reward_points: number;
  invitee_reward_points: number;
  first_post_points: number;
  post_reward_points: number;
  comment_reward_points: number;
  daily_post_reward_limit: number;
  daily_comment_reward_limit: number;
};

const groups: Array<{
  title: string;
  sub: string;
  fields: Array<{ key: keyof RewardConfig; label: string }>;
}> = [
  {
    title: '奖励规则',
    sub: '用于签到、邀请与内容贡献的积分激励',
    fields: [
      { key: 'sign_in_points', label: '签到积分' },
      { key: 'inviter_reward_points', label: '邀请者奖励积分' },
      { key: 'invitee_reward_points', label: '被邀请者奖励积分' },
      { key: 'first_post_points', label: '首帖奖励积分' },
      { key: 'post_reward_points', label: '发帖奖励积分' },
      { key: 'comment_reward_points', label: '评论奖励积分' },
    ],
  },
  {
    title: '每日上限',
    sub: '防刷与成本控制相关配置',
    fields: [
      { key: 'daily_post_reward_limit', label: '每日发帖奖励上限' },
      { key: 'daily_comment_reward_limit', label: '每日评论奖励上限' },
    ],
  },
];

const form = reactive<Record<keyof RewardConfig, number>>({
  sign_in_points: 0,
  inviter_reward_points: 0,
  invitee_reward_points: 0,
  first_post_points: 0,
  post_reward_points: 0,
  comment_reward_points: 0,
  daily_post_reward_limit: 0,
  daily_comment_reward_limit: 0,
});

const loading = ref(false);
const saving = ref(false);
const error = ref('');

const normalize = (cfg: any): RewardConfig => {
  const pick = (k: keyof RewardConfig) => Number(cfg?.[k] ?? 0);
  return {
    sign_in_points: pick('sign_in_points'),
    inviter_reward_points: pick('inviter_reward_points'),
    invitee_reward_points: pick('invitee_reward_points'),
    first_post_points: pick('first_post_points'),
    post_reward_points: pick('post_reward_points'),
    comment_reward_points: pick('comment_reward_points'),
    daily_post_reward_limit: pick('daily_post_reward_limit'),
    daily_comment_reward_limit: pick('daily_comment_reward_limit'),
  };
};

const load = async () => {
  loading.value = true;
  error.value = '';
  try {
    const cfg = await api<any>('/admin/reward-config');
    const n = normalize(cfg);
    groups.forEach((g) => {
      g.fields.forEach((f) => {
        form[f.key] = n[f.key];
      });
    });
  } catch (err: any) {
    error.value = err?.message || '加载失败';
  } finally {
    loading.value = false;
  }
};

const reload = async () => {
  await load();
};

const save = async () => {
  saving.value = true;
  error.value = '';
  try {
    const body: RewardConfig = normalize(form);
    const saved = await api<any>('/admin/reward-config', { method: 'PUT', body });
    const n = normalize(saved);
    groups.forEach((g) => {
      g.fields.forEach((f) => {
        form[f.key] = n[f.key];
      });
    });
  } catch (err: any) {
    error.value = err?.message || '保存失败';
  } finally {
    saving.value = false;
  }
};

onMounted(load);
</script>

<style scoped>
.cfg { margin-top: var(--space-4); }
.cfg-groups { display: flex; flex-direction: column; gap: var(--space-4); }

.cfg-group { padding: var(--space-5); }
.cfg-group-head { display: flex; flex-direction: column; gap: 4px; padding-bottom: var(--space-4); }
.cfg-group-title { font-weight: 900; letter-spacing: 0.2px; }
.cfg-group-sub { font-size: 12px; color: var(--muted); }

.cfg-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.cfg-foot {
  margin-top: var(--space-5);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.cfg-foot-right { display: flex; gap: var(--space-2); }
</style>
