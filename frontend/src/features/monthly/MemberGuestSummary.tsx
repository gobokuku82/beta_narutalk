/**
 * 회원·비회원 + 재구매율 4월·3월 + 신규가입 MoM — Customer Track.
 *
 * 정답: 회원 1,779 / 비회원 140 / 재구매율 79.0%(4월)·76.2%(3월) / 신규가입 MoM -0.2%
 *
 * ChartFrame + 가로 4 cell strip — dense, KpiCard 와 일관된 톤.
 */
import type { ReactNode } from 'react';
import { ArrowDown, ArrowUp, Minus } from 'lucide-react';

import {
  useMonthlyMemberGuest,
  useMonthlyMomNewMembers,
  useMonthlyMomRepurchase,
} from '@/api/hooks/useMonthlyData';
import { ChartFrame } from '@/components/viz/ChartFrame';
import { cn } from '@/lib/cn';
import { formatNumber, formatPercent } from '@/lib/format';

import { PREVIOUS_PERIOD } from './periods';

interface Props {
  period: string;
}

function DeltaTag({ pct, label }: { pct: number | undefined; label: string }) {
  if (pct == null) return null;
  const flat = Math.abs(pct) < 0.05;
  const up = pct > 0;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 text-2xs font-medium',
        flat && 'text-muted-foreground',
        !flat && up && 'text-success',
        !flat && !up && 'text-destructive',
      )}
    >
      {flat ? <Minus className="h-2.5 w-2.5" /> : up ? <ArrowUp className="h-2.5 w-2.5" /> : <ArrowDown className="h-2.5 w-2.5" />}
      {Math.abs(pct).toFixed(1)}% {label}
    </span>
  );
}

interface CellProps {
  label: string;
  value: string;
  sub?: ReactNode;
}

function Cell({ label, value, sub }: CellProps) {
  return (
    // VOCABULARY.md §5.2 H5 v6 — Cell hover (ring-2 inset, 굵기 2배)
    <div className="flex min-w-0 flex-col gap-1 px-4 py-3 transition duration-200 hover:ring-2 hover:ring-inset hover:ring-primary/40">
      <p className="text-2xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="text-lg font-semibold tabular-nums text-foreground">{value}</p>
      {sub && <div className="text-2xs text-muted-foreground tabular-nums">{sub}</div>}
    </div>
  );
}

export function MemberGuestSummary({ period }: Props) {
  const mg = useMonthlyMemberGuest(period);
  const rep = useMonthlyMomRepurchase(PREVIOUS_PERIOD, period);
  const nm = useMonthlyMomNewMembers(PREVIOUS_PERIOD, period);

  const loading = mg.isLoading || rep.isLoading || nm.isLoading;

  return (
    <ChartFrame
      title="회원·비회원 + 재구매·신규가입"
      meta="methodology §정제 10 · §S028 MoM · §S069 MoM"
      height={130}
      responsive={false}
    >
      {loading ? (
        <div className="h-full animate-pulse rounded-sm bg-muted" />
      ) : (
        <div className="grid h-full grid-cols-2 divide-x divide-border md:grid-cols-4">
          <Cell
            label="회원 / 비회원"
            value={
              mg.data
                ? `${formatNumber(mg.data.member_count)} / ${formatNumber(mg.data.guest_count)}`
                : '—'
            }
            sub={
              mg.data
                ? `회원 ${formatPercent(mg.data.member_share_pct)} · 활성 ${formatNumber(mg.data.total_active)}`
                : null
            }
          />
          <Cell
            label={`재구매율 (${period})`}
            value={rep.data ? formatPercent(rep.data.period_b_stats.repurchase_rate) : '—'}
            sub={
              rep.data
                ? `기존 ${formatNumber(rep.data.period_b_stats.existing_buyers)} / 전체 ${formatNumber(rep.data.period_b_stats.total_buyers)}`
                : null
            }
          />
          <Cell
            label={`재구매율 (${PREVIOUS_PERIOD})`}
            value={rep.data ? formatPercent(rep.data.period_a_stats.repurchase_rate) : '—'}
            sub={
              rep.data
                ? `Δ ${rep.data.delta.repurchase_rate_pp > 0 ? '+' : ''}${rep.data.delta.repurchase_rate_pp.toFixed(1)}%p`
                : null
            }
          />
          <Cell
            label="신규 가입 MoM"
            value={nm.data ? formatNumber(nm.data.period_b_total) : '—'}
            sub={<DeltaTag pct={nm.data?.delta_pct} label={`vs ${nm.data?.period_a_total ?? '-'}`} />}
          />
        </div>
      )}
    </ChartFrame>
  );
}
