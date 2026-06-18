/**
 * TrendPage — 시계열 트렌드.
 *
 * 데이터 (2026-06-09 실데이터 배선): GET /api/dashboard1/trend-overview (Postgres 조립).
 *  - 일별 노출·전환·ROAS = daily_performance 날짜 집계
 *  - 목표선·BE선 = marketing_targets raw (대시보드와 동일)
 *  - 노출(수만) vs 전환(수십) 단위차 → 이중 축. ROAS 차트 = 목표선·손익분기선 기준.
 */
import { TrendingUp } from 'lucide-react';
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { PageHeader } from '@/components/layout/PageHeader';
import {
  CHART_AXIS_TICK_PROPS,
  CHART_GRID_PROPS,
  CHART_TOOLTIP_STYLE,
  ChartFrame,
  TARGET_LINE_LABEL_STYLE,
  TARGET_LINE_PROPS,
} from '@/components/viz/ChartFrame';
import { useCurrentClient } from '@/api/clients';
import { useTrendOverview } from '@/api/hooks/useTrendOverview';

const PERIOD = '2026-04';

function formatCompact(v: number): string {
  if (Math.abs(v) >= 10000) return `${(v / 10000).toFixed(1)}만`;
  if (Math.abs(v) >= 1000) return `${(v / 1000).toFixed(1)}K`;
  return String(v);
}

export function TrendPage() {
  const client = useCurrentClient();
  const { data, isLoading } = useTrendOverview(client, PERIOD);

  const daily = (data?.daily ?? []).map((d) => ({ ...d, date: d.date.slice(5) }));
  const targetRoas = data?.target_roas ?? null;
  const beRoas = data?.breakeven_roas ?? null;

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="트렌드"
        description={`일별 시계열 + 목표선 (단위 다른 계열은 이중 축)${client ? ` · ${client} ${PERIOD}` : ''}`}
        icon={TrendingUp}
      />

      {!client ? (
        <p className="text-sm text-muted-foreground">상단에서 client를 선택하세요.</p>
      ) : isLoading ? (
        <p className="text-sm text-muted-foreground">불러오는 중…</p>
      ) : daily.length === 0 ? (
        <p className="text-sm text-muted-foreground">데이터가 없습니다.</p>
      ) : (
        <>
          <ChartFrame title="일별 ROAS" meta={`${PERIOD} (${daily.length}일)`} height={300}>
            <LineChart data={daily} margin={{ top: 8, right: 60, bottom: 8, left: 8 }}>
              <CartesianGrid {...CHART_GRID_PROPS} />
              <XAxis dataKey="date" tick={CHART_AXIS_TICK_PROPS} />
              <YAxis tick={CHART_AXIS_TICK_PROPS} unit="%" />
              <Tooltip
                contentStyle={CHART_TOOLTIP_STYLE}
                formatter={(v: number) => [`${v}%`, 'ROAS']}
              />
              <Line dataKey="roas" stroke="hsl(var(--chart-1))" strokeWidth={2} dot={false} name="ROAS" />
              {targetRoas != null && (
                <ReferenceLine
                  y={targetRoas}
                  label={{ value: `목표 ${targetRoas}%`, position: 'right', ...TARGET_LINE_LABEL_STYLE }}
                  {...TARGET_LINE_PROPS}
                />
              )}
              {beRoas != null && (
                <ReferenceLine
                  y={beRoas}
                  label={{ value: `BE ${beRoas}%`, position: 'right', ...TARGET_LINE_LABEL_STYLE }}
                  {...TARGET_LINE_PROPS}
                  stroke="hsl(var(--destructive))"
                  strokeOpacity={0.4}
                />
              )}
            </LineChart>
          </ChartFrame>

          <ChartFrame
            title="일별 노출수 · 전환수"
            meta="단위 차이 큼 → 이중 축 분리"
            height={300}
          >
            <ComposedChart data={daily} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
              <CartesianGrid {...CHART_GRID_PROPS} />
              <XAxis dataKey="date" tick={CHART_AXIS_TICK_PROPS} />
              <YAxis
                yAxisId="left"
                tick={CHART_AXIS_TICK_PROPS}
                tickFormatter={formatCompact}
                label={{ value: '노출수', angle: -90, position: 'insideLeft', ...TARGET_LINE_LABEL_STYLE }}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={CHART_AXIS_TICK_PROPS}
                label={{ value: '전환수', angle: 90, position: 'insideRight', ...TARGET_LINE_LABEL_STYLE }}
              />
              <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar yAxisId="left" dataKey="impressions" fill="hsl(var(--chart-2))" opacity={0.5} name="노출수" />
              <Line yAxisId="right" dataKey="conversions" stroke="hsl(var(--chart-1))" strokeWidth={2} dot={false} name="전환수" />
            </ComposedChart>
          </ChartFrame>

          <div className="rounded-md bg-muted/40 px-4 py-3 text-2xs leading-relaxed text-muted-foreground">
            <p>
              <span className="font-medium text-foreground">읽는 법</span> — 노출(수만)과 전환(수십)은
              단위 차이가 커서 단일 축에 두면 전환이 깔림 → 좌(노출)/우(전환) 이중 축 분리. ROAS 차트는
              목표선·손익분기(BE)선이 좋다/나쁘다를 직접 말해줌.
            </p>
            <p className="mt-1">데이터: Postgres 실데이터 ({data?.client} {data?.period}).</p>
          </div>
        </>
      )}
    </div>
  );
}
