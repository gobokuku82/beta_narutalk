/**
 * Vitest 전역 셋업 — @testing-library/jest-dom matcher + MSW 자동 시작/종료.
 *
 * spec: 61 §6
 */
import '@testing-library/jest-dom/vitest';
import { afterAll, afterEach, beforeAll } from 'vitest';
import { server } from './mocks/handlers';

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
