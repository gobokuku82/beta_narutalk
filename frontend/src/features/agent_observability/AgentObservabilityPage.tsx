/**
 * AgentObservabilityPage — 에이전트 작동 관찰 대시보드 (Phase 1, 백엔드 0).
 *
 * 본질(계획서 §4.5): 빌더용 "정합성·아키텍처 검증 콘솔" — 사용자 질문이 응답으로 바뀌기까지의
 *  4-레이어 흐름 · 워크플로우(todo+DAG) 생성 · 모든 callback · 중간 산출물 · 데이터 전달 구조를 관찰.
 *
 * 격리(계획서 §7.5): 모든 신규 코드는 features/agent_observability/ 안에만. 공유 스토어는 읽기 전용.
 *  기존 지표페이지 + AI 채팅(SideChatPanel) 구조와 공존 — 채팅은 우상단 버튼으로 호출.
 *
 * 계획서: docs/_claude/dashboard/agent_observability_dashboard_plan_260605_v1.md
 */
import { Activity, MessageSquare } from 'lucide-react';
import { useNavigate } from '@tanstack/react-router';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/cn';
import { PhaseIndicator } from '@/features/agent/PhaseIndicator';
import { ChatTodoCard } from '@/features/agent/ChatTodoCard';
import { useChatPanel } from '@/features/agent/chatPanelStore';
import { useAgentObservability } from './hooks/useAgentObservability';
import { PipelineLanes } from './components/PipelineLanes';
import { FlowCanvasPanel } from './components/FlowCanvasPanel';
import { EventTimeline } from './components/EventTimeline';
import { ArtifactInspector } from './components/ArtifactInspector';
import { DataFlowLegend } from './components/DataFlowLegend';

const CONN_DOT: Record<'connected' | 'reconnecting' | 'closed', string> = {
  connected: 'bg-green-500',
  reconnecting: 'bg-amber-500 animate-pulse',
  closed: 'bg-muted-foreground/40',
};

const CONN_TEXT: Record<'connected' | 'reconnecting' | 'closed', string> = {
  connected: '연결됨',
  reconnecting: '재연결 중',
  closed: '연결 끊김',
};

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
      {children}
    </h2>
  );
}

export function AgentObservabilityPage() {
  const navigate = useNavigate();
  const openChat = useChatPanel((s) => s.open);
  const obs = useAgentObservability();

  const {
    turnId,
    connectionStatus,
    plan,
    hasPlan,
    todos,
    progress,
    isPaused,
    isCompleted,
    nodeEvents,
    events,
    phase,
    artifacts,
    counts,
  } = obs;

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-6">
      <PageHeader
        title="에이전트 관찰"
        description="질문 → 응답까지의 4-레이어 흐름 · 워크플로우 생성 · 콜백 · 중간 산출물을 실시간 관찰"
        icon={Activity}
        badge="Phase 1 · 읽기 전용"
        actions={
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className={cn('h-2 w-2 rounded-full', CONN_DOT[connectionStatus])} aria-hidden />
              {CONN_TEXT[connectionStatus]}
            </span>
            <Button variant="outline" size="sm" onClick={() => openChat()}>
              <MessageSquare className="h-4 w-4" />
              채팅 열기
            </Button>
          </div>
        }
      />

      {/* 현재 턴 요약 strip */}
      <section className="flex flex-wrap items-center gap-3 rounded-lg border border-border bg-card px-3 py-2.5">
        <span className="text-xs text-muted-foreground">
          현재 turn:{' '}
          <code className="rounded-sm bg-muted px-1 text-foreground">{turnId ?? '—'}</code>
        </span>
        <span className="text-xs tabular-nums text-muted-foreground">
          작업 {counts.completed}/{counts.total}
          {counts.running > 0 && ` · 실행중 ${counts.running}`}
          {counts.failed > 0 && (
            <span className="text-destructive"> · 실패 {counts.failed}</span>
          )}
        </span>
        {progress && (
          <span className="text-xs tabular-nums text-muted-foreground">
            진행률 {progress.percent}%
            {progress.phase != null && ` · phase ${progress.phase}/${progress.phases_total ?? '?'}`}
          </span>
        )}
        <div className="ml-auto">
          {phase ? (
            <PhaseIndicator phase={phase} />
          ) : isCompleted ? (
            <span className="rounded-full bg-green-500/15 px-2.5 py-1 text-xs text-green-700">
              응답 완료
            </span>
          ) : (
            <span className="rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground">
              대기 중
            </span>
          )}
        </div>
      </section>

      {/* ① 파이프라인 레인 */}
      <section className="flex flex-col gap-2">
        <SectionTitle>① 4-레이어 파이프라인</SectionTitle>
        <PipelineLanes
          nodeEvents={nodeEvents}
          turnId={turnId}
          isCompleted={isCompleted}
          progress={progress}
        />
      </section>

      {/* ②③ DAG + 콜백 타임라인 */}
      <section className="grid gap-4 lg:grid-cols-2">
        <div className="flex flex-col gap-2">
          <SectionTitle>② 워크플로우 흐름 (DAG)</SectionTitle>
          <FlowCanvasPanel plan={plan} />
        </div>
        <div className="flex flex-col gap-2">
          <SectionTitle>③ 콜백 스트림</SectionTitle>
          <div className="h-[420px]">
            <EventTimeline events={events} currentTurnId={turnId} />
          </div>
        </div>
      </section>

      {/* ④⑥ 작업 진행 + 중간 산출물 */}
      <section className="grid gap-4 lg:grid-cols-2">
        <div className="flex flex-col gap-2">
          <SectionTitle>④ 작업 진행 (todo)</SectionTitle>
          {hasPlan ? (
            <ChatTodoCard
              todos={todos}
              progress={progress}
              isPaused={isPaused}
              isCompleted={isCompleted}
              onOpenWorkflow={() => navigate({ to: '/workflow' })}
            />
          ) : (
            <div className="rounded-lg border border-border bg-card px-3 py-6 text-center text-sm text-muted-foreground">
              아직 계획이 없습니다.
            </div>
          )}
        </div>
        <div className="flex flex-col gap-2">
          <SectionTitle>⑥ 중간 산출물 (레이어 경계)</SectionTitle>
          <div className="h-[360px]">
            <ArtifactInspector artifacts={artifacts} />
          </div>
        </div>
      </section>

      {/* ⑤ 데이터 전달 구조 */}
      <section className="flex flex-col gap-2">
        <SectionTitle>⑤ 데이터 전달 (State / Context / Class)</SectionTitle>
        <DataFlowLegend />
      </section>

      <footer className="pb-4 pt-1 text-center text-xs text-muted-foreground/70">
        Phase 1 — 라이브 단일-턴 관찰 (백엔드 변경 0). 레이어별 타이밍 · 데이터 lineage · 과거 재생은
        계측(Phase 2~3) 후 추가됩니다.
      </footer>
    </div>
  );
}
