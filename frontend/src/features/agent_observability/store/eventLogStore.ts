/**
 * Observability 이벤트 로그 store — 라이브 WS 콜백 스트림의 *원본* 기록.
 *
 * 왜 별도 store 인가:
 *  - useExecution / useAgent 는 콜백을 *파생 상태*(todoRuntime/progress/nodeEvents)로 접고,
 *    raw 이벤트 순서·타임스탬프·layer_start/paused/resumed/error 를 보존하지 않는다.
 *  - 사용자 요구 R6 "모든 과정(log/callback)을 다 보고 싶다" = raw 스트림 그대로 필요.
 *
 * 격리 원칙 (계획서 §7.5): 본 store 는 features/agent_observability/ 안에만 존재.
 *  공유 스토어를 오염시키지 않음. 대시보드 삭제 시 폴더 + useWebSocket.ts 의 tagged 1줄만 제거.
 *
 * cap = MAX_EVENTS ring buffer (메모리 무한 증가 방지). 페이지에 없어도 누적(전역 fanout).
 */
import { create } from 'zustand';
import type { WSMessage } from '@/api/schemas';

const MAX_EVENTS = 500;

/** 타임라인 한 줄. raw 보존 + 사람이 읽는 label/detail. */
export interface ObsEvent {
  seq: number;
  type: WSMessage['type'];
  turnId?: string;
  ts: string; // 도착 시각 (ISO)
  label: string;
  detail?: string;
  raw: WSMessage;
}

/** WS 메시지 1개 → 타임라인 요약(turnId/label/detail). msg.type 으로 narrow. */
function summarize(msg: WSMessage): { turnId?: string; label: string; detail?: string } {
  switch (msg.type) {
    case 'node_event':
      return {
        turnId: msg.turn_id,
        label: `node · ${msg.node}`,
        detail: Object.keys(msg.data).join(', ') || undefined,
      };
    case 'layer_start':
      return { turnId: msg.turn_id ?? msg.session_id, label: `layer_start · ${msg.data.layer}` };
    case 'todo_start':
      return {
        turnId: msg.turn_id ?? msg.session_id,
        label: `todo_start · ${msg.data.tool ?? msg.data.todo_id}`,
        detail: msg.data.todo_id,
      };
    case 'todo_complete': {
      const d = msg.data;
      const dur = typeof d.duration_ms === 'number' ? ` · ${(d.duration_ms / 1000).toFixed(1)}s` : '';
      const sum = d.summary ? ` · ${d.summary}` : '';
      return {
        turnId: msg.turn_id ?? msg.session_id,
        label: `todo_complete · ${d.todo_id}`,
        detail: `${d.status}${dur}${sum}`,
      };
    }
    case 'progress': {
      const d = msg.data;
      return {
        turnId: msg.turn_id ?? msg.session_id,
        label: `progress · ${d.completed}/${d.total}`,
        detail: d.phase != null ? `phase ${d.phase}/${d.phases_total ?? '?'}` : undefined,
      };
    }
    case 'hitl_request':
      return { turnId: msg.turn_id, label: 'hitl_request', detail: msg.data.message };
    case 'paused':
      return {
        turnId: msg.turn_id,
        label: 'paused',
        detail: msg.data.current_phase != null ? `phase ${msg.data.current_phase}` : undefined,
      };
    case 'resumed':
      return { turnId: msg.turn_id, label: `resumed · ${msg.data.action}` };
    case 'hitl_ack':
      return {
        label: `hitl_ack · ${msg.data.action}`,
        detail: msg.data.accepted
          ? 'accepted'
          : `rejected${msg.data.reason ? ` (${msg.data.reason})` : ''}`,
      };
    case 'complete':
      return { turnId: msg.turn_id, label: `complete · ${msg.data.status}` };
    case 'error':
      return {
        turnId: msg.turn_id,
        label: `error · ${msg.code ?? msg.data?.code ?? ''}`,
        detail: msg.message ?? msg.data?.message,
      };
    case 'connected':
      return { label: `connected${msg.channel ? ` · ${msg.channel}` : ''}` };
    case 'pong':
      return { label: 'pong' };
    default:
      return { label: (msg as { type: string }).type };
  }
}

interface ObsEventLogState {
  events: ObsEvent[];
  seq: number;
  handleWSMessage: (msg: WSMessage) => void;
  clear: () => void;
}

export const useObsEventLog = create<ObsEventLogState>((set, get) => ({
  events: [],
  seq: 0,

  handleWSMessage: (msg) => {
    const { turnId, label, detail } = summarize(msg);
    const seq = get().seq + 1;
    const evt: ObsEvent = {
      seq,
      type: msg.type,
      turnId,
      ts: new Date().toISOString(),
      label,
      detail,
      raw: msg,
    };
    set((s) => {
      const next = [...s.events, evt];
      return {
        events: next.length > MAX_EVENTS ? next.slice(next.length - MAX_EVENTS) : next,
        seq,
      };
    });
  },

  clear: () => set({ events: [] }),
}));
