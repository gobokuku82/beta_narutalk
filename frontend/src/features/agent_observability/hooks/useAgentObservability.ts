/**
 * useAgentObservability — 관찰 대시보드용 파생 상태 합성 hook.
 *
 * 격리 원칙 (계획서 §7.5): 공유 스토어는 *읽기 전용*으로만 구독.
 *  대시보드 전용 상태(eventLog)는 로컬 store. 파생값은 본 hook 의 useMemo.
 *
 * 백엔드 변경 0 — 이미 전역 fanout(RootLayout useWebSocket)으로 채워진 스토어를 합성만.
 */
import { useMemo } from 'react';
import type { Plan } from '@/api/schemas';
import { useExecution, buildTodoViews, type TodoView } from '@/features/execution/store';
import { useAgent, type NodeEventRecord } from '@/features/agent/store';
import { useSession } from '@/features/session/store';
import { derivePhase, type AgentPhase } from '@/features/agent/PhaseIndicator';
import { useObsEventLog, type ObsEvent } from '../store/eventLogStore';

export interface ObsArtifacts {
  structured_query: unknown;
  plan: unknown;
  execution_result: unknown;
  response: unknown;
}

export interface ObsCounts {
  total: number;
  completed: number;
  failed: number;
  running: number;
}

export interface AgentObservability {
  turnId: string | null;
  connectionStatus: 'connected' | 'reconnecting' | 'closed';
  plan: Plan | null;
  hasPlan: boolean;
  todos: TodoView[];
  progress: { completed: number; total: number; percent: number; phase?: number; phases_total?: number } | null;
  isPaused: boolean;
  isCompleted: boolean;
  nodeEvents: NodeEventRecord[];
  events: ObsEvent[];
  lastNode: string | null;
  phase: AgentPhase;
  artifacts: ObsArtifacts;
  counts: ObsCounts;
}

export function useAgentObservability(): AgentObservability {
  const turnId = useSession((s) => s.turnId);
  const connectionStatus = useSession((s) => s.connectionStatus);

  const plan = useExecution((s) => s.plan);
  const todoRuntime = useExecution((s) => s.todoRuntime);
  const progress = useExecution((s) => s.progress);
  const isPaused = useExecution((s) => s.isPaused);
  const isCompleted = useExecution((s) => s.isCompleted);

  const nodeEvents = useAgent((s) => s.nodeEvents);
  const events = useObsEventLog((s) => s.events);

  const todos = useMemo(() => buildTodoViews(plan, todoRuntime), [plan, todoRuntime]);

  const lastNode =
    nodeEvents.length > 0 ? (nodeEvents[nodeEvents.length - 1]?.node ?? null) : null;

  const phase: AgentPhase = derivePhase({
    turnId,
    lastNode,
    hasPlan: !!plan,
    isCompleted,
  });

  const artifacts = useMemo<ObsArtifacts>(() => {
    const pick = (node: string, key: string): unknown => {
      for (let i = nodeEvents.length - 1; i >= 0; i--) {
        const e = nodeEvents[i];
        if (e && e.node === node && key in e.data) return e.data[key];
      }
      return undefined;
    };
    return {
      structured_query: pick('cognitive', 'structured_query'),
      plan: pick('planning', 'plan'),
      execution_result: pick('execution', 'execution_result'),
      response: pick('response', 'response'),
    };
  }, [nodeEvents]);

  const counts = useMemo<ObsCounts>(() => {
    let completed = 0;
    let failed = 0;
    let running = 0;
    for (const t of todos) {
      if (t.runtime_status === 'completed') completed += 1;
      else if (t.runtime_status === 'failed') failed += 1;
      else if (t.runtime_status === 'running') running += 1;
    }
    return { total: todos.length, completed, failed, running };
  }, [todos]);

  return {
    turnId,
    connectionStatus,
    plan,
    hasPlan: !!plan,
    todos,
    progress,
    isPaused,
    isCompleted,
    nodeEvents,
    events,
    lastNode,
    phase,
    artifacts,
    counts,
  };
}
