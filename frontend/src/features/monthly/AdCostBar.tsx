/**
 * 광고비 5매체 분배 (가로 막대) — Marketing Track 투입.
 *
 * 정답: Meta 9.2M · NaverSA 6.0M · ADVoost 3.0M · Kakao 59K · Talktalk 12K (합 18.3M)
 *
 * ChartFrame + recharts BarChart (vertical layout = 가로 막대).
 */
import {
  Bar,
  BarChart,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { useMonthlyAdCost } from '@/api/hooks/useMonthlyData';
import {
  CHART_AXIS_TICK_PROPS,
  CHART_GRID_PROPS,
  CHART_TOOLTIP_STYLE,
  ChartFrame,
} from '@/components/viz/ChartFrame';
import { CHART } from '@/lib/chart';
import { formatCompact, formatCurrency } from '@/lib/format';

interface Props {
  period: string;
}

const LABEL: Record<string, string> = {
  meta: 'Meta',
  naver_sa: 'NaverSA',
  advoost: 'ADVoost',
  kakao: 'Kakao',
  talktalk: 'Talktalk',
};

export function AdCostBar({ period }: Props) {
  const { data, isLoading } = useMonthlyAdCost(period);

  const chartData = data
    ? Object.entries(data.by_channel)
        .map(([k, v]) => ({ channel: LABEL[k] ?? k, cost: v }))
        .sort((a, b) => b.cost - a.cost)
    : [];

  const meta = data ? `합 ${formatCurrency(data.total_cost)} · ${period}` : '5매체 합';

  return (
    <ChartFrame title="광고비 5매체 분배" meta={meta} height={240}>
      {isLoading ? (
        <div className="h-full animate-pulse rounded-sm bg-muted" />
      ) : (
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 8, right: 16, bottom: 8, left: 8 }}
        >
          <CartesianGrid {...CHART_GRID_PROPS} />
          <XAxis type="number" tick={CHART_AXIS_TICK_PROPS} tickFormatter={(v) => formatCompact(v)} />
          <YAxis type="category" dataKey="channel" tick={CHART_AXIS_TICK_PROPS} width={70} />
          <Tooltip
            formatter={(v: number) => formatCurrency(v)}
            contentStyle={CHART_TOOLTIP_STYLE}
          />
          <Bar dataKey="cost" fill={CHART[0]} radius={[0, 4, 4, 0]} />
        </BarChart>
      )}
    </ChartFrame>
  );
}
