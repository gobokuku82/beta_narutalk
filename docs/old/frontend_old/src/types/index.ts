export type CampaignStatus = 'running' | 'paused' | 'ended';
export type RiskLevel = 'danger' | 'warning' | 'safe';
export type HitlType = 'creative' | 'budget' | 'report' | 'campaign';
export type HitlStatus = 'pending' | 'delayed' | 'approved' | 'rejected';
export type ChannelType = 'naver' | 'kakao' | 'meta' | 'google';

export interface KpiSummary {
  roas: number;
  roasChange: number;
  spend: number;
  spendBudget: number;
  conversions: number;
  cpa: number;
  monthlyAchievement: number;
  monthlyPrediction: number;
  // 추가
  mer: number;
  merChange: number;
  campaignDays: number;
  campaignStage: 'learning' | 'mature' | 'optimizing';
}

export interface ChannelPerformance {
  channel: ChannelType;
  status: 'safe' | 'warning' | 'danger';
  spend: number;
  roas: number;
  ctr: number;
  cpa: number;
  budgetRate: number;
  // 추가
  cvr: number;
  visitRetention: number;
  purchaseRetention: number;
}

export interface AiInsight {
  type: 'danger' | 'warning' | 'info';
  title: string;
  description: string;
}

export interface Creative {
  id: string;
  name: string;
  channel: ChannelType;
  spec: string;
  ctr: number;
  cvr: number;
  roas: number;
  cpa: number;
  cpc?: number;  // CPC 추가
  frequency: number;
  days: number;
  status: 'winner' | 'monitoring' | 'replace' | 'normal';
  // 추가
  aiScore: {
    sales: number;
    short: number;
    clear: number;
    visual: number;
    benefit: number;
  };
  aiScoreFeedback: string;
  lifeExpectDays: number;
}

export type HitlUrgency = 'critical' | 'warning' | 'normal';

export interface HitlFlowPosition {
  layer: 'intent' | 'plan' | 'execute' | 'result';  // 4개 주요 레이어
  subStep?: string;                                  // 실행 레이어의 세부 단계 이름
  stepNumber?: number;                              // 현재 세부 단계 번호
  totalSteps?: number;                              // 전체 세부 단계 수
  reason?: string;                                   // HITL 발생 사유
}

export interface HitlItem {
  id: string;
  type: HitlType;
  title: string;
  description: string;
  clientName: string;
  createdAt: string;
  waitMinutes: number;
  status: HitlStatus;
  urgency: HitlUrgency;           // 추가
  consequence?: string;           // 추가 — 방치 시 결과 메시지
  choices?: HitlBudgetChoice[];   // 추가 — budget_choice 타입용
  flowPosition?: HitlFlowPosition; // 추가 — 에이전트 플로우 내 위치 정보
}

export interface Client {
  id: string;
  name: string;
  ae: string;
  roas: number;
  roasVsTarget: number;
  riskLevel: RiskLevel;
  riskScore: number; // 1~5
  contractExpiry: string;
  revenue: number;
  // 추가
  mer: number;
  ltv: number;
  ltvChange: number;
}

export interface TeamMember {
  id: string;
  name: string;
  initials: string;
  clientCount: number;
  clients: string[];
  operatingBudget: number;
  kpiAchieved: number;
  kpiTotal: number;
  savedHours: number;
  hitlDelayed: number;
}

// 신규 타입 - BudgetSimulation
export interface BudgetSimulation {
  allocations: {
    channel: ChannelType;
    currentPct: number;
    simulatedPct: number;
  }[];
  predicted: {
    roas: number;
    roasDelta: number;
    conversions: number;
    conversionsDelta: number;
    cpa: number;
    cpaDelta: number;
  };
}

// 진단 항목
export interface DiagnosisItem {
  rank: number;
  cause: string;
  description: string;
  contribution: number;
}

// 예산 재배분
export interface BudgetReallocation {
  current: { [key in ChannelType]: number };
  recommended: { [key in ChannelType]: number };
  expectedEffect: {
    roasChange: number;
    conversionsChange: number;
    revenueChange: number;
  };
}

// 타겟 오디언스
export interface TargetAudience {
  name: string;
  roas: number;
  status: 'excellent' | 'good' | 'poor';
  recommendation?: string;
}

// 무전환 키워드
export interface NoConversionKeyword {
  keyword: string;
  channel: ChannelType;
  spend: number;
  clicks: number;
}

// 동종업계 벤치마크
export interface IndustryBenchmark {
  avgRoas: number;
  ourRoas: number;
  top10Roas: number;
  avgCpa: number;
  ourCpa: number;
  avgCvr: number;
  ourCvr: number;
  channelComparison: {
    [key in ChannelType]: number; // 업종 평균 대비 %
  };
}

// 채널별 상세 데이터 (성과분석용)
export interface ChannelDetail {
  channel: ChannelType;
  impressions: number;
  clicks: number;
  ctr: number;
  conversions: number;
  cvr: number;
  spend: number;
  roas: number;
  cpa: number;
}

// 클라이언트별 전체 데이터를 담는 타입
export interface ClientData {
  id: string;
  name: string;
  kpi: KpiSummary;
  channels: ChannelPerformance[];
  insights: AiInsight[];
  creatives: Creative[];
  hitlItems: HitlItem[];
  chartData: ChartDataPoint[];
  funnelData: FunnelData;
  budgetSimulation: BudgetSimulation;
  diagnosis: DiagnosisItem[];
  budgetReallocation: BudgetReallocation;
  targetAudiences: TargetAudience[];
  noConversionKeywords: NoConversionKeyword[];
  industryBenchmark: IndustryBenchmark;
  channelDetails: ChannelDetail[];
}

// 차트 데이터 타입
export interface ChartDataPoint {
  date: string;
  roas: number;
  ctr: number;
  cpa: number;
}

// 퍼널 단일 데이터 타입
export interface FunnelStageData {
  totalImpressions: number;
  stages: {
    from: string;
    to: string;
    dropRate: number;   // 이탈률 0~100
    remaining: number;  // 해당 단계 잔류 인원
  }[];
  overallConversionRate: number;
}

// 퍼널 데이터 타입 (채널별 분리)
export interface FunnelData {
  all: FunnelStageData;
  naver: FunnelStageData;
  meta: FunnelStageData;
  google: FunnelStageData;
  kakao: FunnelStageData;
}

// Agent Chat types
export type PipelineStepStatus = 'pending' | 'running' | 'done' | 'error';

export interface PipelineStep {
  id: string;
  label: string;
  status: PipelineStepStatus;
}

export interface TodoItem {
  id: string;
  label: string;
  status: 'pending' | 'running' | 'done';
  tags: string[];
  requiresHitl: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  cardType: 'text' | 'clarify' | 'gate' | 'hitl'; // hitl 타입 추가
  content?: string;                        // string → string? 로 변경
  timestamp: string;
  // clarify 카드용
  clarifyPlan?: {
    clientName: string;
    summary: string;
    steps: string[];
  };
  // gate 카드용
  gateQuestion?: string;
  gateChoices?: GateChoice[];
  // HITL 카드용
  hitlData?: {
    id: string;
    title: string;
    description: string;
    stage: string;
    recommendation: string;
  };
}

export interface TaskItem {
  id: string;
  index: number;
  label: string;
  tags: string[];
  status: 'pending' | 'running' | 'done';
  layer: LayerType;  // 어떤 layer에서 실행되는지
  result?: string;   // 실행 결과
}

export interface SystemLog {
  time: string;
  message: string;
  type: 'info' | 'success' | 'warn' | 'error';
}

// 새 타입 추가
export interface GateChoice {
  id: string;
  label: string;
  subLabel: string;
  effect: string;
  effectType: 'good' | 'warn' | 'neutral';
}

export interface HitlBudgetChoice {
  id: string;
  label: string;
  description: string;
  effect: string;
  effectType: 'positive' | 'warning' | 'neutral';
  isRecommended: boolean;
}

// LangGraph Layer 타입 정의
export type LayerType = 'cognitive' | 'planning' | 'execution' | 'response';
export type LayerStatus = 'idle' | 'running' | 'completed' | 'error' | 'waiting_hitl';
export type ExecutionType = 'sequential' | 'parallel' | 'swarm';

export interface CognitiveOutput {
  originalInput: string;
  correctedInput: string | null;
  intentAnalysis: {
    action: string;
    target: string;
    client: string;
    channel?: string;
    context?: string;
  };
  contextDetected?: string[];
  confidence: number;
}

export interface PlanningOutput {
  selectedAgents: string[];
  executionPlan: {
    type: ExecutionType;
    steps: string[];
  };
  estimatedTime: string;
  hitlRequired: string[];
}

export interface ExecutionStep {
  name: string;
  result: any;
  status: 'pending' | 'running' | 'completed' | 'error';
}

export interface ExecutionOutput {
  currentStep: number;
  totalSteps: number;
  steps: Record<string, ExecutionStep>;
}

export interface ResponseOutput {
  outputType: 'text' | 'image' | 'graph' | 'ppt' | 'mov';
  format: string;
  preview: any;
  data: any;
}

export interface LayerState<T> {
  status: LayerStatus;
  output: T | null;
  error: string | null;
  timestamp?: string;
}

export interface EngineMessage {
  layer: LayerType;
  type: 'progress' | 'hitl' | 'result' | 'log' | 'error';
  data: {
    status?: LayerStatus;
    output?: any;
    todo?: TodoItem[];
    hitlRequest?: any;
    error?: string;
    log?: string;
  };
}

// 트렌드 분석 타입 정의
export interface TrendKeyword {
  keyword: string;
  values: number[]; // 0~100 상대값
  dates: string[];
}

export interface ShoppingCategory {
  category: string;
  clicks: number[];
  dates: string[];
}

export interface SentimentAnalysis {
  positive: number;
  negative: number;
  neutral: number;
  samples: {
    id: string;
    title: string;
    snippet: string;
    sentiment: 'positive' | 'negative' | 'neutral';
    source: 'blog' | 'news';
    isSponsored?: boolean;
    publishedAt: string;
  }[];
}

export interface YouTubeTrend {
  id: string;
  title: string;
  viewCount: number;
  uploadDate: string;
  channelName: string;
  thumbnailUrl?: string;
}

export interface TrendData {
  keywords: TrendKeyword[];
  shoppingCategories: ShoppingCategory[];
  sentimentAnalysis: SentimentAnalysis;
  youtubeVideos: YouTubeTrend[];
}