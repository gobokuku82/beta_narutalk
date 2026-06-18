/**
 * askAgent — 카드(대시보드 결과)에서 에이전트에게 질문을 보내는 공용 seam (P1).
 *
 * SideChatPanel.handleSend 와 동일 절차(턴 시작→store 리셋→버블→WS 송신)를 imperative 로 노출.
 * 카드 컨텍스트는 user_input 에 `[지표 값 · 기간]` 으로 임베드 — checkpoint 에 그대로 박제되어
 * 대화이력 회상 시 무엇을 물었는지 보존(설계 §6 저장 트랙).
 *
 * 설계: docs/reports/카드클릭_에이전트연결_설계계획_2026-06-10.md §4.1
 * client 는 호출 컴포넌트가 useCurrentClient() 로 해석해 전달 (해석 규칙 중복 금지).
 */
import { sendQuery } from '@/api/ws';
import { useSession } from '@/features/session/store';
import { useExecution } from '@/features/execution/store';
import { useAgent } from './store';
import { useChatPanel } from './chatPanelStore';

/** 카드 1장의 스코프 — 팝업 컨텍스트 칩 + user_input 임베드에 쓰임. */
export interface CardContext {
  /** 지표 라벨 — '전체 ROAS' */
  metric: string;
  /** 표시값 그대로 — '0.30×' (카드가 보여주는 정답값) */
  value: string;
  /** 기간 — '2026-04' (라우팅 테스트에서 실증된 period gap 의 해법) */
  period: string;
  /** methodology 출처 — 'methodology §S004 — ROAS' (🔍 숫자나온방법 P5 에서 사용) */
  methodology?: string;
  /** 산식 — META.formula (팝업 칩 표시용) */
  formula?: string;
  /** 카드 보조 텍스트 — '매출 ÷ 마케팅비' */
  sub?: string;
}

export type AskAgentResult =
  | { ok: true }
  | { ok: false; reason: 'not_connected' | 'no_client' | 'busy' | 'send_failed' };

/** 카드 컨텍스트를 user_input 접두로 임베드 — 대화이력에 `[전체 ROAS 0.30× · 2026-04] 왜...` 로 박제. */
export function buildUserInput(prompt: string, context?: CardContext): string {
  if (!context) return prompt;
  return `[${context.metric} ${context.value} · ${context.period}] ${prompt}`;
}

/**
 * 카드 → 에이전트 질문 송신. 성공 시 채팅 패널 자동 열림 + 사용자 버블 즉시 표시(빈 대기 금지 §2.2).
 *
 * 가드(SideChatPanel handleSend 와 동일 규칙):
 *  - WS 미연결 / client 미해석 / 실행 중(turnBusy) 이면 송신하지 않고 사유 반환 → 팝업이 피드백.
 */
export function askAgent(params: {
  prompt: string;
  client: string | undefined;
  context?: CardContext;
}): AskAgentResult {
  const { prompt, client, context } = params;

  if (useSession.getState().connectionStatus !== 'connected') {
    return { ok: false, reason: 'not_connected' };
  }
  if (!client) {
    return { ok: false, reason: 'no_client' };
  }
  // 실행 중 차단 — isRunning(turn 있음 + 미완료 + 비일시정지) 은 신규 query 금지 (세션연속성 ②와 동일)
  const { turnId: activeTurn } = useSession.getState();
  const { isCompleted, isPaused } = useExecution.getState();
  if (activeTurn && !isCompleted && !isPaused) {
    return { ok: false, reason: 'busy' };
  }

  const userInput = buildUserInput(prompt, context);

  const { conversationId, turnId } = useSession.getState().startTurn();
  useExecution.getState().reset();
  useAgent.getState().clearTurn();
  useAgent.getState().appendUserMessage(userInput);

  const ok = sendQuery({
    conversationId,
    turnId,
    userInput,
    clientId: client,
    requireReview: useSession.getState().requireReview,
  });
  if (!ok) return { ok: false, reason: 'send_failed' };

  useChatPanel.getState().open(); // 항목 선택 → 패널 열림 + 버블 즉시 (응답 전에! §2.2)
  return { ok: true };
}
