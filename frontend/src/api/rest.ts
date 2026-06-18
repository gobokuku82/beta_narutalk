/**
 * REST 클라이언트 — fetch wrapper + BackendError + zod 검증 통합.
 *
 * spec: 63 §2 (REST API 매핑)
 */
import { BackendError } from './errors';

// 127.0.0.1 고정 — 'localhost' 는 ::1(IPv6) 먼저 시도하다 ~2s 타임아웃 후 IPv4 폴백.
// (Windows 실측: 같은 요청 localhost=2,025ms vs 127.0.0.1=16ms — 모든 API 가 요청마다 2s 내던 원인)
export const BASE_URL = import.meta.env.VITE_BACKEND_URL ?? 'http://127.0.0.1:8001';

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
}

async function request(path: string, options: RequestOptions = {}): Promise<unknown> {
  const { body, headers, ...rest } = options;
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    ...rest,
  });

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw new BackendError(res.status, errBody);
  }

  // 204 No Content 처리
  if (res.status === 204) return null;

  return res.json();
}

export const rest = {
  get: (path: string) => request(path, { method: 'GET' }),
  post: (path: string, body?: unknown) => request(path, { method: 'POST', body }),
  patch: (path: string, body?: unknown) => request(path, { method: 'PATCH', body }),
  put: (path: string, body?: unknown) => request(path, { method: 'PUT', body }),
  delete: (path: string, body?: unknown) => request(path, { method: 'DELETE', body }),
};
