# ELEVATION — 깊이 토큰 v1 (2026-06-08)

> border 위계 + shadow 정책 박제.
> spec 64 §1 정체성 ("그라데이션·glow 금지, hairline 보더") + PALETTE.md §8.1 (그라데이션·glow 금지 이유) 와 짝.

## 1. 결정된 4 룰

| # | 룰 | 값 |
|---|---|---|
| **E1** | **border 위계 우선** | 깊이 표현은 border 가 default. shadow 는 overlay (popover) 한정 |
| **E2** | **shadow blur 강한 효과 금지** | drop-shadow blur · glow · neon · glassmorphism X |
| **E3** | **shadow scale** | Card subtle (1px·0.06) · Tooltip/Popover/Dropdown (sm/md) · Modal (lg) |
| **E4** | **임의 shadow 금지** | `shadow-[arbitrary]` 사용 시 본 문서 §3 정당화 후만 |

## 2. Border 위계 — default

| 단계 | 토큰 | 사용 |
|---|---|---|
| **hairline** (default) | `border border-border` (1px) | 모든 카드 외곽 · 표 행 구분 · divider |
| **강조** | `border-2 border-border` (2px) | 강조 카드 · 선택된 항목 |
| **액센트** | `border border-primary/30` ~ `border-2 border-primary/30` | 강조 영역 외곽 (Hero zone 등) |
| **divider** | `divide-x divide-border` / `divide-y divide-border` | strip cell 사이 · 표 행 사이 |

→ 카드 분리 = **border + bg 명도 차** 만으로 (shadow 없이).

## 3. Shadow 정책 — 보수적 허용

`feedback_no_ai_looking_ui` 메모리 룰 = "그라데이션·glow 금지". shadow blur 강한 효과 = glow 어감 → 금지.
**예외**: 미세 분리 효과 (≤2px blur, ≤0.1 opacity) 와 overlay 의 자연스러운 깊이 표현 허용.

| 토큰 | blur · opacity | 허용 범위 |
|---|---|---|
| `shadow-sm` (Card 미세) | 1px blur, 0.05 opacity | Card 외곽 분리 (warm beige 배경과의 미세 차이) |
| `shadow-md` | 4px blur, 0.1 opacity | **Tooltip · Popover · Dropdown** (overlay) |
| `shadow-lg` | 10px blur, 0.1 opacity | **Modal · Sheet** (overlay) |
| `shadow-[0_1px_2px_0_rgb(41_37_36_/_0.06)]` (Card custom) | 1px blur, 0.06 opacity | Card subtle — 현 sticky token. shadow-sm 으로 단순화 후보 (§5) |
| ❌ `shadow-xl` / `shadow-2xl` (≥20px blur) | 큰 blur | **금지** — glow 어감 |
| ❌ drop-shadow blur / glow | — | **금지** |
| ❌ glassmorphism (backdrop-blur) | — | **금지** |

## 4. 사용 룰 — 어디에 어떤 elevation

| 위치 | elevation |
|---|---|
| Card 외곽 (default) | `border border-border` + `shadow-sm` (또는 custom subtle) |
| ChartFrame · DataTable wrapper | `border border-border` (shadow 없음) |
| Tooltip / Popover (overlay) | `border border-border` + `shadow-md` |
| Dropdown / Select Content | `border border-border` + `shadow-md` |
| Modal / Sheet / Dialog | `border border-border` + `shadow-lg` |
| 강조 카드 / Hero zone | `border-2 border-border` or `bg-accent/50` (color block) |
| Section divider | `border-b border-border` (1px hairline) |
| Strip cell 사이 | `divide-x divide-border` |

## 5. 현 Card custom shadow 정책

`src/components/ui/card.tsx` 의 `shadow-[0_1px_2px_0_rgb(41_37_36_/_0.06)]` (1건) — Card 의 미세 분리.

| 옵션 | 의미 |
|---|---|
| **A. 유지 (현 상태)** | warm beige 위에 카드를 살짝 띄움. 명시적 RGB (foreground 색 톤) |
| B. `shadow-sm` 으로 단순화 | Tailwind 토큰 일관성, 단 색이 다름 (검정 base) |
| C. 폐기 (border only) | hairline border + bg-card 명도 차 (96 vs 100) 만으로 분리 |

→ **현재 A 유지**. warm neutral 베이스라 검정 base shadow-sm 보다 warm RGB shadow 가 정합. 본 문서 §3 표 의 예외 항목.

**미래** (Phase 7 Enforcement 시): `--shadow-card` CSS variable 로 토큰화 + tailwind config 에 등록 → `shadow-card` 토큰. 임의값 0.

## 6. 새 elevation 추가 절차

1. 위치 (Card · overlay · 강조 등) 결정
2. §4 표에서 토큰 찾기 — 매칭되면 그대로
3. blur > 10px 또는 opacity > 0.15 사용 시 **합의 후 본 문서 §3 확장**
4. drop-shadow / glow / glassmorphism 사용 X (E2 룰)
5. 임의 shadow 사용 시 §3 의 정당화 (overlay 등) 와 함께 본 문서 §3 표에 row 추가

## 7. 자취

- **2026-06-08** : v1 박제 — border 위계 default + shadow 보수적 허용 정책
  - 현 사용 audit: shadow-sm 7 / shadow-md 4 / shadow-lg 4 / shadow 4 / Card custom 1
  - 결정: Card custom shadow A 유지 (warm-tinted, 명시적 RGB), 미래 `--shadow-card` 변수화 후보
