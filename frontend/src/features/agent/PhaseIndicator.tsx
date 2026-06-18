/**
 * PhaseIndicator — 4-Layer 진행 phase 를 자연어로 표시하는 인디케이터.
 *
 * 백엔드 node_event 도착 *시점* 으로 derive — node_event 는 노드 *완료* 시 emit 이므로:
 *   - query 송신 직후 ~ node_event(cognitive) 도착 = "사용자 질문 분석 중"
 *   - node_event(cognitive) 도착 ~ node_event(planning) 도착 = "실행 계획 수립 중"
 *   - planning 완료 = ChatTodoCard 가 등장 → phase 메시지 자동 사라짐
 *   - node_event(execution) 도착 ~ complete = "응답 작성 중"
 *
 * 백엔드 변경 0 — 기존 emit 시퀀스만 보고 derive.
 *
 * spec: 21 v1.4 §2.2 / 15 §1 (End-to-End Flow)
 */
import { Loader2 } from 'lucide-react';

export type AgentPhase = 'analyzing' | 'planning' | 'responding' | null;

const PHASE_TEXT: Record<NonNullable<AgentPhase>, string> = {
  analyzing: '사용자 질문을 분석하고 있어요…',
  planning: '실행 계획을 수립하고 있어요…',
  responding: '응답을 작성하고 있어요…',
};

interface PhaseIndicatorProps {
  phase: AgentPhase;
}

export function PhaseIndicator({ phase }: PhaseIndicatorProps) {
  if (!phase) return null;
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/50 text-sm text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin shrink-0" />
      <span>{PHASE_TEXT[phase]}</span>
    </div>
  );
}

/**
 * Phase derive — 입력 4종 → AgentPhase.
 *
 * @param turnId       현재 진행 중인 turn (없으면 null = idle)
 * @param lastNode     useAgent.nodeEvents 의 마지막 항목 node ('cognitive'|'planning'|'execution'|'response')
 * @param hasPlan      useExecution.plan 존재 여부 (true 면 ChatTodoCard 가 phase 메시지 대체)
 * @param isCompleted  useExecution.isCompleted (true 면 phase null — 응답 끝)
 */
export function derivePhase({
  turnId,
  lastNode,
  hasPlan,
  isCompleted,
}: {
  turnId: string | null;
  lastNode: string | null;
  hasPlan: boolean;
  isCompleted: boolean;
}): AgentPhase {
  if (!turnId || isCompleted) return null;
  if (!lastNode) return 'analyzing';
  if (lastNode === 'cognitive') return 'planning';
  if (lastNode === 'planning') {
    // ChatTodoCard 가 등장하면 phase 메시지는 숨김.
    return hasPlan ? null : 'planning';
  }
  if (lastNode === 'execution') return 'responding';
  // response 노드까지 완료 — complete 직전, phase 정리.
  return null;
}
