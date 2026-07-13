/**
 * DbBuildDialog — 설계(ERD) + 엑셀 데이터 → 실제 SQLite 빌드 & 검증.
 *
 * 엑셀을 다시 드롭하면 프론트가 행을 추출(헤더병합·언피벗 그대로)해 각 시트를 설계 테이블에
 * 매핑하고, /build 로 보내 SQLite 를 조립한다. 결과 = 적재 리포트 + 참조 무결성(FK orphan) +
 * "조립(JOIN) 미리보기"(SQL 입력 → /query). 파싱 진실 소스는 프론트(parseWorkbook/unpivot),
 * 백엔드는 빌드·검증·쿼리만. 데이터는 *위치(순서) 정렬*로 설계 칼럼에 싣는다(칼럼명 변경에도 견고).
 */
import { useMemo, useRef, useState } from 'react';
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
import { readWorkbooks, deriveTable, extractRows, type SheetSource, type CellValue } from './parseWorkbook';
import { detectPeriodRuns, unpivotRows } from './unpivot';
import { useDbDesign, type ErdTable } from './store';
import { buildDb, queryDb, type BuildReport, type QueryResult } from '@/api/hooks/useDbDesign';

const FILE_RE = /\.(xlsx|xlsm|xls|csv)$/i;
const ACCEPT = '.xlsx,.xlsm,.xls,.csv';

interface Parsed {
  id: string;
  fileName: string;
  sheetName: string;
  suggestedName: string;
  columns: string[];
  rows: CellValue[][];
  unpivoted: boolean;
}

function q(id: string): string {
  return '"' + String(id).replace(/"/g, '""') + '"';
}

/** 팩트(FK 보유) 1개를 골라 부모들을 JOIN 하는 기본 쿼리 — 사용자가 편집해 탐색. */
function defaultJoinSql(tables: ErdTable[]): string {
  const fact = tables.find((t) => t.columns.some((c) => c.fk)) ?? tables[0];
  if (!fact) return 'SELECT 1';
  const sel: string[] = fact.columns.filter((c) => !c.fk).slice(0, 4).map((c) => `t0.${q(c.name)}`);
  const joins: string[] = [];
  let i = 1;
  for (const c of fact.columns) {
    if (!c.fk) continue;
    const parent = tables.find((t) => t.name === c.fk!.table);
    if (!parent) continue;
    const a = `t${i++}`;
    joins.push(`JOIN ${q(parent.name)} ${a} ON t0.${q(c.name)} = ${a}.${q(c.fk.column)}`);
    const label = parent.columns.find((pc) => !pc.pk) ?? parent.columns[0];
    if (label) sel.push(`${a}.${q(label.name)}`);
  }
  return `SELECT ${sel.join(', ')}\nFROM ${q(fact.name)} t0\n${joins.join('\n')}\nLIMIT 50`;
}

export function DbBuildDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  const tables = useDbDesign((s) => s.tables);
  const designName = useDbDesign((s) => s.name);

  const [parsed, setParsed] = useState<Parsed[]>([]);
  const [mapping, setMapping] = useState<Record<string, string>>({}); // parsed.id → design table name | ''
  const [parsing, setParsing] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [building, setBuilding] = useState(false);
  const [report, setReport] = useState<BuildReport | null>(null);
  const [sql, setSql] = useState('');
  const [queryRes, setQueryRes] = useState<QueryResult | null>(null);
  const [querying, setQuerying] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const reset = () => {
    setParsed([]);
    setMapping({});
    setReport(null);
    setSql('');
    setQueryRes(null);
    setDragOver(false);
  };

  const designNames = useMemo(() => tables.map((t) => t.name), [tables]);

  const toParsed = (source: SheetSource): Parsed => {
    const base = deriveTable(source, source.detected.start, source.detected.count);
    const run = detectPeriodRuns(base.columns).find((r) => r.strong) ?? null;
    const ext = extractRows(source, source.detected.start, source.detected.count);
    const final = run ? unpivotRows(ext.columns, ext.rows, run) : ext;
    return {
      id: source.id,
      fileName: source.fileName,
      sheetName: source.sheetName,
      suggestedName: source.suggestedName,
      columns: final.columns,
      rows: final.rows,
      unpivoted: Boolean(run),
    };
  };

  const handleFiles = async (fileList: FileList | File[] | null) => {
    if (!fileList) return;
    const accepted = Array.from(fileList).filter((f) => FILE_RE.test(f.name));
    if (!accepted.length) {
      toast.error('엑셀/CSV 파일이 아닙니다');
      return;
    }
    setParsing(true);
    try {
      const sources = await readWorkbooks(accepted);
      const newParsed = sources.map(toParsed);
      setParsed((prev) => [...prev, ...newParsed]);
      setMapping((prev) => {
        const next = { ...prev };
        for (const p of newParsed) {
          // 자동 매핑: suggestedName == 설계 테이블명(대소문자 무시).
          const hit = designNames.find((n) => n.toLowerCase() === p.suggestedName.toLowerCase());
          next[p.id] = hit ?? '';
        }
        return next;
      });
    } catch (e) {
      toast.error(`파싱 실패: ${(e as Error).message}`);
    } finally {
      setParsing(false);
    }
  };

  const mappedCount = parsed.filter((p) => mapping[p.id]).length;

  const onBuild = async () => {
    const datasets: Record<string, Record<string, unknown>[]> = {};
    for (const p of parsed) {
      const target = mapping[p.id];
      if (!target) continue;
      const dt = tables.find((t) => t.name === target);
      if (!dt) continue;
      // 위치 정렬 — 설계 칼럼 i ← 파싱 행 i (칼럼명 변경에도 견고).
      datasets[target] = p.rows.map((r) => {
        const o: Record<string, unknown> = {};
        dt.columns.forEach((c, i) => {
          o[c.name] = r[i] ?? null;
        });
        return o;
      });
    }
    if (Object.keys(datasets).length === 0) {
      toast.error('매핑된 테이블이 없습니다');
      return;
    }
    setBuilding(true);
    try {
      const rep = await buildDb(designName, { name: designName, tables }, datasets);
      setReport(rep);
      setSql(defaultJoinSql(tables));
      setQueryRes(null);
      const bad = rep.integrity.filter((v) => v.orphans > 0).length;
      toast.success(`빌드 완료 · ${rep.tables.length}개 테이블${bad ? ` · 무결성 경고 ${bad}건` : ''}`);
    } catch (e) {
      toast.error(`빌드 실패: ${(e as Error).message}`);
    } finally {
      setBuilding(false);
    }
  };

  const onRunQuery = async () => {
    if (!sql.trim()) return;
    setQuerying(true);
    try {
      setQueryRes(await queryDb(designName, sql));
    } catch (e) {
      toast.error(`쿼리 오류: ${(e as Error).message}`);
    } finally {
      setQuerying(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (!v) reset();
        onOpenChange(v);
      }}
    >
      <DialogContent className="flex max-h-[88vh] max-w-4xl flex-col">
        <DialogHeader>
          <DialogTitle>DB 빌드 & 검증 (SQLite)</DialogTitle>
          <DialogDescription>
            설계(ERD)대로 실제 SQLite 를 조립하고, 엑셀 데이터를 적재해 <b>참조 무결성</b>을 검사합니다.
            데이터 없는 차원(마스터)은 팩트에서 <span className="font-mono">DISTINCT</span> 로 채웁니다.
            엑셀을 다시 올려주세요(헤더·언피벗은 가져오기와 동일하게 자동 처리).
          </DialogDescription>
        </DialogHeader>

        {!report ? (
          <>
            {/* 드롭존 */}
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                void handleFiles(e.dataTransfer.files);
              }}
              className={cn(
                'flex w-full flex-col items-center justify-center gap-1 rounded-input border border-dashed py-5 text-2xs transition-colors',
                dragOver
                  ? 'border-accent-action bg-accent-action/5 text-accent-action'
                  : 'border-border text-muted-foreground hover:bg-muted/40',
              )}
            >
              <span className="font-medium">
                {parsing ? '읽는 중…' : '엑셀/CSV 를 여기에 드롭하거나 클릭'}
              </span>
              <span className="opacity-70">설계 테이블에 시트를 매핑해 적재합니다</span>
              <input
                ref={inputRef}
                type="file"
                accept={ACCEPT}
                multiple
                className="hidden"
                onChange={(e) => {
                  void handleFiles(e.target.files);
                  e.target.value = '';
                }}
              />
            </button>

            {/* 매핑 목록 */}
            {parsed.length > 0 && (
              <div className="flex min-h-0 flex-1 flex-col gap-1.5 overflow-y-auto pr-1">
                {parsed.map((p) => (
                  <div
                    key={p.id}
                    className={cn(
                      'flex items-center gap-2 rounded-input border p-2 text-2xs',
                      mapping[p.id] ? 'border-border bg-card' : 'border-border/60 bg-muted/30',
                    )}
                  >
                    <span className="truncate font-mono text-muted-foreground" title={`${p.fileName} · ${p.sheetName}`}>
                      {p.suggestedName}
                    </span>
                    {p.unpivoted && (
                      <span className="shrink-0 rounded-sm border border-accent-action/40 px-1 text-accent-action" title="가로 월 칼럼을 세로로 접어 적재">
                        언피벗
                      </span>
                    )}
                    <span className="shrink-0 text-muted-foreground">{p.rows.length}행 →</span>
                    <select
                      value={mapping[p.id] ?? ''}
                      onChange={(e) => setMapping((m) => ({ ...m, [p.id]: e.target.value }))}
                      className={cn(
                        'ml-auto h-6 max-w-[220px] rounded-sm border bg-background px-1 text-2xs',
                        mapping[p.id] ? 'border-accent-action text-accent-action' : 'border-input text-muted-foreground',
                      )}
                    >
                      <option value="">(건너뜀)</option>
                      {designNames.map((n) => (
                        <option key={n} value={n}>
                          {n}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            )}

            <div className="flex items-center gap-2 border-t border-border pt-3">
              <span className="text-2xs text-muted-foreground">
                매핑 안 된 마스터(거래처·품목 등)는 팩트에서 자동 채움. 설계 테이블 {designNames.length}개.
              </span>
              <div className="ml-auto flex gap-2">
                <Button variant="ghost" size="sm" className="h-8 text-2xs" onClick={() => onOpenChange(false)}>
                  취소
                </Button>
                <Button
                  size="sm"
                  className="h-8 text-2xs"
                  disabled={mappedCount === 0 || building || parsing}
                  onClick={onBuild}
                >
                  {building ? '빌드 중…' : `빌드 & 검증 (${mappedCount}개 매핑)`}
                </Button>
              </div>
            </div>
          </>
        ) : (
          <BuildResult
            report={report}
            sql={sql}
            setSql={setSql}
            onRunQuery={onRunQuery}
            querying={querying}
            queryRes={queryRes}
            onRebuild={() => {
              setReport(null);
              setQueryRes(null);
            }}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}

function BuildResult({
  report,
  sql,
  setSql,
  onRunQuery,
  querying,
  queryRes,
  onRebuild,
}: {
  report: BuildReport;
  sql: string;
  setSql: (v: string) => void;
  onRunQuery: () => void;
  querying: boolean;
  queryRes: QueryResult | null;
  onRebuild: () => void;
}) {
  const SRC_LABEL: Record<string, string> = { data: '엑셀', distinct: 'DISTINCT 자동', empty: '빈' };
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto pr-1">
      {/* 적재 */}
      <section>
        <h3 className="mb-1 text-2xs font-semibold uppercase tracking-wide text-muted-foreground">
          적재 ({report.tables.length}개 테이블)
        </h3>
        <div className="flex flex-col gap-0.5">
          {report.tables.map((t) => (
            <div key={t.name} className="flex items-center gap-2 text-2xs">
              <span className="w-44 truncate font-medium">{t.name}</span>
              <span className="w-20 text-muted-foreground">{SRC_LABEL[t.source] ?? t.source}</span>
              <span className="font-mono">{t.loaded.toLocaleString()}행</span>
              {t.dropped_duplicates > 0 && (
                <span className="font-mono text-amber-500">중복 {t.dropped_duplicates} 버림</span>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* 무결성 */}
      <section>
        <h3 className="mb-1 text-2xs font-semibold uppercase tracking-wide text-muted-foreground">
          참조 무결성 (FK orphan)
        </h3>
        <div className="flex flex-col gap-0.5">
          {report.integrity.length === 0 && (
            <span className="text-2xs text-muted-foreground">FK 가 없습니다 — 캔버스에서 칼럼을 연결하세요.</span>
          )}
          {report.integrity.map((v, i) => (
            <div key={i} className="flex items-center gap-2 text-2xs">
              <span className="font-mono">
                {v.child}.{v.column} → {v.parent}.{v.parent_column}
              </span>
              {v.orphans === 0 ? (
                <span className="text-emerald-500">OK</span>
              ) : (
                <span className="text-rose-500">
                  ⚠ {v.orphans}건 고아{v.samples.length > 0 && ` · 예: ${v.samples.slice(0, 3).join(', ')}`}
                </span>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* 조립 미리보기 */}
      <section className="flex min-h-0 flex-col">
        <h3 className="mb-1 text-2xs font-semibold uppercase tracking-wide text-muted-foreground">
          조립 미리보기 (JOIN)
        </h3>
        <textarea
          value={sql}
          onChange={(e) => setSql(e.target.value)}
          className="h-24 w-full resize-none rounded-input border border-input bg-background p-2 font-mono text-2xs focus:outline-none"
          spellCheck={false}
        />
        <div className="mt-1 flex items-center gap-2">
          <span className="text-2xs text-muted-foreground">한글/공백 이름은 큰따옴표로 감쌉니다.</span>
          <Button
            size="sm"
            variant="outline"
            className="ml-auto h-7 text-2xs"
            onClick={onRunQuery}
            disabled={querying}
          >
            {querying ? '실행 중…' : '실행'}
          </Button>
        </div>

        {queryRes && (
          <div className="mt-2 overflow-auto rounded-input border border-border">
            <table className="w-full border-collapse text-2xs">
              <thead>
                <tr className="bg-muted/50">
                  {queryRes.columns.map((c) => (
                    <th key={c} className="border-b border-border px-2 py-1 text-left font-semibold">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {queryRes.rows.map((row, ri) => (
                  <tr key={ri} className="odd:bg-muted/20">
                    {row.map((cell, ci) => (
                      <td key={ci} className="whitespace-nowrap border-b border-border/50 px-2 py-1 font-mono">
                        {cell === null ? '∅' : String(cell)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            {queryRes.truncated && (
              <div className="px-2 py-1 text-2xs text-muted-foreground">… 상한까지만 표시</div>
            )}
          </div>
        )}
      </section>

      <div className="flex items-center gap-2 border-t border-border pt-2">
        <span className="text-2xs text-muted-foreground">
          빌드된 DB: <span className="font-mono">var/erd/….db</span> (읽기 전용 쿼리)
        </span>
        <Button variant="ghost" size="sm" className="ml-auto h-7 text-2xs" onClick={onRebuild}>
          ← 다시 빌드
        </Button>
      </div>
    </div>
  );
}
