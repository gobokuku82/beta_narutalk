# Compact 복원 가이드 — 2026-05-15 세션

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-05-15 |
| 현재 브랜치 | **`main`** — 프론트 코드 = `a5c4fc3` 그대로 (Phase 1 미시작). 이후 다수 커밋 (정리 + 문서) |
| 세션 범위 | modoo 데모 완성 → main 복귀 → 통합 진단 → 트랙 1 검증 → models/ cleanup → agent_specs 정리 → **통합 설계 점검 + Phase 1 계획서** |
| 다음 최우선 | ~~트랙 1~~ ✅ → ~~정리~~ ✅ → **Phase 1 P1-1 부터 atomic 실행** (10 단계, 계획서 = `_claude/integration_phase1_implementation_plan_2026-05-15.md`) |
| Working tree | clean |
| 트랙 1 결과 | 3 사이클 + 재검증 완료. spec 21/20/22/24/63/61/60 정정 + spec 30 v1.1 정정. 🔴 백엔드 버그 B1/B2 발견(기록만) |
| 정리 결과 | models/ cleanup A1~A7 (-677줄, intent/plan/todo/approval/execution.ExecutionResult/7 enums) + `_old_v1/` 삭제 (-4,891줄) + agent_specs stale 링크 일괄 정정 + 구버전 5 spec legacy/ 이동 |
| Phase 1 결정 | 7건 (D1~D7) + 일시정지 박스 5 액션 (자연어/워크플로우/계속/취소 + 중지). 백엔드 변경 **0** |

---

## 0. Compact 이후 첫 행동

```
1. 본 문서 + docs/_claude/integration_phase1_implementation_plan_2026-05-15.md
   + (옵션) docs/_claude/integration_design_audit_2026-05-15.md 읽기.
   * _claude/ 는 gitignore — 로컬 작업 노트. 파일 그대로 존재.
2. 모든 사전 작업 완료 상태:
   - 트랙 1 (agent_specs 검증) ✅
   - models/ cleanup A1~A7 ✅ (이름 충돌 3건 해소)
   - _old_v1/ 삭제 ✅
   - agent_specs stale 링크 정리 + 구버전 5 spec legacy/ 이동 ✅
   - 통합 설계 점검 (7 결정사항) ✅
   - Phase 1 구현 계획서 ✅
3. Phase 1 = "hitl_manager/todo_manager ↔ FastAPI ↔ WS ↔ Frontend 연결"
   → 백엔드 변경 0. 프론트 only.
4. 의존성 순서 (계획서 §2):
   P1-1 → P1-2 → P1-3 → P1-4 → P1-6 → P1-9 → P1-5 → P1-7 → P1-8 → P1-10
   각 step atomic commit.
5. P1-10 (E2E 검증) 은 PostgreSQL + 백엔드 + 프론트 다 띄워야 함.
   사전 준비 명령은 계획서 §5.
6. 🔴 백엔드 버그 B1/B2 (layer_guard.py) — "기록만, 나중에" — Phase 1 외.
```

---

## 1. 프로젝트 정체성

- **OctorAD Dream Agent** — 4-Layer LangGraph AI 에이전트 (퍼포먼스 마케팅) + React 프론트 + n8n 스타일 Workflow Canvas
- 백엔드 = **완성**. 권위 계약 문서 = `docs/agent_specs/21_WEBSOCKET_PROTOCOL_v1.4.md`

---

## 2. 브랜치 상태 (절대 혼동 금지)

| 브랜치 | 정체 | 처리 |
|--------|------|------|
| **`main`** | 진짜 개발 상태 — 백엔드 완성 + 프론트 일부 연결 (Sprint 0~3). 프론트 코드 = `a5c4fc3`, 이후 커밋은 `docs/reports/` only | **여기서 작업** |
| **`modoo`** | 영상 시연용 mockup (demoScript/demoStore/정적 fixture/스크립트 응답) | **보존 — 건드리지 말 것.** 레퍼런스로만. main 에 머지 X |

> modoo↔main UI 차이: **색감/디자인 토큰 = 100% 동일** (둘 다 Warm Neutral, modoo 분기 전 `a5c4fc3` 에 이미 적용). 다른 건 **컴포넌트 구조** — modoo 가 데모 엔진(demoScript/demoStore/ChatTodoCard) 신규 + 기존 화면(SideChatPanel/ReportPage/NodeComponent/WorkflowCanvas) 데모용 확장. 상세·cherry-pick 후보는 `modoo_ui_reference.md`.
>
> **결론 (2026-05-15 사용자 확정)**: modoo 에서 main 으로 *능동적으로 가져올 것 없음*. modoo 는 그대로 두고, 필요 시 `modoo_ui_reference.md` 색인 + `git show modoo:<경로>` 로 참조만. cherry-pick 후보 3개(`a89c5ed`/`8f9e228`/`83f6ae4`)도 통합 작업(트랙 2) 완료 후 *선택사항*.

---

## 3. 검증된 진단 (★ 이게 기준점 — 전체 스택 검증 완료)

상세: [`main_integration_status_2026-05-15.md`](./main_integration_status_2026-05-15.md)

**핵심 결론**:
- 백엔드는 완성·정확. `query → /ws/agent → run_turn → 4-Layer graph → broadcast` 백본이 실제로 작동.
- **끊긴 단 하나의 지점** = 프론트 `frontend/src/api/ws.ts:32-36` 의 `WSMessageSchema.safeParse`. 백엔드가 보낸 진짜 응답이 zod 검증 실패로 **전량 폐기**됨 (`console.error('[ws] invalid message')` 만 쌓임).
- **원인** = 프론트 `schemas.ts` WS 스키마 + 스펙 63(이번 세션에 내가 만든 frontend-backend contract 문서)이 **spec 21 과 다른 — 일부 실재하지 않는 — 포맷**으로 작성됨.

**계약 불일치 (spec 21 = 진실 / schemas.ts = 틀림)**:
- `node_event`: BE `{type, node, conv_id, turn_id, data:<State dict>}` / FE `{data:{layer,node_name,status,timestamp}}` ← FE 가공
- `complete`: BE `data.status` / FE `data.reason` 기대
- `hitl_request`: BE `data:{request_id,plan,options,message}` / FE `request_type` 기대 (가공 필드)
- `paused`/`resumed`/`layer_start`/`todo_start`/`todo_complete`/`progress`: BE emit / FE 스키마 **없음**
- `agent_message`/`agent_message_complete`: BE **미발행** / FE 핸들러 **있음** (데드코드)
- `error`: BE 평탄 `{code,layer,severity,message}` / FE `data` 중첩

**서버 기동 전제**: 백엔드는 **PostgreSQL 필수** — 없으면 `main.py` lifespan 에서 `RuntimeError` 로 기동 거부. `.env` (`CHECKPOINT_DB_URI`, `OPENAI_API_KEY`) 필요. 프론트 vite → 5173, `/api`·`/ws` → 8001 프록시.

**데이터 2갈래**: 에이전트 실행 도구 = `data/mock/*.csv` **파일 직독** (`load_mock_csv`) / 대시보드 = `/api/mock/*` HTTP. 같은 CSV, 다른 경로.

---

## 4. mock 4갈래 분류 (★ "data 외 모두 삭제" 는 위험)

| 분류 | 정체 | 처리 |
|------|------|------|
| **(A) 데이터 mock** | `data/mock/*.csv` + `/api/mock/*` + `load_mock_csv` | **유지** — 의도된 POC 데이터 레이어 |
| **(B) 데드코드** | `backend/app/dream_agent/_old_v1/` (40여 파일, import 0건) · `schemas.ts` `AgentMessage*` 스키마+핸들러 · `useAgent` `streamingBuffer` 계열 | **삭제** |
| **(C) 도구 stub** | `team_catalog.yaml` `status: stub` 도구 ~26개 + `execution/mock_tools.py` `mock_result()` | **삭제 금지** — 의도된 POC 골격. `executor.py` 가 stub→`mock_result()` 폴백. 지우면 execution 깨짐. 도구 실구현으로 *졸업*시키는 별개 트랙 |
| **(D) 프론트 stub** | `WorkflowPage` `SAMPLE_PLAN`, `PagePlaceholder` | 실 연결로 **교체** |

---

## 5. 다음 작업 — 2 트랙

### 트랙 1 (★ 사용자 강조 — 우선) — agent_specs 문서 다중 사이클 검증 — ✅ **완료 (2026-05-15)**

- **이유**: spec 63 이 spec 21 과 어긋난 게 발견됨 → "다른 문서도 틀렸을 수 있다". 틀린 문서 기준으로 코딩하면 오류가 걷잡을 수 없이 번짐.
- **수행 결과**: 3개 사이클 + 재검증 1회. 상세 = [`agent_specs_verification_2026-05-15.md`](./agent_specs_verification_2026-05-15.md). 커밋 `cd47487` / `2475c91` / `13dc823` / `a47b457`.
  - **사이클 1**: spec 21 ↔ `ws_agent.py`/`ws_hitl.py` — 본문 근본 정합, drift 4건 정정.
  - **사이클 2**: spec 20/22/24 ↔ 백엔드 — spec 20 §3 스키마 8건 정정(Plan 전면 재작성). 🔴 **백엔드 코드 버그 2건(B1/B2 — `layer_guard.py`) 발견** → 사용자 결정 = "문서에 기록만, 나중에 수정".
  - **사이클 3**: spec 63 + 60/61 ↔ 백엔드 — spec 63 이 광범위하게 틀려 있던 게 **프론트 통합 break 의 근본 원인**. 4개 섹션 전면 정정. `21_v1.2.md` 삭제.
  - **재검증**: 정정 문서 상호 정합 확인, spec 63 §6.1 `team` 1건 추가 정정.
- ⚠️ 미해결(별도 hygiene 패스): 다수 문서의 `21_v1.2`/`22_v1.0` stale 링크, spec 61 §4 Design System(Warm Neutral 이전), spec 61 store 경로 표기.
- 🔴 **B1/B2 백엔드 버그**: `layer_guard.py` — B2(execution `"success"`≠`"completed"` → 부분 실패가 전체 abort)는 영향 큼. 트랙 2 또는 별도 백엔드 트랙에서 1-2줄 패치.

### 트랙 2 (재정의됨) — 통합 Phase 1 (★ 다음 세션 진입점)

**사용자 의도** (한 줄): "hitl_manager / todo_manager ↔ FastAPI ↔ data ↔ WebSocket ↔ Frontend 잘 연결만"

**결정 사항 (D1~D7)**:
- D1: Todo board = 이미지 ChatTodoCard 패턴 (워크플로우 호환, 중지버튼)
- D4: HITL 편집도 같은 방식 (인라인)
- D5: 모달 없음 (자동 plan_review approve)
- D6: turn_id/conv_id 클라 자동 생성 + localStorage
- D7: user_id="demo" 하드코딩 유지

**일시정지 박스 5 액션** (사용자 이미지):
- ⚡ 자연어 적용 → `todo_edit_nl`
- 🔗 워크플로우에서 수정 → navigate `/workflow`
- ▶ 계속 → `resume`
- ✕ 취소 → `cancel`
- (실행 중 [⏸ 중지] → `pause`)

**Phase 1 — 10 단계 atomic (계획서 = `docs/_claude/integration_phase1_implementation_plan_2026-05-15.md`)**:

| Step | 내용 | 의존성 |
|------|------|--------|
| P1-1 | `schemas.ts` WS 섹션 재작성 (spec 21 정합) + 동반 typecheck 수정 | 기반 |
| P1-2 | `useSession.startTurn()` 자동 생성 + localStorage | P1-1 |
| P1-3 | `ws.ts` URL `?user_id=demo` + pause/resume/cancel/todo_edit_nl 송신 함수 | P1-1 |
| P1-4 | `useExecution` store + `TodoView` selector (Plan + nodeEvents + progress 결합) | P1-1 |
| P1-6 | 자동 `plan_review` approve (`useHitl.handleWSMessage`) | P1-3/P1-4 |
| P1-9 | `WorkflowPage` SAMPLE_PLAN 제거 → 실 plan 연결 | P1-4 |
| P1-5 | `ChatTodoCard` 컴포넌트 + SideChatPanel 통합 | P1-4 |
| P1-7 | 실행 중 [⏸ 중지] 버튼 | P1-3/P1-5 |
| P1-8 | PauseBox (5 액션) | P1-3/P1-5 |
| P1-10 | E2E 검증 (PostgreSQL + 백엔드 + 프론트) | 전부 |

**Phase 2+ (이번 작업 외 — 후속)**:
- 진행률 바 / 노드 색 변경 (todo_complete 로)
- resume_query 서버 재시작 복원
- WorkflowCanvas 직접 시각 편집 (W2)
- Save/Library (W3)

---

## 6. 핵심 문서 위치

| 문서 | 역할 |
|------|------|
| [`reports/main_integration_status_2026-05-15.md`](./main_integration_status_2026-05-15.md) | ⭐ 전체 스택 검증 진단 — 기준점 |
| [`reports/modoo_ui_reference.md`](./modoo_ui_reference.md) | modoo UI 작업 색인 — 코드 복사 없이 참조. cherry-pick 후보 3개(`a89c5ed`/`8f9e228`/`83f6ae4`) |
| `agent_specs/21_WEBSOCKET_PROTOCOL_v1.4.md` | ⭐ 권위 WS 계약 — 백엔드가 따름 |
| `agent_specs/63_frontend_backend_contract_v1.0.md` | ⚠️ 내가 만든 문서 — WS 부분이 21 과 어긋남, 정정 대상 |
| `agent_specs/20_INTERFACE_CONTRACT_v1.1.md`, `22_error_codes_v1.1.md`, `24_sequence_diagrams_v1.3.md` | 백엔드 계약 보조 |
| `agent_specs/10`~`14`, `30`~`35` | 아키텍처·데이터 모델·DB 스키마 |
| `agent_specs/INDEX.md` | 스펙 맵 |

---

## 7. 좀비/데드코드 방지 원칙 (작업 시 적용)

1. **단일 계약 출처 = spec 21** (WS). 어긋난 문서(스펙 63)는 먼저 정정.
2. **(C) 도구 stub 은 건드리지 않는다** — "data 외 모두 삭제" 금지.
3. 가공 코드(`agent_message`*) 완전 삭제. stub 은 주석처리 X, 삭제/교체.
4. 어댑터(옛+신 포맷 동시 지원) 금지. (memory: `feedback_no_mixed_codebases`)
5. 계약 변경 = 코드 + 문서 한 커밋.
6. `_old_v1/` 삭제는 import 0건 grep 재확인 후.
7. 단계마다 typecheck + 검증 + 커밋. (memory: `feedback_test_no_resource_limit`, `feedback_commit_auto_on_completion`)
8. **문서가 진실이 되기 전엔 코드 작업 진입 금지** (사용자 강조).

---

## 8. Compact 이후 prompt

**모든 사전 작업 완료** → 이제 Phase 1 atomic 실행. 아래 prompt 중 하나 사용:

### 🟢 권장 — Phase 1 P1-1 부터 시작
```
docs/_claude/integration_phase1_implementation_plan_2026-05-15.md 읽고
Phase 1 P1-1 부터 atomic 실행 시작하자. 의존성 순서 (§2):
P1-1 → P1-2 → P1-3 → P1-4 → P1-6 → P1-9 → P1-5 → P1-7 → P1-8 → P1-10.
각 step 마다 typecheck + atomic commit.
```

### 🟢 대안 — 상황 파악 후 결정
```
docs/reports/session_compact_recovery_2026-05-15.md 읽고 현 상황 파악.
```

### 📌 인프라 준비 (P1-10 진입 전 — 미리 띄워두면 좋음)
```bash
# PostgreSQL (docker)
docker run --name octormate-pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16

# .env 확인 (CHECKPOINT_DB_URI, OPENAI_API_KEY)
# 백엔드 (별 터미널)
uv run python run_server_v2.py

# 프론트 (또 별 터미널)
cd frontend && pnpm dev
```

---

## 9. 검증 체크리스트 (Claude 가 본 문서 제대로 읽었는지)

- [ ] 현재 브랜치 = `main` (프론트 코드 `a5c4fc3`), modoo 는 데모 mockup (보존, 능동적으로 가져올 것 없음)
- [ ] 백엔드 = 완성, 권위 계약 = `21_WEBSOCKET_PROTOCOL_v1.4.md`
- [ ] 끊긴 지점 = 프론트 `ws.ts` 의 `WSMessageSchema.safeParse` (백엔드 응답 전량 폐기)
- [ ] 원인 = `schemas.ts`/스펙 63 이 spec 21 과 다른 가공 포맷
- [ ] mock 4갈래 — (C) 도구 stub 은 **삭제 금지**
- [ ] 다음 최우선 = agent_specs 문서 다중 사이클 검증 (코드 작업 전)
- [ ] 백엔드는 PostgreSQL 필수 (없으면 기동 거부)

**틀린 항목 있으면**: 본 문서 + `main_integration_status_2026-05-15.md` 다시 읽고 정확히 보고.

---

## 10. 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-15 | 초안 — modoo 데모 완성 후 main 복귀, 전체 스택 통합 진단 완료. 다음 = agent_specs 문서 다중 사이클 검증 → 통합 Phase 0~5 |
| 2026-05-15 (갱신) | modoo_ui_reference.md 추가 + UI 차이(색감 동일/구조만 다름) 반영. modoo 능동 참조 불필요 확정. Compact prompt = 옵션 A 확정. §2 표·체크리스트 브랜치 해시 불일치 정정 |
| 2026-05-15 (트랙1 완료) | **agent_specs 문서 다중 사이클 검증 완료** — 3 사이클 + 재검증. spec 21/20/22/24/63/61/60 정정, `21_v1.2.md` 삭제. 백엔드 버그 B1/B2 발견(기록만). §0/§5/§8 + 헤더 갱신 — 다음 = 트랙 2 Phase 1. 검증 로그 = `agent_specs_verification_2026-05-15.md` |
| 2026-05-15 (정리 완료) | **models/ cleanup A1~A7 + B 완료** (8 atomic 커밋, -677줄). `intent.py`/`approval.py`/`plan.py`/`todo.py`/`execution.ExecutionResult` + 7 enum 삭제. 이름 충돌 3건(`Plan`/`ExecutionResult`/`TodoStatus`) 해소. spec 30 v1.1 정정판 + legacy/v1.0 archive |
| 2026-05-15 (_old_v1 삭제) | `backend/app/dream_agent/_old_v1/` 43 파일 -4,891줄 삭제 (`a60f0bd`) |
| 2026-05-15 (agent_specs hygiene) | 핵심 spec 3건(ADR-010/14/11) 갱신 + stale 링크 일괄 정정 (30/21/22/10/12 5쌍, sed) + 구버전 5 spec legacy/ 이동 (`d927102`, `ed13904`) |
| 2026-05-15 (Phase 1 설계) | **통합 사전 점검 + Phase 1 구현 계획서 작성** — D1~D7 결정, 일시정지 박스 5 액션 디자인, P1-1~P1-10 atomic 구조 + 의존성 그래프. 계획서 = `docs/_claude/integration_phase1_implementation_plan_2026-05-15.md` (로컬, gitignore). 본 가이드 §0/§5/§8 + 헤더 갱신 — 다음 세션 = Phase 1 P1-1 부터 실행 |
