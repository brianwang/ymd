import { useUserStore } from '../store/user';

const injectedBaseUrl = typeof __YMD_API_BASE_URL__ === 'string' ? __YMD_API_BASE_URL__ : '';
const envBaseUrl = (import.meta as any)?.env?.VITE_API_BASE_URL;
const normalizeBaseUrl = (v: unknown) =>
  typeof v === 'string' && v ? v.replace(/\/+$/, '') : '';
export const BASE_URL =
  normalizeBaseUrl(injectedBaseUrl) ||
  normalizeBaseUrl(envBaseUrl) ||
  'http://localhost:8000/api/v1';

let redirectingToLogin = false;

const getCurrentPagePath = () => {
  try {
    const pages = (getCurrentPages?.() as any[]) || [];
    const last = pages[pages.length - 1] as any;
    const fullPath = last?.$page?.fullPath;
    const route = last?.route;
    const raw = typeof fullPath === 'string' && fullPath ? fullPath : route;
    if (typeof raw !== 'string' || !raw) return '';
    return raw.startsWith('/') ? raw : `/${raw}`;
  } catch {
    return '';
  }
};

export const ensureLoggedIn = () => {
  const token = uni.getStorageSync('token');
  if (token) return true;
  const currentPath = getCurrentPagePath();
  const isOnLogin = currentPath.startsWith('/pages/auth/login');
  if (!isOnLogin && !redirectingToLogin) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    redirectingToLogin = true;
    uni.reLaunch({
      url: '/pages/auth/login',
      complete: () => {
        redirectingToLogin = false;
      },
    });
  }
  return false;
};

export const request = (options: UniApp.RequestOptions) => {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        Authorization: uni.getStorageSync('token')
          ? `Bearer ${uni.getStorageSync('token')}`
          : '',
        ...options.header,
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else if (res.statusCode === 401 || res.statusCode === 403) {
          const currentPath = getCurrentPagePath();
          const isOnLogin = currentPath.startsWith('/pages/auth/login');
          if (!isOnLogin && !redirectingToLogin) {
            uni.showToast({ title: '认证失败，请重新登录', icon: 'none' });
          }
          try {
            useUserStore().logout();
          } catch {
            uni.removeStorageSync('token');
            uni.removeStorageSync('userInfo');
          }
          if (!isOnLogin && !redirectingToLogin) {
            redirectingToLogin = true;
            uni.reLaunch({
              url: '/pages/auth/login',
              complete: () => {
                redirectingToLogin = false;
              },
            });
          }
          reject(res);
        } else {
          uni.showToast({ title: (res.data as any)?.detail || '请求失败', icon: 'none' });
          reject(res);
        }
      },
      fail: (err) => {
        uni.showToast({ title: '网络异常', icon: 'none' });
        reject(err);
      },
    });
  });
};
