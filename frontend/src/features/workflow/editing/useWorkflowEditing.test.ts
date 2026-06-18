/**
 * useWorkflowEditing 단위 테스트 — turnId 가드 + ws 송신 매핑.
 *
 * spec: ADR-012 / 62 §5.1
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useSession } from '@/features/session/store';

// ws 송신 함수 mock.
vi.mock('@/api/ws', () => ({
  sendTodoDelete: vi.fn(() => true),
  sendTodoModify: vi.fn(() => true),
  sendTodoAdd: vi.fn(() => true),
  sendHitlMessage: vi.fn(() => true),
  sendHitlResponse: vi.fn(() => true),
}));

import { sendTodoDelete, sendTodoModify, sendTodoAdd } from '@/api/ws';
import { useWorkflowEditing } from './useWorkflowEditing';
import { useEditingStore } from '../store/editingStore';
import { useExecution } from '@/features/execution/store';
import type { Plan } from '@/api/schemas';

const SAMPLE_PLAN: Plan = {
  teams_selected: [],
  plan_notes: '',
  dag: {},
  todos: [
    {
      id: 'todo_001',
      task_type: 'analysis',
      agent: null,
      tool: null,
      tool_params: {},
      depends_on: [],
      priority: 1,
      rationale: '',
      position: null,
      node_type: 'task',
      visualization_meta: {},
    },
    {
      id: 'todo_002',
      task_type: 'analysis',
      agent: null,
      tool: null,
      tool_params: {},
      depends_on: ['todo_001'],
      priority: 1,
      rationale: '',
      position: null,
      node_type: 'task',
      visualization_meta: {},
    },
  ],
};

describe('useWorkflowEditing', () => {
  beforeEach(() => {
    useSession.setState({ turnId: null, conversationId: null });
    useEditingStore.getState().reset();
    vi.clearAllMocks();
  });

  it('turnId 없으면 deleteTodo / modifyTodo / addTodo 모두 no-op (false)', () => {
    const { result } = renderHook(() => useWorkflowEditing());
    expect(result.current.deleteTodo('todo_1')).toBe(false);
    expect(result.current.modifyTodo('todo_1', { rationale: 'x' })).toBe(false);
    expect(result.current.addTodo({ task_type: 'analysis' })).toBe(false);
    expect(sendTodoDelete).not.toHaveBeenCalled();
    expect(sendTodoModify).not.toHaveBeenCalled();
    expect(sendTodoAdd).not.toHaveBeenCalled();
  });

  it('turnId 있으면 deleteTodo → sendTodoDelete 호출', () => {
    useSession.setState({ turnId: 'turn_1' });
    const { result } = renderHook(() => useWorkflowEditing());
    expect(result.current.deleteTodo('todo_1')).toBe(true);
    expect(sendTodoDelete).toHaveBeenCalledWith('turn_1', 'todo_1');
  });

  it('turnId 있으면 modifyTodo → sendTodoModify(turnId, todoId, changes)', () => {
    useSession.setState({ turnId: 'turn_1' });
    const { result } = renderHook(() => useWorkflowEditing());
    const changes = { rationale: '새 설명', agent: 'analyst' };
    expect(result.current.modifyTodo('todo_2', changes)).toBe(true);
    expect(sendTodoModify).toHaveBeenCalledWith('turn_1', 'todo_2', changes);
  });

  it('turnId 있으면 addTodo → sendTodoAdd(turnId, todo)', () => {
    useSession.setState({ turnId: 'turn_1' });
    const { result } = renderHook(() => useWorkflowEditing());
    const todo = { task_type: 'analysis', agent: 'analyst', depends_on: [] };
    expect(result.current.addTodo(todo)).toBe(true);
    expect(sendTodoAdd).toHaveBeenCalledWith('turn_1', todo);
  });

  it('openContextMenu → editingStore.contextMenu 설정', () => {
    const { result } = renderHook(() => useWorkflowEditing());
    act(() => {
      result.current.openContextMenu('todo_3', { x: 50, y: 60 });
    });
    expect(useEditingStore.getState().contextMenu).toEqual({
      x: 50,
      y: 60,
      nodeId: 'todo_3',
    });
  });

  it('closeContextMenu → editingStore.contextMenu null', () => {
    useEditingStore.getState().openContextMenu({ x: 1, y: 2, nodeId: 'x' });
    const { result } = renderHook(() => useWorkflowEditing());
    act(() => {
      result.current.closeContextMenu();
    });
    expect(useEditingStore.getState().contextMenu).toBeNull();
  });

  it('openPropertyPanel → store 의 propertyPanelOpen + selectedNodeId 동시 설정', () => {
    const { result } = renderHook(() => useWorkflowEditing());
    act(() => {
      result.current.openPropertyPanel('todo_4');
    });
    const s = useEditingStore.getState();
    expect(s.propertyPanelOpen).toBe(true);
    expect(s.selectedNodeId).toBe('todo_4');
  });

  it('selectNode → editingStore.selectedNodeId 설정 / null 해제', () => {
    const { result } = renderHook(() => useWorkflowEditing());
    act(() => result.current.selectNode('todo_5'));
    expect(useEditingStore.getState().selectedNodeId).toBe('todo_5');
    act(() => result.current.selectNode(null));
    expect(useEditingStore.getState().selectedNodeId).toBeNull();
  });

  // ─────────────────────────────────────────────────────────
  // ADR-013 Stage 1 — 엣지 연결/끊기
  // ─────────────────────────────────────────────────────────

  it('connectEdge — turnId 없으면 false, ws 송신 X', () => {
    useExecution.setState({ plan: SAMPLE_PLAN });
    const { result } = renderHook(() => useWorkflowEditing());
    expect(result.current.connectEdge('todo_001', 'todo_002')).toBe(false);
    expect(sendTodoModify).not.toHaveBeenCalled();
  });

  it('connectEdge — plan 없으면 false', () => {
    useSession.setState({ turnId: 'turn_1' });
    useExecution.setState({ plan: null });
    const { result } = renderHook(() => useWorkflowEditing());
    expect(result.current.connectEdge('todo_001', 'todo_002')).toBe(false);
    expect(sendTodoModify).not.toHaveBeenCalled();
  });

  it('connectEdge — target todo 의 depends_on 에 source 추가하여 송신', () => {
    useSession.setState({ turnId: 'turn_1' });
    useExecution.setState({ plan: SAMPLE_PLAN });
    const { result } = renderHook(() => useWorkflowEditing());
    // todo_002 의 depends_on = [todo_001]. todo_003 추가 시도 (가상).
    // SAMPLE_PLAN 에는 todo_003 없지만 connectEdge 는 target id 만 보고 송신.
    // 실제 시나리오: 사용자가 새 엣지 만들 때 source 가 다른 todo.
    // 여기는 todo_001 → todo_002 시 이미 존재 → no-op true.
    expect(result.current.connectEdge('todo_001', 'todo_002')).toBe(true);
    expect(sendTodoModify).not.toHaveBeenCalled(); // 이미 존재 — no-op
  });

  it('connectEdge — 새 의존이면 [기존, source] 로 송신', () => {
    useSession.setState({ turnId: 'turn_1' });
    useExecution.setState({ plan: SAMPLE_PLAN });
    const { result } = renderHook(() => useWorkflowEditing());
    // todo_002 의 depends_on = [todo_001]. 새 source 추가 가상 시나리오.
    // 새 source = 'todo_xxx' (plan 에 없어도 됨, depends_on 은 단지 id 배열).
    expect(result.current.connectEdge('todo_xxx', 'todo_002')).toBe(true);
    expect(sendTodoModify).toHaveBeenCalledWith('turn_1', 'todo_002', {
      depends_on: ['todo_001', 'todo_xxx'],
    });
  });

  it('disconnectEdge — depends_on 에서 source 제거하여 송신', () => {
    useSession.setState({ turnId: 'turn_1' });
    useExecution.setState({ plan: SAMPLE_PLAN });
    const { result } = renderHook(() => useWorkflowEditing());
    expect(result.current.disconnectEdge('todo_001', 'todo_002')).toBe(true);
    expect(sendTodoModify).toHaveBeenCalledWith('turn_1', 'todo_002', {
      depends_on: [],
    });
  });

  it('disconnectEdge — 의존 없으면 no-op true, 송신 X', () => {
    useSession.setState({ turnId: 'turn_1' });
    useExecution.setState({ plan: SAMPLE_PLAN });
    const { result } = renderHook(() => useWorkflowEditing());
    expect(result.current.disconnectEdge('todo_xxx', 'todo_002')).toBe(true);
    expect(sendTodoModify).not.toHaveBeenCalled();
  });

  // ─────────────────────────────────────────────────────────
  // ADR-013 Stage 5 — batched 모드 (applyMode='batched')
  // ws 송신 대신 editingStore.pendingOps 누적, applyAllPendingOps 가 일괄 송신.
  // ─────────────────────────────────────────────────────────

  it('batched 모드 — deleteTodo 는 ws 송신 X, pendingOps 에 delete 추가', () => {
    useSession.setState({ turnId: 'turn_1' });
    useEditingStore.getState().setApplyMode('batched');
    const { result } = renderHook(() => useWorkflowEditing());
    expect(result.current.deleteTodo('todo_1')).toBe(true);
    expect(sendTodoDelete).not.toHaveBeenCalled();
    expect(useEditingStore.getState().pendingOps).toEqual([
      { kind: 'delete', todoId: 'todo_1' },
    ]);
  });

  it('batched 모드 — modifyTodo 는 ws 송신 X, pendingOps 에 modify 추가', () => {
    useSession.setState({ turnId: 'turn_1' });
    useEditingStore.getState().setApplyMode('batched');
    const { result } = renderHook(() => useWorkflowEditing());
    const changes = { rationale: '바뀜' };
    expect(result.current.modifyTodo('todo_2', changes)).toBe(true);
    expect(sendTodoModify).not.toHaveBeenCalled();
    expect(useEditingStore.getState().pendingOps).toEqual([
      { kind: 'modify', todoId: 'todo_2', changes },
    ]);
  });

  it('batched 모드 — addTodo 는 ws 송신 X, pendingOps 에 add 추가', () => {
    useSession.setState({ turnId: 'turn_1' });
    useEditingStore.getState().setApplyMode('batched');
    const { result } = renderHook(() => useWorkflowEditing());
    const todo = { task_type: 'analysis', agent: 'analyst', depends_on: [] };
    expect(result.current.addTodo(todo)).toBe(true);
    expect(sendTodoAdd).not.toHaveBeenCalled();
    expect(useEditingStore.getState().pendingOps).toEqual([
      { kind: 'add', todo },
    ]);
  });

  it('batched 모드 — connectEdge 는 modify 로 변환되어 pendingOps 누적, ws 송신 X', () => {
    useSession.setState({ turnId: 'turn_1' });
    useExecution.setState({ plan: SAMPLE_PLAN });
    useEditingStore.getState().setApplyMode('batched');
    const { result } = renderHook(() => useWorkflowEditing());
    // todo_002.depends_on = [todo_001]. 새 source = todo_xxx.
    expect(result.current.connectEdge('todo_xxx', 'todo_002')).toBe(true);
    expect(sendTodoModify).not.toHaveBeenCalled();
    expect(useEditingStore.getState().pendingOps).toEqual([
      {
        kind: 'modify',
        todoId: 'todo_002',
        changes: { depends_on: ['todo_001', 'todo_xxx'] },
      },
    ]);
  });

  it('batched 모드 — disconnectEdge 는 modify 로 변환되어 pendingOps 누적', () => {
    useSession.setState({ turnId: 'turn_1' });
    useExecution.setState({ plan: SAMPLE_PLAN });
    useEditingStore.getState().setApplyMode('batched');
    const { result } = renderHook(() => useWorkflowEditing());
    expect(result.current.disconnectEdge('todo_001', 'todo_002')).toBe(true);
    expect(sendTodoModify).not.toHaveBeenCalled();
    expect(useEditingStore.getState().pendingOps).toEqual([
      { kind: 'modify', todoId: 'todo_002', changes: { depends_on: [] } },
    ]);
  });

  it('batched 모드 — connectEdge 가 이미 존재하는 의존이면 no-op (pendingOps 추가 X)', () => {
    useSession.setState({ turnId: 'turn_1' });
    useExecution.setState({ plan: SAMPLE_PLAN });
    useEditingStore.getState().setApplyMode('batched');
    const { result } = renderHook(() => useWorkflowEditing());
    expect(result.current.connectEdge('todo_001', 'todo_002')).toBe(true);
    expect(sendTodoModify).not.toHaveBeenCalled();
    expect(useEditingStore.getState().pendingOps).toEqual([]);
  });

  // ─────────────────────────────────────────────────────────
  // applyAllPendingOps — Stage 6 의 BatchedToolbar 가 호출.
  // 누적된 op 들을 순서대로 sendTodoXxx 송신 + clearPendingOps.
  // ─────────────────────────────────────────────────────────

  it('applyAllPendingOps — pendingOps 순회 + sendXxx 호출 + 큐 비움', () => {
    useSession.setState({ turnId: 'turn_1' });
    useEditingStore.getState().setApplyMode('batched');
    const store = useEditingStore.getState();
    store.addPendingOp({ kind: 'delete', todoId: 'todo_a' });
    store.addPendingOp({
      kind: 'modify',
      todoId: 'todo_b',
      changes: { rationale: 'r' },
    });
    store.addPendingOp({ kind: 'add', todo: { task_type: 'analysis' } });

    const { result } = renderHook(() => useWorkflowEditing());
    const sentCount = result.current.applyAllPendingOps();
    expect(sentCount).toBe(3);
    expect(sendTodoDelete).toHaveBeenCalledWith('turn_1', 'todo_a');
    expect(sendTodoModify).toHaveBeenCalledWith('turn_1', 'todo_b', { rationale: 'r' });
    expect(sendTodoAdd).toHaveBeenCalledWith('turn_1', { task_type: 'analysis' });
    expect(useEditingStore.getState().pendingOps).toEqual([]);
  });

  it('applyAllPendingOps — turnId 없으면 0 반환, 송신 X, 큐 유지', () => {
    useEditingStore.getState().setApplyMode('batched');
    useEditingStore.getState().addPendingOp({ kind: 'delete', todoId: 'todo_x' });
    const { result } = renderHook(() => useWorkflowEditing());
    expect(result.current.applyAllPendingOps()).toBe(0);
    expect(sendTodoDelete).not.toHaveBeenCalled();
    expect(useEditingStore.getState().pendingOps).toHaveLength(1);
  });

  it('applyAllPendingOps — 큐 비어있으면 0 반환', () => {
    useSession.setState({ turnId: 'turn_1' });
    const { result } = renderHook(() => useWorkflowEditing());
    expect(result.current.applyAllPendingOps()).toBe(0);
    expect(sendTodoDelete).not.toHaveBeenCalled();
  });
});
