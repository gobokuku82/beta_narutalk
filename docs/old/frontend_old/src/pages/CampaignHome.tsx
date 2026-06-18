import { KpiSummaryRow } from '../components/campaign/KpiSummaryRow';
import { ChannelTable } from '../components/campaign/ChannelTable';
import { useSelector } from 'react-redux';
import { RootState } from '../app/store';
import { ChevronRight, Coins, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '../components/common/Badge';

export const CampaignHome: React.FC = () => {
  const navigate = useNavigate();
  const hitlItems = useSelector((state: RootState) => state.hitl.items);
  const clientData = useSelector((state: RootState) => state.client.currentClientData);
  const tokenUsage = useSelector((state: RootState) => state.settings.tokenUsage);

  const pendingHitlItems = hitlItems.filter(item =>
    item.status === 'pending' || item.status === 'delayed'
  ).slice(0, 3);

  // 토큰 사용률 계산
  const usagePercentage = (tokenUsage.usedTokens / tokenUsage.totalTokens) * 100;
  const isWarning = usagePercentage >= 80 && usagePercentage < 100;
  const isDanger = usagePercentage >= 100;

  return (
    <div className="p-6">
      {/* 토큰 잔여량 바 */}
      <div className="mb-4 bg-white rounded-lg shadow-sm p-3 border border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Coins className="w-4 h-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">토큰 사용량</span>
            <span className="text-sm text-gray-500">
              {tokenUsage.usedTokens.toLocaleString()} / {tokenUsage.totalTokens.toLocaleString()}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {isWarning && (
              <div className="flex items-center gap-1 text-warning">
                <AlertCircle className="w-3.5 h-3.5" />
                <span className="text-xs font-medium">잔여 {(100 - usagePercentage).toFixed(0)}%</span>
              </div>
            )}
            {isDanger && (
              <div className="flex items-center gap-1 text-danger">
                <AlertCircle className="w-3.5 h-3.5" />
                <span className="text-xs font-medium">토큰 소진</span>
              </div>
            )}
            <button
              onClick={() => navigate('/settings')}
              className="text-xs text-accent hover:underline"
            >
              토큰 구매 →
            </button>
          </div>
        </div>
        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              isDanger ? 'bg-danger' : isWarning ? 'bg-warning' : 'bg-accent'
            }`}
            style={{ width: `${Math.min(usagePercentage, 100)}%` }}
          />
        </div>
      </div>

      <KpiSummaryRow />

      {/* 매체별 현황 - 전체 너비 */}
      <div className="mb-6">
        <ChannelTable />
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* KPI 예측 */}
        <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-6">월 KPI 달성 예측</h3>
          <div className="space-y-6">
            <div>
              <div className="flex justify-between items-end mb-2">
                <span className="text-sm text-gray-600">전환 수</span>
                <div className="flex items-baseline gap-2">
                  <span className="text-lg font-bold text-accent">63%</span>
                  <span className="text-sm text-gray-500">달성</span>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
                <div className="bg-accent h-2.5 rounded-full transition-all duration-500" style={{ width: '63%' }} />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">현재 2,471건</span>
                <span className="text-xs text-gray-500">목표 3,920건</span>
              </div>
            </div>
            <div>
              <div className="flex justify-between items-end mb-2">
                <span className="text-sm text-gray-600">광고비</span>
                <div className="flex items-baseline gap-2">
                  <span className="text-lg font-bold text-success-dark">71%</span>
                  <span className="text-sm text-gray-500">소진</span>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
                <div className="bg-success h-2.5 rounded-full transition-all duration-500" style={{ width: '71%' }} />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">현재 ₩21.4M</span>
                <span className="text-xs text-gray-500">예산 ₩30M</span>
              </div>
            </div>
            <div>
              <div className="flex justify-between items-end mb-2">
                <span className="text-sm text-gray-600">ROAS</span>
                <div className="flex items-baseline gap-2">
                  <span className="text-lg font-bold text-success-dark">110%</span>
                  <span className="text-sm text-gray-500">초과달성 ✓</span>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2 overflow-hidden">
                <div className="bg-success h-2.5 rounded-full transition-all duration-500" style={{ width: '110%' }} />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">현재 385%</span>
                <span className="text-xs text-gray-500">목표 350%</span>
              </div>
            </div>
            <div className="pt-3 border-t border-gray-100">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500 font-medium">진행 상황</span>
                <div className="flex items-center gap-3">
                  {/* Circular progress indicator */}
                  <div className="relative w-12 h-12">
                    <svg className="transform -rotate-90 w-12 h-12">
                      <circle
                        cx="24"
                        cy="24"
                        r="20"
                        stroke="#E5E7EB"
                        strokeWidth="4"
                        fill="none"
                      />
                      <circle
                        cx="24"
                        cy="24"
                        r="20"
                        stroke="#4B5563"
                        strokeWidth="4"
                        fill="none"
                        strokeDasharray={`${2 * Math.PI * 20}`}
                        strokeDashoffset={`${2 * Math.PI * 20 * (1 - 0.55)}`}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-xs font-bold text-gray-700">55%</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-gray-900">17일 경과</p>
                    <p className="text-xs text-gray-500">31일 중</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* AI 인사이트 & 승인 대기 통합 섹션 */}
        <div className="bg-white rounded-lg shadow border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h3 className="text-lg font-semibold">알림 센터</h3>
            <button
              onClick={() => navigate('/hitl')}
              className="text-sm text-accent hover:text-accent flex items-center gap-1"
            >
              HITL 센터 <ChevronRight className="w-4 h-4" />
            </button>
          </div>
          <div className="p-6 space-y-4">
            {/* AI 인사이트 섹션 */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">AI 인사이트</h4>
              <div className="space-y-2">
                {clientData?.insights?.slice(0, 2).map((insight, index) => (
                  <div key={index} className={`p-3 rounded-lg border-l-4 ${
                    insight.type === 'danger' ? 'bg-danger-bg border-danger' :
                    insight.type === 'warning' ? 'bg-warning-bg border-warning' :
                    'bg-info-bg border-info'
                  }`}>
                    <p className={`text-sm font-medium ${
                      insight.type === 'danger' ? 'text-danger-dark' :
                      insight.type === 'warning' ? 'text-warning-dark' :
                      'text-accent'
                    }`}>{insight.title}</p>
                    <p className="text-xs text-gray-600 mt-1">{insight.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* 구분선 */}
            <hr className="border-gray-200" />

            {/* 승인 대기 섹션 */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">승인 대기 중 ({pendingHitlItems.length})</h4>
              <div className="space-y-3">
                {pendingHitlItems.length > 0 ? (
                  pendingHitlItems.map(item => (
                    <div key={item.id} className="flex items-start gap-3">
                      <Badge variant={item.type === 'creative' ? 'info' : item.type === 'budget' ? 'warning' : 'gray'} size="sm">
                        {item.type === 'creative' ? '소재' :
                         item.type === 'budget' ? '예산' :
                         item.type === 'report' ? '보고서' : '캠페인'}
                      </Badge>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{item.title}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          대기 {item.waitMinutes}분
                          {item.waitMinutes > 180 && (
                            <span className="text-danger ml-2">⚠ 지연</span>
                          )}
                        </p>
                      </div>
                      <button
                        onClick={() => navigate('/hitl')}
                        className="text-accent hover:text-accent"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-gray-500">대기 중인 항목이 없습니다</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};