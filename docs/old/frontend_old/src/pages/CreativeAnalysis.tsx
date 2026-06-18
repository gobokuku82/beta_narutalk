import { useSelector, useDispatch } from 'react-redux';
import { useState } from 'react';
import { RootState } from '../app/store';
import { Badge } from '../components/common/Badge';
import { ProgressBar } from '../components/common/ProgressBar';
import { CreativeOptimizePanel } from '../components/creative/CreativeOptimizePanel';
import { AlertTriangle, Settings, ChevronRight, X, Download, ExternalLink } from 'lucide-react';
import { setSelectedCreative } from '../features/creative/creativeSlice';
import { setCurrentTab } from '../features/navigation/navigationSlice';
import { setAgentContext, setInitialMessage } from '../features/agentChat/agentChatSlice';
import { useNavigate } from 'react-router-dom';

const getCreativeImageSrc = (name: string): string | null => {
  if (name.includes('N-02') || name.includes('N02'))
    return '/N02_spring_campaign_naver_250x250.png';
  if (name.includes('G-01') || name.includes('G01'))
    return '/G01_skin2534_google_responsive.png';
  if (name.includes('K-03') || name.includes('K03'))
    return '/K03_kakaoB_kakao_1200x628.png';
  if (name.includes('M-04') || name.includes('M04'))
    return '/M04_toner_sale_meta_1080x1080.png';
  return null;
};

export const CreativeAnalysis: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { selectedCreativeId } = useSelector((state: RootState) => state.creative);
  const clientData = useSelector((state: RootState) => state.client.currentClientData);
  const [showImageModal, setShowImageModal] = useState<string | null>(null);
  const [showThresholdModal, setShowThresholdModal] = useState(false);
  const [thresholds, setThresholds] = useState({
    frequency: 3.5,
    ctr: 2.0,
    roas: 200
  });

  const creatives = clientData?.creatives || [];
  const selectedCreative = creatives.find((c: any) => c.id === selectedCreativeId) || null;

  const getFrequencyColor = (freq: number) => {
    if (freq < 2) return 'text-success';
    if (freq < 3.5) return 'text-warning';
    return 'text-danger';
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'winner': return 'success';
      case 'monitoring': return 'warning';
      case 'replace': return 'danger';
      default: return 'gray';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'winner': return '유지';
      case 'monitoring': return '주시';
      case 'replace': return '교체권고';
      default: return status;
    }
  };

  const handleCreativeClick = (creativeId: string) => {
    if (selectedCreativeId === creativeId) {
      dispatch(setSelectedCreative(null));
    } else {
      dispatch(setSelectedCreative(creativeId));
    }
  };

  const handleImageClick = (imageSrc: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setShowImageModal(imageSrc);
  };

  const handleNavigateToAgent = (context: any) => {
    // Redux store에 소재 맥락 저장
    dispatch(setAgentContext(context));

    // 교체가 필요한 소재 정보를 포함한 메시지 생성
    if (context.type === 'creative_generation') {
      const needReplace = context.creatives.filter((c: any) => c.status === 'replace');
      const monitoring = context.creatives.filter((c: any) => c.status === 'monitoring');

      let message = '';
      if (needReplace.length > 0) {
        const replaceList = needReplace.map((c: any) =>
          `- ${c.name} (${c.channel}, Freq: ${c.frequency}, ROAS: ${c.roas}%)`
        ).join('\n');
        message += `다음 소재들이 교체가 필요합니다:\n${replaceList}\n\n`;
      }

      if (monitoring.length > 0) {
        const monitorList = monitoring.map((c: any) =>
          `- ${c.name} (${c.channel}, ROAS: ${c.roas}%)`
        ).join('\n');
        message += `주시 중인 소재:\n${monitorList}\n\n`;
      }

      message += '성과 데이터를 분석하여 새로운 소재를 생성해주세요. 피로도가 높고 ROAS가 낮은 소재를 우선적으로 교체해주세요.';
      dispatch(setInitialMessage(message));
    } else if (context.creative) {
      // 개별 소재 컨텍스트
      const creative = context.creative;
      const action = context.action || 'optimize';

      if (action === 'budget_increase') {
        const message = `${creative.name} 소재의 성과가 우수합니다.\n현재 ROAS: ${creative.roas}%\n예산 증액 방안을 제안해주세요.`;
        dispatch(setInitialMessage(message));
      } else {
        const message = `${creative.name} 소재 최적화가 필요합니다.\n현재 상태: ${getStatusLabel(creative.status)}\nFrequency: ${creative.frequency}, ROAS: ${creative.roas}%\n\n개선 방안을 제시해주세요.`;
        dispatch(setInitialMessage(message));
      }
    }

    dispatch(setCurrentTab('agent'));
    navigate('/agent');
  };

  const handleNavigateToCost = (channel: string) => {
    dispatch({
      type: 'cost/setFocusChannel',
      payload: channel
    });
    dispatch(setCurrentTab('cost'));
    navigate('/cost');
  };

  return (
    <>
      <div className="flex h-full relative">
        <div className={`flex-1 p-6 transition-all duration-300 ${selectedCreativeId ? 'mr-80' : ''}`}>
          {/* 상단 헤더 */}
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">소재 분석</h2>
            <button
              onClick={() => setShowThresholdModal(true)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="임계값 설정"
            >
              <Settings className="w-5 h-5 text-gray-600" />
            </button>
          </div>

          {/* 소재 카드 그리드 - 가로 스크롤 */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">소재 현황</h3>
              {creatives.length > 4 && (
                <button className="text-luminous-blue hover:text-amore-blue text-sm font-medium flex items-center gap-1">
                  전체 보기
                  <ExternalLink className="w-4 h-4" />
                </button>
              )}
            </div>
            <div className={`${creatives.length > 4 ? 'overflow-x-auto' : 'grid grid-cols-4 gap-4'}`}>
              <div className={`${creatives.length > 4 ? 'flex gap-4 pb-2' : 'contents'}`}>
                {creatives.map((creative: any) => (
                  <div
                    key={creative.id}
                    onClick={() => handleCreativeClick(creative.id)}
                    className={`${creatives.length > 4 ? 'flex-shrink-0 w-64' : ''} bg-white rounded-lg shadow border-2 cursor-pointer transition-all hover:shadow-lg ${
                      creative.status === 'winner' ? 'border-success' :
                      creative.status === 'replace' ? 'border-danger' : 'border-gray-200'
                    } ${selectedCreativeId === creative.id ? 'ring-2 ring-luminous-blue' : ''}`}
                  >
                    {(() => {
                      const imageSrc = getCreativeImageSrc(creative.name);
                      if (imageSrc) {
                        return (
                          <>
                            <img
                              src={imageSrc}
                              alt={creative.name}
                              className="w-full h-48 object-cover rounded-t-lg cursor-zoom-in"
                              onClick={(e) => handleImageClick(imageSrc, e)}
                              onError={(e) => {
                                const target = e.target as HTMLImageElement;
                                target.style.display = 'none';
                                const fallback = target.nextElementSibling as HTMLDivElement;
                                if (fallback) fallback.style.display = 'flex';
                              }}
                            />
                            <div className={`h-48 items-center justify-center ${
                              creative.channel === 'naver' ? 'bg-naver/10' :
                              creative.channel === 'kakao' ? 'bg-kakao/10' :
                              creative.channel === 'meta' ? 'bg-meta/10' : 'bg-google/10'
                            } hidden rounded-t-lg`}>
                              <span className="text-gray-400">Preview</span>
                            </div>
                          </>
                        );
                      } else {
                        return (
                          <div className={`h-48 flex items-center justify-center ${
                            creative.channel === 'naver' ? 'bg-naver/10' :
                            creative.channel === 'kakao' ? 'bg-kakao/10' :
                            creative.channel === 'meta' ? 'bg-meta/10' : 'bg-google/10'
                          } rounded-t-lg`}>
                            <span className="text-gray-400">Preview</span>
                          </div>
                        );
                      }
                    })()}
                    <div className="p-3">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold text-sm">{creative.name}</h4>
                        <Badge variant={getStatusBadgeVariant(creative.status)} size="sm">
                          {getStatusLabel(creative.status)}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-500 mb-2">{creative.spec}</p>

                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between">
                          <span className="text-gray-500">CTR/CVR</span>
                          <span className="font-semibold">{creative.ctr}% / {creative.cvr}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">ROAS</span>
                          <span className="font-semibold">{creative.roas}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">CPA</span>
                          <span className="font-semibold">₩{creative.cpa.toLocaleString()}</span>
                        </div>
                      </div>

                      <div className="mt-2">
                        <div className="flex justify-between text-xs mb-1">
                          <span>피로도</span>
                          <span className={getFrequencyColor(creative.frequency)}>
                            {creative.frequency}
                          </span>
                        </div>
                        <ProgressBar
                          value={(creative.frequency / 5) * 100}
                          color={creative.frequency < 2 ? 'green' : creative.frequency < 3.5 ? 'amber' : 'red'}
                          height="sm"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 소재 성과 테이블 - 액션 컬럼 삭제 */}
          <div className="bg-white rounded-lg shadow border border-gray-200 mb-6">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold">소재 성과 상세</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">소재명</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">매체</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">규격</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">CTR</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">CVR</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">CPC</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">ROAS</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">CPA</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Freq</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">집행일</th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">상태</th>
                  </tr>
                </thead>
                <tbody>
                  {creatives.map((creative: any) => (
                    <tr
                      key={creative.id}
                      onClick={() => handleCreativeClick(creative.id)}
                      className={`border-b border-gray-100 hover:bg-gray-50 cursor-pointer ${
                        creative.status === 'replace' ? 'bg-danger-bg' : ''
                      } ${selectedCreativeId === creative.id ? 'bg-luminous-blue/5' : ''}`}
                    >
                      <td className="px-6 py-4 font-medium">{creative.name}</td>
                      <td className="px-6 py-4">{creative.channel}</td>
                      <td className="px-6 py-4">{creative.spec}</td>
                      <td className="px-6 py-4 text-right">{creative.ctr}%</td>
                      <td className="px-6 py-4 text-right">{creative.cvr}%</td>
                      <td className="px-6 py-4 text-right">₩{creative.cpc?.toLocaleString() || '0'}</td>
                      <td className="px-6 py-4 text-right">{creative.roas}%</td>
                      <td className="px-6 py-4 text-right">₩{creative.cpa.toLocaleString()}</td>
                      <td className={`px-6 py-4 text-right ${getFrequencyColor(creative.frequency)}`}>
                        {creative.frequency}
                      </td>
                      <td className="px-6 py-4 text-right">{creative.days}일</td>
                      <td className="px-6 py-4 text-center">
                        <Badge variant={getStatusBadgeVariant(creative.status)}>
                          {getStatusLabel(creative.status)}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 하단 2열 레이아웃 (6:4 비율) */}
          <div className="grid grid-cols-10 gap-6">
            {/* 왼쪽: 소재 성과 인사이트 (6) */}
            <div className="col-span-6 space-y-6">
              {/* 채널별/규격별 성과 요약 */}
              <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
                <h3 className="text-lg font-semibold mb-4">소재 성과 인사이트</h3>
                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">채널별 최고 성과 소재</h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">네이버</span>
                        <span className="font-medium">봄캠페인A (ROAS 421%)</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">구글</span>
                        <span className="font-medium">스킨25-34 (ROAS 510%)</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">카카오</span>
                        <span className="font-medium">카카오B (ROAS 298%)</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">규격별 평균 성과</h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">250×250</span>
                        <span>CTR 4.8% / ROAS 421%</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">1200×628</span>
                        <span>CTR 2.9% / ROAS 298%</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">1080×1080</span>
                        <span>CTR 1.4% / ROAS 201%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 소재 교체 이력 */}
              <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
                <h3 className="text-lg font-semibold mb-4">소재 교체 이력</h3>
                <div className="space-y-3">
                  <div className="flex gap-3">
                    <div className="w-2 h-2 bg-success rounded-full mt-1.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">네이버 배너 교체 완료</p>
                      <p className="text-xs text-gray-500 mt-1">3/15 · CTR 2.1% → 4.8% (+128%)</p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div className="w-2 h-2 bg-luminous-blue rounded-full mt-1.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">메타 동영상 소재 추가</p>
                      <p className="text-xs text-gray-500 mt-1">3/13 · 신규 타겟 그룹 대상</p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div className="w-2 h-2 bg-warning rounded-full mt-1.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">카카오 와이드 배너 A/B 테스트 시작</p>
                      <p className="text-xs text-gray-500 mt-1">3/10 · 2개 버전 동시 집행</p>
                    </div>
                  </div>
                </div>

                {/* 교체 후 성과 변화 */}
                <div className="mt-4 p-3 bg-success-bg border border-success/30 rounded">
                  <p className="text-sm text-success-dark">
                    <strong>최근 교체 효과:</strong> 평균 CTR +85%, ROAS +142% 개선
                  </p>
                </div>
              </div>
            </div>

            {/* 오른쪽: 소재 생성 CTA (4) */}
            <div className="col-span-4">
              <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
                <h3 className="text-lg font-semibold mb-4">소재 최적화 제안</h3>

                {/* 교체 권고 소재 */}
                {creatives.filter((c: any) => c.status === 'replace').length > 0 && (
                  <div className="mb-4 p-3 bg-danger-bg border border-danger/30 rounded">
                    <p className="text-sm text-danger flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" />
                      <strong>교체 권고:</strong> {creatives.filter((c: any) => c.status === 'replace').length}개 소재 즉시 교체 필요
                    </p>
                  </div>
                )}

                <div className="space-y-3 mb-6">
                  {creatives
                    .filter((c: any) => c.status === 'replace' || c.status === 'monitoring')
                    .slice(0, 3)
                    .map((creative: any) => (
                      <div key={creative.id} className="p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">{creative.name}</span>
                          <Badge variant={getStatusBadgeVariant(creative.status)} size="sm">
                            {getStatusLabel(creative.status)}
                          </Badge>
                        </div>
                        <p className="text-xs text-gray-600">
                          Freq {creative.frequency} / ROAS {creative.roas}%
                        </p>
                      </div>
                    ))
                  }
                </div>

                <button
                  onClick={() => handleNavigateToAgent({
                    type: 'creative_generation',
                    creatives: creatives.filter((c: any) => c.status === 'replace' || c.status === 'monitoring')
                  })}
                  className="w-full bg-luminous-blue text-white py-3 rounded-lg font-medium hover:bg-amore-blue transition-colors flex items-center justify-center gap-2"
                >
                  AI 소재 생성 시작
                  <ChevronRight className="w-4 h-4" />
                </button>

                <p className="text-xs text-gray-500 mt-3 text-center">
                  AI가 성과 데이터를 분석하여 최적화된 소재를 생성합니다
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* 우측 슬라이드 패널 */}
        <div
          className={`fixed right-0 top-16 h-[calc(100vh-4rem)] transform transition-transform duration-300 z-40 ${
            selectedCreativeId ? 'translate-x-0' : 'translate-x-full'
          }`}
        >
          <CreativeOptimizePanel
            creative={selectedCreative}
            onClose={() => dispatch(setSelectedCreative(null))}
            onNavigateToAgent={handleNavigateToAgent}
            onNavigateToCost={handleNavigateToCost}
          />
        </div>
      </div>

      {/* 이미지 확대 모달 */}
      {showImageModal && (
        <div
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
          onClick={() => setShowImageModal(null)}
        >
          <div className="relative max-w-4xl max-h-full">
            <img
              src={showImageModal}
              alt="확대 이미지"
              className="max-w-full max-h-full object-contain"
            />
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowImageModal(null);
              }}
              className="absolute top-4 right-4 p-2 bg-white rounded-full shadow-lg hover:bg-gray-100"
            >
              <X className="w-6 h-6" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                const link = document.createElement('a');
                link.href = showImageModal;
                link.download = 'creative_image.png';
                link.click();
              }}
              className="absolute bottom-4 right-4 p-3 bg-white rounded-lg shadow-lg hover:bg-gray-100 flex items-center gap-2"
            >
              <Download className="w-5 h-5" />
              <span>다운로드</span>
            </button>
          </div>
        </div>
      )}

      {/* 임계값 편집 모달 */}
      {showThresholdModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold">소재 상태 임계값 설정</h3>
              <button
                onClick={() => setShowThresholdModal(false)}
                className="p-1 hover:bg-gray-100 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  피로도 임계값
                </label>
                <input
                  type="number"
                  value={thresholds.frequency}
                  onChange={(e) => setThresholds({ ...thresholds, frequency: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-luminous-blue focus:border-luminous-blue"
                  step="0.1"
                  min="0"
                  max="10"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {thresholds.frequency} 초과 시 '교체권고' 상태로 전환
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  CTR 임계값 (%)
                </label>
                <input
                  type="number"
                  value={thresholds.ctr}
                  onChange={(e) => setThresholds({ ...thresholds, ctr: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-luminous-blue focus:border-luminous-blue"
                  step="0.1"
                  min="0"
                  max="100"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {thresholds.ctr}% 미만 시 '주시' 상태로 전환
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ROAS 임계값 (%)
                </label>
                <input
                  type="number"
                  value={thresholds.roas}
                  onChange={(e) => setThresholds({ ...thresholds, roas: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-luminous-blue focus:border-luminous-blue"
                  step="10"
                  min="0"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {thresholds.roas}% 미만 시 '교체권고' 상태로 전환
                </p>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowThresholdModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                취소
              </button>
              <button
                onClick={() => {
                  // 여기에 임계값 저장 로직 추가
                  setShowThresholdModal(false);
                }}
                className="flex-1 px-4 py-2 bg-luminous-blue text-white rounded-lg hover:bg-amore-blue"
              >
                저장
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};