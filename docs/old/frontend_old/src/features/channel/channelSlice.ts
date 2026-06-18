import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { MOCK_CHART_DATA, MOCK_FUNNEL_DATA, MOCK_CHANNELS } from '../../constants/mock';
import { ChannelPerformance, FunnelData } from '../../types';

interface ChannelState {
  selectedChannel: 'all' | 'naver' | 'kakao' | 'meta' | 'google';
  selectedPeriod: 'today' | '7days' | '14days' | '30days' | 'custom';
  chartData: any[];
  funnelData: FunnelData;
  channels: ChannelPerformance[];
  budgetReallocationSuggestion: {
    current: Record<string, number>;
    suggested: Record<string, number>;
    expectedImpact: string;
  };
}

const initialState: ChannelState = {
  selectedChannel: 'all',
  selectedPeriod: '7days',
  chartData: MOCK_CHART_DATA,
  funnelData: MOCK_FUNNEL_DATA,
  channels: MOCK_CHANNELS,
  budgetReallocationSuggestion: {
    current: { naver: 800000, kakao: 600000, meta: 800000, google: 300000 },
    suggested: { naver: 800000, kakao: 600000, meta: 650000, google: 450000 },
    expectedImpact: 'ROAS 385% → 416% (+31%p)',
  },
};

const channelSlice = createSlice({
  name: 'channel',
  initialState,
  reducers: {
    setSelectedChannel: (state, action: PayloadAction<ChannelState['selectedChannel']>) => {
      state.selectedChannel = action.payload;
    },
    setSelectedPeriod: (state, action: PayloadAction<ChannelState['selectedPeriod']>) => {
      state.selectedPeriod = action.payload;
    },
    updateChartData: (state, action: PayloadAction<any[]>) => {
      state.chartData = action.payload;
    },
    approveBudgetReallocation: (state) => {
      state.budgetReallocationSuggestion.current = state.budgetReallocationSuggestion.suggested;
    },
  },
});

export const { setSelectedChannel, setSelectedPeriod, updateChartData, approveBudgetReallocation } = channelSlice.actions;
export default channelSlice.reducer;