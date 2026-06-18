/**
 * WebSocket 클라이언트 — /ws/agent + /ws/hitl 2 채널.
 *
 * spec: 63 §3 / 21
 * Sprint 0 placeholder — Sprint 1 에서 Zustand store 라우팅 추가.
 */
import { WSMessageSchema, type WSMessage } from './schemas';

// 127.0.0.1 고정 — 'localhost' 는 ::1 먼저 시도하다 ~2s 타임아웃 (rest.ts 주석 참조)
const WS_BASE = import.meta.env.VITE_WS_URL ?? 'ws://127.0.0.1:8001';
// spec 21 §1.1 — user_id 는 query parameter 필수. POC 단계 = "demo" 고정.
// Sprint 16+ 로그인 도입 시 useSession 에서 주입하도록 변경.
const USER_ID = 'demo';

type MessageHandler = (msg: WSMessage) => void;

interface ChannelOptions {
  url: string;
  onMessage: MessageHandler;
  onOpen?: () => void;
  onClose?: () => void;
  reconnectMs?: number;
}

function setupChannel(opts: ChannelOptions): { ws: WebSocket; close: () => void } {
  const { url, onMessage, onOpen, onClose, reconnectMs = 1000 } = opts;
  let closedByUser = false;
  let currentWs: WebSocket;

  function connect() {
    currentWs = new WebSocket(url);

    currentWs.onmessage = (event) => {
      try {
        const raw = JSON.parse(event.data);
        const parsed = WSMessageSchema.safeParse(raw);
        if (!parsed.success) {
          console.error('[ws] invalid message', parsed.error, raw);
          return;
        }
        onMessage(parsed.data);
      } catch (e) {
        console.error('[ws] parse failed', e);
      }
    };

    currentWs.onopen = () => onOpen?.();

    currentWs.onclose = () => {
      onClose?.();
      if (!closedByUser) {
        setTimeout(connect, reconnectMs);
      }
    };

    currentWs.onerror = (e) => {
      console.error('[ws] error', e);
    };
  }

  connect();

  return {
    get ws() {
      return currentWs;
    },
    close() {
      closedByUser = true;
      currentWs?.close();
    },
  };
}

let agentChannel: ReturnType<typeof setupChannel> | null = null;
let hitlChannel: ReturnType<typeof setupChannel> | null = null;

export function connectAgent(onMessage: MessageHandler, onOpen?: () => void, onClose?: () => void) {
  agentChannel = setupChannel({
    url: `${WS_BASE}/ws/agent?user_id=${encodeURIComponent(USER_ID)}`,
    onMessage,
    onOpen,
    onClose,
  });
  return agentChannel;
}

export function connectHitl(onMessage: MessageHandler, onOpen?: () => void, onClose?: () => void) {
  hitlChannel = setupChannel({
    url: `${WS_BASE}/ws/hitl?user_id=${encodeURIComponent(USER_ID)}`,
    onMessage,
    onOpen,
    onClose,
  });
  return hitlChannel;
}

export function sendHitlMessage(msg: unknown): boolean {
  if (hitlChannel?.ws?.readyState !== WebSocket.OPEN) {
    console.error('[ws] hitl not connected');
    return false;
  }
  hitlChannel.ws.send(JSON.stringify(msg));
  return true;
}

export function sendAgentMessage(msg: unknown): boolean {
  if (agentChannel?.ws?.readyState !== WebSocket.OPEN) {
    console.error('[ws] agent not connected');
    return false;
  }
  agentChannel.ws.send(JSON.stringify(msg));
  return true;
}

/**
 * query 송신 — 새 turn 시작.
 *
 * require_review (옵션): false 면 백엔드 planning_stage 가 interrupt(plan_review) 스킵 →
 * AI 가 Plan 만들자마자 바로 execution. 누락/true 면 현재 동작 (interrupt 발동).
 *
 * spec: 63 §5.1 / ws_agent.py _parse_query_message + planning_stage
 */
export function sendQuery(params: {
  conversationId: string;
  turnId: string;
  userInput: string;
  clientId?: string;
  language?: string;
  requireReview?: boolean;
}): boolean {
  return sendAgentMessage({
    type: 'query',
    conversation_id: params.conversationId,
    turn_id: params.turnId,
    user_input: params.userInput,
    client_id: params.clientId,
    language: params.language ?? 'ko',
    require_review: params.requireReview ?? true,
  });
}

/**
 * resume_query 송신 — 재연결 후 미수신 interrupt 복구 요청 (멈춤 수술 ③, 2026-06-12).
 *
 * 서버가 Checkpoint 의 pending interrupt(hitl_request/paused)를 재emit.
 * hitl_request 가 WS 순단으로 유실되면 검토 모달이 영영 안 떠 서버가 30분 침묵 대기하던
 * 경로의 복구 수단 — 서버 쪽(ws_agent.py resume_query 분기)은 원래 있었고 호출자가 없었음.
 * pending interrupt 가 없으면 서버가 error 이벤트 응답 (관측 로그행 — 사용자 표시 없음, 무해).
 */
export function sendResumeQuery(conversationId: string, turnId: string): boolean {
  return sendAgentMessage({
    type: 'resume_query',
    conversation_id: conversationId,
    turn_id: turnId,
  });
}

/**
 * hitl_response 송신 — Plan review 승인 / 거부.
 * spec: 63 §5.2 / ws_hitl.py _handle_hitl_response
 */
export function sendHitlResponse(params: {
  requestId: string;
  turnId: string;
  action: 'approve' | 'reject' | 'modify';
  value?: unknown;
  comment?: string;
}): boolean {
  return sendHitlMessage({
    type: 'hitl_response',
    data: {
      request_id: params.requestId,
      turn_id: params.turnId,
      action: params.action,
      value: params.value,
      comment: params.comment,
    },
  });
}

/**
 * pause — Execution 일시중단 요청.
 * spec 21 §3.1 / ws_hitl.py _handle_pause
 */
export function sendPause(turnId: string): boolean {
  return sendHitlMessage({ type: 'pause', data: { turn_id: turnId } });
}

/**
 * resume — 일시중단 해제.
 * spec 21 §3.1 / ws_hitl.py _handle_resume
 */
export function sendResume(turnId: string): boolean {
  return sendHitlMessage({ type: 'resume', data: { turn_id: turnId } });
}

/**
 * cancel — 실행 취소.
 * spec 21 §3.1 / ws_hitl.py _handle_cancel
 */
export function sendCancel(turnId: string): boolean {
  return sendHitlMessage({ type: 'cancel', data: { turn_id: turnId } });
}

/**
 * todo_edit_nl — 자연어 Plan 편집.
 * spec 21 §3.1 v1.3 / ws_hitl.py _handle_todo_edit_nl
 * session_id 는 호환용 (= turn_id).
 */
export function sendTodoEditNl(turnId: string, instruction: string): boolean {
  return sendHitlMessage({
    type: 'todo_edit_nl',
    data: { turn_id: turnId, session_id: turnId, instruction },
  });
}

/**
 * todo_modify — 시각적 편집: 노드 속성 수정 (W2).
 * spec 21 §3.1 / ws_hitl.py _handle_todo_modify
 * 활성 조건: 백엔드 progress.status == "paused" 시점에만 (ADR-012 §1.2).
 */
export function sendTodoModify(
  turnId: string,
  todoId: string,
  changes: Record<string, unknown>,
): boolean {
  return sendHitlMessage({
    type: 'todo_modify',
    data: { turn_id: turnId, session_id: turnId, todo_id: todoId, changes },
  });
}

/**
 * todo_delete — 시각적 편집: 노드 삭제 (W2).
 * spec 21 §3.1 / ws_hitl.py _handle_todo_delete
 * cascade — 백엔드가 downstream todo_id 를 invalidated 로 emit. 프론트는 🔴 tint 표시.
 */
export function sendTodoDelete(turnId: string, todoId: string): boolean {
  return sendHitlMessage({
    type: 'todo_delete',
    data: { turn_id: turnId, session_id: turnId, todo_id: todoId },
  });
}

/**
 * todo_add — 시각적 편집: 신규 노드 추가 (W2).
 * spec 21 §3.1 / ws_hitl.py _handle_todo_add
 * todo payload 필수: task_type, agent (옵션), depends_on. 누락 시 백엔드 reject.
 */
export interface PartialTodo {
  id?: string;
  task_type: string;
  agent?: string | null;
  tool?: string | null;
  tool_params?: Record<string, unknown>;
  depends_on?: string[];
  priority?: number;
  rationale?: string;
  position?: { x: number; y: number } | null;
  node_type?: string;
  [key: string]: unknown;
}

export function sendTodoAdd(turnId: string, todo: PartialTodo): boolean {
  return sendHitlMessage({
    type: 'todo_add',
    data: { turn_id: turnId, session_id: turnId, todo },
  });
}

export function disconnectAll() {
  agentChannel?.close();
  hitlChannel?.close();
  agentChannel = null;
  hitlChannel = null;
}
