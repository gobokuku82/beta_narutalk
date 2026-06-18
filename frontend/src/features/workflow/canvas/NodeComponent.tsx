/**
 * NodeComponent — React Flow 커스텀 노드 (task).
 *
 * spec: 62 §4.1 노드 시각적 사양 / §5 cascade tint (W2) / ADR-013 §6 batched 시각화 (W2').
 */
import { Link2Off, Pencil } from 'lucide-react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { PlannedTodo } from '@/api/schemas';
import { cn } from '@/lib/cn';

export interface TaskNodeData extends Record<string, unknown> {
  todo: PlannedTodo;
  /** cascade 결과 — 직전 편집으로 invalidated 된 downstream 노드 표시 (🔴 + ⛓). */
  isInvalidated?: boolean;
  /** batched 모드에서 삭제 대기 중 — 회색 + 점선 (W2' Stage 6). */
  isPendingDelete?: boolean;
  /** batched 모드에서 수정 대기 중 — ✏ 배지 (W2' Stage 6). */
  isPendingModify?: boolean;
}

const NODE_TYPE_STYLE: Record<string, string> = {
  task: 'bg-node-task border-border',
  branch: 'bg-node-branch/20 border-node-branch',
  start: 'bg-node-start/20 border-node-start',
  end: 'bg-node-end/20 border-node-end',
  join: 'bg-muted border-border',
};

export function NodeComponent({ data, selected }: NodeProps) {
  const { todo, isInvalidated, isPendingDelete, isPendingModify } = data as TaskNodeData;
  const style = NODE_TYPE_STYLE[todo.node_type ?? 'task'] ?? NODE_TYPE_STYLE.task;

  return (
    <div
      className={cn(
        'rounded-lg border-2 px-3 py-2 shadow-sm w-[180px] relative',
        style,
        selected && 'ring-2 ring-primary',
        isInvalidated && 'ring-2 ring-destructive/60 bg-destructive/5',
        // batched 삭제 대기 — 회색 + 점선 + opacity (적용 전 미리보기).
        isPendingDelete && 'border-dashed opacity-50',
      )}
    >
      {isInvalidated && (
        <span
          className="absolute -top-2 -right-2 flex items-center gap-1 rounded-full bg-destructive text-destructive-foreground px-2 py-1 text-2xs font-medium shadow"
          title="이전 편집의 영향 — 재실행 필요"
        >
          <Link2Off className="h-3 w-3" />
          재실행 필요
        </span>
      )}
      {isPendingModify && !isPendingDelete && (
        <span
          className="absolute -top-2 -left-2 flex items-center gap-1 rounded-full bg-primary text-primary-foreground px-2 py-1 text-2xs font-medium shadow"
          title="batched 모드 — 수정 대기 중 (변경 적용 클릭 시 송신)"
        >
          <Pencil className="h-3 w-3" />
          수정 대기
        </span>
      )}
      {isPendingDelete && (
        <span
          className="absolute -top-2 -left-2 rounded-full bg-muted-foreground text-background px-2 py-1 text-2xs font-medium shadow"
          title="batched 모드 — 삭제 대기 중"
        >
          삭제 대기
        </span>
      )}

      <Handle type="target" position={Position.Top} className="!bg-edge" />

      {/* 헤더 — task_type */}
      <div className="text-2xs font-mono text-muted-foreground uppercase tracking-wide">
        {todo.task_type}
      </div>

      {/* 본문 — rationale */}
      <div className="text-sm font-medium leading-tight mt-0.5 line-clamp-2">
        {todo.rationale || todo.task_type}
      </div>

      {/* 푸터 — tool */}
      {todo.tool && (
        <div className="text-2xs text-muted-foreground mt-1 truncate">
          🔧 {todo.tool}
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="!bg-edge" />
    </div>
  );
}
