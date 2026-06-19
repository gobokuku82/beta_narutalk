/**
 * WelcomeHero — 첫 진입 강조 섹션 (Welcome Hero).
 *
 * 차분한 결 (Apple/Stripe 결). 좌측 옥스블러드 strip (PALETTE §8.2 J) 한 군데만.
 * 모노 라벨 + 큰 한국어 sans 제목 + 부제 + 슬로건.
 *
 * spec: VOCABULARY §2 Welcome Hero (v12 재신설).
 */
export function WelcomeHero() {
  return (
    <section className="flex flex-col gap-3 border-l-2 border-primary py-3 pl-6">
      <p className="font-mono text-2xs uppercase tracking-wider text-muted-foreground">
        Agent · Framework
      </p>
      <h1 className="text-3xl font-bold tracking-tight text-foreground md:text-4xl">
        DreamAgent
      </h1>
      <p className="text-lg font-semibold text-foreground md:text-xl">
        4-Layer 에이전트 프레임워크
      </p>
      <p className="text-sm leading-relaxed text-muted-foreground md:text-base">
        자연어로 묻고, 워크플로우로 실행한다.
      </p>
    </section>
  );
}
