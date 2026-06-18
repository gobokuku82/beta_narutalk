# ADR-010: Plan / Todo Schema 통합 — `planner.Plan` 단일화

## Status

**Accepted** (2026-04-30) — Sprint 14 A3 Phase C-Unify 완료

## Context

POC 1차 검증 (R-16) 으로 NL 편집 fatal 발견:

활성 코드에 **3 Plan 클래스 + 2 Todo 클래스** 가 공존했다.

| 클래스 | 위치 | 성격 |
|--------|------|------|
| `planner.Plan` | `planning/planner.py` | LLM 산출물 (간단, 정형) |
| `planner.PlannedTodo` | `planning/planner.py` | LLM 산출물 todo |
| `models.Plan` | `models/plan.py` | Canonical (lifecycle metadata 포함) |
| `models.TodoItem` | `models/todo.py` | Canonical, frozen |

**데이터 흐름의 불일치**:
- `progress.plan` = `planner.Plan.model_dump()` dict (LLM 형식)
- `plan_editor.PlanEditor` 는 `models.Plan` 입력 기대
- 변환 시도 시 Pydantic ValidationError → NL 편집 ("4번 삭제") fatal

**근본 원인**: 두 schema 가 의미적으로 같은 영역 (Plan/Todo) 을 다른 형식으로 표현 → 변환 부담 + 부채.

상세 분석: [`docs/reports/sprint14_a3_research_q1_plan_schema.md`](../../reports/sprint14_a3_research_q1_plan_schema.md)

## Decision

**`planner.Plan` / `planner.PlannedTodo` 로 단일화**.

### 변경 범위 (Sprint 14 A3 Phase C-Unify, 2026-04-30)

| 모듈 | 변경 |
|------|------|
| [`hitl_manager/plan_editor.py`](../../../backend/app/dream_agent/workflow_managers/hitl_manager/plan_editor.py) | `models.Plan/TodoItem/PlanChange` → `planner.Plan/PlannedTodo`. `apply_edit` 단일 반환 (PlanChange 폐기) |
| [`api_v2/ws_hitl.py`](../../../backend/api_v2/ws_hitl.py) | `Plan.model_validate(progress.plan)` 직접 사용. 어댑터 호출 제거 |
| [`scripts/a3_nl_success_rate.py`](../../../backend/scripts/a3_nl_success_rate.py) | 측정 plan fixture `planner.Plan/PlannedTodo` 로 전환 |
| 테스트 fixture | `planner.Plan/PlannedTodo` 로 일괄 전환 (NL unit / NL integration / plan_review integration) |

### 폐기

- `hitl_manager/plan_adapter.py` (Sprint 14 A3 시도 — `e767845`): 삭제
- `tests/sprint14/test_a3_plan_adapter_unit.py`: 삭제
- `models.Plan / TodoItem` 의 활성 코드 사용: 0. 2026-04-30 정리 직후엔 `_old_v1/` 호환 + `approval.PlanChange` 사용처를 위해 deprecated 마커로 유지했음. **2026-05-15 후속 정리에서 완전 제거** — 아래 참조.

### PlanChange 처리

NL edit 경로에서는 폐기 (ws_hitl 미사용). 2026-04-30 시점엔 `approval.py` 가 별도 flow 에서 PlanChange 를 사용한다고 보았으나, **2026-05-15 검증으로 `approval.py` 자체가 활성 호출자 0 임이 확인되어 삭제됨** — PlanChange 도 함께 폐기.

향후 이력 추적 (NL edit 변경 history) 이 필요해지면 Sprint 15 메모리 시스템 (`memory_entries` 의 `conversation_meta` type) 으로 대체.

### 2026-05-15 후속 정리 (models/ cleanup A1~A7)

본 ADR 의 deprecated 표기가 더 이상 정당화되지 않아 통째로 제거:

| 파일 / 클래스 | 처리 | 사유 |
|-------------|------|------|
| `models/plan.py` (`Plan`, `PlanChange`, `PlanVersion`) | **삭제** (A3) | 본 ADR 로 `planner.Plan` 단일화 후 `approval.py` 외 활성 사용 0 |
| `models/todo.py` (`TodoItem`, `validate_transition`) | **삭제** (A4) | `planner.PlannedTodo` 로 대체 완료 |
| `workflow_managers/hitl_manager/approval.py` | **삭제** (A2) | `ApprovalHandler` 활성 호출자 0 확인 |
| `models/enums.py` (`PlanStatus`, `TodoStatus`(8값), `Layer`, `ExecutionStrategy`, `SessionStatus`, `IntentDomain`, `IntentCategory`) | **삭제** (A5) | 위 클래스들 의존 사라짐 + 활성 사용 0 |
| `models/execution.py::ExecutionResult` | **삭제** (A6) | 활성 사용 0, 동명이인 충돌 해소 |
| `models/intent.py` (`Intent`, `Entity`) | **삭제** (A1) | docstring example 만 의존 — `Any` 로 치환 |
| `_old_v1/` 디렉터리 (43 파일) | **삭제** | 외부 import 0 확정 |

**결과**: 이름 충돌 3건 (`Plan`/`ExecutionResult`/`TodoStatus`) 완전 해소 — codebase 안에 각 1곳만 존재.

상세 정리 계획: [`docs/_claude/models_cleanup_plan_2026-05-15.md`](../../_claude/models_cleanup_plan_2026-05-15.md) (로컬)
정리 박제: [`docs/reports/agent_specs_verification_2026-05-15.md`](../../reports/agent_specs_verification_2026-05-15.md) 사이클 5

## Alternatives Considered

| 옵션 | 내용 | 채택 안 한 이유 |
|------|------|---------------|
| **A** | `models.Plan` 으로 통일 (LLM 출력 변경) | LLM prompt / planner / executor 모두 변경 → 회귀 위험 큼. 마이그레이션 비용 ↑↑ |
| **B (시도 후 폐기)** | 어댑터 layer 로 두 schema 공존 (`plan_adapter.py`) | Sprint 14 A3 임시 (commit `e767845`) 로 진행 후 철회. 이유: (1) v1/v2 섞임 부채, (2) 의미 어긋남 매핑 (`task_type ↔ task`) silent bug 위험, (3) "다음 Sprint 정리" 약속이 깨질 가능성 큼 (현장 패턴), (4) 통일 비용 ~1 working day 미만 |
| **C** | 단계적 (B → A) | A 채택 비용 동일. 부채만 추가됨 |
| **D ⭐** | `planner.Plan` 으로 통일 (현재 채택) | LLM prompt 영향 0 / 어댑터 부채 0 / lifecycle metadata 부재는 POC 단계 무해. Sprint 16+ 본격 production 시 PlannedTodo 확장으로 lifecycle 추가 가능 |

## Consequences

### 좋은 점

- ✅ **schema 1개** — v1/v2 섞임 0 (사용자 통찰 부합)
- ✅ **확장 비용 ↓** — 추후 변경 시 단일 모듈만 진화
- ✅ **LLM prompt 영향 0** — D 옵션 채택 핵심 이유
- ✅ **테스트 안전망 유지** — 239 passed + 2 skipped 회귀 0
- ✅ NL 편집 fatal (R-16) 코드 레벨 해소

### 비용 / 위험

- ⚠️ `PlannedTodo` 는 `frozen=False` (mutable) — 의도치 않은 변경 위험. 완화: `model_copy(update=...)` 패턴 유지 (관행)
- ⚠️ `PlanChange` 폐기로 NL edit 이력 추적 약화 — Sprint 15 `memory_entries` 가 더 강력한 대체
- ⚠️ `planner.Plan` 의 dependency 순환 검증 약함 (`models.Plan.validate_dependencies` 같은 model_validator 없음) — `validate_dag()` 함수가 별도 존재 → `plan_editor.validate_edit` 에서 호출 가능 (현재 미사용, 필요시 보강)
- ~~`models.Plan / TodoItem` 활성 사용 0 이지만 deprecated 파일로 유지~~ — **2026-05-15 후속 정리에서 완전 삭제** ([상세](#2026-05-15-후속-정리-models-cleanup-a1a7))

### 향후 작업

- Sprint 15 P0 메모리 시스템 → NL edit 이력 capture (PlanChange 대체)
- Sprint 16+ production 진입 시 `PlannedTodo` 확장 (status / lifecycle / timestamps) 검토

## Related

- 사전 조사: [`docs/reports/sprint14_a3_research_q1_plan_schema.md`](../../reports/sprint14_a3_research_q1_plan_schema.md)
- 작업 계획: [`docs/reports/sprint14_a3_phase_c_unify_plan.md`](../../reports/sprint14_a3_phase_c_unify_plan.md)
- 어댑터 시도 commit: `e767845` (`fix(sprint14): A3 R-16 NL fatal — Plan adapter (B 옵션) 적용`) — D 통일 commit 에서 파일 삭제
- ADR-002 NL 점진 고도화 (편집 경로)
- ADR-015 메모리 architecture (PlanChange 대체)

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-30 | 초안 + Accepted. Sprint 14 A3 D 단일화 결정. 어댑터 시도 (B) 후 D 직진으로 수렴 |
| 2026-05-15 | **후속 정리 반영** — 본 ADR 의 deprecated 마커 정당화가 사라져 `models/plan.py`/`todo.py`/`approval.py`/`intent.py`/`execution.py::ExecutionResult` + 7 enum + `_old_v1/` 통째 삭제. 이름 충돌 3건 모두 해소. 상세 = `_claude/models_cleanup_plan_2026-05-15.md` |
