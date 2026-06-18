import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export type NavigationContext = 'portfolio' | 'client';

export interface NavigationTab {
  id: string;
  label: string;
  path: string;
  icon?: string;
}

interface NavigationState {
  context: NavigationContext;
  selectedClientId: string | null;
  selectedClientName: string | null;
  currentTab: string;
  availableTabs: NavigationTab[];
}

// 전체 포트폴리오 탭
const PORTFOLIO_TABS: NavigationTab[] = [
  { id: 'portfolio', label: '포트폴리오', path: '/portfolio' },
  { id: 'analysis', label: '채널분석', path: '/analysis' },
  { id: 'hitl', label: '사용자개입', path: '/hitl' },
  { id: 'report', label: '리포트', path: '/report' },
];

// 클라이언트별 탭
const CLIENT_TABS: NavigationTab[] = [
  { id: 'dashboard', label: '대시보드', path: '/dashboard' },
  { id: 'analysis', label: '채널분석', path: '/analysis' },
  { id: 'trend', label: '트렌드분석', path: '/trend' },
  { id: 'creatives', label: '소재분석', path: '/creatives' },
  { id: 'hitl', label: '사용자개입', path: '/hitl' },
  { id: 'agent', label: '에이전트', path: '/agent' },
  { id: 'cost', label: '비용최적화', path: '/cost' },
  { id: 'report', label: '리포트', path: '/report' },
];

// localStorage에서 저장된 상태 가져오기
const loadState = (): Partial<NavigationState> => {
  try {
    const savedState = localStorage.getItem('navigationState');
    if (savedState) {
      return JSON.parse(savedState);
    }
  } catch (error) {
    console.error('Failed to load navigation state from localStorage:', error);
  }
  return {};
};

// 저장된 상태를 기반으로 초기값 설정
const savedState = loadState();
const initialState: NavigationState = {
  context: savedState.context || 'portfolio',
  selectedClientId: savedState.selectedClientId || null,
  selectedClientName: savedState.selectedClientName || null,
  currentTab: savedState.currentTab || 'portfolio',
  availableTabs: savedState.context === 'client' ? CLIENT_TABS : PORTFOLIO_TABS,
};

// localStorage에 상태 저장
const saveState = (state: NavigationState) => {
  try {
    const stateToSave = {
      context: state.context,
      selectedClientId: state.selectedClientId,
      selectedClientName: state.selectedClientName,
      currentTab: state.currentTab,
    };
    localStorage.setItem('navigationState', JSON.stringify(stateToSave));
  } catch (error) {
    console.error('Failed to save navigation state to localStorage:', error);
  }
};

const navigationSlice = createSlice({
  name: 'navigation',
  initialState,
  reducers: {
    setContext: (state, action: PayloadAction<NavigationContext>) => {
      const newContext = action.payload;
      state.context = newContext;

      if (newContext === 'portfolio') {
        state.availableTabs = PORTFOLIO_TABS;
        state.selectedClientId = null;
        state.selectedClientName = null;

        // 현재 탭이 포트폴리오 컨텍스트에 없으면 첫 번째 탭으로 이동
        const isTabAvailable = PORTFOLIO_TABS.some(tab => tab.id === state.currentTab);
        if (!isTabAvailable) {
          state.currentTab = PORTFOLIO_TABS[0].id;
        }
      } else {
        state.availableTabs = CLIENT_TABS;

        // 현재 탭이 클라이언트 컨텍스트에 없으면 첫 번째 탭으로 이동
        const isTabAvailable = CLIENT_TABS.some(tab => tab.id === state.currentTab);
        if (!isTabAvailable) {
          state.currentTab = CLIENT_TABS[0].id;
        }
      }
      saveState(state);
    },

    selectClient: (state, action: PayloadAction<{ id: string; name: string }>) => {
      state.context = 'client';
      state.selectedClientId = action.payload.id;
      state.selectedClientName = action.payload.name;
      state.availableTabs = CLIENT_TABS;

      // 현재 탭이 클라이언트 컨텍스트에 없으면 대시보드로 이동
      const isTabAvailable = CLIENT_TABS.some(tab => tab.id === state.currentTab);
      if (!isTabAvailable) {
        state.currentTab = 'dashboard';
      }
      saveState(state);
    },

    selectPortfolio: (state) => {
      state.context = 'portfolio';
      state.selectedClientId = null;
      state.selectedClientName = null;
      state.availableTabs = PORTFOLIO_TABS;

      // 현재 탭이 포트폴리오 컨텍스트에 없으면 포트폴리오 탭으로 이동
      const isTabAvailable = PORTFOLIO_TABS.some(tab => tab.id === state.currentTab);
      if (!isTabAvailable) {
        state.currentTab = 'portfolio';
      }
      saveState(state);
    },

    setCurrentTab: (state, action: PayloadAction<string>) => {
      const isValid = state.availableTabs.some(tab => tab.id === action.payload);
      if (isValid) {
        state.currentTab = action.payload;
        saveState(state);
      }
    },
  },
});

export const { setContext, selectClient, selectPortfolio, setCurrentTab } = navigationSlice.actions;
export default navigationSlice.reducer;