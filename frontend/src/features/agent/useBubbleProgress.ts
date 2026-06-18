/**
 * useBubbleProgress — Active User Bubble (C1) 진행률 selector.
 *
 * 사용자 메시지 박스 자체를 progress bar 로 시각화 (배경 왼쪽 → 오른쪽 채워짐).
 * 진행률 = phase 기반 base + tool 완료 비율 (workflow tool 갯수 / 완료 갯수).
 *
 * Phase 매핑 (단조 증가):
 *   idle           (turnId null)                              → 0, 'idle'
 *   analyzing      (turnId, lastNode null)                    → 5
 *   cognitive 완료 (lastNode='cognitive')                     → 15
 *   planning       (lastNode='planning' && !plan)             → 22
 *   executing      (plan, total>0)                            → 25 + 65 * (completed/total)
 *   executing      (plan, total=0, 도구 미사용)               → 90
 *   responding     (lastNode='execution' or 'response')       → 95
 *   completed      (isCompleted or hasAssistantArrived)       → 100
 *
 * 단조 증가 보장: WS race (progress 가 todo_complete 보다 늦거나, plan 갱신으로 total 변화) 시 percent 역행 회피.
 * turnId 변화 시 자동 리셋 (multi-turn 시 새 turn 의 percent 가 이전 turn 의 100 부터 시작 회피).
 *
 * 이전 turn 의 user 메시지 (isLastUser=false) = Static User Bubble — 정적 (액센트만, 진행바 0%).
 *
 * spec: VOCABULARY.md §1 (Active/Static User Bubble + Bubble Fill).
 * 백엔드 변경 0 — 기존 progress/node_event/complete 이벤트 그대로 사용.
 */
import { useRef } from 'react';
import { useAgent } from './store';
import { useExecution } from '@/features/execution/store';
import { useSession } from '@/features/session/store';

export type BubbleState =
  | 'idle'
  | 'analyzing'
  | 'planning'
  | 'executing'
  | 'responding'
  | 'paused'
  | 'completed';

export interface BubbleProgress {
  percent: number;
  state: BubbleState;
}

/**
 * Pure 함수 — 입력에서 percent + state derive (테스트 가능).
 */
export function computeBubblePercent(args: {
  turnId: string | null;
  lastNode: string | null;
  hasPlan: boolean;
  completed: number;
  total: number;
  isPaused: boolean;
  isCompleted: boolean;
  hasAssistantArrived: boolean;
}): BubbleProgress {
  const {
    turnId,
    lastNode,
    hasPlan,
    completed,
    total,
    isPaused,
    isCompleted,
    hasAssistantArrived,
  } = args;

  if (!turnId) return { percent: 0, state: 'idle' };
  if (isCompleted || hasAssistantArrived) return { percent: 100, state: 'completed' };

  let percent = 0;
  let state: BubbleState = 'analyzing';

  if (!lastNode) {
    percent = 5;
    state = 'analyzing';
  } else if (lastNode === 'cognitive') {
    percent = 15;
    state = 'planning';
  } else if (lastNode === 'planning' && !hasPlan) {
    percent = 22;
    state = 'planning';
  } else if (hasPlan && lastNode !== 'execution' && lastNode !== 'response') {
    if (total > 0) {
      const frac = Math.min(1, Math.max(0, completed / total));
      percent = Math.round(25 + 65 * frac);
    } else {
      percent = 90;
    }
    state = 'executing';
  } else if (lastNode === 'execution' || lastNode === 'response') {
    percent = 95;
    state = 'responding';
  }

  if (isPaused) state = 'paused';
  return { percent, state };
}

/**
 * Active User Bubble (마지막 user 메시지) 진행률 hook.
 *
 * @param isLastUser — 마지막 user 메시지면 true (진행바 활성), 아니면 Static (정적 100%).
 */
export function useBubbleProgress(isLastUser: boolean): BubbleProgress {
  // 모든 hook 을 조건문 전에 호출 (React Hooks 룰 정합)
  const turnId = useSession((s) => s.turnId);
  const plan = useExecution((s) => s.plan);
  const progress = useExecution((s) => s.progress);
  const isPaused = useExecution((s) => s.isPaused);
  const isCompleted = useExecution((s) => s.isCompleted);
  const nodeEvents = useAgent((s) => s.nodeEvents);
  const messages = useAgent((s) => s.messages);

  const lastRef = useRef(0);
  const prevTurnIdRef = useRef<string | null>(null);

  // turnId 변화 시 단조 증가 ref 리셋 (multi-turn 격리)
  if (turnId !== prevTurnIdRef.current) {
    lastRef.current = 0;
    prevTurnIdRef.current = turnId;
  }

  // Static User Bubble — 이전 turn 의 user 메시지 (Q6=a 결정: 정적, 액센트만)
  if (!isLastUser) return { percent: 0, state: 'idle' };

  const lastNode =
    nodeEvents.length > 0 ? (nodeEvents[nodeEvents.length - 1]?.node ?? null) : null;
  const hasAssistantArrived =
    messages.length > 0 && messages[messages.length - 1]?.role === 'assistant';

  const raw = computeBubblePercent({
    turnId,
    lastNode,
    hasPlan: !!plan,
    completed: progress?.completed ?? 0,
    total: progress?.total ?? 0,
    isPaused,
    isCompleted,
    hasAssistantArrived,
  });

  // 단조 증가 보장 — completed=100 은 항상 통과 (raw.state==='completed' 이라도 ref 갱신)
  if (raw.percent > lastRef.current) lastRef.current = raw.percent;

  return { percent: lastRef.current, state: raw.state };
}
