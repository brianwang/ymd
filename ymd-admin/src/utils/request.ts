import { useAuthStore } from '../store/auth';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');

type ApiOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
  auth?: boolean;
};

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

const parseErrorDetail = async (res: Response) => {
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) {
    const data: any = await res.json().catch(() => null);
    return data?.detail || data?.message || JSON.stringify(data) || res.statusText;
  }
  return (await res.text().catch(() => '')) || res.statusText;
};

export const api = async <T>(path: string, options: ApiOptions = {}): Promise<T> => {
  const authEnabled = options.auth !== false;
  const auth = useAuthStore();

  const headers: Record<string, string> = { ...(options.headers || {}) };
  if (options.body != null && !('Content-Type' in headers)) headers['Content-Type'] = 'application/json';
  if (authEnabled && auth.token) headers.Authorization = `Bearer ${auth.token}`;

  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method: options.method || 'GET',
      headers,
      body: options.body == null ? undefined : JSON.stringify(options.body),
    });
  } catch {
    throw new Error(`网络错误：无法连接到 API（${BASE_URL}）。请检查 VITE_API_BASE_URL 与后端服务状态。`);
  }

  if (!res.ok) {
    const detail = await parseErrorDetail(res);
    if (res.status === 401) {
      auth.logout();
      if (window.location.pathname !== '/login') window.location.replace('/login');
      throw new ApiError(401, detail || '登录已过期，请重新登录');
    }
    if (res.status === 403) {
      throw new ApiError(403, detail || '权限不足：需要管理员权限');
    }
    throw new ApiError(res.status, detail || `HTTP ${res.status}`);
  }

  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return (await res.json()) as T;
  return (await res.text()) as unknown as T;
};
