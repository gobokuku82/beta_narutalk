/**
 * TableNode — ERD 캔버스의 테이블 카드 (React Flow 커스텀 노드).
 *
 * 헤더(테이블명) + 컬럼 목록(PK 🔑 / FK 🔗 / NN / UQ 배지).
 * 좌(target)·우(source) Handle 로 테이블 간 FK 연결(드래그).
 */
import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { cn } from '@/lib/cn';
import type { ErdTable } from './store';

export interface TableNodeData {
  table: ErdTable;
  [key: string]: unknown;
}

function TableNodeComponent({ data, selected }: NodeProps) {
  const { table } = data as unknown as TableNodeData;
  return (
    <div
      className={cn(
        'min-w-[180px] rounded-md border bg-card text-card-foreground shadow-sm',
        selected ? 'border-primary ring-1 ring-primary/40' : 'border-border',
      )}
    >
      <Handle type="target" position={Position.Left} className="!h-2 !w-2 !bg-muted-foreground" />
      <Handle type="source" position={Position.Right} className="!h-2 !w-2 !bg-primary" />

      <div className="rounded-t-md border-b border-border bg-muted/50 px-3 py-1.5">
        <span className="text-sm font-semibold">{table.name || '(unnamed)'}</span>
      </div>

      <ul className="flex flex-col py-1">
        {table.columns.length === 0 && (
          <li className="px-3 py-1 text-2xs text-muted-foreground">(컬럼 없음)</li>
        )}
        {table.columns.map((c) => (
          <li
            key={c.id}
            className="flex items-center justify-between gap-2 px-3 py-0.5 text-2xs"
          >
            <span className="flex items-center gap-1 truncate">
              <span className="w-3 shrink-0 text-center">{c.pk ? '🔑' : c.fk ? '🔗' : ''}</span>
              <span className={cn('truncate', c.pk && 'font-semibold')}>{c.name}</span>
            </span>
            <span className="flex shrink-0 items-center gap-1 font-mono text-muted-foreground">
              <span>{c.type}</span>
              {!c.nullable && <span className="text-amber-600">NN</span>}
              {c.unique && !c.pk && <span className="text-sky-600">UQ</span>}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export const TableNode = memo(TableNodeComponent);

export const erdNodeTypes = { table: TableNode };
