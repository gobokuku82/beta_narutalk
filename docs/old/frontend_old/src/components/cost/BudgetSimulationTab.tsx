import React, { useState, useEffect, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../app/store';
import { TrendingUp, TrendingDown, Target, RotateCcw, Save, FolderOpen, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { setAgentContext, setInitialMessage } from '../../features/agentChat/agentChatSlice';

interface Allocation {
  channel: string;
  currentPct: number;
  simulatedPct: number;
}

interface Predicted {
  roas: number;
  roasDelta: number;
  conversions: number;
  conversionsDelta: number;
  cpa: number;
  cpaDelta: number;
}

interface SavedScenario {
  id: string;
  name: string;
  allocations: Allocation[];
  predicted: Predicted;
  createdAt: string;
}

export const BudgetSimulationTab: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const clientData = useSelector((state: RootState) => state.client.currentClientData);
  const initialAllocationsRef = useRef<Allocation[]>([]);
  const initialPredictedRef = useRef<Predicted | null>(null);

  const budgetSimulation = clientData?.budgetSimulation || {
    allocations: [],
    predicted: {
      roas: 0,
      roasDelta: 0,
      conversions: 0,
      conversionsDelta: 0,
      cpa: 0,
      cpaDelta: 0,
    }
  };

  const [allocations, setAllocations] = useState<Allocation[]>(budgetSimulation.allocations);
  const [predicted, setPredicted] = useState<Predicted>(budgetSimulation.predicted);
  const [isDragging, setIsDragging] = useState(false);
  const [dragChannel, setDragChannel] = useState<string | null>(null);
  const [totalExceeded, setTotalExceeded] = useState(false);
  const [showScenarioModal, setShowScenarioModal] = useState(false);
  const [scenarioName, setScenarioName] = useState('');
  const [savedScenarios, setSavedScenarios] = useState<SavedScenario[]>([]);
  const [showLoadModal, setShowLoadModal] = useState(false);

  // 초기값 저장
  useEffect(() => {
    if (clientData?.budgetSimulation) {
      setAllocations(clientData.budgetSimulation.allocations);
      setPredicted(clientData.budgetSimulation.predicted);

      // 초기값 저장 (초기화 기능용)
      if (initialAllocationsRef.current.length === 0) {
        initialAllocationsRef.current = clientData.budgetSimulation.allocations;
        initialPredictedRef.current = clientData.budgetSimulation.predicted;
      }
    }
  }, [clientData]);

  const handleSliderChange = (channel: string, value: number) => {
    // 소수점 1자리로 반올림
    const roundedValue = Math.round(value * 10) / 10;

    const newAllocations = allocations.map(a =>
      a.channel === channel ? { ...a, simulatedPct: roundedValue } : a
    );

    // 합계 계산 및 100% 초과 체크
    const total = newAllocations.reduce((sum: number, a: Allocation) => sum + a.simulatedPct, 0);

    // 100% 초과 허용하되 경고 표시
    setTotalExceeded(total > 100);

    setAllocations(newAllocations);

    // 예측값 재계산 (시뮬레이션)
    const googleChange = newAllocations.find(a => a.channel === 'google')!.simulatedPct -
                         budgetSimulation.allocations.find((a: any) => a.channel === 'google')!.currentPct;
    const metaChange = newAllocations.find(a => a.channel === 'meta')!.simulatedPct -
                       budgetSimulation.allocations.find((a: any) => a.channel === 'meta')!.currentPct;

    setPredicted({
      roas: Math.round((4.2 + (googleChange * 0.02) + (metaChange * 0.015)) * 10) / 10,
      roasDelta: Math.round((0.3 + (googleChange * 0.02) + (metaChange * 0.015)) * 10) / 10,
      conversions: 847 + Math.round(googleChange * 3) + Math.round(metaChange * 2),
      conversionsDelta: 73 + Math.round(googleChange * 3) + Math.round(metaChange * 2),
      cpa: 13200 - Math.round(googleChange * 50) - Math.round(metaChange * 30),
      cpaDelta: -1100 - Math.round(googleChange * 50) - Math.round(metaChange * 30),
    });
  };

  const getChannelColor = (channel: string) => {
    switch (channel) {
      case 'naver': return 'text-success-dark';
      case 'kakao': return 'text-yellow-600';
      case 'meta': return 'text-accent';
      case 'google': return 'text-accent';
      default: return 'text-gray-600';
    }
  };

  const handleApplySimulation = () => {
    // 승인 요청 버튼 클릭 시 에이전트 탭으로 이동 + 컨텍스트 전달
    const context = {
      type: 'budget_approval',
      simulation: {
        allocations,
        predicted,
        totalPercent: allocations.reduce((sum: number, a: Allocation) => sum + a.simulatedPct, 0)
      }
    };

    // 시뮬레이션 결과를 포함한 메시지 생성
    const channelDetails = allocations.map(a => {
      const change = a.simulatedPct - a.currentPct;
      const channelName = a.channel === 'naver' ? '네이버' :
                          a.channel === 'kakao' ? '카카오' :
                          a.channel === 'meta' ? '메타' : '구글';
      return `- ${channelName}: ${a.currentPct.toFixed(1)}% → ${a.simulatedPct.toFixed(1)}% (${change > 0 ? '+' : ''}${change.toFixed(1)}%)`;
    }).join('\n');

    const message = `예산 재배치 시뮬레이션 결과를 검토하고 승인을 요청합니다.

시뮬레이션 내용:
${channelDetails}

예상 효과:
- ROAS: ${predicted.roas.toFixed(1)}x (${predicted.roasDelta > 0 ? '+' : ''}${predicted.roasDelta.toFixed(1)}x)
- 전환수: ${predicted.conversions}건 (${predicted.conversionsDelta > 0 ? '+' : ''}${predicted.conversionsDelta}건)
- CPA: ₩${predicted.cpa.toLocaleString()} (${predicted.cpaDelta > 0 ? '+' : ''}₩${predicted.cpaDelta.toLocaleString()})

이 예산 재배치안을 적용하고 싶습니다. 검토 후 승인 처리를 진행해주세요.`;

    dispatch(setAgentContext(context));
    dispatch(setInitialMessage(message));
    navigate('/agent');
  };

  const handleAIBudgetReallocation = () => {
    // AI 예산 재배분 버튼 클릭 시 에이전트 탭으로 이동 + 컨텍스트 전달
    const context = {
      type: 'ai_budget_reallocation',
      currentAllocation: allocations.map(a => ({ channel: a.channel, percent: a.currentPct })),
      aiRecommendation: allocations.map(a => ({ channel: a.channel, percent: a.simulatedPct }))
    };

    const message = `현재 예산 배분을 AI로 최적화하고 싶습니다.
각 채널의 성과를 분석하고 최적의 예산 재배분안을 제시해주세요.`;

    dispatch(setAgentContext(context));
    dispatch(setInitialMessage(message));
    navigate('/agent');
  };

  const handleReset = () => {
    // 초기화 버튼: 페이지 최초 로드 시점 값으로 즉시 복귀
    if (initialAllocationsRef.current.length > 0 && initialPredictedRef.current) {
      setAllocations(initialAllocationsRef.current);
      setPredicted(initialPredictedRef.current);
      setTotalExceeded(false);
    }
  };

  const handleSaveScenario = () => {
    if (!scenarioName.trim()) return;

    const newScenario: SavedScenario = {
      id: Date.now().toString(),
      name: scenarioName,
      allocations: allocations,
      predicted: predicted,
      createdAt: new Date().toISOString()
    };

    // 로컬 스토리지에 저장 (추후 Supabase 연동)
    const scenarios = [...savedScenarios, newScenario];
    setSavedScenarios(scenarios);
    localStorage.setItem('budgetScenarios', JSON.stringify(scenarios));

    setShowScenarioModal(false);
    setScenarioName('');
  };

  const handleLoadScenario = (scenario: SavedScenario) => {
    setAllocations(scenario.allocations);
    setPredicted(scenario.predicted);

    const total = scenario.allocations.reduce((sum: number, a: Allocation) => sum + a.simulatedPct, 0);
    setTotalExceeded(total > 100);

    setShowLoadModal(false);
  };

  // 저장된 시나리오 불러오기
  useEffect(() => {
    const stored = localStorage.getItem('budgetScenarios');
    if (stored) {
      setSavedScenarios(JSON.parse(stored));
    }
  }, []);

  return (
    <div className="space-y-6">
      {/* 2열 레이아웃: 왼쪽 슬라이더, 오른쪽 예측 지표 */}
      <div className="flex gap-6">
        {/* 왼쪽: 채널별 슬라이더 */}
        <div className="flex-1 space-y-4">
          {allocations.map(allocation => {
            const change = Math.round((allocation.simulatedPct - allocation.currentPct) * 10) / 10;
            return (
              <div key={allocation.channel} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className={`font-medium capitalize ${getChannelColor(allocation.channel)}`}>
                    {allocation.channel === 'naver' ? '네이버' :
                     allocation.channel === 'kakao' ? '카카오' :
                     allocation.channel === 'meta' ? '메타' : '구글'}
                  </span>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-gray-500">{allocation.currentPct.toFixed(1)}%</span>
                    <span className="text-sm">→</span>
                    <span className={`text-sm font-semibold ${
                      change > 0 ? 'text-success-dark' : change < 0 ? 'text-danger' : 'text-gray-600'
                    }`}>
                      {allocation.simulatedPct.toFixed(1)}%
                    </span>
                    {change !== 0 && (
                      <span className={`text-xs ${change > 0 ? 'text-success-dark' : 'text-danger'}`}>
                        ({change > 0 ? '+' : ''}{change.toFixed(1)}%)
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="0"
                    max="50"
                    step="0.1"
                    value={allocation.simulatedPct}
                    onChange={(e) => handleSliderChange(allocation.channel, Number(e.target.value))}
                    className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    style={{
                      background: `linear-gradient(to right, #4a90d9 0%, #4a90d9 ${allocation.simulatedPct * 2}%, #E5E7EB ${allocation.simulatedPct * 2}%, #E5E7EB 100%)`
                    }}
                  />
                  <span className="text-sm font-medium w-12 text-right">
                    {allocation.simulatedPct.toFixed(1)}%
                  </span>
                </div>
              </div>
            );
          })}

          {/* 예산 합계 */}
          <div className={`p-3 rounded-lg ${totalExceeded ? 'bg-red-50 border border-red-200' : 'bg-gray-50'}`}>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">예산 합계</span>
              <span className={`font-semibold ${
                Math.round(allocations.reduce((sum: number, a: Allocation) => sum + a.simulatedPct, 0) * 10) / 10 === 100
                  ? 'text-success'
                  : 'text-danger'
              }`}>
                {(allocations.reduce((sum: number, a: Allocation) => sum + a.simulatedPct, 0)).toFixed(1)}%
              </span>
            </div>
            {totalExceeded && (
              <div className="mt-2 flex items-start gap-1">
                <AlertCircle className="w-4 h-4 text-danger mt-0.5" />
                <p className="text-xs text-danger">예산 합계가 100%를 초과했습니다. 승인 요청이 불가능합니다.</p>
              </div>
            )}
          </div>

          {/* 시나리오 버튼 */}
          <div className="flex gap-2 mt-4">
            <button
              onClick={() => setShowScenarioModal(true)}
              className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 flex items-center justify-center gap-1"
            >
              <Save className="w-4 h-4" />
              저장
            </button>
            <button
              onClick={() => setShowLoadModal(true)}
              className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 flex items-center justify-center gap-1"
            >
              <FolderOpen className="w-4 h-4" />
              불러오기
            </button>
          </div>
        </div>

        {/* 오른쪽: 예측 지표 + 버튼 */}
        <div className="w-80 space-y-3">
          {/* 예상 ROAS */}
          <div className="p-3 bg-white border border-gray-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-accent" />
                <h4 className="font-medium text-sm">예상 ROAS</h4>
              </div>
              <div className="text-right">
                <p className="text-xl font-bold">{predicted.roas.toFixed(1)}x</p>
                <p className={`text-xs ${predicted.roasDelta > 0 ? 'text-success-dark' : 'text-danger'}`}>
                  {predicted.roasDelta > 0 ? '+' : ''}{predicted.roasDelta.toFixed(1)}x
                </p>
              </div>
            </div>
          </div>

          {/* 예상 전환수 */}
          <div className="p-3 bg-white border border-gray-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-accent" />
                <h4 className="font-medium text-sm">예상 전환수</h4>
              </div>
              <div className="text-right">
                <p className="text-xl font-bold">{predicted.conversions}건</p>
                <p className={`text-xs ${predicted.conversionsDelta > 0 ? 'text-success-dark' : 'text-danger'}`}>
                  {predicted.conversionsDelta > 0 ? '+' : ''}{predicted.conversionsDelta}건
                </p>
              </div>
            </div>
          </div>

          {/* 예상 CPA */}
          <div className="p-3 bg-white border border-gray-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-accent" />
                <h4 className="font-medium text-sm">예상 CPA</h4>
              </div>
              <div className="text-right">
                <p className="text-xl font-bold">₩{predicted.cpa.toLocaleString()}</p>
                <p className={`text-xs ${predicted.cpaDelta < 0 ? 'text-success-dark' : 'text-danger'}`}>
                  {predicted.cpaDelta > 0 ? '+' : ''}₩{predicted.cpaDelta.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          {/* 액션 버튼 */}
          <div className="flex gap-2">
            <button
              onClick={handleApplySimulation}
              disabled={totalExceeded}
              className={`flex-1 px-4 py-2.5 rounded-lg font-medium transition-colors text-sm ${
                totalExceeded
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-accent text-white hover:bg-accent/90'
              }`}
            >
              승인 요청
            </button>
            <button
              onClick={handleReset}
              className="flex-1 px-4 py-2.5 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition-colors text-sm flex items-center justify-center gap-1"
            >
              <RotateCcw className="w-4 h-4" />
              초기화
            </button>
          </div>

          {/* AI 예산 재배분 */}
          <button
            onClick={handleAIBudgetReallocation}
            className="w-full px-4 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors text-sm"
          >
            AI 예산 재배분
          </button>
        </div>
      </div>

      {/* AI 권고 사항 */}
      <div className="p-4 bg-info-bg border border-info rounded-lg">
        <p className="text-sm text-accent">
          <strong>AI 권고:</strong> 구글과 메타 채널의 예산을 증액하고 네이버와 카카오를 감축하면
          ROAS {predicted.roasDelta.toFixed(1)}x 개선과 전환 {predicted.conversionsDelta}건 증가가 예상됩니다.
        </p>
      </div>

      {/* 시나리오 저장 모달 */}
      {showScenarioModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold mb-4">시나리오 저장</h3>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">시나리오 이름</label>
              <input
                type="text"
                value={scenarioName}
                onChange={(e) => setScenarioName(e.target.value)}
                placeholder="예: 구글/메타 집중 전략"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setShowScenarioModal(false);
                  setScenarioName('');
                }}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300"
              >
                취소
              </button>
              <button
                onClick={handleSaveScenario}
                disabled={!scenarioName.trim()}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                저장
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 시나리오 불러오기 모달 */}
      {showLoadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold">저장된 시나리오</h3>
            </div>
            <div className="max-h-96 overflow-y-auto">
              {savedScenarios.length === 0 ? (
                <div className="p-6 text-center text-gray-500">
                  저장된 시나리오가 없습니다
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {savedScenarios.map(scenario => (
                    <div
                      key={scenario.id}
                      className="p-4 hover:bg-gray-50 cursor-pointer"
                      onClick={() => handleLoadScenario(scenario)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-gray-900">{scenario.name}</p>
                          <p className="text-sm text-gray-500 mt-1">
                            {new Date(scenario.createdAt).toLocaleDateString('ko-KR')} ·
                            ROAS {scenario.predicted.roas.toFixed(1)}x
                          </p>
                        </div>
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="p-4 border-t border-gray-200">
              <button
                onClick={() => setShowLoadModal(false)}
                className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};