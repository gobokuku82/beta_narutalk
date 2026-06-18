/**
 * 차트 컬러 / 스타일 상수 — Recharts 용.
 *
 * Recharts 의 fill/stroke 는 CSS 색상 문자열을 받으므로 hsl(var(--token)) 사용 가능.
 * 디자인 토큰 (globals.css) 과 단일 소스 유지.
 */

/** 비채널 다계열용 차트 팔레트 5색. 채널 분해는 channelColor() 사용. */
export const CHART = ['hsl(var(--chart-1))', 'hsl(var(--chart-2))', 'hsl(var(--chart-3))', 'hsl(var(--chart-4))', 'hsl(var(--chart-5))'] as const;

/** 매체명 → 브랜드 컬러. */
export const CHANNEL_COLOR: Record<string, string> = {
  네이버: 'hsl(var(--channel-naver))',
  카카오: 'hsl(var(--channel-kakao))',
  메타: 'hsl(var(--channel-meta))',
  구글: 'hsl(var(--channel-google))',
};

export function channelColor(name: string | null | undefined): string {
  return (name && CHANNEL_COLOR[name]) || CHART[0];
}

/** Recharts <Tooltip contentStyle> 공통 스타일. */
export const CHART_TOOLTIP_STYLE = {
  background: 'hsl(var(--popover))',
  border: '1px solid hsl(var(--border))',
  borderRadius: 12,
  fontSize: 12,
  boxShadow: '0 4px 16px rgb(0 0 0 / 0.08)',
} as const;
