/**
 * Navigation store — Sidebar 컨텍스트 + 탭.
 *
 * v1 (Redux) navigationSlice 의 Zustand 포팅.
 * 컨텍스트 자동 전환 (시스템 ↔ 클라이언트) 유지.
 *
 * 2026-06-08 (1): v2 페이지 → 정식 승격. dashboard1 + '분석 v2' group 폐기.
 * 2026-06-08 (2): dashboard1 실데이터 → /monthly (월간 결산) 승격 — 분석 group 6 항목.
 * 2026-06-09 (3): 페이지 재구성 —
 *   - 5 페이지 (리포트·메모리·에이전트 관찰·System·DB) CLIENT → SYSTEM_TABS 이동.
 *   - /agent (AgentChatPage) + /hitl (HitlCenterPage) 폐기 — 라우트·탭·페이지 폴더 모두.
 *   - CLIENT_TABS 17 → 8 (분석 6 + workflow + conversations 만).
 * 2026-06-10 (4): context type 'portfolio' → 'system' 일괄 rename (코드↔UI 의미 일치).
 *   - tab id 'portfolio' (포트폴리오 페이지) 는 /portfolio 라우트 매칭이라 별개로 유지.
 *   - 기존 localStorage `'portfolio'` 잔존 시 첫 진입 Sidebar mismatch 1회 — 사용자 1클릭 또는 localStorage.clear() 복구.
 *
 * spec: 61 §2 / 66 §1.3 / 66 §4.2 / docs/reports/페이지_재구성_계획서_2026-06-09.md
 *       / docs/reports/d_NavigationContext_type_rename_계획서_2026-06-10.md
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type NavigationContext = 'system' | 'client';

export interface NavigationTab {
  id: string;
  label: string;
  path: string;
  iconName: string; // lucide-react 아이콘 이름 (key)
  group?: string; // 그룹화 (분석/AI/리뷰/시스템)
}

// "시스템" 컨텍스트 (type 'system')
const SYSTEM_TABS: NavigationTab[] = [
  { id: 'portfolio', label: '포트폴리오', path: '/portfolio', iconName: 'Briefcase' },
  // 리포트 (2026-06-09 CLIENT 에서 이동)
  { id: 'report', label: '리포트', path: '/report', iconName: 'FileText', group: '리포트' },
  // 현황 (2026-06-09 CLIENT AI 그룹에서 이동, 2026-06-10 group "관찰"→"현황" · 탭 "에이전트 관찰"→"에이전트")
  // [agent-observability] 신설 (2026-06-05). 삭제 시 이 줄 제거.
  { id: 'agent-observability', label: '에이전트', path: '/agent-observability', iconName: 'Activity', group: '현황' },
  { id: 'memory', label: '메모리', path: '/memory', iconName: 'Brain', group: '현황' },
  // 시스템 — [system-console] db_console 개명 (2026-06-07). 삭제 시 이 줄 + router/Sidebar 항목 제거.
  { id: 'system-console', label: 'System', path: '/system', iconName: 'Database', group: '시스템' },
  { id: 'data-console', label: 'DB', path: '/db', iconName: 'Boxes', group: '시스템' },
];

const CLIENT_TABS: NavigationTab[] = [
  // 분석 6 (2026-06-08 v2 승격 + monthly 승격)
  { id: 'dashboard', label: '대시보드', path: '/dashboard', iconName: 'Home', group: '분석' },
  { id: 'monthly', label: '월간 결산', path: '/monthly', iconName: 'CalendarRange', group: '분석' },
  // [marketing-performance] 신설 (2026-06-17) — World-A canonical 첫 페이지. 삭제 시 이 줄 제거.
  { id: 'marketing-performance', label: '마케팅 성과', path: '/marketing-performance', iconName: 'Target', group: '분석' },
  // [data-catalog] 신설 (2026-06-17) — canonical 데이터 전체 펼쳐보기. 삭제 시 이 줄 제거.
  { id: 'data-catalog', label: '데이터 카탈로그', path: '/data-catalog', iconName: 'BookOpen', group: '분석' },
  { id: 'channel', label: '채널', path: '/channel', iconName: 'BarChart3', group: '분석' },
  { id: 'trend', label: '트렌드', path: '/trend', iconName: 'TrendingUp', group: '분석' },
  { id: 'creatives', label: '소재', path: '/creatives', iconName: 'Image', group: '분석' },
  { id: 'cost', label: '비용', path: '/cost', iconName: 'DollarSign', group: '분석' },
  // 에이전트 2 (2026-06-09 agent 삭제 + memory·agent-observability SYSTEM 이동 후 잔존. 2026-06-10 group "AI"→"에이전트")
  { id: 'workflow', label: '워크플로우', path: '/workflow', iconName: 'GitBranch', group: '에이전트' },
  { id: 'conversations', label: '대화이력', path: '/conversations', iconName: 'History', group: '에이전트' },
];

interface NavigationState {
  context: NavigationContext;
  selectedClientId: string | null;
  selectedClientName: string | null;
  currentTab: string;
  availableTabs: NavigationTab[];
  /** Sidebar collapsed (w-20) ↔ expanded (w-56) — 2026-06-09 적극 결 신설 */
  isSidebarExpanded: boolean;
  setContext: (ctx: NavigationContext) => void;
  setClient: (id: string | null, name: string | null) => void;
  setCurrentTab: (id: string) => void;
  toggleSidebar: () => void;
}

export const useNavigation = create<NavigationState>()(
  persist(
    (set) => ({
      context: 'system',
      selectedClientId: null,
      selectedClientName: null,
      currentTab: 'portfolio',
      availableTabs: SYSTEM_TABS,
      isSidebarExpanded: false,
      toggleSidebar: () => set((s) => ({ isSidebarExpanded: !s.isSidebarExpanded })),
      setContext: (ctx) =>
        set({
          context: ctx,
          availableTabs: ctx === 'system' ? SYSTEM_TABS : CLIENT_TABS,
        }),
      setClient: (id, name) =>
        set({
          selectedClientId: id,
          selectedClientName: name,
          context: id ? 'client' : 'system',
          availableTabs: id ? CLIENT_TABS : SYSTEM_TABS,
        }),
      setCurrentTab: (id) => set({ currentTab: id }),
    }),
    {
      name: 'navigation',
      // availableTabs 는 hardcoded — persist 에 저장 X (context 만 저장 후 재계산)
      partialize: (state) => ({
        context: state.context,
        selectedClientId: state.selectedClientId,
        selectedClientName: state.selectedClientName,
        currentTab: state.currentTab,
        isSidebarExpanded: state.isSidebarExpanded,
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.availableTabs =
            state.context === 'system' ? SYSTEM_TABS : CLIENT_TABS;
        }
      },
    },
  ),
);
