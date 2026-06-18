import React, { useState, useMemo } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../app/store';
import { selectItem, setActiveTab, approveItem, rejectItem } from '../features/hitl/hitlSlice';
import { setCurrentTab } from '../features/navigation/navigationSlice';
import { useNavigate } from 'react-router-dom';
import { Badge } from '../components/common/Badge';
import { Clock, CheckCircle, XCircle, AlertCircle, Edit2, AlertTriangle, Users, Calendar, DollarSign } from 'lucide-react';
import type { HitlItem } from '../types';

// 에이전트 플로우 표시 컴포넌트
const AgentFlowDisplay = ({ item }: { item: HitlItem }) => {
  // 4개 주요 레이어
  const mainLayers = [
    { id: 'intent', name: '의도분석', status: 'done' },
    { id: 'plan', name: '계획수립', status: 'done' },
    { id: 'execute', name: '실행', status: 'current' },
    { id: 'result', name: '결과', status: 'pending' },
  ];

  // 실제 item의 flowPosition에서 현재 위치 가져오기
  const flowPosition = item.flowPosition || {
    layer: 'execute',
    subStep: '소재 생성',
    stepNumber: 2,
    totalSteps: 3,
    reason: '예산 초과 승인 필요'
  };

  // 현재 레이어 찾기
  const currentLayerIndex = mainLayers.findIndex(l => l.id === flowPosition.layer);

  // 레이어 상태 업데이트
  const layersWithStatus = mainLayers.map((layer, index) => {
    if (index < currentLayerIndex) return { ...layer, status: 'done' };
    if (index === currentLayerIndex) return { ...layer, status: 'current' };
    return { ...layer, status: 'pending' };
  });

  // 실행 레이어의 세부 단계 (실행 레이어인 경우만)
  const executionSubSteps = flowPosition.layer === 'execute' && flowPosition.subStep ? [
    { name: flowPosition.subStep, current: true, step: `${flowPosition.stepNumber}/${flowPosition.totalSteps}` }
  ] : null;

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <h4 className="text-sm font-semibold mb-3 text-gray-700">에이전트 실행 플로우</h4>

      {/* 메인 4개 레이어 */}
      <div className="flex items-center gap-2 mb-4">
        {layersWithStatus.map((layer, index) => (
          <React.Fragment key={layer.id}>
            <div className="flex flex-col items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-xs font-medium mb-1 ${
                layer.status === 'done' ? 'bg-success text-white' :
                layer.status === 'current' ? 'bg-luminous-blue text-white animate-pulse' :
                'bg-gray-200 text-gray-500'
              }`}>
                {layer.status === 'done' ? '✓' : index + 1}
              </div>
              <span className={`text-xs ${
                layer.status === 'current' ? 'font-semibold text-gray-900' : 'text-gray-600'
              }`}>
                {layer.name}
              </span>
            </div>
            {index < layersWithStatus.length - 1 && (
              <div className={`flex-1 h-0.5 ${
                layersWithStatus[index + 1].status === 'done' || layersWithStatus[index + 1].status === 'current'
                  ? 'bg-luminous-blue'
                  : 'bg-gray-300'
              }`} />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* 실행 레이어 세부 단계 (있는 경우) */}
      {executionSubSteps && (
        <div className="ml-[88px] mt-2 p-3 bg-white rounded-lg border border-luminous-blue/20">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-luminous-blue rounded-full animate-pulse" />
            <span className="text-xs font-medium text-gray-900">
              {executionSubSteps[0].name}
            </span>
            <span className="text-xs text-gray-500">
              ({executionSubSteps[0].step} 단계)
            </span>
          </div>
        </div>
      )}

      {/* HITL 발생 정보 */}
      <div className="mt-4 pt-3 border-t border-gray-200">
        <div className="flex items-start gap-2 mb-2">
          <div className="w-4 h-4 rounded-full bg-warning/20 flex items-center justify-center mt-0.5">
            <div className="w-2 h-2 rounded-full bg-warning" />
          </div>
          <div className="flex-1">
            <p className="text-xs font-medium text-gray-700">HITL 발생 위치</p>
            <p className="text-xs text-gray-600 mt-0.5">
              {layersWithStatus[currentLayerIndex].name} 레이어
              {flowPosition.subStep && ` > ${flowPosition.subStep}`}
            </p>
          </div>
        </div>

        {flowPosition.reason && (
          <div className="flex items-start gap-2">
            <div className="w-4 h-4 rounded-full bg-info/20 flex items-center justify-center mt-0.5">
              <div className="w-2 h-2 rounded-full bg-info" />
            </div>
            <div className="flex-1">
              <p className="text-xs font-medium text-gray-700">개입 사유</p>
              <p className="text-xs text-gray-600 mt-0.5">{flowPosition.reason}</p>
            </div>
          </div>
        )}

        <p className="text-xs text-gray-500 mt-3">
          승인 시 나머지 단계가 자동으로 진행됩니다
        </p>
      </div>
    </div>
  );
};

// 보고서 발송 탭 컴포넌트
const ReportTab = () => {
  const [recipients, setRecipients] = useState('client@example.com, team@example.com');
  const [format, setFormat] = useState('pdf');
  const [scheduleTime, setScheduleTime] = useState('immediate');

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">발송 대상</label>
        <input
          type="text"
          value={recipients}
          onChange={(e) => setRecipients(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-luminous-blue focus:border-luminous-blue"
          placeholder="이메일 주소를 쉼표로 구분하여 입력"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">보고서 형식</label>
        <div className="grid grid-cols-3 gap-3">
          {['pdf', 'excel', 'ppt'].map((type) => (
            <button
              key={type}
              onClick={() => setFormat(type)}
              className={`py-2 px-4 rounded-lg border-2 transition-all ${
                format === type
                  ? 'border-luminous-blue bg-luminous-blue/5 text-luminous-blue'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              {type.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">발송 시간</label>
        <div className="space-y-2">
          <label className="flex items-center gap-2">
            <input
              type="radio"
              value="immediate"
              checked={scheduleTime === 'immediate'}
              onChange={(e) => setScheduleTime(e.target.value)}
              className="text-luminous-blue"
            />
            <span className="text-sm">즉시 발송</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              value="scheduled"
              checked={scheduleTime === 'scheduled'}
              onChange={(e) => setScheduleTime(e.target.value)}
              className="text-luminous-blue"
            />
            <span className="text-sm">예약 발송 (매주 월요일 09:00)</span>
          </label>
        </div>
      </div>

      <div className="bg-info-bg border border-info rounded-lg p-4">
        <p className="text-sm text-info-dark">
          보고서에는 최근 7일간의 성과 데이터와 AI 인사이트가 포함됩니다.
        </p>
      </div>
    </div>
  );
};

// 캠페인 세팅 탭 컴포넌트
const CampaignSettingTab = () => {
  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="font-semibold text-sm mb-3">예산 변경 요청</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-500 mb-1">현재</p>
            <p className="text-lg font-semibold">₩3,000,000</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">변경 후</p>
            <p className="text-lg font-semibold text-success">₩4,500,000</p>
            <p className="text-xs text-success-dark mt-1">+50% 증액</p>
          </div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="font-semibold text-sm mb-3">기간 변경 요청</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-500 mb-1">현재</p>
            <p className="text-sm font-medium">03/01 ~ 03/31</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">변경 후</p>
            <p className="text-sm font-medium text-info">03/01 ~ 04/15</p>
            <p className="text-xs text-info-dark mt-1">+15일 연장</p>
          </div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="font-semibold text-sm mb-3">타겟 변경 요청</h4>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm">연령대</span>
            <span className="text-sm font-medium">25-34 → 20-39</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">관심사</span>
            <span className="text-sm font-medium">뷰티 → 뷰티+패션</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// 완료 이력 탭 컴포넌트
const HistoryTab = () => {
  const historyItems = [
    {
      id: 'h1',
      title: '네이버 배너 3종 승인',
      type: 'creative',
      processor: '김지수',
      processedAt: '2024-03-17 14:35',
      result: 'approved',
      roasChange: '+12%',
    },
    {
      id: 'h2',
      title: '예산 재배분 반려',
      type: 'budget',
      processor: '이서연',
      processedAt: '2024-03-17 13:20',
      result: 'rejected',
      roasChange: '-',
    },
    {
      id: 'h3',
      title: '보고서 발송 승인',
      type: 'report',
      processor: '박민호',
      processedAt: '2024-03-17 10:15',
      result: 'approved',
      roasChange: '-',
    },
  ];

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">항목</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">유형</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">처리자</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">처리 시간</th>
            <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">결과</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">ROAS 변화</th>
          </tr>
        </thead>
        <tbody>
          {historyItems.map((item) => (
            <tr key={item.id} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="px-4 py-3 text-sm font-medium">{item.title}</td>
              <td className="px-4 py-3">
                <Badge variant={item.type === 'creative' ? 'info' : item.type === 'budget' ? 'warning' : 'gray'} size="sm">
                  {item.type === 'creative' ? '소재' : item.type === 'budget' ? '예산' : '보고서'}
                </Badge>
              </td>
              <td className="px-4 py-3 text-sm text-gray-600">{item.processor}</td>
              <td className="px-4 py-3 text-sm text-gray-600">{item.processedAt}</td>
              <td className="px-4 py-3 text-center">
                <Badge variant={item.result === 'approved' ? 'success' : 'danger'} size="sm">
                  {item.result === 'approved' ? '승인' : '반려'}
                </Badge>
              </td>
              <td className="px-4 py-3 text-sm text-right font-medium">
                {item.roasChange !== '-' ? (
                  <span className="text-success">{item.roasChange}</span>
                ) : (
                  <span className="text-gray-400">-</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export const HitlCenter: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { items, selectedId, activeTab } = useSelector((state: RootState) => state.hitl);
  const [selectedChoice, setSelectedChoice] = useState<string | null>(null);
  const [showModifyInput, setShowModifyInput] = useState(false);
  const [modifyText, setModifyText] = useState('');
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  // 목록 정렬 (타임아웃 임박 → 광고비 손실 규모 → 생성 시간 순)
  const sortedItems = useMemo(() => {
    const pendingItems = items.filter(item => item.status === 'pending' || item.status === 'delayed');

    return [...pendingItems].sort((a, b) => {
      // 1. 타임아웃 임박 (대기 시간이 긴 것 우선)
      if (a.waitMinutes !== b.waitMinutes) {
        return b.waitMinutes - a.waitMinutes;
      }

      // 2. 광고비 손실 규모 (urgency가 critical인 것 우선)
      const urgencyOrder = { critical: 0, warning: 1, normal: 2 };
      if (a.urgency !== b.urgency) {
        return urgencyOrder[a.urgency] - urgencyOrder[b.urgency];
      }

      // 3. 생성 시간 (오래된 것 우선)
      return a.createdAt.localeCompare(b.createdAt);
    });
  }, [items]);

  const selectedItem = items.find(item => item.id === selectedId);

  const filteredItems = activeTab === 'all' ? sortedItems :
    activeTab === 'history' ? items.filter(item => item.status === 'approved' || item.status === 'rejected') :
    sortedItems.filter(item => item.type === activeTab);

  const tabs = [
    { key: 'all', label: '전체', count: sortedItems.length },
    { key: 'creative', label: '소재 초안', count: sortedItems.filter(i => i.type === 'creative').length },
    { key: 'budget', label: '예산 재배분', count: sortedItems.filter(i => i.type === 'budget').length },
    { key: 'report', label: '보고서 발송', count: sortedItems.filter(i => i.type === 'report').length },
    { key: 'campaign', label: '캠페인 세팅', count: sortedItems.filter(i => i.type === 'campaign').length },
    { key: 'history', label: '완료 이력', count: items.filter(i => i.status === 'approved' || i.status === 'rejected').length },
  ];

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'creative':
        return <AlertCircle className="w-5 h-5 text-luminous-blue" />;
      case 'budget':
        return <DollarSign className="w-5 h-5 text-warning" />;
      case 'report':
        return <Users className="w-5 h-5 text-gray-600" />;
      case 'campaign':
        return <Calendar className="w-5 h-5 text-purple-600" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-600" />;
    }
  };

  const getUrgencyBadge = (urgency: string, waitMinutes: number) => {
    if (waitMinutes >= 180) {
      return <Badge variant="danger" size="sm">긴급</Badge>;
    }
    if (urgency === 'critical') {
      return <Badge variant="danger" size="sm">중요</Badge>;
    }
    if (urgency === 'warning') {
      return <Badge variant="warning" size="sm">주의</Badge>;
    }
    return null;
  };

  const handleApprove = () => {
    if (!selectedItem) return;
    dispatch(approveItem(selectedItem.id));
    // 완료 이력 기록, 대시보드 수치 갱신, 에이전트 재개 로직
  };

  const handleModify = () => {
    if (!selectedItem || !modifyText) return;
    // 에이전트 탭으로 이동하며 수정 내용 전달
    dispatch({
      type: 'agent/setHitlContext',
      payload: {
        itemId: selectedItem.id,
        modification: modifyText,
      },
    });
    dispatch(setCurrentTab('agent'));
    navigate('/agent');
  };

  const handleReject = () => {
    if (!selectedItem || !rejectReason) return;
    dispatch(rejectItem({ id: selectedItem.id, reason: rejectReason }));
    // 반려 사유를 에이전트에 전달하고 완료 이력에 기록
  };

  // 버튼 활성화 조건
  const isActionEnabled = selectedChoice ||
    (selectedItem?.type === 'creative' && !selectedItem?.choices) ||
    (selectedItem?.type === 'report') ||
    (selectedItem?.type === 'campaign');

  return (
    <div className="h-full flex flex-col">
      {/* 헤더 */}
      <div className="px-6 py-4 bg-white border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-bold">사용자 개입 (HITL)</h2>
            <Badge variant="danger" size="md">
              긴급 {sortedItems.filter(i => i.urgency === 'critical').length}건
            </Badge>
            <Badge variant="warning" size="md">
              대기 {sortedItems.length}건
            </Badge>
          </div>
        </div>
      </div>

      {/* 탭 */}
      <div className="bg-white border-b border-gray-200">
        <div className="flex gap-1 px-6">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => dispatch(setActiveTab(tab.key as any))}
              className={`px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'text-luminous-blue border-b-2 border-luminous-blue'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>
      </div>

      {/* 메인 콘텐츠 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 좌측 목록 */}
        <div className="w-1/3 bg-gray-50 border-r border-gray-200 overflow-y-auto">
          <div className="p-4 space-y-3">
            {activeTab === 'history' ? (
              <HistoryTab />
            ) : (
              filteredItems.map(item => (
                <div
                  key={item.id}
                  onClick={() => dispatch(selectItem(item.id))}
                  className={`bg-white rounded-lg p-4 cursor-pointer transition-all ${
                    selectedId === item.id ? 'ring-2 ring-luminous-blue shadow-md' : 'hover:shadow'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-1">{getTypeIcon(item.type)}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium text-sm truncate">{item.title}</h4>
                        {getUrgencyBadge(item.urgency, item.waitMinutes)}
                      </div>
                      <p className="text-xs text-gray-500 truncate">{item.description}</p>
                      <div className="flex items-center gap-3 mt-2">
                        <span className="text-xs text-gray-500">{item.clientName}</span>
                        <span className="text-xs text-gray-400">·</span>
                        <span className="text-xs text-gray-500">{item.createdAt}</span>
                        {item.waitMinutes >= 60 && (
                          <>
                            <span className="text-xs text-gray-400">·</span>
                            <span className={`text-xs font-medium ${
                              item.waitMinutes >= 180 ? 'text-danger' : 'text-warning'
                            }`}>
                              <Clock className="w-3 h-3 inline mr-1" />
                              {Math.floor(item.waitMinutes / 60)}시간 대기
                            </span>
                          </>
                        )}
                      </div>
                      {item.consequence && (
                        <div className="mt-2 text-xs text-danger flex items-start gap-1">
                          <AlertTriangle className="w-3 h-3 mt-0.5" />
                          <span>{item.consequence}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 우측 상세 */}
        <div className="flex-1 bg-white overflow-y-auto">
          {selectedItem && activeTab !== 'history' ? (
            <div className="h-full flex flex-col">
              {/* 우측 상단: 에이전트 플로우 */}
              <div className="p-6 border-b border-gray-200">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      {getTypeIcon(selectedItem.type)}
                      <h3 className="text-lg font-semibold">{selectedItem.title}</h3>
                    </div>
                    <p className="text-sm text-gray-600 mb-4">{selectedItem.description}</p>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500">클라이언트:</span>
                        <span className="font-medium">{selectedItem.clientName}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500">생성 시각:</span>
                        <span className="font-medium">{selectedItem.createdAt}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500">대기 시간:</span>
                        <span className={`font-medium ${selectedItem.waitMinutes >= 180 ? 'text-danger' : ''}`}>
                          {selectedItem.waitMinutes}분
                        </span>
                      </div>
                    </div>
                  </div>
                  <AgentFlowDisplay item={selectedItem} />
                </div>
              </div>

              {/* 우측 중간: 상세 내용 */}
              <div className="flex-1 p-6 overflow-y-auto">
                {selectedItem.type === 'creative' && (
                  <div>
                    <h4 className="font-semibold mb-4">소재 초안 미리보기</h4>
                    <div className="grid grid-cols-3 gap-4 mb-6">
                      {[1, 2, 3].map(i => (
                        <div key={i} className="border rounded-lg p-4">
                          <div className="bg-gray-100 h-32 rounded mb-3 flex items-center justify-center">
                            <span className="text-gray-400">소재 #{i}</span>
                          </div>
                          <p className="text-sm font-medium">배너 250×250</p>
                          <p className="text-xs text-gray-500 mt-1">CTR 예측: 4.2%</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedItem.type === 'budget' && selectedItem.choices && (
                  <div>
                    <h4 className="font-semibold mb-4">예산 재배분 방향 선택</h4>
                    <div className="grid grid-cols-2 gap-4">
                      {selectedItem.choices.map((choice) => (
                        <div
                          key={choice.id}
                          onClick={() => setSelectedChoice(choice.id)}
                          className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                            selectedChoice === choice.id
                              ? 'border-luminous-blue bg-luminous-blue/5'
                              : choice.isRecommended
                              ? 'border-success/30 bg-success-bg hover:border-success/50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          {choice.isRecommended && (
                            <Badge variant="success" size="sm">AI 추천</Badge>
                          )}
                          <h5 className="font-semibold text-sm mt-2 mb-1">{choice.label}</h5>
                          <p className="text-xs text-gray-600 mb-2">{choice.description}</p>
                          <p className={`text-xs font-medium ${
                            choice.effectType === 'positive' ? 'text-success' :
                            choice.effectType === 'warning' ? 'text-warning' : 'text-gray-500'
                          }`}>
                            {choice.effect}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedItem.type === 'report' && (
                  <ReportTab />
                )}

                {selectedItem.type === 'campaign' && (
                  <CampaignSettingTab />
                )}

                {/* 수정 입력 박스 */}
                {showModifyInput && (
                  <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      수정 사항을 입력하세요
                    </label>
                    <textarea
                      value={modifyText}
                      onChange={(e) => setModifyText(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-luminous-blue focus:border-luminous-blue"
                      rows={3}
                      placeholder="어떤 부분을 수정하고 싶으신가요?"
                    />
                    <div className="flex gap-2 mt-3">
                      <button
                        onClick={handleModify}
                        className="px-4 py-2 bg-luminous-blue text-white rounded-lg text-sm font-medium hover:bg-amore-blue"
                      >
                        에이전트에 전달
                      </button>
                      <button
                        onClick={() => {
                          setShowModifyInput(false);
                          setModifyText('');
                        }}
                        className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-50"
                      >
                        취소
                      </button>
                    </div>
                  </div>
                )}

                {/* 반려 사유 입력 박스 */}
                {showRejectInput && (
                  <div className="mt-6 p-4 bg-danger-bg rounded-lg">
                    <label className="block text-sm font-medium text-danger-dark mb-2">
                      반려 사유를 입력하세요
                    </label>
                    <textarea
                      value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                      className="w-full px-3 py-2 border border-danger/30 rounded-lg focus:ring-2 focus:ring-danger focus:border-danger"
                      rows={3}
                      placeholder="반려 사유를 구체적으로 입력해주세요"
                    />
                    <div className="flex gap-2 mt-3">
                      <button
                        onClick={handleReject}
                        className="px-4 py-2 bg-danger text-white rounded-lg text-sm font-medium hover:bg-danger-dark"
                      >
                        반려 확정
                      </button>
                      <button
                        onClick={() => {
                          setShowRejectInput(false);
                          setRejectReason('');
                        }}
                        className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-50"
                      >
                        취소
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* 우측 하단: 액션 버튼 */}
              <div className="p-6 border-t border-gray-200">
                <div className="flex gap-3">
                  <button
                    onClick={handleApprove}
                    disabled={!isActionEnabled}
                    className={`flex-1 py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-all ${
                      isActionEnabled
                        ? 'bg-success text-white hover:bg-success-dark'
                        : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    <CheckCircle className="w-5 h-5" />
                    승인
                  </button>
                  <button
                    onClick={() => setShowModifyInput(!showModifyInput)}
                    disabled={!isActionEnabled}
                    className={`flex-1 py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-all ${
                      isActionEnabled
                        ? 'bg-gray-600 text-white hover:bg-gray-700'
                        : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    <Edit2 className="w-5 h-5" />
                    수정
                  </button>
                  <button
                    onClick={() => setShowRejectInput(!showRejectInput)}
                    disabled={!isActionEnabled}
                    className={`flex-1 py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-all ${
                      isActionEnabled
                        ? 'bg-danger text-white hover:bg-danger-dark'
                        : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    <XCircle className="w-5 h-5" />
                    반려
                  </button>
                </div>
                {!isActionEnabled && selectedItem.choices && (
                  <p className="text-xs text-gray-500 text-center mt-3">
                    방향을 선택하면 버튼이 활성화됩니다
                  </p>
                )}
              </div>
            </div>
          ) : activeTab === 'history' ? null : (
            <div className="flex items-center justify-center h-full text-gray-400">
              <p>항목을 선택하여 상세 정보를 확인하세요</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};