/**
 * 연령 5세 bucket 분포 (11 bucket) + 핵심 35-44 합 — Segment Track.
 *
 * 정답: 40-44=1,455 / 35-39=1,429 (핵심 35-44 합 2,884)
 *
 * ChartFrame + BarChart, 핵심 bucket highlight.
 */
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { useMonthlyAge } from '@/api/hooks/useMonthlyData';
import {
  CHART_AXIS_TICK_PROPS,
  CHART_GRID_PROPS,
  CHART_TOOLTIP_STYLE,
  ChartFrame,
} from '@/components/viz/ChartFrame';
import { CHART } from '@/lib/chart';
import { formatNumber, formatPercent } from '@/lib/format';

const CORE_BUCKETS = new Set(['35-39', '40-44']);

function bucketSort(b: string): number {
  if (b === '65+') return 65;
  const m = /^(\d+)-/.exec(b);
  return m && m[1] ? parseInt(m[1], 10) : 999;
}

export function AgeBucketBar() {
  const { data, isLoading } = useMonthlyAge();

  const chartData = data
    ? Object.entries(data.table)
        .map(([bucket, row]) => ({
          bucket,
          count: row.count,
          core: CORE_BUCKETS.has(bucket),
        }))
        .sort((a, b) => bucketSort(a.bucket) - bucketSort(b.bucket))
    : [];

  const meta = data
    ? `${Object.keys(data.table).length} bucket · 회원 ${formatNumber(data.total_members)} · 핵심 35-44 ${formatNumber(data.core_segment_35_44)} (${formatPercent((data.core_segment_35_44 / data.total_members) * 100)})`
    : '연령 분포';

  return (
    <ChartFrame title="연령 5세 bucket 분포" meta={meta} height={240}>
      {isLoading ? (
        <div className="h-full animate-pulse rounded-sm bg-muted" />
      ) : (
        <BarChart data={chartData} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid {...CHART_GRID_PROPS} />
          <XAxis dataKey="bucket" tick={CHART_AXIS_TICK_PROPS} />
          <YAxis tick={CHART_AXIS_TICK_PROPS} tickFormatter={(v) => formatNumber(v)} />
          <Tooltip
            formatter={(v: number) => formatNumber(v)}
            contentStyle={CHART_TOOLTIP_STYLE}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {chartData.map((d) => (
              <Cell key={d.bucket} fill={d.core ? CHART[0] : CHART[2]} />
            ))}
          </Bar>
        </BarChart>
      )}
    </ChartFrame>
  );
}
