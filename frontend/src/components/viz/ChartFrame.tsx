/**
 * ChartFrame — 차트 공통 셸 (통합계획서 §5.4 / 원칙 P4·P6·P7).
 *
 * Status: complete.
 *
 * 차트를 *설계물* 로 다루는 얇은 프레임:
 *  - 작은 제목 + 기간/단위 메타 (CardHeader 의 큰 제목 대체)
 *  - hairline 보더만, chrome 최소 (P7)
 *  - ResponsiveContainer 포함 — children 으로 recharts 컴포넌트 직접 전달
 *  - TARGET_LINE_PROPS / CHART_GRID_PROPS / CHART_AXIS_TICK_PROPS 헬퍼
 *    상수로 차트 일관성 강제 (P4 — 라이브러리 기본값 금지)
 */
import type { ReactElement, ReactNode } from 'react';
import { ResponsiveContainer } from 'recharts';
import { cn } from '@/lib/cn';

interface ChartFrameProps {
  title: string;
  meta?: string;
  height?: number;
  /** 차트 또는 HTML 기반 viz. responsive=true(default) 면 recharts 단일 요소. */
  children: ReactNode;
  /** 우상단 액션 슬롯 — 기간 토글 등. */
  actions?: ReactNode;
  /** ResponsiveContainer 로 감쌀지 — recharts 차트면 true(기본),
   *  HTML 기반 viz(FunnelChart·PacingWidget 등) 면 false. */
  responsive?: boolean;
  className?: string;
}

export function ChartFrame({
  title,
  meta,
  height = 280,
  children,
  actions,
  responsive = true,
  className,
}: ChartFrameProps) {
  return (
    <section className={cn(
      // VOCABULARY.md §5.1 H1~H4 — Card 와 일관 hover (v2 2026-06-10 lift 강화: 2px → 4px)
      'rounded-lg border border-border bg-card transition duration-200 hover:-translate-y-1 hover:bg-primary/4 hover:ring-1 hover:ring-primary/40',
      className,
    )}>
      <header className="flex items-baseline justify-between gap-3 border-b border-border px-5 py-3">
        <div className="flex min-w-0 items-baseline gap-3">
          <h3 className="truncate text-sm font-semibold text-foreground">{title}</h3>
          {meta && (
            <span className="shrink-0 text-xs tabular-nums text-muted-foreground">
              {meta}
            </span>
          )}
        </div>
        {actions && <div className="shrink-0">{actions}</div>}
      </header>
      <div className="p-4" style={{ height }}>
        {responsive ? (
          <ResponsiveContainer width="100%" height="100%">
            {children as ReactElement}
          </ResponsiveContainer>
        ) : (
          <div className="h-full overflow-auto">{children}</div>
        )}
      </div>
    </section>
  );
}

/** ReferenceLine 공통 스타일 — 점선 목표선 (P4). */
export const TARGET_LINE_PROPS = {
  stroke: 'hsl(var(--muted-foreground))',
  strokeDasharray: '4 4',
  strokeWidth: 1.5,
} as const;

/** ReferenceLine 라벨 공통 스타일. */
export const TARGET_LINE_LABEL_STYLE = {
  fill: 'hsl(var(--muted-foreground))',
  fontSize: 10,
} as const;

/** CartesianGrid 공통. */
export const CHART_GRID_PROPS = {
  strokeDasharray: '3 3',
  stroke: 'hsl(var(--border))',
} as const;

/** XAxis/YAxis tick 공통. */
export const CHART_AXIS_TICK_PROPS = {
  fontSize: 11,
  fill: 'hsl(var(--muted-foreground))',
} as const;

/** Tooltip contentStyle 공통. */
export const CHART_TOOLTIP_STYLE = {
  background: 'hsl(var(--popover))',
  border: '1px solid hsl(var(--border))',
  borderRadius: 8,
  fontSize: 12,
  boxShadow: '0 4px 16px rgb(0 0 0 / 0.08)',
} as const;
