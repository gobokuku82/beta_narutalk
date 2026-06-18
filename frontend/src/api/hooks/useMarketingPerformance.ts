/**
 * useMarketingPerformance — `/api/canonical/marketing-performance` TanStack Query 래퍼.
 *
 * World-A canonical 정형 테이블 직접 서빙(dashboard1 _workspace 캐시 경로와 별개).
 * useMonthlyData.ts 패턴 답습: client = navigation store selectedClientId (없으면 'clumi'),
 * URL ?client=&period=, queryKey 에 client/period 포함 → 변경 시 자동 refetch.
 */
import { useQuery } from '@tanstack/react-query';

import { rest } from '../rest';
import { MarketingPerformanceSchema } from '@/features/marketing-performance/types';
import { useNavigation } from '@/features/navigation/store';

const STALE_MS = 5 * 60_000;
const DEFAULT_CLIENT = 'clumi';

export function useMarketingPerformance(period: string) {
  const client = useNavigation((s) => s.selectedClientId) ?? DEFAULT_CLIENT;
  return useQuery({
    queryKey: ['canonical', 'marketing-performance', client, period] as const,
    queryFn: async () => {
      const raw = await rest.get(
        `/api/canonical/marketing-performance?client=${client}&period=${period}`,
      );
      return MarketingPerformanceSchema.parse(raw);
    },
    staleTime: STALE_MS,
  });
}
