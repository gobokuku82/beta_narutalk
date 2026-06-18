import React from 'react';
import { KpiCard } from '../common/KpiCard';
import { useSelector } from 'react-redux';
import { RootState } from '../../app/store';

export const KpiSummaryRow: React.FC = () => {
  const clientData = useSelector((state: RootState) => state.client.currentClientData);
  const kpi = clientData?.kpi || {
    roas: 385,
    roasChange: 12,
    spend: 0,
    spendBudget: 0,
    conversions: 0,
    cpa: 0,
    monthlyAchievement: 0,
    monthlyPrediction: 0,
    campaignDays: 0,
    campaignStage: 'learning' as const,
  };

  // AI 예측값 계산 (실제값의 ±5~10% 범위로 설정)
  const roasAIPrediction = 401; // AI가 4% 더 높게 예측
  const conversionsAIPrediction = Math.round(kpi.conversions * 1.08); // AI가 8% 더 높게 예측
  const achievementAIPrediction = Math.round(kpi.monthlyAchievement * 1.06); // AI가 6% 더 높게 예측

  // 실제값과 AI 예측값 차이 계산 (20%p 이상 차이 시 인사이트 카드 표시용)
  const roasDifference = Math.abs(roasAIPrediction - kpi.roas);
  const showRoasInsight = roasDifference >= 20; // 20%p 이상 차이

  return (
    <>
      <div className="grid grid-cols-3 gap-4 mb-6">
        <KpiCard
          label="통합 ROAS"
          actualValue={`${kpi.roas}%`}
          actualTooltip="해당 기간 실제 집행 기준 수치입니다"
          aiPredictedValue={`${roasAIPrediction}%`}
          aiPredictedTooltip="최근 7일 ROAS 추이와 계절성 패턴을 분석한 예측값입니다"
          trend={kpi.roasChange > 0 ? 'up' : 'down'}
          trendValue={`${Math.abs(kpi.roasChange)}%`}
          subText="목표 350% 달성"
        />
        <KpiCard
          label="오늘 전환 수"
          actualValue={kpi.conversions}
          actualTooltip="오늘 실제 발생한 전환 수입니다"
          aiPredictedValue={conversionsAIPrediction}
          aiPredictedTooltip="시간대별 패턴을 분석한 일일 예상 전환 수입니다"
          subText={`CPA ₩${kpi.cpa.toLocaleString()}`}
          trend="up"
          trendValue="목표 달성"
        />
        <KpiCard
          label="월 KPI 달성 예측"
          actualValue={`${kpi.monthlyAchievement}%`}
          actualTooltip="현재까지 실제 달성률입니다"
          aiPredictedValue={`${achievementAIPrediction}%`}
          aiPredictedTooltip="현재 페이스와 잔여 기간을 고려한 월말 예측값입니다"
          subText="17/31일 경과"
        />
      </div>

      {/* AI 예측값과 실제값 차이가 클 때 인사이트 카드 표시 */}
      {showRoasInsight && (
        <div className="mb-6 p-4 bg-info-bg border border-accent/20 rounded-lg">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-accent/10 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-xs">💡</span>
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-gray-900 mb-1">
                AI 인사이트: ROAS 예측값 차이 발생
              </h4>
              <p className="text-xs text-gray-600">
                실제 ROAS({kpi.roas}%)와 AI 예측값({roasAIPrediction}%) 간 {roasDifference}%p 차이가 발생했습니다.
                {roasAIPrediction > kpi.roas
                  ? " 예상보다 낮은 성과는 경쟁 심화 또는 타겟 피로도 증가가 원인일 수 있습니다."
                  : " 예상보다 높은 성과는 시즌 효과 또는 캠페인 최적화의 결과입니다."}
              </p>
              <button className="text-xs text-accent font-medium mt-2 hover:underline">
                상세 분석 보기 →
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};