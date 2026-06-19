/**
 * useConversations — '대화이력' 페이지 data source (Phase 1).
 *
 * GET /api/conversations?client=        → 대화 목록 (checkpoint 기반)
 * GET /api/conversations/{id}/turns     → 대화 메시지 (클릭→채팅 복원)
 * 백엔드 ConversationManager(대화 전용, MemoryManager와 분리)가 dreamagent_system checkpoint를 읽음.
 * 설계: docs/reports/대화이력_설계_단계적_2026-06-09.md
 */
import { useQuery } from '@tanstack/react-query';

import { rest } from '@/api/rest';

export type ConversationStatus =
  | 'completed'
  | 'active'
  | 'error'
  | 'cancelled'
  | 'incomplete';

export interface ConversationListItem {
  conversation_id: string;
  title: string;
  preview: string;
  turn_count: number;
  status: ConversationStatus | string;
  updated_at: string | null;
  client_id: string | null;
}

export interface ConversationList {
  items: ConversationListItem[];
  total: number;
  has_more: boolean;
}

export function useConversations(client: string | undefined) {
  return useQuery({
    queryKey: ['conversations', client],
    enabled: !!client,
    queryFn: async () =>
      (await rest.get(
        `/api/conversations?client=${client}&limit=50`,
      )) as ConversationList,
    // 대화는 실시간(WS)이라 목록은 항상 최신으로 — 페이지 진입/포커스 시 자동 갱신.
    staleTime: 0,
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
  });
}

export interface ConversationTurnMessage {
  role: 'user' | 'assistant';
  content: string;
  format?: string | null;
  attachments?: { kind: string; url?: string; caption?: string }[];
}

export interface ConversationTurn {
  turn_id: string;
  messages: ConversationTurnMessage[];
  status: string;
  created_at: string | null;
}

export interface ConversationTurns {
  conversation_id: string;
  items: ConversationTurn[];
  total: number;
}

/** 클릭→복원용 imperative fetch (목록 카드 onClick 에서 호출). */
export async function fetchConversationTurns(
  conversationId: string,
): Promise<ConversationTurns> {
  return (await rest.get(
    `/api/conversations/${conversationId}/turns`,
  )) as ConversationTurns;
}

/** 대화 삭제 — checkpoint 제거 (되돌릴 수 없음). 성공 후 ['conversations'] invalidate. */
export async function deleteConversation(conversationId: string): Promise<void> {
  await rest.delete(`/api/conversations/${conversationId}`);
}

/**
 * 라이브 실행 상태 스냅샷 (세션연속성 ④) — 재접속 시 진행 중 turn 재연결용.
 * 백엔드 GET /turns/{id}/state — hitl_manager 싱글톤 조회(DB 아님). 실행 중이면 plan + 완료 todo 반환.
 * is_running=false 면 이미 끝남 → 프론트는 정적 복원에 위임.
 * shape = backend api_v2/routes/conversations.py build_turn_state 정합.
 */
export interface TurnState {
  turn_id: string;
  conversation_id: string;
  is_running: boolean;
  status: string; // running | paused | completed | cancelled | unknown
  plan: unknown | null;
  completed_todos: string[];
  current_phase: number;
  total_todos: number;
}

export async function fetchTurnState(
  conversationId: string,
  turnId: string,
): Promise<TurnState> {
  return (await rest.get(
    `/api/conversations/${conversationId}/turns/${turnId}/state`,
  )) as TurnState;
}
