# 64. Design System v1.0 — 결정·이유·자취·메타룰

> **단일 상위 spec** for 8 카테고리 디자인 시스템.
> 카테고리별 토큰 표/구체 값 = `frontend/src/styles/*.md` (코드 옆).
> 본 spec = "왜·언제·자취·메타룰". styles/*.md = "무엇·얼마".

| 항목 | 내용 |
|---|---|
| 정체성 | "2026 Warm Neutral + Warm Dusty" — Linear/Vercel 절제 + 따뜻한 베이지 베이스 + 옥스블러드 액센트 1개 |
| 적용 범위 | frontend/src 전체 (모든 페이지·컴포넌트·viz) |
| 단일 진실 | 토큰 값 = styles/*.md / 결정·자취 = 본 spec |
| 연관 spec | 61 §4 (Frontend Architecture Design System 절 → 본 spec 참조) · 62 (Workflow Canvas 의미 토큰) |

## 1. 정체성

| 축 | 결정 | 거부 |
|---|---|---|
| 색 | warm neutral 베이스 (39° 38% 96%) + 옥스블러드 (350°) 액센트 1개 | cool blue/violet base · 다중 액센트 |
| 명도 | hairline 분리 (카드 vs 배경 명도 차 4%p) | 큰 명도 차이 + 그림자 강조 |
| 채도 | dusty (모든 토큰 S ≤ 60%, 대부분 ≤ 42%) | saturated color (≥ 70%) · 형광 |
| 시각 노이즈 | hairline 보더 · 평면 단색 · 절제 motion | 그라데이션 · glow · glassmorphism · 일러스트 |
| 위계 | typography 위계 · 간격 위계 · radius 위계 · color block | shadow blur · 큰 폰트 강조 |
| 타이포 | Pretendard sans + tabular-nums (숫자) | serif 본문 · 손글씨 폰트 |

→ 한 줄: **"자료/리포트 어감, 결재 화면 어플 어감 X"**

## 2. 8 카테고리 spec 위치

| # | 카테고리 | 단일 진실 | 박제 상태 |
|---|---|---|---|
| 1 | **Color** | [`frontend/src/styles/PALETTE.md`](../../frontend/src/styles/PALETTE.md) | ✅ v1 (5 룰 + 효과 11 카테고리, 2026-06-08) |
| 2 | **Typography** | [`frontend/src/styles/TYPOGRAPHY.md`](../../frontend/src/styles/TYPOGRAPHY.md) | ✅ v1 (2026-06-08, 본 turn 신설) |
| 3 | **Spacing** | [`frontend/src/styles/SPACING.md`](../../frontend/src/styles/SPACING.md) | ✅ v1 (2026-06-08, Phase 2) |
| 4 | **Radius** | [`frontend/src/styles/RADIUS.md`](../../frontend/src/styles/RADIUS.md) | ✅ v1 (2026-06-08, Phase 3) |
| 5 | **Motion** | [`frontend/src/styles/MOTION.md`](../../frontend/src/styles/MOTION.md) | ✅ v1 (2026-06-08, Phase 5) |
| 6 | **Elevation** | [`frontend/src/styles/ELEVATION.md`](../../frontend/src/styles/ELEVATION.md) | ✅ v1 (2026-06-08, Phase 6) |
| 7 | **Layout** | [`frontend/src/styles/LAYOUT.md`](../../frontend/src/styles/LAYOUT.md) | ✅ v1 (2026-06-08, Phase 4) |
| 8 | **Enforcement** | [`frontend/scripts/audit-tokens.sh`](../../frontend/scripts/audit-tokens.sh) + `audit-tabs.sh` + `pnpm audit:all` | ✅ v1 (2026-06-08~09, Phase 7) — grep-based, plugin 보류 |
| 9 | **Vocabulary** | [`frontend/src/styles/VOCABULARY.md`](../../frontend/src/styles/VOCABULARY.md) | ✅ v1 (2026-06-10) — 보드/카드 어휘 + hover H1~H4 |

→ 현 박제 = **2/8**. 우선순위 = Audit 보고서 §"권장 우선순위" 참조.

## 3. 메타룰 — 모든 카테고리 공통

| MR | 룰 | 근거 |
|---|---|---|
| **MR1** | **토큰 외 임의값 금지** — `text-[10px]`·`bg-[#abc]`·`p-[5px]` X. Tailwind scale + 디자인 토큰만 | 일관성. 임의값 = spec 우회 = 흔들림 |
| **MR2** | **convention 우선** — 새 값 도입 전 "기존 토큰으로 되나?" 검증 | 메모리 `feedback_convention_over_hardcoding` |
| **MR3** | **변경 시 spec + 코드 동시 갱신** — 한 곳만 바뀌면 drift | PALETTE.md 가 이미 증명 |
| **MR4** | **위계 명시** — 모든 카테고리 토큰에 "강조 위계" (예: spacing 의 dense/normal/loose) | 결정 시 흔들림 ↓ |
| **MR5** | **자취 박제** — 토큰 추가/변경 시 styles/*.md §자취 + 본 spec §6 갱신 | 미래 "왜 이런 결정?" 추적 |
| **MR6** | **다크 모드 변환 룰 명시** — 라이트 → 다크 변환 함수 (PALETTE R5 처럼) | 수동 결정 최소화 |

## 4. Audit & Enforcement (계획)

### 4.1 수동 audit (현재)

- grep 으로 토큰 사용 빈도 + 임의값 사용처 조사 (2026-06-08 1차 audit 완료)
- 결과: 임의값 57건 / spacing 9종 / radius 6종 / page layout 3+종

### 4.2 자동화 (Phase 7, 2026-06-08 + 2026-06-09)

**현재 = `pnpm audit:all` (통합)** — `audit:tokens` + `audit:tabs` 동시 실행.
(`pnpm audit` 은 pnpm 내장 보안 취약점 검사라 별도 — script 명 충돌 회피.)

**`scripts/audit-tokens.sh`** — 디자인 토큰 정합:
```
T1  text-[Npx] 임의값         (TYPOGRAPHY)
S2  half step (1.5)            (SPACING)
S3  sub-grid (0.5)             (SPACING)
R3  rounded (no suffix)         (RADIUS)
E2  shadow-xl/2xl 큰 blur       (ELEVATION)
```

**`scripts/audit-tabs.sh`** (2026-06-09 신설) — Sidebar/Router 구조 정합:
```
[1] store TABS path → router 등록 확인 (orphan tab → 클릭 시 404 검출)
[2] router path → sidebar/settings/index 표시 확인 (orphan route 검출)
[3] ICON_MAP 키 → store TABS 사용 확인 (잔존 import 검출, WARN)
```

→ 페이지 추가/삭제 시 `pnpm audit:all` 한 번이면 정합 자동 검증.

**ESLint plugin 시도 결과** : `eslint-plugin-tailwindcss@3.18.3` 설치 + 설정 → pnpm/Windows 환경에서 `tailwind-api-utils` 의 config resolution 실패 (`Could not resolve tailwindcss`). 설치는 보존, `.eslintrc.cjs` 에서 비활성화. 미래 plugin v4 또는 환경 개선 시 재시도.

**미래** (MVP 후):
- ESLint plugin 재시도 (v4 또는 환경 개선)
- pre-commit hook (husky + lint-staged) 에 `audit:tokens` 통합
- CI 에 audit step 추가
- Storybook + visual regression (큰 작업, MVP 후 검토)

## 5. 변경 절차 (메타)

새 토큰 추가 / 룰 변경 시:

1. **본 spec §3 메타룰 위반 안 하나?** — MR1~MR6 검증
2. **카테고리 결정** — 8 카테고리 중 어디?
3. **styles/*.md §추가 절차 따름** — 카테고리별 절차 (예: PALETTE.md §6)
4. **본 spec §2 박제 상태 갱신**
5. **본 spec §6 자취 갱신**
6. **spec 61 §4 link 표 갱신** (필요 시)

## 6. 자취 — 디자인 시스템 진화

| 시점 | 변경 | commit |
|---|---|---|
| **2026-05-13** | 초기 shadcn 기본값 (회색/blue 위주) | (Sprint 0) |
| **2026-05-14** | "2026 Warm Neutral" — 따뜻한 베이지 + 옥스블러드 액센트 1개 | (메모리 `feedback_no_ai_looking_ui`) |
| **2026-05-22** | A2 — chart-1~5 / channel-* 색 역할 분리 | 통합계획서 §5.4 |
| **2026-06-08 (1)** | Warm Dusty — status/chart 채도 격차 해소 | `9625cea` |
| **2026-06-08 (2)** | PALETTE.md v1 (5 룰 박제) + R1 위반 조정 + 다크 invert | `ac51144` |
| **2026-06-08 (3)** | PALETTE.md §8 효과(Effects) 카테고리 박제 | `c48c7d2` |
| **2026-06-08 (4)** | monthly Hero 효과 적용 (A 단색 영역 + C 타이포) | `2b81b3b` |
| **2026-06-08 (5)** | **Audit 1차** — 8 카테고리 진단, 박제 2/8 확인 | (본 spec 신설) |
| **2026-06-08 (6)** | spec_64 신설 + TYPOGRAPHY.md v1 + 57 임의값 폐기 (Phase 1) | `6c9569f` |
| **2026-06-08 (7)** | SPACING.md v1 + half step/sub-grid 폐기 106 변환 (Phase 2) | `1656a13` |
| **2026-06-08 (8)** | LAYOUT.md v1 (4 패턴) + AgentObs gap-5→6 (Phase 4) | `8698def` |
| **2026-06-08 (9)** | RADIUS.md v1 (5 단계 위계) + `rounded` (no suffix) 폐기 30 변환 (Phase 3) | `47ea419` |
| **2026-06-08 (10)** | MOTION.md v1 + ELEVATION.md v1 (룰만, 코드 변경 X) (Phase 5+6) | `a2b0dab` |
| **2026-06-08 (11)** | Phase 7 Enforcement — `audit:tokens` grep script + Card text-2xl→base + tailwind ts→cjs | `a786c55` |
| **2026-06-09 (12)** | 외부영역 정합 — Sidebar 다크→라이트 + collapsed/expanded + 채팅창 토큰 15건 + 사용자 메시지 strip + Brand 워드마크 (◈ DreamAgent ·) + TopBar 톤다운 | `075ede6` |
| **2026-06-09 (13)** | 페이지 재구성 — 라우트 17→15 (agent/hitl 폐기) + TopBar 라벨 + 5 페이지 이동 + SideChatPanel Maximize2 폐기 | `9a12c7a` + `c6c1bd9` |
| **2026-06-09 (14)** | `audit:tabs` 신설 — Sidebar/Router 정합 자동 검증 + `pnpm audit:all` 통합 | `55f9e0c` |
| **2026-06-10 (15)** | (b)/(c) 라벨 정합 + (d) 계획서 박제 | `acb4739` + `8d78475` |
| **2026-06-10 (16)** | TopBar 에이전트 버튼 Option A (hover dot · 옥스블러드) | `6d7efef` |
| **2026-06-10 (17)** | VOCABULARY.md v1 (보드/카드) + Card·Frame·Strip·DataTable hover state C2 적용 | `8493c7b` |
| **2026-06-10 (18)** | hover 강화 + 에이전트 버튼 hover bg + chatPanelStore partialize 버그 fix | `4cf933e` |
| **2026-06-10 (19)** | nested DataTable wrapper hover 제거 (ring 짤림 fix) + FunnelChart stage hover 추가 + H6 nested 룰 박제 | `34cf19e` |
| **2026-06-10 (20)** | **FunnelChart stage hover 제거 — 외곽 ChartFrame hover 와 누적 회피, 모든 카드 hover 통일** | (본 commit) |

## 7. 후속 phase 로드맵

| Phase | 산출물 | 우선순위 |
|---|---|---|
| ✅ 0 | PALETTE.md v1 + 효과 카테고리 | 완료 |
| ✅ 1 | TYPOGRAPHY.md + 임의값 폐기 | 완료 (`6c9569f`) |
| ✅ 2 | SPACING.md + 4px 그리드 통일 + half step 폐기 | 완료 (`1656a13`) |
| ✅ 3 | **RADIUS.md + 5 단계 위계 + rounded(no suffix) 폐기** | 완료 (본 turn) |
| ✅ 4 | **LAYOUT.md + 18 페이지 패턴 통일 (4 패턴 박제)** | 완료 (본 turn) |
| ✅ 5 | **MOTION.md (duration·easing·transition property 룰)** | 완료 (본 turn) |
| ✅ 6 | **ELEVATION.md (border 위계 + shadow 정책)** | 완료 (본 turn) |
| ✅ 7 | **Enforcement — `audit:tokens` grep script** (ESLint plugin 보류) | 완료 (본 turn) |
