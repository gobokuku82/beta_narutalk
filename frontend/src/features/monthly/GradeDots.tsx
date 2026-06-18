/**
 * 등급 회원수 시계열 (4 시점) — Segment Track 의 LTV 곡선.
 *
 * 정답: 6,680 → 7,299 → 7,900 → 8,500 (4월말 SILVER 600·GOLD 28 첫 등장)
 *
 * ChartFrame + recharts LineChart. palette A2 (chart-1~5) + 공통 grid/axis/tooltip props.
 */
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { useMonthlyGradeTimeseries } from '@/api/hooks/useMonthlyData';
import {
  CHART_AXIS_TICK_PROPS,
  CHART_GRID_PROPS,
  CHART_TOOLTIP_STYLE,
  ChartFrame,
} from '@/components/viz/ChartFrame';
import { CHART } from '@/lib/chart';

const GRADE_KEYS = ['WELCOME', 'REGULAR', 'SILVER', 'GOLD', 'VIP'] as const;

export function GradeDots() {
  const { data, isLoading } = useMonthlyGradeTimeseries();

  const chartData = data?.timeline.map((snap) => ({
    date: snap.snapshot_date.slice(5),
    total: snap.total,
    ...Object.fromEntries(
      GRADE_KEYS.map((g) => [g, snap.grade_counts[g] ?? 0]),
    ),
  })) ?? [];

  const meta = data
    ? `${data.snapshot_count} 시점 · 최신 ${data.latest_snapshot?.total.toLocaleString()}명`
    : '등급 시계열';

  return (
    <ChartFrame title="등급 회원수 시계열" meta={meta} height={260}>
      {isLoading ? (
        <div className="h-full animate-pulse rounded-sm bg-muted" />
      ) : (
        <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
          <CartesianGrid {...CHART_GRID_PROPS} />
          <XAxis dataKey="date" tick={CHART_AXIS_TICK_PROPS} />
          <YAxis tick={CHART_AXIS_TICK_PROPS} />
          <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          <Line type="monotone" dataKey="total" stroke={CHART[0]} strokeWidth={2.5} dot={{ r: 4 }} name="합계" />
          <Line type="monotone" dataKey="WELCOME" stroke={CHART[1]} strokeWidth={1.5} dot={{ r: 2 }} name="WELCOME" />
          <Line type="monotone" dataKey="REGULAR" stroke={CHART[2]} strokeWidth={1.5} dot={{ r: 2 }} name="REGULAR" />
          <Line type="monotone" dataKey="SILVER" stroke={CHART[3]} strokeWidth={1.5} dot={{ r: 2 }} name="SILVER" />
          <Line type="monotone" dataKey="GOLD" stroke={CHART[4]} strokeWidth={1.5} dot={{ r: 2 }} name="GOLD" />
        </LineChart>
      )}
    </ChartFrame>
  );
}
