/**
 * useDashboardOverview — `/dashboard` 페이지 데이터 source.
 *
 * GET /api/dashboard1/overview?client=&period= → 퍼널·비율·일별ROAS·월목표 한 번에.
 * 백엔드 조립(PipelineRunner → Postgres). 월간결산 useMonthlyData 와 동일 패턴.
 */
import { useQuery } from '@tanstack/react-query';

import { rest } from '@/api/rest';

export interface DashboardOverview {
  client: string;
  period: string;
  funnel: {
    impressions: number;
    clicks: number;
    conversions: number;
    conversion_revenue: number;
  };
  ratios: {
    ctr: number; // %
    cvr: number; // %
    aov: number; // 원
    roas: number; // % (광고성과: 전환매출÷광고비)
  };
  daily: { date: string; roas: number }[];
  targets: {
    target_impressions?: number;
    target_clicks?: number;
    target_conversions?: number;
    target_ctr?: number;
    target_cvr?: number;
    target_roas?: number;
    breakeven_roas?: number;
  };
}

export function useDashboardOverview(client: string | undefined, period: string) {
  return useQuery({
    queryKey: ['dashboardOverview', client, period],
    enabled: !!client,
    queryFn: async () =>
      (await rest.get(
        `/api/dashboard1/overview?client=${client}&period=${period}`,
      )) as DashboardOverview,
    staleTime: 5 * 60_000,
  });
}
