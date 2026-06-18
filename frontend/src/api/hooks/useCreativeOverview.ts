/**
 * useCreativeOverview — `/creatives` 페이지 데이터 source.
 *
 * GET /api/dashboard1/creative-overview?client=&period= → 소재별 성과 표.
 * 백엔드 조립(creatives raw → Postgres). overview 패턴 동일.
 */
import { useQuery } from '@tanstack/react-query';

import { rest } from '@/api/rest';

export interface CreativeOverview {
  client: string;
  period: string;
  creatives: {
    id: string;
    name: string;
    channel: string;
    ctr: number; // %
    cvr: number; // %
    roas: number; // %
    frequency: number;
    fatigue: boolean; // frequency≥3.5 유도
  }[];
}

export function useCreativeOverview(client: string | undefined, period: string) {
  return useQuery({
    queryKey: ['creativeOverview', client, period],
    enabled: !!client,
    queryFn: async () =>
      (await rest.get(
        `/api/dashboard1/creative-overview?client=${client}&period=${period}`,
      )) as CreativeOverview,
    staleTime: 5 * 60_000,
  });
}
