import React from 'react';
import { ChannelPerformance } from '../../types';
import { ProgressBar } from '../common/ProgressBar';
import { TrendingUp, Users } from 'lucide-react';

interface RetentionPanelProps {
  channels: ChannelPerformance[];
  selectedChannel?: string;
}

export const RetentionPanel: React.FC<RetentionPanelProps> = ({ channels, selectedChannel }) => {
  // channels가 undefined인 경우 빈 배열로 처리
  const safeChannels = channels || [];

  const getRetentionColor = (value: number): 'green' | 'amber' | 'red' => {
    if (value >= 40) return 'green';
    if (value >= 25) return 'amber';
    return 'red';
  };

  const channelNames = {
    naver: '네이버',
    kakao: '카카오',
    meta: '메타',
    google: '구글'
  };

  // 데이터가 없으면 로딩 또는 빈 상태 표시
  if (!safeChannels || safeChannels.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Users className="w-5 h-5" />
          방문 리텐션 분석
        </h3>
        <p className="text-gray-500">채널 데이터를 불러오는 중...</p>
      </div>
    );
  }

  // visitRetention이 없는 경우 기본값 설정
  const channelsWithRetention = safeChannels.map(ch => ({
    ...ch,
    visitRetention: ch.visitRetention || 0
  }));

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Users className="w-5 h-5" />
        방문 리텐션 분석
      </h3>

      {/* 리텐션 지표 요약 */}
      <div className="p-4 bg-gray-50 rounded-lg mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-600">평균 재방문율</span>
          <TrendingUp className="w-4 h-4 text-gray-400" />
        </div>
        <p className="text-2xl font-bold text-gray-900">
          {Math.round(channelsWithRetention.reduce((sum, ch) => sum + ch.visitRetention, 0) / channelsWithRetention.length)}%
        </p>
        <p className="text-xs text-gray-500 mt-1">클릭 후 7일 내 재방문 비율</p>
      </div>

      {/* 채널별 리텐션 상세 */}
      <div className="space-y-4">
        <h4 className="text-sm font-semibold text-gray-700">채널별 재방문율</h4>

        {channelsWithRetention.map(channel => {
          const isSelected = selectedChannel === channel.channel || selectedChannel === 'all';
          const isHighlighted = selectedChannel === channel.channel;

          return (
            <div
              key={channel.channel}
              className={`space-y-2 pb-3 border-b border-gray-100 last:border-0 ${
                isHighlighted ? 'bg-accent/5 -mx-2 px-2 py-2 rounded' : ''
              } ${!isSelected && selectedChannel !== 'all' ? 'opacity-50' : ''}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`font-medium text-sm ${isHighlighted ? 'text-accent' : ''}`}>
                    {channelNames[channel.channel]}
                  </span>
                  {isHighlighted && (
                    <span className="text-xs px-2 py-0.5 bg-accent/10 text-accent rounded">선택됨</span>
                  )}
                </div>
                <span className={`font-semibold text-sm ${
                  channel.visitRetention >= 40 ? 'text-success-dark' :
                  channel.visitRetention >= 25 ? 'text-warning-dark' : 'text-danger-dark'
                }`}>
                  {channel.visitRetention}%
                </span>
              </div>
              <ProgressBar
                value={channel.visitRetention}
                color={getRetentionColor(channel.visitRetention)}
                height="sm"
              />
            </div>
          );
        })}
      </div>

      {/* AI 인사이트 */}
      <div className="mt-6 p-4 bg-info-bg border border-info rounded-lg">
        <div className="flex items-start gap-2">
          <div className="w-1 h-1 bg-accent rounded-full mt-2" />
          <div className="flex-1">
            <p className="text-sm text-accent">
              <strong>AI 분석:</strong> 네이버 채널의 재방문율(41%)이 가장 높아 브랜드 인지도 형성에 효과적입니다.
              메타 채널은 재방문율(22%)이 낮아 리타겟팅 캠페인 강화가 필요합니다.
            </p>
            <div className="mt-2 inline-flex items-center gap-1 px-2 py-1 bg-info-bg text-accent rounded text-xs font-medium">
              리타겟팅 최적화 제안 →
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};