/**
 * Session store — WS 연결 / conversation-turn 식별자 관리.
 *
 * spec 21 v1.4 §1.4:
 *  - conversation_id : 클라이언트 생성 (대화방 단위, localStorage 영속)
 *  - turn_id         : 클라이언트 생성 (쿼리 단위, 매번 새로 생성)
 *
 * spec: 61 §1.2 / 21 §1.4
 */
import { create } from 'zustand';

export type ConnectionStatus = 'connected' | 'reconnecting' | 'closed';

const CONV_ID_KEY = 'octormate.conversation_id';
const LAST_TURN_KEY = 'octormate.last_turn_id';
const REQUIRE_REVIEW_KEY = 'octormate.require_review';

function genId(prefix: string): string {
  return `${prefix}_${crypto.randomUUID().slice(0, 8)}`;
}

/** boot 라이브 재연결용 — 마지막 turn_id 조회 (세션연속성 Phase B). hydrate 는 turnId 를 복원하지 않으므로 직접 읽음. */
export function getLastTurnId(): string | null {
  try {
    return localStorage.getItem(LAST_TURN_KEY);
  } catch {
    return null;
  }
}

interface SessionState {
  conversationId: string | null;
  turnId: string | null;
  connectionStatus: ConnectionStatus;
  /**
   * Plan 검토 토글 — true(default) 면 백엔드 planning_stage 가 interrupt(plan_review) 발동.
   * false 면 AI 가 Plan 만들자마자 바로 execution 으로 진행 (interrupt 자체 스킵).
   * localStorage 영속.
   */
  requireReview: boolean;
  setConversation: (id: string | null) => void;
  setTurn: (id: string | null) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  setRequireReview: (v: boolean) => void;
  resetTurn: () => void;
  /** 새 query 송신 직전 — turn_id 자동 생성. conversation_id 없으면 같이 생성. */
  startTurn: () => { conversationId: string; turnId: string };
  /** "새 대화" 버튼 — conversation 리셋. */
  newConversation: () => void;
  /** App mount 1회 — localStorage 에서 conversation_id / requireReview 복원. */
  hydrate: () => void;
}

export const useSession = create<SessionState>((set, get) => ({
  conversationId: null,
  turnId: null,
  connectionStatus: 'closed',
  requireReview: true, // POC 초기 default — Plan 검토 켜짐.

  setConversation: (id) => set({ conversationId: id }),
  setTurn: (id) => set({ turnId: id }),
  setConnectionStatus: (status) => set({ connectionStatus: status }),
  setRequireReview: (v) => {
    set({ requireReview: v });
    try {
      localStorage.setItem(REQUIRE_REVIEW_KEY, v ? '1' : '0');
    } catch {
      // silent
    }
  },
  resetTurn: () => set({ turnId: null }),

  startTurn: () => {
    let convId = get().conversationId;
    if (!convId) {
      convId = genId('conv');
      set({ conversationId: convId });
      try {
        localStorage.setItem(CONV_ID_KEY, convId);
      } catch {
        // private mode 등 — silent fail
      }
    }
    const turnId = genId('turn');
    set({ turnId });
    try {
      localStorage.setItem(LAST_TURN_KEY, turnId);
    } catch {
      // silent
    }
    return { conversationId: convId, turnId };
  },

  newConversation: () => {
    set({ conversationId: null, turnId: null });
    try {
      localStorage.removeItem(CONV_ID_KEY);
      localStorage.removeItem(LAST_TURN_KEY);
    } catch {
      // silent
    }
  },

  hydrate: () => {
    try {
      const convId = localStorage.getItem(CONV_ID_KEY);
      if (convId) set({ conversationId: convId });
      const rr = localStorage.getItem(REQUIRE_REVIEW_KEY);
      if (rr !== null) set({ requireReview: rr === '1' });
    } catch {
      // silent
    }
  },
}));
