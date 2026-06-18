/**
 * Execution store — 4-Layer 실행 진행 상태.
 *
 * 정적(Plan) + 동적(todo_start/complete + progress) + lifecycle(paused/complete) 결합 view-model.
 * ChatTodoCard / PauseBox / WorkflowPage 가 본 store 의 selector 를 구독한다.
 *
 * spec: 21 v1.4 §2.2 (callback bridge 이벤트) / 30 v1.1 (Plan/PlannedTodo) / 12 v1.3 (Manager)
 */
import { create } from 'zustand';
import type { Plan, PlannedTodo, WSMessage } from '@/api/schemas';

export type TodoRuntimeStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'skipped';

export interface TodoRuntimeInfo {
  status: TodoRuntimeStatus;
  duration_ms?: number;
  is_mock?: boolean;
  summary?: string;
  error?: string;
}

export interface ProgressInfo {
  completed: number;
  total: number;
  percent: number;
  phase?: number;
  phases_total?: number;
}

/** ChatTodoCard / WorkflowPage 가 직접 렌더링하는 결합 뷰. */
export interface TodoView extends PlannedTodo {
  runtime_status: TodoRuntimeStatus;
  duration_ms?: number;
  is_mock?: boolean;
  summary?: string;
  error?: string;
}

interface ExecutionState {
  plan: Plan | null;
  todoRuntime: Record<string, TodoRuntimeInfo>;
  progress: ProgressInfo | null;
  isPaused: boolean;
  isCompleted: boolean;

  setPlan: (plan: Plan) => void;
  setPaused: (paused: boolean) => void;
  finalize: () => void;
  reset: () => void;
  /** 재접속 라이브 재연결 — 백엔드 /state 스냅샷으로 진행 상태 rehydrate (세션연속성 ④). */
  rehydrateFromSnapshot: (snap: {
    plan: Plan | null;
    completedTodoIds: string[];
    progress: { completed: number; total: number } | null;
    paused: boolean;
  }) => void;
  handleWSMessage: (msg: WSMessage) => void;
}

function normalizeStatus(raw: string | undefined): TodoRuntimeStatus {
  switch (raw) {
    case 'completed':
    case 'success':
      return 'completed';
    case 'failed':
    case 'error':
      return 'failed';
    case 'skipped':
      return 'skipped';
    case 'running':
    case 'started':
      return 'running';
    default:
      return 'pending';
  }
}

export const useExecution = create<ExecutionState>((set, get) => ({
  plan: null,
  todoRuntime: {},
  progress: null,
  isPaused: false,
  isCompleted: false,

  setPlan: (plan) => set({ plan, isCompleted: false }),
  setPaused: (paused) => set({ isPaused: paused }),

  finalize: () => set({ isCompleted: true, isPaused: false }),

  reset: () =>
    set({
      plan: null,
      todoRuntime: {},
      progress: null,
      isPaused: false,
      isCompleted: false,
    }),

  rehydrateFromSnapshot: (snap) =>
    set(() => {
      // 완료된 todo 만 'completed' 로 표시 — 나머지는 buildTodoViews 에서 'pending',
      // 이후 도착하는 라이브 todo_start/complete 이벤트가 채워 넣음.
      const todoRuntime: Record<string, TodoRuntimeInfo> = {};
      for (const id of snap.completedTodoIds) todoRuntime[id] = { status: 'completed' };
      const completed = snap.progress?.completed ?? snap.completedTodoIds.length;
      const total = snap.progress?.total ?? snap.plan?.todos.length ?? 0;
      return {
        plan: snap.plan,
        todoRuntime,
        progress:
          total > 0
            ? { completed, total, percent: Math.round((completed / total) * 100) }
            : null,
        isPaused: snap.paused,
        isCompleted: false,
      };
    }),

  handleWSMessage: (msg) => {
    switch (msg.type) {
      case 'node_event': {
        // planning 노드가 emit 한 state 안의 plan = plan 의 *정식 진입점*.
        // 검토 OFF 모드 (interrupt 스킵) 에서는 이게 유일한 진입점.
        // 검토 ON 모드에서는 hitl_request 보다 먼저 도착해 plan 을 set —
        // 이후 오는 hitl_request 의 setPlan 은 동일 plan 이므로 무해 (idempotent).
        if (msg.node === 'planning') {
          const plan = (msg.data as { plan?: unknown }).plan;
          if (plan && !get().plan) {
            set({
              plan: plan as Plan,
              todoRuntime: {},
              progress: null,
              isPaused: false,
              isCompleted: false,
            });
          }
        }
        break;
      }

      case 'hitl_request': {
        // plan_review interrupt — node_event(planning) 가 이미 plan 을 set 했으면 skip.
        // 첫 진입 (node_event 누락 케이스) 에서는 여기서 set.
        const plan = msg.data.plan;
        if (plan && !get().plan) {
          set({
            plan: plan as Plan,
            todoRuntime: {},
            progress: null,
            isPaused: false,
            isCompleted: false,
          });
        }
        break;
      }

      case 'paused':
        set({ isPaused: true });
        break;

      case 'resumed':
        set({ isPaused: false });
        break;

      case 'todo_start': {
        const todoId = msg.data.todo_id;
        if (!todoId) break;
        set((s) => ({
          todoRuntime: {
            ...s.todoRuntime,
            [todoId]: { ...s.todoRuntime[todoId], status: 'running' },
          },
        }));
        break;
      }

      case 'todo_complete': {
        const todoId = msg.data.todo_id;
        if (!todoId) break;
        set((s) => ({
          todoRuntime: {
            ...s.todoRuntime,
            [todoId]: {
              status: normalizeStatus(msg.data.status),
              duration_ms: msg.data.duration_ms,
              is_mock: msg.data.is_mock,
              summary: msg.data.summary,
              error: msg.data.error,
            },
          },
        }));
        break;
      }

      case 'progress': {
        const { completed, total, phase, phases_total } = msg.data;
        const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
        set({ progress: { completed, total, percent, phase, phases_total } });
        break;
      }

      case 'hitl_ack': {
        // 자연어 편집 성공 시 plan 갱신 (P1-6 에서 함께 처리되지만 안전망).
        const ack = msg.data;
        if (ack.accepted && ack.plan) {
          set((s) => ({
            plan: ack.plan as Plan,
            // 편집된 plan 의 todo_id 가 바뀌면 runtime 도 초기화 — 보수적으로 전체 리셋.
            todoRuntime: s.isPaused ? s.todoRuntime : {},
          }));
        }
        break;
      }

      case 'complete': {
        // 최종 plan 이 응답 payload 에 포함될 때 굳히기 (cancel/abort 도 동일).
        const finalPlan = msg.data.plan;
        if (finalPlan) set({ plan: finalPlan as Plan });
        get().finalize();
        break;
      }

      default:
        break;
    }
  },
}));

/**
 * canEdit derive — 편집 가능 여부 (W2).
 *
 * 백엔드 _handle_todo_modify/delete/add 가 `progress.status == "paused"` 시점에만 허용.
 * 프론트는 `useExecution.isPaused === true && turnId 존재` 일 때만 편집 UI 활성.
 *
 * spec: ADR-012 §1.2 / 62 §5.1
 *
 * 사용: `const isPaused = useExecution((s) => s.isPaused);`
 *        `const canEdit = computeCanEdit(isPaused, turnId);`
 */
export function computeCanEdit(isPaused: boolean, turnId: string | null): boolean {
  return isPaused && !!turnId;
}

/**
 * TodoView derive — plan + runtime 결합.
 *
 * 주의: useExecution(selector) 로 호출하면 매번 새 배열을 반환하므로 zustand v5 가
 * 변경됨으로 판단해 무한 re-render 가 발생한다. 컴포넌트에서 `useMemo` 로 derive.
 */
export function buildTodoViews(
  plan: Plan | null,
  todoRuntime: Record<string, TodoRuntimeInfo>,
): TodoView[] {
  if (!plan) return [];
  return plan.todos.map((t) => {
    const rt = todoRuntime[t.id];
    return {
      ...t,
      runtime_status: rt?.status ?? 'pending',
      duration_ms: rt?.duration_ms,
      is_mock: rt?.is_mock,
      summary: rt?.summary,
      error: rt?.error,
    };
  });
}
