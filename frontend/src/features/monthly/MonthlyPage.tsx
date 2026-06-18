/**
 * MonthlyPage — `/monthly` 월간 결산.
 *
 * 한 달의 광고·매출·고객을 한 페이지 정량 결산 (운영형 /dashboard 와 보완).
 * dashboard1 의 8 섹션 28 요소 → Hero + 4 트랙 재배열, viz/* 스타일 통일.
 *
 * 데이터: backend `/api/dashboard1/*` 20 endpoint (methodology 17/17 정답값 기반).
 * 트랙 분할:
 *   Hero  · 마케팅비→매출→AOV 사슬 (MetricChainStrip)
 *   Track 1 · 성과       — KpiGrid (KPI 9) + MomBar (MoM 4)
 *   Track 2 · 마케팅      — AdCostBar (5매체) + ChannelDistTable (10 raw + 7 그룹)
 *   Track 3 · 고객       — MemberGuestSummary (회원·게스트·재구매·신규)
 *   Track 4 · 세그먼트    — GradeDots + GradeRatioTable + AgeBucketBar + CategoryDistTable
 */
import type { ReactNode } from 'react';
import { CalendarRange } from 'lucide-react';

import { useCurrentClient } from '@/api/clients';
import { PageHeader } from '@/components/layout/PageHeader';

import { AdCostBar } from './AdCostBar';
import { AgeBucketBar } from './AgeBucketBar';
import { CategoryDistTable } from './CategoryDistTable';
import { ChannelDistTable } from './ChannelDistTable';
import { GradeDots } from './GradeDots';
import { GradeRatioTable } from './GradeRatioTable';
import { KpiGrid } from './KpiGrid';
import { MemberGuestSummary } from './MemberGuestSummary';
import { MomBar } from './MomBar';
import { MonthlyHero } from './MonthlyHero';
import { CURRENT_PERIOD, periodLabel } from './periods';

export function MonthlyPage() {
  const period = CURRENT_PERIOD;
  const currentClient = useCurrentClient();

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title={
          <>
            <span className="text-primary">월간 결산</span>
            <span className="text-muted-foreground font-normal"> — {periodLabel(period)}</span>
          </>
        }
        description={`한 달의 광고·매출·고객을 한 페이지 정량 결산${currentClient ? ` · ${currentClient}` : ''}`}
        icon={CalendarRange}
      />

      {/* Hero zone — PALETTE.md §8.2 A (color block) + K (reading guide) 적용 */}
      <div className="rounded-xl bg-accent/50 p-2">
        <MonthlyHero period={period} />
      </div>

      <TrackSection
        n={1}
        title="성과"
        subtitle="KPI 9 + MoM 4 — 매출·ROAS·CAC·AOV·프로모션·신규회원"
      >
        <KpiGrid period={period} />
        <MomBar period={period} />
      </TrackSection>

      <TrackSection
        n={2}
        title="마케팅"
        subtitle="투입(5매체) · 회수(채널 분포 + 알수없음)"
      >
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <AdCostBar period={period} />
          <ChannelDistTable period={period} />
        </div>
      </TrackSection>

      <TrackSection
        n={3}
        title="고객"
        subtitle="회원·비회원 · 재구매율 · 신규가입 MoM"
      >
        <MemberGuestSummary period={period} />
      </TrackSection>

      <TrackSection
        n={4}
        title="세그먼트"
        subtitle="등급(LTV) · 연령 · 카테고리 분배"
      >
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <GradeDots />
          <GradeRatioTable period={period} />
        </div>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <AgeBucketBar />
          <CategoryDistTable period={period} />
        </div>
      </TrackSection>

      <div className="rounded-md bg-muted/40 px-4 py-3 text-2xs leading-relaxed text-muted-foreground">
        <p>
          <span className="font-medium text-foreground">읽는 법</span> — Hero 사슬은
          마케팅비→매출 의 전환(ROAS) 과 매출→객단가 의 분해(÷주문) 두 단계. 매출 노드의 MoM 으로
          추세 동반. 4 트랙은 8섹션 28요소(methodology 17/17 정답값) 를 성과/마케팅/고객/세그먼트로
          묶음 — 운영형 <span className="font-medium text-foreground">/dashboard</span> 와는 시간
          축(단일월 결산 vs 시계열 운영) 으로 구분.
        </p>
        <p className="mt-1">
          데이터: backend <code className="rounded-sm bg-card px-1 py-1 font-mono">/api/dashboard1/*</code>{' '}
          20 endpoint 실데이터 (현 client = {currentClient ?? '—'}).
        </p>
      </div>
    </div>
  );
}

interface TrackSectionProps {
  n: number;
  title: string;
  subtitle: string;
  children: ReactNode;
}

function TrackSection({ n, title, subtitle, children }: TrackSectionProps) {
  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-baseline gap-2">
        <span className="text-2xs font-medium tabular-nums text-muted-foreground/60">
          {String(n).padStart(2, '0')}
        </span>
        <h2 className="text-sm font-semibold text-foreground">{title}</h2>
        <span className="text-2xs text-muted-foreground">— {subtitle}</span>
      </div>
      <div className="flex flex-col gap-4">{children}</div>
    </section>
  );
}
