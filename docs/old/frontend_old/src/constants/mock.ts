import type {
  HitlItem,
  Client,
  TeamMember,
  PipelineStep,
  TodoItem,
  ChatMessage,
  TaskItem,
  SystemLog,
  ClientData
} from '../types';

// 클라이언트 목록 (3개로 축소)
export const MOCK_CLIENT_LIST = [
  '코스모스 뷰티',
  '홈플렉스',
  '스타일워크'
];

// 각 클라이언트별 상세 데이터
export const CLIENT_DATA_MAP: Record<string, ClientData> = {
  '코스모스 뷰티': {
    id: 'c1',
    name: '코스모스 뷰티',
    kpi: {
      roas: 385,
      roasChange: 12,
      spend: 2140000,
      spendBudget: 3000000,
      conversions: 247,
      cpa: 8664,
      monthlyAchievement: 63,
      monthlyPrediction: 104,
      mer: 4.2,
      merChange: 0.3,
      campaignDays: 5,
      campaignStage: 'learning',
    },
    channels: [
      { channel: 'naver', status: 'safe', spend: 780000, roas: 421, ctr: 3.2, cpa: 7100, budgetRate: 78, cvr: 3.2, visitRetention: 41, purchaseRetention: 22 },
      { channel: 'kakao', status: 'warning', spend: 510000, roas: 298, ctr: 2.1, cpa: 11400, budgetRate: 85, cvr: 1.9, visitRetention: 33, purchaseRetention: 14 },
      { channel: 'meta', status: 'danger', spend: 610000, roas: 201, ctr: 1.4, cpa: 18200, budgetRate: 61, cvr: 1.1, visitRetention: 27, purchaseRetention: 9 },
      { channel: 'google', status: 'safe', spend: 240000, roas: 510, ctr: 5.1, cpa: 5800, budgetRate: 42, cvr: 4.1, visitRetention: 48, purchaseRetention: 28 },
    ],
    insights: [
      { type: 'danger', title: '메타 CTR 급락', description: '소재 #M-04 Freq 4.7, CTR 1.4% (기준 2.5% 이탈). 소재 교체 권고' },
      { type: 'warning', title: '카카오 예산 85% 소진', description: '오후 3시 기준. 야간 노출 누락 위험. 예산 증액 제안 대기' },
      { type: 'info', title: '구글 ROAS 510%', description: '스킨케어_25-34 그룹 고성과. 예산 +15만 시 전환 +18% 예상' },
    ],
    creatives: [
      {
        id: 'N-02', name: '#N-02 봄캠페인A', channel: 'naver', spec: '250×250', ctr: 4.8, cvr: 3.2, roas: 421, cpa: 7100, cpc: 850, frequency: 1.4, days: 7, status: 'winner',
        aiScore: { sales: 88, short: 92, clear: 85, visual: 90, benefit: 87 },
        aiScoreFeedback: '전반적으로 우수. 베네핏 문구를 첫 줄로 이동 권장',
        lifeExpectDays: 8,
      },
      {
        id: 'G-01', name: '#G-01 스킨25-34', channel: 'google', spec: '반응형', ctr: 5.1, cvr: 4.1, roas: 510, cpa: 5800, cpc: 520, frequency: 1.1, days: 7, status: 'winner',
        aiScore: { sales: 91, short: 95, clear: 90, visual: 93, benefit: 92 },
        aiScoreFeedback: '5개 조건 모두 기준 이상. 현행 유지',
        lifeExpectDays: 12,
      },
      {
        id: 'K-03', name: '#K-03 카카오B', channel: 'kakao', spec: '1200×628', ctr: 2.9, cvr: 2.4, roas: 298, cpa: 9200, cpc: 1200, frequency: 2.2, days: 10, status: 'monitoring',
        aiScore: { sales: 72, short: 80, clear: 68, visual: 75, benefit: 70 },
        aiScoreFeedback: '명확함 점수 낮음. CTA 문구 단순화 필요',
        lifeExpectDays: 4,
      },
      {
        id: 'M-04', name: '#M-04 토너기획전', channel: 'meta', spec: '1080×1080', ctr: 1.4, cvr: 1.1, roas: 201, cpa: 18200, cpc: 1850, frequency: 4.7, days: 14, status: 'replace',
        aiScore: { sales: 55, short: 60, clear: 50, visual: 62, benefit: 48 },
        aiScoreFeedback: '고객 중심 메시지 부재. 전면 재기획 권고',
        lifeExpectDays: 0,
      },
    ],
    hitlItems: [
      {
        id: 'h1',
        type: 'creative',
        title: '네이버 배너 3종 — AI 생성 완료',
        description: '봄 시즌 캠페인 · 따봉학습 반영',
        clientName: '코스모스 뷰티',
        createdAt: '14:14',
        waitMinutes: 23,
        status: 'pending',
        urgency: 'warning',
        consequence: '빠른 승인 시 오늘 저녁 타임 노출 가능',
        flowPosition: {
          layer: 'execute',
          subStep: '소재 생성',
          stepNumber: 3,
          totalSteps: 3,
          reason: 'AI 생성 소재 품질 검증 필요'
        },
      },
      {
        id: 'h2',
        type: 'budget',
        title: '예산 재배분 — 메타 -₩150K → 구글',
        description: 'Anomaly 감지 기반 · ROAS +31%p 예상',
        clientName: '코스모스 뷰티',
        createdAt: '13:30',
        waitMinutes: 64,
        status: 'pending',
        urgency: 'critical',
        consequence: '매분 ₩1,800 비효율 지출 중',
        flowPosition: {
          layer: 'plan',
          reason: '예산 초과 승인 권한 필요'
        },
        choices: [
          {
            id: 'ch1',
            label: '구글 예산 증액',
            description: '메타 -₩150K → 구글 +₩150K',
            effect: '예상 ROAS: 385% → 416%',
            effectType: 'positive',
            isRecommended: true,
          },
          {
            id: 'ch2',
            label: '현행 유지',
            description: '현재 배분 유지',
            effect: '메타 소재 교체 후 재평가',
            effectType: 'warning',
            isRecommended: false,
          },
        ],
      },
    ],
    chartData: [
      { date: '3/11', roas: 380, ctr: 3.1, cpa: 8900 },
      { date: '3/12', roas: 395, ctr: 3.3, cpa: 8600 },
      { date: '3/13', roas: 375, ctr: 3.0, cpa: 9100 },
      { date: '3/14', roas: 410, ctr: 3.5, cpa: 8200 },
      { date: '3/15', roas: 385, ctr: 3.2, cpa: 8664 },
      { date: '3/16', roas: 420, ctr: 3.6, cpa: 8100 },
      { date: '3/17', roas: 385, ctr: 3.2, cpa: 8664 },
    ],
    funnelData: {
      all: {
        totalImpressions: 524000,
        stages: [
          { from: '노출', to: '클릭', dropRate: 96.8, remaining: 16768 },
          { from: '클릭', to: '랜딩', dropRate: 20.0, remaining: 13414 },
          { from: '랜딩', to: '장바구니', dropRate: 80.0, remaining: 2683 },
          { from: '장바구니', to: '구매', dropRate: 90.8, remaining: 247 }
        ],
        overallConversionRate: 0.047
      },
      naver: {
        totalImpressions: 188640,
        stages: [
          { from: '노출', to: '클릭', dropRate: 97.2, remaining: 5282 },
          { from: '클릭', to: '랜딩', dropRate: 18.0, remaining: 4331 },
          { from: '랜딩', to: '장바구니', dropRate: 75.0, remaining: 1083 },
          { from: '장바구니', to: '구매', dropRate: 88.0, remaining: 130 }
        ],
        overallConversionRate: 0.069
      },
      meta: {
        totalImpressions: 146720,
        stages: [
          { from: '노출', to: '클릭', dropRate: 95.8, remaining: 6162 },
          { from: '클릭', to: '랜딩', dropRate: 25.0, remaining: 4622 },
          { from: '랜딩', to: '장바구니', dropRate: 82.0, remaining: 832 },
          { from: '장바구니', to: '구매', dropRate: 92.0, remaining: 67 }
        ],
        overallConversionRate: 0.046
      },
      google: {
        totalImpressions: 41920,
        stages: [
          { from: '노출', to: '클릭', dropRate: 94.2, remaining: 2431 },
          { from: '클릭', to: '랜딩', dropRate: 12.0, remaining: 2140 },
          { from: '랜딩', to: '장바구니', dropRate: 70.0, remaining: 642 },
          { from: '장바구니', to: '구매', dropRate: 85.0, remaining: 96 }
        ],
        overallConversionRate: 0.229
      },
      kakao: {
        totalImpressions: 125760,
        stages: [
          { from: '노출', to: '클릭', dropRate: 98.1, remaining: 2390 },
          { from: '클릭', to: '랜딩', dropRate: 30.0, remaining: 1673 },
          { from: '랜딩', to: '장바구니', dropRate: 88.0, remaining: 201 },
          { from: '장바구니', to: '구매', dropRate: 95.0, remaining: 10 }
        ],
        overallConversionRate: 0.008
      }
    },
    budgetSimulation: {
      allocations: [
        { channel: 'google', currentPct: 8, simulatedPct: 15 },
        { channel: 'meta', currentPct: 28, simulatedPct: 20 },
        { channel: 'naver', currentPct: 36, simulatedPct: 40 },
        { channel: 'kakao', currentPct: 24, simulatedPct: 25 },
      ],
      predicted: {
        roas: 4.5,
        roasDelta: 0.3,
        conversions: 920,
        conversionsDelta: 73,
        cpa: 12100,
        cpaDelta: -1100,
      },
    },
    diagnosis: [
      { rank: 1, cause: '메타 소재 피로도 급증', description: 'Frequency 4.7 초과, CTR 40% 하락', contribution: 45 },
      { rank: 2, cause: '카카오 타겟 부적합', description: '연령대 미스매치로 인한 저조한 전환', contribution: 30 },
      { rank: 3, cause: '구글 예산 부족', description: '우수 성과 대비 예산 배정 미흡', contribution: 25 },
    ],
    budgetReallocation: {
      current: { naver: 1000000, kakao: 600000, meta: 700000, google: 300000 },
      recommended: { naver: 900000, kakao: 600000, meta: 500000, google: 600000 },
      expectedEffect: { roasChange: 63, conversionsChange: 52, revenueChange: 2140000 },
    },
    targetAudiences: [
      { name: '스킨케어 관심 25-34 여성', roas: 512, status: 'excellent' },
      { name: '프리미엄 관심 35-44 여성', roas: 298, status: 'good' },
      { name: '기초 화장품 25-34 남성', roas: 201, status: 'poor', recommendation: '타겟 제외 권고' },
      { name: '안티에이징 40-49 여성', roas: 345, status: 'good' },
    ],
    noConversionKeywords: [
      { keyword: '화장품 세일', channel: 'naver', spend: 456000, clicks: 1230 },
      { keyword: '스킨케어 할인', channel: 'google', spend: 312000, clicks: 890 },
      { keyword: '무료배송', channel: 'kakao', spend: 234000, clicks: 567 },
      { keyword: '뷰티 이벤트', channel: 'meta', spend: 189000, clicks: 445 },
    ],
    industryBenchmark: {
      avgRoas: 342, ourRoas: 385, top10Roas: 421,
      avgCpa: 12500, ourCpa: 8664,
      avgCvr: 2.1, ourCvr: 2.8,
      channelComparison: { naver: 15, kakao: -13, meta: -28, google: 32 },
    },
    channelDetails: [
      { channel: 'naver', impressions: 524123, clicks: 16772, ctr: 3.2, conversions: 134, cvr: 3.2, spend: 780000, roas: 421, cpa: 7100 },
      { channel: 'kakao', impressions: 412456, clicks: 8661, ctr: 2.1, conversions: 45, cvr: 1.9, spend: 510000, roas: 298, cpa: 11400 },
      { channel: 'meta', impressions: 892134, clicks: 12490, ctr: 1.4, conversions: 34, cvr: 1.1, spend: 610000, roas: 201, cpa: 18200 },
      { channel: 'google', impressions: 156234, clicks: 7968, ctr: 5.1, conversions: 34, cvr: 4.1, spend: 240000, roas: 510, cpa: 5800 },
    ],
  },
  '홈플렉스': {
    id: 'c2',
    name: '홈플렉스',
    kpi: {
      roas: 201,
      roasChange: -12,
      spend: 4120000,
      spendBudget: 5000000,
      conversions: 298,
      cpa: 13826,
      monthlyAchievement: 38,
      monthlyPrediction: 65,
      mer: 2.1,
      merChange: -0.5,
      campaignDays: 15,
      campaignStage: 'mature',
    },
    channels: [
      { channel: 'naver', status: 'danger', spend: 1450000, roas: 189, ctr: 2.1, cpa: 15200, budgetRate: 92, cvr: 1.7, visitRetention: 22, purchaseRetention: 8 },
      { channel: 'kakao', status: 'danger', spend: 1200000, roas: 178, ctr: 1.8, cpa: 16800, budgetRate: 88, cvr: 1.4, visitRetention: 19, purchaseRetention: 6 },
      { channel: 'meta', status: 'warning', spend: 980000, roas: 212, ctr: 2.3, cpa: 14200, budgetRate: 75, cvr: 1.9, visitRetention: 25, purchaseRetention: 10 },
      { channel: 'google', status: 'warning', spend: 490000, roas: 245, ctr: 2.8, cpa: 12400, budgetRate: 65, cvr: 2.3, visitRetention: 30, purchaseRetention: 13 },
    ],
    insights: [
      { type: 'danger', title: '긴급: 전체 ROAS 위기', description: 'ROAS 201% 역대 최저. 즉시 조치 필요' },
      { type: 'danger', title: '네이버/카카오 적자', description: '두 매체 ROAS 200% 미만. 캠페인 중단 검토' },
      { type: 'warning', title: '소재 전면 교체 필요', description: 'Freq 평균 4.2. 모든 소재 피로도 한계' },
      { type: 'info', title: '구글 상대적 양호', description: '구글만 목표 근접. 예산 집중 고려' },
    ],
    creatives: [
      {
        id: 'HF-N01', name: '가구 할인전', channel: 'naver', spec: '250×250', ctr: 2.2, cvr: 1.8, roas: 189, cpa: 15200, frequency: 4.5, days: 18, status: 'replace',
        aiScore: { sales: 42, short: 48, clear: 39, visual: 45, benefit: 40 },
        aiScoreFeedback: '즉시 교체. 모든 지표 기준 미달',
        lifeExpectDays: 0,
      },
      {
        id: 'HF-K02', name: '인테리어 패키지', channel: 'kakao', spec: '1200×628', ctr: 1.9, cvr: 1.5, roas: 178, cpa: 16800, frequency: 4.8, days: 20, status: 'replace',
        aiScore: { sales: 38, short: 42, clear: 35, visual: 40, benefit: 36 },
        aiScoreFeedback: '성과 최악. 전략 재검토 필요',
        lifeExpectDays: 0,
      },
      {
        id: 'HF-M03', name: '리모델링 상담', channel: 'meta', spec: '1080×1080', ctr: 2.4, cvr: 2.0, roas: 212, cpa: 14200, frequency: 3.9, days: 14, status: 'replace',
        aiScore: { sales: 48, short: 52, clear: 45, visual: 50, benefit: 46 },
        aiScoreFeedback: '긴급 교체 권고',
        lifeExpectDays: 1,
      },
    ],
    hitlItems: [
      {
        id: 'hf-h1',
        type: 'campaign',
        title: '긴급: 캠페인 전략 재수립',
        description: 'AI 전면 재기획안 제시',
        clientName: '홈플렉스',
        createdAt: '08:00',
        waitMinutes: 420,
        status: 'delayed',
        urgency: 'critical',
        consequence: '오늘 내 미승인 시 일 ₩150K 손실 지속',
        flowPosition: {
          layer: 'intent',
          reason: '캠페인 전략 변경 규모가 큼'
        },
      },
      {
        id: 'hf-h2',
        type: 'creative',
        title: '전 매체 소재 20종 교체 대기',
        description: '성과 보장 AI 소재 세트',
        clientName: '홈플렉스',
        createdAt: '09:30',
        waitMinutes: 300,
        status: 'delayed',
        urgency: 'critical',
        consequence: '매시간 ₩8,500 손실 중',
        flowPosition: {
          layer: 'execute',
          subStep: '대량 소재 생성',
          stepNumber: 2,
          totalSteps: 4,
          reason: '20종 동시 교체에 대한 승인 필요'
        },
      },
      {
        id: 'hf-h3',
        type: 'budget',
        title: '예산 50% 삭감 또는 재배분 선택',
        description: '손실 최소화 긴급 조치',
        clientName: '홈플렉스',
        createdAt: '10:00',
        waitMinutes: 240,
        status: 'delayed',
        urgency: 'critical',
        consequence: '결정 지연으로 추가 손실 확대',
        flowPosition: {
          layer: 'result',
          reason: '최종 결과 적용 전 승인 필요'
        },
        choices: [
          {
            id: 'hf-ch1',
            label: '전체 예산 50% 삭감',
            description: '손실 방지 우선',
            effect: '일 손실 ₩75K → ₩38K',
            effectType: 'warning',
            isRecommended: false,
          },
          {
            id: 'hf-ch2',
            label: '구글 집중 재배분',
            description: '타 매체 중단, 구글 올인',
            effect: 'ROAS 201% → 238% 예상',
            effectType: 'positive',
            isRecommended: true,
          },
        ],
      },
    ],
    chartData: [
      { date: '3/11', roas: 245, ctr: 2.8, cpa: 12100 },
      { date: '3/12', roas: 232, ctr: 2.6, cpa: 12800 },
      { date: '3/13', roas: 218, ctr: 2.4, cpa: 13500 },
      { date: '3/14', roas: 205, ctr: 2.2, cpa: 14200 },
      { date: '3/15', roas: 201, ctr: 2.1, cpa: 13826 },
      { date: '3/16', roas: 195, ctr: 2.0, cpa: 14800 },
      { date: '3/17', roas: 198, ctr: 2.1, cpa: 14500 },
    ],
    funnelData: {
      all: {
        totalImpressions: 892000,
        stages: [
          { from: '노출', to: '클릭', dropRate: 97.9, remaining: 18732 },
          { from: '클릭', to: '랜딩', dropRate: 30.0, remaining: 13112 },
          { from: '랜딩', to: '장바구니', dropRate: 75.0, remaining: 3278 },
          { from: '장바구니', to: '구매', dropRate: 90.9, remaining: 298 }
        ],
        overallConversionRate: 0.033
      },
      naver: {
        totalImpressions: 312200,
        stages: [
          { from: '노출', to: '클릭', dropRate: 98.5, remaining: 4683 },
          { from: '클릭', to: '랜딩', dropRate: 35.0, remaining: 3044 },
          { from: '랜딩', to: '장바구니', dropRate: 78.0, remaining: 670 },
          { from: '장바구니', to: '구매', dropRate: 93.0, remaining: 47 }
        ],
        overallConversionRate: 0.015
      },
      meta: {
        totalImpressions: 214080,
        stages: [
          { from: '노출', to: '클릭', dropRate: 97.8, remaining: 4710 },
          { from: '클릭', to: '랜딩', dropRate: 28.0, remaining: 3391 },
          { from: '랜딩', to: '장바구니', dropRate: 73.0, remaining: 915 },
          { from: '장바구니', to: '구매', dropRate: 89.0, remaining: 101 }
        ],
        overallConversionRate: 0.047
      },
      google: {
        totalImpressions: 107040,
        stages: [
          { from: '노출', to: '클릭', dropRate: 96.5, remaining: 3746 },
          { from: '클릭', to: '랜딩', dropRate: 22.0, remaining: 2922 },
          { from: '랜딩', to: '장바구니', dropRate: 68.0, remaining: 935 },
          { from: '장바구니', to: '구매', dropRate: 86.0, remaining: 131 }
        ],
        overallConversionRate: 0.122
      },
      kakao: {
        totalImpressions: 258680,
        stages: [
          { from: '노출', to: '클릭', dropRate: 98.3, remaining: 4397 },
          { from: '클릭', to: '랜딩', dropRate: 38.0, remaining: 2726 },
          { from: '랜딩', to: '장바구니', dropRate: 82.0, remaining: 491 },
          { from: '장바구니', to: '구매', dropRate: 95.0, remaining: 25 }
        ],
        overallConversionRate: 0.010
      }
    },
    budgetSimulation: {
      allocations: [
        { channel: 'google', currentPct: 12, simulatedPct: 60 },
        { channel: 'meta', currentPct: 24, simulatedPct: 30 },
        { channel: 'naver', currentPct: 35, simulatedPct: 10 },
        { channel: 'kakao', currentPct: 29, simulatedPct: 0 },
      ],
      predicted: {
        roas: 2.4,
        roasDelta: 0.39,
        conversions: 320,
        conversionsDelta: 22,
        cpa: 11800,
        cpaDelta: -2026,
      },
    },
    diagnosis: [
      { rank: 1, cause: '전체 타겟 설정 오류', description: '구매력 낮은 연령대 과다 노출', contribution: 55 },
      { rank: 2, cause: '경쟁사 가격 공격', description: '동일 상품 30% 저가 판매 중', contribution: 25 },
      { rank: 3, cause: '계절성 수요 감소', description: '봄철 가구 구매 감소 트렌드', contribution: 20 },
    ],
    budgetReallocation: {
      current: { naver: 800000, kakao: 400000, meta: 500000, google: 200000 },
      recommended: { naver: 200000, kakao: 0, meta: 600000, google: 1100000 },
      expectedEffect: { roasChange: 39, conversionsChange: 22, revenueChange: 741000 },
    },
    targetAudiences: [
      { name: '신혼부부 28-35', roas: 245, status: 'poor' },
      { name: '리모델링 관심 35-45', roas: 312, status: 'good' },
      { name: '원룸 자취생 20-27', roas: 178, status: 'poor', recommendation: '즉시 제외' },
      { name: '프리미엄 가구 40-55', roas: 289, status: 'good' },
    ],
    noConversionKeywords: [
      { keyword: '가구 세일', channel: 'naver', spend: 234000, clicks: 890 },
      { keyword: '소파 할인', channel: 'google', spend: 198000, clicks: 567 },
      { keyword: '무료설치', channel: 'kakao', spend: 167000, clicks: 445 },
      { keyword: '인테리어', channel: 'meta', spend: 145000, clicks: 334 },
    ],
    industryBenchmark: {
      avgRoas: 320, ourRoas: 298, top10Roas: 380,
      avgCpa: 35000, ourCpa: 45600,
      avgCvr: 1.8, ourCvr: 1.2,
      channelComparison: { naver: -22, kakao: -18, meta: -35, google: 12 },
    },
    channelDetails: [
      { channel: 'naver', impressions: 234567, clicks: 4567, ctr: 1.9, conversions: 23, cvr: 0.5, spend: 800000, roas: 289, cpa: 34783 },
      { channel: 'kakao', impressions: 198765, clicks: 2345, ctr: 1.2, conversions: 12, cvr: 0.5, spend: 400000, roas: 245, cpa: 33333 },
      { channel: 'meta', impressions: 345678, clicks: 3456, ctr: 1.0, conversions: 15, cvr: 0.4, spend: 500000, roas: 198, cpa: 33333 },
      { channel: 'google', impressions: 123456, clicks: 2469, ctr: 2.0, conversions: 18, cvr: 0.7, spend: 200000, roas: 378, cpa: 11111 },
    ],
  },
  '스타일워크': {
    id: 'c3',
    name: '스타일워크',
    kpi: {
      roas: 512,
      roasChange: 15,
      spend: 3850000,
      spendBudget: 4800000,
      conversions: 485,
      cpa: 7938,
      monthlyAchievement: 78,
      monthlyPrediction: 125,
      mer: 5.8,
      merChange: 0.6,
      campaignDays: 20,
      campaignStage: 'mature',
    },
    channels: [
      { channel: 'naver', status: 'safe', spend: 1420000, roas: 548, ctr: 4.8, cpa: 6900, budgetRate: 74, cvr: 4.2, visitRetention: 52, purchaseRetention: 32 },
      { channel: 'kakao', status: 'safe', spend: 1080000, roas: 489, ctr: 4.2, cpa: 7400, budgetRate: 68, cvr: 3.8, visitRetention: 46, purchaseRetention: 28 },
      { channel: 'meta', status: 'safe', spend: 890000, roas: 502, ctr: 3.9, cpa: 7800, budgetRate: 62, cvr: 3.5, visitRetention: 43, purchaseRetention: 25 },
      { channel: 'google', status: 'safe', spend: 460000, roas: 521, ctr: 5.2, cpa: 7200, budgetRate: 58, cvr: 4.5, visitRetention: 50, purchaseRetention: 30 },
    ],
    insights: [
      { type: 'info', title: '최고 성과 달성', description: '전 매체 ROAS 500% 돌파. 역대 최고 기록' },
      { type: 'info', title: '네이버 특별 성과', description: 'ROAS 548%. 베스트 프랙티스 사례' },
      { type: 'info', title: '확장 가능성', description: '현 효율 유지하며 예산 30% 증액 가능' },
    ],
    creatives: [
      {
        id: 'SW-N01', name: '신상 스니커즈', channel: 'naver', spec: '250×250', ctr: 5.2, cvr: 4.6, roas: 548, cpa: 6900, frequency: 1.3, days: 5, status: 'winner',
        aiScore: { sales: 95, short: 93, clear: 94, visual: 96, benefit: 92 },
        aiScoreFeedback: '완벽에 가까운 소재. 베스트 프랙티스',
        lifeExpectDays: 15,
      },
      {
        id: 'SW-M02', name: '시즌오프 세일', channel: 'meta', spec: '1080×1080', ctr: 4.3, cvr: 3.9, roas: 502, cpa: 7800, frequency: 1.5, days: 6, status: 'winner',
        aiScore: { sales: 88, short: 90, clear: 87, visual: 91, benefit: 86 },
        aiScoreFeedback: '매우 우수. 장기 운영 적합',
        lifeExpectDays: 12,
      },
      {
        id: 'SW-K03', name: '봄 신상 컬렉션', channel: 'kakao', spec: '1200×628', ctr: 4.5, cvr: 4.0, roas: 489, cpa: 7400, frequency: 1.4, days: 7, status: 'winner',
        aiScore: { sales: 90, short: 88, clear: 89, visual: 92, benefit: 87 },
        aiScoreFeedback: '우수한 성과 지속',
        lifeExpectDays: 11,
      },
      {
        id: 'SW-G04', name: '스니커즈 검색광고', channel: 'google', spec: '반응형', ctr: 5.5, cvr: 4.8, roas: 521, cpa: 7200, frequency: 1.2, days: 6, status: 'winner',
        aiScore: { sales: 93, short: 91, clear: 92, visual: 90, benefit: 89 },
        aiScoreFeedback: '검색 광고 최적화 완료',
        lifeExpectDays: 13,
      },
    ],
    hitlItems: [
      {
        id: 'sw-h1',
        type: 'report',
        title: '월간 성과 리포트 발송 준비',
        description: '베스트 프랙티스 사례 포함',
        clientName: '스타일워크',
        createdAt: '15:00',
        waitMinutes: 30,
        status: 'pending',
        urgency: 'normal',
        consequence: '오늘 중 클라이언트 발송',
        flowPosition: {
          layer: 'result',
          reason: '리포트 발송 전 최종 검토'
        },
      },
    ],
    chartData: [
      { date: '3/11', roas: 478, ctr: 4.3, cpa: 8200 },
      { date: '3/12', roas: 495, ctr: 4.5, cpa: 8000 },
      { date: '3/13', roas: 502, ctr: 4.6, cpa: 7900 },
      { date: '3/14', roas: 518, ctr: 4.8, cpa: 7700 },
      { date: '3/15', roas: 512, ctr: 4.7, cpa: 7938 },
      { date: '3/16', roas: 525, ctr: 4.9, cpa: 7600 },
      { date: '3/17', roas: 520, ctr: 4.8, cpa: 7700 },
    ],
    funnelData: {
      all: {
        totalImpressions: 745000,
        stages: [
          { from: '노출', to: '클릭', dropRate: 95.2, remaining: 35760 },
          { from: '클릭', to: '랜딩', dropRate: 15.0, remaining: 30396 },
          { from: '랜딩', to: '장바구니', dropRate: 80.0, remaining: 6079 },
          { from: '장바구니', to: '구매', dropRate: 92.0, remaining: 485 }
        ],
        overallConversionRate: 0.065
      },
      naver: {
        totalImpressions: 275650,
        stages: [
          { from: '노출', to: '클릭', dropRate: 95.0, remaining: 13783 },
          { from: '클릭', to: '랜딩', dropRate: 12.0, remaining: 12129 },
          { from: '랜딩', to: '장바구니', dropRate: 76.0, remaining: 2911 },
          { from: '장바구니', to: '구매', dropRate: 89.0, remaining: 320 }
        ],
        overallConversionRate: 0.116
      },
      meta: {
        totalImpressions: 156450,
        stages: [
          { from: '노출', to: '클릭', dropRate: 96.2, remaining: 5945 },
          { from: '클릭', to: '랜딩', dropRate: 18.0, remaining: 4875 },
          { from: '랜딩', to: '장바구니', dropRate: 79.0, remaining: 1024 },
          { from: '장바구니', to: '구매', dropRate: 91.0, remaining: 92 }
        ],
        overallConversionRate: 0.059
      },
      google: {
        totalImpressions: 119200,
        stages: [
          { from: '노출', to: '클릭', dropRate: 94.0, remaining: 7152 },
          { from: '클릭', to: '랜딩', dropRate: 10.0, remaining: 6437 },
          { from: '랜딩', to: '장바구니', dropRate: 72.0, remaining: 1802 },
          { from: '장바구니', to: '구매', dropRate: 88.0, remaining: 216 }
        ],
        overallConversionRate: 0.181
      },
      kakao: {
        totalImpressions: 193700,
        stages: [
          { from: '노출', to: '클릭', dropRate: 96.8, remaining: 6198 },
          { from: '클릭', to: '랜딩', dropRate: 20.0, remaining: 4958 },
          { from: '랜딩', to: '장바구니', dropRate: 85.0, remaining: 744 },
          { from: '장바구니', to: '구매', dropRate: 94.0, remaining: 45 }
        ],
        overallConversionRate: 0.023
      }
    },
    budgetSimulation: {
      allocations: [
        { channel: 'naver', currentPct: 37, simulatedPct: 38 },
        { channel: 'kakao', currentPct: 28, simulatedPct: 27 },
        { channel: 'meta', currentPct: 23, simulatedPct: 22 },
        { channel: 'google', currentPct: 12, simulatedPct: 13 },
      ],
      predicted: {
        roas: 5.2,
        roasDelta: 0.08,
        conversions: 500,
        conversionsDelta: 15,
        cpa: 7700,
        cpaDelta: -238,
      },
    },
    diagnosis: [
      { rank: 1, cause: '구글 예산 부족', description: '고효율 채널 예산 제한', contribution: 40 },
      { rank: 2, cause: '네이버 포화 상태', description: '추가 예산 대비 효과 감소', contribution: 35 },
      { rank: 3, cause: '메타 타겟 최적화 필요', description: '관심사 타겟팅 정교화 필요', contribution: 25 },
    ],
    budgetReallocation: {
      current: { naver: 1200000, kakao: 800000, meta: 600000, google: 400000 },
      recommended: { naver: 1100000, kakao: 750000, meta: 650000, google: 500000 },
      expectedEffect: { roasChange: 8, conversionsChange: 15, revenueChange: 384000 },
    },
    targetAudiences: [
      { name: '패션 트렌드세터 20-29', roas: 468, status: 'excellent' },
      { name: 'SNS 활동층 25-34', roas: 445, status: 'excellent' },
      { name: '직장인 캐주얼 30-39', roas: 389, status: 'good' },
      { name: '럭셔리 패션 35-45', roas: 356, status: 'good' },
    ],
    noConversionKeywords: [
      { keyword: '패션 세일', channel: 'naver', spend: 123000, clicks: 456 },
      { keyword: '옷 할인', channel: 'google', spend: 89000, clicks: 234 },
      { keyword: '무료반품', channel: 'kakao', spend: 67000, clicks: 189 },
      { keyword: '스타일 추천', channel: 'meta', spend: 45000, clicks: 123 },
    ],
    industryBenchmark: {
      avgRoas: 365, ourRoas: 422, top10Roas: 450,
      avgCpa: 9800, ourCpa: 7938,
      avgCvr: 2.5, ourCvr: 3.1,
      channelComparison: { naver: 18, kakao: 8, meta: 22, google: 28 },
    },
    channelDetails: [
      { channel: 'naver', impressions: 678901, clicks: 21725, ctr: 3.2, conversions: 189, cvr: 0.9, spend: 1200000, roas: 445, cpa: 6349 },
      { channel: 'kakao', impressions: 543210, clicks: 13025, ctr: 2.4, conversions: 98, cvr: 0.8, spend: 800000, roas: 367, cpa: 8163 },
      { channel: 'meta', impressions: 789012, clicks: 15780, ctr: 2.0, conversions: 67, cvr: 0.4, spend: 600000, roas: 389, cpa: 8955 },
      { channel: 'google', impressions: 234567, clicks: 11728, ctr: 5.0, conversions: 56, cvr: 0.5, spend: 400000, roas: 523, cpa: 7143 },
    ],
  },
};

// 기본값 설정 (기존 목업 데이터는 '코스모스 뷰티' 데이터로 사용)
export const MOCK_KPI = CLIENT_DATA_MAP['코스모스 뷰티'].kpi;
export const MOCK_CHANNELS = CLIENT_DATA_MAP['코스모스 뷰티'].channels;
export const MOCK_AI_INSIGHTS = CLIENT_DATA_MAP['코스모스 뷰티'].insights;
export const MOCK_CREATIVES = CLIENT_DATA_MAP['코스모스 뷰티'].creatives;
export const MOCK_HITL_ITEMS = CLIENT_DATA_MAP['코스모스 뷰티'].hitlItems;
export const MOCK_CHART_DATA = CLIENT_DATA_MAP['코스모스 뷰티'].chartData;
export const MOCK_FUNNEL_DATA = CLIENT_DATA_MAP['코스모스 뷰티'].funnelData;
export const MOCK_BUDGET_SIMULATION = CLIENT_DATA_MAP['코스모스 뷰티'].budgetSimulation;

// 전체 클라이언트 리스트 (포트폴리오 뷰용)
export const MOCK_CLIENTS: Client[] = [
  { id: 'c1', name: '코스모스 뷰티', ae: '최유진', roas: 385, roasVsTarget: 10, riskLevel: 'safe', riskScore: 1, contractExpiry: '26.06.30', revenue: 3360000, mer: 4.2, ltv: 115000, ltvChange: 11 },
  { id: 'c2', name: '홈플렉스', ae: '이서연', roas: 201, roasVsTarget: -29, riskLevel: 'danger', riskScore: 3, contractExpiry: '26.04.03', revenue: 2240000, mer: 2.1, ltv: 42000, ltvChange: -8 },
  { id: 'c3', name: '스타일워크', ae: '박민호', roas: 512, roasVsTarget: 28, riskLevel: 'safe', riskScore: 1, contractExpiry: '26.11.30', revenue: 3840000, mer: 5.8, ltv: 142000, ltvChange: 22 },
];

// 팀 멤버 데이터
export const MOCK_TEAM_MEMBERS: TeamMember[] = [
  { id: 'm1', name: '강지수', initials: '강지', clientCount: 3, clients: ['코스모스 뷰티', '홈플렉스', '스타일워크'], operatingBudget: 128000000, kpiAchieved: 3, kpiTotal: 3, savedHours: 134, hitlDelayed: 1 },
  { id: 'm2', name: '최유진', initials: '최유', clientCount: 1, clients: ['코스모스 뷰티'], operatingBudget: 30000000, kpiAchieved: 1, kpiTotal: 1, savedHours: 38, hitlDelayed: 0 },
  { id: 'm3', name: '이서연', initials: '이서', clientCount: 1, clients: ['홈플렉스'], operatingBudget: 50000000, kpiAchieved: 0, kpiTotal: 1, savedHours: 27, hitlDelayed: 3 },
  { id: 'm4', name: '박민호', initials: '박민', clientCount: 1, clients: ['스타일워크'], operatingBudget: 48000000, kpiAchieved: 1, kpiTotal: 1, savedHours: 42, hitlDelayed: 0 },
];

// Agent Chat mock data
export const MOCK_PIPELINE_STEPS: PipelineStep[] = [
  { id: 'cognitive', label: 'Cognitive', status: 'done' },
  { id: 'planning', label: 'Planning', status: 'done' },
  { id: 'execution', label: 'Execution', status: 'running' },
  { id: 'response', label: 'Response', status: 'pending' },
];

export const MOCK_TODOS: TodoItem[] = [];

export const MOCK_CHAT_MESSAGES: ChatMessage[] = [
  {
    id: 'msg-welcome',
    role: 'assistant',
    cardType: 'text',
    content: '안녕하세요! ADALLPIN Agent입니다.\n무엇을 도와드릴까요?',
    timestamp: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
  },
];

export const MOCK_TASKS: TaskItem[] = [];

export const MOCK_SYSTEM_LOGS: SystemLog[] = [
  { time: '10:29:12', message: 'Agent 초기화 완료', type: 'success' },
  { time: '10:29:13', message: 'WebSocket 연결 성공', type: 'info' },
  { time: '10:29:14', message: '데이터 수집 시작', type: 'info' },
];

// 헬퍼 함수: 클라이언트 이름으로 데이터 가져오기
export function getClientData(clientName: string): ClientData | null {
  return CLIENT_DATA_MAP[clientName] || null;
}

// 헬퍼 함수: 클라이언트별 HITL 아이템 가져오기
export function getClientHitlItems(clientName: string): HitlItem[] {
  const clientData = getClientData(clientName);
  return clientData ? clientData.hitlItems : [];
}

// 헬퍼 함수: 전체 HITL 아이템 가져오기 (모든 클라이언트)
export function getAllHitlItems(): HitlItem[] {
  return Object.values(CLIENT_DATA_MAP).flatMap(client => client.hitlItems);
}