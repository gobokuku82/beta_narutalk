/**
 * PageHeader — 페이지 상단 공통 헤더.
 *
 * 2026 Warm Neutral — 플랫. 그라데이션/blob 없음.
 * hairline 하단 보더 + 중립 아이콘 칩 + 제목/설명.
 */
import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';

interface PageHeaderProps {
  /** string 또는 ReactNode — 일부 글자에 액센트 색을 줄 때 ReactNode (PALETTE.md §8.2 C) */
  title: string | ReactNode;
  description?: string;
  badge?: string;
  icon?: LucideIcon;
  actions?: ReactNode;
}

export function PageHeader({ title, description, badge, icon: Icon, actions }: PageHeaderProps) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border pb-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-3.5 w-3.5 shrink-0 text-muted-foreground" aria-hidden />}
          <h1 className="text-heading-sm font-display text-foreground">{title}</h1>
          {badge && (
            <span className="rounded-control bg-muted px-2 py-1 text-2xs font-medium text-muted-foreground">
              {badge}
            </span>
          )}
        </div>
        {description && (
          <p className="mt-1 text-xs text-muted-foreground">{description}</p>
        )}
      </div>
      {actions && <div className="shrink-0">{actions}</div>}
    </div>
  );
}
