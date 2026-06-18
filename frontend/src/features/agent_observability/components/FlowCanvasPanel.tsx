/**
 * FlowCanvasPanel — 워크플로우 DAG 시각화 (R3 흐름 + R4 워크플로우 생성).
 *
 * 기존 WorkflowCanvas(React Flow) 를 read-only(editable=false)로 재사용.
 *  격리 원칙: 공용 컴포넌트는 *재사용만*, 수정 X (계획서 §7.5).
 * Phase 2+ 에서 todo 실시간 상태 색(running/완료/실패)을 노드에 주입 예정(§9).
 */
import { WorkflowCanvas } from '@/features/workflow/canvas/WorkflowCanvas';
import type { Plan } from '@/api/schemas';

interface FlowCanvasPanelProps {
  plan: Plan | null;
}

export function FlowCanvasPanel({ plan }: FlowCanvasPanelProps) {
  return (
    <div className="h-[420px] overflow-hidden rounded-lg border border-border bg-card">
      {plan && plan.todos.length > 0 ? (
        <WorkflowCanvas plan={plan} direction="LR" editable={false} />
      ) : (
        <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
          활성 워크플로우가 없습니다. 채팅에서 질문을 보내면 계획(DAG)이 여기 그려집니다.
        </div>
      )}
    </div>
  );
}
