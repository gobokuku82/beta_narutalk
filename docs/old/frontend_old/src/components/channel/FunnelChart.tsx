import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../app/store';
import { FunnelStageData } from '../../types';

interface FunnelChartProps {
  selectedChannel?: 'all' | 'naver' | 'meta' | 'google' | 'kakao';
}

const FunnelChart: React.FC<FunnelChartProps> = ({ selectedChannel = 'all' }) => {
  const clientData = useSelector((state: RootState) => state.client.currentClientData);

  // 기본 퍼널 데이터
  const defaultFunnelData: FunnelStageData = {
    totalImpressions: 524000,
    stages: [
      { from: '노출', to: '클릭', dropRate: 96.8, remaining: 16768 },
      { from: '클릭', to: '랜딩', dropRate: 20.0, remaining: 13414 },
      { from: '랜딩', to: '장바구니', dropRate: 80.0, remaining: 2683 },
      { from: '장바구니', to: '구매', dropRate: 90.8, remaining: 247 }
    ],
    overallConversionRate: 0.047
  };

  // 선택된 채널에 따라 퍼널 데이터 가져오기
  const funnelData = clientData?.funnelData?.[selectedChannel] || defaultFunnelData;

  // 이탈률에 따른 색상 및 상태 결정
  const getStageStyle = (dropRate: number) => {
    if (dropRate > 80) {
      return {
        bgColor: 'bg-danger-dark',
        textColor: 'text-white',
        status: '병목'
      };
    } else if (dropRate >= 30) {
      return {
        bgColor: 'bg-warning',
        textColor: 'text-gray-900',
        status: '주의'
      };
    } else {
      return {
        bgColor: 'bg-success',
        textColor: 'text-white',
        status: '양호'
      };
    }
  };

  // 병목 구간 찾기
  const bottleneckStages = funnelData?.stages?.filter(s => s.dropRate > 80) || [];

  // 채널 라벨
  const channelLabels = {
    all: '전체 통합',
    naver: '네이버',
    meta: '메타',
    google: '구글',
    kakao: '카카오'
  };

  return (
    <div className="bg-white rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">전환 퍼널</h3>
        {selectedChannel !== 'all' && (
          <span className="px-3 py-1 bg-accent/10 text-accent text-sm font-medium rounded-full">
            {channelLabels[selectedChannel]} 채널
          </span>
        )}
      </div>

      {/* 총 노출 수 요약 영역 */}
      <div className="bg-gray-50 rounded-lg p-4 mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 bg-gray-600 rounded-full"></div>
          <span className="font-medium text-gray-700">총 노출</span>
          <span className="text-2xl font-bold text-gray-900">
            {funnelData.totalImpressions?.toLocaleString() || '0'}
          </span>
        </div>
        <span className="text-sm text-gray-500">캠페인 기간 내 전체 노출 수</span>
      </div>

      {/* 단계별 이탈률 표시 */}
      <div className="space-y-3 mb-6">
        {funnelData.stages?.map((stage, index) => {
          const style = getStageStyle(stage.dropRate);
          return (
            <div key={index} className="flex items-center gap-4">
              {/* 단계 레이블 */}
              <div className="w-32 flex items-center gap-2 text-sm font-medium text-gray-700">
                <span>{stage.from}</span>
                <span>→</span>
                <span>{stage.to}</span>
              </div>

              {/* 이탈률 바 */}
              <div className={`flex-1 h-10 ${style.bgColor} rounded flex items-center px-3`}>
                <span className={`font-semibold ${style.textColor}`}>
                  {stage.dropRate}% 이탈
                </span>
                <span className={`ml-3 px-2 py-0.5 text-xs font-medium rounded ${
                  style.status === '병목' ? 'bg-white/20 text-white' :
                  style.status === '주의' ? 'bg-white/60 text-gray-800' :
                  'bg-white/60 text-gray-700'
                }`}>
                  {style.status}
                </span>
              </div>

              {/* 잔류 인원 */}
              <div className="w-32 text-right">
                <span className="text-sm font-medium text-gray-900">
                  {stage.remaining.toLocaleString()}명
                </span>
                {/* 리텐션 정보 추가 */}
                {stage.to === '클릭' && (
                  <div className="text-xs text-gray-500 mt-1">방문 리텐션 41%</div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* 범례 및 전체 전환율 */}
      <div className="border-t pt-4 space-y-3">
        {/* 범례 */}
        <div className="flex items-center gap-6 text-sm">
          <span className="text-gray-500">범례:</span>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-success rounded"></div>
            <span className="text-gray-600">양호(30% 미만)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-warning rounded"></div>
            <span className="text-gray-600">주의(30~80%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-danger-dark rounded"></div>
            <span className="text-gray-600">병목(80% 초과)</span>
          </div>
        </div>

        {/* 전체 전환율 */}
        <div className="flex items-center justify-between bg-gray-50 rounded-lg px-4 py-3">
          <span className="text-sm font-medium text-gray-700">전체 전환율 (노출→구매):</span>
          <span className="text-lg font-bold text-gray-900">{funnelData.overallConversionRate || 0}%</span>
        </div>
      </div>

      {/* AI 인사이트 박스 */}
      {bottleneckStages.length > 0 && (
        <div className="mt-6 bg-danger-bg border border-danger rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="mt-0.5">
              <svg className="w-5 h-5 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-danger-dark mb-1">AI 병목 감지</h4>
              <p className="text-sm text-danger-dark">
                {bottleneckStages.map(s => `${s.from}→${s.to}`).join(', ')} 단계에서 심각한 이탈이 발생하고 있습니다.
                {bottleneckStages[0] && bottleneckStages[0].from === '노출' ?
                  ' 클릭률 개선을 위한 소재 최적화가 시급합니다.' :
                  bottleneckStages[0] && bottleneckStages[0].from === '랜딩' ?
                  ' 랜딩 페이지 전환율 개선이 필요합니다.' :
                  ' 구매 전환 프로세스 개선이 필요합니다.'}
              </p>
              <div className="mt-2 inline-flex items-center gap-1 px-2 py-1 bg-info-bg text-accent rounded text-xs font-medium">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                  <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd"/>
                </svg>
                AI 자동 분석
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FunnelChart;