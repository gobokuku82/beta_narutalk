/**
 * ChatTodoCard — 채팅창 안에 표시되는 "작업 단계" 카드.
 *
 * Phase 1 (P1-5, D1):
 *  - 정적 Plan + 동적 todo 이벤트 결합 표시 (useExecution.selectTodoViews).
 *  - 상태 아이콘: pending / running / completed / failed / skipped.
 *  - 진행률 (completed/total).
 *  - "워크플로우로 보기" → /workflow 라우팅.
 *
 * spec: 21 v1.4 §2.2 / 30 v1.1 (Plan)
 */
import { Check, Loader2, AlertCircle, Circle, MinusCircle, GitBranch } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/cn';
import type { TodoView } from '@/features/execution/store';

interface ChatTodoCardProps {
  todos: TodoView[];
  progress: { completed: number; total: number } | null;
  isPaused: boolean;
  isCompleted: boolean;
  onOpenWorkflow: () => void;
}

function StatusIcon({ status }: { status: TodoView['runtime_status'] }) {
  switch (status) {
    case 'completed':
      return <Check className="h-4 w-4 text-success" aria-label="완료" />;
    case 'running':
      return <Loader2 className="h-4 w-4 animate-spin text-accent-action" aria-label="진행 중" />;
    case 'failed':
      return <AlertCircle className="h-4 w-4 text-destructive" aria-label="실패" />;
    case 'skipped':
      return <MinusCircle className="h-4 w-4 text-muted-foreground" aria-label="건너뜀" />;
    case 'pending':
    default:
      return <Circle className="h-4 w-4 text-muted-foreground/60" aria-label="대기" />;
  }
}

export function ChatTodoCard({
  todos,
  progress,
  isPaused,
  isCompleted,
  onOpenWorkflow,
}: ChatTodoCardProps) {
  const completedCount =
    progress?.completed ?? todos.filter((t) => t.runtime_status === 'completed').length;
  const totalCount = progress?.total ?? todos.length;

  return (
    <div className="rounded-card border border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="px-3 py-2 border-b border-border flex items-center justify-between bg-muted/30">
        <div className="flex items-center gap-2 text-sm font-medium">
          <span aria-hidden>⌃≡</span>
          <span>작업 단계</span>
          {isPaused && (
            <span className="rounded-full bg-warning text-warning-foreground px-2 py-1 text-xs">
              일시정지
            </span>
          )}
          {isCompleted && (
            <span className="rounded-full bg-success text-success-foreground px-2 py-1 text-xs">
              완료
            </span>
          )}
        </div>
        <span className="text-xs text-muted-foreground tabular-nums">
          {completedCount}/{totalCount}
        </span>
      </div>

      {/* Todo list */}
      <ol className="px-3 py-2 space-y-2 max-h-[40vh] overflow-y-auto">
        {todos.map((t) => (
          <li
            key={t.id}
            className={cn(
              'flex items-start gap-2 text-sm',
              t.runtime_status === 'completed' && 'text-muted-foreground',
              t.runtime_status === 'failed' && 'text-destructive',
            )}
          >
            <span className="mt-1 shrink-0">
              <StatusIcon status={t.runtime_status} />
            </span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-medium">{t.task_type}</span>
                {t.tool && (
                  <code className="rounded-sm bg-muted px-1 text-xs text-muted-foreground">
                    {t.tool}
                  </code>
                )}
                {t.is_mock && (
                  <span className="text-2xs uppercase tracking-wider text-muted-foreground/70">
                    mock
                  </span>
                )}
                {typeof t.duration_ms === 'number' && (
                  <span className="text-xs text-muted-foreground tabular-nums">
                    {(t.duration_ms / 1000).toFixed(1)}s
                  </span>
                )}
              </div>
              {t.rationale && (
                <p className="text-xs text-muted-foreground truncate">{t.rationale}</p>
              )}
              {t.error && (
                <p className="text-xs text-destructive/80 truncate">{t.error}</p>
              )}
            </div>
          </li>
        ))}
      </ol>

      {/* Footer */}
      <div className="px-3 py-2 border-t border-border bg-muted/20">
        <Button
          variant="outline"
          size="sm"
          onClick={onOpenWorkflow}
          className="w-full justify-center"
        >
          <GitBranch className="h-4 w-4" />
          워크플로우로 보기
        </Button>
      </div>
    </div>
  );
}
