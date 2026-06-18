import React from 'react';
import { ChevronDown, Bell, Calendar, MessageCircle } from 'lucide-react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState, store } from '../../app/store';
import { selectClient } from '../../features/client/clientSlice';
import { selectPendingCount } from '../../features/hitl/hitlSlice';
import { toggleChatPanel } from '../../features/chatPanel/chatPanelSlice';
import { selectPortfolio, selectClient as selectNavigationClient } from '../../features/navigation/navigationSlice';
import { useNavigate } from 'react-router-dom';
import { DateRangePicker } from '../common';

// NotifList 인라인 컴포넌트
const NotifList = ({ onClose }: { onClose: () => void }) => {
  const navigate = useNavigate();
  const hitlItems = useSelector((state: RootState) =>
    state.hitl.items.filter(i => i.status === 'pending' || i.status === 'delayed')
  );
  const clientData = useSelector((state: RootState) => state.client.currentClientData);
  const aiInsights = clientData?.insights || [];

  const urgencyStyle = (urgency: string) => {
    if (urgency === 'critical') return 'border-l-4 border-l-red-500 bg-red-50/30';
    if (urgency === 'warning') return 'border-l-4 border-l-amber-400 bg-amber-50/20';
    return 'border-l-4 border-l-blue-400 bg-blue-50/10';
  };

  const urgencyIcon = (urgency: string) => {
    if (urgency === 'critical') return '🚨';
    if (urgency === 'warning') return '🤔';
    return '📊';
  };

  // AI Insights 배경색
  const insightStyle = (type: string) => {
    if (type === 'danger') return 'bg-danger-bg';
    if (type === 'warning') return 'bg-warning-bg';
    return 'bg-info-bg';
  };

  const insightIcon = (type: string) => {
    if (type === 'danger') return '🚨';
    if (type === 'warning') return '⚠️';
    return 'ℹ️';
  };

  return (
    <div className="max-h-96 overflow-y-auto">
      {/* AI Insights 섹션 */}
      {aiInsights && aiInsights.length > 0 && (
        <div className="border-b border-gray-100">
          <p className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase">AI 인사이트</p>
          {aiInsights.map((insight, idx) => (
            <div
              key={idx}
              onClick={() => {
                if (insight.type === 'danger' && insight.title.includes('메타')) navigate('/creatives');
                else if (insight.type === 'warning' && insight.title.includes('카카오')) navigate('/analysis');
                else navigate('/dashboard');
                onClose();
              }}
              className={`px-4 py-3 cursor-pointer hover:brightness-95 transition-all ${insightStyle(insight.type)}`}
            >
              <div className="flex items-start gap-2">
                <span className="text-base flex-shrink-0">{insightIcon(insight.type)}</span>
                <div className="flex-1">
                  <p className="text-sm font-medium">{insight.title}</p>
                  <p className="text-xs text-gray-600 mt-0.5">{insight.description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 사용자 개입 대기 항목 섹션 */}
      <div className="divide-y divide-gray-100">
        <p className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase">사용자 개입 대기</p>
        {hitlItems.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-6">대기 항목이 없어요</p>
        ) : (
          hitlItems.map(item => (
          <div
            key={item.id}
            onClick={() => { navigate('/hitl'); onClose(); }}
            className={`px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors ${urgencyStyle(item.urgency)}`}
          >
            <div className="flex items-start gap-2">
              <span className="text-base flex-shrink-0">{urgencyIcon(item.urgency)}</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{item.title}</p>
                {item.consequence && (
                  <p className="text-xs text-gray-500 mt-0.5 truncate">{item.consequence}</p>
                )}
                <p className="text-xs text-gray-400 mt-1">
                  {item.waitMinutes < 60
                    ? `${item.waitMinutes}분 대기`
                    : `${Math.floor(item.waitMinutes / 60)}시간 대기`}
                </p>
              </div>
            </div>
          </div>
          ))
        )}
      </div>

      {/* 전체 보기 링크 */}
      <div
        onClick={() => { navigate('/hitl'); onClose(); }}
        className="px-4 py-3 text-center text-sm text-accent font-medium cursor-pointer hover:bg-info-bg border-t border-gray-100"
      >
        사용자 개입 센터에서 전체 보기 →
      </div>
    </div>
  );
};

export const TopBar: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { selectedClient, clientList } = useSelector((state: RootState) => state.client);
  const pendingCount = useSelector(selectPendingCount);
  const isChatOpen = useSelector((state: RootState) => state.chatPanel.isOpen);
  const currentTab = useSelector((state: RootState) => state.navigation.currentTab);
  const authUser = useSelector((state: RootState) => state.auth.user);
  const userRole = useSelector((state: RootState) => state.auth.role);
  const [showDropdown, setShowDropdown] = React.useState(false);
  const [showNotif, setShowNotif] = React.useState(false);

  // 날짜 범위 상태 관리
  const [dateRange, setDateRange] = React.useState({
    start: new Date(new Date().getFullYear(), new Date().getMonth(), 1), // 이번 달 1일
    end: new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0) // 이번 달 마지막 날
  });

  // 에이전트 탭이 활성화되어 있는지 확인
  const isAgentTabActive = currentTab === 'agent';

  const today = new Date().toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return (
    <div className="h-16 bg-white border-b border-gray-200 px-6 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <img
            src="/adallpin_original.png"
            alt="ADALLPIN"
            className="w-8 h-8 object-contain"
          />
          <h1 className="text-xl font-bold text-gray-900">ADALLPIN</h1>
        </div>

        <div className="relative">
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            {selectedClient === '전체 포트폴리오' && <span className="text-lg mr-1">📊</span>}
            <span className="font-medium">{selectedClient}</span>
            <ChevronDown className="w-4 h-4" />
          </button>

          {showDropdown && (
            <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
              <button
                onClick={() => {
                  dispatch(selectClient('전체 포트폴리오'));
                  dispatch(selectPortfolio());
                  navigate('/portfolio');
                  setShowDropdown(false);
                }}
                className={`w-full text-left px-4 py-3 hover:bg-gray-50 font-medium flex items-center gap-2 ${
                  selectedClient === '전체 포트폴리오' ? 'bg-info-bg text-accent' : ''
                }`}
              >
                <span className="text-lg">📊</span>
                전체 포트폴리오
              </button>
              <div className="border-t border-gray-200 my-1"></div>
              {clientList.map(client => (
                <button
                  key={client}
                  onClick={() => {
                    dispatch(selectClient(client));
                    dispatch(selectNavigationClient({ id: client, name: client }));
                    setShowDropdown(false);

                    // navigation 상태 갱신 후 적절한 경로로 이동
                    setTimeout(() => {
                      const navigation = store.getState().navigation;
                      const currentTab = navigation.currentTab;
                      const availableTab = navigation.availableTabs.find(tab => tab.id === currentTab);

                      if (availableTab) {
                        navigate(availableTab.path);
                      } else {
                        // 현재 탭이 새 컨텍스트에 없으면 대시보드로
                        navigate('/dashboard');
                      }
                    }, 0);
                  }}
                  className={`w-full text-left px-4 py-2 hover:bg-gray-50 ${
                    client === selectedClient ? 'bg-info-bg text-accent' : ''
                  }`}
                >
                  {client}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 날짜 피커 - 전체 포트폴리오가 아닐 때만 표시 */}
        {selectedClient !== '전체 포트폴리오' && (
          <DateRangePicker
            startDate={dateRange.start}
            endDate={dateRange.end}
            onDateChange={(start, end) => {
              setDateRange({ start, end });
              // TODO: 실제 데이터 필터링 로직 추가
              console.log('Date range changed:', start, end);
            }}
          />
        )}
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Calendar className="w-4 h-4" />
          {today}
        </div>

        {/* 사용자 정보 표시 */}
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 bg-blue-500 text-white text-sm font-medium rounded-full">
            {authUser?.name || '강지수'}
          </span>
          <span className={`px-3 py-1 text-xs font-medium rounded-full ${
            userRole === 'director' || userRole === 'ceo'
              ? 'bg-purple-500 text-white'
              : userRole === 'performance'
              ? 'bg-green-500 text-white'
              : 'bg-gray-500 text-white'
          }`}>
            {userRole === 'director' ? 'Director' :
             userRole === 'ceo' ? 'CEO' :
             userRole === 'performance' ? 'Performance' : 'AE'}
          </span>
        </div>

        {/* Chat Icon Button */}
        <button
          onClick={() => {
            if (!isAgentTabActive) {
              dispatch(toggleChatPanel());
            }
          }}
          className={`relative p-2 rounded-lg transition-colors ${
            isAgentTabActive
              ? 'opacity-50 cursor-not-allowed bg-gray-50'
              : isChatOpen
              ? 'bg-info-bg text-accent hover:bg-info-bg'
              : 'hover:bg-gray-100 text-gray-600'
          }`}
          title={isAgentTabActive ? "에이전트 탭에서는 사용할 수 없습니다" : "AI Assistant"}
          disabled={isAgentTabActive}
        >
          <MessageCircle className="w-5 h-5" />
          {!isAgentTabActive && (
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-success rounded-full animate-pulse" />
          )}
        </button>

        <div className="relative">
          <button
            onClick={() => setShowNotif(!showNotif)}
            className="relative p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Bell className="w-5 h-5 text-gray-600" />
            {pendingCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 w-5 h-5 bg-danger text-white text-xs
                               rounded-full flex items-center justify-center font-semibold
                               animate-pulse border-2 border-white">
                {pendingCount}
              </span>
            )}
          </button>

          {/* 알림 드롭다운 */}
          {showNotif && (
            <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-xl
                            border border-gray-200 z-50 overflow-hidden">
              <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
                <p className="text-sm font-semibold">AI가 기다리고 있어요</p>
                <span className="text-xs text-gray-500">{pendingCount}건 미확인</span>
              </div>
              <NotifList onClose={() => setShowNotif(false)} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};