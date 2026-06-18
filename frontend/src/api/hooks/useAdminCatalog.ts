/**
 * Admin Catalog hooks — `/api/admin/*` 시스템 메타 조회.
 *
 * Step F7 (2026-05-27): workflow tool palette 데이터 source.
 *
 * 진실 소스: backend/api_v2/routes/admin.py
 * spec: docs/_claude/architecture/frontend_dashboard1_2026-05-26.md §5 Step F7
 */
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';

import { rest } from '../rest';

const STALE_MS = 5 * 60_000; // 5분 — catalog 는 정적 (YAML 로딩 시점 변화 없음)

// ─────────────────────────────────────────────────────────────────
// /api/admin/catalog
// ─────────────────────────────────────────────────────────────────

export const ToolParameterSchema = z.object({
  name: z.string(),
  type: z.string(),
  required: z.boolean(),
  default: z.unknown().nullable().optional(),
  description: z.string(),
});

export const ToolMetaSchema = z.object({
  name: z.string(),
  description: z.string(),
  category: z.string(),
  parameters: z.array(ToolParameterSchema),
  produces: z.array(z.string()),
  dependencies: z.array(z.string()),
  timeout_sec: z.number().int(),
  requires_approval: z.boolean(),
  has_cost: z.boolean(),
});

export const CatalogSchema = z.object({
  total: z.number().int(),
  by_category: z.record(z.number().int()),
  tools: z.array(ToolMetaSchema),
});

export type ToolMeta = z.infer<typeof ToolMetaSchema>;
export type Catalog = z.infer<typeof CatalogSchema>;

export function useAdminCatalog() {
  return useQuery({
    queryKey: ['admin', 'catalog'] as const,
    queryFn: async () => CatalogSchema.parse(await rest.get('/api/admin/catalog')),
    staleTime: STALE_MS,
  });
}

// ─────────────────────────────────────────────────────────────────
// /api/admin/clients
// ─────────────────────────────────────────────────────────────────

export const ClientSchema = z.object({
  id: z.string(),
  name: z.string(),
  raw_count: z.number().int(),
});

export const ClientsSchema = z.object({
  clients: z.array(ClientSchema),
  count: z.number().int(),
});

export type ClientInfo = z.infer<typeof ClientSchema>;

export function useAdminClients() {
  return useQuery({
    queryKey: ['admin', 'clients'] as const,
    queryFn: async () => ClientsSchema.parse(await rest.get('/api/admin/clients')),
    staleTime: STALE_MS,
  });
}
