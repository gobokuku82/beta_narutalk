/**
 * MetricChainStrip — KPI 행을 *퍼널 사슬*로 (통합계획서 §5.1 / 원칙 P1·P2).
 *
 * Status: complete — A3 신규 컴포넌트.
 *
 * 점수판(scoreboard) 4칸이 아니라 인과 사슬:
 *   노출 ─(CTR)→ 클릭 ─(CVR)→ 전환 ─(객단가)→ 매출  (÷광고비 = ROAS)
 * 노드(지표) ↔ 전이(전환율·단가)를 교차로 배치 — ROAS 가 떨어졌을 때
 * 어느 고리가 끊겼는지(CTR? CVR? CPC?) 한눈에 추적할 수 있게 한다.
 *
 * P2: 모든 노드·전이에 *목표 대비*(target) 와 *전기간 대비*(delta) 동반 가능.
 * P7: chrome 최소 — Card 래퍼 없이 canvas 에 직접, 노드/전이 사이는 hairline.
 *
 * 사용:
 *   <MetricChainStrip
 *     nodes={[{label:'노출수', value:'524,123', target:{label:'목표 480K', status:'above'}}, ...]}
 *     transitions={[{label:'CTR', value:'3.2%', target:{label:'목표 3.0%', status:'above'}}, ...]}
 *   />
 */
import { Fragment } from 'react';
import { ArrowRight } from 'lucide-react';
import { cn } from '@/lib/cn';

export type TargetStatus = 'above' | 'below' | 'on';

export interface MetricTarget {
  /** 표시 라벨 — 예: "목표 350%" 또는 "ROAS 421%". */
  label: string;
  /** 목표 대비 상태. above=좋음(녹색), below=나쁨(빨강), on=중립. */
  status: TargetStatus;
}

export interface MetricDelta {
  /** 표시값 — 예: "+8.2%". */
  value: string;
  direction: 'up' | 'down';
  /** 등락이 좋은 방향인지 (예: CPA 하락은 good=true 로 뒤집음). */
  good: boolean;
}

export interface MetricChainNode {
  label: string;
  value: string;
  target?: MetricTarget;
  delta?: MetricDelta;
}

export interface MetricChainTransition {
  label: string;
  value: string;
  target?: MetricTarget;
}

interface MetricChainStripProps {
  nodes: MetricChainNode[];
  /** length = nodes.length - 1. 노드 사이를 잇는 전이값. */
  transitions: MetricChainTransition[];
  className?: string;
}

export function MetricChainStrip({
  nodes,
  transitions,
  className,
}: MetricChainStripProps) {
  return (
    <div
      className={cn(
        // VOCABULARY.md §5.1 H1~H4 — Hero strip 외곽 hover (v2 2026-06-10 lift 강화: 2px → 4px)
        'flex items-stretch divide-x divide-border rounded-lg border border-border bg-card transition duration-200 hover:-translate-y-1 hover:bg-primary/4 hover:ring-1 hover:ring-primary/40',
        className,
      )}
    >
      {nodes.map((node, i) => {
        const t = i < nodes.length - 1 ? transitions[i] : undefined;
        return (
          <Fragment key={i}>
            <NodeTile node={node} />
            {t && <TransitionStub transition={t} />}
          </Fragment>
        );
      })}
    </div>
  );
}

function NodeTile({ node }: { node: MetricChainNode }) {
  return (
    // VOCABULARY.md §5.2 H5 v6 — Cell hover (ring-2 inset 만, 굵기 2배)
    <div className="flex-1 min-w-0 px-4 py-3 transition duration-200 hover:ring-2 hover:ring-inset hover:ring-primary/40">
      <p className="text-2xs font-medium uppercase tracking-wide text-muted-foreground">
        {node.label}
      </p>
      <p className="mt-1 text-lg font-semibold tabular-nums text-foreground">
        {node.value}
      </p>
      <div className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-2xs">
        {node.target && <TargetBadge target={node.target} />}
        {node.delta && <DeltaBadge delta={node.delta} />}
      </div>
    </div>
  );
}

function TransitionStub({ transition }: { transition: MetricChainTransition }) {
  return (
    // VOCABULARY.md §5.2 H5 v6 — Cell hover (ring-2 inset, 굵기 2배)
    <div className="flex shrink-0 flex-col items-center justify-center px-3 py-3 text-center transition duration-200 hover:ring-2 hover:ring-inset hover:ring-primary/40">
      <ArrowRight className="h-3 w-3 text-muted-foreground/60" />
      <p className="mt-0.5 text-2xs font-medium uppercase tracking-wide text-muted-foreground">
        {transition.label}
      </p>
      <p className="text-xs font-medium tabular-nums text-foreground">
        {transition.value}
      </p>
      {transition.target && (
        <span className="mt-0.5">
          <TargetBadge target={transition.target} small />
        </span>
      )}
    </div>
  );
}

function TargetBadge({ target, small }: { target: MetricTarget; small?: boolean }) {
  return (
    <span
      className={cn(
        'font-medium',
        small ? 'text-2xs' : 'text-xs',
        target.status === 'above' && 'text-success',
        target.status === 'below' && 'text-destructive',
        target.status === 'on' && 'text-muted-foreground',
      )}
    >
      {target.label}
    </span>
  );
}

function DeltaBadge({ delta }: { delta: MetricDelta }) {
  return (
    <span
      className={cn(
        'font-medium',
        delta.good ? 'text-success' : 'text-destructive',
      )}
    >
      {delta.direction === 'up' ? '↑' : '↓'} {delta.value}
    </span>
  );
}
