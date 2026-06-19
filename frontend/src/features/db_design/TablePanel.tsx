/**
 * TablePanel — 선택된 테이블의 편집 패널 (우측 도킹).
 *
 * 테이블명/주석 + 컬럼 추가·편집(이름/타입/PK/NN/UQ/기본값)·삭제 + FK 표시·해제 + 테이블 삭제.
 * FK *생성*은 캔버스에서 테이블→테이블 드래그(connect). 여기선 표시/해제.
 */
import { useDbDesign, COLUMN_TYPES, type ErdColumn } from './store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/cn';

export function TablePanel() {
  const selectedId = useDbDesign((s) => s.selectedTableId);
  const table = useDbDesign((s) => s.tables.find((t) => t.id === s.selectedTableId) ?? null);
  const renameTable = useDbDesign((s) => s.renameTable);
  const setTableComment = useDbDesign((s) => s.setTableComment);
  const removeTable = useDbDesign((s) => s.removeTable);
  const addColumn = useDbDesign((s) => s.addColumn);
  const updateColumn = useDbDesign((s) => s.updateColumn);
  const removeColumn = useDbDesign((s) => s.removeColumn);

  if (!selectedId || !table) {
    return (
      <div className="flex h-full items-center justify-center p-4 text-center text-2xs text-muted-foreground">
        테이블을 선택하거나
        <br />
        상단 [+ 테이블]로 추가하세요.
      </div>
    );
  }

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
            onChange={(patch) => updateColumn(table.id, c.id, patch)}
            onRemove={() => removeColumn(table.id, c.id)}
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
  onChange,
  onRemove,
}: {
  column: ErdColumn;
  onChange: (patch: Partial<ErdColumn>) => void;
  onRemove: () => void;
}) {
  return (
    <li className="flex flex-col gap-1 rounded-md border border-border bg-card p-2">
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
        {column.fk && (
          <span className="flex items-center gap-1 rounded-sm bg-muted px-1 font-mono text-muted-foreground">
            🔗 {column.fk.table}.{column.fk.column}
            <button
              type="button"
              onClick={() => onChange({ fk: null })}
              className="hover:text-destructive"
              title="FK 해제"
            >
              ✕
            </button>
          </span>
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
        'rounded-sm border px-1.5 py-0.5 font-mono',
        active ? 'border-primary bg-primary/10 text-primary' : 'border-border text-muted-foreground',
      )}
    >
      {label}
    </button>
  );
}
