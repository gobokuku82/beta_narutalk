/**
 * ChannelComparison — 채널별 small multiples (통합계획서 §5.6 / 원칙 P6).
 *
 * Status: complete.
 *
 * 단일 ROAS 막대 비교가 아닌 채널 *역할 존중*:
 *  - 채널마다 별도 패널 — 채널 색·이름·핵심 지표·목표 대비
 *  - 같은 잣대 강요 안 함 (검색 vs 소셜 ROAS 기대치 다름)
 *  - 채널별 미니 sparkline 옵션
 */
import type { TargetStatus } from './MetricChainStrip';
import { cn } from '@/lib/cn';

export interface ChannelMetric {
  label: string;
  value: string;
  target?: { label: string; status: TargetStatus };
}

export interface ChannelPanel {
  name: string;
  /** hsl 색상 — 보통 hsl(var(--channel-naver)) 등. */
  color: string;
  /** 채널 역할 — 예: '검색', '디스플레이/소셜'. */
  role?: string;
  metrics: ChannelMetric[];
  /** sparkline 데이터 (선택). */
  sparkData?: number[];
}

interface ChannelComparisonProps {
  channels: ChannelPanel[];
  className?: string;
}

export function ChannelComparison({
  channels,
  className,
}: ChannelComparisonProps) {
  return (
    <div
      className={cn('grid gap-3', className)}
      style={{
        gridTemplateColumns: `repeat(${channels.length}, minmax(0, 1fr))`,
      }}
    >
      {channels.map((ch) => (
        <ChannelPanelCard key={ch.name} panel={ch} />
      ))}
    </div>
  );
}

function ChannelPanelCard({ panel }: { panel: ChannelPanel }) {
  return (
    // VOCABULARY.md §5.1 H1~H4 — 외곽 카드 hover (Card 와 일관)
    <div className="rounded-lg border border-border bg-card p-3 transition duration-200 hover:-translate-y-1 hover:bg-primary/4 hover:ring-1 hover:ring-primary/40">
      <header className="flex items-baseline justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <span
            aria-hidden
            className="h-2.5 w-2.5 shrink-0 rounded-full"
            style={{ background: panel.color }}
          />
          <span className="truncate text-sm font-semibold text-foreground">
            {panel.name}
          </span>
        </div>
        {panel.role && (
          <span className="text-2xs uppercase tracking-wide text-muted-foreground">
            {panel.role}
          </span>
        )}
      </header>
      {panel.sparkData && panel.sparkData.length > 1 && (
        <Sparkline
          data={panel.sparkData}
          color={panel.color}
          className="mt-2"
        />
      )}
      <div className="mt-2 space-y-1">
        {panel.metrics.map((m, i) => (
          <div
            key={i}
            className="flex items-baseline justify-between gap-2 text-xs"
          >
            <span className="text-muted-foreground">{m.label}</span>
            <div className="flex items-baseline gap-2">
              <span className="text-sm font-medium tabular-nums text-foreground">
                {m.value}
              </span>
              {m.target && (
                <span
                  className={cn(
                    'text-2xs font-medium',
                    m.target.status === 'above' && 'text-success',
                    m.target.status === 'below' && 'text-destructive',
                    m.target.status === 'on' && 'text-muted-foreground',
                  )}
                >
                  {m.target.label}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Sparkline({
  data,
  color,
  className,
}: {
  data: number[];
  color: string;
  className?: string;
}) {
  const w = 100;
  const h = 24;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((v - min) / range) * h;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(' ');
  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      className={cn('h-6 w-full', className)}
      preserveAspectRatio="none"
    >
      <polyline points={points} fill="none" stroke={color} strokeWidth={1.5} />
    </svg>
  );
}
