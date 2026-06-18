/**
 * editingStore 단위 테스트 — 편집 임시 상태 전이.
 *
 * spec: ADR-012 / 62 §5.1
 */
import { beforeEach, describe, expect, it } from 'vitest';
import { useEditingStore } from './editingStore';

describe('useEditingStore', () => {
  beforeEach(() => {
    useEditingStore.getState().reset();
  });

  it('초기 상태 — 모두 null/false/immediate + pendingOps 빈 배열', () => {
    const s = useEditingStore.getState();
    expect(s.selectedNodeId).toBeNull();
    expect(s.propertyPanelOpen).toBe(false);
    expect(s.contextMenu).toBeNull();
    expect(s.applyMode).toBe('immediate');
    expect(s.pendingOps).toEqual([]);
  });

  it('select(id) — selectedNodeId 설정', () => {
    useEditingStore.getState().select('todo_1');
    expect(useEditingStore.getState().selectedNodeId).toBe('todo_1');
    useEditingStore.getState().select(null);
    expect(useEditingStore.getState().selectedNodeId).toBeNull();
  });

  it('openPropertyPanel — selectedNodeId + propertyPanelOpen 동시 + contextMenu 닫힘', () => {
    // 미리 컨텍스트 메뉴 열려있는 상태.
    useEditingStore.getState().openContextMenu({ x: 10, y: 20, nodeId: 'todo_2' });
    expect(useEditingStore.getState().contextMenu).not.toBeNull();

    useEditingStore.getState().openPropertyPanel('todo_1');
    const s = useEditingStore.getState();
    expect(s.selectedNodeId).toBe('todo_1');
    expect(s.propertyPanelOpen).toBe(true);
    // 속성 패널 열면 컨텍스트 메뉴 자동 닫힘 (UI 충돌 방지).
    expect(s.contextMenu).toBeNull();
  });

  it('closePropertyPanel — selectedNodeId 는 유지', () => {
    useEditingStore.getState().openPropertyPanel('todo_1');
    useEditingStore.getState().closePropertyPanel();
    const s = useEditingStore.getState();
    expect(s.propertyPanelOpen).toBe(false);
    expect(s.selectedNodeId).toBe('todo_1'); // 유지
  });

  it('openContextMenu / closeContextMenu — 위치/대상 저장 후 해제', () => {
    useEditingStore.getState().openContextMenu({ x: 100, y: 200, nodeId: 'todo_3' });
    expect(useEditingStore.getState().contextMenu).toEqual({
      x: 100,
      y: 200,
      nodeId: 'todo_3',
    });
    useEditingStore.getState().closeContextMenu();
    expect(useEditingStore.getState().contextMenu).toBeNull();
  });

  it('setApplyMode — immediate ↔ batched 전환', () => {
    useEditingStore.getState().setApplyMode('batched');
    expect(useEditingStore.getState().applyMode).toBe('batched');
    useEditingStore.getState().setApplyMode('immediate');
    expect(useEditingStore.getState().applyMode).toBe('immediate');
  });

  it('reset — 모든 임시 상태 초기로 (turn 종료 / 페이지 이탈 시) + pendingOps 초기화', () => {
    useEditingStore.getState().openPropertyPanel('todo_1');
    useEditingStore.getState().openContextMenu({ x: 50, y: 60, nodeId: 'todo_2' });
    useEditingStore.getState().setApplyMode('batched');
    useEditingStore.getState().addPendingOp({ kind: 'delete', todoId: 'todo_x' });

    useEditingStore.getState().reset();
    const s = useEditingStore.getState();
    expect(s.selectedNodeId).toBeNull();
    expect(s.propertyPanelOpen).toBe(false);
    expect(s.contextMenu).toBeNull();
    expect(s.applyMode).toBe('immediate');
    expect(s.pendingOps).toEqual([]);
  });

  // ───── W2' Stage 5 — pendingOps 누적 (ADR-013 §6) ─────

  it('addPendingOp — kind=delete 1개 누적', () => {
    useEditingStore.getState().addPendingOp({ kind: 'delete', todoId: 'todo_3' });
    expect(useEditingStore.getState().pendingOps).toEqual([
      { kind: 'delete', todoId: 'todo_3' },
    ]);
  });

  it('addPendingOp — 여러 종류 순서 보존', () => {
    const store = useEditingStore.getState();
    store.addPendingOp({ kind: 'delete', todoId: 'todo_a' });
    store.addPendingOp({
      kind: 'modify',
      todoId: 'todo_b',
      changes: { rationale: '수정됨' },
    });
    store.addPendingOp({ kind: 'add', todo: { task_type: 'analysis' } });
    expect(useEditingStore.getState().pendingOps).toEqual([
      { kind: 'delete', todoId: 'todo_a' },
      { kind: 'modify', todoId: 'todo_b', changes: { rationale: '수정됨' } },
      { kind: 'add', todo: { task_type: 'analysis' } },
    ]);
  });

  it('clearPendingOps — 큐 비움 (apply 완료 또는 사용자 취소)', () => {
    useEditingStore.getState().addPendingOp({ kind: 'delete', todoId: 'todo_x' });
    useEditingStore.getState().addPendingOp({ kind: 'delete', todoId: 'todo_y' });
    expect(useEditingStore.getState().pendingOps).toHaveLength(2);
    useEditingStore.getState().clearPendingOps();
    expect(useEditingStore.getState().pendingOps).toEqual([]);
  });

  it('setApplyMode 전환 시 pendingOps 는 *유지* (사용자가 보고 결정)', () => {
    useEditingStore.getState().setApplyMode('batched');
    useEditingStore.getState().addPendingOp({ kind: 'delete', todoId: 'todo_x' });
    useEditingStore.getState().setApplyMode('immediate');
    // immediate 로 돌아와도 큐는 그대로 — 명시적 apply / cancel 만 비움.
    expect(useEditingStore.getState().pendingOps).toHaveLength(1);
  });
});
