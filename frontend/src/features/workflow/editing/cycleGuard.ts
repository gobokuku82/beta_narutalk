/**
 * cycleGuard — DAG cycle 사전 차단 (W2', ADR-013 Stage 2).
 *
 * 책임: 프론트가 *드래그 중* 새 엣지가 cycle 만들 지 DFS 로 검증.
 *       cycle 이면 drop 거부 + 시각 피드백 (빨간 X).
 *       백엔드 `TodoManager.validate._detect_cycle` 와 의미적 일치 — fall-back.
 *
 * 사용:
 *   const wouldCreateCycle = wouldAddEdgeCreateCycle(plan, source, target);
 *   if (wouldCreateCycle) { reject + UI 피드백 } else { sendTodoModify }
 *
 * spec: 62 §5.1 / ADR-013 §3
 */
import type { Plan, PlannedTodo } from '@/api/schemas';

/**
 * 새 엣지 (source → target) 추가가 cycle 을 만들지 검증.
 *
 * 의미 모델:
 *   엣지 source → target = "source 실행 후 target 실행" (실행 흐름 방향).
 *   schemas 표현: target.depends_on 에 source 포함.
 *
 * 알고리즘:
 *   1. children map build: parent → set(children).
 *      child.depends_on 의 각 parent 에 대해 child 를 그 parent 의 children 에 추가.
 *   2. 새 엣지 추가 후 cycle 조건 = 기존 그래프에서 *target → ... → source* 경로 존재.
 *      (target 후에 source 가 실행돼야 하는 상태인데, 새 엣지는 source 후 target = 모순)
 *   3. target 부터 BFS 로 descendants 탐색 — source 도달하면 cycle.
 *
 * @returns true = cycle 만듦 (거부), false = 안전
 */
export function wouldAddEdgeCreateCycle(
  plan: Plan,
  source: string,
  target: string,
): boolean {
  // self-loop 즉시 차단.
  if (source === target) return true;

  const childrenMap = buildChildrenMap(plan.todos);

  // target 부터 descendants 탐색 — source 만나면 cycle.
  const visited = new Set<string>();
  const queue: string[] = [target];

  while (queue.length > 0) {
    const cur = queue.shift()!;
    if (visited.has(cur)) continue;
    visited.add(cur);

    const children = childrenMap.get(cur);
    if (!children) continue;

    for (const child of children) {
      if (child === source) return true; // target → ... → source 경로 발견 = cycle.
      queue.push(child);
    }
  }
  return false;
}

/**
 * `child → set(parents)` 가 아니라 `parent → set(children)` 인덱스.
 *
 * PlannedTodo.depends_on = parents (자기를 실행하기 전에 필요한 todo 들).
 * 즉 forward edge: parent → self. self 가 parent 의 child.
 * 본 함수가 만드는 children map: parent_id → {child_ids}.
 */
function buildChildrenMap(todos: readonly PlannedTodo[]): Map<string, Set<string>> {
  const map = new Map<string, Set<string>>();
  for (const todo of todos) {
    for (const parent of todo.depends_on) {
      if (!map.has(parent)) map.set(parent, new Set());
      map.get(parent)!.add(todo.id);
    }
  }
  return map;
}
