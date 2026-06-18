/**
 * TopBar — 로고 / 컨텍스트 전환 / 알림 / 채팅 토글 / 사용자.
 *
 * v1 (Redux) TopBar.tsx 의 Zustand 포팅.
 * spec: 61 §2.3 / 66 §2.1
 */
import { MessageSquare, Bell } from 'lucide-react';
import { useNavigate, useRouterState } from '@tanstack/react-router';
import { useChatPanel } from '@/features/agent/chatPanelStore';
import { useNavigation, type NavigationContext } from '@/features/navigation/store';
import { useSession } from '@/features/session/store';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/cn';
import { useClients, useCurrentClient } from '@/api/clients';
import { Brand } from './Brand';

// path '/portfolio' = 시스템 컨텍스트 첫 페이지 (포트폴리오) 라우트.
const CONTEXTS: Array<{ value: NavigationContext; label: string; path: string }> = [
  { value: 'system', label: '시스템', path: '/portfolio' },
  { value: 'client', label: '클라이언트', path: '/dashboard' },
];

export function TopBar() {
  const toggleChatPanel = useChatPanel((s) => s.toggle);
  const chatPanelOpen = useChatPanel((s) => s.isOpen);
  const context = useNavigation((s) => s.context);
  const setContext = useNavigation((s) => s.setContext);
  const setClient = useNavigation((s) => s.setClient);
  const connectionStatus = useSession((s) => s.connectionStatus);
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { data: clients = [] } = useClients();

  const switchContext = (ctx: NavigationContext, path: string) => {
    if (ctx === context) return;
    setContext(ctx);
    navigate({ to: path });
  };

  // 클라이언트 드롭다운 변경 → store 업데이트 (client-scope query 자동 refetch)
  const handleClientChange = (id: string) => {
    const c = clients.find((x) => x.id === id);
    if (c) setClient(c.id, c.name);
  };

  // 현재 client = store 선택값 ?? 데이터 기반(데이터 있는 첫 client) — clumi 하드코딩 제거(①.6c)
  const currentClient = useCurrentClient();

  const today = new Date().toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return (
    <header className="h-16 bg-card border-b border-border flex items-center justify-between px-4 flex-shrink-0">
      <div className="flex items-center gap-4">
        <Brand size="sm" />

        {/* 컨텍스트 전환 토글 */}
        <div className="flex items-center gap-1 rounded-lg bg-muted p-1">
          {CONTEXTS.map((c) => (
            <button
              key={c.value}
              type="button"
              onClick={() => switchContext(c.value, c.path)}
              className={cn(
                'rounded-md px-3 py-1 text-xs font-medium transition-colors',
                context === c.value
                  ? 'bg-card text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              {c.label}
            </button>
          ))}
        </div>

        {/* 클라이언트 드롭다운 — client 컨텍스트 + /db(Data DB 콘솔)에서 표시.
            /db 는 client-scoped 라 system 컨텍스트에서도 선택 필요 → 전역 단일 출처 (2026-06-07) */}
        {(context === 'client' || pathname === '/db') && (
          <Select value={currentClient} onValueChange={handleClientChange}>
            <SelectTrigger className="h-8 w-32 text-xs">
              <SelectValue placeholder="클라이언트 선택" />
            </SelectTrigger>
            <SelectContent>
              {clients.map((c) => (
                <SelectItem key={c.id} value={c.id} className="text-xs">
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      <div className="flex items-center gap-3">
        <span className="text-xs tabular-nums text-muted-foreground">{today}</span>

        {/* 연결 상태 — dot 톤다운 (w-2→w-1.5) */}
        <div className="flex items-center gap-2">
          <span
            className={cn(
              'h-1.5 w-1.5 rounded-full',
              connectionStatus === 'connected' && 'bg-success animate-pulse',
              connectionStatus === 'reconnecting' && 'bg-warning',
              connectionStatus === 'closed' && 'bg-muted-foreground',
            )}
          />
          <span className="text-xs text-muted-foreground">
            {connectionStatus === 'connected'
              ? '연결됨'
              : connectionStatus === 'reconnecting'
              ? '재연결 중'
              : '연결 끊김'}
          </span>
        </div>

        {/* 알림 */}
        <button
          type="button"
          className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          title="알림"
        >
          <Bell className="h-4 w-4" />
        </button>

        {/* 에이전트 채팅 토글 — hover 강화 (2026-06-10): bg-primary/8 옅은 옥스블러드 + dot 페이드인 + 아이콘 옥스블러드 */}
        <button
          type="button"
          onClick={toggleChatPanel}
          className={cn(
            'group flex items-center gap-2 rounded-md p-2 transition-colors duration-200',
            chatPanelOpen
              ? 'bg-accent text-foreground'
              : 'text-muted-foreground hover:bg-primary/8 hover:text-foreground',
          )}
          title="에이전트 채팅 (열기/닫기)"
        >
          <MessageSquare className="h-4 w-4 transition-colors duration-200 group-hover:text-primary" />
          <span className="text-xs font-medium">에이전트</span>
          <span
            aria-hidden
            className="font-semibold leading-none text-primary opacity-0 transition-opacity duration-200 group-hover:opacity-100"
          >
            ·
          </span>
        </button>

        {/* 사용자 — 옥스블러드 lighter 액센트로 브랜드 family */}
        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-accent text-2xs font-semibold text-accent-foreground">
          U
        </div>
      </div>
    </header>
  );
}
