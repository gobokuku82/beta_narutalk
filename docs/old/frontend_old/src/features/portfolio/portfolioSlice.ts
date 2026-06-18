import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Client, TeamMember } from '../../types';
import { MOCK_CLIENTS, MOCK_TEAM_MEMBERS } from '../../constants/mock';

interface PortfolioState {
  clients: Client[];
  teamMembers: TeamMember[];
  selectedClientId: string | null;
  totalOperatingBudget: number;
  totalRevenue: number;
  kpiAchievedCount: number;
  totalKpiCount: number;
  totalSavedHours: number;
}

const initialState: PortfolioState = {
  clients: MOCK_CLIENTS,
  teamMembers: MOCK_TEAM_MEMBERS,
  selectedClientId: null,
  totalOperatingBudget: 128000000,
  totalRevenue: 9440000,
  kpiAchievedCount: 2,
  totalKpiCount: 3,
  totalSavedHours: 241,
};

const portfolioSlice = createSlice({
  name: 'portfolio',
  initialState,
  reducers: {
    selectClient: (state, action: PayloadAction<string | null>) => {
      state.selectedClientId = action.payload;
    },
    updateClientRisk: (state, action: PayloadAction<{ id: string; riskLevel: Client['riskLevel']; riskScore: number }>) => {
      const client = state.clients.find(c => c.id === action.payload.id);
      if (client) {
        client.riskLevel = action.payload.riskLevel;
        client.riskScore = action.payload.riskScore;
      }
    },
    updateTeamMemberKpi: (state, action: PayloadAction<{ id: string; achieved: number; total: number }>) => {
      const member = state.teamMembers.find(m => m.id === action.payload.id);
      if (member) {
        member.kpiAchieved = action.payload.achieved;
        member.kpiTotal = action.payload.total;
      }
    },
  },
});

export const { selectClient, updateClientRisk, updateTeamMemberKpi } = portfolioSlice.actions;
export default portfolioSlice.reducer;