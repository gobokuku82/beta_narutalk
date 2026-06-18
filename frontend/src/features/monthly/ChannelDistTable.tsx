/**
 * 채널 매출 분포 (10 raw + 7 그룹) + 알수없음 매출비중 — Marketing Track 회수.
 *
 * 정답: Naver 530 · Unknown 481 · Meta 388 · Direct 273 / unknown 매출비중 39.8%
 *
 * DataTable 2개 (그룹·raw) + 알수없음 메타 badge.
 */
import { useMonthlyChannel, useMonthlyUnknownShare } from '@/api/hooks/useMonthlyData';
import { ChartFrame } from '@/components/viz/ChartFrame';
import { DataTable, type DataTableColumn } from '@/components/viz/DataTable';
import { formatCurrency, formatNumber, formatPercent } from '@/lib/format';

interface Props {
  period: string;
}

interface GroupRow extends Record<string, unknown> {
  name: string;
  count: number;
  share_pct: number;
}

interface RawRow extends Record<string, unknown> {
  name: string;
  count: number;
}

const GROUP_COLUMNS: DataTableColumn<GroupRow>[] = [
  { key: 'name', label: '그룹', align: 'left', sortable: false },
  { key: 'count', label: '주문', align: 'right', format: (v) => formatNumber(v as number), bar: {} },
  {
    key: 'share_pct',
    label: '비중',
    align: 'right',
    format: (v) => <span className="text-muted-foreground">{formatPercent(v as number)}</span>,
  },
];

const RAW_COLUMNS: DataTableColumn<RawRow>[] = [
  { key: 'name', label: 'raw 채널', align: 'left', sortable: false },
  { key: 'count', label: '주문', align: 'right', format: (v) => formatNumber(v as number), bar: {} },
];

export function ChannelDistTable({ period }: Props) {
  const channels = useMonthlyChannel(period);
  const unknown = useMonthlyUnknownShare(period);

  const loading = channels.isLoading || unknown.isLoading;
  const groupTotal = channels.data
    ? Object.values(channels.data.by_group).reduce((a, b) => a + b, 0)
    : 0;

  const groupRows: GroupRow[] = channels.data
    ? Object.entries(channels.data.by_group).map(([name, count]) => ({
        name,
        count,
        share_pct: groupTotal ? (count / groupTotal) * 100 : 0,
      }))
    : [];

  const rawRows: RawRow[] = channels.data
    ? Object.entries(channels.data.by_raw_channel).map(([name, count]) => ({ name, count }))
    : [];

  const meta = unknown.data
    ? `알수없음 매출비중 ${formatPercent(unknown.data.unknown_share_pct)} · ${period}`
    : period;

  return (
    <ChartFrame title="채널 분포" meta={meta} height={360} responsive={false}>
      {loading ? (
        <div className="h-full animate-pulse rounded-sm bg-muted" />
      ) : (
        <div className="flex h-full flex-col gap-3">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div className="flex flex-col gap-2">
              <p className="text-2xs font-medium uppercase tracking-wide text-muted-foreground">
                그룹별 ({groupRows.length})
              </p>
              <DataTable<GroupRow>
                columns={GROUP_COLUMNS}
                rows={groupRows}
                defaultSort={{ key: 'count', desc: true }}
                className="border-0"
              />
            </div>
            <div className="flex flex-col gap-2">
              <p className="text-2xs font-medium uppercase tracking-wide text-muted-foreground">
                raw 채널 ({rawRows.length})
              </p>
              <DataTable<RawRow>
                columns={RAW_COLUMNS}
                rows={rawRows}
                defaultSort={{ key: 'count', desc: true }}
                className="border-0"
              />
            </div>
          </div>
          {unknown.data && (
            <p className="px-1 text-2xs text-muted-foreground">
              알수없음 매출 {formatCurrency(unknown.data.unknown_revenue)} / 총{' '}
              {formatCurrency(unknown.data.total_revenue)} (주문{' '}
              {formatNumber(unknown.data.unknown_orders)}건)
            </p>
          )}
        </div>
      )}
    </ChartFrame>
  );
}
