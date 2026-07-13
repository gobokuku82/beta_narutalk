/**
 * HITL store 박제 — D5 자동승인 폐기 (멈춤 수술 ①④, 2026-06-12).
 *
 * 구버전: hitl_request 수신 즉시 자동 approve 송신 → 검토 모달 dormant + 의미 없는
 * 자동 왕복이 WS 순단과 겹치면 30분 침묵 멈춤. 폐기 후: pending 만 설정(사람이 결정),
 * ack accepted:false 는 pending 유지(재시도) + 토스트.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { toast } from 'sonner';
import { useHitl } from './store';
import type { WSMessage } from '@/api/schemas';

vi.mock('sonner', () => ({
  toast: Object.assign(vi.fn(), {
    error: vi.fn(),
    warning: vi.fn(),
    success: vi.fn(),
    message: vi.fn(),
  }),
}));

// 자동 송신이 완전히 사라졌는지 감시 — store 가 ws 모듈을 import 조차 안 해야 하지만,
// 만약 재도입되면 이 mock 호출로 적발된다.
vi.mock('@/api/ws', () => ({
  sendHitlResponse: vi.fn(),
}));

import { sendHitlResponse } from '@/api/ws';

const HITL_REQUEST: WSMessage = {
  type: 'hitl_request',
  turn_id: 't1',
  data: {
    request_id: 'req1',
    turn_id: 't1',
    message: '3개 Todo 실행 계획이 생성되었습니다. 승인하시겠습니까?',
    plan: { todos: [], dag: {}, teams_selected: [], plan_notes: '' },
  },
} as unknown as WSMessage;

function ack(accepted: boolean, action = 'approve', reason?: string): WSMessage {
  return {
    type: 'hitl_ack',
    data: { request_id: 'req1', action, accepted, ...(reason ? { reason } : {}) },
  } as unknown as WSMessage;
}

describe('hitl store — D5 자동승인 폐기', () => {
  beforeEach(() => {
    useHitl.setState({ pending: null, cascadeResult: null });
    vi.clearAllMocks();
  });

  it('hitl_request 수신 시 자동 approve 를 보내지 않는다 (사람이 결정)', () => {
    useHitl.getState().handleWSMessage(HITL_REQUEST);
    expect(useHitl.getState().pending).not.toBeNull();
    expect(sendHitlResponse).not.toHaveBeenCalled();
  });

  it('ack accepted:true(approve) 면 pending 을 지운다 (모달 닫힘)', () => {
    useHitl.getState().handleWSMessage(HITL_REQUEST);
    useHitl.getState().handleWSMessage(ack(true, 'approve'));
    expect(useHitl.getState().pending).toBeNull();
  });

  it('ack accepted:false 면 pending 유지(재시도 가능) + 에러 토스트', () => {
    useHitl.getState().handleWSMessage(HITL_REQUEST);
    useHitl.getState().handleWSMessage(ack(false, 'approve', 'turn_not_active'));
    expect(useHitl.getState().pending).not.toBeNull();
    expect(toast.error).toHaveBeenCalledOnce();
    expect(String(vi.mocked(toast.error).mock.calls[0]?.[0])).toContain('turn_not_active');
  });

  it('todo 편집 ack(accepted:false)는 승인 토스트 경로를 타지 않는다 (소음 방지)', () => {
    useHitl.getState().handleWSMessage(HITL_REQUEST);
    useHitl.getState().handleWSMessage(ack(false, 'todo_modify'));
    expect(toast.error).not.toHaveBeenCalled();
    expect(useHitl.getState().pending).not.toBeNull();
  });
});
