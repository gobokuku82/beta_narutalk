/**
 * Monthly period 상수 + helper.
 *
 * MVP: 4월·3월 고정. 추후 임의 YYYY-MM 지원 시 selector 추가.
 * (이전 features/_pipeline/periods 에서 monthly 폴더 내부로 인라인 — 2026-06-08)
 */

export const CURRENT_PERIOD = '2026-04' as const;
export const PREVIOUS_PERIOD = '2026-03' as const;

export type Period = string;

export function periodLabel(period: Period): string {
  const m = /^(\d{4})-(\d{2})$/.exec(period);
  if (!m || !m[1] || !m[2]) return period;
  return `${m[1]}년 ${parseInt(m[2], 10)}월`;
}
