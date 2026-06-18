/**
 * GlobalLayout — TopBar + Sidebar + Outlet + SideChatPanel.
 *
 * v1 GlobalLayout.tsx 의 Zustand 포팅. 사용자 통찰 "동료 화면 + 채팅 지시" UX.
 * spec: 61 §2.3 / 66 §2.1
 */
import { useEffect, useState, type ReactNode } from 'react';
import { TopBar } from './TopBar';
import { Sidebar } from './Sidebar';
import { SideChatPanel } from '@/features/agent/SideChatPanel';
import { useChatPanel } from '@/features/agent/chatPanelStore';
import { PlanReviewModal } from '@/features/hitl/PlanReviewModal';
import { cn } from '@/lib/cn';

interface GlobalLayoutProps {
  /** 메인 영역 콘텐츠 (Sprint 1 에서 Router Outlet 으로 대체). */
  children: ReactNode;
  /** 현재 라우트 (Sidebar 활성 표시용). */
  currentPath?: string;
  /** 라우트 이동 핸들러 (Sprint 1 에서 router navigate). */
  onNavigate?: (path: string) => void;
}

export function GlobalLayout({ children, currentPath: _currentPath, onNavigate: _onNavigate }: GlobalLayoutProps) {
  const chatPanelOpen = useChatPanel((s) => s.isOpen);
  const chatPanelWidth = useChatPanel((s) => s.width);
  const setWidth = useChatPanel((s) => s.setWidth);
  const [isResizing, setIsResizing] = useState(false);

  // Resizer 마우스 핸들러
  useEffect(() => {
    if (!isResizing) return;

    const handleMove = (e: MouseEvent) => {
      setWidth(window.innerWidth - e.clientX);
    };

    const handleUp = () => setIsResizing(false);

    document.addEventListener('mousemove', handleMove);
    document.addEventListener('mouseup', handleUp);
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'col-resize';

    return () => {
      document.removeEventListener('mousemove', handleMove);
      document.removeEventListener('mouseup', handleUp);
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    };
  }, [isResizing, setWidth]);

  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        {/* 메인 영역 (대쉬보드 / Workflow / Agent 등) */}
        <main
          className="flex-1 overflow-auto transition-all duration-300 ease-in-out"
          style={{ marginRight: chatPanelOpen ? `${chatPanelWidth}px` : '0' }}
        >
          {children}
        </main>

        {/* Resizer (채팅 열렸을 때만) */}
        {chatPanelOpen && (
          <div
            role="separator"
            aria-orientation="vertical"
            className={cn(
              'fixed top-16 h-[calc(100vh-4rem)] w-1 bg-border hover:bg-primary transition-colors cursor-col-resize z-50',
              isResizing && 'bg-primary',
            )}
            style={{ right: `${chatPanelWidth}px` }}
            onMouseDown={(e) => {
              e.preventDefault();
              setIsResizing(true);
            }}
          />
        )}

        {/* SideChatPanel (우측, 호출형) */}
        <aside
          className={cn(
            'fixed top-16 right-0 h-[calc(100vh-4rem)] bg-card shadow-lg border-l border-border transition-transform duration-300 ease-in-out',
            chatPanelOpen ? 'translate-x-0' : 'translate-x-full',
          )}
          style={{ width: `${chatPanelWidth}px` }}
        >
          <SideChatPanel />
        </aside>
      </div>

      {/* HITL — Plan 검토 모달 (hitl_request 수신 시 open) */}
      <PlanReviewModal />
    </div>
  );
}
