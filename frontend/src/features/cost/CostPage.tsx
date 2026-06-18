/**
 * CostPage — 비용.
 *
 * 데이터 (2026-06-09 실데이터 배선): GET /api/dashboard1/cost-overview (Postgres 조립).
 *  - KPI(총예산·집행률·키워드ROAS) = cost_kpi_budget_total(K22)·cost_kpi_keyword_metrics(K24)
 *  - 채널 예산 비중 = cost_pie_channel_share(C09)
 *  - 키워드 ROI 표 = cost_table_keyword_top12(T07) (cpa 유도·qs←quality_score)
 *  - 예산 페이싱 = campaigns.budget + daily_performance.spent 조인 (실데이터 유도, mock 불요)
 */
import type { ReactNode } from 'react';
import { DollarSign, Percent, Target, Wallet } from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { KpiCard } from '@/components/layout/KpiCard';
import { ChartFrame } from '@/components/viz/ChartFrame';
import { DataTable, type DataTableColumn } from '@/components/viz/DataTable';
import { PacingWidget, type CampaignPacing } from '@/components/viz/PacingWidget';
import { useCurrentClient } from '@/api/clients';
import { useCostOverview } from '@/api/hooks/useCostOverview';

const PERIOD = '2026-04';

const krw = (n: number) => `₩${n.toLocaleString('ko-KR')}`;
const krwM = (n: number) => `₩${(n / 1e6).toFixed(0)}M`;

const CHANNEL_LABEL: Record<string, string> = {
  naver: '네이버', kakao: '카카오', meta: '메타', google: '구글',
};
const CHANNEL_COLOR: Record<string, string> = {
  naver: 'hsl(var(--channel-naver))',
  kakao: 'hsl(var(--channel-kakao))',
  meta: 'hsl(var(--channel-meta))',
  google: 'hsl(var(--channel-google))',
};

function ChannelTag({ ch }: { ch: string }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span
        aria-hidden
        className="h-2 w-2 rounded-full"
        style={{ background: CHANNEL_COLOR[ch] ?? 'hsl(var(--muted-foreground))' }}
      />
      <span className="text-xs">{CHANNEL_LABEL[ch] ?? ch}</span>
    </span>
  );
}

interface ChannelRow extends Record<string, unknown> {
  channel: string;
  budget: number;
  share: number;
}
const CHANNEL_COLUMNS: DataTableColumn<ChannelRow>[] = [
  { key: 'channel', label: '채널', format: (v): ReactNode => <ChannelTag ch={v as string} /> },
  { key: 'budget', label: '예산', align: 'right', format: (v) => krw(v as number) },
  { key: 'share', label: '비중', align: 'right', format: (v) => `${v}%`, bar: {} },
];

interface KeywordRow extends Record<string, unknown> {
  keyword: string;
  channel: string;
  cost: number;
  conv: number;
  cpa: number;
  roas: number;
  qs: number;
}
const KEYWORD_COLUMNS: DataTableColumn<KeywordRow>[] = [
  { key: 'keyword', label: '키워드' },
  { key: 'channel', label: '채널', format: (v): ReactNode => <ChannelTag ch={v as string} /> },
  { key: 'cost', label: '광고비', align: 'right', format: (v) => krw(v as number) },
  { key: 'conv', label: '전환', align: 'right' },
  {
    key: 'cpa',
    label: 'CPA',
    align: 'right',
    format: (v) => krw(v as number),
    heat: { direction: 'low', goodAt: 10_000, badAt: 25_000 },
  },
  {
    key: 'roas',
    label: 'ROAS',
    align: 'right',
    format: (v) => `${v}%`,
    bar: {},
    heat: { direction: 'high', goodAt: 500, badAt: 300 },
  },
  {
    key: 'qs',
    label: '품질',
    align: 'center',
    format: (v) => `${v}/10`,
    heat: { direction: 'high', goodAt: 8, badAt: 5 },
  },
];

export function CostPage() {
  const client = useCurrentClient();
  const { data, isLoading } = useCostOverview(client, PERIOD);

  const kpi = data?.kpi;
  const channels = (data?.channels ?? []) as ChannelRow[];
  const keywords = (data?.keywords ?? []) as KeywordRow[];
  const pacing = (data?.pacing ?? []) as CampaignPacing[];
  const progressPct = pacing[0] ? Math.round(pacing[0].periodProgress * 100) : 0;

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="비용"
        description={`예산·키워드 ROI (실데이터) + 페이싱(데모)${client ? ` · ${client} ${PERIOD}` : ''}`}
        icon={DollarSign}
      />

      {!client ? (
        <p className="text-sm text-muted-foreground">상단에서 client를 선택하세요.</p>
      ) : (
        <>
          {/* KPI */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <KpiCard
              label="총 예산"
              value={kpi ? krwM(kpi.total_budget) : '-'}
              loading={isLoading}
              icon={Wallet}
            />
            <KpiCard
              label="평균 집행률"
              value={kpi ? `${kpi.avg_exec_rate}%` : '-'}
              loading={isLoading}
              icon={Percent}
            />
            <KpiCard
              label="키워드 평균 ROAS"
              value={kpi ? `${kpi.avg_roas}%` : '-'}
              sub={kpi ? `${kpi.keyword_count}개 운영` : undefined}
              loading={isLoading}
              icon={Target}
            />
          </div>

          {/* 채널 예산 비중 (C09) — DataTable 은 자체 렌더(ChartFrame 미사용) */}
          <div>
            <div className="mb-2 flex items-baseline gap-3">
              <h3 className="text-sm font-semibold text-foreground">채널 예산 비중</h3>
              <span className="text-xs text-muted-foreground">{channels.length} 채널</span>
            </div>
            <DataTable columns={CHANNEL_COLUMNS} rows={channels} defaultSort={{ key: 'share', desc: true }} />
          </div>

          {/* 키워드 ROI (T07) */}
          <div>
            <div className="mb-2 flex items-baseline gap-3">
              <h3 className="text-sm font-semibold text-foreground">키워드 ROI</h3>
              <span className="text-xs text-muted-foreground">{keywords.length} 키워드 · ROAS 내림차순</span>
            </div>
            <DataTable
              columns={KEYWORD_COLUMNS}
              rows={keywords}
              defaultSort={{ key: 'roas', desc: true }}
              footerSum={['cost', 'conv']}
            />
          </div>

          {/* 예산 페이싱 — campaigns.budget + daily_performance.spent 조인 (실데이터).
              PacingWidget=HTML viz → responsive=false + 캠페인 수에 맞춰 높이 동적 계산(겹침 방지) */}
          <ChartFrame
            title="예산 페이싱"
            meta={isLoading ? '불러오는 중…' : `${pacing.length} 캠페인 · 기간 진행 ${progressPct}%`}
            height={Math.max(320, pacing.length * 64 + 48)}
            responsive={false}
          >
            {pacing.length === 0 && !isLoading ? (
              <p className="p-4 text-sm text-muted-foreground">집행 데이터가 있는 캠페인이 없습니다.</p>
            ) : (
              <PacingWidget campaigns={pacing} />
            )}
          </ChartFrame>

          <div className="rounded-md bg-muted/40 px-4 py-3 text-2xs leading-relaxed text-muted-foreground">
            <span className="font-medium text-foreground">데이터 출처</span> — 전부 Postgres 실데이터.
            KPI·채널비중·키워드표 = cost_* 파이프라인(CPA=광고비÷전환 유도). 예산 페이싱 =
            campaigns 예산 + daily_performance 집행액(ad_cost 합) 조인 · 기간 진행률 = 데이터일수÷그달.
          </div>
        </>
      )}
    </div>
  );
}
