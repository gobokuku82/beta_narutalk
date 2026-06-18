import React from 'react';
import { Brain, CheckCircle, AlertCircle, Target, Sparkles } from 'lucide-react';
import type { CognitiveOutput } from '../../../types';

interface CognitivePreviewProps {
  data: CognitiveOutput | null;
}

export const CognitivePreview: React.FC<CognitivePreviewProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="text-center py-8 text-sm text-gray-400">
        <Brain className="w-8 h-8 mx-auto mb-2 text-gray-300 animate-pulse" />
        <div>의도 분석 대기 중...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* AI 분석 요약 */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-3">
        <div className="flex items-start gap-2">
          <Sparkles className="w-4 h-4 text-blue-600 mt-0.5" />
          <div className="flex-1">
            <div className="text-xs font-semibold text-blue-700 mb-1">AI 이해도 분석</div>
            <div className="text-sm text-gray-700">
              "사용자가 <span className="font-semibold text-blue-600">{data.intentAnalysis?.action || '분석'}</span> 작업을
              <span className="font-semibold text-blue-600"> {data.intentAnalysis?.target || '캠페인'}</span>에 대해
              요청했습니다."
            </div>
          </div>
        </div>
      </div>

      {/* 원본 입력 */}
      <div>
        <div className="text-xs font-medium text-gray-500 mb-1">사용자 입력</div>
        <div className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm">
          {data.originalInput}
        </div>
      </div>

      {/* 오타 수정 */}
      {data.correctedInput && (
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1 flex items-center gap-1">
            <CheckCircle className="w-3 h-3 text-green-500" />
            표현 개선
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg px-3 py-2 text-sm">
            {data.correctedInput}
          </div>
        </div>
      )}

      {/* 의도 분석 결과 - 개선된 디자인 */}
      {data.intentAnalysis && (
        <div>
          <div className="text-xs font-medium text-gray-500 mb-2">세부 분석</div>
          <div className="bg-gray-50 rounded-lg p-3 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white rounded-lg p-2 border border-gray-200">
                <div className="text-xs text-gray-500 mb-1">작업 유형</div>
                <div className="flex items-center gap-1.5">
                  <Target className="w-3.5 h-3.5 text-blue-500" />
                  <span className="text-sm font-semibold text-gray-900">{data.intentAnalysis.action || '분석'}</span>
                </div>
              </div>
              <div className="bg-white rounded-lg p-2 border border-gray-200">
                <div className="text-xs text-gray-500 mb-1">대상</div>
                <div className="text-sm font-semibold text-gray-900">{data.intentAnalysis.target || '전체'}</div>
              </div>
            </div>

            {data.intentAnalysis.context && (
              <div className="bg-white rounded-lg p-2 border border-gray-200">
                <div className="text-xs text-gray-500 mb-1">맥락</div>
                <div className="text-sm text-gray-700">{data.intentAnalysis.context}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 감지된 키워드 */}
      {data.contextDetected && data.contextDetected.length > 0 && (
        <div>
          <div className="text-xs font-medium text-gray-500 mb-2">감지된 키워드</div>
          <div className="flex flex-wrap gap-1.5">
            {data.contextDetected.map((keyword, idx) => (
              <span key={idx} className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                {keyword}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 신뢰도 - 개선된 디자인 */}
      <div className="bg-gradient-to-r from-gray-50 to-white rounded-lg p-3 border border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-gray-600">분석 신뢰도</span>
          <span className={`text-sm font-bold ${
            data.confidence > 0.8 ? 'text-green-600' :
            data.confidence > 0.6 ? 'text-amber-600' : 'text-red-600'
          }`}>
            {(data.confidence * 100).toFixed(0)}%
          </span>
        </div>
        <div className="relative h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`absolute h-full transition-all duration-500 ease-out ${
              data.confidence > 0.8 ? 'bg-gradient-to-r from-green-400 to-green-600' :
              data.confidence > 0.6 ? 'bg-gradient-to-r from-amber-400 to-amber-600' :
              'bg-gradient-to-r from-red-400 to-red-600'
            }`}
            style={{ width: `${data.confidence * 100}%` }}
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs text-white font-medium drop-shadow-sm">
              {data.confidence > 0.8 ? '높음' : data.confidence > 0.6 ? '보통' : '낮음'}
            </span>
          </div>
        </div>
        {data.confidence < 0.8 && (
          <div className="flex items-start gap-1.5 mt-2">
            <AlertCircle className="w-3 h-3 text-amber-500 mt-0.5" />
            <p className="text-xs text-amber-600">
              명확한 지시를 위해 더 구체적인 정보를 입력해주세요
            </p>
          </div>
        )}
      </div>

      {/* AI 판단 근거 */}
      <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
        <div className="text-xs font-semibold text-blue-700 mb-1">💭 AI 사고 과정</div>
        <div className="text-xs text-gray-600 space-y-1">
          <div>1. 입력 문장에서 핵심 동사 "{data.intentAnalysis?.action}" 감지</div>
          <div>2. 대상 객체 "{data.intentAnalysis?.target}" 식별</div>
          <div>3. 광고/마케팅 도메인 컨텍스트 확인</div>
          <div>4. 유사 요청 패턴과 {(data.confidence * 100).toFixed(0)}% 일치</div>
        </div>
      </div>
    </div>
  );
};