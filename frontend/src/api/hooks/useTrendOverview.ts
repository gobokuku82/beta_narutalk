/**
 * useTrendOverview — `/trend` 페이지 데이터 source.
 *
 * GET /api/dashboard1/trend-overview?client=&period= → 일별 노출·전환·ROAS 시계열 + 목표선.
 * 백엔드 조립(daily_performance 날짜 집계 → Postgres). overview 패턴 동일.
 */
import { useQuery } from '@tanstack/react-query';

import { rest } from '@/api/rest';

export interface TrendOverview {
  client: string;
  period: string;
  daily: {
    date: string;
    impressions: number;
    clicks: number;
    conversions: number;
    roas: number; // %
  }[];
  target_roas: number | null;
  breakeven_roas: number | null;
}

export function useTrendOverview(client: string | undefined, period: string) {
  return useQuery({
    queryKey: ['trendOverview', client, period],
    enabled: !!client,
    queryFn: async () =>
      (await rest.get(
        `/api/dashboard1/trend-overview?client=${client}&period=${period}`,
      )) as TrendOverview,
    staleTime: 5 * 60_000,
  });
}
