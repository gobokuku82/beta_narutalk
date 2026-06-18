# Sprint 14 A3 종결 — Phase C 세부 작업계획서 (NL fix + 문서 정리)

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-28 |
| Phase | C — Sprint 14 A3 종결 (POC 1차 Minimum Viable Completion) |
| 마스터 | [`sprint15_implementation_plan.md`](./sprint15_implementation_plan.md) |
| 의존 | Phase B (사전 조사) ✅ 완료 |
| 다음 | [`sprint15_phase_d_adr.md`](./sprint15_phase_d_adr.md) Phase D — ADR 본문 |
| 예상 작업량 | ~3시간 (1세션) |
| Acceptance | R-16/17/18 PASS + spec bump + ADR-010 본문 + 완료 보고서 |

---

## 0. 본 문서의 역할

Phase C 의 **모든 작업 카탈로그** — 파일 / LoC / 테스트 / 검증 / acceptance.

작업 시작 시 본 문서 따라가고, 완료 시 §10 체크리스트 마킹.

본 문서는 Phase C 만 다룸. Phase D 이후는 별도 문서.

---

## 1. Phase C 의 의도

### 1.1 왜 이 Phase 가 필요한가

POC 1차 검증 결과 (R-16) — NL 편집 ("4번 삭제") 이 **fatal**. Sprint 14 A3 의 핵심 가치 (자유 대화 1차) 가 작동 X.

→ **schema 불일치 fatal 만 해소** 후 종결. 다른 ISSUE (002 / 011 / 013 / 015) 는 Sprint 15 묶음.

### 1.2 작업 원칙

- **Throwaway 의도** — 어댑터는 Sprint 15 D 단일화 시 폐기 예정 (의도된 임시)
- **Breaking change 0** — 기존 작동 경로 (직접 편집) 손대지 않음
- **검증 우선** — R-16/17/18 PASS 까지 = Sprint 14 A3 종결 조건

---

## 2. 작업 분해 — 5 sub-phase

### 2.1 의존성 그래프

```
C-1 코드 변경 (어댑터 + ws_hitl 수정 + 단위 테스트)
   ↓
C-2 브라우저 검증 (R-16/17/18)
   ↓
C-3 spec 점진 update (12 / 22 / INDEX / known_issues)
   ↓
C-4 ADR-010 본문 (Sprint 15 D 권고 박제)
   ↓
C-5 Sprint 14 A3 완료 보고서
```

### 2.2 시간 추정

| Sub-phase | 시간 | 누적 |
|-----------|------|------|
| C-1 코드 변경 | 1h | 1h |
| C-2 브라우저 검증 | 30min | 1.5h |
| C-3 spec update | 30min | 2h |
| C-4 ADR-010 본문 | 30min | 2.5h |
| C-5 완료 보고서 | 15min | 2.75h |
| **합계** | | **~3h** |

---

## 3. C-1: 코드 변경 (~1시간)

### 3.1 작업 1.1 — `plan_adapter.py` 신규

**경로**: `backend/app/dream_agent/workflow_managers/hitl_manager/plan_adapter.py`

**LoC**: ~80

**전체 코드**:

```python
"""Plan Adapter — Sprint 14 A3 임시 어댑터.

planner.Plan dict (PlannedTodo 형식) ↔ models.Plan (TodoItem 형식) 변환.

Status: complete — Sprint 14 A3 임시 fix.
폐기 예정: ADR-010 Sprint 15 D 단일화 시 (planner.Plan 으로 통일됨).

Reference:
- docs/reports/sprint14_a3_research_q1_plan_schema.md §6 어댑터 설계
- docs/agent_specs/adr/ADR-010_plan_schema_unification.md
"""

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import Plan, TodoItem

logger = get_logger(__name__)


def planner_dict_to_models_plan(plan_dict: dict[str, Any], session_id: str) -> Plan:
    """planner.Plan dict → models.Plan 변환.

    매핑:
        PlannedTodo.task_type → TodoItem.task (rationale 우선)
        PlannedTodo.rationale → TodoItem.description
        plan.dag → plan.dependency_graph
        plan.teams_selected / plan_notes → 정보 손실 (warning 로그)

    Args:
        plan_dict: planner.Plan.model_dump() 결과 (progress.plan 형식)
        session_id: Plan.session_id 채울 값

    Returns:
        models.Plan instance
    """
    if plan_dict.get("teams_selected") or plan_dict.get("plan_notes"):
        logger.warning(
            "plan_adapter: teams_selected/plan_notes 정보 손실",
            session_id=session_id,
        )

    todos: list[TodoItem] = []
    for pt in plan_dict.get("todos", []):
        todos.append(
            TodoItem(
                id=pt["id"],
                plan_id=session_id,
                task=pt.get("rationale") or pt.get("task_type") or "Unknown task",
                description=pt.get("rationale"),
                tool=pt.get("tool") or "unknown",  # validator (not empty) 통과
                tool_params=pt.get("tool_params") or {},
                agent=pt.get("agent") or "",
                depends_on=pt.get("depends_on") or [],
                priority=pt.get("priority", 5),
            )
        )

    return Plan(
        plan_id=session_id,
        session_id=session_id,
        version=plan_dict.get("version", 1),
        todos=todos,
        dependency_graph=plan_dict.get("dag", plan_dict.get("dependency_graph", {})),
    )


def models_plan_to_planner_dict(plan: Plan) -> dict[str, Any]:
    """models.Plan → planner.Plan dict 역변환.

    매핑:
        TodoItem.task → PlannedTodo.rationale (사용자 표시 우선)
        plan.dependency_graph → plan.dag
        TodoItem.status / lifecycle metadata → 정보 손실

    Args:
        plan: NL 편집 후 models.Plan instance

    Returns:
        planner.Plan dict (progress.plan 에 저장 가능한 형식)
    """
    return {
        "teams_selected": [],  # 어댑터 라운드트립 시 손실
        "todos": [
            {
                "id": t.id,
                "task_type": t.task,  # 의미 어긋남 (warning) — Sprint 15 D 시 정정
                "agent": t.agent or None,
                "tool": t.tool if t.tool != "unknown" else None,
                "tool_params": dict(t.tool_params),
                "depends_on": list(t.depends_on),
                "priority": t.priority,
                "rationale": t.task,
            }
            for t in plan.todos
        ],
        "dag": dict(plan.dependency_graph),
        "plan_notes": "",
    }
```

**Acceptance**:
- [ ] 파일 생성
- [ ] `Status: complete — Sprint 14 A3 임시 fix...` 마커 명시
- [ ] 양방향 함수 모두 정의
- [ ] 정보 손실 시 warning 로그

### 3.2 작업 1.2 — `ws_hitl.py` 수정

**경로**: `backend/api_v2/ws_hitl.py`

**LoC**: ~10 (변경)

**Diff** (의도):

```python
# 추가 import (line 466 근처, 다른 import 들과 함께):
from app.dream_agent.workflow_managers.hitl_manager.plan_adapter import (
    planner_dict_to_models_plan,
    models_plan_to_planner_dict,
)

# 변경 1 — line 507:
# Before:
plan_pydantic = Plan.model_validate(progress.plan)
# After:
plan_pydantic = planner_dict_to_models_plan(progress.plan, session_id)

# 변경 2 — line 591:
# Before:
new_plan_dict = new_plan_pydantic.model_dump(mode="json")
# After:
new_plan_dict = models_plan_to_planner_dict(new_plan_pydantic)
```

**Acceptance**:
- [ ] 3 변경 (import + L507 + L591) 적용
- [ ] 기존 import 의 `Plan` 은 그대로 유지 (다른 지점 사용)
- [ ] 코멘트 추가: `# Sprint 14 A3 어댑터 — ADR-010 Sprint 15 D 단일화 시 변경 예정`

### 3.3 작업 1.3 — 단위 테스트 신규

**경로**: `backend/tests/sprint14/test_a3_plan_adapter_unit.py`

**LoC**: ~80

**테스트 케이스** (5 TC):

```python
"""Plan Adapter 단위 테스트 — Sprint 14 A3 R-16 fatal fix.

Status: complete — Sprint 14 A3.
"""

import pytest

from app.dream_agent.models import Plan, TodoItem
from app.dream_agent.workflow_managers.hitl_manager.plan_adapter import (
    planner_dict_to_models_plan,
    models_plan_to_planner_dict,
)


@pytest.fixture
def planner_dict_sample() -> dict:
    """planner.Plan.model_dump() 샘플 — 실제 progress.plan 형식."""
    return {
        "teams_selected": ["analysis_team"],
        "todos": [
            {
                "id": "todo_001",
                "task_type": "data_collection",
                "agent": "collection_agent",
                "tool": "naver_collector",
                "tool_params": {"brand": "블루밍글로우"},
                "depends_on": [],
                "priority": 1,
                "rationale": "네이버 리뷰 수집",
            },
            {
                "id": "todo_002",
                "task_type": "data_preprocessing",
                "agent": "preprocessing_agent",
                "tool": "format_normalizer",
                "tool_params": {},
                "depends_on": ["todo_001"],
                "priority": 2,
                "rationale": "정규화",
            },
        ],
        "dag": {"todo_002": ["todo_001"]},
        "plan_notes": "수집 → 정규화",
    }


def test_TC_PA_01_planner_dict_to_models_plan_all_fields(planner_dict_sample):
    """TC-PA-01: planner dict → models.Plan 모든 필드 매핑 정확."""
    plan = planner_dict_to_models_plan(planner_dict_sample, "session_xyz")
    assert plan.session_id == "session_xyz"
    assert plan.plan_id == "session_xyz"
    assert plan.version == 1
    assert len(plan.todos) == 2
    assert plan.todos[0].id == "todo_001"
    assert plan.todos[0].task == "네이버 리뷰 수집"  # rationale 우선
    assert plan.todos[0].description == "네이버 리뷰 수집"
    assert plan.todos[0].tool == "naver_collector"
    assert plan.todos[0].tool_params == {"brand": "블루밍글로우"}
    assert plan.todos[0].agent == "collection_agent"
    assert plan.todos[0].priority == 1
    assert plan.dependency_graph == {"todo_002": ["todo_001"]}


def test_TC_PA_02_models_plan_to_planner_dict_round_trip(planner_dict_sample):
    """TC-PA-02: 양방향 변환 round-trip 데이터 보존."""
    plan = planner_dict_to_models_plan(planner_dict_sample, "session_xyz")
    new_dict = models_plan_to_planner_dict(plan)
    assert len(new_dict["todos"]) == 2
    assert new_dict["todos"][0]["id"] == "todo_001"
    assert new_dict["todos"][0]["tool"] == "naver_collector"
    assert new_dict["todos"][0]["tool_params"] == {"brand": "블루밍글로우"}
    assert new_dict["todos"][0]["depends_on"] == []
    assert new_dict["dag"] == {"todo_002": ["todo_001"]}


def test_TC_PA_03_tool_missing_default_unknown():
    """TC-PA-03: tool 누락 시 'unknown' default — TodoItem.tool validator 통과."""
    pd = {
        "teams_selected": [],
        "todos": [{"id": "todo_001", "task_type": "x", "rationale": "y"}],
        "dag": {},
    }
    plan = planner_dict_to_models_plan(pd, "s1")
    assert plan.todos[0].tool == "unknown"


def test_TC_PA_04_rationale_missing_uses_task_type():
    """TC-PA-04: rationale 누락 시 task_type 사용."""
    pd = {
        "teams_selected": [],
        "todos": [{"id": "t1", "task_type": "data_collection"}],
        "dag": {},
    }
    plan = planner_dict_to_models_plan(pd, "s1")
    assert plan.todos[0].task == "data_collection"


def test_TC_PA_05_dag_dependency_graph_bidirectional():
    """TC-PA-05: dag ↔ dependency_graph 양방향."""
    pd = {
        "teams_selected": [],
        "todos": [{"id": "t1", "task_type": "x"}, {"id": "t2", "task_type": "y", "depends_on": ["t1"]}],
        "dag": {"t2": ["t1"]},
    }
    plan = planner_dict_to_models_plan(pd, "s1")
    assert plan.dependency_graph == {"t2": ["t1"]}
    new_dict = models_plan_to_planner_dict(plan)
    assert new_dict["dag"] == {"t2": ["t1"]}
```

**Acceptance**:
- [ ] 5 TC 모두 통과
- [ ] `pytest backend/tests/sprint14/test_a3_plan_adapter_unit.py -v` PASS
- [ ] 전체 자동 테스트 244+ passed (기존 239 + 신규 5)

---

## 4. C-2: 브라우저 검증 (~30분)

### 4.1 환경 준비

```bash
# 서버 기동
uv run python run_server_v2.py

# 브라우저
http://localhost:8001/dashboard
F12 → Console + Network (ws 필터) 열어두기
```

### 4.2 R-16 — NL 삭제

**시나리오**:
1. 새 쿼리: `"블루밍글로우 네이버 리뷰 분석"` (성공한 케이스)
2. Plan review 모달 자동 팝업 대기
3. 🗣 textarea: `"4번 삭제"` 입력
4. **[⚡ 적용]** 클릭

**검증 포인트**:
- [ ] textarea 비활성화 (로딩 중)
- [ ] 1~3초 후 ack 수신
- [ ] F12 Console: `[hitl] ack: { accepted: true, nl_action: "remove", invalidated: [...], plan: ... }`
- [ ] 모달에서 4번 todo 삭제됨
- [ ] downstream 🔴 tint
- [ ] textarea 초기화
- [ ] "✓ remove 적용됨" 토스트

**서버 로그 확인**:
- [ ] `Parsing plan edit instruction instruction="4번 삭제"`
- [ ] LLM 호출 (planning client)
- [ ] `todo_edit_nl applied` info 로그
- [ ] **`plan dict → Pydantic 변환 실패` warning 없음** ← 핵심

**FAIL 시 진단**:
- 어댑터 import 누락 → `ws_hitl.py` 라인 466 확인
- TodoItem validator 실패 → tool="unknown" default 확인
- LLM 응답 unknown → R-18 경로

### 4.3 R-17 — NL 순서 변경

**시나리오**:
1. 모달 (R-16 후 또는 새 쿼리)
2. 🗣 textarea: `"3번과 4번 순서 바꿔"`
3. **[⚡ 적용]**

**검증 포인트**:
- [ ] ack `accepted: true, nl_action: "reorder"`
- [ ] UI 에서 3번/4번 위치 교환
- [ ] depends_on 영향 시 invalidated

### 4.4 R-18 — NL 파싱 실패 UX

**시나리오**:
1. 모달
2. 🗣 textarea: `"asdf xyz 123"`
3. **[⚡ 적용]**

**검증 포인트**:
- [ ] ack `accepted: false, code: "NL_INTENT_UNCLEAR"`
- [ ] 한국어 토스트 ("⚠️ 어떤 작업을 원하시는지 이해하지 못했습니다...")
- [ ] textarea 내용 보존 (재시도 가능)
- [ ] 모달 유지

### 4.5 결과 기록

**파일**: `docs/reports/sprint14_a3_test_log.md`

세션 #2 추가:
```markdown
## 세션 #2 — 2026-04-XX (도윤 + Claude)

### 환경
- 커밋 SHA: <Phase C-1 커밋>
- 브라우저: Chrome <version>

### A3 NL 시나리오 (B 어댑터 적용 후 재검증)
| ID | 결과 | 비고 |
|----|------|------|
| R-16 | ✅/❌ | nl_action: "remove" 확인 |
| R-17 | ✅/❌ | nl_action: "reorder" 확인 |
| R-18 | ✅/❌ | NL_INTENT_UNCLEAR 확인 |
```

**Acceptance**:
- [ ] R-16/17/18 모두 ✅ PASS
- [ ] `sprint14_a3_test_log.md` 세션 #2 추가됨

---

## 5. C-3: spec 점진 update (~30분)

### 5.1 작업 3.1 — `12_manager_layer_v1.4.md` 신규

**경로**: `docs/agent_specs/12_manager_layer_v1.4.md` (기존 v1.3 그대로 두고 v1.4 신규)

**변경점** (v1.3 → v1.4):
- `_handle_todo_edit_nl` 의 `plan_adapter` 사용 명시 (어댑터 함수 위치 + 매핑 정책)
- "dict ↔ Pydantic 경계" 섹션 추가 — Sprint 14 A3 임시 정책
- "ADR-010 Sprint 15 D 단일화 시 폐기 예정" 표기
- 변경 이력에 v1.4 entry 추가

**Acceptance**:
- [ ] v1.4 파일 신규 (v1.3 도 그대로 둠 — inline 공존)
- [ ] §어댑터 정책 신규 섹션
- [ ] Sprint 15 폐기 예정 명시

### 5.2 작업 3.2 — `22_error_codes_v1.2.md` 신규 (선택)

**경로**: `docs/agent_specs/22_error_codes_v1.2.md` (또는 v1.1 유지)

**판단 기준**:
- 어댑터로 fallback 가능 → 신규 error code 불필요 → **v1.2 신규 안 함**
- 어댑터 변환 자체가 fail 가능 → 신규 코드 (`PLAN_SCHEMA_MISMATCH`) → v1.2 신규

**현 상태 판단**: 어댑터 함수가 모든 케이스 처리 (warning 로그만). **v1.2 신규 X**.

**대안**: known_issues 에 "어댑터 schema 누락 케이스 → 향후 ADR-010 D 단일화로 해소" 기록만.

**Acceptance**:
- [x] v1.2 신규 안 함 (조건부)
- [ ] known_issues 갱신 (대안)

### 5.3 작업 3.3 — `INDEX.md` 갱신

**경로**: `docs/agent_specs/INDEX.md`

**변경**:
- 12 항목: v1.3 → v1.4 표기 (또는 둘 다 표기)
- 상태 마커: "Sprint 14 A3 종결 + 어댑터 추가" 표기

**Acceptance**:
- [ ] INDEX 갱신
- [ ] v 버전 일관성

### 5.4 작업 3.4 — `known_issues.md` 갱신

**경로**: `docs/reports/sprint14_a3_known_issues.md`

**변경**:
- ISSUE-016 → ✅ 해결 표기 (어댑터 + Sprint 15 D 단일화 예정)
- ISSUE-002 (Cognitive enum) — Phase C 에서 다루지 않음 / Sprint 15 묶음 표기

**Acceptance**:
- [ ] ISSUE-016 해결 표기
- [ ] 변경 이력 entry 추가

---

## 6. C-4: ADR-010 본문 작성 (~30분)

### 6.1 파일 생성

**경로**: `docs/agent_specs/adr/ADR-010_plan_schema_unification.md`

### 6.2 본문 골격 (Q1 §7 권고 박제)

```markdown
# ADR-010: Plan/Todo Schema 통합

## Status

Accepted (2026-04-XX) — Sprint 14 A3 어댑터 임시 / Sprint 15 P0 D 단일화 본격

## Context

POC 1차 검증 (R-16) 으로 NL 편집 fatal 발견:
- 활성 코드에 3 Plan 클래스 + 2 Todo 클래스 공존
- planner.Plan / planner.PlannedTodo (LLM 출력 raw)
- models.Plan / models.TodoItem (canonical 풀 lifecycle)
- 데이터 흐름: progress.plan = planner 형식 dict / plan_editor = models.Plan 기대 → 변환 fatal

상세: [`docs/reports/sprint14_a3_research_q1_plan_schema.md`](../../reports/sprint14_a3_research_q1_plan_schema.md)

## Decision

### Sprint 14 A3 (Phase C, 임시): Option B — 어댑터 layer

`backend/app/dream_agent/workflow_managers/hitl_manager/plan_adapter.py` 신규.
양방향 변환 함수 — `_handle_todo_edit_nl` 입출력 지점에서 사용.

### Sprint 15 P0 (Phase E-1 직전): Option D — planner.Plan 으로 통일

- `models.Plan` / `models.TodoItem` 폐기 (또는 deprecation)
- `plan_editor.py` 가 `planner.Plan` + `planner.PlannedTodo` 사용
- 어댑터 (`plan_adapter.py`) 폐기

### 선택 근거 (D vs A vs C)

- A (models 통일): LLM prompt 변경 → 회귀 위험 큼
- C (단계적): B → A. POC 단계 lifecycle metadata (status/versions/timestamps) 불필요
- **D**: A 보다 가벼움 (LoC 절반), POC 적합. Sprint 16+ 본격 production 시 PlannedTodo 확장으로 lifecycle 추가 가능

## Consequences

### 좋은 점
- Sprint 14 A3 즉시 NL 편집 작동 (어댑터)
- Sprint 15 본격 단일화로 schema 부채 해소
- LLM prompt 변경 0 (D 채택 이유)

### 나쁜 점 / 비용
- 어댑터 = throwaway 코드 (~80 LoC). 의도된 것
- planner.Plan 의 lifecycle metadata 부재 — Sprint 16+ 필요 시 확장

### 위험
- 어댑터 round-trip 정보 손실 (rationale ↔ description, task ↔ task_type) — POC 단계 무해
- D 단일화 마이그레이션 (~5 파일 / ~150 LoC) — Sprint 15 P0

## Alternatives Considered

[Q1 자료 §5 참조]

- A models 통일 — 큰 마이그레이션 + LLM prompt 변경
- B 영구 어댑터 — 변환 부담 영구
- C 단계적 (B → A) — A 선택 시 D 와 동일 부담

## Related

- 사전 조사: `docs/reports/sprint14_a3_research_q1_plan_schema.md`
- 어댑터 구현: `backend/app/dream_agent/workflow_managers/hitl_manager/plan_adapter.py`
- ADR-015 메모리 architecture (schema 영향)
- ADR-002 NL 점진 고도화 (편집 경로)

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-XX | 초안 + Accepted. Sprint 14 A3 B 어댑터 + Sprint 15 P0 D 단일화 결정 |
```

**Acceptance**:
- [ ] ADR-010 파일 생성
- [ ] Status / Context / Decision / Consequences / Alternatives / Related 모두 작성
- [ ] ADR INDEX 갱신 (새 행 추가)

---

## 7. C-5: Sprint 14 A3 완료 보고서 (~15분)

### 7.1 파일 생성 / 업데이트

**경로**: `docs/reports/sprint14_a3_completion_report_v1.1.md` (또는 기존 보고서 v1.1 bump)

### 7.2 본문 핵심 섹션

- §1 검증 결과 (R-1~R-8 + R-16~R-18 모두 PASS)
- §2 9 ISSUE 상태 (해결 / 보류 / Sprint 15 묶음)
- §3 POC 1차 산출물 = "한계 측정 + NL 작동 + 다음 단계 trigger 식별"
- §4 Sprint 15 (POC 2차) 진입 준비 완료 표기
- §5 다음 작업 link (`sprint15_phase_d_adr.md`)

**Acceptance**:
- [ ] 보고서 작성
- [ ] Sprint 14 A3 종결 선언

---

## 8. 검증 / 테스트 strategy

### 8.1 자동 테스트

```bash
# 어댑터 단위 테스트만
pytest backend/tests/sprint14/test_a3_plan_adapter_unit.py -v

# 전체 (회귀 확인)
pytest backend/tests/ -v --tb=short
```

**기대**: 244+ passed (기존 239 + 신규 5).

### 8.2 브라우저 검증

C-2 §4 의 R-16/17/18 시나리오.

### 8.3 DC 검증 (계약 / 문서 일관성)

```bash
pytest backend/tests/test_doc_contracts.py -v
```

**기대**: DC-5 통과. DC-4 archived 잔여는 그대로.

---

## 9. Risk + 완화

| Risk | 완화 |
|------|------|
| 어댑터 매핑 오류 (rationale ↔ task) | 단위 테스트 5 TC 로 검증 |
| 어댑터 round-trip 정보 손실 | warning 로그 + ADR-010 본문에 명시 |
| TodoItem validator (tool not empty) 실패 | "unknown" default |
| Sprint 15 D 단일화 시 어댑터 throwaway 비용 | 의도된 임시. ADR-010 에 박제 |
| R-17 reorder 가 다른 sub-flow → 어댑터 영향? | apply_edit reorder 분기는 todos 만 조작. 어댑터 무관 |
| LLM 응답 변동 (R-18 unknown vs remove 경계) | parse_instruction 의 action="unknown" 처리 |

---

## 10. 완료 체크리스트

### C-1 코드 변경
- [ ] `plan_adapter.py` 신규 (~80 LoC)
- [ ] `ws_hitl.py` 3 변경 (import + L507 + L591)
- [ ] `test_a3_plan_adapter_unit.py` 신규 (5 TC)
- [ ] 자동 테스트 244+ passed

### C-2 브라우저 검증
- [ ] R-16 ✅ PASS
- [ ] R-17 ✅ PASS
- [ ] R-18 ✅ PASS
- [ ] `sprint14_a3_test_log.md` 세션 #2 추가

### C-3 spec update
- [ ] `12_manager_layer_v1.4.md` 신규
- [ ] `22_error_codes_v1.2.md` skip (또는 신규)
- [ ] `INDEX.md` 갱신
- [ ] `sprint14_a3_known_issues.md` ISSUE-016 해결

### C-4 ADR-010 본문
- [ ] `ADR-010_plan_schema_unification.md` 신규
- [ ] ADR INDEX 갱신

### C-5 완료 보고서
- [ ] `sprint14_a3_completion_report_v1.1.md`
- [ ] Sprint 14 A3 종결 선언

### Phase C 종합
- [ ] 모든 sub-phase 완료
- [ ] 커밋 (`fix(sprint14): A3 NL fatal 해소 — B 어댑터 + ADR-010` 권장)
- [ ] 다음 [`sprint15_phase_d_adr.md`](./sprint15_phase_d_adr.md) 진입

---

## 11. 다음 Phase 연결

Phase C 완료 후 → **Phase D**: ADR 본문 작성 (메모리 + Clarification 통합 architecture)

[`sprint15_phase_d_adr.md`](./sprint15_phase_d_adr.md) 참조.

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-28 | 초안 — Phase C 5 sub-phase 세부 작업 카탈로그. 코드 / 테스트 / 검증 / 문서 / ADR 모든 작업 정의 |
