/**
 * PacingWidget — 캠페인별 예산 페이싱 (통합계획서 §5.3 / 원칙 P3).
 *
 * Status: complete.
 *
 * '평균 집행률 N%' 한 숫자가 아닌 캠페인별 페이싱 진단:
 *  - 진행률 막대 (현재 소진 / 총예산)
 *  - 예상 위치 마크 (기간 진행률) — 그 지점이 'on track'
 *  - under(<90%) / on(90~110%) / over(>110%) 밴드 색
 *  - 정렬: 위험(over/under) 강조 표시
 */
import { cn } from '@/lib/cn';

export type PacingStatus = 'under' | 'on' | 'over';

export interface CampaignPacing {
  id: string;
  name: string;
  /** 총 예산. */
  budget: number;
  /** 현재 소진액. */
  spent: number;
  /** 기간 진행률 (0~1) — 예: 월 중간이면 0.5. */
  periodProgress: number;
}

interface PacingWidgetProps {
  campaigns: CampaignPacing[];
  formatCurrency?: (v: number) => string;
  className?: string;
}

const STATUS_LABEL: Record<PacingStatus, string> = {
  under: '저소진',
  on: '정상',
  over: '과소진',
};

const STATUS_TEXT: Record<PacingStatus, string> = {
  under: 'text-warning',
  on: 'text-success',
  over: 'text-destructive',
};

const STATUS_BG: Record<PacingStatus, string> = {
  under: 'bg-warning',
  on: 'bg-success',
  over: 'bg-destructive',
};

function getStatus(
  spent: number,
  budget: number,
  periodProgress: number,
): PacingStatus {
  if (budget <= 0) return 'on';
  const actualPct = spent / budget;
  const expectedPct = periodProgress;
  const ratio = expectedPct > 0 ? actualPct / expectedPct : 1;
  if (ratio < 0.9) return 'under';
  if (ratio > 1.1) return 'over';
  return 'on';
}

export function PacingWidget({
  campaigns,
  formatCurrency = (v) => `₩${v.toLocaleString('ko-KR')}`,
  className,
}: PacingWidgetProps) {
  return (
    <div className={cn('space-y-2', className)}>
      {campaigns.map((c) => {
        const spentPct = c.budget > 0 ? (c.spent / c.budget) * 100 : 0;
        const expectedPct = c.periodProgress * 100;
        const status = getStatus(c.spent, c.budget, c.periodProgress);

        return (
          // VOCABULARY.md §5.1 H1~H4 — row = 카드 결, 외곽 hover 적용
          <div
            key={c.id}
            className="rounded-md border border-border bg-card px-3 py-2 transition duration-200 hover:-translate-y-1 hover:bg-primary/4 hover:ring-1 hover:ring-primary/40"
          >
            <div className="flex items-baseline justify-between gap-2">
              <div className="flex min-w-0 items-baseline gap-2">
                <span className="truncate text-sm font-medium text-foreground">
                  {c.name}
                </span>
                <span className="shrink-0 text-xs tabular-nums text-muted-foreground">
                  {c.id}
                </span>
              </div>
              <span
                className={cn(
                  'shrink-0 text-xs font-medium tabular-nums',
                  STATUS_TEXT[status],
                )}
              >
                {STATUS_LABEL[status]} · {spentPct.toFixed(0)}%
              </span>
            </div>
            <div className="relative mt-1.5 h-2 rounded-full bg-muted">
              <div
                aria-hidden
                className={cn(
                  'absolute inset-y-0 left-0 rounded-full',
                  STATUS_BG[status],
                )}
                style={{ width: `${Math.min(spentPct, 100)}%` }}
              />
              <div
                aria-hidden
                title={`기간 진행 ${expectedPct.toFixed(0)}%`}
                className="absolute top-1/2 h-3 w-0.5 -translate-x-1/2 -translate-y-1/2 bg-foreground/60"
                style={{ left: `${Math.min(expectedPct, 100)}%` }}
              />
            </div>
            <div className="mt-1 flex items-center justify-between text-2xs tabular-nums text-muted-foreground">
              <span>
                {formatCurrency(c.spent)} / {formatCurrency(c.budget)}
              </span>
              <span>기간 진행 {expectedPct.toFixed(0)}%</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
