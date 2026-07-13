/**
 * TablePanel — 선택된 테이블의 편집 패널 (우측 도킹).
 *
 * 테이블명/주석 + 컬럼 추가·편집(이름/타입/PK/NN/UQ/기본값)·삭제 + 테이블 삭제.
 * FK 는 두 경로: 캔버스 드래그(새 FK 칼럼 생성) / 여기 칼럼별 "FK 연결" 드롭다운
 * (기존 칼럼에 직접 지정 — 새 칼럼 안 만들고 방향/이름 무관하게 다른 테이블 PK 참조).
 */
import { useDbDesign, COLUMN_TYPES, type ErdColumn } from './store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/cn';

type FkTarget = { table: string; column: string };

export function TablePanel() {
  const selectedId = useDbDesign((s) => s.selectedTableId);
  const table = useDbDesign((s) => s.tables.find((t) => t.id === s.selectedTableId) ?? null);
  const renameTable = useDbDesign((s) => s.renameTable);
  const setTableComment = useDbDesign((s) => s.setTableComment);
  const removeTable = useDbDesign((s) => s.removeTable);
  const addColumn = useDbDesign((s) => s.addColumn);
  const updateColumn = useDbDesign((s) => s.updateColumn);
  const removeColumn = useDbDesign((s) => s.removeColumn);
  const extractDimension = useDbDesign((s) => s.extractDimension);
  const allTables = useDbDesign((s) => s.tables);

  if (!selectedId || !table) {
    return (
      <div className="flex h-full items-center justify-center p-4 text-center text-2xs text-muted-foreground">
        테이블을 선택하거나
        <br />
        상단 [+ 테이블]로 추가하세요.
      </div>
    );
  }

  // 다른 테이블들의 PK(없으면 첫 칼럼)를 FK 연결 후보로.
  const fkTargets: FkTarget[] = allTables
    .filter((t) => t.id !== table.id)
    .flatMap((t) => {
      const keys = t.columns.filter((c) => c.pk);
      const cols = keys.length > 0 ? keys : t.columns.slice(0, 1);
      return cols.map((c) => ({ table: t.name, column: c.name }));
    });

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto p-3">
      <div className="flex flex-col gap-1">
        <label className="text-2xs font-medium uppercase tracking-wide text-muted-foreground">
          테이블명
        </label>
        <Input
          value={table.name}
          onChange={(e) => renameTable(table.id, e.target.value)}
          className="h-8"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-2xs font-medium uppercase tracking-wide text-muted-foreground">
          주석 (선택)
        </label>
        <Input
          value={table.comment ?? ''}
          onChange={(e) => setTableComment(table.id, e.target.value)}
          className="h-8"
          placeholder="테이블 설명"
        />
      </div>

      <div className="flex items-center justify-between pt-1">
        <span className="text-2xs font-semibold uppercase tracking-wide text-muted-foreground">
          컬럼 ({table.columns.length})
        </span>
        <Button size="sm" variant="outline" className="h-6 px-2 text-2xs" onClick={() => addColumn(table.id)}>
          + 컬럼
        </Button>
      </div>

      <ul className="flex flex-col gap-2">
        {table.columns.map((c) => (
          <ColumnRow
            key={c.id}
            column={c}
            fkTargets={fkTargets}
            onChange={(patch) => updateColumn(table.id, c.id, patch)}
            onRemove={() => removeColumn(table.id, c.id)}
            onExtract={() => extractDimension(table.id, c.id)}
          />
        ))}
      </ul>

      <div className="mt-auto pt-3">
        <Button
          variant="destructive"
          size="sm"
          className="h-7 w-full text-2xs"
          onClick={() => removeTable(table.id)}
        >
          테이블 삭제
        </Button>
      </div>
    </div>
  );
}

function ColumnRow({
  column,
  fkTargets,
  onChange,
  onRemove,
  onExtract,
}: {
  column: ErdColumn;
  fkTargets: FkTarget[];
  onChange: (patch: Partial<ErdColumn>) => void;
  onRemove: () => void;
  onExtract: () => void;
}) {
  const fk = column.fk ?? null;
  const fkIndex = fk
    ? fkTargets.findIndex((t) => t.table === fk.table && t.column === fk.column)
    : -1;
  // 현재 FK 대상이 후보에 없으면(테이블명 변경 등) 'cur' 로 표시만 유지.
  const selectValue = fk ? (fkIndex >= 0 ? String(fkIndex) : 'cur') : '';

  return (
    <li className="flex flex-col gap-1 rounded-input border border-border bg-card p-2">
      <div className="flex items-center gap-1">
        <Input
          value={column.name}
          onChange={(e) => onChange({ name: e.target.value })}
          className="h-7 flex-1 text-2xs"
          placeholder="컬럼명"
        />
        <select
          value={column.type}
          onChange={(e) => onChange({ type: e.target.value })}
          className="h-7 rounded-sm border border-input bg-background px-1 text-2xs"
        >
          {COLUMN_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
          {!COLUMN_TYPES.includes(column.type as never) && (
            <option value={column.type}>{column.type}</option>
          )}
        </select>
        <button
          type="button"
          onClick={onRemove}
          className="px-1 text-2xs text-muted-foreground hover:text-destructive"
          title="컬럼 삭제"
        >
          ✕
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-2xs">
        <Flag label="PK" active={column.pk} onClick={() => onChange({ pk: !column.pk, nullable: column.pk ? column.nullable : false })} />
        <Flag label="NN" active={!column.nullable} onClick={() => onChange({ nullable: !column.nullable })} />
        <Flag label="UQ" active={column.unique} onClick={() => onChange({ unique: !column.unique })} />
        <Input
          value={column.default ?? ''}
          onChange={(e) => onChange({ default: e.target.value || null })}
          className="h-6 w-24 text-2xs"
          placeholder="default"
        />
        <select
          value={selectValue}
          onChange={(e) => {
            const v = e.target.value;
            if (v === '') return onChange({ fk: null });
            if (v === 'cur') return; // 현재 값 유지
            const t = fkTargets[Number(v)];
            if (t) onChange({ fk: { table: t.table, column: t.column } });
          }}
          className={cn(
            'h-6 max-w-[160px] rounded-sm border bg-background px-1 text-2xs',
            fk ? 'border-accent-action text-accent-action' : 'border-input text-muted-foreground',
          )}
          title="FK 연결 — 이 칼럼이 가리킬 테이블.PK"
        >
          <option value="">🔗 FK 없음</option>
          {fk && fkIndex < 0 && (
            <option value="cur">
              🔗 {fk.table}.{fk.column}
            </option>
          )}
          {fkTargets.map((t, i) => (
            <option key={`${t.table}.${t.column}.${i}`} value={String(i)}>
              🔗 {t.table}.{t.column}
            </option>
          ))}
        </select>
        {!column.pk && !column.fk && (
          <button
            type="button"
            onClick={onExtract}
            className="rounded-sm border border-border px-1.5 py-1 font-mono text-muted-foreground hover:border-accent-action hover:text-accent-action"
            title="이 칼럼을 차원(마스터) 테이블로 분리 + FK 연결"
          >
            ⇲ 차원
          </button>
        )}
      </div>
    </li>
  );
}

function Flag({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'rounded-sm border px-2 py-1 font-mono',
        active ? 'border-accent-action bg-accent-action/10 text-accent-action' : 'border-border text-muted-foreground',
      )}
    >
      {label}
    </button>
  );
}
