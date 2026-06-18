import React from 'react';
import { Users, Clock, AlertCircle, GitBranch, Cpu, Grid3x3, ArrowRight } from 'lucide-react';
import type { PlanningOutput } from '../../../types';

interface PlanningPreviewProps {
  data: PlanningOutput | null;
}

export const PlanningPreview: React.FC<PlanningPreviewProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="text-center py-8 text-sm text-gray-400">
        <GitBranch className="w-8 h-8 mx-auto mb-2 text-gray-300 animate-pulse" />
        <div>계획 수립 대기 중...</div>
      </div>
    );
  }

  const getExecutionTypeIcon = (type: string) => {
    switch (type) {
      case 'sequential':
        return <ArrowRight className="w-3 h-3" />;
      case 'parallel':
        return <Grid3x3 className="w-3 h-3" />;
      case 'swarm':
        return <Cpu className="w-3 h-3" />;
      default:
        return <ArrowRight className="w-3 h-3" />;
    }
  };

  const getExecutionTypeColor = (type: string) => {
    switch (type) {
      case 'sequential':
        return 'bg-blue-100 text-blue-700 border-blue-300';
      case 'parallel':
        return 'bg-green-100 text-green-700 border-green-300';
      case 'swarm':
        return 'bg-purple-100 text-purple-700 border-purple-300';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  const getExecutionTypeLabel = (type: string) => {
    switch (type) {
      case 'sequential':
        return '순차 실행';
      case 'parallel':
        return '병렬 실행';
      case 'swarm':
        return '스웜 실행';
      default:
        return type;
    }
  };

  const getAgentIcon = (agent: string) => {
    if (agent.includes('분석')) return '📊';
    if (agent.includes('최적화')) return '⚡';
    if (agent.includes('보고')) return '📄';
    if (agent.includes('생성')) return '🎨';
    if (agent.includes('검증')) return '✅';
    return '🤖';
  };

  return (
    <div className="space-y-4">
      {/* AI 전략 요약 */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-3">
        <div className="text-xs font-semibold text-indigo-700 mb-1">🧠 AI 실행 전략</div>
        <div className="text-sm text-gray-700">
          {data.selectedAgents?.length || 0}개의 에이전트를
          <span className="font-semibold text-indigo-600"> {getExecutionTypeLabel(data.executionPlan?.type || 'sequential')}</span>
          로 실행하여 최적의 결과를 도출합니다.
        </div>
      </div>

      {/* 선택된 에이전트 - 개선된 디자인 */}
      {data.selectedAgents && data.selectedAgents.length > 0 && (
        <div>
          <div className="text-xs font-medium text-gray-500 mb-2 flex items-center gap-1">
            <Users className="w-3 h-3" />
            활성화된 AI 에이전트 ({data.selectedAgents.length})
          </div>
          <div className="grid grid-cols-2 gap-2">
            {data.selectedAgents.map((agent, index) => (
              <div
                key={index}
                className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
              >
                <span className="text-lg">{getAgentIcon(agent)}</span>
                <span className="text-sm font-medium text-gray-700">{agent}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 실행 계획 */}
      {data.executionPlan && (
        <div>
          <div className="text-xs font-medium text-gray-500 mb-2 flex items-center justify-between">
            <span>실행 플로우</span>
            <div className={`px-2 py-0.5 text-xs font-medium rounded border flex items-center gap-1 ${
              getExecutionTypeColor(data.executionPlan.type)
            }`}>
              {getExecutionTypeIcon(data.executionPlan.type)}
              {getExecutionTypeLabel(data.executionPlan.type)}
            </div>
          </div>
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-lg p-3">
            <div className="space-y-2">
              {data.executionPlan.steps && data.executionPlan.steps.map((step, index) => (
                <div key={index} className="flex items-start gap-3">
                  <div className="relative">
                    <span className="w-6 h-6 bg-gradient-to-br from-green-500 to-green-600 text-white text-xs rounded-full flex items-center justify-center flex-shrink-0 font-bold shadow-sm">
                      {index + 1}
                    </span>
                    {index < data.executionPlan.steps.length - 1 && (
                      <div className="absolute top-6 left-3 w-0.5 h-4 bg-green-300" />
                    )}
                  </div>
                  <div className="flex-1">
                    <span className="text-sm text-gray-700 font-medium">{step}</span>
                    {index === 0 && <span className="text-xs text-green-600 ml-2">시작</span>}
                    {index === data.executionPlan.steps.length - 1 && <span className="text-xs text-blue-600 ml-2">완료</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* HITL 필요 단계 */}
      {data.hitlRequired && data.hitlRequired.length > 0 && (
        <div>
          <div className="text-xs font-medium text-gray-500 mb-2 flex items-center gap-1">
            <AlertCircle className="w-3 h-3 text-amber-500" />
            사용자 승인 필요
          </div>
          <div className="bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-300 rounded-lg p-3">
            <div className="space-y-2">
              {data.hitlRequired.map((step, index) => (
                <div key={index} className="flex items-center gap-2">
                  <div className="w-1 h-1 bg-amber-500 rounded-full" />
                  <span className="text-sm text-amber-800 font-medium">{step}</span>
                  <span className="text-xs text-amber-600 ml-auto">대기 예정</span>
                </div>
              ))}
            </div>
            <div className="mt-2 pt-2 border-t border-amber-200">
              <p className="text-xs text-amber-700">
                💡 승인이 필요한 시점에 자동으로 실행을 일시정지하고 알림을 보냅니다
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 예상 소요시간 및 리소스 */}
      <div className="bg-gradient-to-r from-gray-50 to-white rounded-lg p-3 border border-gray-200">
        <div className="grid grid-cols-2 gap-3">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-gray-500" />
            <div>
              <div className="text-xs text-gray-500">예상 시간</div>
              <div className="text-sm font-semibold text-gray-900">{data.estimatedTime}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-gray-500" />
            <div>
              <div className="text-xs text-gray-500">리소스 사용</div>
              <div className="text-sm font-semibold text-gray-900">보통</div>
            </div>
          </div>
        </div>
      </div>

      {/* AI 의사결정 근거 */}
      <div className="bg-indigo-50 rounded-lg p-3 border border-indigo-200">
        <div className="text-xs font-semibold text-indigo-700 mb-1">🎯 AI 의사결정</div>
        <div className="text-xs text-gray-600 space-y-1">
          <div>• 요청 복잡도 분석: 중간 (3개 이상 작업)</div>
          <div>• 데이터 의존성: {data.executionPlan?.type === 'sequential' ? '순차적 처리 필요' : '독립 실행 가능'}</div>
          <div>• 최적 에이전트 조합으로 {data.selectedAgents?.length || 0}개 선택</div>
          <div>• 예상 성공률: 95%</div>
        </div>
      </div>
    </div>
  );
};