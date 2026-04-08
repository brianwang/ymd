<template>
  <div class="adm-shell">
    <aside class="adm-sidebar">
      <div class="adm-sidebar-card card">
        <div class="adm-brand">
          <div class="adm-brand-title">游牧岛管理后台</div>
          <div class="adm-brand-sub">Admin Console</div>
        </div>
        <nav class="adm-nav">
          <RouterLink class="adm-nav-item" to="/users" active-class="active">用户</RouterLink>
          <RouterLink class="adm-nav-item" to="/posts" active-class="active">帖子</RouterLink>
          <RouterLink class="adm-nav-item" to="/comments" active-class="active">评论</RouterLink>
          <RouterLink class="adm-nav-item" to="/reward-config" active-class="active">奖励配置</RouterLink>
          <RouterLink class="adm-nav-item" to="/events" active-class="active">活动</RouterLink>
          <RouterLink class="adm-nav-item" to="/inquiries" active-class="active">咨询线索</RouterLink>
        </nav>
        <div class="adm-sidebar-foot">
          <div class="adm-sidebar-meta">管理端 API：/api/v1/admin/*</div>
          <button class="btn ghost" @click="logout">退出登录</button>
        </div>
      </div>
    </aside>

    <div class="adm-main">
      <header class="adm-titlebar">
        <div class="adm-titlebar-inner">
          <div>
            <div class="adm-title">{{ title }}</div>
            <div class="adm-subtitle">{{ subtitle }}</div>
          </div>
          <div class="adm-title-actions">
            <button class="btn ghost" @click="logout">退出登录</button>
          </div>
        </div>
      </header>

      <main class="adm-content">
        <div class="adm-content-inner">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '../store/auth';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const title = computed(() => {
  if (route.name === 'users') return '用户列表';
  if (route.name === 'posts') return '帖子列表';
  if (route.name === 'comments') return '评论列表';
  if (route.name === 'reward-config') return '奖励配置';
  if (route.name === 'events') return '活动管理';
  if (route.name === 'event-registrations') return '报名名单';
  if (route.name === 'inquiries') return '咨询线索';
  return '控制台';
});

const subtitle = computed(() => {
  if (route.name === 'users') return '用户状态、管理员权限与积分管理';
  if (route.name === 'posts') return '帖子筛选与删除（含评论与点赞清理）';
  if (route.name === 'comments') return '评论筛选与删除（回写评论数）';
  if (route.name === 'reward-config') return '运营参数配置（保存后立即生效）';
  if (route.name === 'events') return '活动创建、发布与报名管理';
  if (route.name === 'event-registrations') return '查看活动报名名单';
  if (route.name === 'inquiries') return '空间咨询线索筛选、备注与状态更新';
  return '管理后台';
});

const logout = async () => {
  auth.logout();
  await router.replace('/login');
};
</script>
