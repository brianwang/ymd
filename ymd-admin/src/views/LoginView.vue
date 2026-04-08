<template>
  <div class="login">
    <div class="login-card card">
      <div class="login-head">
        <div class="login-title">游牧岛管理后台</div>
        <div class="login-sub">使用管理员邮箱与密码登录</div>
      </div>

      <div v-if="error" class="login-error">{{ error }}</div>

      <div class="login-form">
        <label class="adm-field">
          <div class="adm-label">邮箱</div>
          <input class="input" v-model="email" placeholder="name@example.com" autocomplete="username" inputmode="email" />
        </label>
        <label class="adm-field">
          <div class="adm-label">密码</div>
          <input class="input" v-model="password" type="password" placeholder="请输入密码" autocomplete="current-password" />
        </label>

        <button class="btn primary login-submit" :disabled="loading" @click="submit">
          {{ loading ? '登录中…' : '登录' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../store/auth';

const router = useRouter();
const auth = useAuthStore();

const email = ref('');
const password = ref('');
const loading = ref(false);
const error = ref('');

const submit = async () => {
  error.value = '';
  const e = email.value.trim();
  if (!e) {
    error.value = '请输入邮箱';
    return;
  }
  if (!password.value) {
    error.value = '请输入密码';
    return;
  }
  loading.value = true;
  try {
    await auth.login(e, password.value);
    await router.replace('/users');
  } catch (err: any) {
    error.value = err?.message || '登录失败';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-7) var(--space-5);
}

.login-card {
  width: min(440px, 100%);
  padding: var(--space-6);
}

.login-head { margin-bottom: var(--space-4); }
.login-title { font-size: 18px; font-weight: 900; letter-spacing: 0.2px; }
.login-sub { margin-top: 6px; font-size: 12px; color: var(--muted); }

.login-form { display: flex; flex-direction: column; gap: var(--space-4); }
.login-submit { width: 100%; height: 40px; font-size: 14px; }

.login-error {
  margin: var(--space-4) 0;
  padding: 10px 12px;
  border: 1px solid rgba(var(--danger-rgb), 0.28);
  background: rgba(var(--danger-rgb), 0.08);
  border-radius: var(--radius-sm);
  color: var(--danger);
  font-size: 13px;
}
</style>
