/**
 * Clients API — GET /api/admin/clients.
 *
 * 백엔드(admin.py)가 data/{client}/raw/ 를 스캔해 사용 가능 client 목록을 반환.
 * → client 추가 = data 폴더만 만들면 자동(하드코딩 없음). TopBar 드롭다운의 source.
 */
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';

import { useNavigation } from '@/features/navigation/store';

import { rest } from './rest';

export const ClientSchema = z.object({
  id: z.string(),
  name: z.string(),
  raw_count: z.number().int(),
});
export type Client = z.infer<typeof ClientSchema>;

export const ClientsResponseSchema = z.object({
  clients: z.array(ClientSchema),
  count: z.number().int(),
});

/** 사용 가능 client 목록 (data/{client}/raw/ 존재 기준). */
export function useClients() {
  return useQuery({
    queryKey: ['clients'],
    queryFn: async () => {
      const raw = await rest.get('/api/admin/clients');
      return ClientsResponseSchema.parse(raw).clients;
    },
    staleTime: 5 * 60_000,
  });
}

/**
 * 현재 client — store 선택값 우선, 없으면 **데이터 기반**(데이터 있는 첫 client → 첫 client).
 * 미선택/로딩 중이면 `undefined` → 호출부는 `enabled: !!client` 로 게이트.
 * ①.6c (2026-05-29): 'clumi' 하드코딩 제거 — 코드는 "목록의 첫 client" 규칙만 안다.
 */
export function useCurrentClient(): string | undefined {
  const selected = useNavigation((s) => s.selectedClientId);
  const { data: clients = [] } = useClients();
  return selected ?? clients.find((c) => c.raw_count > 0)?.id ?? clients[0]?.id;
}
