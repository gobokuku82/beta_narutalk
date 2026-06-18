/**
 * 월간 결산 Hero — 마케팅비→매출 사슬 + 객단가 분해.
 *
 * MetricChainStrip 으로 인과 분해 시각화 (점수판 X):
 *   마케팅비 ─(ROAS)→ 매출 ─(÷주문)→ AOV
 *
 * 매출 노드에 MoM delta. P1 (점수판 아닌 시스템) / P2 (목표·기간대비 동반).
 */
import { useMonthlyAdCost, useMonthlyAov, useMonthlyMomRevenue, useMonthlyRevenue, useMonthlyRoas } from '@/api/hooks/useMonthlyData';
import {
  MetricChainStrip,
  type MetricChainNode,
  type MetricChainTransition,
} from '@/components/viz/MetricChainStrip';
import { formatCompact, formatCurrency, formatNumber } from '@/lib/format';
import { PREVIOUS_PERIOD } from './periods';

interface Props {
  period: string;
}

export function MonthlyHero({ period }: Props) {
  const adCost = useMonthlyAdCost(period);
  const revenue = useMonthlyRevenue(period);
  const roas = useMonthlyRoas(period);
  const aov = useMonthlyAov(period);
  const momRev = useMonthlyMomRevenue(PREVIOUS_PERIOD, period);

  const nodes: MetricChainNode[] = [
    {
      label: '마케팅비',
      value: adCost.data ? formatCompact(adCost.data.total_cost) : '—',
    },
    {
      label: '매출',
      value: revenue.data ? formatCompact(revenue.data.revenue_total) : '—',
      delta: momRev.data
        ? {
            value: `${Math.abs(momRev.data.delta_pct).toFixed(1)}% MoM`,
            direction: momRev.data.delta_pct > 0 ? 'up' : 'down',
            good: momRev.data.delta_pct > 0,
          }
        : undefined,
    },
    {
      label: '객단가 (AOV)',
      value: aov.data ? formatCurrency(aov.data.aov) : '—',
    },
  ];

  const transitions: MetricChainTransition[] = [
    {
      label: 'ROAS',
      value: roas.data ? `${roas.data.roas.toFixed(2)}×` : '—',
    },
    {
      label: '÷ 주문',
      value: aov.data ? `${formatNumber(aov.data.orders_count)}건` : '—',
    },
  ];

  return <MetricChainStrip nodes={nodes} transitions={transitions} />;
}
