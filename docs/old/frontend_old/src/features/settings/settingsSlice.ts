import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// 타입 정의
export interface WorkspaceSettings {
  companyName: string;
  logoUrl: string;
  contactName: string;
  contactEmail: string;
  contactPhone: string;
}

export interface TokenUsage {
  totalTokens: number;
  usedTokens: number;
  remainingTokens: number;
  usageHistory: Array<{
    id: string;
    date: string;
    feature: string;
    tokens: number;
    description: string;
  }>;
}

export interface KPISettings {
  roasTarget: number;
  statusThresholds: {
    success: number;
    warning: number;
    danger: number;
  };
  ctrTarget: number;
  cpaTarget: number;
}

export interface NotificationSettings {
  emailEnabled: boolean;
  slackEnabled: boolean;
  recipients: string[];
  conditions: {
    roasBelowTarget: boolean;
    budgetExceeded: boolean;
    creativePoorPerformance: boolean;
    hitlPending: boolean;
  };
  alertThreshold: number;
}

export interface PlanInfo {
  currentPlan: 'starter' | 'professional' | 'enterprise';
  billingCycle: 'monthly' | 'yearly';
  nextBillingDate: string;
  paymentMethod: string;
  invoiceEmail: string;
}

interface SettingsState {
  workspace: WorkspaceSettings;
  tokenUsage: TokenUsage;
  kpiSettings: KPISettings;
  notifications: NotificationSettings;
  plan: PlanInfo;
  loading: boolean;
  error: string | null;
}

const initialState: SettingsState = {
  workspace: {
    companyName: '마케팅프로',
    logoUrl: '',
    contactName: '강지수',
    contactEmail: 'jisoo.kang@marketingpro.com',
    contactPhone: '02-1234-5678',
  },
  tokenUsage: {
    totalTokens: 100000,
    usedTokens: 65000,
    remainingTokens: 35000,
    usageHistory: [
      {
        id: '1',
        date: '2024-03-20',
        feature: '소재 자동 생성',
        tokens: 1500,
        description: '네이버 검색광고 소재 10개 생성',
      },
      {
        id: '2',
        date: '2024-03-19',
        feature: '리포트 생성',
        tokens: 800,
        description: '월간 성과 리포트 자동 생성',
      },
      {
        id: '3',
        date: '2024-03-18',
        feature: '예산 최적화',
        tokens: 2000,
        description: 'AI 예산 재배분 분석',
      },
    ],
  },
  kpiSettings: {
    roasTarget: 350,
    statusThresholds: {
      success: 400,
      warning: 300,
      danger: 200,
    },
    ctrTarget: 5.0,
    cpaTarget: 10000,
  },
  notifications: {
    emailEnabled: true,
    slackEnabled: false,
    recipients: ['team@marketingpro.com'],
    conditions: {
      roasBelowTarget: true,
      budgetExceeded: true,
      creativePoorPerformance: false,
      hitlPending: true,
    },
    alertThreshold: 80,
  },
  plan: {
    currentPlan: 'professional',
    billingCycle: 'monthly',
    nextBillingDate: '2024-04-01',
    paymentMethod: '신용카드 (****1234)',
    invoiceEmail: 'billing@marketingpro.com',
  },
  loading: false,
  error: null,
};

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    updateWorkspace: (state, action: PayloadAction<Partial<WorkspaceSettings>>) => {
      state.workspace = { ...state.workspace, ...action.payload };
    },
    updateKPISettings: (state, action: PayloadAction<Partial<KPISettings>>) => {
      state.kpiSettings = { ...state.kpiSettings, ...action.payload };
    },
    updateNotifications: (state, action: PayloadAction<Partial<NotificationSettings>>) => {
      state.notifications = { ...state.notifications, ...action.payload };
    },
    updateTokenUsage: (state, action: PayloadAction<Partial<TokenUsage>>) => {
      state.tokenUsage = { ...state.tokenUsage, ...action.payload };
    },
    updatePlan: (state, action: PayloadAction<Partial<PlanInfo>>) => {
      state.plan = { ...state.plan, ...action.payload };
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const {
  updateWorkspace,
  updateKPISettings,
  updateNotifications,
  updateTokenUsage,
  updatePlan,
  setLoading,
  setError,
} = settingsSlice.actions;

export default settingsSlice.reducer;