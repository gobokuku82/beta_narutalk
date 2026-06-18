/**
 * useChannelOverview — `/channel` 페이지 데이터 source.
 *
 * GET /api/dashboard1/channel-overview?client=&period= → 채널 비교 + 3단계 퍼널.
 * 백엔드 조립(PipelineRunner → Postgres). 대시보드/비용 overview 와 동일 패턴.
 */
import { useQuery } from '@tanstack/react-query';

import { rest } from '@/api/rest';

export interface ChannelOverview {
  client: string;
  period: string;
  channels: {
    channel: string;
    roas: number; // %
    cpa: number; // 원
    conversions: number;
    spark: number[]; // 일별 ROAS 추이
    target_roas: number | null;
    target_cpa: number | null;
  }[];
  funnel: { label: string; value: number }[];
}

export function useChannelOverview(client: string | undefined, period: string) {
  return useQuery({
    queryKey: ['channelOverview', client, period],
    enabled: !!client,
    queryFn: async () =>
      (await rest.get(
        `/api/dashboard1/channel-overview?client=${client}&period=${period}`,
      )) as ChannelOverview,
    staleTime: 5 * 60_000,
  });
}
