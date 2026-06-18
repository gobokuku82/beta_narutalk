/**
 * SideChatPanel — 우측 호출형 채팅 패널.
 *
 * v1 SideChatPanel.tsx 의 Zustand 포팅 + WebSocket 연동.
 * - 연결 상태 표시 (useSession)
 * - 수신 메시지 / 노드 이벤트 표시 (useAgent)
 * - query 송신 (Sprint 2-4)
 *
 * spec: 61 §2.4 / 63 §3 / §5.1 / 66 §2.1
 */
import { Fragment, useMemo, useState, type KeyboardEvent } from 'react';
import { X, CornerDownLeft, Pause, ShieldCheck, ShieldOff } from 'lucide-react';
import { useNavigate } from '@tanstack/react-router';
import { useChatPanel } from './chatPanelStore';
import { useSession } from '@/features/session/store';
import { useAgent } from './store';
import { useExecution, buildTodoViews } from '@/features/execution/store';
import { ChatTodoCard } from './ChatTodoCard';
import { ChatSkeleton } from './ChatSkeleton';
import { SlideView } from './SlideView';
import { Attachments } from './Attachments';
import { Markdown } from '@/components/Markdown';
import { PauseBox } from './PauseBox';
import { PhaseIndicator, derivePhase } from './PhaseIndicator';
import { UserBubble } from './UserBubble';
import { sendQuery, sendPause, sendResume, sendCancel, sendTodoEditNl } from '@/api/ws';
import { useCurrentClient } from '@/api/clients';
import { cn } from '@/lib/cn';

export function SideChatPanel() {
  const close = useChatPanel((s) => s.close);
  const connectionStatus = useSession((s) => s.connectionStatus);
  const messages = useAgent((s) => s.messages);
  const nodeEvents = useAgent((s) => s.nodeEvents);
  const isRestoring = useAgent((s) => s.isRestoring);

  // zustand v5 — selector 가 새 배열 반환하면 무한 re-render 발생.
  // 원시 슬라이스만 구독하고 useMemo 로 derive.
  const plan = useExecution((s) => s.plan);
  const todoRuntime = useExecution((s) => s.todoRuntime);
  const progress = useExecution((s) => s.progress);
  const isPaused = useExecution((s) => s.isPaused);
  const isCompleted = useExecution((s) => s.isCompleted);
  const todos = useMemo(() => buildTodoViews(plan, todoRuntime), [plan, todoRuntime]);

  // 4-Layer 진행 phase 자연어 표시 — node_event 시퀀스로 derive (turnId 는 아래에서 구독).
  const lastNode = nodeEvents.length > 0 ? (nodeEvents[nodeEvents.length - 1]?.node ?? null) : null;

  const navigate = useNavigate();

  const [input, setInput] = useState('');
  const connected = connectionStatus === 'connected';
  const client = useCurrentClient();   // ⑪.D — ADR-022 helper-B fail-fast 정합 (undefined 시 disabled)
  const turnId = useSession((s) => s.turnId);
  const requireReview = useSession((s) => s.requireReview);
  const setRequireReview = useSession((s) => s.setRequireReview);

  const phase = useMemo(
    () => derivePhase({ turnId, lastNode, hasPlan: !!plan, isCompleted }),
    [turnId, lastNode, plan, isCompleted],
  );
  // 실행 중 = turn 있음 + 완료/일시정지 아님.
  const isRunning = !!turnId && !isCompleted && !isPaused;

  const handleSend = () => {
    const text = input.trim();
    if (!text || !connected || !client) return;   // ⑪.D — client undefined 시 silent return (disabled 가드)
    if (isRunning) return;   // 세션연속성 ② — 실행 중 신규 송신 차단 (동시 turn 방지, 백엔드 concurrency 거부 선제)

    // P1-2 — turn_id 자동 생성 + conversation_id localStorage 영속.
    const { conversationId, turnId } = useSession.getState().startTurn();
    useExecution.getState().reset();
    useAgent.getState().clearTurn();

    useAgent.getState().appendUserMessage(text);
    const ok = sendQuery({
      conversationId,
      turnId,
      userInput: text,
      clientId: client,
      requireReview: useSession.getState().requireReview,
    });
    if (ok) setInput('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="h-full flex flex-col bg-card">
      {/* 헤더 */}
      <header className="h-14 border-b border-border flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center gap-3">
          <h3 className="font-semibold">OctorAD Agent</h3>
          <div className="flex items-center gap-2">
            <span
              className={cn(
                'w-2 h-2 rounded-full',
                connectionStatus === 'connected' && 'bg-success animate-pulse',
                connectionStatus === 'reconnecting' && 'bg-warning',
                connectionStatus === 'closed' && 'bg-gray-400',
              )}
            />
            <span
              className={cn(
                'text-xs font-medium',
                connectionStatus === 'connected' && 'text-success',
                connectionStatus === 'reconnecting' && 'text-warning',
                connectionStatus === 'closed' && 'text-muted-foreground',
              )}
            >
              {connectionStatus === 'connected'
                ? 'Connected'
                : connectionStatus === 'reconnecting'
                ? '재연결 중'
                : '연결 끊김'}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {/* Plan 검토 토글 — On 시 AI 계획을 사용자 승인 후 실행 */}
          <button
            type="button"
            onClick={() => setRequireReview(!requireReview)}
            className={cn(
              'flex items-center gap-1 px-2 py-1 rounded-lg transition-colors text-xs font-medium',
              requireReview
                ? 'bg-success/10 text-success hover:bg-success/15'
                : 'bg-muted text-muted-foreground hover:bg-muted/80',
            )}
            title={
              requireReview
                ? 'Plan 검토 ON — AI 계획을 사용자가 확인 후 실행. 클릭하면 OFF.'
                : 'Plan 검토 OFF — AI 계획을 만들자마자 바로 실행. 클릭하면 ON.'
            }
          >
            {requireReview ? (
              <ShieldCheck className="w-3.5 h-3.5" />
            ) : (
              <ShieldOff className="w-3.5 h-3.5" />
            )}
            <span>검토 {requireReview ? 'ON' : 'OFF'}</span>
          </button>
          <button
            type="button"
            onClick={close}
            className="p-2 hover:bg-muted rounded-lg transition-colors"
            title="닫기"
          >
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
      </header>

      {/* 본문 — 메시지 / 노드 이벤트 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {isRestoring && messages.length === 0 ? (
          // 부팅 복원 중 — 빈 상태 대신 말풍선 스켈레톤(직전 대화 fetch 1~2초). 세션연속성 UX.
          <ChatSkeleton />
        ) : messages.length === 0 && nodeEvents.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            <p className="mb-1 font-medium text-foreground">대화를 시작하세요</p>
            <p className="text-xs">
              {connected
                ? 'AI 에게 무엇이든 물어보세요. Enter 로 송신.'
                : '서버에 연결하는 중...'}
            </p>
          </div>
        ) : null}

        {(() => {
          // 마지막 user 메시지 직후에 ChatTodoCard / PhaseIndicator / PauseBox 인라인 삽입.
          // multi-turn 안전: 이전 turn 의 [user][assistant] 는 그대로, 마지막 turn 만 카드 삽입.
          // 결과 순서: [user][ChatTodoCard 진행→완료][PhaseIndicator][PauseBox][assistant]
          let lastUserIdx = -1;
          for (let i = messages.length - 1; i >= 0; i--) {
            if (messages[i]?.role === 'user') {
              lastUserIdx = i;
              break;
            }
          }
          return messages.map((m, i) => (
            <Fragment key={m.id}>
              {m.role === 'assistant' && m.format === 'ppt' ? (
                // ppt 요청 → 슬라이드 카드 시각화 (Phase3) + 다운로드 칩
                <>
                  <SlideView markdown={m.content} />
                  <Attachments items={m.attachments} />
                </>
              ) : m.role === 'assistant' ? (
                // 그 외 에이전트 응답 → 마크다운 렌더 (근본수정: 날것 `**`/`#` 제거) + 다운로드 칩
                <>
                  <div className="mr-8 rounded-lg bg-muted px-3 py-2 text-sm">
                    <Markdown>{m.content}</Markdown>
                  </div>
                  <Attachments items={m.attachments} />
                </>
              ) : (
                // Active/Static User Bubble (C1 진행바) — VOCABULARY.md §1 / useBubbleProgress hook
                <UserBubble content={m.content} isLastUser={i === lastUserIdx} />
              )}
              {i === lastUserIdx && (
                <>
                  {/* 작업 단계 카드 — todo view-model 결합 표시 (P1-5) */}
                  {todos.length > 0 && (
                    <ChatTodoCard
                      todos={todos}
                      progress={progress ? { completed: progress.completed, total: progress.total } : null}
                      isPaused={isPaused}
                      isCompleted={isCompleted}
                      onOpenWorkflow={() => navigate({ to: '/workflow' })}
                    />
                  )}

                  {/* 진행 phase 자연어 인디케이터 — Plan 등장 전 / response 작성 중 표시 */}
                  <PhaseIndicator phase={phase} />

                  {/* 일시정지 박스 — 5 액션 (P1-8) */}
                  {isPaused && turnId && (
                    <PauseBox
                      turnId={turnId}
                      onResume={() => sendResume(turnId)}
                      onCancel={() => sendCancel(turnId)}
                      onOpenWorkflow={() => navigate({ to: '/workflow' })}
                      onApplyNl={(inst) => sendTodoEditNl(turnId, inst)}
                    />
                  )}
                </>
              )}
            </Fragment>
          ));
        })()}

      </div>

      {/* 입력창 — query 송신 + 실행 중 [⏸ 중지] (P1-7) */}
      <div className="border-t border-border p-3 flex-shrink-0 space-y-2">
        {isRunning && (
          <button
            type="button"
            onClick={() => turnId && sendPause(turnId)}
            className="w-full flex items-center justify-center gap-2 rounded-md border border-input bg-background px-3 py-2 text-sm font-medium hover:bg-muted transition-colors"
            title="실행 일시중단"
          >
            <Pause className="w-4 h-4" />
            중지
          </button>
        )}
        <div className="relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              !connected
                ? '연결 대기 중...'
                : !client
                ? 'client 미선택 — 좌측 상단 드롭다운에서 선택'
                : isRunning
                ? '작업 중… 완료 후 입력할 수 있어요 (중지하려면 위 버튼)'
                : 'AI 에게 무엇이든... (Enter 송신 / Shift+Enter 줄바꿈)'
            }
            disabled={!connected || !client || isRunning}
            className="w-full resize-none rounded-md border border-input bg-background px-3 py-2 pr-10 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            rows={3}
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!connected || !client || !input.trim() || isRunning}
            className="absolute bottom-2 right-2 p-2 rounded-md bg-primary text-primary-foreground hover:opacity-90 transition-opacity disabled:opacity-30 disabled:cursor-not-allowed"
            title="송신 (Enter)"
          >
            <CornerDownLeft className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
