/**
 * 카테고리 5 균등 분배 (count + 매출) — Segment Track 매출 분배.
 *
 * 정답: 스킨케어 67.7M (1,400건) · 클렌징 19.1M · 마스크팩 19.4M · 자외선차단 6.9M · 기타 6.5M
 *
 * DataTable + 매출 in-cell bar.
 */
import { useMonthlyCategory } from '@/api/hooks/useMonthlyData';
import { ChartFrame } from '@/components/viz/ChartFrame';
import { DataTable, type DataTableColumn } from '@/components/viz/DataTable';
import { formatCurrency, formatNumber, formatPercent } from '@/lib/format';

interface Props {
  period: string;
}

interface CategoryRow extends Record<string, unknown> {
  category: string;
  count: number;
  revenue: number;
  share_pct: number;
}

export function CategoryDistTable({ period }: Props) {
  const { data, isLoading } = useMonthlyCategory(period);

  const rows: CategoryRow[] = data
    ? Object.entries(data.by_category).map(([category, row]) => ({
        category,
        count: row.count,
        revenue: row.revenue,
        share_pct: data.total_distributed_revenue
          ? (row.revenue / data.total_distributed_revenue) * 100
          : 0,
      }))
    : [];

  const COLUMNS: DataTableColumn<CategoryRow>[] = [
    { key: 'category', label: '카테고리', align: 'left', sortable: false },
    { key: 'count', label: '주문수', align: 'right', format: (v) => formatNumber(v as number) },
    {
      key: 'revenue',
      label: '매출',
      align: 'right',
      format: (v) => formatCurrency(v as number),
      bar: {},
    },
    {
      key: 'share_pct',
      label: '비중',
      align: 'right',
      format: (v) => <span className="text-muted-foreground">{formatPercent(v as number)}</span>,
    },
  ];

  const meta = data
    ? `${data.total_categories} 카테고리 · 분배매출 ${formatCurrency(data.total_distributed_revenue)}`
    : '카테고리 분배';

  return (
    <ChartFrame title="카테고리 균등 분배" meta={meta} height={220} responsive={false}>
      {isLoading ? (
        <div className="h-full animate-pulse rounded-sm bg-muted" />
      ) : (
        <DataTable<CategoryRow>
          columns={COLUMNS}
          rows={rows}
          defaultSort={{ key: 'revenue', desc: true }}
          className="border-0"
        />
      )}
    </ChartFrame>
  );
}
