/**
 * editingStore — Workflow Canvas 편집 임시 UI 상태 (W2 + W2' Stage 5).
 *
 * 책임:
 *   - 선택된 노드 id (단일 선택, multi-select 는 W3+ 검토)
 *   - 우클릭 컨텍스트 메뉴 위치 + 대상
 *   - 속성 패널 열림 여부
 *   - 변경 적용 모드 (immediate / batched)
 *   - batched 모드에서 누적되는 PendingOp 큐 (Stage 5)
 *
 * 서버 진실 캐시 (`useExecution.plan`) 와 *분리*. turn 끝나면 reset.
 *
 * spec: 62 §5.1 / ADR-012 §1.3 / ADR-013 §6
 */
import { create } from 'zustand';
import type { PartialTodo } from '@/api/ws';

export type ApplyMode = 'immediate' | 'batched';

export interface ContextMenuPosition {
  x: number;
  y: number;
  nodeId: string;
}

/**
 * batched 모드에서 누적되는 편집 단위.
 * - delete: 노드 1개 삭제 (cascade 는 백엔드가 계산)
 * - modify: 노드 1개의 일부 필드 변경 (connectEdge/disconnectEdge 는 depends_on 변경으로 들어옴)
 * - add: 신규 노드 1개 추가 (PartialTodo)
 *
 * Stage 5: 누적만, atomicity 보장 안 함 (백엔드 batch endpoint 없음 — POC).
 * Stage 6 의 BatchedToolbar 가 applyAll 시점에 순차 송신.
 */
export type PendingOp =
  | { kind: 'delete'; todoId: string }
  | { kind: 'modify'; todoId: string; changes: Record<string, unknown> }
  | { kind: 'add'; todo: PartialTodo };

export interface EditingState {
  /** 선택된 노드 id. 단일 선택 (W2). null = 없음. */
  selectedNodeId: string | null;
  /** 속성 패널 열림 여부. */
  propertyPanelOpen: boolean;
  /** 컨텍스트 메뉴 위치 + 대상 노드. null = 닫힘. */
  contextMenu: ContextMenuPosition | null;
  /**
   * 변경 적용 모드.
   * - 'immediate' (default, ADR-013 Q2): 우클릭 삭제 즉시 송신.
   * - 'batched': 누적 후 "변경 적용" 클릭 시 일괄.
   */
  applyMode: ApplyMode;
  /**
   * batched 모드에서 누적된 편집 큐 (W2' Stage 5).
   * immediate 모드에서는 항상 빈 배열 유지 — useWorkflowEditing 이 분기.
   * insertion-order 보존 (apply 시 동일 순서 송신).
   */
  pendingOps: readonly PendingOp[];

  /** 노드 선택. null 전달 시 해제. */
  select: (id: string | null) => void;
  /** 속성 패널 열기 — selectedNodeId 자동 설정. */
  openPropertyPanel: (nodeId: string) => void;
  /** 속성 패널 닫기. selectedNodeId 는 유지 (외부 클릭으로만 해제). */
  closePropertyPanel: () => void;
  /** 컨텍스트 메뉴 열기. */
  openContextMenu: (m: ContextMenuPosition) => void;
  /** 컨텍스트 메뉴 닫기. */
  closeContextMenu: () => void;
  /** applyMode 변경. batched ↔ immediate 전환 시 pendingOps 는 그대로 유지 (사용자가 보고 결정). */
  setApplyMode: (mode: ApplyMode) => void;
  /** PendingOp 큐 끝에 추가 (Stage 5). */
  addPendingOp: (op: PendingOp) => void;
  /** PendingOp 큐 전체 비우기 — apply 완료 또는 사용자 취소 시 (Stage 5). */
  clearPendingOps: () => void;
  /** 모든 편집 임시 상태 리셋 — turn 시작 / 페이지 이탈 시. */
  reset: () => void;
}

const initialState = {
  selectedNodeId: null,
  propertyPanelOpen: false,
  contextMenu: null,
  applyMode: 'immediate' as ApplyMode,
  pendingOps: [] as readonly PendingOp[],
};

export const useEditingStore = create<EditingState>((set) => ({
  ...initialState,

  select: (id) => set({ selectedNodeId: id }),

  openPropertyPanel: (nodeId) =>
    set({ selectedNodeId: nodeId, propertyPanelOpen: true, contextMenu: null }),

  closePropertyPanel: () => set({ propertyPanelOpen: false }),

  openContextMenu: (m) => set({ contextMenu: m }),

  closeContextMenu: () => set({ contextMenu: null }),

  setApplyMode: (mode) => set({ applyMode: mode }),

  addPendingOp: (op) => set((s) => ({ pendingOps: [...s.pendingOps, op] })),

  clearPendingOps: () => set({ pendingOps: [] }),

  reset: () => set(initialState),
}));
