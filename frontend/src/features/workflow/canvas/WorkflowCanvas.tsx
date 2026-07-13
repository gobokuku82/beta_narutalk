/**
 * WorkflowCanvas — React Flow 기반 워크플로우 시각화 (W1 read-only + W2 이벤트 위임).
 *
 * 책임: *순수 시각화*. 우클릭/더블클릭/선택 이벤트는 콜백으로 위로 emit.
 *       편집 동작 자체는 `features/workflow/editing/` 이 처리.
 *
 * spec: 62 §2 / §4 / §5
 * W1: read-only 렌더. W2 (편집 활성 / 이벤트 wiring) 는 부모 (WorkflowPage) 가 결정.
 */
import { useMemo, type MouseEvent as ReactMouseEvent } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Connection,
  type Edge,
  type Node as RFNode,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import type { Plan } from '@/api/schemas';
import { planToFlow, type LayoutDirection } from '@/lib/dagre';
import { nodeTypes } from './nodeTypes';

export interface WorkflowCanvasProps {
  plan: Plan;
  direction?: LayoutDirection;
  /** 편집 활성 여부 (paused 상태에서만 true). false 면 우클릭/더블클릭/연결 콜백 firing 안 함. */
  editable?: boolean;
  /** cascade 결과 — 직전 편집으로 invalidated 된 todo id 들 (NodeComponent 가 🔴 tint). */
  invalidatedIds?: readonly string[];
  /** batched 모드 — 삭제 대기 중 todo id 들 (NodeComponent 가 회색+점선). */
  pendingDeleteIds?: readonly string[];
  /** batched 모드 — 수정 대기 중 todo id 들 (NodeComponent 가 ✏ 배지). */
  pendingModifyIds?: readonly string[];
  /** 노드 클릭 — 선택. nodeId=null 이면 배경 클릭으로 해제. */
  onNodeSelect?: (nodeId: string | null) => void;
  /** 노드 우클릭 — 컨텍스트 메뉴 트리거. editable 일 때만 fire. */
  onNodeContextMenu?: (nodeId: string, e: ReactMouseEvent) => void;
  /** 노드 더블클릭 — 속성 패널 트리거. editable 일 때만 fire. */
  onNodeDoubleClick?: (nodeId: string) => void;
  /**
   * 엣지 연결 — Handle drag 로 source → target 새 엣지 생성 (W2', ADR-013).
   * editable 일 때만 fire. 부모가 cycle 검증 + sendTodoModify 송신 책임.
   */
  onEdgeConnect?: (source: string, target: string) => void;
  /**
   * 엣지 클릭 — "끊기" 의도 (W2', ADR-013).
   * editable 일 때만 fire. 부모가 확인 모달 + sendTodoModify 송신.
   */
  onEdgeClick?: (edge: Edge) => void;
  /**
   * 노드 드래그 종료 — position 변경 (W2', ADR-013 Stage 3).
   * editable 일 때만 fire. 부모가 debounce + sendTodoModify({position}) 책임.
   */
  onNodeDragEnd?: (nodeId: string, position: { x: number; y: number }) => void;
}

export function WorkflowCanvas({
  plan,
  direction = 'TB',
  editable = false,
  invalidatedIds,
  pendingDeleteIds,
  pendingModifyIds,
  onNodeSelect,
  onNodeContextMenu,
  onNodeDoubleClick,
  onEdgeConnect,
  onEdgeClick,
  onNodeDragEnd,
}: WorkflowCanvasProps) {
  const { nodes, edges } = useMemo(() => {
    const { nodes: baseNodes, edges: baseEdges } = planToFlow(plan, direction);
    const invalidSet = new Set(invalidatedIds ?? []);
    const deleteSet = new Set(pendingDeleteIds ?? []);
    const modifySet = new Set(pendingModifyIds ?? []);
    if (invalidSet.size === 0 && deleteSet.size === 0 && modifySet.size === 0) {
      return { nodes: baseNodes, edges: baseEdges };
    }
    // cascade + batched 시각화 inject — 기존 data 보존하면서 flag 추가.
    const nodes = baseNodes.map((n) => {
      const extra: Record<string, unknown> = {};
      if (invalidSet.has(n.id)) extra.isInvalidated = true;
      if (deleteSet.has(n.id)) extra.isPendingDelete = true;
      if (modifySet.has(n.id)) extra.isPendingModify = true;
      return Object.keys(extra).length > 0
        ? { ...n, data: { ...n.data, ...extra } }
        : n;
    });
    return { nodes, edges: baseEdges };
  }, [plan, direction, invalidatedIds, pendingDeleteIds, pendingModifyIds]);

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        nodesDraggable={editable}
        nodesConnectable={editable}
        elementsSelectable
        proOptions={{ hideAttribution: true }}
        onNodeClick={(_e, n: RFNode) => onNodeSelect?.(n.id)}
        onPaneClick={() => onNodeSelect?.(null)}
        onNodeContextMenu={(e, n: RFNode) => {
          if (!editable) return;
          e.preventDefault();
          onNodeContextMenu?.(n.id, e);
        }}
        onNodeDoubleClick={(_e, n: RFNode) => {
          if (!editable) return;
          onNodeDoubleClick?.(n.id);
        }}
        onConnect={(c: Connection) => {
          if (!editable) return;
          if (!c.source || !c.target || c.source === c.target) return;
          onEdgeConnect?.(c.source, c.target);
        }}
        onEdgeClick={(_e, edge: Edge) => {
          if (!editable) return;
          onEdgeClick?.(edge);
        }}
        onNodeDragStop={(_e, n: RFNode) => {
          if (!editable) return;
          onNodeDragEnd?.(n.id, { x: n.position.x, y: n.position.y });
        }}
      >
        <Background gap={16} className="!bg-card" />
        <Controls showInteractive={false} />
        <MiniMap
          pannable
          zoomable
          className="!bg-card !border !border-border"
          nodeColor="hsl(var(--node-task))"
        />
      </ReactFlow>
    </div>
  );
}
