import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Creative } from '../../types';
import { MOCK_CREATIVES } from '../../constants/mock';

interface CreativeState {
  creatives: Creative[];
  selectedCreativeId: string | null;
  abTestResults: {
    variantA: { name: string; ctr: number; cvr: number; roas: number };
    variantB: { name: string; ctr: number; cvr: number; roas: number };
    winner: 'A' | 'B' | null;
    confidence: number;
  } | null;
}

const initialState: CreativeState = {
  creatives: MOCK_CREATIVES,
  selectedCreativeId: null,
  abTestResults: {
    variantA: { name: 'A안: 감성적 카피', ctr: 4.8, cvr: 3.2, roas: 421 },
    variantB: { name: 'B안: 기능적 카피', ctr: 3.9, cvr: 2.8, roas: 356 },
    winner: 'A',
    confidence: 95,
  },
};

const creativeSlice = createSlice({
  name: 'creative',
  initialState,
  reducers: {
    setSelectedCreative: (state, action: PayloadAction<string | null>) => {
      state.selectedCreativeId = action.payload;
    },
    updateCreativeStatus: (state, action: PayloadAction<{ id: string; status: Creative['status'] }>) => {
      const creative = state.creatives.find(c => c.id === action.payload.id);
      if (creative) {
        creative.status = action.payload.status;
      }
    },
    replaceCreative: (state, action: PayloadAction<{ oldId: string; newCreative: Creative }>) => {
      const index = state.creatives.findIndex(c => c.id === action.payload.oldId);
      if (index !== -1) {
        state.creatives[index] = action.payload.newCreative;
      }
    },
    setAbTestWinner: (state, action: PayloadAction<'A' | 'B'>) => {
      if (state.abTestResults) {
        state.abTestResults.winner = action.payload;
      }
    },
  },
});

export const { setSelectedCreative, updateCreativeStatus, replaceCreative, setAbTestWinner } = creativeSlice.actions;
export default creativeSlice.reducer;