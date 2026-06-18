/**
 * useCostOverview — `/cost` 페이지 데이터 source.
 *
 * GET /api/dashboard1/cost-overview?client=&period= → KPI·채널비중·키워드 ROI 한 번에.
 * 백엔드 조립(PipelineRunner → Postgres). 대시보드 useDashboardOverview 와 동일 패턴.
 */
import { useQuery } from '@tanstack/react-query';

import { rest } from '@/api/rest';

export interface CostOverview {
  client: string;
  period: string;
  kpi: {
    total_budget: number;
    avg_exec_rate: number; // %
    avg_roas: number; // %
    keyword_count: number;
  };
  channels: { channel: string; budget: number; share: number }[];
  keywords: {
    keyword: string;
    channel: string;
    cost: number; // ← ad_cost
    conv: number; // ← conversions
    cpa: number; // 유도
    roas: number; // %
    qs: number; // ← quality_score
  }[];
  pacing: {
    id: string;
    name: string;
    budget: number;
    spent: number;
    periodProgress: number; // 0~1 (데이터일수/그달총일수)
  }[];
}

export function useCostOverview(client: string | undefined, period: string) {
  return useQuery({
    queryKey: ['costOverview', client, period],
    enabled: !!client,
    queryFn: async () =>
      (await rest.get(
        `/api/dashboard1/cost-overview?client=${client}&period=${period}`,
      )) as CostOverview,
    staleTime: 5 * 60_000,
  });
}
