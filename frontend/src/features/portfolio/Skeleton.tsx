/** 표 로딩용 스켈레톤. */
export function Skeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-8 w-full animate-pulse rounded-sm bg-muted" />
      ))}
    </div>
  );
}
