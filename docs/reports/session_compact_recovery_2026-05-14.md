# Compact 복원 가이드 — 2026-05-14 세션

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-05-14 |
| 마지막 커밋 | `b960ffe` feat(frontend): Sprint 2-4 — SideChatPanel query 송신 |
| 세션 범위 | Sprint 14 A3 종결 + Sprint 15 (백엔드 mock API) + **Frontend Sprint 0~2** + ADALLPIN→OctorAD rename |
| 커밋 수 | 24 (e767845 ~ b960ffe) |
| Working tree | clean (`backend/logs/layer_guard.jsonl` 런타임 로그만 — 무시) |
| 다음 작업 | **Frontend Sprint 3** (hitl 라우팅 + Workflow 실 plan 연결 + 분석 페이지 3) |

---

## 0. Compact 이후 첫 행동

```
1. 본 문서 읽고 현 상황 파악 (5분)
2. 사용자에게 "Sprint 3 진입할까요?" 확인 — §6 다음 작업
3. 또는 사용자가 정식 백엔드로 Sprint 1+2 결과 검증 원하면 §7 실행 방법
```

---

## 1. 프로젝트 정체성 (절대 잊지 말 것)

- **프로젝트명**: **OctorAD** (구 ADALLPIN — 2026-05-13 전체 rename, commit `6b9f664`)
- **풀네임**: OctorAD Dream Agent
- **본질**: 4-Layer LangGraph AI 에이전트 (퍼포먼스 마케팅) + n8n 스타일 Workflow Canvas
- **vision** ([`agent_specs/00_vision_and_intent.md`](../agent_specs/00_vision_and_intent.md)): 사용자 ↔ AI 파트너쉽 / 자유 대화 / 학습 / **맞춤형 에이전트** (H0~H4 가설)

---

## 2. 이번 세션 진행 — 3 트랙

### 2.1 트랙 A — Sprint 14 A3 종결 (백엔드, 커밋 4)

| 커밋 | 내용 |
|------|------|
| `e767845` | A3 R-16 NL fatal — Plan adapter (B 옵션 시도) |
| `1e8f319` | **A3 Phase C-Unify — planner.Plan 단일화** (ADR-010 Accepted) — 어댑터 폐기, D 직진 |
| `3105de5` | 문서 cascade (known_issues / test_log / completion_report) |
| `d89f5ec` | 8 사이클 검증 — 12 TC 추가 (Full suite 251 passed) |

→ **ADR-010**: `models.Plan/TodoItem` deprecated, `planner.Plan/PlannedTodo` 단일화.

### 2.2 트랙 B — 60대 Frontend Spec + Sprint 15 백엔드 (커밋 9)

| 커밋 | 내용 |
|------|------|
| `71df3de` | 60대 영역 신설 + 62 Workflow Canvas v1.0 |
| `b19031d` | 60 Frontend Overview v1.0 |
| `5a60d1a` | 61 Architecture + 63 Backend Contract v1.0 |
| `7f0d1e1` | **Frontend Sprint 0 셋업** — frontend/ 디렉터리 + config + 스켈레톤 |
| `a07cee6` | frontend v1 분석 — "대쉬보드 + 채팅창 호출" 3축 검증 |
| `34da8c5` | mock_data_description.md 보강 (KPI/Enum/FK/AI 5축/API 매핑) |
| `77fc4db` | Phase A — spec 60/61/62/63 v1.1 + 66 마이그레이션 맵 신규 |
| `c028163` | **Phase B — 백엔드 Mock Data API 12 endpoint** (`/api/mock/*`) |
| `61b1e1b` | Phase C — v1 GlobalLayout 포팅 (Zustand 4 store) |

### 2.3 트랙 C — Rename + Frontend Sprint 1~2 (커밋 11)

| 커밋 | 내용 |
|------|------|
| `6b9f664` | **ADALLPIN → OctorAD 전체 rename** (28 활성 파일) |
| `c9c95b5` | Sprint 1-A+B — shadcn/ui 16 + TanStack Router 14 라우트 |
| `e186e2d` | Sprint 1-C+E — Mock API hooks 12 + PortfolioPage 실 데이터 |
| `42e2054` | Sprint 1-D — WebSocket 통합 (agent store) |
| `3df0a1c` | fix — mock zod `.optional()` → `.nullish()` (null 허용) |
| `358cbe2` | fix — PortfolioPage KPI "-" (빈 합계 행 처리) |
| `aec0930` | Sprint 2-1 — DashboardPage (KPI + 일별 차트 + 캠페인 표) |
| `8ae8a19` | Sprint 2-2 — ChannelAnalysisPage (막대 차트 + 퍼널) |
| `500b708` | Sprint 2-3 — WorkflowCanvas W1 (React Flow read-only) |
| `b960ffe` | Sprint 2-4 — SideChatPanel query 송신 |

---

## 3. 결정 lock 매트릭스 (사용자 통찰 — 절대 잊지 말 것)

### 3.1 백엔드 결정

| 결정 | 내용 |
|------|------|
| **ADR-010** | `planner.Plan` 단일화. `models.Plan/TodoItem` deprecated |
| **Sprint 14 A3** | 종결 (자동 테스트 251 passed). 브라우저 R-16/17/18 검증만 미완 |

### 3.2 Frontend 결정

| 결정 | 내용 |
|------|------|
| **Layout 패턴** | v1 GlobalLayout (TopBar + Sidebar w-20 + Outlet + SideChatPanel 호출형). 사용자 통찰 "동료 화면 + 채팅 지시" |
| **Tech Stack** | Vite + React 19 + TS strict + Tailwind v3.4 + shadcn/ui + Zustand + TanStack Query + TanStack Router + @xyflow/react + dagre |
| **데이터 source (POC)** | `data/mock/` 12 CSV → 백엔드 `/api/mock/*` 12 endpoint 서빙 |
| **14 라우트** | 포트폴리오 4 + 클라이언트 8 (v1) + 신규 3 (workflow/memory/conversations) |
| **v1→v2** | layout 패턴 채택, 11 페이지 유지, 도구만 마이그레이션 (Redux→Zustand) |

### 3.3 사용자 통찰 박제 (memory)

- `project_extension_ease_priority` — 확장/변경 용이성 우선
- `feedback_no_mixed_codebases` — v1/v2 섞임 금지
- `feedback_test_no_resource_limit` — 테스트 리소스/시간 제약 없이
- `feedback_commit_auto_on_completion` — 단계 완료 시 자동 커밋
- `project_mock_data_as_poc_source` — POC 데이터 = mock CSV → 백엔드 API
- `project_no_user_domain_assumption` — 사용자 도메인 지식 가정 X
- `project_nl_edit_roadmap` — NL 편집 1·2·3차 점진

---

## 4. 핵심 문서 위치 맵

### 4.1 Frontend spec (60대)

| 문서 | 역할 |
|------|------|
| [`agent_specs/60_frontend_overview_v1.0.md`](../agent_specs/60_frontend_overview_v1.0.md) | ⭐ 진입점 — Tech Stack / Vision UX / 7 Sprint Roadmap |
| [`agent_specs/61_frontend_architecture_v1.0.md`](../agent_specs/61_frontend_architecture_v1.0.md) | State (Zustand) / Routing (14) / Component / Design System |
| [`agent_specs/62_workflow_canvas_design_v1.0.md`](../agent_specs/62_workflow_canvas_design_v1.0.md) | Workflow Canvas (React Flow) — W1~W4 |
| [`agent_specs/63_frontend_backend_contract_v1.0.md`](../agent_specs/63_frontend_backend_contract_v1.0.md) | REST/WS/zod 계약 + Mock API 12 endpoint |
| [`agent_specs/66_v1_to_v2_migration_map.md`](../agent_specs/66_v1_to_v2_migration_map.md) | v1 11 페이지 → v2 14 라우트 매핑 + Sprint 우선순위 |

### 4.2 데이터 / 분석

| 문서 | 역할 |
|------|------|
| [`data/mock/mock_data_description.md`](../../data/mock/mock_data_description.md) | 12 CSV — KPI / Enum 14 / FK / AI 5축 / API 매핑 (280줄) |
| [`reports/frontend_v1_analysis_for_v2_layout.md`](./frontend_v1_analysis_for_v2_layout.md) | v1 분석 + 3축 검증 |

### 4.3 백엔드 (Sprint 14 A3)

| 문서 | 역할 |
|------|------|
| [`agent_specs/adr/ADR-010_plan_schema_unification.md`](../agent_specs/adr/ADR-010_plan_schema_unification.md) | planner.Plan 단일화 결정 |
| [`reports/sprint14_a3_completion_report.md`](./sprint14_a3_completion_report.md) | A3 종결 보고서 v1.1 |

---

## 5. Frontend 구조 현황 (frontend/)

### 5.1 작동하는 것

```
frontend/src/
├─ main.tsx                       # RouterProvider + QueryClient + Toaster
├─ routes/
│  ├─ router.tsx                  # 14 라우트 (TanStack Router code-based)
│  └─ RootLayout.tsx              # GlobalLayout + useWebSocket
├─ components/
│  ├─ ui/                         # shadcn/ui 16 primitives
│  └─ layout/
│     ├─ GlobalLayout.tsx         # TopBar + Sidebar + Outlet + SideChatPanel
│     ├─ TopBar.tsx / Sidebar.tsx
│     ├─ PagePlaceholder.tsx / KpiCard.tsx
├─ features/
│  ├─ agent/                      # store / chatPanelStore / SideChatPanel / AgentChatPage
│  ├─ navigation/store.ts         # 컨텍스트 + 14탭
│  ├─ session/store.ts            # conv/turn/connectionStatus
│  ├─ settings/store.ts           # theme
│  ├─ portfolio/PortfolioPage.tsx ✅ 실 데이터 (KPI + 매체별 표)
│  ├─ dashboard/DashboardPage.tsx ✅ 실 데이터 (KPI + 일별 차트 + 캠페인 표)
│  ├─ channel/ChannelAnalysisPage.tsx ✅ 실 데이터 (막대 + 퍼널)
│  ├─ workflow/                   # WorkflowCanvas / NodeComponent / WorkflowPage ✅ W1 (샘플 plan)
│  ├─ trend/ creative/ cost/ hitl/ memory/ conversations/  # placeholder
├─ api/
│  ├─ rest.ts / ws.ts             # WS 2채널 + sendQuery
│  ├─ schemas.ts                  # zod (Plan/Memory/WS/Mock 12 row)
│  ├─ hooks/useMockData.ts        # 12 mock hooks
│  ├─ hooks/useWebSocket.ts       # WS lifecycle
│  └─ errors.ts / errorMessages.ts / queryKeys.ts
├─ lib/cn.ts / dagre.ts / format.ts
└─ styles/globals.css             # 디자인 토큰 (라이트/다크/의미적)
```

### 5.2 검증 상태

- `pnpm typecheck` — 0 errors
- `pnpm build` — 성공 (~850kB / 246kB gzip, Recharts 포함)
- Backend `pytest tests/` — 265 passed + 2 skipped

### 5.3 미완 (placeholder)

- trend / creative / cost / hitl / memory / conversations / settings / report 페이지 = `PagePlaceholder`
- WorkflowCanvas = 샘플 plan (실 plan WS 연결 X)
- SideChatPanel = query 송신 가능 / hitl_request 라우팅 X

---

## 6. 다음 작업 — Frontend Sprint 3

[`66_v1_to_v2_migration_map.md`](../agent_specs/66_v1_to_v2_migration_map.md) §3 Sprint 3:

| # | 작업 | 비고 |
|---|------|------|
| 3-1 | **hitl_request → useHitl store + Plan review modal** | WS hitl 채널 라우팅 |
| 3-2 | **node_event / plan 수신 → WorkflowCanvas 실 plan 연결** | 샘플 plan → 실 plan |
| 3-3 | TrendAnalysisPage 실 데이터 | daily + reviews |
| 3-4 | CreativeAnalysisPage 실 데이터 + AI 5축 radar | creatives + ab-tests |
| 3-5 | CostOptimizationPage 실 데이터 | budget + daily + keywords |

→ 진입 prompt: `session_compact_recovery_2026-05-14.md 읽고 Frontend Sprint 3 진입해. 3-1 hitl 라우팅부터.`

---

## 7. 실행 방법 (사용자 직접)

```powershell
# 터미널 1 — 백엔드 (정식 entry, SelectorEventLoop)
cd C:\kdy\Projects\octormate\beta_v001
uv run python run_server_v2.py
# → "Checkpointer connected + Graph compiled" 뜨면 정상 (port 8001)

# 터미널 2 — 프론트엔드
cd C:\kdy\Projects\octormate\beta_v001\frontend
pnpm dev
# → http://localhost:5173
```

**주의**: 백엔드는 `uvicorn` 직접 X — 반드시 `run_server_v2.py` (Windows ProactorEventLoop 문제).
**종료**: 각 터미널 `Ctrl + C`. 좀비 시 `netstat -ano | findstr :8001` → `Stop-Process -Id <PID> -Force`.

확인 포인트:
- `/portfolio` `/dashboard` `/analysis` — 실 mock 데이터 차트/표
- `/workflow` — React Flow 캔버스 (샘플 5 노드)
- 💬 AI 패널 — "Connected" + query 송신

---

## 8. Compact 이후 prompt 옵션

### 🟢 옵션 A (표준) — 상황 파악 후 결정
```
session_compact_recovery_2026-05-14.md 읽고 현 상황 파악 후 다음 단계 안내해줘.
```

### 🟡 옵션 B — Sprint 3 즉시 진입
```
session_compact_recovery_2026-05-14.md 읽고 Frontend Sprint 3 진입해.
3-1 hitl_request → useHitl store + Plan review modal 부터.
```

### 🟢 옵션 C — 검증 우선
```
session_compact_recovery_2026-05-14.md 읽고, 정식 백엔드 + 프론트 실행 가이드 안내해줘.
Sprint 1+2 결과를 브라우저로 검증하고 싶다.
```

---

## 9. 검증 체크리스트 (Claude 가 본 문서 제대로 읽었는지)

- [ ] 마지막 커밋 = `b960ffe`
- [ ] 프로젝트명 = **OctorAD** (ADALLPIN 아님)
- [ ] 이번 세션 커밋 = 24개
- [ ] Frontend Sprint 0~2 완료 / Sprint 3 다음
- [ ] 데이터 source = mock CSV → `/api/mock/*` 12 endpoint
- [ ] Layout = v1 GlobalLayout 패턴 (TopBar + Sidebar + Outlet + SideChatPanel)
- [ ] 백엔드는 `run_server_v2.py` 로 실행 (uvicorn 직접 X)

**틀린 항목 있으면**: 본 문서 다시 읽고 정확히 보고.

---

## 10. 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-14 | 초안 — 2026-05-14 세션 (24 커밋) compact 준비. Sprint 14 A3 종결 + 60대 spec + Frontend Sprint 0~2 + ADALLPIN→OctorAD rename. 다음 = Frontend Sprint 3 |
