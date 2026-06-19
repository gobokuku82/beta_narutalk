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

// "시스템" 컨텍스트 (type 'system') — 프레임 골격: 랜딩 + 에이전트
const SYSTEM_TABS: NavigationTab[] = [
  { id: 'portfolio', label: '포트폴리오', path: '/portfolio', iconName: 'Briefcase' },
  { id: 'workflow', label: '워크플로우', path: '/workflow', iconName: 'GitBranch', group: '에이전트' },
  { id: 'conversations', label: '대화이력', path: '/conversations', iconName: 'History', group: '에이전트' },
];

// "클라이언트" 컨텍스트 — 도메인 분석 페이지 제거 후 에이전트 기능만 잔존 (2026-06-19)
const CLIENT_TABS: NavigationTab[] = [
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
