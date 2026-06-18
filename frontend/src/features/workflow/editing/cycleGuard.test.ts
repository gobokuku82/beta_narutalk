/**
 * cycleGuard 단위 테스트 — DAG cycle 사전 차단 (ADR-013 Stage 2).
 */
import { describe, expect, it } from 'vitest';
import type { Plan, PlannedTodo } from '@/api/schemas';
import { wouldAddEdgeCreateCycle } from './cycleGuard';

function todo(id: string, depends_on: string[]): PlannedTodo {
  return {
    id,
    task_type: 'analysis',
    agent: null,
    tool: null,
    tool_params: {},
    depends_on,
    priority: 1,
    rationale: '',
    position: null,
    node_type: 'task',
    visualization_meta: {},
  };
}

function plan(todos: PlannedTodo[]): Plan {
  return { teams_selected: [], plan_notes: '', dag: {}, todos };
}

describe('wouldAddEdgeCreateCycle', () => {
  it('self-loop — 즉시 cycle', () => {
    const p = plan([todo('A', [])]);
    expect(wouldAddEdgeCreateCycle(p, 'A', 'A')).toBe(true);
  });

  it('빈 의존 그래프 — A → B 안전', () => {
    const p = plan([todo('A', []), todo('B', [])]);
    expect(wouldAddEdgeCreateCycle(p, 'A', 'B')).toBe(false);
  });

  it('단순 사슬 A → B 존재, B → A 추가 = cycle', () => {
    // 현재: B.depends_on = [A] (A → B).
    // 새 엣지 B → A 추가 시도 = A.depends_on 에 B 추가.
    // → A 가 B 에 의존 + B 가 A 에 의존 = cycle.
    const p = plan([todo('A', []), todo('B', ['A'])]);
    expect(wouldAddEdgeCreateCycle(p, 'B', 'A')).toBe(true);
  });

  it('단순 사슬 A → B 존재, A → B 다시 추가 = 안전 (중복)', () => {
    // 중복 의존은 이미 connectEdge 에서 no-op 처리. 본 함수는 cycle 만 봄.
    // 이 케이스는 cycle 이 아니라서 false.
    const p = plan([todo('A', []), todo('B', ['A'])]);
    expect(wouldAddEdgeCreateCycle(p, 'A', 'B')).toBe(false);
  });

  it('긴 사슬 A → B → C, C → A 추가 = cycle (transitive)', () => {
    const p = plan([
      todo('A', []),
      todo('B', ['A']),
      todo('C', ['B']),
    ]);
    expect(wouldAddEdgeCreateCycle(p, 'C', 'A')).toBe(true);
  });

  it('긴 사슬 A → B → C, A → C 추가 = 안전 (shortcut)', () => {
    // A → C 는 그래프를 더 dense 하게 만들 뿐, cycle 아님.
    const p = plan([
      todo('A', []),
      todo('B', ['A']),
      todo('C', ['B']),
    ]);
    expect(wouldAddEdgeCreateCycle(p, 'A', 'C')).toBe(false);
  });

  it('병렬 분기 A → B, A → C — D → A 추가 = 안전 (D 신규 root)', () => {
    const p = plan([
      todo('A', []),
      todo('B', ['A']),
      todo('C', ['A']),
      todo('D', []),
    ]);
    expect(wouldAddEdgeCreateCycle(p, 'D', 'A')).toBe(false);
  });

  it('병렬 분기 + 후속 cycle 시도 — B → A 추가 = cycle', () => {
    const p = plan([
      todo('A', []),
      todo('B', ['A']),
      todo('C', ['A']),
    ]);
    expect(wouldAddEdgeCreateCycle(p, 'B', 'A')).toBe(true);
  });

  it('Y 모양 A → C, B → C, C → A 추가 = cycle', () => {
    const p = plan([
      todo('A', []),
      todo('B', []),
      todo('C', ['A', 'B']),
    ]);
    expect(wouldAddEdgeCreateCycle(p, 'C', 'A')).toBe(true);
  });

  it('Y 모양 + 무관 노드 — C → D 추가 = 안전', () => {
    const p = plan([
      todo('A', []),
      todo('B', []),
      todo('C', ['A', 'B']),
      todo('D', []),
    ]);
    expect(wouldAddEdgeCreateCycle(p, 'C', 'D')).toBe(false);
  });

  it('Diamond A → B,C → D, D → A 추가 = cycle', () => {
    const p = plan([
      todo('A', []),
      todo('B', ['A']),
      todo('C', ['A']),
      todo('D', ['B', 'C']),
    ]);
    expect(wouldAddEdgeCreateCycle(p, 'D', 'A')).toBe(true);
  });

  it('Diamond + 무관 — A → D 추가 = 안전 (shortcut)', () => {
    const p = plan([
      todo('A', []),
      todo('B', ['A']),
      todo('C', ['A']),
      todo('D', ['B', 'C']),
    ]);
    expect(wouldAddEdgeCreateCycle(p, 'A', 'D')).toBe(false);
  });
});
