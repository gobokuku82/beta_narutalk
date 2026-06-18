/**
 * RootLayout — GlobalLayout 을 router 와 연결.
 *
 * useRouter hook 으로 currentPath / navigate 를 GlobalLayout 에 전달.
 */
import { useEffect, type ReactNode } from 'react';
import { useRouterState, useNavigate } from '@tanstack/react-router';
import { GlobalLayout } from '@/components/layout/GlobalLayout';
import { useWebSocket } from '@/api/hooks/useWebSocket';
import { useSession } from '@/features/session/store';
import { useAgent } from '@/features/agent/store';
import { turnsToMessages, restoreLiveExecution } from '@/features/agent/restore';
import { fetchConversationTurns } from '@/api/hooks/useConversations';

export function RootLayout({ children }: { children: ReactNode }) {
  const currentPath = useRouterState({ select: (s) => s.location.pathname });
  const navigate = useNavigate();

  // WS 2 채널 lifecycle (mount 시 연결 / unmount 시 해제)
  useWebSocket();

  // 세션 연속성 — 부팅 시 직전 대화(완료 메시지) 정적 복원(P2) + 진행 중이면 라이브 재연결(P4).
  // hydrate(main.tsx)가 conversationId를 이미 복원 → 그 대화 turns 를 fetch → loadMessages.
  // 이어서: 마지막 turn 이 아직 실행 중이면 진행 상태를 rehydrate(입력 잠금 + 패널 열림).
  // 설계: docs/reports/세션연속성_복원_설계계획_2026-06-11.md §3
  useEffect(() => {
    const convId = useSession.getState().conversationId;
    if (!convId) return;
    if (useAgent.getState().messages.length > 0) {
      useAgent.getState().setRestoring(false); // 이미 채팅 있으면 복원 불요 → 스피너 끔
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const turns = await fetchConversationTurns(convId);
        if (cancelled) return;
        if (useAgent.getState().messages.length > 0) return; // 그새 새 대화 시작됨
        useAgent.getState().loadMessages(turnsToMessages(turns));
        // P4 — 마지막 turn 이 백엔드에서 아직 실행 중이면 라이브 재연결(진행 박스 이어 그림).
        if (!cancelled) void restoreLiveExecution(convId);
      } catch (e) {
        console.error('부팅 대화 복원 실패', e);
      } finally {
        // 성공·0건·실패 모두 스피너 끔(무한 스피너 방지). cancelled(StrictMode/언마운트)면 다음 마운트가 처리.
        if (!cancelled) useAgent.getState().setRestoring(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <GlobalLayout
      currentPath={currentPath}
      onNavigate={(path) => navigate({ to: path })}
    >
      {children}
    </GlobalLayout>
  );
}
