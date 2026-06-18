/**
 * DashboardPage — 마케팅 퍼널 + ROAS 진단 (목표 대비).
 *
 * 데이터 (2026-06-09 실데이터 배선): GET /api/dashboard1/overview (Postgres 조립).
 *  - 퍼널/비율 = daily_performance·orders 실측, 목표 = marketing_targets raw.
 *  - ROAS = 광고성과(전환매출÷광고비), 일별 라인과 동일 기준.
 *  - MetricChainStrip + 일별 ROAS 라인(목표선·BE선) 시각화는 그대로.
 */
import { Home } from 'lucide-react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { PageHeader } from '@/components/layout/PageHeader';
import {
  MetricChainStrip,
  type MetricChainNode,
  type MetricChainTransition,
  type MetricTarget,
  type TargetStatus,
} from '@/components/viz/MetricChainStrip';
import {
  CHART_AXIS_TICK_PROPS,
  CHART_GRID_PROPS,
  CHART_TOOLTIP_STYLE,
  ChartFrame,
  TARGET_LINE_LABEL_STYLE,
  TARGET_LINE_PROPS,
} from '@/components/viz/ChartFrame';
import { useCurrentClient } from '@/api/clients';
import { useDashboardOverview, type DashboardOverview } from '@/api/hooks/useDashboardOverview';

// 전역 기간 선택기 도입 전 임시 (월간결산 CURRENT_PERIOD 와 동일)
const PERIOD = '2026-04';

const nf = (n: number) => n.toLocaleString('ko-KR');
const compact = (n: number) =>
  n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `${Math.round(n / 1e3)}K` : `${n}`;
const krwM = (n: number) => `₩${(n / 1e6).toFixed(1)}M`;

function statusOf(actual: number, target: number | undefined): TargetStatus | undefined {
  if (target == null) return undefined;
  return actual >= target ? 'above' : 'below';
}

function tgt(label: string, actual: number, target: number | undefined): MetricTarget | undefined {
  const s = statusOf(actual, target);
  return s ? { label, status: s } : undefined;
}

function buildNodes(d: DashboardOverview): MetricChainNode[] {
  const { funnel: f, targets: t, ratios: r } = d;
  return [
    {
      label: '노출수',
      value: nf(f.impressions),
      target: tgt(`목표 ${t.target_impressions ? compact(t.target_impressions) : '-'}`, f.impressions, t.target_impressions),
    },
    {
      label: '클릭수',
      value: nf(f.clicks),
      target: tgt(`목표 ${t.target_clicks ? compact(t.target_clicks) : '-'}`, f.clicks, t.target_clicks),
    },
    {
      label: '전환수',
      value: nf(f.conversions),
      target: tgt(`목표 ${t.target_conversions ? nf(t.target_conversions) : '-'}`, f.conversions, t.target_conversions),
    },
    {
      label: '전환매출',
      value: krwM(f.conversion_revenue),
      target: tgt(`ROAS ${r.roas}% (목표 ${t.target_roas ?? '-'}%)`, r.roas, t.target_roas),
    },
  ];
}

function buildTransitions(d: DashboardOverview): MetricChainTransition[] {
  const { ratios: r, targets: t } = d;
  return [
    { label: 'CTR', value: `${r.ctr}%`, target: tgt(`목표 ${t.target_ctr ?? '-'}%`, r.ctr, t.target_ctr) },
    { label: 'CVR', value: `${r.cvr}%`, target: tgt(`목표 ${t.target_cvr ?? '-'}%`, r.cvr, t.target_cvr) },
    { label: '객단가', value: `₩${nf(r.aov)}` },
  ];
}

export function DashboardPage() {
  const client = useCurrentClient();
  const { data, isLoading } = useDashboardOverview(client, PERIOD);

  const daily = (data?.daily ?? []).map((x) => ({ date: x.date.slice(5), roas: x.roas }));
  const targetRoas = data?.targets.target_roas ?? null;
  const beRoas = data?.targets.breakeven_roas ?? null;

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="대시보드"
        description={`마케팅 퍼널 + ROAS 진단 (목표 대비)${client ? ` · ${client} ${PERIOD}` : ''}`}
        icon={Home}
      />

      {!client ? (
        <p className="text-sm text-muted-foreground">상단에서 client를 선택하세요.</p>
      ) : isLoading ? (
        <p className="text-sm text-muted-foreground">불러오는 중…</p>
      ) : !data ? (
        <p className="text-sm text-muted-foreground">데이터가 없습니다.</p>
      ) : (
        <>
          <MetricChainStrip nodes={buildNodes(data)} transitions={buildTransitions(data)} />

          <ChartFrame title="일별 ROAS" meta={`${PERIOD} (${daily.length}일)`} height={260}>
            <LineChart data={daily} margin={{ top: 8, right: 60, bottom: 8, left: 8 }}>
              <CartesianGrid {...CHART_GRID_PROPS} />
              <XAxis dataKey="date" tick={CHART_AXIS_TICK_PROPS} />
              <YAxis tick={CHART_AXIS_TICK_PROPS} unit="%" />
              <Tooltip
                contentStyle={CHART_TOOLTIP_STYLE}
                formatter={(v: number) => [`${v}%`, 'ROAS']}
              />
              <Line
                dataKey="roas"
                stroke="hsl(var(--chart-1))"
                strokeWidth={2}
                dot={false}
                name="ROAS"
              />
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

          <div className="rounded-md bg-muted/40 px-4 py-3 text-2xs leading-relaxed text-muted-foreground">
            <p>
              <span className="font-medium text-foreground">읽는 법</span> — 퍼널 각 단계의
              목표 미달(빨강)을 따라가면 병목이 보입니다. 일별 ROAS 라인은 목표선 · 손익분기(BE)선 대비 추이.
            </p>
            <p className="mt-1">데이터: Postgres 실데이터 ({data.client} {data.period}).</p>
          </div>
        </>
      )}
    </div>
  );
}
