import { API_BASE } from '@/constants/api';

const BASE = API_BASE;

export type QueryParams = Record<string, string | number | boolean | undefined | null>;

/** GET → JSON (ยิงไป /api/v1/* · MSW intercept เมื่อ dev:mock) */
export async function apiGet<T>(path: string, params?: QueryParams): Promise<T> {
  const url = new URL(BASE + path, window.location.origin);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, String(v));
    }
  }
  const res = await fetch(url.toString(), {
    headers: { Authorization: 'Bearer mock-jwt', Accept: 'application/json' },
  });
  if (!res.ok) throw new Error(`API ${res.status} · ${path}`);
  return (await res.json()) as T;
}

type Method = 'POST' | 'PUT' | 'DELETE';

/** POST/PUT/DELETE + JSON body — คืน JSON (หรือ null เมื่อ 204) */
export async function apiSend<T = unknown>(method: Method, path: string, body?: unknown): Promise<T | null> {
  const res = await fetch(BASE + path, {
    method,
    headers: { Authorization: 'Bearer mock-jwt', 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API ${res.status} · ${method} ${path}`);
  return res.status === 204 ? null : ((await res.json()) as T);
}

export const apiPost = <T = unknown>(path: string, body?: unknown) => apiSend<T>('POST', path, body);
export const apiPut = <T = unknown>(path: string, body?: unknown) => apiSend<T>('PUT', path, body);
export const apiDelete = <T = unknown>(path: string, body?: unknown) => apiSend<T>('DELETE', path, body);
