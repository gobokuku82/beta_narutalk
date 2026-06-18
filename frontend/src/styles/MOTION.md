# MOTION — 모션 토큰 v1 (2026-06-08)

> Tailwind 의 transition / duration / ease 토큰 + 사용 룰 박제.
> spec 64 §3 메타룰 (MR1 임의값 금지) 적용.
> PALETTE.md §8 효과 F (motion) 와 짝.

## 1. 결정된 4 룰

| # | 룰 | 값 |
|---|---|---|
| **M1** | **duration 3 단계** | `duration-150` (fast) · `duration-200` (default) · `duration-300` (slow) |
| **M2** | **easing 2 단계** | `ease-out` (default — 자연스러운 감속) · `ease-in-out` (bidirectional) |
| **M3** | **`transition-all` 회피** | 명시적 property (`transition-colors`/`transition-opacity`/`transition-transform`) — 성능 + 의도 명확 |
| **M4** | **임의값 금지** | `duration-[450ms]` X. 위 §1·§2 토큰만 |

추가 룰:
- **금지** : `duration-500` 이상 (느림, 답답함) · `ease-bounce`/`elastic` (장식) · `motion-safe`/`motion-reduce` 외 임의 keyframe

## 2. Duration Scale — 3 단계

| 토큰 | ms | 사용 |
|---|---|---|
| `duration-150` | **150** | hover state · color transition · 가장 빈번 (Tailwind default) |
| `duration-200` | **200** | fade-in/out · opacity transition |
| `duration-300` | **300** | modal/sheet 진입·퇴장 · transform |

→ 200ms 가 인지 한계 (사용자가 "즉시" 느끼는 최대). 300ms 까지는 OK, 그 이상 = 답답.

## 3. Easing Scale — 2 단계

| 토큰 | 곡선 | 사용 |
|---|---|---|
| `ease-out` | 빠르게 시작 → 느리게 끝 | **default** — 자연스러운 감속 (등장/hover) |
| `ease-in-out` | 부드러운 양방향 | toggle · 양방향 transition (slide·rotate) |

→ `ease-in` (느리게 시작) 거의 안 씀 — 답답한 인상.

## 4. Transition Property 사용 룰

| 토큰 | 사용처 |
|---|---|
| `transition-colors` | hover (background·text·border 색 변화) — 가장 빈번 (26회) |
| `transition-opacity` | fade-in/out · 진입 motion · skeleton transition |
| `transition-transform` | translate · scale · rotate (Sheet slide 등) |
| `transition` (default = colors+bg+border+text+...) | 일반 — Tailwind default 토큰 사용 |
| ❌ `transition-all` | **회피** — 성능 ↓ + 의도 불명. 명시적 property 사용 |

## 5. 사용 룰 — 어디에 어떤 motion

| 위치 | motion |
|---|---|
| Button / Card hover | `transition-colors duration-150` |
| Tab / Toggle 전환 | `transition-colors duration-150` |
| Sheet / Modal 진입 | `transition-transform duration-300 ease-out` (Radix data-[state] 활용) |
| Tooltip / Popover fade | `transition-opacity duration-200` |
| Chart reveal (recharts) | 기본 활성 (라이브러리 default) — 변경 X |
| Skeleton pulse | `animate-pulse` (Tailwind 기본 1.5s ease-in-out) |
| Loading shimmer | `animate-pulse-soft` (globals.css keyframe 1.5s) |
| Status dot pulse | `animate-pulse` (연결 상태 등) |

## 6. PALETTE.md §8 효과 F 와의 짝

§8.2 F (Motion 절제) 의 구체 룰 = 본 문서 §2~§5.
- "staggered fade-in (50~100ms 차등, 200ms 이내)" = `duration-200 ease-out` + staggered delay
- "chart reveal" = recharts 기본 활성

## 7. 새 motion 추가 절차

1. 위치 (hover · modal · fade · transform 등) 결정
2. §5 표에서 토큰 찾기 — 매칭되면 그대로
3. 매칭 안 되면 §2/§3 scale 안에서 조합 (임의값 X)
4. duration > 300ms 또는 ease-bounce 사용 시 **합의 후 본 문서 §1 확장**
5. 본 문서 §자취 + spec 64 §6 갱신

## 8. 자취

- **2026-06-08** : v1 박제 — 3 단계 duration + 2 단계 easing + transition property 룰
  - 현 사용 audit: transition-colors 26 / transition 16 / transition-opacity 5 / transition-all 4 (회피 대상) / transition-transform 2
  - duration: 150 (default) · 200 · 300 만 허용
  - 본 박제로 `transition-all` 4건은 점진 정리 (성능 + 의도 명확화). 이번 commit 변환 X (작은 회귀 risk, 후속 turn 에 페이지별 검토)
