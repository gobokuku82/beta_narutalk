/**
 * Brand — OctorAD 워드마크 (◈ OctorAD ·).
 *
 * 2026-06-09 Phase 4 신설. PALETTE §8.2 C (typography 위계) + 브랜드 액센트 dot.
 * 2026-06-10 v2: Link to="/" 추가 — 외부 프레임 좌상단 Brand 클릭 시 첫 진입 (PortfolioPage).
 *
 * 구성:
 *   ◈ (Diamond)  — text-muted-foreground/60, h-3.5 w-3.5 (브랜드 마크)
 *   OctorAD      — text-foreground, font-semibold tracking-tight
 *   ·            — text-primary, 옥스블러드 dot (브랜드 색 표시)
 *
 * size: 'sm' (TopBar) / 'md' (확장 footer 등)
 */
import { Diamond } from 'lucide-react';
import { Link } from '@tanstack/react-router';
import { cn } from '@/lib/cn';

interface BrandProps {
  size?: 'sm' | 'md';
  /** mark + dot 숨김 (아주 작은 공간 — 예: Sidebar collapsed) */
  compact?: boolean;
  className?: string;
}

export function Brand({ size = 'sm', compact = false, className }: BrandProps) {
  const wordmarkClass =
    size === 'sm'
      ? 'text-base font-semibold tracking-tight'
      : 'text-lg font-semibold tracking-tight';
  const iconClass = size === 'sm' ? 'h-3.5 w-3.5' : 'h-4 w-4';

  return (
    <Link
      to="/"
      className={cn(
        'inline-flex items-center gap-2 rounded-md transition-opacity duration-200 hover:opacity-80',
        className,
      )}
      aria-label="OctorAD 홈으로"
      title="홈"
    >
      {!compact && (
        <Diamond
          className={cn('text-muted-foreground/60 shrink-0', iconClass)}
          aria-hidden
        />
      )}
      <span className={cn('text-foreground', wordmarkClass)}>OctorAD</span>
      {!compact && (
        <span
          aria-hidden
          className={cn('font-semibold leading-none text-primary', size === 'sm' ? 'text-base' : 'text-lg')}
        >
          ·
        </span>
      )}
    </Link>
  );
}
