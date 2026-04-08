import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../store/auth';

import LoginView from '../views/LoginView.vue';
import LayoutView from '../views/LayoutView.vue';
import UsersView from '../views/UsersView.vue';
import PostsView from '../views/PostsView.vue';
import CommentsView from '../views/CommentsView.vue';
import RewardConfigView from '../views/RewardConfigView.vue';
import EventsView from '../views/EventsView.vue';
import EventRegistrationsView from '../views/EventRegistrationsView.vue';
import InquiriesView from '../views/InquiriesView.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
    {
      path: '/',
      component: LayoutView,
      children: [
        { path: '', redirect: '/users' },
        { path: 'users', name: 'users', component: UsersView },
        { path: 'posts', name: 'posts', component: PostsView },
        { path: 'comments', name: 'comments', component: CommentsView },
        { path: 'reward-config', name: 'reward-config', component: RewardConfigView },
        { path: 'events', name: 'events', component: EventsView },
        { path: 'events/:id/registrations', name: 'event-registrations', component: EventRegistrationsView },
        { path: 'inquiries', name: 'inquiries', component: InquiriesView },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/users' },
  ],
});

router.beforeEach((to) => {
  const auth = useAuthStore();
  if (to.meta.public) {
    if (to.path === '/login' && auth.token) return '/users';
    return true;
  }
  if (!auth.token) return '/login';
  return true;
});

export default router;
