/**
 * Sidebar — 좌측 메뉴 (collapsed w-20 / expanded w-56).
 *
 * Phase 1 (2026-06-09): 다크 strip 폐기 → warm neutral 라이트 + collapsed/expanded toggle.
 * PALETTE.md §8.2 I (card lifting, active) + J (color strip, border-l) + B (hairline).
 * 활성 라우트 = useRouterState pathname (reactive, currentPath prop 폐기).
 *
 * spec: 61 §2.3 / 66 §1.3 / 64 §2 (Layout / Color / Effects)
 */
import {
  Home,
  BarChart3,
  Image,
  Briefcase,
  MessageSquare,
  DollarSign,
  FileText,
  TrendingUp,
  GitBranch,
  Brain,
  History,
  Activity, // [agent-observability]
  Database, // [system-console]
  Boxes, // [data-console]
  CalendarRange, // [monthly]
  Target, // [marketing-performance]
  BookOpen, // [data-catalog]
  ChevronLeft,
  ChevronRight,
  type LucideIcon,
} from 'lucide-react';
import { useNavigate, useRouterState } from '@tanstack/react-router';
import { useNavigation, type NavigationTab } from '@/features/navigation/store';
import { cn } from '@/lib/cn';

const ICON_MAP: Record<string, LucideIcon> = {
  Home,
  BarChart3,
  Image,
  Briefcase,
  MessageSquare,
  DollarSign,
  FileText,
  TrendingUp,
  GitBranch,
  Brain,
  History,
  Activity,
  Database,
  Boxes,
  CalendarRange,
  Target,
  BookOpen,
};

export function Sidebar() {
  const availableTabs = useNavigation((s) => s.availableTabs);
  const setCurrentTab = useNavigation((s) => s.setCurrentTab);
  const isExpanded = useNavigation((s) => s.isSidebarExpanded);
  const toggleSidebar = useNavigation((s) => s.toggleSidebar);
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  const handleClick = (tab: NavigationTab) => {
    setCurrentTab(tab.id);
    navigate({ to: tab.path });
  };

  return (
    <aside
      className={cn(
        'flex h-full flex-col flex-shrink-0 border-r border-border bg-card transition-[width] duration-200 ease-out',
        isExpanded ? 'w-56' : 'w-20',
      )}
    >
      <nav className="flex-1 overflow-y-auto py-2">
        {availableTabs.map((tab) => {
          const Icon = ICON_MAP[tab.iconName] ?? Home;
          const isActive = pathname === tab.path;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => handleClick(tab)}
              title={isExpanded ? undefined : tab.label}
              className={cn(
                'group relative flex w-full items-center transition-colors',
                isExpanded ? 'gap-3 px-4 py-2' : 'flex-col gap-1 py-2 px-2',
                isActive
                  ? 'bg-accent text-foreground'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground',
              )}
            >
              {isActive && (
                <span
                  aria-hidden
                  className="absolute inset-y-1 left-0 w-0.5 rounded-r-sm bg-steel"
                />
              )}
              <Icon className={cn('shrink-0', isExpanded ? 'h-4 w-4' : 'h-4 w-4')} />
              <span
                className={cn(
                  'leading-tight tabular-nums',
                  isExpanded ? 'text-sm' : 'text-2xs',
                )}
              >
                {tab.label}
              </span>
            </button>
          );
        })}
      </nav>

      <div className="border-t border-border py-2">
        <button
          type="button"
          onClick={toggleSidebar}
          className={cn(
            'flex w-full items-center text-muted-foreground transition-colors hover:bg-muted hover:text-foreground',
            isExpanded ? 'gap-3 px-4 py-2 text-sm' : 'flex-col gap-1 px-2 py-2 text-2xs',
          )}
          title={isExpanded ? '접기' : '펼치기'}
        >
          {isExpanded ? (
            <ChevronLeft className="h-4 w-4 shrink-0" />
          ) : (
            <ChevronRight className="h-4 w-4 shrink-0" />
          )}
          <span className="leading-tight">{isExpanded ? '접기' : '펼치기'}</span>
        </button>
        {/* (2026-07-02) 설정 버튼 제거 — /settings 라우트 미존재(프레임 추출 잔재)로
            tsc -b TS2322 유발. 설정 페이지가 생기면 라우트 등록과 함께 복원. */}
      </div>
    </aside>
  );
}
