/**
 * FunnelChart — 단계별 CVR + 드롭오프 (통합계획서 §5.5 / 원칙 P6).
 *
 * Status: complete.
 *
 * progress bar 묶음이 아닌 진짜 퍼널:
 *  - 단계별 절대값 + 폭(전체 첫 단계 대비)
 *  - 단계 간 CVR (이전 → 현재, %) 명시
 *  - 누적 CVR (첫 단계 대비) 동반 표시
 *  - 드롭오프(이탈량) 강조
 */
import { cn } from '@/lib/cn';

export interface FunnelStage {
  label: string;
  value: number;
  /** 단계 CVR (이전 단계 대비, %) — 미지정 시 자동 계산. */
  stepCvr?: number;
}

interface FunnelChartProps {
  stages: FunnelStage[];
  /** 폭 색 — default chart-1. */
  color?: string;
  /** 절대값 포맷터 — default ko-KR locale. */
  formatValue?: (v: number) => string;
  className?: string;
}

export function FunnelChart({
  stages,
  color = 'hsl(var(--chart-1))',
  formatValue = (v) => v.toLocaleString('ko-KR'),
  className,
}: FunnelChartProps) {
  if (stages.length === 0) return null;
  const top = stages[0]!.value;

  return (
    <div className={cn('space-y-2', className)}>
      {stages.map((stage, i) => {
        const prev = i > 0 ? stages[i - 1] : null;
        const stepCvr =
          stage.stepCvr != null
            ? stage.stepCvr
            : prev && prev.value > 0
              ? (stage.value / prev.value) * 100
              : null;
        const totalCvr = top > 0 ? (stage.value / top) * 100 : 0;
        const widthPct = top > 0 ? (stage.value / top) * 100 : 0;
        const dropoff = prev ? prev.value - stage.value : 0;

        return (
          // Stage hover (2026-06-10 재도입, A 안 시도) — bar opacity 0.85 → 1.0
          //   외곽 ChartFrame hover (ring + bg-primary/4) 와 다른 속성 → 누적/dilution 없음.
          //   마케팅 5매체 분배 (recharts BarChart) 의 자동 bar hover 와 정신 동등.
          <div key={i}>
            {i > 0 && stepCvr != null && (
              <div className="flex items-center gap-2 px-3 py-1 text-2xs text-muted-foreground">
                <span className="font-medium tabular-nums text-foreground">
                  {stepCvr.toFixed(1)}%
                </span>
                <span>이전 단계 대비 전환</span>
                {dropoff > 0 && (
                  <span className="ml-auto tabular-nums text-destructive/80">
                    −{formatValue(dropoff)} 이탈
                  </span>
                )}
              </div>
            )}
            <div className="group relative h-10 overflow-hidden rounded-md bg-muted/30 transition duration-200 hover:ring-2 hover:ring-primary/40">
              <div
                aria-hidden
                className="absolute inset-y-0 left-0 rounded-md opacity-80 transition-opacity duration-200 group-hover:opacity-100"
                style={{ width: `${widthPct}%`, background: color }}
              />
              <div className="relative flex h-full items-center justify-between gap-3 px-3 text-xs">
                <span className="font-medium text-foreground">{stage.label}</span>
                <span className="tabular-nums text-foreground">
                  {formatValue(stage.value)}
                  <span className="ml-2 text-muted-foreground">
                    ({totalCvr.toFixed(1)}%)
                  </span>
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
