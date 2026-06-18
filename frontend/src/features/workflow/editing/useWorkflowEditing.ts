/**
 * useWorkflowEditing — Workflow Canvas 편집 동작 hook (W2 + W2' Stage 5).
 *
 * 책임: 사용자 시각적 편집 액션 → ws.ts 송신 또는 editingStore.pendingOps 누적.
 *       editingStore 와 useSession.turnId 결합한 callback 들 반환.
 *
 * 분기 (applyMode):
 *   - immediate (default): 즉시 sendTodoXxx 송신 (W2 기본 동작).
 *   - batched: pendingOps 에 push, ws 송신 X. applyAllPendingOps 가 일괄 적용.
 *
 * 의존:
 *   - useSession.turnId (필수 — 없으면 모든 액션 no-op)
 *   - editingStore (UI 임시 상태 + pendingOps + applyMode)
 *   - useExecution.plan (엣지 연결/끊기 시 depends_on 계산)
 *   - ws.ts 송신 함수 (sendTodoModify/Delete/Add)
 *
 * spec: 62 §5.1 / ADR-012 §2.1 / ADR-013 §6
 */
import { useCallback } from 'react';
import { useSession } from '@/features/session/store';
import { useExecution } from '@/features/execution/store';
import {
  sendTodoAdd,
  sendTodoDelete,
  sendTodoModify,
  type PartialTodo,
} from '@/api/ws';
import { useEditingStore, type PendingOp } from '../store/editingStore';

export interface UseWorkflowEditingResult {
  /** 컨텍스트 메뉴 열기 — 우클릭 위치 + 대상 노드 저장. */
  openContextMenu: (nodeId: string, position: { x: number; y: number }) => void;
  /** 컨텍스트 메뉴 닫기. */
  closeContextMenu: () => void;
  /** 속성 패널 열기 (더블클릭 트리거). */
  openPropertyPanel: (nodeId: string) => void;
  /** 속성 패널 닫기. */
  closePropertyPanel: () => void;
  /** 노드 선택. */
  selectNode: (nodeId: string | null) => void;

  /**
   * 노드 삭제.
   * - immediate: 즉시 sendTodoDelete.
   * - batched: pendingOps 에 누적, ws 송신 X.
   * turnId 없으면 no-op (false).
   */
  deleteTodo: (todoId: string) => boolean;
  /** 노드 속성 수정 (applyMode 분기 동일). */
  modifyTodo: (todoId: string, changes: Record<string, unknown>) => boolean;
  /** 신규 노드 추가 (applyMode 분기 동일). */
  addTodo: (todo: PartialTodo) => boolean;
  /**
   * 엣지 연결 — target todo 의 depends_on 에 source 추가 (W2', ADR-013 Stage 1).
   * 이미 존재하는 의존이면 no-op true. 내부적으로 modifyTodo 위임 → applyMode 자동 따름.
   */
  connectEdge: (source: string, target: string) => boolean;
  /**
   * 엣지 끊기 — target todo 의 depends_on 에서 source 제거.
   * 의존이 없으면 no-op true.
   */
  disconnectEdge: (source: string, target: string) => boolean;
  /**
   * batched 모드의 pendingOps 를 순서대로 일괄 송신 + 큐 비움 (Stage 5).
   * Stage 6 의 BatchedToolbar "변경 적용" 버튼이 호출.
   * @returns 송신된 op 개수. turnId 없거나 큐 비어있으면 0.
   *          (atomicity 보장 X — POC 단계. 중간 fail 은 백엔드 hitl_ack 으로 인지)
   */
  applyAllPendingOps: () => number;
}

/**
 * pendingOp 1건을 적절한 ws 송신 함수로 dispatch.
 * applyAllPendingOps 와 immediate 분기의 "최종 송신" 부분이 공유.
 */
function dispatchOp(turnId: string, op: PendingOp): boolean {
  switch (op.kind) {
    case 'delete':
      return sendTodoDelete(turnId, op.todoId);
    case 'modify':
      return sendTodoModify(turnId, op.todoId, op.changes);
    case 'add':
      return sendTodoAdd(turnId, op.todo);
  }
}

export function useWorkflowEditing(): UseWorkflowEditingResult {
  const openContextMenuRaw = useEditingStore((s) => s.openContextMenu);
  const closeContextMenuRaw = useEditingStore((s) => s.closeContextMenu);
  const openPropertyPanelRaw = useEditingStore((s) => s.openPropertyPanel);
  const closePropertyPanelRaw = useEditingStore((s) => s.closePropertyPanel);
  const selectRaw = useEditingStore((s) => s.select);

  const openContextMenu = useCallback(
    (nodeId: string, position: { x: number; y: number }) => {
      openContextMenuRaw({ x: position.x, y: position.y, nodeId });
    },
    [openContextMenuRaw],
  );

  const closeContextMenu = useCallback(() => {
    closeContextMenuRaw();
  }, [closeContextMenuRaw]);

  const openPropertyPanel = useCallback(
    (nodeId: string) => {
      openPropertyPanelRaw(nodeId);
    },
    [openPropertyPanelRaw],
  );

  const closePropertyPanel = useCallback(() => {
    closePropertyPanelRaw();
  }, [closePropertyPanelRaw]);

  const selectNode = useCallback(
    (nodeId: string | null) => {
      selectRaw(nodeId);
    },
    [selectRaw],
  );

  // applyMode 가 'batched' 면 pendingOps 에 push 후 true 반환, 송신 X.
  // 그 외 (immediate) 면 false 반환 → 호출자가 sendTodoXxx 직접 호출.
  const enqueueIfBatched = useCallback((op: PendingOp): boolean => {
    const { applyMode, addPendingOp } = useEditingStore.getState();
    if (applyMode !== 'batched') return false;
    addPendingOp(op);
    return true;
  }, []);

  const deleteTodo = useCallback(
    (todoId: string): boolean => {
      const turnId = useSession.getState().turnId;
      if (!turnId) return false;
      if (enqueueIfBatched({ kind: 'delete', todoId })) return true;
      return sendTodoDelete(turnId, todoId);
    },
    [enqueueIfBatched],
  );

  const modifyTodo = useCallback(
    (todoId: string, changes: Record<string, unknown>): boolean => {
      const turnId = useSession.getState().turnId;
      if (!turnId) return false;
      if (enqueueIfBatched({ kind: 'modify', todoId, changes })) return true;
      return sendTodoModify(turnId, todoId, changes);
    },
    [enqueueIfBatched],
  );

  const addTodo = useCallback(
    (todo: PartialTodo): boolean => {
      const turnId = useSession.getState().turnId;
      if (!turnId) return false;
      if (enqueueIfBatched({ kind: 'add', todo })) return true;
      return sendTodoAdd(turnId, todo);
    },
    [enqueueIfBatched],
  );

  const connectEdge = useCallback(
    (source: string, target: string): boolean => {
      const turnId = useSession.getState().turnId;
      if (!turnId) return false;
      const plan = useExecution.getState().plan;
      if (!plan) return false;
      const targetTodo = plan.todos.find((t) => t.id === target);
      if (!targetTodo) return false;
      // 이미 의존이면 no-op (성공 처리).
      if (targetTodo.depends_on.includes(source)) return true;
      const newDepends = [...targetTodo.depends_on, source];
      // modifyTodo 로 위임 → applyMode 분기 자동 처리.
      return modifyTodo(target, { depends_on: newDepends });
    },
    [modifyTodo],
  );

  const disconnectEdge = useCallback(
    (source: string, target: string): boolean => {
      const turnId = useSession.getState().turnId;
      if (!turnId) return false;
      const plan = useExecution.getState().plan;
      if (!plan) return false;
      const targetTodo = plan.todos.find((t) => t.id === target);
      if (!targetTodo) return false;
      if (!targetTodo.depends_on.includes(source)) return true; // 없으면 no-op true.
      const newDepends = targetTodo.depends_on.filter((d) => d !== source);
      return modifyTodo(target, { depends_on: newDepends });
    },
    [modifyTodo],
  );

  const applyAllPendingOps = useCallback((): number => {
    const turnId = useSession.getState().turnId;
    if (!turnId) return 0;
    const { pendingOps, clearPendingOps } = useEditingStore.getState();
    if (pendingOps.length === 0) return 0;
    // 순서 보존 송신. atomicity 는 POC 단계 미보장 — 중간 fail 시 hitl_ack 으로 사용자 인지.
    let sent = 0;
    for (const op of pendingOps) {
      dispatchOp(turnId, op);
      sent += 1;
    }
    clearPendingOps();
    return sent;
  }, []);

  return {
    openContextMenu,
    closeContextMenu,
    openPropertyPanel,
    closePropertyPanel,
    selectNode,
    deleteTodo,
    modifyTodo,
    addTodo,
    connectEdge,
    disconnectEdge,
    applyAllPendingOps,
  };
}
