/**
 * Section 1 — 핵심 KPI 9 (3×3 그리드).
 *
 * 기존 components/layout/KpiCard 9개 재사용 (신규 작성 X).
 * 데이터 = useMonthly* 9 hook 자체 호출 → loading 전파.
 *
 * Step 7 — ⓘ tooltip (progressive disclosure 1차):
 *   각 카드 hover 시 methodology §id + 산식 표시. KpiCard 본체 무수정 — Tooltip wrap.
 *
 * spec: 계획서 §1.2 (K-1 ~ K-9 정답값) · §5 Step 7 DoD
 */
import {
  Gift,
  Info,
  Percent,
  Receipt,
  Target,
  TrendingUp,
  UserPlus,
  Wallet,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import type { ReactNode } from 'react';

import {
  useMonthlyAdCost,
  useMonthlyAov,
  useMonthlyCac,
  useMonthlyMomAov,
  useMonthlyNewMembers,
  useMonthlyPromotionRevenue,
  useMonthlyPromotionRoas,
  useMonthlyRevenue,
  useMonthlyRoas,
  useMonthlySignupConversion,
} from '@/api/hooks/useMonthlyData';
import { CardAsk } from '@/features/agent/CardAsk';
import { KpiCard } from '@/components/layout/KpiCard';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { formatCompact, formatCurrency, formatNumber, formatPercent } from '@/lib/format';

import { PREVIOUS_PERIOD } from './periods';

interface Props {
  period: string;
}

interface KpiMeta {
  methodologyId: string; // 'methodology §S001' 등
  formula: string;       // 'SUM(payment_amount) WHERE active AND period' 등
}

/**
 * KPI 카드를 Tooltip 으로 wrap — ⓘ 우하단 visual indicator + 카드 전체 hover trigger.
 */
function KpiTooltip({
  meta,
  children,
}: {
  meta: KpiMeta;
  children: ReactNode;
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className="relative cursor-help">
          {children}
          <Info
            className="pointer-events-none absolute bottom-3 right-3 h-3 w-3 text-muted-foreground opacity-60"
            aria-hidden
          />
        </div>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-xs text-xs">
        <p className="font-semibold">{meta.methodologyId}</p>
        <p className="mt-1 whitespace-pre-line text-muted-foreground">{meta.formula}</p>
      </TooltipContent>
    </Tooltip>
  );
}

// methodology 출처 + 산식 — backend catalog 와 일치
const META: Record<string, KpiMeta> = {
  revenue: {
    methodologyId: 'methodology §S001 — 매출',
    formula: 'SUM(orders.payment_amount)\nWHERE order_status != C40\n  AND order_date IN period',
  },
  adCost: {
    methodologyId: 'methodology §S003 / 정제 5 — 마케팅비',
    formula: 'Meta.spend + NaverSA.salesAmt\n+ ADVoost.cost + Kakao.total_cost_krw\n+ Talktalk.total_cost_krw',
  },
  roas: {
    methodologyId: 'methodology §S004 — ROAS',
    formula: 'total_revenue / total_marketing_cost\n(round 2자리)',
  },
  cac: {
    methodologyId: 'methodology §S032 — CAC',
    formula: 'total_marketing_cost / new_members_count\n(round)',
  },
  promoRev: {
    methodologyId: 'methodology §S002 — 프로모션 매출',
    formula: 'SUM(payment_amount)\nWHERE active AND promotion_code IS NOT NULL',
  },
  promoRoas: {
    methodologyId: 'methodology §S005 — 프로모션 ROAS',
    formula: 'promotion_revenue / total_marketing_cost\n(round 2자리)',
  },
  newMembers: {
    methodologyId: 'methodology §S069 — 신규 회원',
    formula: 'COUNT(*) FROM customers\nWHERE signup_date prefix period\nGROUP BY signup_utm_source',
  },
  aov: {
    methodologyId: 'methodology §S048 — 객단가 (AOV)',
    formula: 'SUM(payment_amount) / COUNT(order_id)\nWHERE active AND period (round)',
  },
  signup: {
    methodologyId: 'methodology §S067 — 가입 전환율',
    formula: 'new_members_monthly / ga4_session_start_total * 100\n(round 2자리)',
  },
};

interface KpiCellProps {
  metaKey: keyof typeof META;
  period: string;
  label: string;
  value: string;
  sub?: string;
  loading: boolean;
  icon: LucideIcon;
  delta?: number;
  deltaGood?: boolean;
}

function KpiCell({ metaKey, period, ...rest }: KpiCellProps) {
  const meta = META[metaKey]!;
  return (
    // 카드클릭→에이전트 (P3): hover ✨ → 팝업 → 진단/추천/재검증. 컨텍스트 = 카드 표시값 그대로.
    <CardAsk
      context={{
        metric: rest.label,
        value: rest.value,
        period,
        methodology: meta.methodologyId,
        formula: meta.formula,
        sub: rest.sub,
      }}
      disabled={rest.loading || rest.value === '-'}
    >
      <KpiTooltip meta={meta}>
        <KpiCard {...rest} />
      </KpiTooltip>
    </CardAsk>
  );
}

export function KpiGrid({ period }: Props) {
  const revenue = useMonthlyRevenue(period);
  const adCost = useMonthlyAdCost(period);
  const roas = useMonthlyRoas(period);
  const cac = useMonthlyCac(period);
  const promoRev = useMonthlyPromotionRevenue(period);
  const promoRoas = useMonthlyPromotionRoas(period);
  const newMembers = useMonthlyNewMembers(period);
  const aov = useMonthlyAov(period);
  const signup = useMonthlySignupConversion(period);
  // K-8 객단가 MoM 만 헤더 카드에 표시 (단일 KPI 의 delta context)
  const aovMom = useMonthlyMomAov(PREVIOUS_PERIOD, period);

  return (
    <TooltipProvider delayDuration={200}>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <KpiCell
          period={period}
          metaKey="revenue"
          label="매출 (활성주문)"
          value={revenue.data ? formatCurrency(revenue.data.revenue_total) : '-'}
          sub={
            revenue.data
              ? `활성주문 ${formatNumber(revenue.data.active_orders_count)}건`
              : undefined
          }
          loading={revenue.isLoading}
          icon={TrendingUp}
        />

        <KpiCell
          period={period}
          metaKey="adCost"
          label="마케팅비"
          value={adCost.data ? formatCurrency(adCost.data.total_cost) : '-'}
          sub="5매체 합산 (Meta·NaverSA·ADVoost·Kakao·Talktalk)"
          loading={adCost.isLoading}
          icon={Wallet}
        />

        <KpiCell
          period={period}
          metaKey="roas"
          label="전체 ROAS"
          value={roas.data ? `${roas.data.roas.toFixed(2)}×` : '-'}
          sub="매출 ÷ 마케팅비"
          loading={roas.isLoading}
          icon={Zap}
        />

        <KpiCell
          period={period}
          metaKey="cac"
          label="전체 CAC"
          value={cac.data ? formatCurrency(cac.data.cac) : '-'}
          sub={cac.data ? `신규 ${formatNumber(cac.data.new_members_count)}명 / 1인당` : undefined}
          loading={cac.isLoading}
          icon={Target}
        />

        <KpiCell
          period={period}
          metaKey="promoRev"
          label="프로모션 매출"
          value={promoRev.data ? formatCurrency(promoRev.data.promotion_revenue) : '-'}
          sub={
            promoRev.data
              ? `전체 매출 중 ${promoRev.data.promotion_share_pct.toFixed(1)}%`
              : undefined
          }
          loading={promoRev.isLoading}
          icon={Gift}
        />

        <KpiCell
          period={period}
          metaKey="promoRoas"
          label="프로모션 ROAS"
          value={promoRoas.data ? `${promoRoas.data.promotion_roas.toFixed(2)}×` : '-'}
          sub="프모매출 ÷ 마케팅비"
          loading={promoRoas.isLoading}
          icon={Zap}
        />

        <KpiCell
          period={period}
          metaKey="newMembers"
          label="신규 회원"
          value={newMembers.data ? formatNumber(newMembers.data.new_members_total) : '-'}
          sub={
            newMembers.data
              ? `${Object.keys(newMembers.data.new_members_by_channel).length}개 채널`
              : undefined
          }
          loading={newMembers.isLoading}
          icon={UserPlus}
        />

        <KpiCell
          period={period}
          metaKey="aov"
          label="객단가 (AOV)"
          value={aov.data ? formatCurrency(aov.data.aov) : '-'}
          sub={
            aov.data
              ? `구매자 ${formatNumber(aov.data.unique_buyers)} · 주문 ${formatNumber(aov.data.orders_count)}`
              : undefined
          }
          loading={aov.isLoading}
          icon={Receipt}
          delta={aovMom.data?.delta.aov_pct}
        />

        <KpiCell
          period={period}
          metaKey="signup"
          label="가입 전환율"
          value={signup.data ? formatPercent(signup.data.signup_conversion_pct, 2) : '-'}
          sub={
            signup.data
              ? `${formatNumber(signup.data.signups)} / 세션 ${formatCompact(signup.data.sessions)}`
              : undefined
          }
          loading={signup.isLoading}
          icon={Percent}
        />
      </div>
    </TooltipProvider>
  );
}
