/**
 * MetricDiscoveryDialog — 지표 발견기.
 *
 * 빈 폼이 아니라, 데이터 모양(ERD)에서 후보 지표를 자동 제안(metrics.suggestMetrics)하고,
 * 고른 후보의 SQL 초안(metricToSql)을 빌드된 SQLite 에 바로 돌려(/query) 실제 숫자를 본다.
 * = "무엇을 볼지" 설계의 가이드형 진입점. (Phase 1a 빌드와 루프가 닫힘 — 먼저 [DB 빌드] 필요.)
 */
import { useMemo, useState } from 'react';
import { toast } from 'sonner';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/cn';
import { useDbDesign } from './store';
import { suggestMetrics, metricToSql, type Metric, type MetricKind, type ChartKind } from './metrics';
import { queryDb, type QueryResult } from '@/api/hooks/useDbDesign';

const CHART_ICON: Record<ChartKind, string> = { kpi: '🔢', line: '📈', bar: '📊', pie: '🥧', table: '▦' };
const KIND_LABEL: Record<MetricKind, string> = {
  kpi: 'KPI',
  trend: '추이',
  breakdown: 'Top-N',
  trend_by: '차원×시간',
  growth: '성장',
};

export function MetricDiscoveryDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  const tables = useDbDesign((s) => s.tables);
  const designName = useDbDesign((s) => s.name);

  const metrics = useMemo(() => (open ? suggestMetrics(tables) : []), [open, tables]);
  const grouped = useMemo(() => {
    const g = new Map<string, Metric[]>();
    for (const m of metrics) {
      const list = g.get(m.sourceTable) ?? [];
      list.push(m);
      g.set(m.sourceTable, list);
    }
    return [...g.entries()];
  }, [metrics]);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = metrics.find((m) => m.id === selectedId) ?? null;
  const [sql, setSql] = useState('');
  const [res, setRes] = useState<QueryResult | null>(null);
  const [running, setRunning] = useState(false);

  const pick = (m: Metric) => {
    setSelectedId(m.id);
    setSql(metricToSql(m));
    setRes(null);
  };

  const onRun = async () => {
    if (!sql.trim()) return;
    setRunning(true);
    try {
      setRes(await queryDb(designName, sql));
    } catch (e) {
      const msg = (e as Error).message;
      toast.error(/404|빌드/.test(msg) ? '먼저 [DB 빌드]로 데이터를 적재하세요' : `쿼리 오류: ${msg}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (!v) {
          setSelectedId(null);
          setRes(null);
        }
        onOpenChange(v);
      }}
    >
      <DialogContent className="flex h-[80vh] max-w-4xl flex-col">
        <DialogHeader>
          <DialogTitle>지표 발견기</DialogTitle>
          <DialogDescription>
            데이터 모양에서 <b>후보 지표를 자동 제안</b>합니다(직접 발명 X). 고르면 SQL 초안이 나오고,
            <b> 빌드된 DB</b>에 바로 실행해 실제 숫자를 봅니다. ({metrics.length}개 후보)
          </DialogDescription>
        </DialogHeader>

        {metrics.length === 0 ? (
          <div className="rounded-input border border-dashed border-border px-4 py-10 text-center text-2xs text-muted-foreground">
            측정값(숫자)을 가진 <b>팩트 테이블</b>이 없습니다.
            <br />
            실적·매출 같은 수치 칼럼이 있는 표가 있어야 지표를 제안할 수 있어요.
          </div>
        ) : (
          <div className="flex min-h-0 flex-1 gap-3">
            {/* 후보 목록 */}
            <div className="flex w-2/5 min-h-0 flex-col gap-2 overflow-y-auto pr-1">
              {grouped.map(([table, list]) => (
                <div key={table}>
                  <div className="sticky top-0 bg-background py-0.5 text-2xs font-semibold text-muted-foreground">
                    {table} <span className="font-normal">({list.length})</span>
                  </div>
                  <ul className="flex flex-col gap-0.5">
                    {list.map((m) => (
                      <li key={m.id}>
                        <button
                          type="button"
                          onClick={() => pick(m)}
                          className={cn(
                            'flex w-full items-center gap-1.5 rounded-sm border px-1.5 py-1 text-left text-2xs',
                            selectedId === m.id
                              ? 'border-accent-action bg-accent-action/10'
                              : 'border-transparent hover:bg-muted/50',
                          )}
                        >
                          <span>{CHART_ICON[m.chart]}</span>
                          <span className="flex-1 truncate">{m.name}</span>
                          <span className="shrink-0 rounded-sm bg-muted px-1 text-[10px] text-muted-foreground">
                            {KIND_LABEL[m.kind]}
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>

            {/* 상세 + SQL + 실행 */}
            <div className="flex w-3/5 min-h-0 flex-col gap-2 border-l border-border pl-3">
              {!selected ? (
                <div className="flex flex-1 items-center justify-center text-center text-2xs text-muted-foreground">
                  왼쪽에서 지표를 선택하세요.
                </div>
              ) : (
                <>
                  <div className="text-sm font-semibold">
                    {CHART_ICON[selected.chart]} {selected.name}
                  </div>
                  <div className="flex flex-wrap gap-2 text-2xs text-muted-foreground">
                    <span>차트 <b className="text-foreground">{selected.chart}</b></span>
                    <span>집계 <b className="text-foreground font-mono">{selected.aggregate}({selected.measure ?? '*'})</b></span>
                    {selected.dimensions.length > 0 && (
                      <span>차원 <b className="text-foreground">{selected.dimensions.map((d) => d.column).join(' × ')}</b></span>
                    )}
                  </div>
                  <textarea
                    value={sql}
                    onChange={(e) => setSql(e.target.value)}
                    className="h-28 w-full resize-none rounded-input border border-input bg-background p-2 font-mono text-2xs focus:outline-none"
                    spellCheck={false}
                  />
                  <div className="flex items-center gap-2">
                    <span className="text-2xs text-muted-foreground">SQL 초안 — 고쳐서 탐색 가능</span>
                    <Button size="sm" variant="outline" className="ml-auto h-7 text-2xs" onClick={onRun} disabled={running}>
                      {running ? '실행 중…' : '▶ 빌드 DB에 실행'}
                    </Button>
                  </div>

                  {res && (
                    <div className="min-h-0 flex-1 overflow-auto rounded-input border border-border">
                      <table className="w-full border-collapse text-2xs">
                        <thead>
                          <tr className="bg-muted/50">
                            {res.columns.map((c) => (
                              <th key={c} className="sticky top-0 border-b border-border bg-muted/50 px-2 py-1 text-left font-semibold">
                                {c}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {res.rows.map((row, ri) => (
                            <tr key={ri} className="odd:bg-muted/20">
                              {row.map((cell, ci) => (
                                <td key={ci} className="whitespace-nowrap border-b border-border/50 px-2 py-1 font-mono">
                                  {cell === null ? '∅' : typeof cell === 'number' ? cell.toLocaleString() : String(cell)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {res.rows.length === 0 && (
                        <div className="px-2 py-2 text-2xs text-muted-foreground">결과 0행</div>
                      )}
                      {res.truncated && (
                        <div className="px-2 py-1 text-2xs text-muted-foreground">… 상한까지만 표시</div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
