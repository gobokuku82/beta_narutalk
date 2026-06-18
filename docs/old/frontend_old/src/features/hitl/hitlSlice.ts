import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { HitlItem, HitlStatus } from '../../types';
import { getClientHitlItems, getAllHitlItems } from '../../constants/mock';
import { selectClient } from '../client/clientSlice';

interface HitlState {
  items: HitlItem[];
  selectedId: string | null;
  activeTab: 'all' | 'creative' | 'budget' | 'report' | 'campaign' | 'history';
  currentClientName: string;
}

// 초기값은 코스모스 뷰티의 HITL 아이템
const initialState: HitlState = {
  items: getClientHitlItems('코스모스 뷰티'),
  selectedId: getClientHitlItems('코스모스 뷰티')[0]?.id || null,
  activeTab: 'all',
  currentClientName: '코스모스 뷰티',
};

const hitlSlice = createSlice({
  name: 'hitl',
  initialState,
  reducers: {
    selectItem: (state, action: PayloadAction<string | null>) => {
      state.selectedId = action.payload;
    },
    setActiveTab: (state, action: PayloadAction<HitlState['activeTab']>) => {
      state.activeTab = action.payload;
    },
    updateItemStatus: (state, action: PayloadAction<{ id: string; status: HitlStatus }>) => {
      const item = state.items.find(i => i.id === action.payload.id);
      if (item) {
        item.status = action.payload.status;
      }
    },
    addItem: (state, action: PayloadAction<HitlItem>) => {
      state.items.unshift(action.payload);
    },
    approveItem: (state, action: PayloadAction<string>) => {
      const item = state.items.find(i => i.id === action.payload);
      if (item) {
        item.status = 'approved';
      }
    },
    rejectItem: (state, action: PayloadAction<{ id: string; reason: string }>) => {
      const item = state.items.find(i => i.id === action.payload.id);
      if (item) {
        item.status = 'rejected';
      }
    },
    snoozeItem: (state, action: PayloadAction<string>) => {
      const item = state.items.find(i => i.id === action.payload);
      if (item) {
        item.status = 'rejected'; // snoozed 처리
      }
    },
  },
  extraReducers: (builder) => {
    // 클라이언트 변경 시 해당 클라이언트의 HITL 아이템으로 업데이트
    builder.addCase(selectClient, (state, action) => {
      const clientName = action.payload;
      state.currentClientName = clientName;

      if (clientName === '전체 포트폴리오') {
        // 포트폴리오 뷰일 때는 모든 클라이언트의 HITL 아이템 표시
        state.items = getAllHitlItems();
      } else {
        // 개별 클라이언트일 때는 해당 클라이언트의 아이템만 표시
        state.items = getClientHitlItems(clientName);
      }

      state.selectedId = state.items[0]?.id || null;
    });
  },
});

export const { selectItem, setActiveTab, updateItemStatus, addItem, approveItem, rejectItem, snoozeItem } = hitlSlice.actions;

// 파일 맨 아래 export 아래에 추가
export const selectPendingCount = (state: { hitl: HitlState }) =>
  state.hitl.items.filter(i => i.status === 'pending' || i.status === 'delayed').length;

export const selectCriticalCount = (state: { hitl: HitlState }) =>
  state.hitl.items.filter(i => i.urgency === 'critical' && i.status === 'pending').length;

export default hitlSlice.reducer;