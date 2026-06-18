/**
 * MSW handlers — REST endpoint mock.
 *
 * 백엔드 진실 소스: spec 20 (REST API).
 * Sprint 1 에서 실제 endpoint 추가.
 */
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

export const handlers = [
  // 예시 — Sprint 1 에서 endpoint 별로 추가
  http.get('*/health', () => HttpResponse.json({ status: 'ok' })),
];

export const server = setupServer(...handlers);
