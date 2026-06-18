import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { getClientData, MOCK_CLIENT_LIST } from '../../constants/mock';
import type { ClientData } from '../../types';

interface ClientState {
  selectedClient: string;
  currentClientData: ClientData | null;
  clientList: string[];
  isPortfolioView: boolean;
}

// localStorage에서 저장된 클라이언트 상태 가져오기
const loadClientState = (): Partial<ClientState> => {
  try {
    const savedClient = localStorage.getItem('selectedClient');
    const navigationState = localStorage.getItem('navigationState');

    if (navigationState) {
      const navState = JSON.parse(navigationState);
      // navigation 상태와 동기화
      if (navState.context === 'portfolio') {
        return {
          selectedClient: '전체 포트폴리오',
          isPortfolioView: true,
        };
      } else if (navState.selectedClientName) {
        return {
          selectedClient: navState.selectedClientName,
          isPortfolioView: false,
        };
      }
    }

    // 이전 버전 호환성을 위한 fallback
    if (savedClient) {
      const clientName = JSON.parse(savedClient);
      return {
        selectedClient: clientName,
        isPortfolioView: clientName === '전체 포트폴리오',
      };
    }
  } catch (error) {
    console.error('Failed to load client state from localStorage:', error);
  }
  return {};
};

const savedClientState = loadClientState();
const initialClient = savedClientState.selectedClient || '전체 포트폴리오';
const isPortfolio = initialClient === '전체 포트폴리오';

const initialState: ClientState = {
  selectedClient: initialClient,
  currentClientData: isPortfolio ? null : getClientData(initialClient),
  clientList: MOCK_CLIENT_LIST,
  isPortfolioView: isPortfolio,
};

const clientSlice = createSlice({
  name: 'client',
  initialState,
  reducers: {
    selectClient: (state, action: PayloadAction<string>) => {
      state.selectedClient = action.payload;
      if (action.payload === '전체 포트폴리오') {
        state.isPortfolioView = true;
        state.currentClientData = null;
      } else {
        state.isPortfolioView = false;
        state.currentClientData = getClientData(action.payload);
      }

      // localStorage에 저장
      try {
        localStorage.setItem('selectedClient', JSON.stringify(action.payload));
      } catch (error) {
        console.error('Failed to save selected client to localStorage:', error);
      }
    },
  },
});

export const { selectClient } = clientSlice.actions;
export default clientSlice.reducer;