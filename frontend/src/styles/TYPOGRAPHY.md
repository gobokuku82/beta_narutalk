# TYPOGRAPHY — 타이포 토큰 v1 (2026-06-08)

> tailwind.config.ts 의 fontSize/fontWeight 토큰 결정을 박제.
> 새 텍스트 추가/변경 시 본 문서의 룰 통과해야 함.
> spec 64 §3 메타룰 (특히 MR1 임의값 금지) 적용.

## 1. 결정된 5 룰

| # | 룰 | 값 |
|---|---|---|
| **T1** | **임의값 금지** — `text-[Npx]` 사용 X | Tailwind scale + 본 문서 §2 토큰만 |
| **T2** | **font size 위계** | 8 단계 (`text-2xs ~ text-3xl`) — 본 §2 참조 |
| **T3** | **font weight 사용 룰** | `font-medium` (default) · `font-semibold` (강조) · `font-bold` (Hero) — 4단계 |
| **T4** | **숫자 = tabular-nums** | 모든 숫자 (KPI·메트릭·비율·금액) 에 `tabular-nums` 적용 |
| **T5** | **uppercase 라벨** | 메타 라벨(섹션·KPI 라벨) 에 `uppercase tracking-wide` |

## 2. Font Size Scale — 8 단계

| 토큰 | px | rem | 사용처 | line-height |
|---|---|---|---|---|
| `text-2xs` | **10** | 0.625 | 메타 라벨 (uppercase) · MetricChain transition label · 작은 sub | 14px |
| `text-xs` | 12 | 0.75 | 보조 텍스트 · description · footnote (가장 빈번 — 86 회) | 16px |
| `text-sm` | 14 | 0.875 | 본문 · table 셀 · button 텍스트 (두 번째 빈번 — 78 회) | 20px |
| `text-base` | 16 | 1.0 | 카드 title · section title | 24px |
| `text-lg` | 18 | 1.125 | Hero metric · 강조 숫자 | 28px |
| `text-xl` | 20 | 1.25 | KpiCard value (큰 숫자) | 28px |
| `text-2xl` | 24 | 1.5 | Hero title (드물게) | 32px |
| `text-3xl` | 30 | 1.875 | 사용 X (Splash 같은 특수 경우만) | 36px |

**신규 토큰** = `text-2xs` (10px). tailwind.config.ts §2.2 에 박제 — 이전의 `text-[10px]·[11px]·[9px]` 임의값 57건 모두 본 토큰으로 통일 (2026-06-08).

## 3. Font Weight Scale

| 토큰 | weight | 사용 |
|---|---|---|
| `font-normal` | 400 | description · footnote (드물게 — 1 회) |
| `font-medium` | 500 | **default 라벨·메타** (가장 빈번 74 회) |
| `font-semibold` | 600 | 카드/섹션 title · 강조 KPI value (21 회) |
| `font-bold` | 700 | Hero title · 매우 강조 (9 회, 절제 사용) |

→ font-extrabold (800) / font-black (900) 사용 X.

## 4. Line-height

Tailwind 기본 default (위 §2 표). 추가 사용 시:
- `leading-tight` (1.25) — KPI value · 큰 숫자 (조밀)
- `leading-snug` (1.375) — 카드 title
- `leading-normal` (1.5) — 본문 (default)
- `leading-relaxed` (1.625) — 긴 description · "읽는 법" 박스

## 5. 사용 룰 — 어디에 어떤 size

| 위치 | 토큰 |
|---|---|
| Hero metric value | `text-lg` ~ `text-xl` `font-semibold` `tabular-nums` |
| KPI value (KpiCard) | `text-xl` `font-semibold` `tabular-nums leading-tight` |
| Section title (h1) | `text-base` `font-semibold` |
| Card/Frame title | `text-sm` `font-semibold` |
| Table 셀 | `text-sm` `tabular-nums` |
| 메타 라벨 (KPI label·section meta) | `text-2xs` `font-medium uppercase tracking-wide text-muted-foreground` |
| Sub-text (description) | `text-xs` `text-muted-foreground` |
| Delta / 화살표 | `text-2xs` ~ `text-xs` `font-medium` |
| 본문 | `text-sm` |
| Code / 식별자 | `text-xs` `font-mono` (rounded bg-muted px-1.5 py-0.5) |

## 6. 새 텍스트 추가 절차

1. 위치 (Hero / KPI / Card title / 본문 / 메타 등) 결정
2. §5 표에서 토큰 찾기 — 매칭되면 그대로 사용
3. **매칭 안 되는 경우 → §5 표에 새 row 추가** (임의값 X)
4. 새 size 가 필요하면 §2 표에 새 토큰 + tailwind.config.ts 동시 갱신
5. 본 문서 §자취 갱신

## 7. 자취

- **2026-06-08** : v1 박제 — `text-2xs` (10px) 토큰 신설 + 임의값 57건 폐기
  - 이전: `text-[9px]` 3건 / `text-[10px]` 28건 / `text-[11px]` 26건 — 모두 `text-2xs` 로 통일
  - 변경 영향: 11px → 10px 로 1px 작아짐 (사이즈 의도 보존, 정확)
  - 영향 파일 9개: KpiCard · PageHeader · Sidebar · MetricChainStrip · ChannelComparison · FunnelChart · PacingWidget · ChatTodoCard · PauseBox
