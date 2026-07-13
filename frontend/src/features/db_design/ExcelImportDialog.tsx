/**
 * ExcelImportDialog — 엑셀/CSV 업로드 → ERD 테이블 가져오기 (미리보기 + 보정).
 *
 * 여러 파일을 한번에/계속 올리면 시트마다 테이블 후보 생성. "첫 줄=컬럼" 고정이 아니라
 * 헤더 행을 자동 감지하고, 카드별로 헤더 행/행 수를 보정(계층 헤더 대응)·테이블명 편집·
 * 포함 토글 가능. 확정 시 store.importTables 로 기존 설계에 누적 추가(옵션: FK 자동추론).
 * 파싱은 parseWorkbook(SheetJS) — 백엔드 불요, 브라우저에서 처리.
 */
import { useCallback, useMemo, useRef, useState } from 'react';
import { toast } from 'sonner';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/cn';
import { readWorkbooks, deriveTable, type SheetSource } from './parseWorkbook';
import { detectPeriodRuns, unpivotDerived } from './unpivot';
import { useDbDesign, type ImportTableInput } from './store';

const ACCEPT = '.xlsx,.xlsm,.xls,.csv';
const FILE_RE = /\.(xlsx|xlsm|xls|csv)$/i;

interface SourceConfig {
  include: boolean;
  name: string;
  headerStart: number;
  headerCount: number;
  unpivot: boolean; // 연속 기간 칼럼을 [기간, 값]으로 접기
}

export function ExcelImportDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  const importTables = useDbDesign((s) => s.importTables);
  const [sources, setSources] = useState<SheetSource[]>([]);
  const [config, setConfig] = useState<Record<string, SourceConfig>>({});
  const [autoFk, setAutoFk] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const reset = () => {
    setSources([]);
    setConfig({});
    setAutoFk(false);
    setDragOver(false);
  };

  const handleFiles = useCallback(async (fileList: FileList | File[] | null) => {
    if (!fileList) return;
    const accepted = Array.from(fileList).filter((f) => FILE_RE.test(f.name));
    if (accepted.length === 0) {
      toast.error('엑셀/CSV 파일이 아닙니다 (.xlsx, .xls, .csv)');
      return;
    }
    setParsing(true);
    try {
      const parsed = await readWorkbooks(accepted);
      if (parsed.length === 0) {
        toast.error('읽을 수 있는 시트가 없습니다');
        return;
      }
      setSources((prev) => [...prev, ...parsed]);
      setConfig((prev) => {
        const next = { ...prev };
        for (const src of parsed) {
          const base = deriveTable(src, src.detected.start, src.detected.count);
          const strongRun = detectPeriodRuns(base.columns).find((r) => r.strong);
          next[src.id] = {
            include: true,
            name: src.suggestedName,
            headerStart: src.detected.start,
            headerCount: src.detected.count,
            unpivot: Boolean(strongRun), // 강한 기간 런이면 기본 ON
          };
        }
        return next;
      });
    } catch (e) {
      toast.error(`파싱 실패: ${(e as Error).message}`);
    } finally {
      setParsing(false);
    }
  }, []);

  const patch = (id: string, p: Partial<SourceConfig>) =>
    setConfig((c) => {
      const cur = c[id];
      if (!cur) return c;
      return { ...c, [id]: { ...cur, ...p } };
    });

  const removeSource = (id: string) => {
    setSources((s) => s.filter((x) => x.id !== id));
    setConfig((c) => {
      const next = { ...c };
      delete next[id];
      return next;
    });
  };

  const derived = useMemo(
    () =>
      sources.map((source) => {
        const cfg = config[source.id];
        if (!cfg) return { source, cfg: undefined, table: null, run: null };
        const base = deriveTable(source, cfg.headerStart, cfg.headerCount);
        const runs = detectPeriodRuns(base.columns);
        const run = runs.find((r) => r.strong) ?? runs[0] ?? null;
        const table = cfg.unpivot && run ? unpivotDerived(base, run) : base;
        return { source, cfg, table, run };
      }),
    [sources, config],
  );

  const includedCount = derived.filter((d) => d.cfg?.include).length;

  const onImport = () => {
    const inputs: ImportTableInput[] = derived
      .filter((d) => d.cfg?.include && d.table)
      .map((d) => ({
        name: d.cfg!.name,
        comment: `${d.source.fileName} · ${d.source.sheetName}`,
        columns: d.table!.columns.map((c) => ({ name: c.name, type: c.type })),
      }));
    if (inputs.length === 0) {
      toast.error('가져올 테이블을 선택하세요');
      return;
    }
    const added = importTables(inputs, { autoFk });
    toast.success(`${added}개 테이블 추가됨${autoFk ? ' · FK 자동추론 적용' : ''}`);
    reset();
    onOpenChange(false);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (!v) reset();
        onOpenChange(v);
      }}
    >
      <DialogContent className="flex max-h-[85vh] max-w-3xl flex-col">
        <DialogHeader>
          <DialogTitle>엑셀 가져오기</DialogTitle>
          <DialogDescription>
            시트마다 테이블 1개. 헤더 행은 자동 감지되며, 카드에서 보정할 수 있습니다. 여러 파일을
            한번에/계속 올릴 수 있습니다.
          </DialogDescription>
        </DialogHeader>

        {/* 드롭존 (항상 노출 — 계속 추가 가능) */}
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
            'flex w-full flex-col items-center justify-center gap-1 rounded-input border border-dashed py-6 text-2xs transition-colors',
            dragOver
              ? 'border-accent-action bg-accent-action/5 text-accent-action'
              : 'border-border text-muted-foreground hover:bg-muted/40',
          )}
        >
          <span className="font-medium">
            {parsing ? '읽는 중…' : '엑셀/CSV 파일을 여기에 드롭하거나 클릭해서 선택'}
          </span>
          <span className="opacity-70">.xlsx · .xls · .csv · 여러 개 가능</span>
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

        {/* 후보 목록 */}
        {derived.length > 0 && (
          <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto pr-1">
            {derived.map(({ source, cfg, table, run }) => {
              if (!cfg) return null;
              const maxStart = Math.max(0, source.rows.length - 1);
              return (
                <div
                  key={source.id}
                  className={cn(
                    'rounded-input border p-2.5',
                    cfg.include ? 'border-border bg-card' : 'border-border/60 bg-muted/30 opacity-70',
                  )}
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={cfg.include}
                      onChange={(e) => patch(source.id, { include: e.target.checked })}
                      className="h-3.5 w-3.5 accent-accent-action"
                    />
                    <Input
                      value={cfg.name}
                      onChange={(e) => patch(source.id, { name: e.target.value })}
                      className="h-7 max-w-[220px] text-2xs font-medium"
                    />
                    <span className="truncate font-mono text-2xs text-muted-foreground">
                      {source.fileName} · {source.sheetName}
                    </span>
                    <button
                      type="button"
                      onClick={() => removeSource(source.id)}
                      className="ml-auto px-1 text-2xs text-muted-foreground hover:text-destructive"
                      title="목록에서 제거"
                    >
                      ✕
                    </button>
                  </div>

                  <div className="mt-2 flex flex-wrap items-center gap-3 text-2xs text-muted-foreground">
                    <Stepper
                      label="헤더 행"
                      value={cfg.headerStart + 1}
                      onDec={() =>
                        patch(source.id, { headerStart: Math.max(0, cfg.headerStart - 1) })
                      }
                      onInc={() =>
                        patch(source.id, { headerStart: Math.min(maxStart, cfg.headerStart + 1) })
                      }
                    />
                    <Stepper
                      label="헤더 행 수"
                      value={cfg.headerCount}
                      onDec={() =>
                        patch(source.id, { headerCount: Math.max(1, cfg.headerCount - 1) })
                      }
                      onInc={() =>
                        patch(source.id, { headerCount: Math.min(3, cfg.headerCount + 1) })
                      }
                    />
                    <span>
                      컬럼 {table?.columns.length ?? 0} · 데이터 {table?.rowCount ?? 0}행
                    </span>
                    {run && (
                      <label className="flex items-center gap-1 text-accent-action" title="가로형 월별 칼럼을 세로형 [기간, 값]으로 — DB에 맞는 형태">
                        <input
                          type="checkbox"
                          checked={cfg.unpivot}
                          onChange={(e) => patch(source.id, { unpivot: e.target.checked })}
                          className="h-3.5 w-3.5 accent-accent-action"
                        />
                        기간 칼럼 {run.length}개 → [{run.periodName}, {run.valueName}]로 접기
                      </label>
                    )}
                  </div>

                  {table && (
                    <div className="mt-2 flex max-h-24 flex-wrap gap-1 overflow-y-auto">
                      {table.columns.map((c, i) => (
                        <span
                          key={`${c.name}-${i}`}
                          className="inline-flex items-center gap-1 rounded-sm border border-border bg-background px-1.5 py-0.5 text-2xs"
                          title={`${c.samples} 샘플`}
                        >
                          <span className="font-medium">{c.name}</span>
                          <span className="font-mono text-muted-foreground">{c.type}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* 푸터 */}
        <div className="flex items-center gap-3 border-t border-border pt-3">
          <label className="flex items-center gap-1.5 text-2xs text-muted-foreground">
            <input
              type="checkbox"
              checked={autoFk}
              onChange={(e) => setAutoFk(e.target.checked)}
              className="h-3.5 w-3.5 accent-accent-action"
            />
            FK 자동추론 (<span className="font-mono">xxx_id</span> 또는 컬럼명=다른 표 PK명 → 연결)
          </label>
          <div className="ml-auto flex gap-2">
            <Button variant="ghost" size="sm" className="h-8 text-2xs" onClick={() => onOpenChange(false)}>
              취소
            </Button>
            <Button
              size="sm"
              className="h-8 text-2xs"
              disabled={includedCount === 0 || parsing}
              onClick={onImport}
            >
              가져오기{includedCount > 0 ? ` (${includedCount}개 테이블)` : ''}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function Stepper({
  label,
  value,
  onDec,
  onInc,
}: {
  label: string;
  value: number;
  onDec: () => void;
  onInc: () => void;
}) {
  return (
    <span className="inline-flex items-center gap-1">
      <span>{label}</span>
      <span className="inline-flex items-center overflow-hidden rounded-sm border border-border">
        <button type="button" onClick={onDec} className="px-1.5 hover:bg-muted" tabIndex={-1}>
          −
        </button>
        <span className="min-w-[1.5rem] bg-background px-1 text-center font-mono text-foreground">
          {value}
        </span>
        <button type="button" onClick={onInc} className="px-1.5 hover:bg-muted" tabIndex={-1}>
          +
        </button>
      </span>
    </span>
  );
}
