/**
 * 포맷 헬퍼 — 숫자 / 통화 / 퍼센트.
 */

export function formatNumber(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return '-';
  return new Intl.NumberFormat('ko-KR').format(n);
}

export function formatCurrency(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return '-';
  return `₩${new Intl.NumberFormat('ko-KR').format(n)}`;
}

export function formatPercent(n: number | null | undefined, digits = 1): string {
  if (n == null || Number.isNaN(n)) return '-';
  return `${n.toFixed(digits)}%`;
}

export function formatCompact(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return '-';
  return new Intl.NumberFormat('ko-KR', { notation: 'compact' }).format(n);
}
