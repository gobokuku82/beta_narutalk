# Main Graph State 명세서

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 개발 - AI 에이전트 |
| 진행상태 | 작업중 (Sprint 12 반영) |
| 버전 | **v1.3** |
| 최종 수정일 | 2026-04-19 |
| State 클래스 | `AgentState` (TypedDict) |
| 코드 위치 | `backend/app/dream_agent/states/agent_state.py` |
| Reducer 위치 | `backend/app/dream_agent/states/reducers.py` |
| 이전 버전 | v1.1 (2026-04-10) |

> **v1.3 What's New** (Sprint 12 + 13 로드맵)
> - `execution_progress` 필드 신규 (Sprint 12) — HITL Pause/Resume 영속화
> - v2 실제 사용 필드 정리 (`structured_query`, `plan`, `execution_result`, `response`)
> - Sprint 13 예정 필드(`user_id`, `conversation_id`, `turn_id`, `conversation_history`) 명시
> - v1 잔재 필드(`cognitive_result`, `planning_result`, `response_result`) — deprecated 표시 후 정리 예정

> 이 문서는 **Main Graph (4-Layer)의 AgentState**를 정의하는 명세서이다.
> Execution 내부의 subgraph State는 Agent 구현 시 별도 작성한다.

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| 그래프 이름 | Main Graph (Dream Agent 4-Layer) |
| 노드 목록 | cognitive, planning, execution, response |
| State 클래스 | `AgentState(TypedDict, total=False)` |
| 타입 전략 | Hybrid — State는 TypedDict, Layer I/O는 Pydantic |

**`total=False`의 의미**: 모든 필드가 Optional. 각 필드의 "없을 때의 의미"를 아래 스키마에서 명시한다.

---

## 2. 스키마 (v1.3 — v2 실사용 기준)

### 2.0 현행 (v2 코드 기준, Sprint 12 반영)

| 필드 | 타입 | Reducer | 초기값 | Pydantic 모델 | 없을 때의 의미 | 설명 |
|------|------|---------|--------|---------------|-------------|------|
| `session_id` | `str` | - | (필수) | - | - | 세션 식별자 (Sprint 13에서 `turn_id` alias로 deprecated) |
| `user_input` | `str` | - | (필수) | - | - | 사용자 원본 입력 |
| `language` | `str` | - | `"ko"` | - | 한국어 기본 | 언어 코드 (ko/en/ja) |
| `structured_query` | `dict[str, Any]` | - (LWW) | `{}` | `StructuredQuery` | 아직 처리 안 됨 | Cognitive 산출 (targets/goal/tasks/meta) |
| `plan` | `dict[str, Any]` | - (LWW) | `{}` | `Plan` | 아직 처리 안 됨 | Planning 산출 (Todo + DAG) |
| `execution_result` | `dict[str, Any]` | - (LWW) | `{}` | `ExecutionResult` | 아직 처리 안 됨 | Execution 산출 (todos/phase_timings/overall_status) |
| **`execution_progress`** | `dict[str, Any]` | - (LWW) | `{}` | `ExecutionProgress` (dataclass) | Pause/Resume 정보 없음 | **✅ Sprint 12 신규** — Phase별 진행 상태 + completed_todos. Checkpoint 영속화. |
| `response` | `dict[str, Any]` | - (LWW) | `{}` | `ResponsePayload` | 아직 처리 안 됨 | 최종 응답 (format/text/summary/attachments) |
| `error` | `Optional[str]` | - (LWW) | `None` | - | 에러 없음 | 에러 메시지. 마지막 에러만 남음 |
| `hitl_pending` | `Optional[dict]` | - (LWW) | `None` | (interrupt payload) | HITL 대기 없음 | interrupt() 시 임시 보관 (현재는 graph_state.tasks에서 직접 추출) |
| `trace` | `Annotated[list, trace_reducer]` | `trace_reducer` | `[]` | - | 로그 없음 | 실행 트레이스 (append-only, 최대 200개) |

### 2.0-a Sprint 13 예정 필드 (Session/Thread 재설계)

| 필드 | 타입 | 용도 |
|------|------|------|
| `user_id` | `str` | 사용자 식별 (Multi-user 대비, 현재는 mock) |
| `conversation_id` | `str` | 대화방 단위 (UI 채팅방 1개 = 1 conversation) |
| `turn_id` | `str` | 단일 쿼리 단위 (대화 안의 1턴) |
| `conversation_history` | `list[dict]` | Cognitive 주입용 최근 N턴 요약 (Sprint 15에서 MemoryManager가 채움) |

> Sprint 13 적용 시 `thread_id = f"{conversation_id}_{turn_id}"`로 LangGraph Checkpointer 호출.
> `session_id`는 deprecated alias로 `turn_id`와 동일 값 유지 (하위 호환).

### 2.0-b Deprecated 필드 (v1 잔재, v2 코드 미사용)

| 필드 | 상태 | 대체 |
|------|------|------|
| `cognitive_result` | deprecated | `structured_query` |
| `planning_result` | deprecated | `plan` (Planning 메타는 plan.plan_notes로 흡수) |
| `execution_results` | deprecated | `execution_result` (단수) — todos는 execution_result.todos 안에 |
| `todos` | deprecated | `plan.todos` + `execution_result.todos`로 분리 |
| `response_result` | deprecated | `response` |

> 정리는 Sprint 13/15에서 일괄 진행 (현 시점은 v2 코드는 신규 필드만 사용).

> **LWW** = Last Write Wins. Reducer가 없는 필드는 마지막으로 쓴 값이 이긴다.

### 2.0-c execution_progress 상세 (Sprint 12 신규)

```python
{
    "session_id": "sess_xxx",            # = turn_id (Sprint 13)
    "plan": {...},                        # 현재 유효한 Plan (수정 반영)
    "phases": [["t1"], ["t2", "t3"], ["t4"]],   # DAG 분석 결과
    "current_phase": 1,                   # 0-based 진행 위치
    "completed_todos": {                  # todo_id → result
        "t1": {"status": "completed", "data": {...}},
    },
    "status": "paused",                   # running | paused | cancelled
    "paused_at_phase": 2,                 # paused일 때만 의미 있음
}
```

**라이프사이클**:
1. execution_stage 진입 시 `hitl.create_progress(session_id, plan)` 호출
2. Phase 완료마다 `hitl.report_phase_complete(session_id, phase_results)` → completed_todos 누적
3. 사용자 Pause 요청 → `hitl.request_pause(session_id)` → 다음 Phase 직전 interrupt
4. 사용자 Resume → ws_hitl이 `hitl.request_resume()` → astream에 LGCommand(resume) 전달
5. Todo 수정/삭제 → cascade 무효화 → completed_todos에서 invalidated 제거 → phases 재구성
6. 모든 Phase 완료 → `hitl.get_execution_result(session_id)` → ExecutionResult 조립

---

## 2.1 Planning 산출물 하위 구조 (v1.1 추가)

> Planning Layer가 state에 쓰는 3개 필드(`plan`, `todos`, `planning_result`)의 내부 구조를 정의한다.
> 산출물은 3종: Execution용(todos), 시각화용(plan.visualization), 문서용(planning_result.generation_trace).

### `plan` 필드 하위 구조

```python
plan: dict = {
    # 기존 (v1.0)
    "plan_id": str,                    # Plan UUID
    "intent_summary": str,             # "블루밍글로우 네이버 리뷰 감성 분석"
    "todos": list[dict],               # TodoItem 리스트 (todos 필드와 동기화)
    "dependency_graph": dict[str, list[str]],  # todo_id → [depends_on_ids]
    "strategy": str,                   # "sequential" | "parallel" | ...
    "estimated_duration_sec": int,
    "mermaid_diagram": str,            # Mermaid 다이어그램 문자열

    # 추가 (v1.1) — 시각화용
    "visualization": {
        "summary": str,                # 한줄 요약
        "total_steps": int,
        "estimated_duration_sec": int,
        "strategy": str,
        "steps": [
            {
                "step": int,                   # 1-based
                "label": str,                  # "데이터 수집"
                "description": str,            # "네이버에서 블루밍글로우 리뷰 수집"
                "agent": str,                  # "수집 에이전트" (한국어 표시명)
                "tool": str,                   # "naver_collector"
                "depends_on_steps": list[int], # [1, 2] (step 번호 참조)
                "requires_approval": bool,
            },
        ],
        "mermaid_diagram": str,
    },
}
```

### `planning_result` 필드 하위 구조

```python
planning_result: dict = {
    # 기존 (v1.0)
    "plan_id": str,
    "version": int,
    "requires_approval": bool,
    "approved_by": str | None,
    "approved_at": str | None,

    # 추가 (v1.1) — 문서/감사용
    "generation_trace": {
        "step1_macro_plan": {
            "input": str,           # Intent 요약
            "output": list[str],    # ["데이터 수집", "전처리", "감성 분석"]
            "duration_ms": int,
        },
        "step2_todo_decomposition": {
            "input": str,           # "3개 큰 단위 + ToolRegistry 카탈로그"
            "output": str,          # "TodoItem N개"
            "duration_ms": int,
        },
        "step3_validation": {
            "structural": bool,
            "dag": bool,
            "logical": bool,
            "retries": int,         # 재생성 횟수 (0~2)
            "duration_ms": int,
        },
    },
    "tool_selection_reason": dict[str, str],  # tool_name → 선택 근거
}
```

### `todos` 필드 — `agent` 필드 추가 (v1.1)

> TodoItem에 `agent: str` 필드가 추가됨. 어떤 실행 에이전트에 라우팅할지 명시.
> 상세 필드 정의는 DATA_MODELS_poc.md §6.1 참조.

```python
# 예시
{
    "id": "uuid",
    "task": "네이버 리뷰 수집",
    "agent": "collection_agent",       # ← v1.1 추가
    "tool": "naver_collector",
    "tool_params": {"brand": "블루밍글로우", "period": "30d"},
    "depends_on": [],
    "priority": 1,
    "status": "pending",
}
```

---

## 3. Reader/Writer 매트릭스 (v1.3 — v2 실사용)

| 필드 | cognitive | planning | execution | response | hitl_manager | 비고 |
|------|:-:|:-:|:-:|:-:|:-:|------|
| `session_id` | R | R | R | R | R | 전 레이어 참조 (Sprint 13: `turn_id` 추가) |
| `user_input` | R | - | - | - | - | Cognitive만 사용 |
| `language` | R | - | - | R | - | 다국어 지원용 |
| `structured_query` | **W** | R | - | R | - | Cognitive→Planning, Response |
| `plan` | - | **W** | R | R | R/W | Planning 생성, Execution 참조, **HITL 수정 시 갱신** |
| `execution_result` | - | - | **W** | R | R | Execution→Response |
| **`execution_progress`** | - | - | R | - | **R/W** | ✅ Sprint 12 — HITL Manager가 PM으로서 관리 |
| `response` | - | - | - | **W** | - | Response 최종 출력 |
| `error` | W | W | W | W | W | 모든 레이어에서 에러 발생 가능 |
| `hitl_pending` | - | (interrupt) | (interrupt) | - | R | interrupt() payload (graph_state.tasks에서 추출) |
| `trace` | W | W | W | W | - | 모든 레이어에서 로그 추가 |

**Sprint 12 변화**:
- `execution_progress` 필드 신규 — Writer는 hitl_manager 단독 (executor는 phase 결과만 보고)
- `plan` Writer가 hitl_manager로 확장됨 (Todo 수정/삭제/추가 시 갱신)

**v1.1 매트릭스 (deprecated 필드 포함)는 §3.0 참조 (아카이브).**

**매트릭스에서 읽을 수 있는 것:**

| 관찰 | 의미 |
|------|------|
| `todos` — Writer 2개 (planning, execution) | Reducer 필수 → `todo_reducer` ✅ |
| `execution_results` — Writer 1개지만 루프 | Reducer 필수 (자기가 쓴 걸 다시 읽고 추가) → `results_reducer` ✅ |
| `trace` — Writer 4개 | Reducer 필수 → `trace_reducer` ✅ |
| `error` — Writer 4개, Reducer 없음 | LWW. **복구 불가능한 시스템 에러 전용** (전체 중단, 즉시 __end__). Todo 레벨 실패는 `execution_results[todo_id].success=false`에 기록 |
| `language` — Writer 없음 | 초기값 설정 후 **Reader-only**. 런타임 변경 없음 |
| `user_input` — Reader 1개 (cognitive만) | 정상. Cognitive만 원본 입력 필요 |
| `planning_result` — Reader 1개 (response) | response가 Planning 메타데이터를 응답에 포함 가능 |

---

## 4. Reducer 상세

### 4.1 `todo_reducer`

| 항목 | 내용 |
|------|------|
| **동작** | ID 기반 upsert. 같은 ID → 교체, 새 ID → 추가. **병합 후 priority 기반 정렬** |
| **불변조건** | final 상태(completed, **failed**, skipped, cancelled)인 Todo는 덮어쓰기 불가. **failed는 재시도 불가 (final)** |
| **엣지케이스** | ID가 없는 update → 무시 (skip) |
| **정렬** | 병합 후 `priority` 오름차순 정렬 (낮은 숫자 = 높은 우선순위) |

```
입력 예시:
  existing: [{id:"001", status:"completed", priority:1}, {id:"002", status:"pending", priority:3}]
  updates:  [{id:"002", status:"in_progress", priority:3}, {id:"003", status:"pending", priority:2}]

결과 (priority 정렬):
  [{id:"001", status:"completed", priority:1},     ← 보호됨 (final)
   {id:"003", status:"pending", priority:2},       ← 추가됨 (priority순 2번째)
   {id:"002", status:"in_progress", priority:3}]   ← 업데이트됨 (priority순 3번째)
```

> **failed = final 상태**: 재시도 없이 즉시 failed. 복구(failed → pending) 불가.
> 향후 재시도 도입 시 failed → pending 전이를 허용하도록 변경.

### 4.2 `results_reducer`

| 항목 | 내용 |
|------|------|
| **동작** | 재귀적 dict 병합. 동일 todo_id → 최신 결과로 교체 |
| **불변조건** | 없음. 항상 최신 값 우선 |
| **엣지케이스** | 중첩 dict는 재귀 병합, 그 외는 교체 |

```
입력 예시:
  existing: {"todo_001": {"success": true, "data": {"score": 0.8}}}
  new:      {"todo_002": {"success": true, "data": {"keywords": [...]}}}

결과:
  {"todo_001": {"success": true, "data": {"score": 0.8}},
   "todo_002": {"success": true, "data": {"keywords": [...]}}}
```

### 4.3 `trace_reducer`

| 항목 | 내용 |
|------|------|
| **동작** | append-only. `existing + new` 순수 연결. **최대 200개 유지** |
| **불변조건** | 기존 로그 삭제/수정 불가 (단, 200개 초과 시 오래된 것부터 제거) |
| **엣지케이스** | 중복 제거 없음. 200개 초과 시 `combined[-200:]`으로 최신 200개만 유지 |
| **제한 이유** | trace가 무한히 쌓이면 Checkpoint 크기가 커지고 State 직렬화가 느려짐 |

```
입력 예시:
  existing: [log_001, log_002, ..., log_199]  (199개)
  new:      [log_200, log_201]                (2개)

  combined: [log_001, ..., log_201]           (201개 → 200개 초과)
  결과:     [log_002, ..., log_201]           (최신 200개만 유지)
```

### 4.4 `hitl_pending` 최소 구조

> Pydantic 모델은 HITL 구현 시 확정. 아래는 최소 골격.

**Type 1: Agent 트리거** (시스템 → 사용자)
```python
{
    "hitl_type": "agent_trigger",
    "todo_id": "todo_005",           # 어떤 Todo에서 발생했는가
    "trigger": "image_selection",    # 트리거 식별자
    "question": "이미지 3장 중 선택해주세요",
    "options": ["이미지A", "이미지B", "이미지C"],  # 선택지 (없을 수도 있음)
    "data": { ... },                 # 사용자에게 보여줄 중간 결과
}
```

**Type 2: 사용자 Pause** (사용자 → 시스템)
```python
{
    "hitl_type": "user_pause",
    "paused_at": "execution",        # 어느 레이어에서 멈췄는가
    "current_todo_id": "todo_003",   # 현재 실행 중이던 Todo
    "user_request": None,            # 사용자 자연어 입력 대기 (입력 후 채워짐)
}
```

---

## 5. 데이터 흐름도

```
create_initial_state(session_id, user_input, language)
  │
  │  session_id, user_input, language 설정
  │  나머지 필드 초기값({}, [], None)
  │
  ▼
cognitive_node
  reads:  user_input, language, session_id
  writes: cognitive_result, trace
  writes: error (실패 시)
  │
  ├─ 명확화 필요 → goto="response"
  └─ 의도 명확 → goto="planning"
       │
       ▼
  planning_node
    reads:  cognitive_result, session_id
    writes: planning_result, plan, todos, trace
    writes: error (실패 시)
       │
       └─ goto="execution"
            │
            ▼
  execution_node (루프)
    reads:  plan, todos, execution_results, session_id, language
    writes: execution_results, todos, trace
    writes: error (실패 시)
    writes: hitl_pending (HITL 필요 시)
       │
       ├─ 미완료 Todo 있음 → goto="execution" (루프)
       └─ 모든 Todo 완료 → goto="response"
            │
            ▼
  response_node
    reads:  execution_results, cognitive_result, todos, language
    writes: response_result, trace
    writes: error (실패 시)
       │
       └─ goto=END
```

---

## 6. 직렬화 경계

각 노드에서 Pydantic ↔ State 변환이 일어나는 지점:

```
cognitive_node:
  CognitiveOutput 생성 → .model_dump() → state["cognitive_result"]에 dict로 저장

planning_node:
  state["cognitive_result"] → CognitiveOutput(**dict) 복원 (Intent 추출)
  Plan 생성 → .model_dump() → state["plan"]에 dict로 저장
  TodoItem[] → [item.model_dump()] → state["todos"]에 list[dict]로 저장

execution_node:
  state["plan"] → Plan(**dict) 복원
  state["todos"] → [TodoItem(**d) for d in list] 복원
  ExecutionResult 생성 → .model_dump() → state["execution_results"]에 추가

response_node:
  state["execution_results"] → {id: ExecutionResult(**d)} 복원
  ResponsePayload 생성 → .model_dump() → state["response_result"]에 dict로 저장
```

**변환 책임:**
- **쓰는 노드**: Pydantic → `.model_dump()` → dict → State
- **읽는 노드**: State → dict → `PydanticModel(**dict)` → 복원

---

## 7. 생명주기

### 생성

| 시점 | 위치 | 동작 |
|------|------|------|
| 사용자 입력 수신 | API Layer | `create_initial_state(session_id, user_input, language)` 호출 |

### Checkpoint

| 시점 | 동작 |
|------|------|
| 매 노드 실행 후 | LangGraph가 자동으로 State 전체를 Checkpoint에 저장 |
| `interrupt()` 호출 시 | 현재 State를 Checkpoint에 저장 → 사용자 응답 대기 |
| 사용자 응답 수신 시 | Checkpoint에서 State 복원 → 실행 재개 |

### 만료/정리

| 시점 | 동작 |
|------|------|
| 그래프 정상 종료 (END) | State는 Checkpoint에 남아 있음 |
| 세션 만료 | Session Manager가 관련 Checkpoint 정리 |
| 보존 정책 | (미정 — 세션 만료 후 N일 보존 후 삭제) |

---

## 8. 초기 State 값

`create_initial_state()` 호출 결과:

```python
{
    "session_id": str,          # 필수 입력
    "user_input": str,          # 필수 입력
    "language": "ko",           # 기본값

    "cognitive_result": {},     # 빈 dict = "아직 처리 안 됨"
    "planning_result": {},      # 빈 dict
    "execution_results": {},    # 빈 dict
    "response_result": {},      # 빈 dict

    "plan": {},                 # 빈 dict
    "todos": [],                # 빈 list

    "error": None,              # None = "에러 없음"
    "hitl_pending": None,       # None = "HITL 대기 없음"
    "trace": [],                # 빈 list
}
```

---

## 9. 검증 체크리스트

- [x] 모든 State 필드가 스키마 표에 있는가
- [x] 모든 필드에 Reader/Writer가 하나 이상 있는가
- [x] Writer가 2개 이상인 필드에 Reducer가 정의되었는가
- [x] Reducer의 동작과 엣지케이스가 설명되었는가
- [x] 데이터 흐름도가 실제 코드와 일치하는가
- [x] 모든 필드 값이 JSON 직렬화 가능한가
- [x] 초기값이 `create_initial_state()`와 일치하는가
- [x] 각 필드에 대응되는 Pydantic 모델이 명시되었는가

**해결된 이슈:**
- `planning_result`: response 노드가 Reader로 추가됨 (Planning 메타데이터를 최종 응답에 포함)

---

## 변경 이력

| 버전 | 날짜 | 변경자 | 변경 내용 |
|------|------|--------|----------|
| v1.0 | 2026-04-01 | 도윤 | 초기 작성. 현재 코드 기반 AgentState 명세 |
| v1.1 | 2026-04-10 | 도윤 | §2.1 신설: Planning 산출물 하위 구조 (plan.visualization, planning_result.generation_trace, planning_result.tool_selection_reason). TodoItem에 agent 필드 추가 명시 |
| **v1.3** | **2026-04-19** | **도윤 + Sprint 12** | **v2 실사용 기준으로 §2 스키마 전면 갱신**. (1) `execution_progress` 필드 신규 — Sprint 12 HITL PM 구조의 핵심 영속화 필드(ExecutionProgress dataclass: phases, current_phase, completed_todos, status, paused_at_phase). (2) v2 코드 실사용 필드 정리(`structured_query`/`plan`/`execution_result`/`response` 단수형 4종). (3) v1 잔재 필드 deprecated 표시(`cognitive_result`/`planning_result`/`execution_results`/`todos`/`response_result`). (4) Sprint 13 예정 필드 명시(`user_id`/`conversation_id`/`turn_id`/`conversation_history`). (5) §3 Reader/Writer 매트릭스에 hitl_manager 컬럼 추가 — `plan`과 `execution_progress` Writer 갱신. |
