/**
 * useWebSocket — WS 2 채널 lifecycle 관리 hook.
 *
 * App mount 시 connectAgent + connectHitl, unmount 시 disconnect.
 * 수신 메시지를 agent / session store 로 라우팅.
 *
 * spec: 61 §1.5 / 63 §3
 */
import { useEffect } from 'react';
import { connectAgent, connectHitl, disconnectAll, sendResumeQuery } from '../ws';
import { useAgent } from '@/features/agent/store';
import { useExecution } from '@/features/execution/store';
import { useHitl } from '@/features/hitl/store';
import { useSession } from '@/features/session/store';
// [agent-observability] raw 콜백 스트림 캡처용 (계획서 §7.5). 대시보드 삭제 시 이 import + 아래 fanout 1줄 제거.
import { useObsEventLog } from '@/features/agent_observability/store/eventLogStore';
import type { WSMessage } from '../schemas';

export function useWebSocket() {
  useEffect(() => {
    const setConnectionStatus = useSession.getState().setConnectionStatus;

    // 모든 store 가 동일 메시지를 받음 — store 마다 관심 type 만 처리.
    const fanout = (msg: WSMessage) => {
      useAgent.getState().handleWSMessage(msg);
      useExecution.getState().handleWSMessage(msg);
      useHitl.getState().handleWSMessage(msg);
      useObsEventLog.getState().handleWSMessage(msg); // [agent-observability] 삭제 시 이 줄 제거
    };

    // (멈춤 수술 ③, 2026-06-12) 순단 복구 — 끊겼다 다시 붙으면, 진행 중 turn 의
    // 미수신 interrupt(hitl_request/paused)를 서버에 재요청. 순단 1초 창에서 유실된
    // 승인 요청이 검토 모달을 영영 못 띄우던 30분 침묵 멈춤(~1/20)의 직접 처방.
    let hadDrop = false;

    connectAgent(
      fanout,
      () => {
        setConnectionStatus('connected');
        if (hadDrop) {
          hadDrop = false;
          const { turnId, conversationId } = useSession.getState();
          const { isCompleted } = useExecution.getState();
          if (turnId && conversationId && !isCompleted) {
            sendResumeQuery(conversationId, turnId);
          }
        }
      },
      () => {
        hadDrop = true;
        setConnectionStatus('reconnecting');
      },
    );

    connectHitl(fanout, undefined, undefined);

    return () => {
      disconnectAll();
      setConnectionStatus('closed');
    };
  }, []);
}
