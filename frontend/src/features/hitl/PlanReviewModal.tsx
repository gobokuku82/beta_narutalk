/**
 * PlanReviewModal — hitl_request(plan_review) 수신 시 뜨는 Plan 승인 모달.
 *
 * 백엔드가 Planning 단계에서 사람 검토를 요청하면 pending 이 설정되고
 * 본 모달이 열린다. 승인 → 실행 진행 / 거부 → turn 종료.
 *
 * (2026-06-12 멈춤 수술 ②) D5 자동승인 폐기로 부활 — 검토 ON 의 실주인.
 * pending 은 낙관적으로 지우지 않는다: 서버 hitl_ack(accepted:true)가 지운다(store).
 * accepted:false 면 모달이 유지돼 재시도 가능. 전송 후 ack 까지는 버튼 잠금(sending)
 * — 더블클릭이 재개 Queue 에 잔류 신호를 남기는 것 방지.
 *
 * spec: 62 §3 / 63 §4.2 / 66 §3 (Sprint 3-1)
 * W1: 읽기 전용 검토 + approve/reject. NL 편집은 Sprint 3 후속 / W2.
 */
import { useEffect, useState } from 'react';
import { Check, X } from 'lucide-react';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useHitl } from './store';
import { sendHitlResponse } from '@/api/ws';

export function PlanReviewModal() {
  const pending = useHitl((s) => s.pending);

  const isPlanReview = !!pending?.plan;
  const plan = pending?.plan;

  // 전송 후 ack 대기 잠금. pending 이 바뀌면(ack 처리/새 요청) 해제.
  const [sending, setSending] = useState(false);
  useEffect(() => {
    setSending(false);
  }, [pending]);

  const respond = (action: 'approve' | 'reject') => {
    if (!pending || sending) return;
    const turnId = pending.turn_id;
    if (!turnId) return;
    const ok = sendHitlResponse({
      requestId: pending.request_id,
      turnId,
      action,
    });
    if (!ok) {
      // (멈춤 수술 ④) hitl 채널 순단 — 모달 유지, 사람이 재시도 (재연결은 1초 내 자동)
      toast.error('승인 채널이 연결되지 않았습니다. 잠시 후 다시 시도하세요.');
      return;
    }
    setSending(true);
    toast.message(
      action === 'approve' ? '승인을 전송했습니다 — 실행을 진행합니다.' : '거부를 전송했습니다.',
    );
    // pending clear 는 hitl_ack(accepted:true) 수신 시 store 가 수행 (낙관적 clear 금지).
  };

  return (
    <Dialog
      open={isPlanReview}
      onOpenChange={(open) => {
        // X / ESC / 바깥 클릭으로 닫으면 거부로 간주.
        if (!open && isPlanReview) respond('reject');
      }}
    >
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>실행 계획 검토</DialogTitle>
          <DialogDescription>
            AI 가 아래 계획을 수립했습니다. 승인하면 실행 단계로 진행합니다.
          </DialogDescription>
        </DialogHeader>

        {plan && (
          <div className="space-y-4 max-h-[55vh] overflow-y-auto">
            {plan.teams_selected.length > 0 && (
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-muted-foreground">담당 팀:</span>
                {plan.teams_selected.map((t) => (
                  <Badge key={t} variant="secondary">
                    {t}
                  </Badge>
                ))}
              </div>
            )}

            {plan.plan_notes && (
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                {plan.plan_notes}
              </p>
            )}

            <ol className="space-y-2">
              {plan.todos.map((todo, idx) => (
                <li
                  key={todo.id}
                  className="rounded-input border border-border px-3 py-2 text-sm"
                >
                  <div className="flex items-center gap-2">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-medium">
                      {idx + 1}
                    </span>
                    <span className="font-medium">{todo.task_type}</span>
                    {todo.agent && (
                      <Badge variant="outline" className="text-xs">
                        {todo.agent}
                      </Badge>
                    )}
                    {todo.tool && (
                      <code className="rounded-sm bg-muted px-1 text-xs">{todo.tool}</code>
                    )}
                  </div>
                  {todo.rationale && (
                    <p className="mt-1 pl-7 text-xs text-muted-foreground">
                      {todo.rationale}
                    </p>
                  )}
                  {todo.depends_on.length > 0 && (
                    <p className="mt-1 pl-7 text-xs text-muted-foreground">
                      선행: {todo.depends_on.join(', ')}
                    </p>
                  )}
                </li>
              ))}
            </ol>

            {plan.todos.length === 0 && (
              <p className="text-sm text-muted-foreground">계획에 작업이 없습니다.</p>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" disabled={sending} onClick={() => respond('reject')}>
            <X className="h-4 w-4" />
            거부
          </Button>
          <Button disabled={sending} onClick={() => respond('approve')}>
            <Check className="h-4 w-4" />
            {sending ? '전송 중…' : '승인'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
