import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../app/store';
import { Button, Table } from '../common';
import { Coins, TrendingUp, AlertCircle, Download } from 'lucide-react';
import type { TableColumn } from '../common';

export const TokenUsageTab: React.FC = () => {
  const tokenUsage = useSelector((state: RootState) => state.settings.tokenUsage);

  const usagePercentage = (tokenUsage.usedTokens / tokenUsage.totalTokens) * 100;
  const isWarning = usagePercentage >= 80;
  const isDanger = usagePercentage >= 90;

  const columns: TableColumn<typeof tokenUsage.usageHistory[0]>[] = [
    {
      key: 'date',
      label: '날짜',
      render: (value) => (
        <span className="text-sm text-gray-900">{value}</span>
      ),
    },
    {
      key: 'feature',
      label: '기능',
      render: (value) => (
        <span className="px-2 py-1 text-xs bg-gray-100 rounded-full">
          {value}
        </span>
      ),
    },
    {
      key: 'description',
      label: '상세 내용',
      render: (value) => (
        <span className="text-sm text-gray-600">{value}</span>
      ),
    },
    {
      key: 'tokens',
      label: '토큰 사용량',
      align: 'right',
      render: (value) => (
        <span className="text-sm font-medium">{value.toLocaleString()}</span>
      ),
    },
  ];

  const featureUsage = [
    { feature: '소재 자동 생성', tokens: 25000, percentage: 38 },
    { feature: '리포트 생성', tokens: 15000, percentage: 23 },
    { feature: '예산 최적화', tokens: 12000, percentage: 18 },
    { feature: '채널 분석', tokens: 8000, percentage: 12 },
    { feature: '기타', tokens: 5000, percentage: 9 },
  ];

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
          <Coins className="w-5 h-5" />
          토큰 사용량
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          AI 기능 사용에 따른 토큰 소비 현황을 확인합니다
        </p>
      </div>

      {/* 토큰 현황 카드 */}
      <div className="bg-white rounded-lg p-6 mb-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-sm font-medium text-gray-600 mb-1">토큰 잔여량</h3>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-gray-900">
                {tokenUsage.remainingTokens.toLocaleString()}
              </span>
              <span className="text-sm text-gray-500">
                / {tokenUsage.totalTokens.toLocaleString()}
              </span>
            </div>
          </div>

          {isWarning && (
            <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${
              isDanger ? 'bg-danger/10 text-danger' : 'bg-warning/10 text-warning'
            }`}>
              <AlertCircle className="w-4 h-4" />
              <span className="text-xs font-medium">
                {isDanger ? '토큰 부족' : '토큰 주의'}
              </span>
            </div>
          )}
        </div>

        {/* 프로그레스 바 */}
        <div className="mb-6">
          <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                isDanger ? 'bg-danger' : isWarning ? 'bg-warning' : 'bg-accent'
              }`}
              style={{ width: `${usagePercentage}%` }}
            />
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-xs text-gray-500">
              사용: {tokenUsage.usedTokens.toLocaleString()}
            </span>
            <span className="text-xs text-gray-500">
              {usagePercentage.toFixed(1)}%
            </span>
          </div>
        </div>

        {/* 경고 메시지 */}
        {isWarning && (
          <div className={`p-3 rounded-lg flex items-start gap-2 ${
            isDanger ? 'bg-danger/5' : 'bg-warning/5'
          }`}>
            <AlertCircle className={`w-4 h-4 flex-shrink-0 mt-0.5 ${
              isDanger ? 'text-danger' : 'text-warning'
            }`} />
            <div className="text-sm">
              <p className={`font-medium ${isDanger ? 'text-danger' : 'text-warning'}`}>
                {isDanger
                  ? '토큰이 90% 이상 소진되었습니다!'
                  : '토큰이 80% 이상 소진되었습니다.'}
              </p>
              <p className="text-gray-600 mt-1">
                추가 토큰 구매를 고려하시거나 사용량을 조절해주세요.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* 기능별 사용 현황 */}
      <div className="bg-white rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">기능별 사용 현황</h3>

        <div className="space-y-3">
          {featureUsage.map((item) => (
            <div key={item.feature} className="flex items-center gap-4">
              <div className="w-32 text-sm text-gray-600">{item.feature}</div>
              <div className="flex-1">
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent"
                    style={{ width: `${item.percentage}%` }}
                  />
                </div>
              </div>
              <div className="text-sm font-medium w-20 text-right">
                {item.tokens.toLocaleString()}
              </div>
              <div className="text-sm text-gray-500 w-12 text-right">
                {item.percentage}%
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 사용 내역 테이블 */}
      <div className="bg-white rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-900">최근 사용 내역</h3>
          <Button variant="secondary" size="sm">
            <Download className="w-4 h-4" />
            내역 다운로드
          </Button>
        </div>

        <Table
          columns={columns}
          data={tokenUsage.usageHistory}
        />
      </div>

      {/* 토큰 안내 */}
      <div className="mt-6 p-4 bg-info-bg rounded-lg">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">토큰 사용 안내</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• 토큰은 AI 기능 사용 시 자동으로 차감됩니다</li>
          <li>• 소재 생성, 리포트 작성 등 기능별로 차감량이 다릅니다</li>
          <li>• 토큰 소진 시 일부 AI 기능이 제한될 수 있습니다</li>
          <li>• 추가 토큰은 플랜/결제 탭에서 구매할 수 있습니다</li>
        </ul>
      </div>
    </div>
  );
};