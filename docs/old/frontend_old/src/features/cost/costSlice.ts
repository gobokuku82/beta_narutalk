import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { BudgetSimulation, ChannelType } from '../../types';
import { MOCK_BUDGET_SIMULATION } from '../../constants/mock';

interface CostState {
  activeTab: 'waste' | 'simulation' | 'benchmark';
  simulation: BudgetSimulation;
}

const initialState: CostState = {
  activeTab: 'waste',
  simulation: MOCK_BUDGET_SIMULATION,
};

const costSlice = createSlice({
  name: 'cost',
  initialState,
  reducers: {
    setCostTab: (state, action: PayloadAction<CostState['activeTab']>) => {
      state.activeTab = action.payload;
    },
    updateSimulatedPct: (state, action: PayloadAction<{ channel: ChannelType; pct: number }>) => {
      const allocation = state.simulation.allocations.find(
        a => a.channel === action.payload.channel
      );
      if (allocation) {
        allocation.simulatedPct = action.payload.pct;
      }
    },
    resetSimulation: (state) => {
      state.simulation = MOCK_BUDGET_SIMULATION;
    },
  },
});

export const { setCostTab, updateSimulatedPct, resetSimulation } = costSlice.actions;
export default costSlice.reducer;