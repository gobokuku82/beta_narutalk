/**
 * EventTimeline — 라이브 콜백 스트림(raw WS 이벤트) 타임라인.
 *
 * 사용자 요구 R6 핵심: "사용자에게 보여주기 전까지의 모든 과정(callback)을 다 보고 싶다".
 *  useObsEventLog 의 원본 이벤트를 시각·필터링. (callback = 휘발성이므로 로컬 ring buffer 에 누적)
 *
 * 필터: 현재 턴만 / 노이즈(connected·pong) 숨김. newest-first.
 */
import { useState } from 'react';
import { Trash2 } from 'lucide-react';
import { cn } from '@/lib/cn';
import { Button } from '@/components/ui/button';
import { useObsEventLog, type ObsEvent } from '../store/eventLogStore';

type Category = 'node' | 'exec' | 'hitl' | 'done' | 'error' | 'meta';

function categoryOf(type: ObsEvent['type']): Category {
  switch (type) {
    case 'node_event':
      return 'node';
    case 'layer_start':
    case 'todo_start':
    case 'todo_complete':
    case 'progress':
      return 'exec';
    case 'hitl_request':
    case 'paused':
    case 'resumed':
    case 'hitl_ack':
      return 'hitl';
    case 'complete':
      return 'done';
    case 'error':
      return 'error';
    case 'connected':
    case 'pong':
    default:
      return 'meta';
  }
}

const BADGE: Record<Category, string> = {
  node: 'bg-primary/10 text-primary',
  exec: 'bg-blue-500/10 text-blue-700',
  hitl: 'bg-amber-500/15 text-amber-700',
  done: 'bg-green-500/15 text-green-700',
  error: 'bg-destructive/10 text-destructive',
  meta: 'bg-muted text-muted-foreground',
};

function hhmmss(iso: string): string {
  // 라이브 표시용 — 로캘 시:분:초. (브라우저 코드, new Date OK)
  const d = new Date(iso);
  return d.toLocaleTimeString('ko-KR', { hour12: false });
}

interface EventTimelineProps {
  events: ObsEvent[];
  currentTurnId: string | null;
}

export function EventTimeline({ events, currentTurnId }: EventTimelineProps) {
  const clear = useObsEventLog((s) => s.clear);
  const [onlyCurrentTurn, setOnlyCurrentTurn] = useState(false);
  const [hideNoise, setHideNoise] = useState(true);

  const filtered = events.filter((e) => {
    if (hideNoise && (e.type === 'pong' || e.type === 'connected')) return false;
    if (onlyCurrentTurn && currentTurnId && e.turnId !== currentTurnId) return false;
    return true;
  });
  const ordered = [...filtered].reverse(); // newest-first

  return (
    <div className="flex h-full flex-col rounded-lg border border-border bg-card">
      <div className="flex items-center justify-between gap-2 border-b border-border px-3 py-2">
        <span className="text-sm font-medium">이벤트 타임라인 (callback)</span>
        <div className="flex items-center gap-2 text-xs">
          <label className="flex cursor-pointer items-center gap-1 text-muted-foreground">
            <input
              type="checkbox"
              checked={onlyCurrentTurn}
              onChange={(e) => setOnlyCurrentTurn(e.target.checked)}
            />
            현재 턴
          </label>
          <label className="flex cursor-pointer items-center gap-1 text-muted-foreground">
            <input
              type="checkbox"
              checked={hideNoise}
              onChange={(e) => setHideNoise(e.target.checked)}
            />
            노이즈 숨김
          </label>
          <Button variant="ghost" size="sm" onClick={clear} title="로그 비우기" className="h-7 px-2">
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      <ol className="flex-1 overflow-y-auto p-2 font-mono text-xs">
        {ordered.length === 0 && (
          <li className="px-2 py-6 text-center text-muted-foreground">
            아직 이벤트가 없습니다. 채팅에서 질문을 보내면 콜백이 실시간으로 쌓입니다.
          </li>
        )}
        {ordered.map((e) => {
          const cat = categoryOf(e.type);
          return (
            <li key={e.seq} className="flex items-start gap-2 px-1 py-1 hover:bg-muted/40">
              <span className="shrink-0 tabular-nums text-muted-foreground/70">{hhmmss(e.ts)}</span>
              <span className={cn('shrink-0 rounded-sm px-2 py-1 text-2xs', BADGE[cat])}>
                {e.type}
              </span>
              <span className="min-w-0 flex-1">
                <span className="break-words">{e.label}</span>
                {e.detail && (
                  <span className="ml-1 break-words text-muted-foreground">— {e.detail}</span>
                )}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
