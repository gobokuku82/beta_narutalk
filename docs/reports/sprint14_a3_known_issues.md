# Sprint 14 A3 — Known Issues (추후 수정 대기)

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-27 |
| 발견 시점 | R-5 브라우저 검증 (Phase 5 핵심 흐름 PASS 확인 후) |
| 정책 | 핵심 동작은 정상 작동하므로 즉시 수정 안 함. **별도 Sprint 또는 사용자 명시 결정 시 처리** |
| 상위 추적 | [`docs/agent_specs/adr/INDEX.md`](../agent_specs/adr/INDEX.md) "발견된 결정 누락" 표 |

---

## ISSUE-001 — UI stale: Plan review 편집 후 메인 파이프라인 카드 미갱신

### 증상

사용자가 Plan review 모달에서 todo 삭제 → 승인 → execution 진행 → 완료 후, **삭제된 todo 가 메인 파이프라인 카드에 그대로 표시됨**.

### 발견 시점

R-5 검증 (2026-04-27 15:05:14~45). 사용자 보고 + 서버 로그 분석으로 원인 확정.

### 근본 원인 (확정)

서버 로그 흐름:

```
15:05:14  첫 planning done todos=8         ← dashboard 메인 카드 8개 그림
15:05:18  todo_008 삭제 → hitl_ack         ← 모달 내 목록 7개로 갱신 (정상)
15:05:19  resume modify
15:05:30  두 번째 planning done todos=8    ← LangGraph 재실행, 8 todos 새로 생성
          planning modified by user        ← 그 후 user value(7 todos) 로 교체
15:05:30~ execution: 7 todos 실행          ← 백엔드는 정상
```

LangGraph 의 `interrupt()` 는 노드 함수를 **처음부터 재실행** 하되 `interrupt()` 호출 지점에 resume value 를 반환. 즉:

1. 첫 실행: planning_stage → stage1/2/3 LLM → plan 생성 → interrupt → 정지
2. resume(modify): planning_stage 처음부터 재실행 → stage1/2/3 LLM 다시 호출 → 새 8 todos plan 생성 → 그 후 interrupt() 가 user_decision 반환 → modify 분기 진입 → `plan_dict = user_decision["value"]` 로 7 todos 교체

문제는 **재실행 중 stage1/2/3 가 LangGraph chunk 로 emit 되고 ws_agent 가 이를 `node_event(planning, 8 todos)` 로 broadcast** → dashboard 가 메인 카드를 8개로 다시 그림.

execution 자체는 7 todos 로 정상 실행되지만 UI 는 8 todos 로 잘못 표시되고 갱신 안 됨.

### 영향

- **기능적 영향 없음** — execution 은 사용자 의도대로 7 todos 실행됨
- **UX 영향** — 사용자가 "내 삭제가 반영됐나?" 의문 가능. 결과 보고서 확인 후 안심하지만 잠깐 혼란

### 수정 방향 (3개 옵션)

| 옵션 | 위치 | 변경 | 장점 | 단점 |
|------|------|------|------|------|
| A | 백엔드 `planning_stage.py` | `if action=="modify" and value: skip LLM → plan_dict=value → goto execution` | 가장 깔끔, LLM 호출 절약 (3건 × 0.5~6초) | LangGraph 재실행 패턴 변경, 다른 분기 영향 검토 필요 |
| B | 프론트 `dashboard/index.html` | `handleEvent` 의 두 번째 `node_event(planning)` 무시 (modify 후 수신 시) | 백엔드 무변경 | dashboard JS 분기 추가, modify 직후 시점 추적 필요 |
| C | 백엔드 `_graph_runner_with_resume` 또는 `planning_stage` | modify 시 `node_event(planning)` emit 자체 skip | 변경 작음 | LangGraph chunk filter 추가 필요 |

**제 추천**: **옵션 A** — modify 시 LLM 재호출 자체가 낭비 (15:05:19~30, 약 11초 + LLM 비용). user 가 명시 modify value 보냈는데 LLM 다시 돌릴 이유 없음.

### 우선순위

- **중** — UX 영향만 있고 기능은 정상. R-7 재재검증 (2026-04-27, todo 추가) 이후 **사용자 추가 todo 가 메인 카드에 안 보임** 으로 임팩트 격상 → 해결됨

### 수정 (2026-04-27 사용자 인사이트로 단순 fix 발견 — 옵션 D 채택)

**사용자 표현**: "todo manager 가 todo 를 변경해서 frontend 에 쏴줘서 todo preview 와 todo board 양쪽 모두 갱신해주면 되는 거 아닌가?"

→ **정답**. 위 옵션 A/B/C 모두 과대 분석. 진짜 문제는 단순:
- `handleHitlAckTodo` 가 모달 (`renderHitlTodoList`) 만 갱신
- 메인 파이프라인 카드 (`renderTodoList`) 호출 누락

**옵션 D — handleHitlAckTodo 에 renderTodoList 1줄 추가**:
```javascript
if (data.plan && Array.isArray(data.plan.todos)) {
  ...
  renderHitlTodoList(...);  // 모달 갱신 (기존)
  renderTodoList(data.plan.todos);  // ISSUE-001 fix: 메인 파이프라인도 동일 plan 으로
}
```

이 패턴은 ISSUE-007 의 "책임 분리" 와 같은 정신: **편집 ack 받으면 모든 표시 영역 갱신**. backend / LangGraph 손대지 않음.

**상태**: ✅ 해결됨 (커밋 예정)

### 영역 명칭 (참고)

| 영역 | id | 표기 | 갱신 함수 |
|------|----|------|---------|
| 모달 (todo preview) | `hitl-overlay` 안 `hitl-plan-summary` | 편집 모달 | `renderHitlTodoList` |
| 메인 (todo board) | `todo-list` (영역 `todo-list-area`) | "📋 파이프라인 & 작업 현황" | `renderTodoList` |

### 관련

- ADR-001 hitl/pause 통합 (Phase 5)
- 코드: `dashboard/index.html::handleHitlAckTodo`
- 사용자 인사이트 (R-7 재검증 후): 표준 broadcast 패턴이 정답

---

## ISSUE-002 — Cognitive LLM enum validation 실패 (robust prompting)

### 증상

쿼리 "블루밍글로우 2024 Q3 리뷰 분석 **요약**해줘" → cognitive 단계에서 LLM 이 `goal.type='summary'` 반환 → Pydantic enum validation 실패 → cognitive fail → `complete(error)` 즉시 종료.

### 발견 시점

R-5 검증 직전 (2026-04-27 15:04:30~34) — 첫 시도 쿼리에서 발생. 두 번째 다른 쿼리는 정상 진행.

### 근본 원인 (서버 로그)

```
15:04:34 [error] cognitive failed
  error: 1 validation error for StructuredQuery
         goal.type
         Input should be 'answer','metric','insight','report','creative','mixed'
         [type=enum, input_value='summary', input_type=str]
```

→ LLM 이 사용자 입력의 "**요약**" 단어 영향으로 `goal.type='summary'` 반환. `summary` 는 enum 에 없음.

### 영향

- **기능적 영향 — 큼**: 특정 입력 패턴에서 cognitive 가 즉시 fail. 사용자에게 cryptic Pydantic error 노출
- POC 수준에선 흔하지만 MVP 진행 시 critical

### 수정 방향 (3개 옵션)

| 옵션 | 위치 | 변경 |
|------|------|------|
| A | `cognitive` prompt | enum 6개 명시 + 각 enum 사용 예시. "summary" 같은 단어가 들어와도 `report` 로 매핑되도록 가이드 |
| B | `cognitive_stage` post-validation | LLM 응답을 Pydantic 검증 전에 `summary→report`, `요약→report` 등 매핑 fallback 추가 |
| C | `StructuredQuery` enum | `summary` 를 enum 에 추가 |

**제 추천**: **A + B 조합** — A 는 근본 해결, B 는 fallback 안전망. C 는 모델 의미가 흐트러짐 (summary vs report 의미 차이).

### 우선순위

- **높** (POC 안정성). 다음 Sprint 우선 처리 권장. 사용자가 다양한 자연어 쓸 때 자주 만날 가능성

### 관련

- `backend/app/dream_agent/cognitive/cognitive_stage.py`
- `backend/app/dream_agent/models/structured_query.py` (StructuredQuery / GoalType enum)
- `backend/app/dream_agent/llm_manager/prompts/` (cognitive prompt YAML)
- ADR-009 LLM timeout 과 함께 처리 가능 (LLM client 안정성 묶음)

---

## ISSUE-004 — Plan review 모달 헤더 메시지 stale (보류)

### 증상

R-6 검증 (2026-04-27 16:22~25) — Plan review 모달 상단 헤더에 "**8개** Todo 실행 계획이 생성되었습니다. 승인하시겠습니까?" 표시되는데, todo_002 삭제 후에도 헤더는 "8개" 그대로. 실제 모달 내 표시 todo 는 7개 (정상).

### 발견 시점

R-6 검증 (2026-04-27 16:22:58 todo_delete 후). 사용자 스크린샷에서 직접 확인.

### 근본 원인

`dashboard/index.html::renderHitlTodoList` 가 모달 내부 todo 리스트만 갱신 + `renderCascade` 가 통계 바만 갱신. **모달 헤더 메시지 (`hitl-message`) 갱신 누락**.

ISSUE-007 의 책임 분리 fix 와 같은 패턴이지만 헤더만 빠진 케이스. 관련 코드:

```javascript
// openHitlModal 에서 한 번만 설정 후 갱신 안 함
$("hitl-message").textContent = payload.message || "실행 계획을 확인해주세요.";
```

→ 편집 ack 후 todo 개수 변경 시 헤더 메시지 갱신 안 함.

### 영향

- 기능 영향 0
- UX 약간의 혼란 — 헤더는 "8개" 인데 목록은 7개

### 수정 방향

`handleHitlAckTodo` 에서 plan 갱신 시 헤더 메시지도 갱신:
```javascript
const todoCount = data.plan.todos.length;
$("hitl-message").textContent = `${todoCount}개 Todo 실행 계획이 생성되었습니다. 승인하시겠습니까?`;
```

3줄 추가. ISSUE-007 fix 와 같은 책임 분리 패턴 확장.

### 우선순위

- **낮음** — UX 혼란만, 기능 영향 없음
- 마무리 시점 일괄 처리 또는 사용자 명시 요청 시

### 상태

🟡 보류 — known_issues 박제만, fix 안 함

### 관련

- ISSUE-007 (책임 분리 패턴 — 같은 fix 패턴)
- 코드: `dashboard/index.html::handleHitlAckTodo`, `openHitlModal`

---

## ISSUE-005 — `handle_todo_delete` 가 ack 에 `restart_from` 미포함 (해결됨)

### 증상

Plan review 모달에서 다중 todo 삭제 시 (R-6 시나리오), UI 에 ⛓ "Todo X 부터 재실행됩니다" 라벨이 표시 안 됨.

### 발견 시점

R-6 검증 (2026-04-27 16:22:58). F12 Console 에서 hitl_ack 의 `restart_from` 필드 자체가 없음을 확인.

### 근본 원인

[`hitl_manager/manager.py::handle_todo_delete`](../../backend/app/dream_agent/workflow_managers/hitl_manager/manager.py) 의 반환 dict 가 `restart_from` 필드 누락. `handle_todo_edit` 에는 있는데 delete 에서 빠뜨림. cascade 객체 자체엔 `restart_from` 가 있는데 dict 변환 시 누락.

### 수정

2026-04-27 즉시 fix: `handle_todo_delete` 의 return 에 `"restart_from": cascade.restart_from` 1줄 추가. Group H TE-H02 테스트에 검증 assertion 추가.

**상태**: ✅ 해결됨 (커밋 예정)

---

## ISSUE-006 — 도메인 의미적 검증 부재 + 사전 경고 부족 (Level A 부분 해결)

### 증상

사용자가 Plan review 단계에서 `format_normalizer` 같은 데이터 흐름 필수 todo 를 삭제 → execution 진행 → downstream 이 빈 입력으로 동작 → 보고서에 "데이터 0건" 표시.

### 발견 시점

R-6 검증 (2026-04-27 16:25:34~55). 사용자가 직접 도메인 인사이트 식별:
> "중간에 특정 todo 를 삭제하면 전체 구조가 바뀌는 부분은 고려를 못 했다. 삭제 이후에 다시 검증작업을 하는 로직이 필요할 것 같다."

### 근본 원인

시스템이 todo 의 **의미적 필수성** 을 모름:
- 구조적 검증 (`tm.validate(plan)`): DAG 순환 / depends_on 일관성만 검사 ✅ 구현됨
- **의미적 검증**: "이 todo 가 데이터 흐름 필수 단계인가?" ❌ 미구현
- **재계획**: 편집 후 cognitive/planning layer 재진입 ❌ 미구현

### 수정 — 3 레벨 단계적 접근 (ADR-002 NL 점진 고도화와 연동)

| 레벨 | 내용 | 시점 |
|------|------|------|
| **A — Prevention** (사전 경고) | 🗑 클릭 시 confirm 메시지에 downstream 영향 명시 | **2026-04-27 구현 ✅** |
| B — Validation (사후 LLM 검증) | 편집 후 LLM 호출로 "이 plan 으로 원본 의도 충족 가능?" 검사 | NL 2차 (Sprint 16+) |
| C — Reconciliation (자동 재계획) | cognitive layer 재진입 → 자동 보완 plan 제안 | NL 3차 (Sprint 18+) |

### Level A 구현 내역 (2026-04-27)

`dashboard/index.html`:
1. `_currentHitlPlan` 변수 추가 — 모달 열릴 때 / 편집 ack 받을 때 dag 정보 보존
2. `_calculateDownstreamForConfirm(todoId)` 함수 추가 — 백엔드 `calculate_cascade` 와 동일 BFS 로직을 클라이언트에서 동기 실행
3. 🗑 클릭 시 confirm 메시지 강화:
   ```
   ⚠️ 'todo_002' 삭제 시 총 7개 todo 가 무효화됩니다.
   영향받는 후속 todo:
     todo_003, todo_004, todo_005, todo_006, todo_007 외 2개
   이 단계가 데이터 흐름의 필수 노드라면 후속 단계가 빈 입력으로 동작할 수 있습니다.
   계속하시겠습니까?
   ```
4. 백엔드 무변경 — UX 개선만

**상태**: 🟡 Level A 해결, B/C 는 ADR-002 NL 2/3차 진행 시 검토

### 관련

- 사용자 인사이트 시점: 2026-04-27 R-6 검증 후
- Walkthrough §6.1 (Plan review 편집 흐름)
- ADR-002 (NL 점진 고도화 — 검증 로직 연동)
- 코드: `dashboard/index.html` `_calculateDownstreamForConfirm`, 편집 버튼 wire-up

---

## ISSUE-007 — `handleHitlAckTodo` 가 todo_add 후 모달 리스트 미갱신 (해결됨)

### 증상

R-7 검증 (2026-04-27) — Plan review 모달에서 [+ Todo 추가] 버튼 4번 클릭 → 백엔드 정상 (todo_009/010/011/012 모두 생성, ack 의 plan.todos 정확) → **모달 내 리스트는 8 todos 그대로 stale**.

### 발견 시점

R-7 검증 (2026-04-27 17:19~20). 사용자가 4번 추가했는데 모달엔 변화 없음.

### 근본 원인 (확정)

`dashboard/index.html::handleHitlAckTodo` 의 흐름:

```javascript
// 성공 — cascade 시각화 + plan 갱신
if (data.plan && ...) {
  _currentHitlTodos = data.plan.todos;
  _currentHitlPlan = data.plan;
  // ❌ renderHitlTodoList 호출 없음
}
renderCascade(data);
```

`renderCascade` 내부:
```javascript
function renderCascade(ack) {
  if (!inv.length && !restart && !issues.length) {
    hideCascade();
    return;       // ← todo_add 는 여기서 탈출
  }
  ...
  renderHitlTodoList(...);  // 도달 못 함
}
```

→ todo_add 처럼 cascade 무관 액션은 모달 리스트 갱신 누락. todo_modify/delete 는 cascade 발생해서 우연히 갱신됐던 것.

### 수정 (2026-04-27 즉시 fix)

**책임 분리 패턴 적용**:
- `handleHitlAckTodo` 가 plan 갱신 + `renderHitlTodoList` 책임
- `renderCascade` 는 cascade 시각화 (라벨, 통계 바) 만 담당
- 중복 plan 갱신 코드 `renderCascade` 에서 제거

```javascript
// Before
if (data.plan && ...) { _currentHitlTodos = data.plan.todos; }
renderCascade(data);

// After
if (data.plan && ...) {
  _currentHitlTodos = data.plan.todos;
  _currentHitlPlan = data.plan;
  renderHitlTodoList(data.plan.todos, _currentHitlCompleted, data.invalidated || []);
}
renderCascade(data);
```

### 영향

- todo_add: 추가된 todo 즉시 모달 리스트에 표시 ✅
- todo_modify/delete: 기존과 동일 (cascade 무관, 단지 한 번에 호출 — 중복 제거)
- todo_edit_nl: 동일 패턴으로 자동 적용

### 상태

✅ 해결됨 (커밋 예정). 사용자 R-7 재검증 필요.

### 관련

- ADR-001 (편집 경로 통합 — 이 통합 덕에 모든 ack 가 같은 handler 통과)
- 코드: `dashboard/index.html::handleHitlAckTodo`, `renderCascade`

---

## ISSUE-008 — `add_todo` 가 `task_type` 기본값 누락 → Plan validation 실패 (해결됨)

### 증상

R-7 재검증 (2026-04-27 19:40~41) — Plan review 모달에서 [+ Todo 추가] 후 [✅ 승인] 클릭 → 빨간 fatal 에러:

```
[fatal/runtime] EXECUTION_ERROR: 1 validation error for Plan
todos.8.task_type Field required
[type=missing, input_value={'agent': 'analysis_agent...: [], 'tool_params': {}}, input_type=dict]
```

→ 사용자가 추가한 9번째 todo (todo_009) 의 `task_type` 필드 누락 → Plan.model_validate 실패 → execution 진입 못 함.

### 발견 시점

R-7 재검증 (2026-04-27 19:40~41). ISSUE-007 fix 후 모달 리스트 갱신은 정상 작동했으나 **승인 시점에 fatal 발생** 으로 실제 추가가 의미 없는 상태.

### 근본 원인 (확정)

두 Plan 모델이 공존:

| 모델 | 위치 | 필수 필드 |
|------|------|---------|
| `TodoItem` | `models/todo.py` | `task`, `tool` |
| `PlannedTodo` | `planning/planner.py` | `id`, **`task_type`** |

**`Plan` 모델 (planning_stage 의 modify 분기에서 사용) 은 `PlannedTodo` 를 사용**. 사용자가 추가한 todo 는 `task_type` 없이 들어가 검증 실패.

`tm.add_todo` 의 setdefault 누락:

```python
# Before
new_todo.setdefault("id", f"todo_{next_num:03d}")
new_todo.setdefault("status", "pending")
new_todo.setdefault("depends_on", [])
new_todo.setdefault("tool_params", {})
# ❌ task_type 없음
```

dashboard 의 prompt 가 `agent` + `task` 만 받으니 클라이언트는 task_type 모름. backend 가 default 줘야 함.

### 수정 (2026-04-27 즉시 fix)

**1줄 추가**:

```python
new_todo.setdefault("task_type", "custom")
```

**기본값 "custom"** 선택 이유:
- `task_type` 의 역할: executor 가 todo 를 분류 라벨로 사용 (`todo.task_type` → ToolStartEvent)
- 사용자 추가 todo 는 **분류 모름** → "custom" 이 의미적으로 명확

### 테스트 보강

- `test_TE_A08`: `task_type == "custom"` assertion 추가
- `test_TE_A08b` (신규): `add_todo` 결과를 `PlannedTodo.model_validate()` 로 검증 — 회귀 방지

### 영향

- todo_add 후 승인 시 Plan validation 통과 ✅
- executor 의 task_type 분류 라벨 처리 정상 (custom 도 유효)
- 기존 LLM 생성 todo 는 영향 없음 (LLM 이 task_type 줌)

### 상태

✅ 해결됨 (커밋 예정). 사용자 R-7 재재검증 필요.

### 관련

- 코드: `backend/app/dream_agent/workflow_managers/todo_manager/manager.py::add_todo`
- 모델: `backend/app/dream_agent/planning/planner.py::PlannedTodo`
- 자동 테스트 추가: TE-A08 (강화) + TE-A08b (신규)

### 부수 인사이트

이 버그는 ADR-007 (session_id/turn_id 정책) 과 비슷한 구조적 모호함 — **두 모델 공존 (`TodoItem` vs `PlannedTodo`) 도 정리 대상** 일 수 있음. ADR INDEX 의 결정 누락에 후속 ADR 후보로 등록 권장.

---

## ISSUE-009 — `tool` 미지정 사용자 추가 todo 는 execution 단계에서 skip

### 증상

R-7 재재재검증 (2026-04-27 21:23~45) — 사용자가 [+ Todo 추가] 로 추가한 todo (agent + task 만 입력) 가 메인 파이프라인에 표시되지만 실제 execution 시 **"건너뜀"** 으로 처리.

### 발견 시점

R-7 재재재검증 (2026-04-27 21:23). ISSUE-001/007/008 fix 후 메인 카드에 9개 todo 모두 표시되지만 마지막 custom todo 가 ⏳ "건너뜀".

### 근본 원인 (확정)

`backend/app/dream_agent/execution/executor.py::_run_single_todo` L144-150:

```python
if not tool_name:
    return TodoResult(
        ...
        status=TodoStatus.SKIPPED,
        data={"reason": "no tool assigned"},
        ...
    )
```

**이는 defensive 동작 — 합리적**. tool 모르는 todo 는 어떻게 실행할지 모르니 SKIP.

원인 chain:
1. dashboard prompt 가 `agent` + `task` 만 받음 (tool 없음)
2. `tm.add_todo` setdefault 가 tool 미지정 (의도적 — 사용자가 모르는 것 강요 안 함)
3. executor 가 tool 없으면 SKIPPED 반환

### 영향

- **기능적**: 사용자 추가 todo 가 실행 안 됨. 사용자 의도와 직접 충돌
- **UX**: "건너뜀" 만 표시, **왜** 건너뛰는지 + **어떻게 고치는지** 안내 없음

### 수정 방향 (3 옵션)

| 옵션 | 내용 | 비용 | 한계 |
|------|------|------|------|
| **A** prompt 강화 | + 버튼 prompt 3단 (agent / task / tool) | 작음 (10분) | 사용자가 tool 이름 알아야 함 — 8개도 외우기 어려운데 10~20개 되면 비현실 |
| **B** Tool dropdown UI | 모달에 tool 선택 dropdown (catalog 표시) | 중간 (1시간) | 같은 한계 — 사용자가 "이 task 에 어떤 tool?" 판단해야 |
| **C** LLM Tool Routing | 사용자는 task 만 입력 → LLM 이 자동 매핑 | 큼 (NL 2차 범위) | 본질적 해결. ADR-002 진입 |

POC 1차 한계: **A/B 모두 확장 한계**. C 가 본질적 해결이지만 NL 2차 (Sprint 16+).

### 결정 (2026-04-27)

**현 상태 유지** — 즉시 수정 X. 종합 인사이트 (아래 §) 와 함께 **ADR-002 NL 2차 진입 정당성** 으로 박제. POC 1차에선 사용자가 의도적 추가 시점에 책임 가짐.

### 관련

- 코드: `backend/app/dream_agent/execution/executor.py::_run_single_todo` L144
- ADR-002 (NL 점진 고도화 — 1/2/3차)
- 종합 인사이트 (아래 §)

---

## 🌟 종합 인사이트 — POC 1차 검증의 큰 결론

R-5/R-6/R-7 누적 검증 (2026-04-27) 으로 도달한 **제품 방향성 차원의 깨달음**.

### 발견된 4 ISSUE 의 공통 근본 원인

| ISSUE | 표면 증상 | 진짜 원인 |
|-------|---------|---------|
| 006 | format 삭제 → 데이터 흐름 끊김 | 사용자가 **DAG 의존성** 모름 |
| 007 | 모달 갱신 후 메인 카드 stale | 표시 영역 일관성 (해결됨, 부수 issue) |
| 008 | task_type 누락 → fatal | 사용자가 **모델 schema** 모름 |
| 009 | tool 미지정 → skip | 사용자가 **tool catalog** 모름 |

### 공통 근본 원인 (한 문장)

> **사용자가 시스템 내부 도메인 지식 (DAG / schema / tool catalog) 을 가지고 있어야만 직접 편집이 안전하게 작동한다 — 비현실적 가정.**

### 확장성 우려 (사용자 인사이트)

> "10~20개 tool 되면 그 로직은 어떻게 할지 등등"

- 8 tool 도 사용자가 외우기 어려움
- 20 tool 되면 dropdown UI 도 무력
- DAG 의존성 머릿속 시뮬레이션 불가
- → **구조화 직접 편집의 본질적 한계**

### 이는 POC 의 가치 있는 발견

POC 1차 (구조화 + 단순 NL) 를 실제 운영해 보지 않았다면 발견하지 못할 인사이트. 사용자 5항목 §4 "단순 작업은 간단하면 좋겠다" 의 **"단순"의 경계** 를 이번 검증으로 측정.

| 작업 | "단순" 인가? |
|------|------------|
| 마지막 todo 삭제 (downstream 0) | ✅ 간단 — R-5 정상 |
| 중간 todo 삭제 (downstream N) | ⚠️ 위험 — DAG 지식 필요 |
| 새 todo 추가 (실행 가능) | ❌ 어려움 — tool 지식 필요 |
| NL "4번 삭제" | ✅ 간단 (R-16, 1차) |
| NL "이 분석 빠르게 해줘" | ❌ 어려움 (NL 2/3차) |

### 방향성 결정 (강화)

ADR-002 의 1·2·3차 점진 고도화가 **이번 검증으로 정당성 입증**. 특히:

- **1차 (현재)**: 단순 NL ("N번 삭제") + 단순 구조화 (🗑 마지막 todo). 한계 명확.
- **2차 (Sprint 16+)**: LLM 이 의도 해석 → 적절한 tool 선택. ISSUE-009 자연 해결
- **3차 (Sprint 18+)**: Memory + 사용자 패턴 기반 자동 재계획. ISSUE-006 자연 해결

### POC 1차의 "성공" 정의 재조정

기존: "Plan 편집 기능 작동" → 이제: **"Plan 편집의 한계를 측정 + NL 2차 진입 trigger 식별"** 이 1차의 진짜 가치.

브라우저 R-5~R-9 검증의 **진짜 산출물은 자동 테스트가 못 잡는 도메인 차원 발견** — 이번 4 ISSUE + 종합 인사이트가 그 증거.

### ADR-002 진입 조건 갱신 권장

- 1차 D-14 NL 성공률 측정만으로 부족
- **사용자 추가/편집 시도 중 도메인 지식 필요한 비율** 도 측정 후보
- ISSUE-006/009 같은 패턴 발생 빈도가 5~10% 넘으면 **2차 진입 정당성**

---

## ISSUE-003 (확인) — Memory drift 정정 ✅

R-5 로그에서 추가 확정:

```
15:05:30  AgentPool loaded (Eager) agents=9 teams=2
```

- AgentPool 이 **부팅 시가 아니라 execution 첫 진입 시 load** 됨 (catalog-preload pattern)
- Walkthrough §1.3 "lazy with catalog-preload" 설명과 일치
- Memory `project_eager_agent_init.md` 정정도 정확

→ **이슈 아님**. 단지 의도(eager) ↔ 현 코드(lazy) gap 이 실제 운영에서도 그대로 작동함을 확인. 별도 ADR 결정 시 (Sprint 15+) 처리.

---

## ISSUE-016 — Plan/Todo schema 불일치 NL fatal (R-16) ✅ 해결 (2026-04-30)

### 증상

R-16 ("4번 삭제") 시 서버 로그:
```
plan dict → Pydantic 변환 실패 error="9 validation errors for Plan ..."
```

→ NL 편집 fatal. ack `accepted: false, reason: "Plan 변환 실패: ..."`.

### 발견 시점

POC 1차 검증 (Sprint 14 A3 Phase B 사전 조사 / Q1 분석).

### 근본 원인 (확정)

활성 코드에 **3 Plan 클래스 + 2 Todo 클래스** 공존:

| 클래스 | 위치 | 성격 |
|--------|------|------|
| `planner.Plan / PlannedTodo` | `planning/planner.py` | LLM 산출물, dict 저장 |
| `models.Plan / TodoItem` | `models/plan.py`, `models/todo.py` | Canonical, lifecycle metadata |

`progress.plan` = planner 형식 dict / `plan_editor` = `models.Plan` 기대 → 변환 실패.

### 영향

- R-16 NL 편집 ("4번 삭제") fatal
- 자유 대화 1차 (Sprint 14 A3 핵심 가치) 작동 X

### 수정 (2026-04-30 — D 옵션 직진)

- **시도 (`e767845`)**: B 옵션 — 어댑터 layer (`plan_adapter.py`)
  - 1시간 내 fatal 해소
  - 단, 사용자 통찰 ("v1/v2 섞임 금지") 위반 + throwaway 약속 깨질 위험
- **채택 (`1e8f319`)**: D 옵션 — `planner.Plan` 단일화
  - `plan_editor.py` rewrite (planner 기반)
  - `ws_hitl.py` 어댑터 호출 제거 (직접 `planner.Plan.model_validate`)
  - `plan_adapter.py` + `test_a3_plan_adapter_unit.py` 삭제
  - `models/plan.py` + `models/todo.py` deprecated 마커 (활성 사용 0)
  - **PlanChange** 폐기 (NL edit 경로). approval.py 는 별도 flow 로 유지.

### 검증

- 자동 테스트: 단위 D01~D10 PASS / NL integration TE-E01~E07 PASS / plan_review TE-H01~H08 PASS / Full suite **239 passed + 2 skipped**
- 브라우저 R-16/17/18: 다음 세션 사용자 협조

### 관련

- ADR-010: [`docs/agent_specs/adr/ADR-010_plan_schema_unification.md`](../agent_specs/adr/ADR-010_plan_schema_unification.md)
- 작업 계획서: [`sprint14_a3_phase_c_unify_plan.md`](./sprint14_a3_phase_c_unify_plan.md)
- 사전 조사: [`sprint14_a3_research_q1_plan_schema.md`](./sprint14_a3_research_q1_plan_schema.md)

---

## 처리 정책

1. **즉시 처리 X** — 사용자 결정 (2026-04-27 15:0?: "기록만 해뒀다가 추후 수정")
2. **추적 위치**:
   - 본 파일에 상세 기록
   - [`agent_specs/adr/INDEX.md`](../agent_specs/adr/INDEX.md) "발견된 결정 누락" 표에 cross-reference
3. **수정 시점**: ADR-008 (C/D 정리) 또는 별도 Sprint 진행 시. ISSUE-002 는 우선순위 높으므로 ADR-009 (LLM stability) 와 묶어서 처리 검토
4. **예외**: ISSUE-016 (R-16 NL fatal) 는 Sprint 14 A3 종결을 위해 즉시 처리 (2026-04-30, D 통일)

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-27 | 초안 — R-5 검증 중 발견된 ISSUE-001 (UI stale) + ISSUE-002 (cognitive enum) 박제. ISSUE-003 (memory drift 정정 확인) 기록 |
| 2026-04-27 | R-6 검증 결과 ISSUE-005 (restart_from 누락, 1줄 fix 즉시 처리) + ISSUE-006 (도메인 의미적 검증 부재 + Level A Prevention 구현) 추가 |
| 2026-04-27 | R-7 검증 결과 ISSUE-007 (handleHitlAckTodo 가 todo_add 시 모달 리스트 미갱신) 발견 + 즉시 fix (책임 분리 패턴, renderCascade 의 plan 갱신 코드를 handleHitlAckTodo 로 이동) |
| 2026-04-27 | R-7 재검증 결과 ISSUE-008 (add_todo task_type 누락 → Plan.model_validate fatal) 발견 + 즉시 fix (1줄 setdefault). TE-A08 강화 + TE-A08b 신규 회귀 테스트. 부수 인사이트: TodoItem vs PlannedTodo 두 모델 공존 → ADR-010 후보로 ADR INDEX 등록 |
| 2026-04-27 | R-7 재재검증 결과 ISSUE-008 fix 작동 확인 (execution todos=9). ISSUE-001 (UI stale) 재현 → **사용자 인사이트로 단순 fix 발견** ("todo manager 가 frontend 에 쏴줘서 양쪽 갱신"). 옵션 D 채택: handleHitlAckTodo 에 renderTodoList 1줄 추가. 위 옵션 A/B/C 모두 과대 분석으로 판명 |
| 2026-04-27 | R-7 재재재검증 결과 ISSUE-009 (tool 미지정 사용자 추가 todo 가 execution 에서 SKIP) 발견. **종합 인사이트 섹션 추가** — ISSUE-006/007/008/009 가 모두 "사용자가 시스템 도메인 지식 가져야 안전" 이라는 공통 근본 원인 공유. POC 1차 한계 측정 + ADR-002 NL 2차 진입 정당성 강화. 사용자 결정: 현 상태 유지, NL 2/3차에서 본질적 해결 |
| 2026-04-27 | Compact 직전 종합 점검 — ISSUE-004 (모달 헤더 stale, R-6 발견) 가 복원가이드 매트릭스에만 있고 known_issues 정식 섹션 + ADR INDEX 누락 발견 → 정식 등록 (drift 정리) |
| 2026-04-30 | ISSUE-016 (Plan/Todo schema 불일치 NL fatal R-16) 정식 등록 + 즉시 해결. Phase C-Unify (D 통일) 완료. ADR-010 Accepted. 어댑터 시도 (B, e767845) 후 D 직진 (1e8f319) 으로 수렴. 자동 테스트 239 passed. 브라우저 검증 다음 세션 |
