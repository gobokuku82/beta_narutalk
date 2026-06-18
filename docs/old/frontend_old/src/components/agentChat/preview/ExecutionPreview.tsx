import React from 'react';
import { CheckCircle, Loader2, Circle, XCircle, Play, Activity, Zap } from 'lucide-react';
import type { ExecutionOutput, ExecutionStep } from '../../../types';

interface ExecutionPreviewProps {
  data: ExecutionOutput | null;
}

export const ExecutionPreview: React.FC<ExecutionPreviewProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="text-center py-8 text-sm text-gray-400">
        <Play className="w-8 h-8 mx-auto mb-2 text-gray-300 animate-pulse" />
        <div>실행 대기 중...</div>
      </div>
    );
  }

  const getStepIcon = (status: ExecutionStep['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'running':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Circle className="w-4 h-4 text-gray-300" />;
    }
  };

  const getStepBgColor = (status: ExecutionStep['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-300';
      case 'running':
        return 'bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-400 shadow-sm';
      case 'error':
        return 'bg-gradient-to-r from-red-50 to-pink-50 border-red-300';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const steps = data.steps ? Object.entries(data.steps) : [];
  const progress = data.totalSteps > 0 ? (steps.filter(([_, step]) => step.status === 'completed').length / data.totalSteps) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* AI 실행 상태 요약 */}
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-3">
        <div className="flex items-start gap-2">
          <Zap className="w-4 h-4 text-purple-600 mt-0.5" />
          <div className="flex-1">
            <div className="text-xs font-semibold text-purple-700 mb-1">실행 엔진 상태</div>
            <div className="text-sm text-gray-700">
              {progress === 100 ? '✅ 모든 작업이 성공적으로 완료되었습니다' :
               progress > 0 ? `⚡ ${Math.round(progress)}% 진행 중... 에이전트가 열심히 작업하고 있어요` :
               '🚀 실행을 시작합니다...'}
            </div>
          </div>
        </div>
      </div>

      {/* 진행률 */}
      <div>
        <div className="flex items-center justify-between text-xs font-medium text-gray-500 mb-2">
          <div className="flex items-center gap-1">
            <Activity className="w-3 h-3" />
            <span>전체 진행도</span>
          </div>
          <span className="font-bold text-gray-700">
            {steps.filter(([_, step]) => step.status === 'completed').length} / {data.totalSteps || 0} 완료
          </span>
        </div>
        <div className="relative h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="absolute h-full bg-gradient-to-r from-blue-400 to-purple-600 transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs text-white font-medium drop-shadow-sm">
              {Math.round(progress)}%
            </span>
          </div>
        </div>
      </div>

      {/* 단계별 실행 상황 */}
      <div className="space-y-3">
        <div className="text-xs font-medium text-gray-500 mb-2">작업 단계별 상세</div>
        {steps.map(([key, step], index) => (
          <div
            key={key}
            className={`border-2 rounded-lg p-3 transition-all duration-300 ${getStepBgColor(step.status)} ${
              step.status === 'running' ? 'scale-[1.02] animate-pulse' : ''
            }`}
          >
            <div className="flex items-start gap-3">
              {getStepIcon(step.status)}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-gray-400">STEP {index + 1}</span>
                  <div className="font-medium text-sm text-gray-900">{step.name || key}</div>
                </div>

                {/* 실행 시간 정보 - 타입에 없으므로 제거 또는 주석 처리 */}
                {/* {(step.startTime || step.endTime) && (
                  <div className="text-xs text-gray-500 mt-1">
                    {step.startTime && `시작: ${new Date(step.startTime).toLocaleTimeString('ko-KR')}`}
                    {step.endTime && ` → 완료: ${new Date(step.endTime).toLocaleTimeString('ko-KR')}`}
                  </div>
                )} */}

                {/* 결과 표시 */}
                {step.result && (
                  <div className="mt-2">
                    {typeof step.result === 'string' ? (
                      <div className="text-sm text-gray-700 bg-white/60 rounded px-2 py-1">
                        → {step.result}
                      </div>
                    ) : Array.isArray(step.result) ? (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {step.result.map((item, i) => (
                          <span key={i} className="px-2 py-0.5 bg-white/70 rounded text-xs">
                            {item}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <pre className="bg-white/70 p-2 rounded mt-1 overflow-x-auto text-xs">
                        {JSON.stringify(step.result, null, 2)}
                      </pre>
                    )}
                  </div>
                )}

                {/* 상태 메시지 */}
                {step.status === 'running' && (
                  <div className="flex items-center gap-1 mt-2">
                    <div className="w-1 h-1 bg-blue-500 rounded-full animate-ping" />
                    <span className="text-xs text-blue-600 font-medium">에이전트 작업 진행 중...</span>
                  </div>
                )}
                {step.status === 'error' && (
                  <div className="text-xs text-red-600 mt-2 font-medium">⚠️ 오류가 발생했습니다</div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 실행 메트릭 - 타입에 없으므로 제거 또는 주석 처리 */}
      {/* {data.metrics && (
        <div className="bg-gradient-to-r from-gray-50 to-white rounded-lg p-3 border border-gray-200">
          <div className="text-xs font-medium text-gray-500 mb-2">성능 지표</div>
          <div className="grid grid-cols-3 gap-2">
            <div className="text-center">
              <div className="text-xs text-gray-500">실행 시간</div>
              <div className="text-sm font-semibold text-gray-900">{data.metrics.executionTime}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500">리소스</div>
              <div className="text-sm font-semibold text-gray-900">{data.metrics.resourceUsage}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500">성공률</div>
              <div className="text-sm font-semibold text-green-600">{data.metrics.successRate}</div>
            </div>
          </div>
        </div>
      )} */}

      {/* AI 실행 로그 */}
      <div className="bg-gray-900 rounded-lg p-3">
        <div className="text-xs font-mono space-y-1">
          <div className="text-green-400">[SYSTEM] Execution pipeline active</div>
          {steps.map(([key, step]) => (
            <div key={key} className={
              step.status === 'completed' ? 'text-blue-400' :
              step.status === 'running' ? 'text-yellow-400 animate-pulse' :
              step.status === 'error' ? 'text-red-400' :
              'text-gray-500'
            }>
              [{new Date().toLocaleTimeString('ko-KR')}] {step.name || key}: {
                step.status === 'completed' ? 'SUCCESS' :
                step.status === 'running' ? 'PROCESSING...' :
                step.status === 'error' ? 'FAILED' :
                'PENDING'
              }
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};