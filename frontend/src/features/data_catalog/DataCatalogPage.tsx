/**
 * DataCatalogPage — canonical 정형 데이터 전체를 '메뉴얼처럼' 펼쳐 골라보기.
 *
 * 좌: 소스별(광고/메시징/커머스/통합) 테이블 목록(정규화/계산/통합 + 행수).
 * 우: 선택 테이블의 컬럼 사전(의미) + 데이터(행). raw 제외 — raw 전용 페이지 별도(/db).
 * 행은 기존 data_console useDataRows(/api/data) 재사용.
 */
import { useState, type ReactNode } from 'react';
import { BookOpen, Search } from 'lucide-react';

import { PageHeader } from '@/components/layout/PageHeader';
import { DataTable, type DataTableColumn } from '@/components/viz/DataTable';
import { useDataRows, type DataRow } from '@/features/data_console/api';
import { useNavigation } from '@/features/navigation/store';
import { formatNumber } from '@/lib/format';
import { cn } from '@/lib/cn';
import { useCanonicalCatalog, type CatalogTable } from './api';

const NUMERIC = new Set(['bigint', 'integer', 'smallint', 'double precision', 'numeric', 'real']);
const ROW_LIMIT = 200;

function cell(v: unknown, type: string): ReactNode {
  if (v == null) return <span className="text-muted-foreground">—</span>;
  if (NUMERIC.has(type)) return typeof v === 'number' ? formatNumber(v) : String(v);
  if (typeof v === 'object') return <span className="text-muted-foreground">{JSON.stringify(v).slice(0, 80)}</span>;
  return String(v);
}

export function DataCatalogPage() {
  const client = useNavigation((s) => s.selectedClientId) ?? 'clumi';
  const { data: catalog, isLoading, error } = useCanonicalCatalog(client);
  const [selected, setSelected] = useState<string | null>(null);
  const [q, setQ] = useState('');

  const sources = catalog?.sources ?? [];
  const firstTable = sources[0]?.tables[0]?.table ?? null;
  const activeTable = selected ?? firstTable;

  // 선택 테이블 메타 + 소스 라벨
  let activeMeta: CatalogTable | undefined;
  let activeSourceLabel = '';
  for (const s of sources) {
    const t = s.tables.find((x) => x.table === activeTable);
    if (t) {
      activeMeta = t;
      activeSourceLabel = s.label;
      break;
    }
  }

  const rowsQuery = useDataRows(client, activeTable, { limit: ROW_LIMIT, offset: 0, q });
  const rows: DataRow[] = rowsQuery.data?.rows ?? [];
  const total = rowsQuery.data?.total ?? 0;

  const dataColumns: DataTableColumn<DataRow>[] = (activeMeta?.columns ?? []).map((c) => ({
    key: c.name,
    label: c.name,
    align: NUMERIC.has(c.type) ? 'right' : 'left',
    format: (v) => cell(v, c.type),
  }));

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="데이터 카탈로그"
        description="canonical 정형 데이터 전체 — 골라보기 (raw 제외, raw는 /db)"
        icon={BookOpen}
        badge="canonical"
      />

      {error && <p className="text-sm text-destructive">카탈로그를 불러오지 못했습니다.</p>}
      {isLoading && <p className="text-sm text-muted-foreground">불러오는 중…</p>}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr]">
        {/* 좌: 소스/테이블 네비 */}
        <aside className="space-y-3 self-start rounded-lg border border-border bg-card p-3">
          {sources.map((s, i) => {
            const showGroup = i === 0 || sources[i - 1]!.group !== s.group;
            return (
              <div key={s.source}>
                {showGroup && (
                  <p className="px-1 pb-1 pt-2 text-2xs font-medium uppercase tracking-wide text-muted-foreground first:pt-0">
                    {s.group}
                  </p>
                )}
                <p className="px-1 text-xs font-semibold text-foreground">{s.label}</p>
                <div className="mt-1 space-y-0.5">
                  {s.tables.map((t) => (
                    <button
                      key={t.table}
                      type="button"
                      onClick={() => setSelected(t.table)}
                      className={cn(
                        'flex w-full items-center justify-between rounded-md px-2 py-1 text-xs transition',
                        activeTable === t.table
                          ? 'bg-primary/10 font-medium text-primary'
                          : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground',
                      )}
                    >
                      <span>{t.layer_label}</span>
                      <span className="tabular-nums opacity-70">{formatNumber(t.row_count)}</span>
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </aside>

        {/* 우: 선택 테이블 상세 */}
        <div className="min-w-0 space-y-4">
          {activeMeta && (
            <>
              <div className="flex flex-wrap items-baseline justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="text-sm font-semibold text-foreground">
                    {activeSourceLabel} · {activeMeta.layer_label}
                  </h2>
                  <p className="truncate font-mono text-2xs text-muted-foreground">
                    {activeMeta.table} · {formatNumber(activeMeta.row_count)}행
                  </p>
                </div>
                <div className="relative">
                  <Search className="pointer-events-none absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                  <input
                    value={q}
                    onChange={(e) => setQ(e.target.value)}
                    placeholder="행 검색…"
                    className="h-8 w-48 rounded-md border border-border bg-card pl-7 pr-2 text-xs outline-none focus:ring-1 focus:ring-primary/40"
                  />
                </div>
              </div>

              {/* 컬럼 사전 (의미) */}
              <div className="space-y-2">
                <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">컬럼 사전</h3>
                <div className="overflow-x-auto rounded-lg border border-border bg-card">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-border text-left text-muted-foreground">
                        <th className="px-3 py-1.5 font-medium">컬럼</th>
                        <th className="px-3 py-1.5 font-medium">타입</th>
                        <th className="px-3 py-1.5 font-medium">의미</th>
                      </tr>
                    </thead>
                    <tbody>
                      {activeMeta.columns.map((c) => (
                        <tr key={c.name} className="border-b border-border last:border-0">
                          <td className="px-3 py-1.5 font-mono text-foreground">{c.name}</td>
                          <td className="px-3 py-1.5 text-muted-foreground">{c.type}</td>
                          <td className="px-3 py-1.5">
                            {c.desc ?? <span className="text-muted-foreground">—</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 데이터 */}
              <div className="space-y-2">
                <div className="flex items-baseline gap-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">데이터</h3>
                  <span className="text-2xs text-muted-foreground">
                    {total > ROW_LIMIT ? `총 ${formatNumber(total)}행 중 ${ROW_LIMIT}개 표시` : `${formatNumber(total)}행`}
                  </span>
                </div>
                {rowsQuery.isLoading ? (
                  <p className="text-xs text-muted-foreground">불러오는 중…</p>
                ) : rows.length ? (
                  <DataTable columns={dataColumns} rows={rows} />
                ) : (
                  <p className="text-xs text-muted-foreground">행 없음.</p>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
