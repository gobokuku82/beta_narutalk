/**
 * Section 2 — MoM 변화 4 (4월 vs 3월).
 *
 * 매출 +50.5% · 주문 +42.6% · 기존고객 +19.2% · 신규주문 +1.4%
 *
 * 단순 4-칼럼 정량 카드 (recharts 안 씀 — 4개라 BarChart 과함).
 *
 * spec: 계획서 §1.2 M-1 ~ M-4
 */
import { ArrowDown, ArrowUp, Minus } from 'lucide-react';

import { useMonthlyMomAov, useMonthlyMomRepurchase, useMonthlyMomRevenue } from '@/api/hooks/useMonthlyData';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/cn';
import { PREVIOUS_PERIOD } from './periods';

interface Props {
  period: string;
}

interface DeltaItem {
  label: string;
  pct?: number;
  sub?: string;
}

function DeltaCell({ item, loading }: { item: DeltaItem; loading: boolean }) {
  const hasPct = item.pct != null && !Number.isNaN(item.pct);
  const up = hasPct && item.pct! > 0;
  const flat = hasPct && Math.abs(item.pct!) < 0.05;

  return (
    // VOCABULARY.md §5.2 H5 v6 — Cell hover (ring-2 inset, 굵기 2배)
    <div className="flex flex-col gap-1 rounded-md p-2 transition duration-200 hover:ring-2 hover:ring-inset hover:ring-primary/40">
      <p className="text-2xs font-medium uppercase tracking-wide text-muted-foreground">
        {item.label}
      </p>
      {loading ? (
        <div className="h-5 w-16 animate-pulse rounded-sm bg-muted" />
      ) : (
        <div
          className={cn(
            'flex items-center gap-1 text-base font-semibold tabular-nums',
            !hasPct && 'text-muted-foreground',
            hasPct && flat && 'text-muted-foreground',
            hasPct && !flat && up && 'text-success',
            hasPct && !flat && !up && 'text-destructive',
          )}
        >
          {hasPct && (flat ? <Minus className="h-3 w-3" /> : up ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)}
          {hasPct ? `${item.pct! >= 0 ? '+' : ''}${item.pct!.toFixed(1)}%` : '-'}
        </div>
      )}
      {item.sub && <p className="text-2xs text-muted-foreground tabular-nums">{item.sub}</p>}
    </div>
  );
}

export function MomBar({ period }: Props) {
  const rev = useMonthlyMomRevenue(PREVIOUS_PERIOD, period);
  const rep = useMonthlyMomRepurchase(PREVIOUS_PERIOD, period);
  const aov = useMonthlyMomAov(PREVIOUS_PERIOD, period);

  const loading = rev.isLoading || rep.isLoading || aov.isLoading;

  const items: DeltaItem[] = [
    {
      label: '매출 MoM',
      pct: rev.data?.delta_pct,
      sub: rev.data
        ? `${Math.round(rev.data.period_a_revenue / 1_000_000)}M → ${Math.round(rev.data.period_b_revenue / 1_000_000)}M`
        : undefined,
    },
    {
      label: '주문 MoM',
      pct: aov.data?.delta.orders_pct,
      sub: aov.data
        ? `${aov.data.period_a_stats.orders_count} → ${aov.data.period_b_stats.orders_count}`
        : undefined,
    },
    {
      label: '기존 구매자 MoM',
      pct: rep.data?.delta.existing_buyers_pct,
      sub: rep.data
        ? `${rep.data.period_a_stats.existing_buyers} → ${rep.data.period_b_stats.existing_buyers}`
        : undefined,
    },
    {
      label: '신규 구매자 MoM',
      pct: rep.data?.delta.new_buyers_pct,
      sub: rep.data
        ? `${rep.data.period_a_stats.new_buyers} → ${rep.data.period_b_stats.new_buyers}`
        : undefined,
    },
  ];

  return (
    <Card className="p-4">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {items.map((it) => (
          <DeltaCell key={it.label} item={it} loading={loading} />
        ))}
      </div>
    </Card>
  );
}
