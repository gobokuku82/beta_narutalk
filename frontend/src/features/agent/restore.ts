/**
 * 대화 복원 매핑 — 공용 순수 함수.
 *
 * GET /api/conversations/{id}/turns 응답(ConversationTurns) → 채팅 ChatMessage[].
 * 사용처: ConversationsPage 클릭 복원 + RootLayout 부팅 자동 복원(세션 연속성 P2).
 */
import type { Plan } from '@/api/schemas';
import type { ChatMessage } from './store';
import { fetchTurnState, type ConversationTurns } from '@/api/hooks/useConversations';
import { useExecution } from '@/features/execution/store';
import { useSession, getLastTurnId } from '@/features/session/store';
import { useChatPanel } from './chatPanelStore';

/** 대화 turns → 채팅 메시지 배열 (완료된 정적 메시지만; 진행 박스는 라이브 재구독 전용). */
export function turnsToMessages(turns: ConversationTurns): ChatMessage[] {
  return turns.items.flatMap((t) =>
    t.messages.map((m, mi) => ({
      id: `restored_${t.turn_id}_${mi}`,
      role: m.role,
      content: m.content,
      format: m.format ?? undefined,
      attachments: (m.attachments ?? [])
        .filter((a) => a.url)
        .map((a) => ({ kind: a.kind, url: a.url as string, caption: a.caption })),
      timestamp: t.created_at ?? '',
    })),
  );
}

/**
 * 라이브 실행 재연결 (세션연속성 ④) — RootLayout 부팅 정적 복원 직후 호출.
 *
 * 마지막 turn 이 백엔드(GET /state, hitl_manager)에서 아직 실행 중이면 진행 상태를 rehydrate:
 *  - execution store 에 plan + 완료 todo 복원 → ChatTodoCard 가 "9번 작업 중"으로 이어 그림.
 *  - setTurn → isRunning/turnBusy 파생 → 입력 잠금 + [중지] 버튼.
 *  - 패널 자동 열림(진행 중일 때만; 완료 대화는 정적 복원만 = 과거 "박스 안 없어지는 버그" 수정 존중).
 * 이후 남은 todo_start·complete·progress 이벤트는 재접속 ws(user=demo)로 콜백 브리지가 자동 fan-out.
 */
export async function restoreLiveExecution(conversationId: string): Promise<void> {
  const turnId = getLastTurnId();
  if (!turnId) return;
  try {
    const snap = await fetchTurnState(conversationId, turnId);
    if (!snap.is_running) return; // 이미 끝남 — 정적 복원으로 충분.
    const completed = snap.completed_todos ?? [];
    useExecution.getState().rehydrateFromSnapshot({
      plan: (snap.plan as Plan | null) ?? null,
      completedTodoIds: completed,
      progress:
        snap.total_todos > 0
          ? { completed: completed.length, total: snap.total_todos }
          : null,
      paused: snap.status === 'paused',
    });
    useSession.getState().setTurn(turnId); // → isRunning/turnBusy: 입력 잠금 + [중지]
    useChatPanel.getState().open(); // 진행 중이면 패널 자동 열림.
  } catch (e) {
    console.error('boot 라이브 재연결 실패', e);
  }
}
