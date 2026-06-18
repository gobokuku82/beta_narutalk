# SPACING — 간격 토큰 v1 (2026-06-08)

> Tailwind 의 4px 그리드 + 본 문서의 5 단계 scale 룰.
> spec 64 §3 메타룰 (특히 MR1 임의값 금지) 적용.

## 1. 결정된 5 룰

| # | 룰 | 값 |
|---|---|---|
| **S1** | **4px 그리드 강제** | 모든 spacing 토큰은 4px 배수 (`p-1`=4, `p-2`=8, `p-3`=12 …) |
| **S2** | **half step 금지** | `p-1.5` (6px) · `gap-1.5` 등 4px 위반 토큰 사용 X |
| **S3** | **sub-grid (≤2px) 금지** | `gap-0.5` (2px) · `p-0.5` 등 너무 작은 spacing X |
| **S4** | **5 단계 scale** | xs (4) · sm (8) · md (12) · lg (16) · xl (24) — 본 §2 참조 |
| **S5** | **임의값 금지** | `p-[5px]` · `gap-[10px]` 등 임의값 X (MR1 메타룰) |

## 2. Spacing Scale — 5 단계 (+ 특수)

| 토큰 | px | rem | 빈도 | 의미 |
|---|---|---|---|---|
| `p-1` / `gap-1` | **4** | 0.25 | xs | 미세 (inline icon + label 사이) |
| `p-2` / `gap-2` | **8** | 0.5 | sm | dense 카드 / strip cell padding (가장 빈번) |
| `p-3` / `gap-3` | **12** | 0.75 | md | dense Card 내부 / 작은 영역 padding |
| `p-4` / `gap-4` | **16** | 1.0 | lg | 일반 Card padding (default) |
| `p-6` / `gap-6` / `space-y-6` | **24** | 1.5 | xl | 페이지 root padding · section 간격 |

**특수 (드물게)**:
| 토큰 | px | 사용 |
|---|---|---|
| `p-8` / `gap-8` | 32 | 큰 Hero zone 또는 큰 section break |
| `p-0` / `gap-0` | 0 | reset (e.g. tight nav) |

→ **6 단계 전부 = 4 / 8 / 12 / 16 / 24 / 32**. 4px 그리드 완벽 정렬.

## 3. 폐기 토큰 (S2·S3 위반)

| 폐기 토큰 | 이전 사용 | 대체 |
|---|---|---|
| `p-1.5` · `py-1.5` · `px-1.5` (6px) | 23 + 25 + 8 = **56회** | `p-2` · `py-2` · `px-2` (8px) |
| `gap-1.5` (6px) | **19회** | `gap-2` (8px) |
| `p-0.5` · `py-0.5` (2px) | 10 + 13 = **23회** | `p-1` · `py-1` (4px) |
| `gap-0.5` (2px) | **8회** | `gap-1` (4px) |

→ 4 종 위반 토큰 **106회** 일괄 변환 (2026-06-08, 본 commit).

## 4. 사용 룰 — 어디에 어떤 값

| 위치 | spacing 권장 |
|---|---|
| 페이지 root (`features/*/Page.tsx`) | `p-6` · `space-y-6` (xl) |
| 일반 Card / ChartFrame | `p-4` (lg) |
| dense Card / KpiCard | `p-3` ~ `p-4` (md~lg) |
| Strip cell (DataTable·MemberGuestSummary Cell) | `p-2` · `px-3 py-2` (sm) |
| inline icon + label | `gap-1` ~ `gap-2` (xs~sm) |
| 카드 내부 stack (flex-col) | `gap-3` ~ `gap-4` (md~lg) |
| Track / Section 간격 | `space-y-6` (xl) |
| Hero zone wrapper outer padding | `p-2` (sm — frame 효과) |
| Form field 간격 | `gap-4` ~ `gap-6` (lg~xl) |

## 5. 새 spacing 추가 절차

1. 위치 결정 (페이지/Card/strip/inline 등)
2. §4 표에서 토큰 찾기 — 매칭되면 그대로 사용
3. **half step (1.5) / sub-grid (0.5) / 임의값 사용 금지** (S2·S3·S5)
4. 매칭 안 되면 §2 scale 에 새 단계 추가 (단 4px 배수 강제)
5. 본 문서 §자취 + spec 64 §6 동시 갱신

## 6. 자취

- **2026-06-08** : v1 박제 — 4px 그리드 강제 + 5 단계 scale + half step / sub-grid 폐기
  - 폐기 토큰 106회 일괄 변환:
    - `p-1.5/py-1.5/px-1.5` (56회) → `p-2/py-2/px-2`
    - `gap-1.5` (19회) → `gap-2`
    - `p-0.5/py-0.5` (23회) → `p-1/py-1`
    - `gap-0.5` (8회) → `gap-1`
  - visual 변화: 1~2px (4px 그리드 정렬). 인지 가능하지만 더 정돈된 느낌
