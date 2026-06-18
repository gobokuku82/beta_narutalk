/**
 * KpiCard — 대쉬보드 공통 KPI 카드.
 *
 * 2026 Warm Neutral — 플랫. 컬러 액센트 바 없음, 중립 아이콘 칩.
 * 큰 잉크 숫자 + 의미적 델타(상승=success / 하락=destructive)만 색 사용.
 */
import { ArrowDown, ArrowUp, type LucideIcon } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/cn';

/** 호환용 — 기존 호출부 props 유지. 현재 렌더에는 미사용 (1-accent 원칙). */
export type KpiAccent =
  | 'brand'
  | 'naver'
  | 'kakao'
  | 'meta'
  | 'google'
  | 'success'
  | 'warning';

interface KpiCardProps {
  label: string;
  value: string;
  sub?: string;
  loading?: boolean;
  /** 등락률(%) — 양수=상승. 부호로 화살표/색 결정. */
  delta?: number;
  /** delta 색을 의미적으로 뒤집을 때 (예: CPA 하락이 좋음 → deltaGood). */
  deltaGood?: boolean;
  icon?: LucideIcon;
  /** 호환용 — 현재 비주얼에서는 미사용. */
  accent?: KpiAccent;
}

export function KpiCard({
  label,
  value,
  sub,
  loading,
  delta,
  deltaGood,
  icon: Icon,
}: KpiCardProps) {
  const hasDelta = delta != null && !Number.isNaN(delta);
  const up = hasDelta && delta! >= 0;
  const good = deltaGood ?? up;

  return (
    <Card className="p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-2xs font-medium uppercase tracking-wide text-muted-foreground">
            {label}
          </p>
          {loading ? (
            <div className="mt-1.5 h-6 w-20 animate-pulse rounded-sm bg-muted" />
          ) : (
            <p className="mt-1 text-xl font-semibold leading-tight tabular-nums text-foreground">
              {value}
            </p>
          )}
          <div className="mt-0.5 flex flex-wrap items-center gap-x-2">
            {hasDelta && !loading && (
              <span
                className={cn(
                  'inline-flex items-center gap-1 text-2xs font-medium',
                  good ? 'text-success' : 'text-destructive',
                )}
              >
                {up ? (
                  <ArrowUp className="h-2.5 w-2.5" />
                ) : (
                  <ArrowDown className="h-2.5 w-2.5" />
                )}
                {Math.abs(delta!).toFixed(1)}%
              </span>
            )}
            {sub && <span className="text-2xs text-muted-foreground">{sub}</span>}
          </div>
        </div>
        {Icon && (
          <Icon className="h-3.5 w-3.5 shrink-0 text-muted-foreground/60" aria-hidden />
        )}
      </div>
    </Card>
  );
}
