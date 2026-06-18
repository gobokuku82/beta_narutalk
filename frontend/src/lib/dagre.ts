/**
 * dagre 자동 레이아웃 — planner.Plan dict → React Flow nodes/edges + position.
 *
 * spec: 62 §2.2 / 62 §3.1
 * Sprint 2 (W1) 에서 본격 사용.
 */
import dagre from 'dagre';
import type { Node, Edge } from '@xyflow/react';
import type { Plan, PlannedTodo } from '@/api/schemas';

const NODE_WIDTH = 180;
const NODE_HEIGHT = 80;

export type LayoutDirection = 'TB' | 'LR';

export interface LayoutResult {
  nodes: Node[];
  edges: Edge[];
}

/**
 * planner.Plan dict → React Flow nodes/edges. position 이 있으면 사용, 없으면 dagre 자동 계산.
 */
export function planToFlow(plan: Plan, direction: LayoutDirection = 'TB'): LayoutResult {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: direction, nodesep: 40, ranksep: 60 });

  // 노드 등록
  for (const todo of plan.todos) {
    g.setNode(todo.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  }
  // 엣지 등록 (depends_on)
  for (const todo of plan.todos) {
    for (const dep of todo.depends_on) {
      g.setEdge(dep, todo.id);
    }
  }

  dagre.layout(g);

  const nodes: Node[] = plan.todos.map((todo: PlannedTodo) => {
    const layouted = g.node(todo.id);
    const position =
      todo.position ?? { x: layouted.x - NODE_WIDTH / 2, y: layouted.y - NODE_HEIGHT / 2 };
    return {
      id: todo.id,
      type: 'taskNode', // TODO: NodeComponent 등록 후 매핑
      position,
      data: {
        todo,
      },
    };
  });

  const edges: Edge[] = [];
  for (const todo of plan.todos) {
    for (const dep of todo.depends_on) {
      edges.push({
        id: `${dep}->${todo.id}`,
        source: dep,
        target: todo.id,
        type: 'default',
      });
    }
  }

  return { nodes, edges };
}
