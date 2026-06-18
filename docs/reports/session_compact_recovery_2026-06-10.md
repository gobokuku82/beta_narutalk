# Session Compact Recovery — 2026-06-10

> 다음 세션 시작 시 컨텍스트 복원용. **간략 프롬프트 + 핵심 박제 위치 + 미해결 이슈** 만.

## 다음 세션 시작 프롬프트 (복사용)

```
이전 세션 진행 박제 = docs/reports/session_compact_recovery_2026-06-10.md
및 docs/reports/audit_tabs_결과_결정후보_가이드_2026-06-10.md.

요약: 디자인 시스템 9/9 카테고리 박제 + 페이지 재구성 (17→15 라우트, agent/hitl 폐기)
+ 외부 영역 정합 (Sidebar 다크→라이트, ◈ OctorAD · 브랜드)
+ 보드/카드 어휘 박제 (VOCABULARY.md) + 카드 hover state (ring + bg-primary/4 + translate)
+ audit:tabs 신설 (pnpm audit:all 통합).

미해결 = (d) NavigationContext type 'portfolio' → 'system' rename (계획서:
docs/reports/d_NavigationContext_type_rename_계획서_2026-06-10.md).

현 미적용 사항 = 큰 카드 (전환 퍼널 등) hover 인지 약 — 사용자 (I) 결정으로 수용.

다음 step 후보: (d) 진행 / (f1) 빈 페이지 / (f2) 데이터/백엔드 / (f3) viz 다듬기
/ (f6) 다크 모드 / (f7) 채널 색 다크. 가이드: docs/reports/audit_tabs_결과_결정후보_가이드_2026-06-10.md §7.
```

## 1. 디자인 시스템 진척 — 9/9 박제 완성

| # | 카테고리 | 단일 진실 |
|---|---|---|
| 1 | Color | `frontend/src/styles/PALETTE.md` |
| 2 | Typography | `frontend/src/styles/TYPOGRAPHY.md` |
| 3 | Spacing | `frontend/src/styles/SPACING.md` |
| 4 | Radius | `frontend/src/styles/RADIUS.md` |
| 5 | Motion | `frontend/src/styles/MOTION.md` |
| 6 | Elevation | `frontend/src/styles/ELEVATION.md` |
| 7 | Layout | `frontend/src/styles/LAYOUT.md` |
| 8 | Enforcement | `frontend/scripts/audit-{tokens,tabs}.sh` + `pnpm audit:all` |
| 9 | Vocabulary | `frontend/src/styles/VOCABULARY.md` (2026-06-10 신설) |

상위 spec = `docs/agent_specs/64_design_system_v1.0.md`.

## 2. 핵심 컨벤션 (자주 사용)

| 어휘 | 정의 |
|---|---|
| **보드** (Board) | 페이지 메인 콘텐츠 영역 (Outlet) |
| **카드** (Card) | 보드 안 개별 단위 (KPI·차트·표) |
| **Hero·Track·Strip·Cell·Frame** | 보조 어휘 (VOCABULARY.md §2) |

| 코드 룰 |
|---|
| 임의값 금지 (`text-[Npx]` X, `pnpm audit:tokens` 검증) |
| spacing 4px 그리드 (half step 금지) |
| `rounded` (no suffix) 금지 — `rounded-sm` 명시 |
| Card hover = `hover:-translate-y-0.5 hover:bg-primary/4 hover:ring-1 hover:ring-primary/40` |
| Nested 카드 hover 미적용 (H6) — 외곽만 강조 |
| Cell hover 미적용 (H5) — dense 영역 |

## 3. 페이지 구조 (2026-06-09 재구성 후)

| 컨텍스트 | 페이지 (15 라우트) |
|---|---|
| 시스템 (6) | portfolio · report · memory · agent-observability · system · db |
| 클라이언트 (8) | dashboard · monthly · channel · trend · creatives · cost · workflow · conversations |
| 공통 (1) | settings |
| 폐기 | ~~agent~~ · ~~hitl~~ (페이지만, hitl/store 보존) |

| TopBar 라벨 | "시스템" ↔ "클라이언트" (type 'portfolio' 그대로) |
| TopBar AI 버튼 | "에이전트" + hover dot 페이드인 |
| Brand | `◈ OctorAD ·` (TopBar 좌측) |

## 4. 미해결 이슈 + 결정 후보

### 미해결 (계획서 박제됨, 적용 대기)

| 항목 | 계획서 |
|---|---|
| **(d) NavigationContext type rename** | `docs/reports/d_NavigationContext_type_rename_계획서_2026-06-10.md` (45분, S1~S6 + R1~R5 검증 매트릭스) |

### 결정 후보 (가이드 박제됨)

`docs/reports/audit_tabs_결과_결정후보_가이드_2026-06-10.md` §7:

| 후보 | 상태 |
|---|---|
| (a) Sidebar default expanded | 사용자 = 안 함 |
| (b) group label | 적용 완료 (관찰→현황, AI→에이전트) |
| (c) /agent-observability 짧은 라벨 | 적용 완료 (에이전트) |
| **(d) type rename** | 계획서 박제, 적용 대기 |
| (e) audit:tabs | 적용 완료 (`pnpm audit:all`) |
| (f1) 빈 페이지 완성 | 후보 — Settings·Workflow·AgentObservability·Memory·Conversations |
| (f2) 데이터/백엔드 (clumi) | 후보 — 큰 작업, POC 본질 |
| (f3) viz/* 다듬기 | 후보 |
| (f6) 다크 모드 토글 | 후보 |
| (f7) 채널 색 다크 오버라이드 | 후보 |

## 5. 알려진 디자인 시스템 한계 (사용자 (I) 수용)

| 현상 | 원인 |
|---|---|
| 큰 카드 (height ≥ 300px) hover 인지 약 (전환 퍼널 등) | `bg-primary/4` 4% opacity + `ring-1` 1px — 큰 카드에서 분산 |
| 카드끼리 hover 색 미세 차이 | 안 콘텐츠 색 (chart fill·muted bg 등) 과 4% tint mix |

→ 결정 (I) = 모든 카드 같은 룰 유지 + 한계 수용.

## 6. 자주 사용하는 명령

```bash
pnpm dev              # vite dev server
pnpm build            # typecheck + vite build
pnpm audit:all        # 디자인 토큰 + Sidebar/Router 정합 검증
pnpm audit:tokens     # 토큰만
pnpm audit:tabs       # 라우트/사이드바만
pnpm test             # vitest
```

## 7. 핵심 commit 자취 (2026-06-08~10)

```
8d78475   (d) 검증 표 갱신
acb4739   (b)/(c) 라벨 + (d) 계획서
6d7efef   TopBar 에이전트 버튼
8493c7b   VOCABULARY v1 + 카드 hover
4cf933e   hover 강화 + 에이전트 hover bg + 패널 버그 fix
34cf19e   nested DataTable hover 제거 + FunnelChart stage hover (이후 제거)
5c09e1e   FunnelChart stage hover 제거 — 외곽 hover 만 통일
55f9e0c   audit:tabs 신설
9a12c7a   페이지 재구성 (17→15, agent/hitl 폐기)
c6c1bd9   hitl 보존 정정
075ede6   외부영역 정합 + Brand 워드마크
a786c55   Phase 7 Enforcement + 종합 점검
```

## 8. 메모리 룰 (자주 참조 — `~/.claude/projects/.../memory/`)

| 룰 | 핵심 |
|---|---|
| `feedback_plan_intent_before_code` | 큰/모호한 작업은 계획서 먼저 |
| `feedback_no_ai_looking_ui` | 그라데이션·glow 금지, 액센트 1개 |
| `feedback_convention_over_hardcoding` | 규칙으로 자동, denylist 추가 전 "규칙으로 되나?" |
| `project_no_user_domain_assumption` | DAG/schema/tool catalog 강요 X |
| `feedback_test_no_resource_limit` | TDD 우선, 단축/skip X |
| `project_tool_data_agent_separation` | tool=순수 / data=Repository / agent 분리 |
