import React, { useState } from 'react';
import { TrendingUp, TrendingDown, Minus, Info } from 'lucide-react';
import { AiTag } from './AiTag';

interface KpiCardProps {
  label: string;
  value?: string | number;  // Optional로 변경
  subText?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  aiNote?: string;
  aiTooltip?: string;
  className?: string;
  // 새로운 props: 실제값과 AI 예측값 분리
  actualValue?: string | number;
  actualTooltip?: string;
  aiPredictedValue?: string | number;
  aiPredictedTooltip?: string;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  label,
  value,
  subText,
  trend,
  trendValue,
  aiNote,
  aiTooltip,
  className,
  actualValue,
  actualTooltip,
  aiPredictedValue,
  aiPredictedTooltip,
}) => {
  const [showActualTooltip, setShowActualTooltip] = useState(false);
  const [showPredictedTooltip, setShowPredictedTooltip] = useState(false);

  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendColor = trend === 'up' ? 'text-success' : trend === 'down' ? 'text-danger' : 'text-muted-foreground';

  // 새로운 레이아웃: actualValue가 있으면 분리 표시
  if (actualValue !== undefined) {
    return (
      <div className={`bg-white rounded-lg shadow p-4 border border-gray-200 ${className || ''}`}>
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm text-gray-600">{label}</p>
          {aiPredictedValue && <AiTag tooltip="AI 예측값 포함" />}
        </div>

        {/* 실제값 (크게 표시) */}
        <div className="flex items-baseline gap-2 mb-1">
          <h3 className="text-2xl font-bold text-gray-900">
            {typeof actualValue === 'number' ? actualValue.toLocaleString() : actualValue}
          </h3>
          {trend && trendValue && (
            <div className={`flex items-center ${trendColor}`}>
              <TrendIcon className="w-4 h-4" />
              <span className="text-sm font-medium ml-1">{trendValue}</span>
            </div>
          )}
          {actualTooltip && (
            <div className="relative">
              <Info
                className="w-4 h-4 text-gray-400 cursor-help"
                onMouseEnter={() => setShowActualTooltip(true)}
                onMouseLeave={() => setShowActualTooltip(false)}
              />
              {showActualTooltip && (
                <div className="absolute left-0 top-6 z-50 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg">
                  {actualTooltip}
                </div>
              )}
            </div>
          )}
        </div>

        {/* AI 예측값 (작게 표시) */}
        {aiPredictedValue && (
          <div className="flex items-center gap-1 mb-1">
            <span className="text-sm text-gray-500">AI 예측</span>
            <span className="text-base font-semibold text-gray-600">
              {typeof aiPredictedValue === 'number' ? aiPredictedValue.toLocaleString() : aiPredictedValue}
            </span>
            {aiPredictedTooltip && (
              <div className="relative">
                <Info
                  className="w-3.5 h-3.5 text-gray-400 cursor-help"
                  onMouseEnter={() => setShowPredictedTooltip(true)}
                  onMouseLeave={() => setShowPredictedTooltip(false)}
                />
                {showPredictedTooltip && (
                  <div className="absolute left-0 top-5 z-50 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg">
                    {aiPredictedTooltip}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {subText && <p className="text-sm text-muted-foreground">{subText}</p>}
        {aiNote && <p className="text-xs text-luminous-blue mt-2">{aiNote}</p>}
      </div>
    );
  }

  // 기존 레이아웃 (하위 호환성)
  return (
    <div className={`bg-white rounded-lg shadow p-4 border border-gray-200 ${className || ''}`}>
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm text-gray-600">{label}</p>
        {aiNote && <AiTag tooltip={aiTooltip} />}
      </div>
      <div className="flex items-baseline gap-2 mb-1">
        <h3 className="text-2xl font-bold text-gray-900">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </h3>
        {trend && trendValue && (
          <div className={`flex items-center ${trendColor}`}>
            <TrendIcon className="w-4 h-4" />
            <span className="text-sm font-medium ml-1">{trendValue}</span>
          </div>
        )}
      </div>
      {subText && <p className="text-sm text-muted-foreground">{subText}</p>}
      {aiNote && <p className="text-xs text-luminous-blue mt-2">{aiNote}</p>}
    </div>
  );
};