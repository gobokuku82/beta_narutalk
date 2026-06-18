# Sprint 14 A1 완료 보고서 — HITL Resume Timeout

| 항목 | 내용 |
|------|------|
| 스프린트 | **Sprint 14 A1 — HITL wait_for_resume Timeout + Stale Turn Guard** |
| 기간 | 2026-04-22 (1일, Plan v0.8 → 구현 → 브라우저 검증) |
| 담당자 | 도윤 + Claude |
| 상태 | **✅ 완료** |
| 작성일 | 2026-04-22 |
| 관련 Plan | `docs/_claude/sprint14_a1_hitl_timeout_plan.md` v0.8 |
| 관련 요구사항 | `docs/agent_specs/01_requirements_v1.2.md` FR-13/13a/13b · NFR-9/10 · UX-4/5 |

---

## 1. 목표 및 결과 요약

### 1.1 Sprint 14 A1 목표
1. `wait_for_resume` 에 timeout 지원 — 무한 대기로 인한 slot 누수 방지 (FR-13)
2. timeout 시 `complete(status="aborted", reason="hitl_timeout")` emit + concurrency slot 해제 (FR-13a)
3. timeout 이후 동일 turn_id 의 HITL 요청은 `turn_not_active` 로 거부 (FR-13b)
4. 기본 30분 + `.env HITL_RESUME_TIMEOUT_SEC` override (NFR-9/10)
5. 대시보드 UX — 한글 메시지 + hitl_ack 토스트 (UX-4/5)
6. G-1 Critical: 실 Checkpoint 종결 증명

### 1.2 결과 지표

| 항목 | 수치 |
|------|------|
| Unit + Integration (그룹 A~F) | **36/36 pass** (Round 17 에서 그룹 B 에 HT-06e/06f 2건 추가) |
| Live (그룹 G HTL-01~04) | **4/4 pass** ⭐ |
| Sprint 13 regression | **137/137 유지** |
| **총 자동 테스트** | **177 passed** (173 non-live + 4 live) |
| Contract Test (DC-1~5) | 5/5 pass |
| Browser regression (R-13/14/15) | **전수 pass** (2026-04-22 live 확인) |

---

## 2. 구현 내역

### 2.1 백엔드 코드 변경 (4 파일)

| 파일 | 변경 |
|------|------|
| `backend/app/dream_agent/workflow_managers/hitl_manager/manager.py` | `_active_turns` set 필드 + `register_turn` / `is_turn_active` 신규. `wait_for_resume(turn_id, timeout=None)` timeout 인자 추가 — 초과 시 `{"action":"timeout"}` 반환. `cleanup_turn` 확장 — `_active_turns` + `_paused.discard` 추가 (CS-2 잔류 방지) |
| `backend/app/core/config.py` | `HITL_RESUME_TIMEOUT_SEC: int = Field(default=1800, ge=1)` 신규. `.env` override 가능, 0/음수 pydantic validator 차단 |
| `backend/api_v2/ws_hitl.py` | 4개 핸들러에 `is_turn_active` 가드 — `_handle_pause` / `_handle_resume` / `_handle_cancel` + `_handle_hitl_response` (Round 17 drift 보완). 비활성 turn → `hitl_ack {accepted:false, reason:"turn_not_active"}` |
| `backend/api_v2/ws_agent.py` | `run_turn` try 블록 첫 줄에 `register_turn(turn_id)`. `_graph_runner_with_resume` 에 timeout 인자 전달 + 분기 추가 — **G-11 intr_type 별 주입값** (`plan_review` → reject / `execution_pause` → cancel) + `resumed` 이벤트 skip + structured warning log (G-12) |

### 2.2 Dashboard (1 파일)

`dashboard/index.html`:
- `handleComplete` — aborted/rejected/cancelled 수신 시 plan_review 모달 자동 close (Round 17)
- `handleComplete` aborted 분기 — `ABORT_REASON_LABELS` 매핑 (hitl_timeout → 한글, UX-4)
- `wsHitl.onmessage` hitl_ack 핸들러 — `accepted:false, reason:turn_not_active` 감지 → 토스트 + `resetSendButton()` (UX-5)
- `submitHitlResponse` — null turn_id 분기에서도 모달 close (방어)

### 2.3 테스트 신규 (37건)

| 그룹 | 파일 | 건수 | 역할 |
|------|------|------|------|
| A | `test_hitl_timeout_unit.py` | 6 | HITLManager pure async — timeout / register / cleanup |
| B | `test_hitl_timeout_guard_unit.py` | 9 | ws_hitl 4종 가드 + fallback + 대칭 회귀 (Round 17 에서 HT-06e/06f 추가) |
| C | `test_hitl_timeout_integration.py` | 13 | run_turn 통합 (MockAgent) — 이벤트 순서, G-11, G-12 |
| D | `test_settings_validator_unit.py` | 5 | Field(ge=1) boundary |
| E | `test_hitl_timeout_resume_query_unit.py` | 1 | resume_query 재진입 INVALID_MESSAGE |
| F | `test_hitl_timeout_race_unit.py` | 2 | timeout↔signal race 100회 반복 결정성 |
| G | `test_hitl_timeout_e2e_live.py` | 4 | E2E live — 실 Checkpoint 종결 (G-1 진짜 증명) |

fixture 보강: `conftest.py fresh_hitl` 에 `_active_turns.clear()` 추가.
회귀 보강: `sprint13/test_ws_hitl_integration.py WH-03~07` 에 `register_turn` 선행.

### 2.4 문서 cascade (6 bump)

| 문서 | 변경 |
|------|------|
| `01_requirements_v1.1` → **v1.2** | FR-13 을 13/13a/13b 로 분해. §3.5 UX 섹션 신설 (UX-1~6). NFR-9/10 추가. §5 In Scope Sprint 14 블록. §6 Sprint 14 Acceptance + R-13/R-14 regression. §7 용어 `turn_not_active` |
| `12_manager_layer_v1.0` → **v1.1** | §4.3 API — `register_turn`/`is_turn_active` 신규, `wait_for_resume` 확장. §4.4 공유상태에 `_active_turns` 추가. §4.5 테스트 목록 sprint14 7개 파일 |
| `13_lifecycle_v1.1` → **v1.2** | §3.3 Sprint 14 A1 구현 완료 재작성 — intr_type 별 reject/cancel G-11, T-1/T-2/T-3 시나리오, `_active_turns` 레지스트리 |
| `20_INTERFACE_CONTRACT_v1.0` → **v1.1** | §0 개요 Manager API 링크 + Sprint 14 A1 변경 요약 |
| `21_WEBSOCKET_PROTOCOL_v1.1` → **v1.2** | `complete.data.reason=hitl_timeout` 추가 + reason 카탈로그 표 신설. `hitl_ack accepted:false / reason:turn_not_active` 케이스 추가 + reason 카탈로그 |
| `24_sequence_diagrams_v1.1` → **v1.2** | §5a/b/c 신규 — plan_review timeout (reject), execution_pause timeout (cancel), 늦은 HITL 요청 → turn_not_active |

`INDEX.md` 6개 링크 갱신. Cross-link drift sed 일괄 치환 (22/30 등).

---

## 3. Plan v0.8 수립 과정 — 16 라운드 누적

Plan 초안(v0.1, 157줄) → **v0.8 동결(1142줄)** 까지 16라운드 반복 검증.

### 3.1 라운드 요약

| 범주 | 라운드 | 주요 산출 |
|------|--------|-----------|
| 초기 설계 | R1~R5 | R0 범위 + R1 시그니처 + R2 체크포인트 C-1~7 + R2.5 Cascade CS-1~6 + R3 최종 스윕 + Phase 1~9 + Acceptance 12 체크 |
| Gap 발굴 | R6~R10 | 7개 gap G-1~G-7 → 이차 gap G-8/9/10 (Round 7). 테스트 5그룹 구조 개편 (A~E, 20건). Traceability Matrix. R-13/R-14/R-15 regression 명세 |
| 심층 검증 | R11~R13 | Phase 의존성 + atomic PR 전략. **🔴 G-11 Critical 발견** (plan_review timeout cancel 주입 시 fallthrough → execution 진입 위험) → intr_type 별 reject/cancel 분기로 수정. G-12 structured log. 문서 cascade 6개로 확대 |
| 코드·specs 대조 | R14 | F-1~F-12 실재성 검증 — HT-04d 중복 삭제, HT-08f structlog 교체, HT-10 범위 재정의, register_turn try 내부 배치, 22_error_codes 제외, 12_manager_layer 구체 diff. 그룹 G Live 4건 신규 (HTL-01~04). 총 37건 |
| 검증 규칙 | R15~R16 | 8 규칙 V-1~V-8 자기 점검 → minor 3건 발견 → 해소. **v0.8 동결**. "구현 중 발견 시만 재진입" 정책 |
| 구현 중 | **R17** | 브라우저 R-13 실 검증에서 drift 3건 발견 — Dashboard 모달 자동 close + null turn_id 방어 + 서버 `_handle_hitl_response` 가드 (FR-13b 4종 완결) |

### 3.2 G-11 (Critical) 상세 — 가장 큰 발견

**증상**: `planning_stage.py:81~97` 은 `action=="reject"` / `"modify"` 만 분기. `"cancel"` 주입 시 fallthrough → `goto="execution"` → plan_review timeout 인데도 계획이 실행됨.

**수정**: `_graph_runner_with_resume` timeout 분기에서 `intr_type` 따라 주입값 선택
```python
timeout_action = "reject" if intr_type == "plan_review" else "cancel"
```

**검증**:
- Unit: HT-08c (resume_values == [{"action":"reject"}]), HT-08g (execution 노드 chunk 부재)
- Live: HTL-01 (실 planning → END 종결), HTL-02 (실 execution → END 종결)

---

## 4. G-1 Critical — 실 Checkpoint 종결 증명

### 배경
timeout 분기에서 `LGCommand(resume={...})` silent drain 후, 실제 PostgreSQL Checkpoint 가 **재진입 불가 (terminal)** 상태인지 확인 필요.

### 검증 방식
HTL-01 / HTL-02 테스트에서 `.env HITL_RESUME_TIMEOUT_SEC=10` 임시 주입 후:
1. 실 OpenAI + PostgreSQL + FastAPI TestClient 로 query 수행
2. timeout 발생 대기
3. `complete(aborted, reason=hitl_timeout)` 실수신
4. `graph.aget_state({"configurable": {"thread_id": thread_id}})` 호출
5. `gs.next == ()` AND 모든 `tasks[].interrupts == []` 확인

**결과**: 두 interrupt 타입 모두 Checkpoint terminal 확인.
- HTL-01 (plan_review, 31s): pass ✅
- HTL-02 (execution_pause, 33s): pass ✅

Browser regression R-15 와도 정합 — timeout 된 turn 에 resume_query → `INVALID_MESSAGE`.

---

## 5. 브라우저 Regression (live 수동)

| ID | 시나리오 | 검증 |
|----|---------|------|
| R-13 | plan_review 10s 방치 → `complete(aborted, hitl_timeout)` + Dashboard "⏱ 자동 종료됨" 한글 메시지 + 모달 자동 close | ✅ (Round 17 포함) |
| R-14 | 비활성 turn 에 pause/resume/cancel/hitl_response 4종 전송 → `turn_not_active` ack + "⚠️ 이 쿼리는 시간 초과로 종료되었습니다" 토스트 + idle 복귀 | ✅ |
| R-15 | `LS.set("last_turn_id", "stale_id")` 후 새로고침 → onopen resume_query 자동 전송 → `[fatal/transport] INVALID_MESSAGE` 수신 | ✅ |

**방법**: F12 콘솔 + 임의 stale turn_id. `.env HITL_RESUME_TIMEOUT_SEC=10` 임시 주입.

---

## 6. 커밋 이력 (7건)

```
d6434e5 fix(sprint14): R-13 실 검증 drift 보완 — 모달 자동 close + hitl_response 가드
11e8beb test(sprint14): A1 HITL timeout 그룹 G Live 4건 실구현 — 전수 pass (G-1 진짜 검증)
f8f6590 docs(sprint14): agent_specs cascade — 5 문서 bump + INDEX (Phase 7)
b8132ea feat(sprint14): Dashboard UX-4/UX-5 — HITL timeout 한글 매핑 + hitl_ack 핸들러
4f8dc4b test(sprint14): A1 HITL timeout 테스트 34건 pass + live 4건 skeleton
a95a0e2 feat(sprint14): A1 HITL resume timeout — 핵심 원자 (Phase 2+3+4+5)
d2d14a9 docs(sprint14): requirements v1.1 → v1.2 — A1 HITL timeout 요구사항 확장
```

---

## 7. 알려진 한계 / Out of Scope

### 7.1 수용 선언
- **Dashboard UX 자동화 회귀 부재** (V-4): Playwright/Puppeteer E2E 미도입. POC 단계 수용, live browser R-13/R-14/R-15 수동 검증으로 대체
- **T-3 race** (timeout↔resume 버튼 μs 단위 race): 2택 결과 허용 (Queue leak 없음). 그룹 F 100회 결정성 확인

### 7.2 Sprint 15+ 이관
- **UX-6 aborted turn 재개/복원 UI** — Conversation DB + 사이드바 기반 (Memory sprint)
- **dead constants cleanup**: `HITL_TIMEOUT_SEC=300` / `HITL_MAX_RETRIES=3` — 참조 없음, Sprint 15+ 정리
- **legacy `_run_agent` / `wait_for_response`**: Sprint 13 이후 dashboard 미사용. Memory sprint 와 묶어 재평가

### 7.3 기존 Sprint 13 한계 유지
- TestClient + asyncio sequential hang — live 테스트 개별 실행 원칙
- PostgreSQL Checkpoint rotation — Sprint 17+

---

## 8. Plan v0.8 자산

- `docs/_claude/sprint14_a1_hitl_timeout_plan.md` — 1142줄, 16 라운드 반복 고도화 과정 + Traceability Matrix + 검증 규칙 V-1~V-8
- `docs/_claude/sprint14_master_plan.md` v1.1 — Reducer 보류 반영, Tier 1=A1 단독
- `docs/_claude/sprint14_reducer_plan.md` — 🔒 보류 상태 헤더. Tool 확장 이후 재평가

---

## 9. 다음 스프린트

### Tier 2 (독립 실행 가능)
- **A2**: phase 내 pause 세밀화 (`should_continue` 를 Todo 단위)
- **A3**: Todo 편집 HITL (add/delete/modify + Cascade)
- **A4**: `team_catalog.yaml` `requires_approval` 확장

### Tier 3 (문서 신설)
- `23_event_catalog_v1.0` / `32_team_catalog_schema_v1.0` / `33_prompt_catalog_v1.0` / `40_runbook_v1.0` / `41_testing_strategy_v1.0` / `50_glossary_v1.0`

### Tier 4 (Sprint 15)
- Memory — Conversation DB + 사이드바 + UX-6 재개 UI

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-22 | 초안 — Sprint 14 A1 구현 / 검증 / 브라우저 regression 완료 보고 |
