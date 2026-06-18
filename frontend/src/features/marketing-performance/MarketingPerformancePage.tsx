/**
 * MarketingPerformancePage — World-A canonical 정형 테이블 첫 수직 슬라이스.
 *
 * clumi.blended_computed + *_normalized → /api/canonical/marketing-performance → 본 페이지.
 * 광고(ROAS)와 메시징(ROI)은 결을 분리 표기 (C6.3 — ROI≠ROAS, 동일 축 비교 금지).
 * 컴포넌트 재사용: PageHeader·KpiCard·ChartFrame·DataTable (월간 결산 톤 답습).
 */
import { useState, type ReactNode } from 'react';
import { Target } from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { useMarketingPerformance } from '@/api/hooks/useMarketingPerformance';
import { KpiCard } from '@/components/layout/KpiCard';
import { PageHeader } from '@/components/layout/PageHeader';
import {
  CHART_AXIS_TICK_PROPS,
  CHART_GRID_PROPS,
  CHART_TOOLTIP_STYLE,
  ChartFrame,
} from '@/components/viz/ChartFrame';
import { MetricChainStrip } from '@/components/viz/MetricChainStrip';
import { DataTable, type DataTableColumn } from '@/components/viz/DataTable';
import { cn } from '@/lib/cn';
import { CURRENT_PERIOD, periodLabel } from '@/features/monthly/periods';
import {
  CHANNEL_FILL,
  channelLabel,
  type AdChannelPerf,
  type CampaignPerf,
  type MsgChannelPerf,
} from './types';
import { formatCurrency, formatNumber, formatPercent } from '@/lib/format';

const compact = (v: number) =>
  new Intl.NumberFormat('ko-KR', { notation: 'compact' }).format(v);
const roasText = (v: unknown) => (v == null ? '—' : `${(v as number).toFixed(2)}x`);

const AD_COLUMNS: DataTableColumn<AdChannelPerf>[] = [
  { key: 'channel', label: '채널', sortable: false, format: (v) => channelLabel(String(v)) },
  { key: 'ad_cost_krw', label: '광고비', align: 'right', bar: {}, format: (v) => formatCurrency(v as number) },
  { key: 'roas_x', label: 'ROAS', align: 'right', format: roasText, heat: { direction: 'high', goodAt: 4, badAt: 1 } },
  { key: 'ctr_pct', label: 'CTR', align: 'right', format: (v) => formatPercent(v as number, 2) },
  { key: 'cpc_krw', label: 'CPC', align: 'right', format: (v) => (v == null ? '—' : formatCurrency(v as number)) },
  { key: 'cvr_pct', label: 'CVR', align: 'right', format: (v) => formatPercent(v as number, 2) },
  { key: 'conversion_count', label: '전환', align: 'right', format: (v) => formatNumber(v as number) },
];

const CAMPAIGN_COLUMNS: DataTableColumn<CampaignPerf>[] = [
  { key: 'channel', label: '채널', sortable: false, format: (v) => channelLabel(String(v)) },
  { key: 'campaign_id', label: '캠페인', sortable: false, format: (v, row) => row.campaign_name || String(v) },
  { key: 'ad_cost_krw', label: '광고비', align: 'right', bar: {}, format: (v) => formatCurrency(v as number) },
  { key: 'roas_x', label: 'ROAS', align: 'right', format: roasText, heat: { direction: 'high', goodAt: 4, badAt: 1 } },
  { key: 'ctr_pct', label: 'CTR', align: 'right', format: (v) => formatPercent(v as number, 2) },
  { key: 'cvr_pct', label: 'CVR', align: 'right', format: (v) => formatPercent(v as number, 2) },
  { key: 'conversion_count', label: '전환', align: 'right', format: (v) => formatNumber(v as number) },
];

const MSG_COLUMNS: DataTableColumn<MsgChannelPerf>[] = [
  { key: 'channel', label: '채널', sortable: false, format: (v) => channelLabel(String(v)) },
  { key: 'msg_cost_krw', label: '발송비', align: 'right', bar: {}, format: (v) => formatCurrency(v as number) },
  { key: 'msg_target_count', label: '발송수', align: 'right', format: (v) => formatNumber(v as number) },
  { key: 'msg_conversion_count', label: '전환', align: 'right', format: (v) => formatNumber(v as number) },
  { key: 'msg_conversion_revenue_krw', label: '전환매출', align: 'right', format: (v) => formatCurrency(v as number) },
  { key: 'msg_roi_pct', label: 'ROI', align: 'right', format: (v) => formatPercent(v as number, 1) },
];

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'rounded-md px-2.5 py-1 text-xs font-medium transition',
        active ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:text-foreground',
      )}
    >
      {children}
    </button>
  );
}

function SectionTable<T extends Record<string, unknown>>({
  title,
  note,
  columns,
  rows,
  footerSum,
  defaultSortKey,
  actions,
}: {
  title: string;
  note?: string;
  columns: DataTableColumn<T>[];
  rows: T[];
  footerSum?: string[];
  defaultSortKey?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between gap-3">
        <div className="flex items-baseline gap-3">
          <h2 className="text-sm font-semibold text-foreground">{title}</h2>
          {note && <span className="text-xs text-muted-foreground">{note}</span>}
        </div>
        {actions && <div className="flex shrink-0 items-center gap-1">{actions}</div>}
      </div>
      <DataTable
        columns={columns}
        rows={rows}
        defaultSort={{ key: defaultSortKey ?? columns[1]!.key, desc: true }}
        footerSum={footerSum}
      />
    </div>
  );
}

export function MarketingPerformancePage() {
  const period = CURRENT_PERIOD;
  const { data, isLoading, error } = useMarketingPerformance(period);
  const [channelFilter, setChannelFilter] = useState<string | null>(null);

  const kpi = data?.kpi;
  const adChannels = data?.ad_channels ?? [];
  const campaigns = data?.campaigns ?? [];
  const msgChannels = data?.msg_channels ?? [];
  const daily = data?.daily ?? [];
  const barData = adChannels.map((c) => ({ ...c, name: channelLabel(c.channel) }));

  // 광고 합산 — 전환 사슬(노출→클릭→전환→전환매출, 광고 universe 일관)
  const t = adChannels.reduce(
    (a, c) => ({
      imp: a.imp + c.impressions,
      clk: a.clk + c.clicks,
      conv: a.conv + c.conversion_count,
      rev: a.rev + c.conversion_revenue_krw,
    }),
    { imp: 0, clk: 0, conv: 0, rev: 0 },
  );
  const pct = (n: number, d: number) => (d ? `${((n / d) * 100).toFixed(2)}%` : '-');
  const chainNodes = [
    { label: '노출', value: formatNumber(t.imp) },
    { label: '클릭', value: formatNumber(t.clk) },
    { label: '전환', value: formatNumber(t.conv) },
    { label: '전환매출', value: formatCurrency(t.rev) },
  ];
  const chainTransitions = [
    { label: 'CTR', value: pct(t.clk, t.imp) },
    { label: 'CVR', value: pct(t.conv, t.clk) },
    { label: '객단가', value: formatCurrency(t.conv ? Math.round(t.rev / t.conv) : 0) },
  ];

  const filteredCampaigns = channelFilter
    ? campaigns.filter((c) => c.channel === channelFilter)
    : campaigns;

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="마케팅 성과"
        description={`${periodLabel(period)} · canonical 정형 데이터 직접 연결`}
        icon={Target}
        badge="canonical"
      />

      {error && (
        <p className="text-sm text-destructive">데이터를 불러오지 못했습니다. (백엔드/적재 확인)</p>
      )}

      {/* KPI strip — blended_computed */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <KpiCard label="MER" value={kpi?.mer != null ? `${kpi.mer.toFixed(2)}x` : '-'} sub="전체매출 ÷ 마케팅비" loading={isLoading} />
        <KpiCard label="총 마케팅비" value={kpi ? formatCurrency(kpi.total_marketing_cost_krw) : '-'} sub="광고 + 메시징" loading={isLoading} />
        <KpiCard label="총 매출" value={kpi ? formatCurrency(kpi.total_order_revenue_krw) : '-'} loading={isLoading} />
        <KpiCard label="TACoS" value={kpi ? formatPercent(kpi.tacos_pct) : '-'} sub="광고비 ÷ 매출" loading={isLoading} />
      </div>

      {/* 전환 사슬 — 노출 →CTR→ 클릭 →CVR→ 전환 →객단가→ 전환매출 (광고 합산) */}
      {adChannels.length > 0 && (
        <MetricChainStrip nodes={chainNodes} transitions={chainTransitions} />
      )}

      {/* 채널별 광고비 + ROAS 비교 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartFrame title="채널별 광고비" meta={periodLabel(period)} height={260}>
          <BarChart data={barData} margin={{ top: 8, right: 8, bottom: 4, left: 8 }}>
            <CartesianGrid {...CHART_GRID_PROPS} vertical={false} />
            <XAxis dataKey="name" tick={CHART_AXIS_TICK_PROPS} />
            <YAxis tick={CHART_AXIS_TICK_PROPS} tickFormatter={(v) => compact(v as number)} width={48} />
            <Tooltip contentStyle={CHART_TOOLTIP_STYLE} formatter={(v) => formatCurrency(v as number)} />
            <Bar dataKey="ad_cost_krw" radius={[4, 4, 0, 0]}>
              {barData.map((c) => (
                <Cell key={c.channel} fill={CHANNEL_FILL[c.channel] ?? 'hsl(var(--chart-1))'} />
              ))}
            </Bar>
          </BarChart>
        </ChartFrame>

        <ChartFrame title="채널 ROAS 비교" meta="전환매출 ÷ 광고비" height={260}>
          <BarChart data={barData} margin={{ top: 8, right: 8, bottom: 4, left: 8 }}>
            <CartesianGrid {...CHART_GRID_PROPS} vertical={false} />
            <XAxis dataKey="name" tick={CHART_AXIS_TICK_PROPS} />
            <YAxis tick={CHART_AXIS_TICK_PROPS} tickFormatter={(v) => `${(v as number).toFixed(1)}x`} width={40} />
            <Tooltip contentStyle={CHART_TOOLTIP_STYLE} formatter={(v) => roasText(v)} />
            <Bar dataKey="roas_x" radius={[4, 4, 0, 0]}>
              {barData.map((c) => (
                <Cell key={c.channel} fill={CHANNEL_FILL[c.channel] ?? 'hsl(var(--chart-1))'} />
              ))}
            </Bar>
          </BarChart>
        </ChartFrame>
      </div>

      {/* 일별 ROAS 추이 (전폭) */}
      <ChartFrame title="일별 ROAS 추이" meta="광고 매체 합산 (전환매출 ÷ 광고비)" height={260}>
        <LineChart data={daily} margin={{ top: 8, right: 8, bottom: 4, left: 8 }}>
          <CartesianGrid {...CHART_GRID_PROPS} vertical={false} />
          <XAxis dataKey="report_date" tick={CHART_AXIS_TICK_PROPS} tickFormatter={(d) => String(d).slice(5)} />
          <YAxis tick={CHART_AXIS_TICK_PROPS} tickFormatter={(v) => `${(v as number).toFixed(1)}x`} width={48} />
          <Tooltip contentStyle={CHART_TOOLTIP_STYLE} formatter={(v) => roasText(v)} />
          <Line type="monotone" dataKey="roas_x" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
        </LineChart>
      </ChartFrame>

      {/* 광고 매체 성과 표 */}
      <SectionTable
        title="광고 매체 성과"
        note="ROAS = 전환매출 ÷ 광고비"
        columns={AD_COLUMNS}
        rows={adChannels}
        footerSum={['ad_cost_krw', 'conversion_count']}
      />

      {/* 캠페인 성과 드릴다운 (채널 필터) */}
      <SectionTable
        title="캠페인 성과"
        note="채널·캠페인 단위 드릴다운"
        columns={CAMPAIGN_COLUMNS}
        rows={filteredCampaigns}
        footerSum={['ad_cost_krw', 'conversion_count']}
        defaultSortKey="ad_cost_krw"
        actions={
          <>
            <FilterChip active={channelFilter == null} onClick={() => setChannelFilter(null)}>
              전체
            </FilterChip>
            {adChannels.map((c) => (
              <FilterChip
                key={c.channel}
                active={channelFilter === c.channel}
                onClick={() => setChannelFilter(c.channel)}
              >
                {channelLabel(c.channel)}
              </FilterChip>
            ))}
          </>
        }
      />

      {/* 메시징 성과 표 — 광고와 분리 (C6.3) */}
      <SectionTable
        title="메시징 성과"
        note="ROI ≠ ROAS — 광고 ROAS와 직접 비교 금지"
        columns={MSG_COLUMNS}
        rows={msgChannels}
        footerSum={['msg_cost_krw', 'msg_conversion_count']}
      />
    </div>
  );
}
