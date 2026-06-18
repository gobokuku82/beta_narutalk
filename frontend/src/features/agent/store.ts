/**
 * Agent store — 채팅 메시지 / 노드 이벤트 (WS 수신).
 *
 * spec: 21 v1.4 §2.2 / 61 §1.2
 * in-memory only — 영속화 X (백엔드 DB 가 진실 소스).
 */
import { create } from 'zustand';
import { ResponseAttachmentSchema, type WSMessage } from '@/api/schemas';

/** 다운로드 가능한 산출물 (url 있는 attachment 만) — 채팅 칩으로 렌더. */
export interface ChatAttachment {
  kind: string; // 'pdf' | 'ppt' | 'excel' | 'chart' | ...
  url: string; // /api/files/download?p=...
  caption?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  /** response.format — 'ppt' 면 슬라이드 카드로 렌더(SlideView). 그 외 plain text. */
  format?: string;
  /** response.attachments — pdf/ppt 등 다운로드 산출물 (url 보유분만). */
  attachments?: ChatAttachment[];
  timestamp: string;
}

export interface NodeEventRecord {
  turnId?: string;
  conversationId?: string;
  node: 'cognitive' | 'planning' | 'execution' | 'response';
  data: Record<string, unknown>;
  timestamp: string;
}

interface AgentState {
  messages: ChatMessage[];
  nodeEvents: NodeEventRecord[];
  /** 부팅 대화 복원 fetch 진행 중 — SideChatPanel 이 빈 상태 대신 스피너 표시 (세션연속성 UX). */
  isRestoring: boolean;
  appendUserMessage: (content: string) => void;
  appendAssistantMessage: (content: string, format?: string, attachments?: ChatAttachment[]) => void;
  /** 대화이력 복원 — 메시지 배열을 통째로 교체 (Phase1 click→restore). */
  loadMessages: (messages: ChatMessage[]) => void;
  /** 부팅 복원 시작(true)/종료(false) 토글. 종료는 결과 0건·실패여도 finally 에서 보장 → 무한 스피너 방지. */
  setRestoring: (v: boolean) => void;
  appendNodeEvent: (e: NodeEventRecord) => void;
  clearTurn: () => void;
  /** WS 메시지 1개를 받아 store 갱신. */
  handleWSMessage: (msg: WSMessage) => void;
}

function genId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

/** response.attachments[] → 다운로드 가능한 칩 (url 있는 것만). 형식 불일치는 안전 무시. */
function extractAttachments(response: Record<string, unknown> | undefined): ChatAttachment[] {
  const raw = response?.['attachments'];
  if (!Array.isArray(raw)) return [];
  const out: ChatAttachment[] = [];
  for (const item of raw) {
    const parsed = ResponseAttachmentSchema.safeParse(item);
    if (parsed.success && parsed.data.url) {
      out.push({
        kind: parsed.data.kind,
        url: parsed.data.url,
        caption: parsed.data.caption ?? undefined,
      });
    }
  }
  return out;
}

function extractResponse(
  payload: Record<string, unknown> | undefined,
): { text: string | null; format?: string; attachments: ChatAttachment[] } {
  if (!payload) return { text: null, attachments: [] };
  const response = payload['response'] as Record<string, unknown> | undefined;
  const format =
    response && typeof response['format'] === 'string'
      ? (response['format'] as string)
      : undefined;
  const attachments = extractAttachments(response);
  if (response && typeof response['text'] === 'string')
    return { text: response['text'] as string, format, attachments };
  if (typeof payload['text'] === 'string') return { text: payload['text'] as string, format, attachments };
  if (typeof payload['message'] === 'string')
    return { text: payload['message'] as string, format, attachments };
  return { text: null, format, attachments };
}

export const useAgent = create<AgentState>((set, get) => ({
  messages: [],
  nodeEvents: [],
  isRestoring: false,

  setRestoring: (v) => set({ isRestoring: v }),

  appendUserMessage: (content) =>
    set((s) => ({
      messages: [
        ...s.messages,
        { id: genId(), role: 'user', content, timestamp: new Date().toISOString() },
      ],
    })),

  appendAssistantMessage: (content, format, attachments) =>
    set((s) => ({
      messages: [
        ...s.messages,
        {
          id: genId(),
          role: 'assistant',
          content,
          format,
          attachments,
          timestamp: new Date().toISOString(),
        },
      ],
    })),

  loadMessages: (messages) => set({ messages, nodeEvents: [] }),

  appendNodeEvent: (e) => set((s) => ({ nodeEvents: [...s.nodeEvents, e] })),

  clearTurn: () => set({ nodeEvents: [] }),

  handleWSMessage: (msg) => {
    const { appendNodeEvent, appendAssistantMessage, clearTurn } = get();
    switch (msg.type) {
      case 'node_event':
        appendNodeEvent({
          turnId: msg.turn_id,
          conversationId: msg.conversation_id,
          node: msg.node,
          data: msg.data,
          timestamp: new Date().toISOString(),
        });
        break;
      case 'complete': {
        const { text, format, attachments } = extractResponse(msg.data);
        if (text) appendAssistantMessage(text, format, attachments);
        else if (msg.data.status === 'rejected') appendAssistantMessage(msg.data.message ?? '계획이 거부되었습니다.');
        else if (msg.data.status === 'cancelled') appendAssistantMessage('실행이 취소되었습니다.');
        else if (msg.data.status === 'aborted') appendAssistantMessage(`실행이 중단되었습니다 (${msg.data.reason ?? 'unknown'}).`);
        clearTurn();
        break;
      }
      // hitl_request / hitl_ack / paused / resumed / todo_* / progress 는 각 전용 store 에서 처리
      default:
        break;
    }
  },
}));
