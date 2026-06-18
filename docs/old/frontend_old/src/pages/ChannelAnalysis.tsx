import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../app/store';
import { openChatPanel, setAgentContext, setInitialMessage } from '../features/agentChat/agentChatSlice';
import { useNavigate } from 'react-router-dom';
import FunnelChart from '../components/channel/FunnelChart';
import { RetentionPanel } from '../components/channel/RetentionPanel';
import { Button } from '../components/common';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AlertCircle, ArrowRight, X, Bot } from 'lucide-react';

export const ChannelAnalysis: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const clientData = useSelector((state: RootState) => state.client.currentClientData);
  const kpi = clientData?.kpi;

  const [selectedPeriod, setSelectedPeriod] = useState('7days');
  const [selectedChannel, setSelectedChannel] = useState('all');
  const [showBanner, setShowBanner] = useState(true);

  // 라벨 정의를 상단으로 이동
  const channelLabels: { [key: string]: string } = {
    all: '전체',
    naver: '네이버',
    kakao: '카카오',
    meta: '메타',
    google: '구글',
  };

  const periodLabels: { [key: string]: string } = {
    today: '오늘',
    '7days': '7일',
    '14days': '14일',
    '30days': '30일',
  };

  // 배너 표시 여부를 sessionStorage에서 확인
  useEffect(() => {
    const bannerDismissed = sessionStorage.getItem('learningBannerDismissed');
    if (bannerDismissed === 'true') {
      setShowBanner(false);
    }
  }, []);

  // 배너 닫기 핸들러
  const handleDismissBanner = () => {
    setShowBanner(false);
    sessionStorage.setItem('learningBannerDismissed', 'true');
  };

  // AI 자동 분석 버튼 핸들러
  const handleAIAnalysis = () => {
    // 현재 채널과 기간 정보를 포함한 메시지 생성
    const channelName = channelLabels[selectedChannel];
    const periodName = periodLabels[selectedPeriod];

    const message = `${channelName} 채널의 최근 ${periodName} 성과를 분석해주세요.
주요 지표인 ROAS, CTR, CPA의 추이를 파악하고, 개선이 필요한 부분을 찾아 최적화 방안을 제시해주세요.`;

    dispatch(setInitialMessage(message));
    dispatch(openChatPanel());
  };

  // 리타겟팅 최적화 제안 버튼 핸들러
  const handleRetargetingOptimization = () => {
    // 현재 채널, 기간, 재방문율 맥락 전달
    const context = {
      channel: selectedChannel,
      period: selectedPeriod,
      retentionData: channelPerformance.map(ch => ({
        channel: ch.channel,
        retention: ch.visitRetention
      }))
    };

    // 재방문율 데이터를 포함한 메시지 생성
    const channelRetentionInfo = channelPerformance.map(ch => {
      const channelName = ch.channel === 'naver' ? '네이버' :
                          ch.channel === 'kakao' ? '카카오' :
                          ch.channel === 'meta' ? '메타' : '구글';
      return `- ${channelName}: 재방문율 ${ch.visitRetention}%, 재구매율 ${ch.purchaseRetention}%`;
    }).join('\n');

    const message = `채널별 리타겟팅 성과를 분석하고 최적화 방안을 제시해주세요.

현재 채널별 리텐션 현황:
${channelRetentionInfo}

재방문율이 낮은 채널의 리타겟팅 전략을 수립하고, 구체적인 실행 방안을 제안해주세요.`;

    dispatch(setAgentContext(context));
    dispatch(setInitialMessage(message));
    navigate('/agent');
  };

  // 샘플 차트 데이터
  const chartData = [
    { date: '10/21', roas: 320, ctr: 2.8, cpa: 15000 },
    { date: '10/22', roas: 385, ctr: 3.2, cpa: 14000 },
    { date: '10/23', roas: 410, ctr: 3.5, cpa: 13500 },
    { date: '10/24', roas: 380, ctr: 3.1, cpa: 14500 },
    { date: '10/25', roas: 395, ctr: 3.3, cpa: 14200 },
    { date: '10/26', roas: 420, ctr: 3.6, cpa: 13000 },
    { date: '10/27', roas: 415, ctr: 3.4, cpa: 13200 },
  ];

  // 선택된 채널에 따라 차트 데이터 필터링
  const filteredChartData = selectedChannel === 'all'
    ? chartData
    : chartData.map((day: any) => ({
        ...day,
        // 채널별 데이터 시뮬레이션 (실제로는 API에서 받아옴)
        roas: selectedChannel === 'google' ? day.roas * 1.3 :
              selectedChannel === 'naver' ? day.roas * 0.95 :
              selectedChannel === 'kakao' ? day.roas * 0.8 :
              selectedChannel === 'meta' ? day.roas * 0.5 : day.roas,
        ctr: selectedChannel === 'google' ? day.ctr * 1.5 :
             selectedChannel === 'naver' ? day.ctr * 1.1 : day.ctr,
        cpa: selectedChannel === 'google' ? day.cpa * 0.4 :
             selectedChannel === 'naver' ? day.cpa * 0.8 : day.cpa
      }));

  // 채널별 성과 데이터 - 클라이언트 데이터에서 가져오기
  const channelPerformance = clientData?.channels || [
    { channel: 'naver' as const, status: 'safe' as const, spend: 780000, roas: 421, ctr: 3.2, cpa: 7100, budgetRate: 78, cvr: 3.2, visitRetention: 41, purchaseRetention: 22 },
    { channel: 'kakao' as const, status: 'warning' as const, spend: 510000, roas: 298, ctr: 2.1, cpa: 11400, budgetRate: 85, cvr: 1.9, visitRetention: 33, purchaseRetention: 14 },
    { channel: 'meta' as const, status: 'danger' as const, spend: 610000, roas: 201, ctr: 1.4, cpa: 18200, budgetRate: 61, cvr: 1.1, visitRetention: 27, purchaseRetention: 9 },
    { channel: 'google' as const, status: 'safe' as const, spend: 240000, roas: 510, ctr: 5.1, cpa: 5800, budgetRate: 42, cvr: 4.1, visitRetention: 48, purchaseRetention: 28 },
  ];

  // 채널별 성과 데이터 - 테이블용 확장 데이터 (클라이언트 데이터 기반 생성)
  const channelPerformanceForTable = channelPerformance.map(ch => {
    // 해당 채널의 퍼널 데이터 가져오기
    const channelFunnel = clientData?.funnelData?.[ch.channel as 'naver' | 'meta' | 'google' | 'kakao'];

    if (channelFunnel) {
      // 퍼널 데이터에서 노출수, 클릭수, 구매수 가져오기
      const impressions = channelFunnel.totalImpressions;
      const clickStage = channelFunnel.stages.find(s => s.to === '클릭');
      const purchaseStage = channelFunnel.stages.find(s => s.to === '구매');
      const clicks = clickStage?.remaining || 0;
      const conversions = purchaseStage?.remaining || 0;

      return {
        ...ch,
        impressions,
        clicks,
        conversions,
      };
    }

    // 퍼널 데이터가 없으면 기본값 사용
    return {
      ...ch,
      impressions: Math.floor(Math.random() * 500000) + 100000,
      clicks: Math.floor((ch.spend / ch.cpa) * (ch.ctr / 100) * 1000),
      conversions: Math.floor(ch.spend / ch.cpa),
    };
  });

  // 선택된 채널 데이터 찾기
  const selectedChannelData = channelPerformance.find((ch: any) => ch.channel === selectedChannel);

  return (
    <div className="p-6">
      {/* 학습기 상태 배너 - 간소화 */}
      {kpi?.campaignStage === 'learning' && showBanner && (
        <div className="mb-4 p-2 bg-amber-50 border border-amber-200 rounded-lg relative">
          <p className="text-sm text-amber-800 flex items-center justify-center gap-2 pr-8">
            <AlertCircle className="w-4 h-4" />
            <strong>학습기 {kpi?.campaignDays}일차</strong> · 데이터 수집 중 ({7 - (kpi?.campaignDays || 0)}일 후 최적화 완료 예상)
          </p>
          <button
            onClick={handleDismissBanner}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-amber-100 rounded transition-colors"
            title="닫기"
          >
            <X className="w-4 h-4 text-amber-700" />
          </button>
        </div>
      )}

      {/* 상단 탭 & 기간 선택 */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex gap-2">
          {Object.entries(channelLabels).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setSelectedChannel(key)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedChannel === key
                  ? 'bg-gray-900 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          {Object.entries(periodLabels).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setSelectedPeriod(key)}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                selectedPeriod === key
                  ? 'bg-accent text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* 차트 영역 - 2개 차트 */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* ROAS 일별 추이 */}
        <div className="bg-white rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">ROAS 일별 추이</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleAIAnalysis}
              className="gap-2"
            >
              <Bot className="w-4 h-4" />
              AI 자동 분석
            </Button>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={filteredChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                axisLine={{ stroke: '#9CA3AF' }}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                axisLine={{ stroke: '#9CA3AF' }}
                label={{ value: 'ROAS (%)', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
              />
              <Tooltip
                contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', border: '1px solid #E5E7EB', borderRadius: '8px' }}
                formatter={(value: any) => [`${value}%`, 'ROAS']}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Line
                type="monotone"
                dataKey="roas"
                stroke="#6366F1"
                strokeWidth={2}
                dot={{ fill: '#6366F1', r: 4 }}
                activeDot={{ r: 6 }}
                name="ROAS"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* CTR/CPA 일별 추이 */}
        <div className="bg-white rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">CTR/CPA 일별 추이</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={filteredChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                axisLine={{ stroke: '#9CA3AF' }}
              />
              <YAxis
                yAxisId="left"
                tick={{ fontSize: 12 }}
                axisLine={{ stroke: '#9CA3AF' }}
                label={{ value: 'CTR (%)', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fontSize: 12 }}
                axisLine={{ stroke: '#9CA3AF' }}
                label={{ value: 'CPA (₩)', angle: 90, position: 'insideRight', style: { fontSize: 12 } }}
              />
              <Tooltip
                contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', border: '1px solid #E5E7EB', borderRadius: '8px' }}
                formatter={(value: any, name: any) => {
                  if (name === 'CTR (%)') return [`${value}%`, 'CTR'];
                  return [`₩${value.toLocaleString()}`, 'CPA'];
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="ctr"
                stroke="#10B981"
                strokeWidth={2}
                dot={{ fill: '#10B981', r: 4 }}
                activeDot={{ r: 6 }}
                name="CTR (%)"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="cpa"
                stroke="#EF4444"
                strokeWidth={2}
                dot={{ fill: '#EF4444', r: 4 }}
                activeDot={{ r: 6 }}
                name="CPA (₩)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 채널별 성과 */}
      <div className="mb-6">
        <div className="bg-white rounded-lg overflow-hidden">
          {/* 개별 채널 선택 시 카드형 레이아웃 */}
          {selectedChannel !== 'all' && selectedChannelData && (
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-bold text-gray-900">
                  {channelLabels[selectedChannel]} 채널 성과
                </h3>
                <span className="px-3 py-1 bg-accent/10 text-accent text-sm font-medium rounded-full">
                  선택된 채널
                </span>
              </div>

              {/* 핵심 지표 - 큰 카드 */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-2">CTR</p>
                  <p className="text-2xl font-bold text-gray-900">{selectedChannelData.ctr}%</p>
                  <p className="text-xs text-gray-500 mt-2">
                    전체 평균 대비 {selectedChannelData.ctr > 3.2 ? '+' : ''}{(selectedChannelData.ctr - 3.2).toFixed(1)}%p
                    <span className={selectedChannelData.ctr > 3.2 ? 'text-success ml-1' : 'text-danger ml-1'}>
                      {selectedChannelData.ctr > 3.2 ? '↑' : '↓'}
                    </span>
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-2">ROAS</p>
                  <p className="text-2xl font-bold text-gray-900">{selectedChannelData.roas}%</p>
                  <p className="text-xs text-gray-500 mt-2">
                    전체 평균 대비 {selectedChannelData.roas > 366 ? '+' : ''}{selectedChannelData.roas - 366}%p
                    <span className={selectedChannelData.roas > 366 ? 'text-success ml-1' : 'text-danger ml-1'}>
                      {selectedChannelData.roas > 366 ? '↑' : '↓'}
                    </span>
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-2">CPA</p>
                  <p className="text-2xl font-bold text-gray-900">₩{selectedChannelData.cpa.toLocaleString()}</p>
                  <p className="text-xs text-gray-500 mt-2">
                    전체 평균 대비 ₩{Math.abs(selectedChannelData.cpa - 10550).toLocaleString()}
                    <span className={selectedChannelData.cpa < 10550 ? 'text-success ml-1' : 'text-danger ml-1'}>
                      {selectedChannelData.cpa < 10550 ? '↓(개선)' : '↑'}
                    </span>
                  </p>
                </div>
              </div>

              {/* 상세 지표 - 작은 카드 그리드 */}
              <div className="border-t pt-6">
                <h4 className="text-sm font-medium text-gray-700 mb-4">상세 데이터</h4>
                {channelPerformanceForTable
                  .filter(detail => detail.channel === selectedChannel)
                  .map((detail) => (
                    <div key={detail.channel} className="grid grid-cols-2 gap-3">
                      <div className="bg-white border border-gray-200 rounded-lg p-3 flex justify-between items-center">
                        <span className="text-sm text-gray-600">총 노출수</span>
                        <span className="text-sm font-semibold text-gray-900">{detail.impressions.toLocaleString()}</span>
                      </div>
                      <div className="bg-white border border-gray-200 rounded-lg p-3 flex justify-between items-center">
                        <span className="text-sm text-gray-600">클릭수</span>
                        <span className="text-sm font-semibold text-gray-900">{detail.clicks.toLocaleString()}</span>
                      </div>
                      <div className="bg-white border border-gray-200 rounded-lg p-3 flex justify-between items-center">
                        <span className="text-sm text-gray-600">전환수</span>
                        <span className="text-sm font-semibold text-gray-900">{detail.conversions.toLocaleString()}</span>
                      </div>
                      <div className="bg-white border border-gray-200 rounded-lg p-3 flex justify-between items-center">
                        <span className="text-sm text-gray-600">전환율 (CVR)</span>
                        <span className="text-sm font-semibold text-gray-900">{detail.cvr}%</span>
                      </div>
                      <div className="bg-white border border-gray-200 rounded-lg p-3 flex justify-between items-center">
                        <span className="text-sm text-gray-600">광고비 집행</span>
                        <span className="text-sm font-semibold text-gray-900">₩{detail.spend.toLocaleString()}</span>
                      </div>
                      <div className="bg-white border border-gray-200 rounded-lg p-3 flex justify-between items-center">
                        <span className="text-sm text-gray-600">예산 소진율</span>
                        <span className="text-sm font-semibold text-gray-900">{detail.budgetRate}%</span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* 전체 선택 시 테이블 */}
          {selectedChannel === 'all' && (
            <>
              <div className="flex justify-between items-center p-4 border-b">
                <h3 className="text-lg font-semibold">채널별 성과</h3>
                <Button
                variant="ghost"
                size="sm"
                onClick={handleRetargetingOptimization}
                className="gap-2"
              >
                리타겟팅 최적화 제안
                <ArrowRight className="w-4 h-4" />
              </Button>
              </div>
              <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">채널</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">노출</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">클릭</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">CTR</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">전환</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">CVR</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">광고비</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">ROAS</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">CPA</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {channelPerformanceForTable.map((detail) => {
                const channelNames = {
                  naver: '네이버',
                  kakao: '카카오',
                  meta: '메타',
                  google: '구글'
                };

                return (
                  <tr
                    key={detail.channel}
                    className="border-b border-gray-100 hover:bg-gray-50"
                  >
                    <td className="px-6 py-4">
                      {channelNames[detail.channel as keyof typeof channelNames]}
                    </td>
                    <td className="px-6 py-4 text-right">{detail.impressions.toLocaleString()}</td>
                    <td className="px-6 py-4 text-right">{detail.clicks.toLocaleString()}</td>
                    <td className="px-6 py-4 text-right">{detail.ctr}%</td>
                    <td className="px-6 py-4 text-right">{detail.conversions.toLocaleString()}</td>
                    <td className="px-6 py-4 text-right">{detail.cvr}%</td>
                    <td className="px-6 py-4 text-right">₩{detail.spend.toLocaleString()}</td>
                    <td className={`px-6 py-4 text-right ${
                      detail.roas >= 400 ? 'text-green-600 font-semibold' :
                      detail.roas >= 300 ? 'text-amber-600' : 'text-red-600'
                    }`}>
                      {detail.roas}%
                    </td>
                    <td className="px-6 py-4 text-right">₩{detail.cpa.toLocaleString()}</td>
                  </tr>
                );
              })}
            </tbody>
              </table>
            </>
          )}
        </div>
      </div>

      {/* 전환 퍼널과 방문 리텐션 분석 - 2열 레이아웃 */}
      <div className="grid grid-cols-2 gap-6">
        {/* 전환 퍼널 */}
        <FunnelChart selectedChannel={selectedChannel as 'all' | 'naver' | 'meta' | 'google' | 'kakao'} />

        {/* 방문 리텐션 분석 */}
        <RetentionPanel
          channels={channelPerformance}
          selectedChannel={selectedChannel}
        />
      </div>
    </div>
  );
};

export default ChannelAnalysis;