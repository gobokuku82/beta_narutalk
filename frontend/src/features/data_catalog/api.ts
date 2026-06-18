/**
 * Data Catalog API — `/api/canonical/catalog` TanStack Query 훅.
 *
 * canonical 정형 테이블(정규화/계산/통합)을 소스별로 묶어 메타·컬럼 사전·행수 반환.
 * 행 데이터는 기존 data_console `useDataRows`(/api/data/*) 재사용 — 카탈로그=메타만.
 * data_console/api.ts 의 plain-interface + cast 패턴 답습.
 */
import { useQuery } from '@tanstack/react-query';

import { rest } from '@/api/rest';

export interface CatalogColumn {
  name: string;
  type: string;
  desc: string | null;
}
export interface CatalogTable {
  table: string;
  layer: string;
  layer_label: string;
  row_count: number;
  columns: CatalogColumn[];
}
export interface CatalogSource {
  source: string;
  label: string;
  group: string;
  tables: CatalogTable[];
}
export interface CatalogResp {
  client: string;
  sources: CatalogSource[];
}

export function useCanonicalCatalog(client: string | null) {
  return useQuery({
    queryKey: ['canonical', 'catalog', client],
    enabled: !!client,
    queryFn: async () =>
      (await rest.get(`/api/canonical/catalog?client=${client}`)) as CatalogResp,
    staleTime: 5 * 60_000,
  });
}
