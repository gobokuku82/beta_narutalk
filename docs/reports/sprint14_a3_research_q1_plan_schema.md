# Sprint 14 A3 — Q1 사전 조사: Plan/Todo Schema 현황 매핑

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-28 |
| 작성자 | Claude (코드 전수 조사 기반) |
| 자매 문서 | [`sprint14_a3_poc1_settlement.md`](./sprint14_a3_poc1_settlement.md) §3.3 / §4.2 / [`sprint14_a3_poc1_deliverables.md`](./sprint14_a3_poc1_deliverables.md) Q1 |
| 목적 | ADR-010 결정 입력 자료 — Plan/Todo schema 단일화 / 어댑터 / 단계적 / 폐기 옵션 비교 |
| 본 문서 위치 | `docs/reports/sprint14_a3_research_q1_plan_schema.md` |

---

## 0. 본 문서의 역할

**Q1 결정 ("ADR-010 옵션") 의 객관적 자료** — 의견 ≠ 사실. 사실 위주. 권고는 § 7 에 분리.

조사 범위: 활성 코드만 (`backend/app/dream_agent/_old_v1/`, `backend/_old/`, `backend/_domains/` 제외).

---

## 1. 클래스 정의 — 4개 (실제로는 2 + 2)

### 1.1 `models.plan.Plan` (canonical 풀 라이프사이클)

**위치**: `backend/app/dream_agent/models/plan.py:44`

**필드**:
```python
class Plan(BaseModel):
    plan_id: str             # default UUID
    session_id: str          # required
    version: int = 1
    status: PlanStatus       # enum (DRAFT/...)
    todos: list[TodoItem]    # canonical TodoItem
    dependency_graph: dict[str, list[str]]
    estimated_duration_sec: int = 0
    estimated_cost_usd: float = 0.0
    mermaid_diagram: Optional[str]
    versions: list[PlanVersion]
    changes: list[PlanChange]
    intent_summary: str = ""
    created_at / approved_at / started_at / completed_at: datetime
```

→ **15+ 필드, 풀 lifecycle metadata + history**.

### 1.2 `models.todo.TodoItem` (canonical, frozen)

**위치**: `backend/app/dream_agent/models/todo.py:32`

**필드 (필수만)**:
```python
class TodoItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    id: str = ...                # default UUID
    plan_id: Optional[str]
    task: str                    # ★ required
    description: Optional[str]
    tool: str                    # ★ required (validator: not empty)
    tool_params: dict[str, Any]
    agent: str = ""
    status: Literal[...]         # default "pending"
    priority: int = 5            # 0~10
    depends_on: list[str]
    timeout_sec: int = 300
    requires_approval: bool = False
    result / error_message / created_at / started_at / completed_at / version
```

→ **20+ 필드, frozen (immutable), 풀 lifecycle**.

### 1.3 `planner.Plan` (planner LLM 출력 전용)

**위치**: `backend/app/dream_agent/planning/planner.py:50`

**필드**:
```python
class Plan(BaseModel):
    teams_selected: list[str]    # planner Stage 1 결과
    todos: list[PlannedTodo]
    dag: dict[str, list[str]]    # ⚠ "dependency_graph" 아님
    plan_notes: str = ""
```

→ **4 필드. minimal. session_id / status / version 없음**.

### 1.4 `planner.PlannedTodo` (planner 출력 전용)

**위치**: `backend/app/dream_agent/planning/planner.py:37`

**필드**:
```python
class PlannedTodo(BaseModel):
    id: str                       # ★ required
    task_type: str                # ★ required (≠ models.TodoItem.task)
    team: str | None
    agent: str | None
    tool: str | None              # nullable (≠ models.TodoItem.tool 필수)
    tool_params: dict[str, Any]
    depends_on: list[str]
    priority: int = 1             # default 1 (≠ TodoItem default 5)
    rationale: str = ""           # 사용자 표시용
```

→ **9 필드. minimal. status / timestamps / lifecycle 없음**.

---

## 2. 필드 충돌 매트릭스

### 2.1 Plan 클래스 비교

| 필드 | models.Plan | planner.Plan | 충돌 |
|------|------------|------------|------|
| 식별 | `plan_id` (default UUID) + `session_id` (필수) | (없음) | ❌ session_id 누락 |
| `version` | int | (없음) | 변환 시 default |
| `status` | enum PlanStatus | (없음) | 변환 시 default |
| Todos | `list[TodoItem]` | `list[PlannedTodo]` | 🔥 **타입 충돌** |
| DAG | `dependency_graph` | `dag` | 🔥 **이름 충돌** |
| Stage1 결과 | (없음) | `teams_selected` | 정보 손실 |
| 노트 | (없음) | `plan_notes` | 정보 손실 |
| Lifecycle (estimated_*, created_at, etc.) | 多 (15+) | (없음) | 변환 시 default |
| History (versions, changes) | list | (없음) | 정보 손실 |

→ **두 모델은 conceptually 다른 것**: planner.Plan = LLM 출력 raw / models.Plan = 풀 lifecycle entity.

### 2.2 Todo 클래스 비교

| 필드 | models.TodoItem | planner.PlannedTodo | 충돌 |
|------|--------------|----------|------|
| `id` | default UUID | ★ required | minor |
| 작업 설명 | `task` ★ required | (없음) | 🔥 **누락** |
| 작업 분류 | (없음) | `task_type` ★ required | 🔥 **누락** |
| 사용자 표시 | `description` | `rationale` | 🔥 **이름 + 의미 충돌** |
| `tool` | ★ required (validator: not empty) | nullable | 🔥 **필수 vs nullable** |
| `agent` | "" default | nullable | minor |
| `status` | enum default "pending" | (없음) | 변환 시 default |
| `priority` | 5 default (0~10) | 1 default | minor |
| Lifecycle | 多 (timestamps, result, error_message) | (없음) | 정보 손실 |

→ **두 Todo 도 conceptually 다른 것**: PlannedTodo = LLM 출력 raw / TodoItem = 실행 + 결과 + history.

---

## 3. 사용 위치 매트릭스

### 3.1 활성 코드 (각 클래스)

#### `models.Plan` 사용
| 파일 | 용도 | 라인 |
|------|------|------|
| `models/__init__.py` | export | — |
| `models/plan.py` | 정의 | 44 |
| `workflow_managers/hitl_manager/plan_editor.py` | NL edit 입력/출력 | 17, 188 |
| `api_v2/ws_hitl.py` | NL handler | 464, **507 (FATAL)** |
| `tests/sprint14/test_a3_plan_editor_nl_unit.py` | 단위 테스트 | 21 |
| `tests/sprint14/test_a3_plan_review_edit_integration.py` | 통합 테스트 | — |
| `scripts/a3_nl_success_rate.py` | NL D-14 측정 | 63 |

→ **NL edit 경로 전용**. 6 파일.

#### `planner.Plan` 사용
| 파일 | 용도 | 라인 |
|------|------|------|
| `planning/planner.py` | 정의 | 50 |
| `planning/planning_stage.py` | LangGraph node import | 1 |
| `execution/execution_stage.py` | progress.plan validate | 42, **173, 209** |
| `execution/executor.py` | 실행 시 todo 처리 | — |
| `tests/sprint14/test_a3_todo_manager_unit.py` | 단위 테스트 | — |

→ **planning + execution 경로 전용**. 5 파일.

#### `models.TodoItem` 사용
| 파일 | 용도 |
|------|------|
| `models/todo.py` | 정의 |
| `models/__init__.py` | export |
| `models/plan.py` | Plan.todos 타입 |
| `workflow_managers/hitl_manager/plan_editor.py` | NL edit todo 생성 |
| `tests/sprint14/test_a3_plan_editor_nl_unit.py` | 테스트 |
| `tests/sprint14/test_a3_plan_review_edit_integration.py` | 테스트 |
| `scripts/a3_nl_success_rate.py` | NL 측정 |

→ **NL edit + plan_editor 전용**. 7 파일.

#### `planner.PlannedTodo` 사용
| 파일 | 용도 |
|------|------|
| `planning/planner.py` | 정의 |
| `workflow_managers/todo_manager/manager.py` | dict 처리 (간접 — `task_type` setdefault 등) |
| `execution/executor.py` | 실행 시 |
| `tests/sprint14/test_a3_todo_manager_unit.py` | 테스트 |

→ **planning + execution + todo_manager 전용**. 4 파일.

### 3.2 데이터 흐름 시각화

```
사용자 쿼리
    ↓
Cognitive (StructuredQuery 출력)
    ↓
Planning [planner.Plan / PlannedTodo 생성]
    ↓
plan.model_dump(mode="json") → plan_dict
    ↓
HITLManager.create_progress(plan_dict)
    ↓
progress.plan = plan_dict   ← planner.Plan 형식 dict
    ↓
        ┌─────────┴────────────────────────┐
        │                                  │
   Execution path                  HITL edit path
   ────────────────────             ─────────────────
   plan = planner.Plan              plan = models.Plan
        .model_validate(progress.plan)  .model_validate(progress.plan)  ← 🔥 FATAL
   ✅ 작동                          ❌ schema 불일치
                                    
                                    todo_manager (dict 직접 조작) ✅ 작동
                                    plan_editor (Pydantic 기반) ❌ 차단
```

→ **progress.plan = planner.Plan 형식**. execution 은 같은 형식이라 OK. plan_editor 는 다른 형식 기대 → fatal.

---

## 4. 변환 지점 매핑

### 4.1 작동 중 (정상)

| 위치 | 변환 | 이유 |
|------|------|------|
| `planner.py:62` | `plan.model_dump(mode="json")` → dict | planner → progress 저장 |
| `execution_stage.py:173, 209` | `Plan.model_validate(progress.plan)` (planner.Plan) | 같은 형식 |
| `todo_manager/manager.py` 전반 | dict 직접 조작 | 형식 동일 가정 |
| `todo_manager.py:97` | `dag = plan.get("dag", plan.get("dependency_graph", {}))` | 양쪽 fallback (이미 schema 가교 일부 인지) |

### 4.2 FAIL (schema 불일치)

| 위치 | 변환 | 결과 |
|------|------|------|
| **`ws_hitl.py:507`** | `Plan.model_validate(progress.plan)` (models.Plan) | **9 validation errors** (session_id 누락 + todos[].task 누락 × 8) |
| (잠재) `plan_editor.apply_edit` 출력 | `models.Plan` 반환 → `model_dump` → progress.plan 교체 | progress.plan 형식이 모델 변경됨. execution_stage.py 재진입 시 더 이상 작동 안 할 가능성 |

### 4.3 잠재 충돌 (현재 안 일어나는 이유)

`ws_hitl.py:591`:
```python
new_plan_dict = new_plan_pydantic.model_dump(mode="json")
```

이 `new_plan_dict` 는 `models.Plan` 형식 (TodoItem). 이를 progress.plan 에 저장하면:
- 다음 execution_stage 진입 시 `Plan.model_validate(progress.plan)` (planner.Plan) → fatal 가능성
- 즉 **507 fatal 이 우연히 막아주는 부수 효과** — 만약 어댑터로 507 통과시키면 591 의 dump 가 후속 fatal 유발 가능

→ **어댑터는 양방향 (입력 + 출력) 둘 다 필요**.

---

## 5. 마이그레이션 옵션 — 4개 비교

### Option A — 단일화 (models.Plan 으로 통일)

**내용**: planner 가 `models.Plan` 출력. PlannedTodo 폐기.

**작업**:
- `planner.py`: Plan / PlannedTodo 정의 제거. `models.Plan` 사용. LLM JSON output schema 변경 (task_type → task, rationale → description, dag → dependency_graph)
- `planning/planning_stage.py`: import 변경
- `execution/execution_stage.py`: import 변경 (`from app.dream_agent.models import Plan`)
- `execution/executor.py`: PlannedTodo → TodoItem
- `todo_manager/manager.py`: `dag` / `dependency_graph` 통일 — `task_type` 처리 제거
- `LLM prompts/planning_stage3_todo.yaml`: schema 변경 (task_title → task)
- 테스트 모두 갱신
- **파일 수**: ~10
- **LoC 변경**: ~300~500
- **breaking changes**: LLM output schema (prompt + parse) — 가장 위험

**장점**: 가장 깔끔, 타입 안전성 ↑, 정보 손실 0
**단점**: 큰 마이그레이션, LLM prompt 변경 (테스트 회귀 위험)

### Option B — 어댑터 layer (Sprint 14 A3 임시 fix)

**내용**: planner.Plan / models.Plan 모두 유지. ws_hitl 입구에 양방향 변환 함수.

**작업**:
- 신규 파일: `backend/app/dream_agent/workflow_managers/hitl_manager/plan_adapter.py`
  - `planner_dict_to_models_plan(plan_dict, session_id) -> Plan`
  - `models_plan_to_planner_dict(plan: Plan) -> dict`
- `ws_hitl.py:507` 수정: `Plan.model_validate(progress.plan)` → `planner_dict_to_models_plan(progress.plan, session_id)`
- `ws_hitl.py:591` 수정: 변환 함수로 교체
- 단위 테스트: `test_a3_plan_adapter_unit.py` 신규
- **파일 수**: ~3 (1 신규 + ws_hitl + 테스트)
- **LoC 변경**: ~80~150
- **breaking changes**: 0

**장점**: 작은 변경, Sprint 14 A3 종결 즉시 가능, throwaway 의도라 본격 결정 보류 가능
**단점**: 변환 부담 영구. 두 schema 동거. 정보 손실 (rationale ↔ description 같은 의미 매핑은 lossy)

### Option C — 단계적 (B → A)

**내용**: B 어댑터로 Sprint 14 A3 종결 → Sprint 15 에서 A 단일화 → 어댑터 폐기.

**작업**:
- Sprint 14 A3: B 작업
- Sprint 15: A 작업 + adapter 제거

**장점**: 위험 분산, 사용자 결정 시간 확보
**단점**: 일정 길어짐, 두 번 작업

### Option D — 단일화 (planner.Plan 으로 통일)

**내용**: models.Plan 폐기. plan_editor 가 planner.Plan + PlannedTodo 사용.

**작업**:
- `models/plan.py` + `models/todo.py` 폐기 (또는 deprecation)
- `models/__init__.py`: Plan / TodoItem export 제거
- `plan_editor.py`: import 변경 (`from app.dream_agent.planning.planner import Plan, PlannedTodo`)
  - `apply_edit add 분기`: `TodoItem` → `PlannedTodo`
- `ws_hitl.py:464, 507`: import + validate 모두 planner 형식
- 테스트 갱신 (a3_nl_success_rate, test_a3_plan_editor_nl_unit, test_a3_plan_review_edit_integration)
- **파일 수**: ~5
- **LoC 변경**: ~100~200
- **breaking changes**: 작음 (canonical Plan 의 풀 lifecycle metadata 손실 — 현재도 안 쓰임)

**장점**: A 보다 가벼움 (LLM prompt 무변경), planner.Plan 이 더 단순
**단점**: 풀 lifecycle metadata (status, versions, changes, timestamps) 손실 — Sprint 16+ HITL history 기능 시 재작성 필요

### 5.1 비교 매트릭스

| 항목 | A (models 통일) | B (어댑터) | C (B → A) | D (planner 통일) |
|------|-----------|---------|---------|----------|
| 파일 수 | ~10 | ~3 | ~3 + ~10 | ~5 |
| LoC 변경 | ~300~500 | ~80~150 | 누적 | ~100~200 |
| LLM prompt 변경 | ✅ 필요 | ❌ | 단계적 | ❌ |
| breaking changes | 큼 | 0 | 분산 | 작음 |
| 정보 손실 | 0 | rationale 매핑 lossy | 0 (최종) | metadata 손실 |
| Sprint 14 A3 종결 가능성 | ❌ 위험 | ✅ 즉시 | ✅ 어댑터로 | 🟡 가능하나 큼 |
| 미래 lifecycle 기능 (status, versions) | ✅ 유지 | ✅ 유지 | ✅ 유지 | ❌ 재작성 필요 |
| 미래 LLM 재학습 비용 | ✅ 1회 | ❌ 영구 변환 | 1회 (최종) | ✅ 무 |
| 어댑터 함수 유지비 | 0 | 영구 | 임시 | 0 |

---

## 6. 어댑터 함수 설계 (Option B / C 선택 시)

```python
# backend/app/dream_agent/workflow_managers/hitl_manager/plan_adapter.py
"""Sprint 14 A3 임시 어댑터 — ADR-010 단일화 시 폐기."""

# ⚠️ DEPRECATED (2026-05-15 cleanup A3/A4 으로 삭제됨) — 활성: planning.planner.Plan/PlannedTodo
# from app.dream_agent.models import Plan, TodoItem   (원본 예시)
from typing import Any


def planner_dict_to_models_plan(plan_dict: dict[str, Any], session_id: str) -> Plan:
    """planner.Plan dict → models.Plan 변환.
    
    매핑:
        PlannedTodo.task_type → TodoItem.task (1차) — rationale 우선
        PlannedTodo.rationale → TodoItem.description
        plan.dag → plan.dependency_graph
        plan.teams_selected / plan_notes → 정보 손실 (warning 로그)
    """
    todos: list[TodoItem] = []
    for pt in plan_dict.get("todos", []):
        todos.append(TodoItem(
            id=pt["id"],
            plan_id=session_id,
            task=pt.get("rationale") or pt.get("task_type") or "Unknown task",
            description=pt.get("rationale"),
            tool=pt.get("tool") or "unknown",  # validator 통과를 위한 default
            tool_params=pt.get("tool_params") or {},
            agent=pt.get("agent") or "",
            depends_on=pt.get("depends_on") or [],
            priority=pt.get("priority", 5),
        ))
    
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
        TodoItem.description → (손실 — task 가 사용자 표시 역할)
        plan.dependency_graph → plan.dag
        TodoItem.status / lifecycle → 손실 (planner.Plan 에 없음)
    """
    return {
        "teams_selected": [],  # 손실
        "todos": [
            {
                "id": t.id,
                "task_type": t.task,  # 임시 — task_type 의미와 다름 (warning)
                "agent": t.agent or None,
                "tool": t.tool if t.tool != "unknown" else None,
                "tool_params": dict(t.tool_params),
                "depends_on": list(t.depends_on),
                "priority": t.priority,
                "rationale": t.task,  # 사용자 표시
            }
            for t in plan.todos
        ],
        "dag": dict(plan.dependency_graph),
        "plan_notes": "",
    }
```

**알려진 정보 손실**:
- `teams_selected`, `plan_notes`: 변환 시 빈값
- `task_type` 재변환 시 의미 어긋남 (event labeling 부정확)
- `description` ↔ `rationale` 의미 매핑 불완전

→ **Sprint 14 A3 임시 fix 로는 OK**. 진짜 통합은 ADR-010 결정 후.

---

## 7. 권고 (의견)

### 7.1 Sprint 14 A3 종결 — Option B (어댑터)

**이유**:
- 1~2시간 작업으로 R-16/17/18 PASS
- breaking changes 0
- 미래 결정 (A/D) 어떤 쪽이든 throwaway 가능

**산출물**:
- `plan_adapter.py` 신규 (~80 LoC)
- `ws_hitl.py:507, 591` 수정 (~10 LoC)
- 단위 테스트 신규 (~50 LoC)

### 7.2 Sprint 15 ADR-010 본문 — Option D (planner.Plan 통일) **추천**

**이유**:
- A 보다 가벼움 (LoC 절반)
- LLM prompt 변경 없음 (회귀 위험 낮음)
- POC 단계엔 풀 lifecycle metadata (status/versions/changes/timestamps) **불필요**
- Sprint 16+ HITL history 기능 시 어차피 재설계 (지금 보존 의미 작음)
- TodoManager 가 이미 dict 직접 조작 — planner 형식 가정과 일관

**대안 D 의 단점 완화**:
- 풀 lifecycle 필요 시 PlannedTodo 에 timestamps / status / result 필드 점진 추가 (Sprint 16+)

### 7.3 옵션 A 가 적합한 시점

- Sprint 16~ 본격 production 진입 시 (lifecycle 필요)
- HITL history / replay / audit 기능 도입 시
- 그 전에는 D 가 합리적

### 7.4 옵션 C (단계적 B → A) 의 위치

D 채택 시 C 형태 변형 가능: B 어댑터 → Sprint 15 D 단일화. 기본 추천 흐름.

---

## 8. 결정 input 정리

ADR-010 본문에서 결정해야 할 항목:

| 결정 | 옵션 |
|------|------|
| Sprint 14 A3 임시 fix | **B 어댑터 (권고)** / 다른 안 |
| Sprint 15 본격 통합 방향 | A (models 통일) / **D (planner 통일, 권고)** / B 영구 / 다른 안 |
| 어댑터 폐기 시점 | Sprint 15 P0 (단일화 직후) |
| 풀 lifecycle metadata (status/versions/timestamps) | 도입 시점 — Sprint 16+ |

---

## 9. 다음 단계

1. 사용자 본 자료 검토
2. Q3 (메모리 architecture) 자료 진입 — 메모리 schema 결정이 ADR-010 D 에 영향 가능 (PlannedTodo 의 lifecycle 필드 = 메모리 저장 단위?)
3. Q4 (Clarification UX) 자료 진입
4. 3 자료 종합 → ADR-010 + ADR-015 본문 결정 (Phase D)

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-28 | 초안 — 활성 코드 전수 조사. 4 클래스 정의 + 충돌 매트릭스 + 사용 위치 + 변환 지점 + 4 옵션 비교 + 어댑터 설계 + 권고 (B 어댑터 → D 통일) |
