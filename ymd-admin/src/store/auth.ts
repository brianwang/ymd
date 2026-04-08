import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { api } from '../utils/request';

type TokenResp = {
  access_token: string;
  token_type: string;
  user_id: number;
};

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('admin_token') || '');
  const userId = ref<number | null>(localStorage.getItem('admin_user_id') ? Number(localStorage.getItem('admin_user_id')) : null);

  const isAuthed = computed(() => Boolean(token.value));

  const setToken = (t: string) => {
    token.value = t;
    localStorage.setItem('admin_token', t);
  };

  const setUserId = (id: number | null) => {
    userId.value = id;
    if (id == null) localStorage.removeItem('admin_user_id');
    else localStorage.setItem('admin_user_id', String(id));
  };

  const logout = () => {
    token.value = '';
    userId.value = null;
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user_id');
  };

  const login = async (email: string, password: string) => {
    const data = await api<TokenResp>('/auth/login', {
      method: 'POST',
      body: { email, password },
      auth: false,
    });
    setToken(data.access_token);
    setUserId(data.user_id);
    return data;
  };

  return { token, userId, isAuthed, setToken, setUserId, login, logout };
});
