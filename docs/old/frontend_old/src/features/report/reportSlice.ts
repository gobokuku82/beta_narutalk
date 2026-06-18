import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface WorkspaceSettings {
  companyName: string;
  logo: string;
  contactName: string;
  contactEmail: string;
  contactPhone: string;
}

interface ReportHistory {
  id: string;
  title: string;
  clientName: string;
  dateRange: string;
  createdAt: string;
  fileName: string;
  format: 'PDF' | 'PPT' | 'EXCEL';
}

interface ReportState {
  activeTab: 'template' | 'custom';
  customUploadFileName: string | null;
  customOutputFormat: 'pdf' | 'docx' | 'excel' | 'pptx';
  selectedDataOptions: string[];
  selectedTemplate: 'report' | 'client' | 'internal';
  selectedFormat: 'PDF' | 'PPT' | 'EXCEL';
  isGenerating: boolean;
  generationProgress: number;
  generationStatus: string;
  recentReports: ReportHistory[];
  workspaceSettings: WorkspaceSettings | null;
  includeWorkspaceInfo: boolean;
}

const initialState: ReportState = {
  activeTab: 'template',
  customUploadFileName: null,
  customOutputFormat: 'pdf',
  selectedDataOptions: [
    'KPI 요약',
    '채널별 성과',
    '소재 분석',
    '비용 최적화',
    '트렌드',
    '벤치마킹',
    'Goal Pacing'
  ],
  selectedTemplate: 'report',
  selectedFormat: 'PDF',
  isGenerating: false,
  generationProgress: 0,
  generationStatus: '',
  recentReports: [],
  workspaceSettings: null,
  includeWorkspaceInfo: true,
};

const reportSlice = createSlice({
  name: 'report',
  initialState,
  reducers: {
    setReportTab: (state, action: PayloadAction<'template' | 'custom'>) => {
      state.activeTab = action.payload;
    },
    setCustomFile: (state, action: PayloadAction<string | null>) => {
      state.customUploadFileName = action.payload;
    },
    setCustomOutputFormat: (state, action: PayloadAction<ReportState['customOutputFormat']>) => {
      state.customOutputFormat = action.payload;
    },
    toggleDataOption: (state, action: PayloadAction<string>) => {
      const option = action.payload;
      if (state.selectedDataOptions.includes(option)) {
        state.selectedDataOptions = state.selectedDataOptions.filter((o: string) => o !== option);
      } else {
        state.selectedDataOptions.push(option);
      }
    },
    setSelectedTemplate: (state, action: PayloadAction<ReportState['selectedTemplate']>) => {
      state.selectedTemplate = action.payload;
    },
    setSelectedFormat: (state, action: PayloadAction<ReportState['selectedFormat']>) => {
      state.selectedFormat = action.payload;
    },
    startReportGeneration: (state) => {
      state.isGenerating = true;
      state.generationProgress = 0;
      state.generationStatus = '보고서를 생성 중입니다';
    },
    updateGenerationProgress: (state, action: PayloadAction<{ progress: number; status: string }>) => {
      state.generationProgress = action.payload.progress;
      state.generationStatus = action.payload.status;
    },
    completeReportGeneration: (state, action: PayloadAction<ReportHistory>) => {
      state.isGenerating = false;
      state.generationProgress = 100;
      state.generationStatus = '보고서 생성 완료';
      state.recentReports.unshift(action.payload);
      if (state.recentReports.length > 10) {
        state.recentReports.pop();
      }
    },
    failReportGeneration: (state, action: PayloadAction<string>) => {
      state.isGenerating = false;
      state.generationProgress = 0;
      state.generationStatus = action.payload;
    },
    setWorkspaceSettings: (state, action: PayloadAction<WorkspaceSettings>) => {
      state.workspaceSettings = action.payload;
    },
    toggleIncludeWorkspaceInfo: (state) => {
      state.includeWorkspaceInfo = !state.includeWorkspaceInfo;
    },
    setRecentReports: (state, action: PayloadAction<ReportHistory[]>) => {
      state.recentReports = action.payload;
    },
  },
});

export const {
  setReportTab,
  setCustomFile,
  setCustomOutputFormat,
  toggleDataOption,
  setSelectedTemplate,
  setSelectedFormat,
  startReportGeneration,
  updateGenerationProgress,
  completeReportGeneration,
  failReportGeneration,
  setWorkspaceSettings,
  toggleIncludeWorkspaceInfo,
  setRecentReports,
} = reportSlice.actions;

export default reportSlice.reducer;