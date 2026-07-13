/**
 * PauseBox — 실행 일시정지 시 채팅창에 표시되는 5 액션 박스.
 *
 * Phase 1 (P1-8) — 디자인 시안 정합:
 *  1. 자연어 textarea ─ "예: 3번 삭제" → ⚡ 적용 (sendTodoEditNl)
 *  2. 🔗 워크플로우에서 수정 (/workflow 라우팅)
 *  3. ▶ 계속 (sendResume)
 *  4. ✕ 취소 (sendCancel)
 *
 * 액션 이벤트는 부모(SideChatPanel) 가 ws.ts 송신을 담당 — 본 컴포넌트는 props 콜백만.
 *
 * spec: 21 v1.4 §3.1 (pause/resume/cancel/todo_edit_nl)
 */
import { useState, type KeyboardEvent } from 'react';
import { Pause, Zap, GitBranch, Play, X } from 'lucide-react';

interface PauseBoxProps {
  turnId: string;
  onResume: () => void;
  onCancel: () => void;
  onOpenWorkflow: () => void;
  onApplyNl: (instruction: string) => void;
}

export function PauseBox({ turnId, onResume, onCancel, onOpenWorkflow, onApplyNl }: PauseBoxProps) {
  const [instruction, setInstruction] = useState('');

  const apply = () => {
    const text = instruction.trim();
    if (!text) return;
    onApplyNl(text);
    setInstruction('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      apply();
    }
  };

  return (
    <div className="rounded-card border border-warning/40 bg-warning/5">
      <div className="px-3 py-2 border-b border-warning/30 flex items-center gap-2">
        <Pause className="h-4 w-4 text-warning" />
        <div>
          <p className="text-sm font-medium text-charcoal">실행 일시정지됨</p>
          <p className="text-xs text-muted-foreground">
            계획 실행을 멈췄습니다. 단계를 수정하거나 계속 진행하세요.
          </p>
        </div>
      </div>

      <div className="px-3 py-2 space-y-2">
        <textarea
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder='자연어로 수정 (예: "3번 삭제", "2번 다음에 리뷰 분석 추가")'
          rows={2}
          className="w-full resize-none rounded-input border border-input bg-background px-2 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <button
          type="button"
          onClick={apply}
          disabled={!instruction.trim()}
          className="w-full flex items-center justify-center gap-2 rounded-button bg-accent-action text-accent-action-foreground px-3 py-2 text-sm font-medium hover:bg-accent-action-deep transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          title="Ctrl/Cmd+Enter"
        >
          <Zap className="h-4 w-4" />
          적용
        </button>
      </div>

      <div className="px-3 py-2 border-t border-warning/30 flex items-center gap-2">
        <button
          type="button"
          onClick={onOpenWorkflow}
          className="flex-1 flex items-center justify-center gap-2 rounded-button border border-input bg-background px-3 py-2 text-sm font-medium hover:bg-muted transition-colors"
          title="워크플로우 캔버스에서 수정"
        >
          <GitBranch className="h-4 w-4" />
          워크플로우에서 수정
        </button>
        <button
          type="button"
          onClick={onResume}
          className="flex items-center justify-center gap-2 rounded-button bg-accent-action text-accent-action-foreground px-3 py-2 text-sm font-medium hover:bg-accent-action-deep transition-colors"
          title="실행 재개"
        >
          <Play className="h-4 w-4" />
          계속
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="flex items-center justify-center gap-2 rounded-button border border-destructive/40 bg-destructive/5 text-destructive px-3 py-2 text-sm font-medium hover:bg-destructive/10 transition-colors"
          title="실행 취소"
        >
          <X className="h-4 w-4" />
          취소
        </button>
      </div>

      <div className="px-3 py-1 text-2xs text-muted-foreground/70 border-t border-warning/20">
        turn_id: <code>{turnId}</code>
      </div>
    </div>
  );
}
