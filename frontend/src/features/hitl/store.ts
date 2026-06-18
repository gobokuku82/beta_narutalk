/**
 * HITL store — /ws/hitl 수신 메시지 (hitl_request / hitl_ack).
 *
 * (2026-06-12 멈춤 수술 ①) D5 자동승인 폐기 — 오너 정정: "검토 ON = 사람이 확인 후 실행"
 * 이 원래 의도. 자동 approve 가 PlanReviewModal 을 dormant 로 만들었고, 판단 없는 자동
 * 왕복이 WS 순단(1초 재연결 창)과 겹치면 서버가 HITL_RESUME_TIMEOUT_SEC(30분)을 침묵
 * 대기하는 간헐 멈춤(~1/20)의 원인이었음. 검토 없이 빠르게 돌리려면 토글 OFF
 * (require_review=false — 서버가 interrupt 자체를 스킵, 왕복 없음).
 *
 * hitl_request 수신 → pending 설정 → PlanReviewModal 표시 → 사람이 승인/거부.
 * hitl_ack 수신 → cascadeResult 갱신, approve/reject **accepted:true** 시 pending clear.
 *   accepted:false(turn 만료 등)면 pending 유지(모달 재시도 가능) + toast 로 사유 표시.
 * W2' Stage 4 (ADR-013): hitl_ack.data.issues 가 있으면 sonner toast 로 사용자 경고.
 *
 * spec: 21 v1.4 §2.2 (hitl_request) / §3.1 (hitl_response approve) / 63 §4.2 / ADR-013 §4
 */
import { create } from 'zustand';
import { toast } from 'sonner';
import type { HitlAck, HitlRequest, WSMessage } from '@/api/schemas';

export type HitlRequestData = HitlRequest['data'];
export type HitlAckData = HitlAck['data'];

interface HitlState {
  /** 현재 사용자 응답 대기 중인 HITL 요청 (없으면 null). */
  pending: HitlRequestData | null;
  /** 마지막 hitl_ack — 편집 cascade 결과 표시용. */
  cascadeResult: HitlAckData | null;
  setPending: (req: HitlRequestData) => void;
  clearPending: () => void;
  setCascadeResult: (ack: HitlAckData) => void;
  /** WS 메시지 1개를 받아 store 갱신. */
  handleWSMessage: (msg: WSMessage) => void;
}

export const useHitl = create<HitlState>((set) => ({
  pending: null,
  cascadeResult: null,

  setPending: (req) => set({ pending: req }),
  clearPending: () => set({ pending: null }),
  setCascadeResult: (ack) => set({ cascadeResult: ack }),

  handleWSMessage: (msg) => {
    switch (msg.type) {
      case 'hitl_request': {
        // pending 설정 → PlanReviewModal 이 열려 사람이 승인/거부 (D5 자동승인 폐기, 헤더 참조)
        set({ pending: msg.data });
        break;
      }
      case 'hitl_ack': {
        const ack = msg.data;
        set((s) => ({
          cascadeResult: ack,
          // approve / reject 가 수락되면 대기 종료.
          pending:
            ack.accepted && (ack.action === 'approve' || ack.action === 'reject')
              ? null
              : s.pending,
        }));
        // (멈춤 수술 ④) 승인/거부 거절은 침묵 금지 — pending 이 유지되므로 모달에서 재시도 가능.
        if (!ack.accepted && (ack.action === 'approve' || ack.action === 'reject')) {
          toast.error(
            `계획 ${ack.action === 'approve' ? '승인' : '거부'}이 처리되지 않았습니다` +
              `${ack.reason ? ` (${ack.reason})` : ''}. 다시 시도해주세요.`,
          );
        }
        // ADR-013 §4 — 백엔드 validate 가 cycle/orphan/missing dep 등을 issues 로 emit.
        // 변경 자체는 적용되었지만 사용자에게 경고. cycle 사전 차단은 cycleGuard, 본 토스트는 fall-back.
        if (Array.isArray(ack.issues) && ack.issues.length > 0) {
          for (const issue of ack.issues) {
            toast.warning(`DAG 검증 오류 — ${issue}`);
          }
        }
        break;
      }
      default:
        break;
    }
  },
}));
