import React, { useState } from 'react';
import { X, AlertCircle, TrendingUp, Clock, AlertTriangle, ChevronRight, RefreshCw } from 'lucide-react';
import { Creative } from '../../types';
import { Badge } from '../common/Badge';
import { ProgressBar } from '../common/ProgressBar';
import { useSelector } from 'react-redux';
import { RootState } from '../../app/store';

interface CreativeOptimizePanelProps {
  creative: Creative | null;
  onClose: () => void;
  onNavigateToAgent?: (context: any) => void;
  onNavigateToCost?: (channel: string) => void;
}

export const CreativeOptimizePanel: React.FC<CreativeOptimizePanelProps> = ({
  creative,
  onClose,
  onNavigateToAgent,
  onNavigateToCost
}) => {
  const { abTestResults } = useSelector((state: RootState) => state.creative);
  const [showToast, setShowToast] = useState(false);

  if (!creative) return null;

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-amber-600';
    return 'text-red-600';
  };

  const getScoreBarColor = (score: number): 'green' | 'amber' | 'red' => {
    if (score >= 80) return 'green';
    if (score >= 60) return 'amber';
    return 'red';
  };

  const getFrequencyStatus = () => {
    if (creative.frequency >= 3.5) {
      return { variant: 'danger' as const, text: '피로도 임계 초과' };
    }
    if (creative.frequency >= 2.5) {
      return { variant: 'warning' as const, text: '피로도 주의' };
    }
    return { variant: 'success' as const, text: '정상' };
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'winner': return '유지';
      case 'monitoring': return '주시';
      case 'replace': return '교체권고';
      default: return status;
    }
  };

  const handleActionButton = () => {
    if (!onNavigateToAgent || !onNavigateToCost) return;

    if (creative.status === 'winner') {
      // 유지 상태: 비용 최적화 탭으로 이동
      onNavigateToCost(creative.channel);
    } else if (creative.status === 'monitoring' || creative.status === 'replace') {
      // 주시/교체권고: 에이전트 탭으로 이동
      onNavigateToAgent({
        type: 'creative_generation',
        channel: creative.channel,
        spec: creative.spec,
        currentPerformance: {
          ctr: creative.ctr,
          cvr: creative.cvr,
          roas: creative.roas,
          frequency: creative.frequency
        }
      });
    }
  };

  const handleContinueTest = () => {
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  const frequencyStatus = getFrequencyStatus();

  // 해당 소재에 대한 A/B 테스트 여부 확인 (임시 로직)
  const hasAbTest = creative.status === 'winner' && abTestResults;

  return (
    <>
      <div className="w-80 bg-white h-full border-l border-gray-200 shadow-xl">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-lg">소재 최적화</h3>
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
          <p className="text-sm text-gray-600 mt-1">{creative.name}</p>
          <Badge variant={creative.status === 'winner' ? 'success' : creative.status === 'monitoring' ? 'warning' : 'danger'} size="sm">
            {getStatusLabel(creative.status)}
          </Badge>
        </div>

        <div className="p-4 space-y-6 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 200px)' }}>
          {/* 섹션 1: AI 품질 채점 */}
          <div>
            <h4 className="font-semibold text-sm mb-3 flex items-center gap-1">
              <TrendingUp className="w-4 h-4" />
              AI 품질 채점
            </h4>
            <div className="space-y-3">
              {[
                { label: '목적성(Sales)', value: creative.aiScore.sales },
                { label: '간결함(Short)', value: creative.aiScore.short },
                { label: '명확함(Clear)', value: creative.aiScore.clear },
                { label: '가시성(Visual)', value: creative.aiScore.visual },
                { label: '고객중심(Benefit)', value: creative.aiScore.benefit },
              ].map(item => (
                <div key={item.label}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">{item.label}</span>
                    <span className={`font-semibold ${getScoreColor(item.value)}`}>
                      {item.value}
                    </span>
                  </div>
                  <ProgressBar
                    value={item.value}
                    color={getScoreBarColor(item.value)}
                    height="sm"
                  />
                </div>
              ))}
            </div>

            {creative.aiScoreFeedback && (
              <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-sm text-amber-800 flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  {creative.aiScoreFeedback}
                </p>
              </div>
            )}
          </div>

          {/* 섹션 2: 수명 예측 */}
          <div>
            <h4 className="font-semibold text-sm mb-3 flex items-center gap-1">
              <Clock className="w-4 h-4" />
              수명 예측
            </h4>

            {creative.lifeExpectDays === 0 ? (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm font-medium text-red-800">교체 즉시 권고</p>
              </div>
            ) : creative.lifeExpectDays <= 3 ? (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-sm font-medium text-amber-800">곧 교체 필요</p>
              </div>
            ) : (
              <p className="text-sm font-medium text-blue-600">약 {creative.lifeExpectDays}일 유효</p>
            )}

            <div className="mt-2">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-gray-500">남은 수명</span>
                <span className="text-gray-700">{creative.lifeExpectDays} / 14일</span>
              </div>
              <ProgressBar
                value={(creative.lifeExpectDays / 14) * 100}
                color={creative.lifeExpectDays === 0 ? 'red' : creative.lifeExpectDays <= 3 ? 'amber' : 'blue'}
                height="sm"
              />
            </div>
          </div>

          {/* 섹션 3: 피로도 상태 */}
          <div>
            <h4 className="font-semibold text-sm mb-3 flex items-center gap-1">
              <AlertTriangle className="w-4 h-4" />
              피로도 상태
            </h4>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Frequency</p>
                <p className="text-2xl font-bold">{creative.frequency.toFixed(1)}</p>
              </div>
              <Badge variant={frequencyStatus.variant}>
                {frequencyStatus.text}
              </Badge>
            </div>

            <div className="mt-3">
              <ProgressBar
                value={(creative.frequency / 5) * 100}
                color={creative.frequency >= 3.5 ? 'red' : creative.frequency >= 2.5 ? 'amber' : 'green'}
              />
            </div>

            <p className="text-xs text-gray-500 mt-2">
              임계값 3.5 초과 시 CTR/CVR 급락 위험
            </p>
          </div>

          {/* A/B 테스트 섹션 (우측 패널 안으로 이동) */}
          <div>
            <h4 className="font-semibold text-sm mb-3 flex items-center gap-1">
              <RefreshCw className="w-4 h-4" />
              A/B 테스트
            </h4>

            {hasAbTest && abTestResults ? (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-2">
                  <div className={`p-3 rounded-lg text-xs ${abTestResults.winner === 'A' ? 'bg-success-bg border border-success' : 'bg-gray-50'}`}>
                    <h5 className="font-semibold mb-2">{abTestResults.variantA.name}</h5>
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span>CTR</span>
                        <span className="font-semibold">{abTestResults.variantA.ctr}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>ROAS</span>
                        <span className="font-semibold">{abTestResults.variantA.roas}%</span>
                      </div>
                    </div>
                  </div>
                  <div className={`p-3 rounded-lg text-xs ${abTestResults.winner === 'B' ? 'bg-success-bg border border-success' : 'bg-gray-50'}`}>
                    <h5 className="font-semibold mb-2">{abTestResults.variantB.name}</h5>
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span>CTR</span>
                        <span className="font-semibold">{abTestResults.variantB.ctr}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>ROAS</span>
                        <span className="font-semibold">{abTestResults.variantB.roas}%</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-2 bg-success-bg border border-success/30 rounded text-xs">
                  <p className="text-success-dark">
                    <strong>AI 판정:</strong> {abTestResults.winner}안 우위 · 신뢰도 {abTestResults.confidence}%
                  </p>
                </div>

                <button
                  onClick={handleContinueTest}
                  className="w-full py-2 bg-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-300"
                >
                  계속 테스트
                </button>
              </div>
            ) : (
              <div className="p-4 bg-gray-50 rounded-lg text-center">
                <p className="text-sm text-gray-600 mb-3">
                  진행 중인 A/B 테스트가 없습니다
                </p>
                <button className="px-4 py-2 bg-luminous-blue text-white rounded-lg text-sm font-medium hover:bg-amore-blue">
                  테스트 시작
                </button>
              </div>
            )}
          </div>

          {/* 성과 요약 */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-semibold text-sm mb-3">성과 요약</h4>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-500">CTR</span>
                <p className="font-semibold">{creative.ctr}%</p>
              </div>
              <div>
                <span className="text-gray-500">CVR</span>
                <p className="font-semibold">{creative.cvr}%</p>
              </div>
              <div>
                <span className="text-gray-500">ROAS</span>
                <p className="font-semibold">{creative.roas}%</p>
              </div>
              <div>
                <span className="text-gray-500">집행일</span>
                <p className="font-semibold">{creative.days}일</p>
              </div>
            </div>
          </div>

          {/* 하단 액션 버튼 */}
          <div className="pt-2">
            {creative.status === 'winner' ? (
              <button
                onClick={handleActionButton}
                className="w-full bg-green-600 text-white py-2.5 rounded-lg font-medium hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
              >
                예산 증액 제안
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : creative.status === 'monitoring' ? (
              <button
                onClick={handleActionButton}
                className="w-full bg-amber-600 text-white py-2.5 rounded-lg font-medium hover:bg-amber-700 transition-colors flex items-center justify-center gap-2"
              >
                새 소재 생성
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleActionButton}
                className="w-full bg-red-600 text-white py-2.5 rounded-lg font-medium hover:bg-red-700 transition-colors flex items-center justify-center gap-2"
              >
                새 소재 생성
                <ChevronRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 토스트 메시지 */}
      {showToast && (
        <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white px-6 py-3 rounded-lg shadow-lg z-50">
          A/B 테스트를 계속 진행합니다
        </div>
      )}
    </>
  );
};