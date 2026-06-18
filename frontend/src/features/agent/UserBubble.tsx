/**
 * UserBubble — Active/Static User Bubble (C1 진행바 메시지 박스).
 *
 * 마지막 user 메시지 = Active User Bubble (진행바 오버레이 + 텍스트 stack).
 * 이전 turn 의 user 메시지 = Static User Bubble (액센트만, 진행바 없음, Q6=a 결정).
 *
 * 디자인 시스템 정합:
 *  - PALETTE §8.2 J — 좌측 옥스블러드 액센트 (border-l-2 border-primary) 유지
 *  - MOTION M3 — transition-transform (transition-all 회피, 명시적 property)
 *  - MOTION M1 — duration-200 ease-out (forward fill 표준)
 *  - SPACING 4px grid — 임의값 0
 *  - RADIUS — rounded-md (6px) 유지, fill 은 부모 overflow-hidden 으로 경계 흡수
 *  - TEXT z-10 — 배경 채움이 텍스트 가리지 않게 stack
 *
 * Bubble Fill 색:
 *  - 기본 = bg-primary/15 (12~18% 권장 중앙값, 텍스트 가독성 안전)
 *  - paused = bg-warning/15 (앰버 톤, ChatTodoCard running 칩과 동일)
 *
 * a11y: role="progressbar" + aria-valuenow (sr-only).
 *
 * spec: VOCABULARY.md §1 (Active/Static User Bubble + Bubble Fill).
 */
import { useBubbleProgress } from './useBubbleProgress';
import { cn } from '@/lib/cn';

interface UserBubbleProps {
  content: string;
  isLastUser: boolean;
}

export function UserBubble({ content, isLastUser }: UserBubbleProps) {
  const { percent, state } = useBubbleProgress(isLastUser);

  // showBar = Active User Bubble 의 진행 중 상태 (analyzing ~ responding, paused 포함)
  const showBar = isLastUser && state !== 'idle' && state !== 'completed';

  // state → fill color 매핑 (PALETTE §8.2 J 액센트 톤 유지)
  const fillColor = state === 'paused' ? 'bg-warning/15' : 'bg-primary/15';

  return (
    <div className="relative ml-8 overflow-hidden rounded-md border-l-2 border-primary bg-muted/40 text-sm text-foreground">
      {/* Bubble Fill — absolute 진행 채움. transform scaleX 로 폭 변화 (M3 transition-transform) */}
      {showBar && (
        <div
          aria-hidden="true"
          className={cn(
            'absolute inset-y-0 left-0 w-full origin-left',
            'transition-transform duration-200 ease-out',
            fillColor,
          )}
          style={{ transform: `scaleX(${percent / 100})` }}
        />
      )}
      {/* 텍스트 레이어 — 진행 배경 위 z-10 stack */}
      <div className="relative z-10 whitespace-pre-wrap px-3 py-2">{content}</div>
      {/* a11y — 스크린리더용 진행도 live region (Active 만) */}
      {showBar && (
        <div
          role="progressbar"
          aria-valuenow={percent}
          aria-valuemin={0}
          aria-valuemax={100}
          className="sr-only"
        >
          {state} {percent}%
        </div>
      )}
    </div>
  );
}
