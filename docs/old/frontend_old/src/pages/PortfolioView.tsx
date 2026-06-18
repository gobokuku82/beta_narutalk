import { useSelector } from 'react-redux';
import { RootState } from '../app/store';
import { KpiCard } from '../components/common/KpiCard';
import { Badge } from '../components/common/Badge';
import { AlertItem } from '../components/common/AlertItem';
import { AiTag } from '../components/common/AiTag';

export const PortfolioView: React.FC = () => {
  const { clients, teamMembers, totalOperatingBudget, totalRevenue, totalSavedHours } =
    useSelector((state: RootState) => state.portfolio);

  const getRiskDots = (score: number) => {
    return (
      <div className="flex items-center gap-0.5">
        {Array(5).fill(0).map((_, i) => (
          <div
            key={i}
            className={`w-2 h-2 rounded-full ${
              i < score
                ? score >= 4 ? 'bg-red-500' : score >= 3 ? 'bg-amber-500' : 'bg-yellow-400'
                : 'bg-gray-300'
            }`}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="p-6">
      {/* 상단 KPI 카드 */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard
          label="총 운용 광고비(MTD)"
          value={`₩${(totalOperatingBudget / 1000000).toFixed(0)}M`}
          subText="목표 ₩250M"
          trend="up"
          trendValue="87%"
        />
        <KpiCard
          label="대행 수수료 수익"
          value={`₩${(totalRevenue / 1000000).toFixed(1)}M`}
          subText="전월 대비 +12%"
          trend="up"
          trendValue="+₩2.1M"
        />
        <KpiCard
          label="포트폴리오 평균 MER"
          value={clients.reduce((sum, c) => sum + c.mer, 0) / clients.length || 0}
          subText="총매출 / 총광고비"
          trend="up"
          trendValue="+0.3"
          aiNote="간접 효과 포함 전체 효율"
        />
        <KpiCard
          label="AI 절감 추정 공수"
          value={`${totalSavedHours}시간`}
          subText="이번 달 누적"
          trend="up"
          trendValue="+28%"
        />
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* 클라이언트 포트폴리오 테이블 */}
        <div className="col-span-2 bg-white rounded-lg shadow border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold">클라이언트 포트폴리오</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">클라이언트</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">담당AE</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">ROAS</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">MER</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">LTV</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">목표대비</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">위험도</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">계약만료</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">상태</th>
                </tr>
              </thead>
              <tbody>
                {clients.map(client => {
                  const daysUntilExpiry = Math.floor((new Date(client.contractExpiry).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
                  const isExpiringSoon = daysUntilExpiry <= 30;

                  return (
                    <tr
                      key={client.id}
                      className={`border-b border-gray-100 hover:bg-gray-50 cursor-pointer ${
                        client.riskLevel === 'danger' ? 'bg-red-50' : ''
                      }`}
                    >
                      <td className="px-6 py-4 font-medium">{client.name}</td>
                      <td className="px-6 py-4">{client.ae}</td>
                      <td className="px-6 py-4 text-right font-semibold">
                        <span className={client.roas < 300 ? 'text-red-600' : ''}>
                          {client.roas}%
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className={client.mer >= 4.0 ? 'text-green-700 font-semibold' : client.mer < 3.0 ? 'text-red-600 font-semibold' : ''}>
                          {client.mer.toFixed(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <span>₩{(client.ltv / 1000).toFixed(0)}K</span>
                          <span className={client.ltvChange > 0 ? 'text-green-600' : 'text-red-600'}>
                            {client.ltvChange > 0 ? '↑' : '↓'}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className={client.roasVsTarget < 0 ? 'text-red-600' : 'text-green-600'}>
                          {client.roasVsTarget > 0 ? '+' : ''}{client.roasVsTarget}%
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex justify-center gap-0.5 text-xs">
                          {getRiskDots(client.riskScore)}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex flex-col items-center gap-1">
                          <span className={isExpiringSoon ? 'text-red-600 font-semibold' : 'text-gray-700'}>
                            {client.contractExpiry}
                          </span>
                          {isExpiringSoon && (
                            <Badge variant="danger" size="sm">
                              D-{daysUntilExpiry}
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <Badge
                          variant={
                            client.riskLevel === 'safe' ? 'success' :
                            client.riskLevel === 'warning' ? 'warning' : 'danger'
                          }
                        >
                          {client.riskLevel === 'safe' ? '안전' :
                           client.riskLevel === 'warning' ? '주의' : '위험'}
                        </Badge>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* 즉시 조치 필요 */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">즉시 조치 필요</h3>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-red-600 font-medium">3건 긴급</span>
              </div>
            </div>
            <div className="space-y-3">
              <div className="relative">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-red-500 to-red-400 rounded"></div>
                <div className="ml-3">
                  <AlertItem
                    type="danger"
                    title="클라이언트 B ROAS 급락"
                    description="목표 대비 -29%, 계약 갱신 위험"
                  />
                </div>
              </div>
              <div className="relative">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-red-500 to-red-400 rounded"></div>
                <div className="ml-3">
                  <AlertItem
                    type="danger"
                    title="클라이언트 H 계약 만료 임박"
                    description="D-14, ROAS 178% 미달"
                  />
                </div>
              </div>
              <div className="relative">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-amber-500 to-amber-400 rounded"></div>
                <div className="ml-3">
                  <AlertItem
                    type="warning"
                    title="클라이언트 C 예산 초과 집행"
                    description="일 예산 115% 소진, 조정 필요"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* 클라이언트별 수수료 기여도 */}
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">수수료 기여도 TOP 5</h3>
            <div className="space-y-3">
              {clients
                .slice()
                .sort((a, b) => b.revenue - a.revenue)
                .slice(0, 5)
                .map((client, index) => {
                  const maxRevenue = clients.reduce((max, c) => Math.max(max, c.revenue), 0);
                  const percentage = (client.revenue / maxRevenue) * 100;

                  return (
                    <div key={client.id}>
                      <div className="flex justify-between items-center text-sm mb-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-gray-500 w-4">{index + 1}</span>
                          <span className="font-medium truncate flex-1">{client.name}</span>
                        </div>
                        <span className="font-semibold text-gray-700">₩{(client.revenue / 1000000).toFixed(1)}M</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-2 rounded-full transition-all duration-500 ${
                            index === 0 ? 'bg-gradient-to-r from-blue-600 to-blue-700' :
                            index === 1 ? 'bg-gradient-to-r from-blue-500 to-blue-600' :
                            'bg-blue-400'
                          }`}
                          style={{ width: `${Math.min(percentage, 100)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        </div>
      </div>

      {/* 팀원별 운영 현황 */}
      <div className="mt-6 bg-white rounded-lg shadow border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold">팀원별 운영 현황</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-2 gap-4">
            {teamMembers.map(member => {
              const kpiRate = (member.kpiAchieved / member.kpiTotal) * 100;

              return (
                <div key={member.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-white shadow-md ${
                      kpiRate === 100 ? 'bg-gradient-to-br from-green-500 to-green-600' :
                      kpiRate >= 70 ? 'bg-gradient-to-br from-blue-500 to-blue-600' :
                      kpiRate >= 50 ? 'bg-gradient-to-br from-amber-500 to-amber-600' :
                      'bg-gradient-to-br from-red-500 to-red-600'
                    }`}>
                      {member.initials}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900">{member.name}</h4>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-gray-500">담당 {member.clientCount}개</span>
                        <span className="text-xs text-gray-400">|</span>
                        <span className="text-xs text-gray-600 font-medium">
                          {member.clients.slice(0, 2).join(', ')}
                          {member.clients.length > 2 && ` 외 ${member.clients.length - 2}개`}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-gray-50 rounded-lg p-2">
                        <p className="text-xs text-gray-500 mb-1">운용액</p>
                        <p className="text-base font-bold text-gray-900">₩{(member.operatingBudget / 1000000).toFixed(0)}M</p>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-2">
                        <p className="text-xs text-gray-500 mb-1">KPI 달성</p>
                        <div className="flex items-center gap-2">
                          <p className={`text-base font-bold ${
                            kpiRate === 100 ? 'text-green-600' :
                            kpiRate >= 70 ? 'text-blue-600' :
                            kpiRate >= 50 ? 'text-amber-600' : 'text-red-600'
                          }`}>
                            {member.kpiAchieved}/{member.kpiTotal}
                          </p>
                          <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                            kpiRate === 100 ? 'bg-green-100 text-green-700' :
                            kpiRate >= 70 ? 'bg-blue-100 text-blue-700' :
                            kpiRate >= 50 ? 'bg-amber-100 text-amber-700' :
                            'bg-red-100 text-red-700'
                          }`}>
                            {kpiRate.toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-1">
                          <span className="text-xs text-gray-500">AI 절감</span>
                          <span className="text-sm font-semibold text-green-600">{member.savedHours}h</span>
                          <AiTag />
                        </div>
                        {member.hitlDelayed > 0 && (
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                            <span className="text-xs text-red-600 font-medium">HITL {member.hitlDelayed}건 지연</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};