# RADIUS — 모서리 토큰 v1 (2026-06-08)

> tailwind.config.ts 의 borderRadius + Tailwind 기본의 5 단계 위계 박제.
> spec 64 §3 메타룰 (MR4 위계 명시) 적용.

## 1. 결정된 4 룰

| # | 룰 | 값 |
|---|---|---|
| **R1** | **5 단계 위계** | `sm` (4) · `md` (6) · `lg` (8) · `xl` (12) · `full` (999) |
| **R2** | **default = `rounded-lg`** | Card 외곽의 표준 (8px) |
| **R3** | **`rounded` (no suffix) 사용 금지** | Tailwind default 4px = `rounded-sm` 과 동일. 명시적 `rounded-sm` 사용 |
| **R4** | **위계 = 위계** | 강조 ↑ = radius ↑ (Hero `xl` > Card `lg` > Card 내부 `md` > Badge `sm`) |

## 2. Scale — 5 단계

| 토큰 | px | Tailwind config | 사용 |
|---|---|---|---|
| `rounded-sm` | **4** | `calc(var(--radius) - 4px)` | Badge · Input · 작은 cell · in-cell bar · code tag |
| `rounded-md` | **6** | `calc(var(--radius) - 2px)` | Card 내부 element · Tooltip · Popover |
| `rounded-lg` | **8** | `var(--radius)` (default) | Card 외곽 (default) · ChartFrame · DataTable wrapper |
| `rounded-xl` | **12** | Tailwind default `0.75rem` | Hero zone wrapper · 강조 카드 |
| `rounded-full` | **999** | `9999px` | Circle · Avatar · status dot · progress bar fill |

→ `--radius` (8px) 가 lg 의 기준. sm/md = -4/-2 derived. xl 은 Tailwind default 12px 직접 사용.

## 3. 폐기 토큰 (R3 위반)

| 폐기 토큰 | 이전 사용 | 대체 |
|---|---|---|
| `rounded` (no suffix, 4px default) | **30회** | `rounded-sm` (4px, 동일 값 — 명시적) |

→ 30회 일괄 변환 (2026-06-08). visual 차이 **0** (동일 4px).

## 4. 사용 룰 — 어디에 어떤 단계

| 위치 | 토큰 |
|---|---|
| Card 외곽 (default) | `rounded-lg` (8px) |
| ChartFrame · DataTable wrapper | `rounded-lg` |
| Card 내부 element (Tooltip · Popover · 작은 sub-card) | `rounded-md` (6px) |
| Hero zone wrapper · 강조 카드 | `rounded-xl` (12px) |
| Badge · Input · 작은 cell · in-cell bar | `rounded-sm` (4px) |
| `<code>` tag · keyboard key 표시 | `rounded-sm` |
| Avatar · status dot · circle button | `rounded-full` |
| Progress bar fill | `rounded-full` |

## 5. 위계 룰 (R4 구체)

```
강조도   |  토큰        |  예시
────────┼─────────────┼─────────────────────
높음    |  rounded-xl  |  Hero zone (MonthlyPage)
중      |  rounded-lg  |  Card 외곽 (default)
낮음    |  rounded-md  |  Tooltip · Popover · 내부 element
미세    |  rounded-sm  |  Badge · Input · 작은 cell
별도    |  rounded-full|  Circle · Avatar
```

→ 같은 페이지에서 강조 영역 = 더 큰 radius. 일관성.

## 6. 새 radius 추가 절차

1. 위치 (Card / Badge / Hero / Tooltip / Circle 등) 결정
2. §4 표에서 토큰 찾기 — 매칭되면 그대로
3. `rounded` (no suffix) **사용 금지** (R3)
4. 임의값 `rounded-[Npx]` **사용 금지** (MR1)
5. 새 단계 필요 시 §2 scale 확장 합의

## 7. 자취

- **2026-06-08** : v1 박제 — 5 단계 위계 + `rounded` (no suffix) 폐기 30회 일괄 변환
  - 폐기: `rounded` (4px default) → `rounded-sm` (4px, 동일 값 명시적)
  - visual 변화: 0 (동일 4px)
  - 영향 파일: KpiCard · ChatTodoCard · AgentObservability · DataFlowLegend · EventTimeline · DataConsole · HitlCenter · PlanReviewModal 등
