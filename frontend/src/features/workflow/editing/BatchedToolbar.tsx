/**
 * BatchedToolbar — 변경 적용 모드 토글 + pendingOps 카운트 + 일괄 적용/취소 (W2', ADR-013 §6).
 *
 * 위치: WorkflowPage 가 EditToolbar 옆에 배치.
 *
 * 동작:
 *   - 모드 토글 — 즉시 적용 ↔ 묶어서 적용. batched 진입 시 pendingOps 누적 시작.
 *   - 모드 immediate 일 때: 큐가 차있어도 적용/취소 노출 (사용자가 batched 에서 만든 큐).
 *   - 큐 0건 + immediate: 토글만 표시.
 *   - editable=false 면 숨김.
 *
 * spec: 62 §5.1 / ADR-013 §6 / Stage 6
 */
import { Check, Layers, Undo2, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useEditingStore } from '../store/editingStore';
import { useWorkflowEditing } from './useWorkflowEditing';

interface BatchedToolbarProps {
  editable: boolean;
}

export function BatchedToolbar({ editable }: BatchedToolbarProps) {
  const applyMode = useEditingStore((s) => s.applyMode);
  const pendingOps = useEditingStore((s) => s.pendingOps);
  const setApplyMode = useEditingStore((s) => s.setApplyMode);
  const clearPendingOps = useEditingStore((s) => s.clearPendingOps);
  const { applyAllPendingOps } = useWorkflowEditing();

  if (!editable) return null;

  const isBatched = applyMode === 'batched';
  const pendingCount = pendingOps.length;
  const hasPending = pendingCount > 0;

  const handleToggle = () => {
    setApplyMode(isBatched ? 'immediate' : 'batched');
  };

  const handleApply = () => {
    applyAllPendingOps();
  };

  const handleCancel = () => {
    clearPendingOps();
  };

  return (
    <div className="absolute top-3 right-[16.5rem] z-10 flex items-center gap-2 rounded-panel border border-border bg-card/95 backdrop-blur px-2 py-2 shadow-panel">
      <Button
        type="button"
        variant={isBatched ? 'default' : 'outline'}
        size="sm"
        onClick={handleToggle}
        title={isBatched ? '묶어서 적용 모드 — 클릭하면 즉시 적용으로' : '즉시 적용 모드 — 클릭하면 묶어서 적용으로'}
      >
        {isBatched ? <Layers className="h-4 w-4" /> : <Zap className="h-4 w-4" />}
        {isBatched ? '묶음' : '즉시'}
      </Button>

      {hasPending && (
        <>
          <span
            className="text-xs text-muted-foreground tabular-nums"
            title={`${pendingCount}건의 변경이 큐에 대기`}
          >
            {pendingCount}건 대기
          </span>
          <Button
            type="button"
            variant="default"
            size="sm"
            onClick={handleApply}
            title={`${pendingCount}건 일괄 적용`}
          >
            <Check className="h-4 w-4" />
            적용
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleCancel}
            title="대기 중인 변경 모두 취소"
          >
            <Undo2 className="h-4 w-4" />
            취소
          </Button>
        </>
      )}
    </div>
  );
}
