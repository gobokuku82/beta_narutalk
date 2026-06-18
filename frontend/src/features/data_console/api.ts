/**
 * Data Console API — `/api/data/*` (Data DB, schema-per-client) TanStack Query 훅.
 *
 * 백엔드 계약: backend/api_v2/routes/data_console.py.
 * client = schema. 사용자는 SQL 0줄 — 훅이 REST 호출, 백엔드가 파라미터라이즈드 SQL.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { rest } from '@/api/rest';

export interface DataColumn {
  name: string;
  type: string;
}
export interface DataTable {
  name: string;
  row_count: number;
  pk_columns: string[];
}
export type DataRow = Record<string, unknown>;

interface TablesResp {
  client: string;
  total: number;
  tables: DataTable[];
}
interface RowsResp {
  client: string;
  table: string;
  columns: DataColumn[];
  pk_columns: string[];
  total: number;
  rows: DataRow[];
}

export function useDataTables(client: string | null) {
  return useQuery({
    queryKey: ['data', 'tables', client],
    enabled: !!client,
    queryFn: async () => (await rest.get(`/api/data/${client}/tables`)) as TablesResp,
  });
}

export function useDataRows(
  client: string | null,
  table: string | null,
  opts: { limit: number; offset: number; q: string },
) {
  return useQuery({
    queryKey: ['data', 'rows', client, table, opts.limit, opts.offset, opts.q],
    enabled: !!client && !!table,
    queryFn: async () => {
      const p = new URLSearchParams({ limit: String(opts.limit), offset: String(opts.offset) });
      if (opts.q) p.set('q', opts.q);
      return (await rest.get(`/api/data/${client}/tables/${table}/rows?${p}`)) as RowsResp;
    },
  });
}

export function useDeleteDataRow(client: string, table: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (pk: DataRow) =>
      rest.delete(`/api/data/${client}/tables/${table}/rows`, { pk }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['data'] }),
  });
}

export function useUpdateDataRow(client: string, table: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { pk: DataRow; updates: DataRow }) =>
      rest.patch(`/api/data/${client}/tables/${table}/rows`, vars),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['data'] }),
  });
}
