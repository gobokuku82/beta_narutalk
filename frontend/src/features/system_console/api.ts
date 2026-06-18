/**
 * System Console API — `/api/system/*` 의 zod schema + TanStack Query 훅.
 *
 * 백엔드 계약: backend/api_v2/routes/system_console.py.
 * 사용자는 SQL 0줄 — 이 훅들이 REST 호출, 백엔드가 파라미터라이즈드 SQL 실행.
 * (훅/타입명은 범용 유지 — 추후 Data 콘솔이 같은 엔진 재사용)
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { z } from 'zod';

import { rest } from '@/api/rest';

// ── 스키마 ──
export const DbColumnSchema = z.object({ name: z.string(), type: z.string() });
export type DbColumn = z.infer<typeof DbColumnSchema>;

export const DbTableSchema = z.object({
  name: z.string(),
  row_count: z.number().int(),
  is_system: z.boolean(),
  pk_columns: z.array(z.string()),
});
export type DbTable = z.infer<typeof DbTableSchema>;

export const DbTablesSchema = z.object({
  total: z.number().int(),
  tables: z.array(DbTableSchema),
});

export const DbRowsSchema = z.object({
  table: z.string(),
  is_system: z.boolean(),
  columns: z.array(DbColumnSchema),
  pk_columns: z.array(z.string()),
  total: z.number().int(),
  rows: z.array(z.record(z.unknown())),
});
export type DbRows = z.infer<typeof DbRowsSchema>;

export type DbRow = Record<string, unknown>;

// ── 조회 ──
export function useDbTables() {
  return useQuery({
    queryKey: ['db', 'tables'],
    queryFn: async () => DbTablesSchema.parse(await rest.get('/api/system/tables')),
  });
}

export function useDbRows(
  table: string | null,
  opts: { limit: number; offset: number; q: string },
) {
  return useQuery({
    queryKey: ['db', 'rows', table, opts.limit, opts.offset, opts.q],
    enabled: !!table,
    queryFn: async () => {
      const params = new URLSearchParams({
        limit: String(opts.limit),
        offset: String(opts.offset),
      });
      if (opts.q) params.set('q', opts.q);
      return DbRowsSchema.parse(await rest.get(`/api/system/tables/${table}/rows?${params}`));
    },
  });
}

// ── 변경 (삭제/수정) — 성공 시 db 쿼리 무효화로 자동 갱신 ──
export function useDeleteDbRow(table: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (pk: DbRow) =>
      rest.delete(`/api/system/tables/${table}/rows`, { pk }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['db'] }),
  });
}

export function useUpdateDbRow(table: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { pk: DbRow; updates: DbRow }) =>
      rest.patch(`/api/system/tables/${table}/rows`, vars),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['db'] }),
  });
}
