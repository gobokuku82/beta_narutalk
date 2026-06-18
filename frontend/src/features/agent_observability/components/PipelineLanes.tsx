/**
 * PipelineLanes — 4-Layer 파이프라인(Cognitive→Planning→Execution→Response) 진행 레인.
 *
 * derive 규칙: node_event 는 노드 *완료* 시 emit → seen 에 들어온 레이어 = done.
 *  turn 진행 중이고 미완료면 첫 unseen 레이어 = active. 그 외 pending.
 * 백엔드 변경 0 — 기존 emit 시퀀스만 보고 상태 도출 (PhaseIndicator 와 동일 원리).
 */
import { cn } from '@/lib/cn';
import type { NodeEventRecord } from '@/features/agent/store';

type LaneStatus = 'done' | 'active' | 'pending';

const ORDER = ['cognitive', 'planning', 'execution', 'response'] as const;

const LANE_LABEL: Record<(typeof ORDER)[number], { ko: string; sub: string }> = {
  cognitive: { ko: '인지', sub: '질문 해석 → structured_query' },
  planning: { ko: '계획', sub: '워크플로우 생성 (todo + DAG)' },
  execution: { ko: '실행', sub: '도구 호출 → execution_result' },
  response: { ko: '응답', sub: '결과 작성 → response' },
};

interface PipelineLanesProps {
  nodeEvents: NodeEventRecord[];
  turnId: string | null;
  isCompleted: boolean;
  progress: { completed: number; total: number; phase?: number; phases_total?: number } | null;
}

const DOT: Record<LaneStatus, string> = {
  done: 'bg-primary',
  active: 'bg-blue-500 animate-pulse',
  pending: 'bg-muted-foreground/30',
};

const CARD: Record<LaneStatus, string> = {
  done: 'border-primary/40 bg-primary/5',
  active: 'border-blue-500/50 bg-blue-500/5',
  pending: 'border-border bg-card',
};

export function PipelineLanes({ nodeEvents, turnId, isCompleted, progress }: PipelineLanesProps) {
  const seen = new Set(nodeEvents.map((e) => e.node));
  let activeAssigned = false;

  const lanes = ORDER.map((node) => {
    let status: LaneStatus;
    if (seen.has(node)) {
      status = 'done';
    } else if (turnId && !isCompleted && !activeAssigned) {
      status = 'active';
      activeAssigned = true;
    } else {
      status = 'pending';
    }
    return { node, status };
  });

  return (
    <div className="flex items-stretch gap-1">
      {lanes.map(({ node, status }, i) => {
        const label = LANE_LABEL[node];
        const showProgress = node === 'execution' && status === 'active' && progress;
        return (
          <div key={node} className="flex flex-1 items-stretch gap-1">
            <div className={cn('flex-1 rounded-lg border px-3 py-2.5 transition-colors', CARD[status])}>
              <div className="flex items-center gap-2">
                <span className={cn('h-2 w-2 shrink-0 rounded-full', DOT[status])} aria-hidden />
                <span className="text-sm font-semibold">{label.ko}</span>
                {status === 'done' && (
                  <span className="ml-auto text-xs text-primary">완료</span>
                )}
                {status === 'active' && (
                  <span className="ml-auto text-xs text-blue-600">진행 중</span>
                )}
              </div>
              <p className="mt-1 truncate text-xs text-muted-foreground">{label.sub}</p>
              {showProgress && progress && (
                <p className="mt-1 text-xs tabular-nums text-blue-600">
                  {progress.completed}/{progress.total}
                  {progress.phase != null && ` · phase ${progress.phase}/${progress.phases_total ?? '?'}`}
                </p>
              )}
            </div>
            {i < lanes.length - 1 && (
              <div className="flex items-center text-muted-foreground/50" aria-hidden>
                →
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
