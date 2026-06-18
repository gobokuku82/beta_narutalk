import React from 'react';
import { AlertCircle, TrendingUp, Target } from 'lucide-react';

interface CampaignStageBannerProps {
  stage: 'learning' | 'mature' | 'optimizing';
  campaignDays: number;
}

const STAGE_CONFIG = {
  learning: {
    color: 'amber',
    label: '학습기',
    range: '1~7일',
    message: '성과 지표는 7~14일 이후 안정화됩니다. 지금은 예산 소진율과 노출수를 중심으로 확인하세요.',
    highlightMetrics: ['budgetRate', 'impressions'],
    deferMetrics: ['roas', 'cpa', 'conversions'],
    icon: AlertCircle,
  },
  mature: {
    color: 'blue',
    label: '성숙기',
    range: '8~21일',
    message: 'ROAS와 CTR이 안정화되었습니다. 소재 최적화와 타겟 세분화를 집중하세요.',
    highlightMetrics: ['roas', 'ctr'],
    deferMetrics: [],
    icon: TrendingUp,
  },
  optimizing: {
    color: 'green',
    label: '최적화기',
    range: '22일+',
    message: '캠페인이 최적화 단계입니다. CPA 개선과 예산 재배분 전략을 실행하세요.',
    highlightMetrics: ['cpa', 'roas'],
    deferMetrics: [],
    icon: Target,
  },
};

export const CampaignStageBanner: React.FC<CampaignStageBannerProps> = ({
  stage,
  campaignDays,
}) => {
  const config = STAGE_CONFIG[stage];
  const Icon = config.icon;

  const getColorClasses = () => {
    switch (config.color) {
      case 'amber':
        return 'bg-amber-50 border-amber-200 text-amber-800';
      case 'blue':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      case 'green':
        return 'bg-green-50 border-green-200 text-green-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const getDotColorClasses = () => {
    switch (config.color) {
      case 'amber':
        return 'bg-amber-500';
      case 'blue':
        return 'bg-blue-500';
      case 'green':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className={`mb-6 p-4 rounded-lg border ${getColorClasses()}`}>
      <div className="flex items-start gap-3 mb-3">
        <Icon className="w-5 h-5 mt-0.5" />
        <div className="flex-1">
          <h3 className="font-semibold text-sm mb-1">
            현재 {config.label} (캠페인 시작 {campaignDays}일차)
          </h3>
          <p className="text-sm">{config.message}</p>
        </div>
      </div>

      {/* 진행 단계 표시 */}
      <div className="flex items-center gap-2 mt-4 pt-3 border-t border-current/10">
        <div className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full ${stage === 'learning' ? getDotColorClasses() : 'bg-gray-300'}`} />
          <span className={`text-xs font-medium ${stage === 'learning' ? '' : 'text-gray-500'}`}>
            학습기
          </span>
        </div>
        <div className="flex-1 h-px bg-current/20" />
        <div className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full ${stage === 'mature' ? getDotColorClasses() : 'bg-gray-300'}`} />
          <span className={`text-xs font-medium ${stage === 'mature' ? '' : 'text-gray-500'}`}>
            성숙기
          </span>
        </div>
        <div className="flex-1 h-px bg-current/20" />
        <div className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full ${stage === 'optimizing' ? getDotColorClasses() : 'bg-gray-300'}`} />
          <span className={`text-xs font-medium ${stage === 'optimizing' ? '' : 'text-gray-500'}`}>
            최적화기
          </span>
        </div>
      </div>

      {/* 강조 지표 안내 */}
      {config.highlightMetrics.length > 0 && (
        <div className="mt-3 text-xs">
          <span className="font-medium">현재 주요 지표:</span>
          <span className="ml-2">
            {config.highlightMetrics.map(metric => {
              const labels: Record<string, string> = {
                budgetRate: '예산 소진율',
                impressions: '노출수',
                roas: 'ROAS',
                ctr: 'CTR',
                cpa: 'CPA',
                conversions: '전환수',
              };
              return labels[metric] || metric;
            }).join(', ')}
          </span>
        </div>
      )}
    </div>
  );
};