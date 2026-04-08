import { useAuthStore } from '../store/auth';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');

type ApiOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
  auth?: boolean;
};

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

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (authEnabled && auth.token) headers.Authorization = `Bearer ${auth.token}`;

  const res = await fetch(`${BASE_URL}${path}`, {
    method: options.method || 'GET',
    headers,
    body: options.body == null ? undefined : JSON.stringify(options.body),
  });

  if (!res.ok) {
    if (res.status === 401) auth.logout();
    const detail = await parseErrorDetail(res);
    throw new Error(detail || `HTTP ${res.status}`);
  }

  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return (await res.json()) as T;
  return (await res.text()) as unknown as T;
};
