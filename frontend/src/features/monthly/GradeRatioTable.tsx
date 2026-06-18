/**
 * 등급별 회원·매출 (5등급) — Segment Track LTV 분배.
 *
 * 정답: SILVER 매출 65.8M (비중 57.8%) · WELCOME 회원 74.5%
 *
 * DataTable + 매출 in-cell bar.
 */
import { useMonthlyGrade } from '@/api/hooks/useMonthlyData';
import { ChartFrame } from '@/components/viz/ChartFrame';
import { DataTable, type DataTableColumn } from '@/components/viz/DataTable';
import { formatCurrency, formatNumber, formatPercent } from '@/lib/format';

interface Props {
  period: string;
}

const GRADE_ORDER = ['VIP', 'GOLD', 'SILVER', 'REGULAR', 'WELCOME'] as const;

interface GradeTableRow extends Record<string, unknown> {
  grade: string;
  member_count: number;
  member_share_pct: number;
  buyer_count: number;
  revenue: number;
  revenue_share_pct: number;
}

const COLUMNS: DataTableColumn<GradeTableRow>[] = [
  { key: 'grade', label: '등급', align: 'left', sortable: false },
  { key: 'member_count', label: '회원', align: 'right', format: (v) => formatNumber(v as number) },
  {
    key: 'member_share_pct',
    label: '비중',
    align: 'right',
    format: (v) => <span className="text-muted-foreground">{formatPercent(v as number)}</span>,
  },
  { key: 'buyer_count', label: '구매자', align: 'right', format: (v) => formatNumber(v as number) },
  {
    key: 'revenue',
    label: '매출',
    align: 'right',
    format: (v) => formatCurrency(v as number),
    bar: {},
  },
  {
    key: 'revenue_share_pct',
    label: '매출비중',
    align: 'right',
    format: (v) => <span className="text-muted-foreground">{formatPercent(v as number)}</span>,
  },
];

export function GradeRatioTable({ period }: Props) {
  const { data, isLoading } = useMonthlyGrade(period);

  const rows: GradeTableRow[] = data
    ? GRADE_ORDER.flatMap((g) => {
        const r = data.table[g];
        return r ? [{ grade: g as string, ...r }] : [];
      })
    : [];

  const meta = data
    ? `회원 ${formatNumber(data.total_members)} · 회원매출 ${formatCurrency(data.total_member_revenue)}`
    : '등급 분배';

  return (
    <ChartFrame title="등급별 회원·매출" meta={meta} height={260} responsive={false}>
      {isLoading ? (
        <div className="h-full animate-pulse rounded-sm bg-muted" />
      ) : (
        <DataTable<GradeTableRow> columns={COLUMNS} rows={rows} className="border-0" />
      )}
    </ChartFrame>
  );
}
