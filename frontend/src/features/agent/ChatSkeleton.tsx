/**
 * ChatSkeleton — 부팅 대화 복원 중 표시 (세션연속성 UX).
 *
 * 직전 대화 fetch(1~2초) 동안 채팅 말풍선 모양 placeholder 를 보여줘
 * "빈 것처럼" 보이던 오해를 막음. 메시지가 들어오면 SideChatPanel 이 교체.
 * 디자인시스템: animate-pulse(투명도 펄스)만 — 움직이는 그라데이션/glow 금지, bg-muted.
 */
export function ChatSkeleton() {
  return (
    <div className="space-y-3" role="status" aria-label="이전 대화를 불러오는 중">
      {/* user 말풍선 (우측, 좁음) */}
      <div className="flex justify-end">
        <div className="h-9 w-2/5 animate-pulse rounded-card bg-muted" />
      </div>
      {/* assistant 말풍선 (좌측, 여러 줄) */}
      <div className="mr-8 space-y-2 rounded-panel bg-muted/40 px-3 py-2">
        <div className="h-3.5 w-3/4 animate-pulse rounded-control bg-muted" />
        <div className="h-3.5 w-full animate-pulse rounded-control bg-muted" />
        <div className="h-3.5 w-1/2 animate-pulse rounded-control bg-muted" />
      </div>
      {/* 한 쌍 더 — 패널을 적당히 채워 로딩감 전달 */}
      <div className="flex justify-end">
        <div className="h-9 w-1/3 animate-pulse rounded-card bg-muted" />
      </div>
      <div className="mr-8 space-y-2 rounded-panel bg-muted/40 px-3 py-2">
        <div className="h-3.5 w-2/3 animate-pulse rounded-control bg-muted" />
        <div className="h-3.5 w-5/6 animate-pulse rounded-control bg-muted" />
      </div>
    </div>
  );
}
