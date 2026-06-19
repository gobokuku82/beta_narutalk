/**
 * askAgent seam (P1) 단위 테스트.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/api/ws', () => ({ sendQuery: vi.fn(() => true) }));

import { sendQuery } from '@/api/ws';
import { askAgent, buildUserInput, type CardContext } from './actions';
import { useAgent } from './store';
import { useChatPanel } from './chatPanelStore';
import { useExecution } from '@/features/execution/store';
import { useSession } from '@/features/session/store';

const CTX: CardContext = {
  metric: '전체 ROAS',
  value: '0.30×',
  period: '2026-04',
  methodology: 'methodology §S004 — ROAS',
};

function resetStores() {
  useSession.setState({ conversationId: null, turnId: null, connectionStatus: 'connected' });
  useExecution.getState().reset();
  useAgent.setState({ messages: [], nodeEvents: [], isRestoring: false });
  useChatPanel.setState({ isOpen: false });
  vi.mocked(sendQuery).mockClear();
  vi.mocked(sendQuery).mockReturnValue(true);
}

describe('buildUserInput', () => {
  it('컨텍스트를 [지표 값 · 기간] 접두로 임베드 (대화이력 회상용)', () => {
    expect(buildUserInput('왜 이렇게 낮은지 분석해줘', CTX)).toBe(
      '[전체 ROAS 0.30× · 2026-04] 왜 이렇게 낮은지 분석해줘',
    );
  });
  it('컨텍스트 없으면 원문 그대로', () => {
    expect(buildUserInput('안녕')).toBe('안녕');
  });
});

describe('askAgent', () => {
  beforeEach(resetStores);

  it('성공: 버블 추가 + sendQuery(컨텍스트 임베드·period 포함) + 패널 열림', () => {
    const r = askAgent({ prompt: '왜 이렇게 낮은지 분석해줘', client: 'clumi', context: CTX });
    expect(r.ok).toBe(true);
    expect(useAgent.getState().messages).toHaveLength(1);
    expect(useAgent.getState().messages[0]?.content).toContain('[전체 ROAS 0.30× · 2026-04]');
    expect(sendQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        clientId: 'clumi',
        userInput: expect.stringContaining('2026-04'),
      }),
    );
    expect(useChatPanel.getState().isOpen).toBe(true);
    expect(useSession.getState().turnId).toBeTruthy(); // startTurn 됨
  });

  it('가드: WS 미연결이면 송신 안 함', () => {
    useSession.setState({ connectionStatus: 'closed' });
    const r = askAgent({ prompt: 'x', client: 'clumi' });
    expect(r).toEqual({ ok: false, reason: 'not_connected' });
    expect(sendQuery).not.toHaveBeenCalled();
  });

  it('가드: client 미해석이면 송신 안 함', () => {
    const r = askAgent({ prompt: 'x', client: undefined });
    expect(r).toEqual({ ok: false, reason: 'no_client' });
    expect(sendQuery).not.toHaveBeenCalled();
  });

  it('가드: 실행 중(turnBusy)이면 차단 — SideChatPanel 과 동일 규칙', () => {
    useSession.setState({ turnId: 'turn_running' });
    // isCompleted=false·isPaused=false (reset 기본) = 실행 중
    const r = askAgent({ prompt: 'x', client: 'clumi' });
    expect(r).toEqual({ ok: false, reason: 'busy' });
    expect(sendQuery).not.toHaveBeenCalled();
  });

  it('완료된 턴이 있으면 새 질문 허용', () => {
    useSession.setState({ turnId: 'turn_done' });
    useExecution.getState().finalize(); // isCompleted=true
    const r = askAgent({ prompt: 'x', client: 'clumi' });
    expect(r.ok).toBe(true);
  });

  it('sendQuery 실패 시 패널 안 열고 사유 반환', () => {
    vi.mocked(sendQuery).mockReturnValue(false);
    const r = askAgent({ prompt: 'x', client: 'clumi' });
    expect(r).toEqual({ ok: false, reason: 'send_failed' });
    expect(useChatPanel.getState().isOpen).toBe(false);
  });
});
