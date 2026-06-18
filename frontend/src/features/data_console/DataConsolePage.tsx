/**
 * DataConsolePage — Data DB(client 정형 데이터) 무-SQL 콘솔 (`/db`).
 *
 * client(schema) 선택 → 그 client의 테이블을 표로 보고(조회) · 행 삭제 · 행 수정.
 * 백엔드 `/api/data/*` (data_console.py)가 SQL 전담. 사용자는 드롭다운·검색·폼만.
 *
 * [data-console] 신설 (2026-06-07). 삭제 시: features/data_console/ + router/Sidebar/navigation 항목 제거.
 */
import { useEffect, useState } from 'react';
import {
  Boxes,
  Search,
  Trash2,
  Pencil,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
} from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from '@/components/ui/sheet';
import { cn } from '@/lib/cn';
import { useCurrentClient } from '@/api/clients';
import {
  useDataTables,
  useDataRows,
  useDeleteDataRow,
  useUpdateDataRow,
  type DataRow,
} from './api';

const PAGE_SIZE = 50;

function cell(v: unknown): string {
  if (v === null || v === undefined) return '';
  return String(v);
}

export function DataConsolePage() {
  // client = 전역 단일 출처(navigation store). 선택 UI 는 TopBar (대시보드들과 동일 패턴). (2026-06-07)
  const client = useCurrentClient() ?? null;
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [q, setQ] = useState('');
  const [qInput, setQInput] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<DataRow | null>(null);
  const [editTarget, setEditTarget] = useState<DataRow | null>(null);
  const [editValues, setEditValues] = useState<Record<string, string>>({});

  const tablesQ = useDataTables(client);
  const rowsQ = useDataRows(client, selectedTable, { limit: PAGE_SIZE, offset: page * PAGE_SIZE, q });
  const deleteRow = useDeleteDataRow(client ?? '', selectedTable ?? '');
  const updateRow = useUpdateDataRow(client ?? '', selectedTable ?? '');

  // 전역 client 변경 시 페이지/검색 리셋 (테이블은 아래 effect 에서 첫 번째 자동 선택)
  useEffect(() => {
    setPage(0);
    setQ('');
    setQInput('');
  }, [client]);

  // client 바뀌면 테이블 자동 선택(첫 번째)
  useEffect(() => {
    if (client && tablesQ.data?.tables.length) {
      setSelectedTable((prev) =>
        prev && tablesQ.data.tables.some((t) => t.name === prev) ? prev : tablesQ.data.tables[0]!.name,
      );
    } else {
      setSelectedTable(null);
    }
  }, [client, tablesQ.data]);

  // 편집 드로어 열릴 때 폼 초기화
  useEffect(() => {
    if (editTarget && rowsQ.data) {
      const init: Record<string, string> = {};
      for (const c of rowsQ.data.columns) init[c.name] = cell(editTarget[c.name]);
      setEditValues(init);
    }
  }, [editTarget, rowsQ.data]);

  const selectTable = (name: string) => {
    setSelectedTable(name);
    setPage(0);
    setQ('');
    setQInput('');
  };

  const applySearch = () => {
    setQ(qInput.trim());
    setPage(0);
  };

  const rows = rowsQ.data?.rows ?? [];
  const columns = rowsQ.data?.columns ?? [];
  const pkCols = rowsQ.data?.pk_columns ?? [];
  const total = rowsQ.data?.total ?? 0;
  const canWrite = !!rowsQ.data && pkCols.length > 0;

  const pkOf = (row: DataRow): DataRow => Object.fromEntries(pkCols.map((c) => [c, row[c]]));

  const confirmDelete = () => {
    if (!deleteTarget) return;
    deleteRow.mutate(pkOf(deleteTarget), { onSuccess: () => setDeleteTarget(null) });
  };

  const saveEdit = () => {
    if (!editTarget) return;
    const updates: Record<string, unknown> = {};
    for (const c of columns) {
      if (pkCols.includes(c.name)) continue;
      const orig = cell(editTarget[c.name]);
      const next = editValues[c.name] ?? '';
      if (next !== orig) updates[c.name] = next === '' ? null : next;
    }
    if (Object.keys(updates).length === 0) {
      setEditTarget(null);
      return;
    }
    updateRow.mutate({ pk: pkOf(editTarget), updates }, { onSuccess: () => setEditTarget(null) });
  };

  return (
    <div className="flex h-full flex-col gap-4 p-6">
      <PageHeader
        title="DB"
        description="client별 데이터를 SQL 없이 조회 · 수정 · 삭제 (Data DB) · client는 상단에서 선택"
        icon={Boxes}
        badge={client ?? undefined}
        actions={
          <Button variant="outline" size="sm" onClick={() => tablesQ.refetch()}>
            <RefreshCw className="h-4 w-4" />
            새로고침
          </Button>
        }
      />

      <div className="flex min-h-0 flex-1 gap-4">
        {/* 좌: 테이블 목록 */}
        <aside className="w-56 shrink-0 space-y-2 overflow-y-auto">
          {!client && (
            <p className="px-2 text-sm text-muted-foreground">상단에서 client를 선택하세요.</p>
          )}
          {client && tablesQ.isLoading && (
            <p className="px-2 text-sm text-muted-foreground">불러오는 중…</p>
          )}
          {tablesQ.data?.tables.map((t) => (
            <button
              key={t.name}
              type="button"
              onClick={() => selectTable(t.name)}
              className={cn(
                'w-full rounded-lg border px-3 py-2 text-left transition-colors',
                selectedTable === t.name
                  ? 'border-primary bg-accent'
                  : 'border-border bg-card hover:bg-accent/50',
              )}
            >
              <span className="block truncate text-sm font-medium">{t.name}</span>
              <span className="text-xs text-muted-foreground">{t.row_count.toLocaleString()} 행</span>
            </button>
          ))}
          {tablesQ.data?.tables.length === 0 && (
            <p className="px-2 text-sm text-muted-foreground">이 client에 테이블이 없습니다.</p>
          )}
        </aside>

        {/* 우: 데이터 그리드 */}
        <section className="flex min-w-0 flex-1 flex-col gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative max-w-xs flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={qInput}
                onChange={(e) => setQInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && applySearch()}
                placeholder="이 테이블에서 검색…"
                className="pl-9"
                disabled={!selectedTable}
              />
            </div>
            <Button variant="outline" size="sm" onClick={applySearch} disabled={!selectedTable}>
              검색
            </Button>
          </div>

          <div className="min-h-0 flex-1 overflow-auto rounded-lg border border-border bg-card">
            {!selectedTable ? (
              <p className="p-4 text-sm text-muted-foreground">왼쪽에서 테이블을 선택하세요.</p>
            ) : rowsQ.isLoading ? (
              <p className="p-4 text-sm text-muted-foreground">불러오는 중…</p>
            ) : rows.length === 0 ? (
              <p className="p-4 text-sm text-muted-foreground">
                {q ? '검색 결과가 없습니다.' : '행이 없습니다.'}
              </p>
            ) : (
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-muted/60 backdrop-blur">
                  <tr className="text-left text-muted-foreground">
                    {columns.map((c) => (
                      <th key={c.name} className="whitespace-nowrap px-3 py-2 font-medium">
                        {c.name}
                        {pkCols.includes(c.name) && (
                          <span className="ml-1 text-2xs text-primary">PK</span>
                        )}
                      </th>
                    ))}
                    {canWrite && <th className="px-3 py-2" />}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, ri) => (
                    <tr key={ri} className="border-t border-border hover:bg-accent/30">
                      {columns.map((c) => (
                        <td
                          key={c.name}
                          className="max-w-[240px] truncate px-3 py-2 tabular-nums"
                          title={cell(row[c.name])}
                        >
                          {cell(row[c.name])}
                        </td>
                      ))}
                      {canWrite && (
                        <td className="whitespace-nowrap px-2 py-2 text-right">
                          <button
                            type="button"
                            onClick={() => setEditTarget(row)}
                            title="수정"
                            className="rounded-sm p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </button>
                          <button
                            type="button"
                            onClick={() => setDeleteTarget(row)}
                            title="삭제"
                            className="rounded-sm p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {total > 0 && (
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>
                {page * PAGE_SIZE + 1}–{page * PAGE_SIZE + rows.length} / {total.toLocaleString()}
              </span>
              <div className="flex items-center gap-1">
                <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}>
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={(page + 1) * PAGE_SIZE >= total}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </section>
      </div>

      {/* 삭제 확인 */}
      <Dialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              행을 삭제할까요?
            </DialogTitle>
            <DialogDescription>
              <code className="rounded-sm bg-muted px-1">
                {client}.{selectedTable}
              </code>{' '}
              에서 이 행이 영구 삭제됩니다.
            </DialogDescription>
          </DialogHeader>
          {deleteTarget && (
            <div className="rounded-md bg-muted/50 p-3 text-xs">
              {pkCols.map((c) => (
                <div key={c}>
                  <span className="text-muted-foreground">{c}:</span> {cell(deleteTarget[c])}
                </div>
              ))}
            </div>
          )}
          {deleteRow.isError && <p className="text-xs text-destructive">삭제 실패 — 다시 시도해주세요.</p>}
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              취소
            </Button>
            <Button variant="destructive" onClick={confirmDelete} disabled={deleteRow.isPending}>
              삭제
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 행 수정 */}
      <Sheet open={!!editTarget} onOpenChange={(o) => !o && setEditTarget(null)}>
        <SheetContent side="right" className="flex w-full flex-col gap-0 overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>행 수정</SheetTitle>
            <SheetDescription>
              <code className="rounded-sm bg-muted px-1">
                {client}.{selectedTable}
              </code>{' '}
              · 기본키(PK)는 수정 불가
            </SheetDescription>
          </SheetHeader>
          <div className="flex-1 space-y-3 py-4">
            {columns.map((c) => {
              const isPk = pkCols.includes(c.name);
              return (
                <div key={c.name} className="space-y-1">
                  <label className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                    {c.name}
                    <span className="text-2xs text-muted-foreground/60">{c.type}</span>
                    {isPk && <span className="text-2xs text-primary">PK</span>}
                  </label>
                  <Input
                    value={editValues[c.name] ?? ''}
                    onChange={(e) => setEditValues((v) => ({ ...v, [c.name]: e.target.value }))}
                    disabled={isPk}
                    className={cn(isPk && 'opacity-60')}
                  />
                </div>
              );
            })}
          </div>
          {updateRow.isError && (
            <p className="text-xs text-destructive">수정 실패 — 값/타입을 확인해주세요.</p>
          )}
          <SheetFooter>
            <Button variant="outline" onClick={() => setEditTarget(null)}>
              취소
            </Button>
            <Button onClick={saveEdit} disabled={updateRow.isPending}>
              저장
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </div>
  );
}
