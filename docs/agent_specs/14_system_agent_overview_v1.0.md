# 14. System Agent Overview — 4-Layer OS Agent 전체 지도

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 아키텍처 (System Agent Overview) |
| 진행상태 | Active |
| 버전 | **v1.0** |
| 최종 수정일 | 2026-04-24 |
| 독자 | 실행 에이전트(Tool)를 확장·추가하려는 개발자, 시스템 동작을 한눈에 파악하고 싶은 신규 인입자 |
| 관련 명세 | `10_system_architecture_v1.9.md`, `12_manager_layer_v1.4.md`, `21_WEBSOCKET_PROTOCOL_v1.5.md` |

**목적**: Cognitive / Planning / Execution / Response 4 레이어로 구성된 **시스템 에이전트(=OS 에이전트)** 가 어떻게 한 Turn을 처리하는지, 각 레이어의 책임·입출력·의존성·현재 구현 상태를 **단일 문서**로 설명한다. 실행 에이전트(Tool) 확장의 선행 문서.

---

## 1. "시스템 에이전트" 와 "실행 에이전트" 의 관계

이 프로젝트에서 쓰는 두 용어:

| 용어 | 의미 | 구현 위치 |
|------|------|-----------|
| **시스템 에이전트** (= OS Agent) | 사용자 자연어 → 구조화 → 계획 → 실행 → 응답의 **전체 오케스트레이션**. LangGraph 4-Layer 파이프라인 + Manager Layer. | [backend/app/dream_agent/](../../backend/app/dream_agent/) 전체 |
| **실행 에이전트** (= Tool) | 계획된 Todo 하나를 실제로 수행하는 **원자 단위 함수**. (도구 카탈로그는 현재 비어 있음 — `tools/{registry,base_tool,llm_tool}` 프레임워크만 존재.) | [backend/app/dream_agent/tools/](../../backend/app/dream_agent/tools/) |

> **비유**: 시스템 에이전트 = OS 커널(스케줄링·자원·대화 주기 관리) / 실행 에이전트 = 프로세스(각자 계산만).
>
> 문서 목적은 **실행 에이전트가 OS 어디에 꽂혀 동작하는지** 이해시켜, Tool 확장이 안전·일관되게 이루어지게 하는 것.

---

## 2. 4-Layer 파이프라인 개요

```
         ┌────────────────────────────────────────────────────┐
         │                  WebSocket (ws_agent)              │
         │       query / resume_query → run_turn() 생성      │
         └────────────────┬───────────────────────────────────┘
                          │
                          ▼  AgentState (TypedDict)
    ┌───────────────────────────────────────────────────────────┐
    │  Layer 1. Cognitive        자연어 → StructuredQuery      │
    │  (cognitive/)              ─ 대화 이력 주입               │
    └──────────────────┬────────────────────────────────────────┘
                       │ structured_query
                       ▼
    ┌───────────────────────────────────────────────────────────┐
    │  Layer 2. Planning         StructuredQuery → Plan(DAG)   │
    │  (planning/)               ─ 3-stage: Team→Agent→Todo    │
    │                            ─ 🛑 interrupt: plan_review   │
    └──────────────────┬────────────────────────────────────────┘
                       │ plan (승인된 경우)
                       ▼
    ┌───────────────────────────────────────────────────────────┐
    │  Layer 3. Execution        Phase-loop + Tool 호출        │
    │  (execution/, tools/)      ─ DAG 위상정렬 → 병렬 Phase   │
    │                            ─ 🛑 interrupt: execution_pause│
    └──────────────────┬────────────────────────────────────────┘
                       │ execution_result
                       ▼
    ┌───────────────────────────────────────────────────────────┐
    │  Layer 4. Response         결과 → 자연어 Markdown        │
    │  (response/)                                              │
    └──────────────────┬────────────────────────────────────────┘
                       │ response
                       ▼
                    WS complete event
```

### 핵심 속성

- **단방향**: 원칙적으로 위→아래. 역방향 요청은 **Manager Layer** (HITL / Callback) 로만 허용.
- **계약은 AgentState**: 레이어 간 전달은 [AgentState](../../backend/app/dream_agent/states/agent_state.py) TypedDict 의 특정 키로만. ([11_main_graph_state_v1.5.md](11_main_graph_state_v1.5.md) 참조)
- **레이어 경계에 Guard**: 각 레이어 종료 직후 `inspect_layer_output()` 으로 `COGNITIVE_EMPTY_QUERY` / `PLANNING_EMPTY_PLAN` / `EXECUTION_ALL_FAILED` / `RESPONSE_EMPTY` 검사. ([22_error_codes_v1.1.md](22_error_codes_v1.1.md))
- **Interrupt 2 군데만**: `plan_review` (항상), `execution_pause` (사용자 요청 시 Phase 경계). 이 외 사람 개입 없음.
- **개념 단위 Layer, 자유로운 노드 구현**: 4 레이어는 개념 구분. 내부 노드는 필요에 따라 분리·추가 가능(예: Planning 내부 3-stage). MEMORY: *4-Layer는 개념 단위, 구현 노드는 자유*.

---

## 3. 레이어별 상세

### 3.1 Cognitive — 자연어 → 정형쿼리 번역기

**디렉터리**: [cognitive/](../../backend/app/dream_agent/cognitive/)

| 항목 | 내용 |
|------|------|
| 책임 | 사용자 발화 + 대화 이력 → `StructuredQuery` (Targets / Goal / Tasks / Meta) |
| 입력 | `user_input`, `language`, `conversation_history`, `history_limit` |
| 출력 | `structured_query: dict` (StructuredQuery.model_dump) |
| 실패 | `error` 키 세팅 → `COGNITIVE_EMPTY_QUERY` guard → `complete(aborted)` |
| 구현 파일 | [cognitive_stage.py](../../backend/app/dream_agent/cognitive/cognitive_stage.py), [history_injector.py](../../backend/app/dream_agent/cognitive/history_injector.py) |
| 프롬프트 | `llm_manager/prompts/cognitive.yaml` |
| LLM 설정 | gpt-5.4-mini / temp 0.1 / max_tokens 2500 ([config.py](../../backend/app/dream_agent/llm_manager/config.py)) |

**스키마 계약**: [schemas/structured_query.py](../../backend/app/dream_agent/schemas/structured_query.py)

```
StructuredQuery
├─ targets   : 누가/어느 대상/어느 기간 (brand/product/source 등)
├─ goal      : 왜 (GoalType enum: answer|metric|insight|report|creative|mixed, depth, output_format)
├─ tasks     : 무엇을 (TaskType id × priority)
└─ meta      : 신뢰도, ambiguity, missing fields, 원문, 언어
```

> **TaskType / Source 는 open-vocab(자유 문자열)** — 고정 enum 이 아니다. 예시 값: `data_collection`, `metric_calculation`, `analysis`, `comparison`, `insight_generation`, `summary_generation`, `report_generation`, `recommendation`, `factual_lookup`.

> **MEMORY 상기**: *Cognitive = 자연어→정형쿼리 번역기*. Cognitive 출력 스키마가 시스템의 **핵심 계약**. 여기가 부실하면 뒤가 다 흔들림.

**Status**: ✅ **complete** (Sprint 9-1 완료, Sprint 13 I8 이력 주입 추가)

**history_injector 주의**: 현재는 **슬롯만** 있음. 실제 이력 데이터는 Sprint 15 MemoryManager 구현 시점에 채워짐. 현재 동작은 "빈 history 통과" 수준.

---

### 3.2 Planning — StructuredQuery → Plan (DAG)

**디렉터리**: [planning/](../../backend/app/dream_agent/planning/)

| 항목 | 내용 |
|------|------|
| 책임 | TaskType 요구를 **Team → Agent → Todo** 3-stage로 분해 + DAG 구성 + 검증 |
| 입력 | `structured_query: dict` |
| 출력 | `plan: dict` (Plan.model_dump) 또는 reject 경로 시 `response: dict` |
| Interrupt | **plan_review** (항상 발행) — HITLManager 통해 사용자가 approve/reject/modify |
| 실패 | todos 비면 `PLANNING_EMPTY_PLAN` guard |
| 구현 파일 | [planner.py](../../backend/app/dream_agent/planning/planner.py), [planning_stage.py](../../backend/app/dream_agent/planning/planning_stage.py) |
| 카탈로그 | [planning/catalog/team_catalog.yaml](../../backend/app/dream_agent/planning/catalog/team_catalog.yaml) |
| 프롬프트 | `planning_stage1_team.yaml`, `planning_stage2_agent.yaml`, `planning_stage3_todo.yaml` |

**3-Stage 내부 흐름**:

```
Stage 1: _select_teams()    팀 선택 LLM (analysis/qa/decision 등)
Stage 2: _select_agents()   선택된 Team 내 Agent 후보 선별
Stage 3: _build_todos()     Todo 리스트 + DAG + 프롬프트 rationale
           ↓
      validate_dag()        cycle 검사 (DFS white/gray/black), undefined dep 검사
           ↓
      interrupt(plan_review)  항상
```

**산출 스키마** (`planner.py` 의 `PlannedTodo` + `Plan`):

```
PlannedTodo: id, task_type, team, agent, tool, tool_params, depends_on, priority, rationale, requires_approval
Plan       : plan_id, todos[], dag{id→[deps]}, teams_selected, strategy, mermaid_diagram, plan_notes
```

**Status**: ✅ **complete** (Sprint 9-2 hierarchical 설계 완료)

**추가 구현 필요 — Sprint 14 A4**:
- `requires_approval: bool` 필드는 이미 모델에 있으나, **Execution 단계의 pre-execution interrupt** 가 아직 미구현. A4에서 고비용·외부 사이드이펙트 Tool 에 대해 Phase 시작 전 승인 요구 interrupt 추가 예정.

---

### 3.3 Execution — Plan → ExecutionResult (Phase DAG 병렬 실행)

**디렉터리**: [execution/](../../backend/app/dream_agent/execution/) + [tools/](../../backend/app/dream_agent/tools/)

| 항목 | 내용 |
|------|------|
| 책임 | Plan.dag → Phase 위상 정렬 → Phase별 Tool 병렬 호출 → 결과 수집 |
| 입력 | `plan: dict`, (재개 시) `execution_progress: dict` |
| 출력 | `execution_result: dict`, `execution_progress: dict` (checkpoint 용) |
| Interrupt | **execution_pause** — Phase 경계에서 `hitl.should_continue()==pause` 시 |
| 실패 | 전부 실패 시 `EXECUTION_ALL_FAILED` fatal / 부분 실패 시 `EXECUTION_PARTIAL_FAILED` warning |
| 구현 파일 | [execution_stage.py](../../backend/app/dream_agent/execution/execution_stage.py), [executor.py](../../backend/app/dream_agent/execution/executor.py), [agent_pool.py](../../backend/app/dream_agent/execution/agent_pool.py), [mock_tools.py](../../backend/app/dream_agent/execution/mock_tools.py) |

**핵심 하위 컴포넌트**:

| 컴포넌트 | 역할 |
|---------|------|
| **AgentPool** (singleton) | 서버 부팅 시 `team_catalog.yaml` 을 읽어 Agent/Tool 메타를 Eager Init. `is_tool_implemented()` / `is_tool_stub()` 판별. |
| **ToolRegistry** (singleton) | `tools/catalog/*.yaml` 을 재귀 스캔 → `ToolSpec` 생성 → 필요 시 클래스 lazy import (`app.dream_agent.tools.<path>.<ClassName>`). |
| **executor.build_phases(plan)** | DAG 위상 정렬 → `[["t1"], ["t2","t3"], ["t4"]]` 형태의 Phase 리스트. |
| **executor.execute_phase()** | `asyncio.gather()` 로 Phase 내 Todo 병렬 실행. 각 Todo 는 `_run_single_todo()` 로 ToolClass().execute(params, context). |
| **_inject_prev_outputs()** | 이전 Phase 결과를 setdefault 패턴으로 tool_params 에 주입 (`_` prefix 키 제외). Tool 간 체이닝의 핵심. |
| **mock_tools.mock_result()** | Stub 판별된 Tool 은 mock 결과 반환. `is_mock=True` flag 전파. |
| **HITLManager (PM 역할)** | `create_progress()` / `report_phase_complete()` / `should_continue()` / `get_completed()` — Phase 단위 상태 관리 & 재개 지원. |

**런타임 플로우**:

```
execution_stage(state)
 ├─ hitl.create_progress / get_progress   (재개 시 상태 복원)
 ├─ build_phases(plan)                    (Phase 리스트 생성)
 └─ for phase_idx, phase in enumerate(phases):
       ├─ if hitl.should_continue()=="pause": interrupt(execution_pause)
       ├─ execute_phase(phase_todos, ctx, previous_results)
       │   └─ asyncio.gather( _run_single_todo × N )
       │       └─ ToolClass(spec).execute(params, context) | mock_result(...)
       ├─ hitl.report_phase_complete(results)
       └─ emit todo_start / todo_complete / progress (via CallbackManager)
 └─ build ExecutionResult → Command(update=..., goto="response")
```

**Status**:
- ✅ Phase DAG 실행 엔진 (Sprint 10)
- ✅ PM 패턴 (Sprint 12)
- ✅ Queue 기반 비동기 resume (Sprint 13 I7)
- ✅ HITL Timeout (Sprint 14 A1)
- ✅ Todo Edit HITL (Sprint 14 A3, 브라우저 검증 대기)
- ⏳ Phase-level pause 세분화 (Sprint 14 A2)
- ⏳ `requires_approval` pre-exec interrupt (Sprint 14 A4)

**디테일은 실행 에이전트(Tool) 확장 가이드 참조.**

---

### 3.4 Response — ExecutionResult → ResponsePayload (자연어)

**디렉터리**: [response/](../../backend/app/dream_agent/response/)

| 항목 | 내용 |
|------|------|
| 책임 | Tool 결과 dict 를 Markdown + 첨부(Attachments) 로 재조립. 사용자에게 가는 최종 메시지. |
| 입력 | `execution_result`, `structured_query` (컨텍스트), `plan`, `language` |
| 출력 | `response: dict` (ResponsePayload.model_dump) |
| 실패 | text 가 비면 `RESPONSE_EMPTY` fatal |
| 구현 파일 | [responder.py](../../backend/app/dream_agent/response/responder.py), [response_stage.py](../../backend/app/dream_agent/response/response_stage.py) |
| 프롬프트 | `llm_manager/prompts/response.yaml` |
| LLM 설정 | gpt-5.4-nano / temp 0.3 / max_tokens 1500 (비용 낮은 모델) |

**산출 스키마** ([schemas/response_payload.py](../../backend/app/dream_agent/schemas/response_payload.py)):

```
ResponsePayload
├─ format        : text | markdown | pdf | image | chart | video | mixed | error
├─ text          : Markdown 본문
├─ summary       : 한 문장 요약 (optional)
├─ attachments[] : {kind, path, url, caption, meta}
├─ next_actions[]: 사용자 제안 액션
├─ meta          : completed_todo_count, total_duration_ms ...
└─ error         : optional (Responder 내부 실패 시)
```

**Status**: ✅ **complete** (Sprint 4)

**놓치기 쉬운 점**: `attachments[].path` 는 **서버 로컬 경로**, `url` 은 **배포 URL** 이다. 파일 산출 Tool 확장 시 둘 다 채울지, 하나만 채울지 합의 필요.

---

## 4. 공통 기반 — AgentState / Command / Interrupt

### 4.1 AgentState

파일: [states/agent_state.py](../../backend/app/dream_agent/states/agent_state.py)

`TypedDict(total=False)` — 전 필드 Optional. 레이어별 writer 는 정확히 하나 (일부 예외):

| 필드 | Writer | Reader |
|------|--------|--------|
| `user_id` / `conversation_id` / `turn_id` / `session_id` | ws_agent | all |
| `conversation_history` / `history_limit` | ws_agent | cognitive |
| `user_input` / `language` | ws_agent | cognitive, response |
| `structured_query` | cognitive | planning, response |
| `plan` | planning, **hitl (편집)** | execution, response, hitl |
| `execution_result` | execution | response |
| `execution_progress` | hitl (PM) | execution (재개) |
| `response` | response | — |
| `error` | 모든 레이어 (LWW, fatal 만) | ws_agent |
| `trace` | 모든 레이어 (reducer: append, cap 200) | debug |
| `hitl_pending` | interrupt buffer | — |

**초기화**: `init_agent_state(user_input, conversation_id, turn_id, ...)` — session_id 를 turn_id 의 alias 로 동기화.

### 4.2 LangGraph Command 패턴

각 레이어는 다음 형태로 상태 갱신 + 다음 노드 지정:

```python
return Command(
    update={"structured_query": sq.model_dump(mode="json")},
    goto="planning",   # 다음 노드 or END
)
```

### 4.3 Interrupt (HITL 진입점)

LangGraph `interrupt()` 호출 시 checkpoint 저장 후 해당 노드에서 중단. 재개는 `Command(resume=<payload>)` 로.

| Interrupt Type | 발행 위치 | 대기 방법 | 타임아웃 처리 |
|----------------|-----------|-----------|---------------|
| `plan_review` | planning_stage 말미 | `hitl.wait_for_resume(turn_id, timeout)` | timeout → `{action: "reject"}` 주입 → END |
| `execution_pause` | execution_stage Phase 경계 | 동일 | timeout → `{action: "cancel"}` 주입 → END |

> **핵심**: Interrupt 직전에 `trace` + `execution_progress` 가 Postgres Checkpointer 에 저장되므로 서버 재시작 후 `resume_query` 로 재입장 가능.

---

## 5. Manager Layer — "OS 커널" 역할

시스템 에이전트가 **OS** 처럼 보이는 이유는 이 Manager 들이 프로세스(Turn)의 생명주기·통신·동시성을 관리하기 때문. 레이어처럼 보이지만 실제로는 **서비스 레지스트리 + 싱글톤 집합**.

**디렉터리**: [workflow_managers/](../../backend/app/dream_agent/workflow_managers/)

| Manager | 책임 | 파일 | Status |
|---------|------|------|--------|
| **ConnectionManager** | WS 연결 등록, user 단위 fan-out broadcast, 죽은 WS 청소 (MAX 5/user) | `connection_manager.py` (api 쪽) | ✅ |
| **ConcurrencyManager** | user 당 동시 Turn ≤ 3 슬롯 제한 (`try_acquire` / `release`) | [concurrency_manager.py](../../backend/app/dream_agent/workflow_managers/concurrency_manager.py) | ✅ |
| **CallbackManager** | Executor → WS bridge. `register(turn_id, cb)` + `emit(event)` | [callback_manager/](../../backend/app/dream_agent/workflow_managers/callback_manager/) | ✅ |
| **HITLManager** | 승인 대기 (`wait_for_resume`), 진행률 PM (`create_progress`), Todo 편집 (`handle_todo_*`), 타임아웃, per-session Lock | [hitl_manager/](../../backend/app/dream_agent/workflow_managers/hitl_manager/) | ✅ (Sprint 14 A1/A3) |
| **TodoManager** | DAG cascade 계산, Phase rebuild | [todo_manager/](../../backend/app/dream_agent/workflow_managers/todo_manager/) | ✅ |
| ~~SessionManager~~ | **폐기 (2026-06-12 정리 Sprint)** — 호출 0 의 v1 잔재, 영속은 LangGraph checkpointer 가 전담 | — | 삭제됨 |
| **MemoryManager** | conversation_history 실제 저장소. 현재 슬롯만 존재. | [memory_manager/](../../backend/app/dream_agent/workflow_managers/memory_manager/) | ⏳ planned (Sprint 15) |
| **FeedbackManager** | 사용자 피드백 수집 | [feedback_manager/](../../backend/app/dream_agent/workflow_managers/feedback_manager/) | ⏳ planned |
| **LearningManager** | POC→MVP 전환 시 규칙/프롬프트 학습 적응 | [learning_manager/](../../backend/app/dream_agent/workflow_managers/learning_manager/) | ⏳ planned |

### Lifecycle per Turn

```
run_turn(user_id, payload)
  try:
    cb_manager.unregister(turn_id)                    # dedup (resume 시 leak 방지)
    cb_manager.register(turn_id, _callback_bridge)
    concurrency.try_acquire(user_id, turn_id)         # slot (False → CONCURRENT_LIMIT_EXCEEDED)
    hitl.register_turn(turn_id)                       # _active_turns 등록 (timeout guard)

    await _graph_runner_with_resume(agent, state, thread_id)
      ├─ astream(...) — initial run
      ├─ 만약 interrupt → hitl.wait_for_resume(turn_id, timeout)
      │                   ├─ approve/reject/modify → astream(Command(resume=...))
      │                   ├─ pause/resume/cancel  → 동일
      │                   └─ timeout → action 주입 → END
      └─ complete event emit
  finally:
    cb_manager.unregister(turn_id)
    hitl.cleanup_turn(turn_id)     # _active_turns / _paused / _resume_queues / _session_locks 해제
    concurrency.release(user_id, turn_id)
```

> **놓치기 쉬운 실무 디테일**:
> - `cb_manager.unregister` 를 **register 이전에 호출** 하는 이유는 resume 시 이전 Turn 의 리스너가 쌓이는 bug (R-9) 방지.
> - `hitl._session_locks` 는 Sprint 14 A3 D9 L1 로 도입. Todo 편집 race 방지.
> - 이 패턴을 깨면 **좀비 리스너 / 슬롯 leak / timeout 오발** 이 생김.

> **MEMORY 상기**: *Scheduler 레이어 없음 — 책임 분산*. 전략 결정 / HITL / 타임아웃은 Cognitive·Planning·Execution 에 흡수된 **13-노드 토폴로지**.

---

## 6. WebSocket 통신 — 외부 경계

외부에서 시스템 에이전트에 접근하는 유일 경계.

| 채널 | 방향 | 용도 |
|------|------|------|
| `/ws/agent` | Server → Client + Client → Server | Turn 시작 (`query` / `resume_query`), 이벤트 스트림 (node_event / complete / error) |
| `/ws/hitl` | Bidirectional | 사용자 명령 (approve/reject/pause/resume/cancel/todo_*) + ack |

**이중 채널 이유**: Event 백프레셔 ↔ 사용자 명령 독립성.

프로토콜 상세는 [21_WEBSOCKET_PROTOCOL_v1.5.md](21_WEBSOCKET_PROTOCOL_v1.5.md).

---

## 7. 에러 & Guard 체계

### 7.1 레이어 Guard

각 노드 완료 직후 `inspect_layer_output(node, data)`:

| 코드 | 레이어 | 심각도 | 조건 |
|------|--------|--------|------|
| `COGNITIVE_EMPTY_QUERY` | cognitive | fatal | StructuredQuery 비어 있음 |
| `PLANNING_EMPTY_PLAN` | planning | fatal | todos == [] |
| `EXECUTION_ALL_FAILED` | execution | fatal | 전부 실패 |
| `EXECUTION_PARTIAL_FAILED` | execution | warning | 일부 실패 — guard_warnings 축적 |
| `RESPONSE_EMPTY` | response | fatal | text 비어 있음 |

fatal → `complete(status="aborted", reason=<code>)`. warning → 최종 complete 에 `guard_warnings` 배열로.

### 7.2 트랜스포트 / 런타임 에러

| 코드 | 레이어 | 조건 |
|------|--------|------|
| `INVALID_MESSAGE` | transport | conv/turn/input 누락 |
| `CONCURRENT_LIMIT_EXCEEDED` | transport | 4번째 동시 Turn |
| `EXECUTION_ERROR` | runtime | unhandled exception |
| `TODO_EDIT_NOT_PAUSED` | runtime | Sprint 14 A3 — edit attempt 시 paused/plan_review 상태 아님 |
| `INVALID_DAG` | planning | cascade 시 cycle |
| `NL_INTENT_UNCLEAR` | planning | NL parse 실패 (action=unknown) |

전체 카탈로그: [22_error_codes_v1.1.md](22_error_codes_v1.1.md)

---

## 8. 현재 구현 상태 요약표

| 영역 | Status | 비고 |
|------|--------|------|
| **4-Layer Graph 조립** | ✅ complete | [system_graph/builder.py](../../backend/app/dream_agent/system_graph/builder.py) |
| **AgentState + init** | ✅ complete | Sprint 13 I6 |
| **Cognitive + History Injector (슬롯)** | ✅ complete | 실제 history 데이터는 Sprint 15 |
| **Planning 3-stage** | ✅ complete | Sprint 9-2 |
| **plan_review interrupt** | ✅ complete | |
| **Execution Phase DAG + Parallel** | ✅ complete | |
| **execution_pause interrupt** | ✅ complete | Phase 경계만 |
| **Response LLM markdown** | ✅ complete | |
| **LLM Manager (OpenAI + Anthropic)** | ✅ complete | |
| **ConnectionManager** | ✅ complete | |
| **ConcurrencyManager** | ✅ complete | Sprint 13 T2 |
| **CallbackManager (bridge)** | ✅ complete | Sprint 13 I11-b2 |
| **HITLManager (approval + pause + PM)** | ✅ complete | Sprint 12 |
| **HITL Timeout (30min)** | ✅ complete | Sprint 14 A1 (2026-04-22) |
| **TodoManager cascade** | ✅ complete | Sprint 12 |
| **Todo Edit HITL (structured + NL)** | ✅ complete (브라우저 검증 대기) | Sprint 14 A3 (2026-04-23) |
| **Checkpointer 서버 재시작 복원** | ✅ complete | Sprint 13 I11-c |
| **Multi-tab broadcast** | ✅ complete | Sprint 13 I9 |
| **Layer Guard + ErrorCodes** | ✅ complete | Sprint 13 I10 |
| **Reducer (multi-writer race 방어)** | 🔒 postponed | 현재 실제 race 없음. Tool 확장 후 재검토 |
| **Phase-level pause 세분화 (A2)** | ⏳ planned | Sprint 14 A2 |
| **`requires_approval` pre-exec interrupt (A4)** | ⏳ planned | Sprint 14 A4 |
| **MemoryManager 실제 구현** | ⏳ planned | Sprint 15 |
| ~~SessionManager DB 백엔드~~ | 폐기 (2026-06-12 — SessionManager 자체 삭제) | — |
| **FeedbackManager** | ⏳ planned | |
| **LearningManager** | ⏳ planned | |
| **Multi-turn Clarification (γ)** | ⏳ planned | Sprint 15+ |

---

## 9. 사용자가 놓치기 쉬운 포인트 (Gaps & Caveats)

### 9.1 ~~Plan 모델이 두 곳에 존재~~ — ✅ **해소 (2026-05-15)**

이전 본 문서는 `Plan` 이 [planning/planner.py](../../backend/app/dream_agent/planning/planner.py) 와 `models/plan.py` 두 곳에 존재함을 함정으로 지적하고 "Sprint 15 숙제" 로 남겼음. **2026-04-30 ADR-010 단일화 결정 + 2026-05-15 후속 정리 (models/ cleanup A3)** 로 `models/plan.py` 가 통째로 삭제되어 **`Plan` 은 `planner.py` 한 곳만 존재**.

추가로 `TodoItem` (`models/todo.py`) 도 함께 제거됨 — 활성 todo 모델은 `planner.PlannedTodo` 단 1개.

### 9.2 ~~`ExecutionResult` 스키마도 두 곳~~ — ✅ **해소 (2026-05-15)**

이전 본 문서는 동명의 `ExecutionResult` 가 [schemas/execution_result.py](../../backend/app/dream_agent/schemas/execution_result.py) (Layer 출력 계약) 와 `models/execution.py` (단일 Tool 결과 wrapper) 두 곳에 존재함을 함정으로 지적하고 "전환 Sprint 정리" 로 남겼음. **2026-05-15 models/ cleanup A6** 에서 `models/execution.py::ExecutionResult` 클래스를 삭제 — **`ExecutionResult` 도 `schemas/` 한 곳만 존재**.

`models/execution.py` 자체는 살아있음 — `ExecutionContext` (Tool 입력 컨텍스트) 가 본 파일에 정의됨. ExecutionContext 만 유지.

### 9.3 `session_id` 는 `turn_id` 의 **deprecated alias**

Sprint 12 코드 호환을 위해 `init_agent_state` 가 `session_id = turn_id` 로 세팅. 신규 코드는 **`turn_id` 만** 써야 함. Sprint 12 코드와 섞이는 영역(hitl_manager 등)에서 양쪽 key 가 공존하는 곳이 있으므로 주의.

### 9.4 `stub` vs `planned` vs `partial`

MEMORY의 **코드 Status 마커 컨벤션**:
- `Status: complete` — 완전 구현
- `Status: partial — <설명>` — 일부만 구현, Handoff 있음
- `Status: planned — <Sprint#>` — 스켈레톤만, 실제 로직 없음
- `Status: stub` — 의도적 mock (AgentPool 이 mock_tools 로 라우팅)

이 구분이 **AgentPool 판별**과 **Contract Test DC-10** 양쪽에서 중요. Tool YAML 의 `status` 필드와 `.py` docstring 은 반드시 일치해야 함.

### 9.5 `interrupt()` 는 "노드 상단" 이 아니라 "노드 말미"

LangGraph 의 interrupt 는 **해당 노드 재실행 시 interrupt 호출 시점부터 이어서 실행**. Planning 은 interrupt 를 노드 **말미**에 호출하므로, 재개 시 LLM 호출은 재실행되지 않는다 (checkpoint 에 plan_dict 가 이미 저장됨). 이 전제가 깨지면 중복 LLM 호출 → 비용 / 비결정론.

### 9.6 Tool 의 `previous_results` 는 setdefault 로 주입됨

[executor.py](../../backend/app/dream_agent/execution/executor.py) 의 `_inject_prev_outputs()` 는 **기존 tool_params 를 덮지 않음**. 즉 사용자가 tool_params 에 명시한 값이 우선. 새 Tool 작성 시 이 동작을 기억해야 기본값/override 전략을 올바르게 설계함.

### 9.7 Mock 이 은폐하는 것

Stub Tool 은 `mock_result()` 가 "그럴듯한" 데이터를 반환해서 DAG 는 통과함. → **실제 Tool 구현 전엔 Response Layer 품질을 판단 불가**. MEMORY: *초기는 LLM 많이 써도 됨* — POC 단계에선 OK 지만, MVP 전환 시 mock→real 전환 체크리스트가 필요.

### 9.8 `conversation_history` 는 **방어적 복사 안 함**

[agent_state.py](../../backend/app/dream_agent/states/agent_state.py) `init_agent_state()` 는 pass-through. 호출자(ws_agent)가 매번 새 list 를 넘겨야 하며, MemoryManager 구현 시 **공유 참조 오염** 주의.

### 9.9 Prompt 파일 정적 상수 위치

`llm_manager/prompts/*.yaml` 이 실제 동작을 상당 부분 좌우함. 레이어 튜닝 = 거의 YAML 튜닝. 그러나 YAML 변경은 **Contract Test 에 걸리지 않는다**. 따라서 레이어 회귀는 *통합 시나리오 테스트* 로만 포착 가능.

### 9.10 "Tool 카탈로그 하나 = 파일 하나" 컨벤션

[tools/registry.py](../../backend/app/dream_agent/tools/registry.py) 는 `tools/catalog/<category>/<name>.yaml` → `app.dream_agent.tools.<category>.<name>.<PascalCase>` 로 자동 import. 경로 규칙을 어기면 `import_tool()` 실패 시점에만 에러가 터지므로 **신규 Tool 추가 시 경로/클래스명 일치 필수**.

---

## 10. 실행 에이전트 확장 시 되돌아볼 것들

실행 에이전트(Tool) 추가는 실행 에이전트 확장 가이드의 checklist 를 따르되, 시스템 에이전트 관점에서 **특히** 확인할 사항:

1. **Planning 카탈로그 등록** — `planning/catalog/team_catalog.yaml` 에 해당 Agent 의 tools 목록에 추가하지 않으면 Planner 가 절대 선택 못함. (Tool YAML 만 있어도 실행은 되지만, **계획되지 않음**.)
2. **Status marker 일관성** — Tool YAML `status` == `.py` docstring `Status:` == AgentPool `is_tool_implemented()` 판별 결과 일치.
3. **Produces 선언** — Tool YAML `produces` 키. 다음 Tool 이 `find_in_previous()` 로 꺼내 쓸 수 있어야 함. 네이밍 컨벤션 일치 중요 (e.g. `raw_records`, `normalized_records`, `cleaned_items`, `count`, `total`, `rate`, `insights`, `report_text`).
4. **requires_approval** — 고비용 / 외부 사이드이펙트 Tool 이면 `True`. Sprint 14 A4 이후 pre-exec interrupt 발동.
5. **Mermaid & visualization** — Planning 이 출력하는 mermaid_diagram 은 대시보드 시각화에 쓰임. Tool 이름이 이상하면 diagram 이 지저분해짐.
6. **Cancel/Pause safety** — Phase 내 asyncio.gather 는 중단 불가. 긴 작업 Tool 은 **Phase 단독 배치** 권장. (A2 가 세분화하기 전까진 이 제약 유지.)
7. **에러 래핑** — Tool 이 raise 하면 `_run_single_todo` 가 `TodoResult(status=FAILED, error=str(e))` 로 감싸서 throw 억제. DAG 는 계속 진행. → **사용자에게 실패 전파가 필요한 치명 에러** 는 별도 Guard 로 수동 관리 필요.

---

## 11. 관련 문서

| 번호 | 제목 | 용도 |
|------|------|------|
| [01_requirements_v1.6.md](01_requirements_v1.6.md) | Requirements | FR/NFR/UX, Sprint 범위 |
| [10_system_architecture_v1.9.md](10_system_architecture_v1.9.md) | System Architecture | 아키텍처 전체 diagram + interrupt 모델 |
| [11_main_graph_state_v1.5.md](11_main_graph_state_v1.5.md) | AgentState | 전 필드 reader/writer 표 |
| [12_manager_layer_v1.4.md](12_manager_layer_v1.4.md) | Manager Layer | 5+ Manager API 상세 |
| [13_lifecycle_v1.3.md](13_lifecycle_v1.3.md) | Lifecycle | 13-state state machine |
| **14** (이 문서) | **System Agent Overview** | **4-Layer 전체 지도** |
| [20_INTERFACE_CONTRACT_v1.1.md](20_INTERFACE_CONTRACT_v1.1.md) | Interface Contract | REST/WS/Layer 계약 |
| [21_WEBSOCKET_PROTOCOL_v1.5.md](21_WEBSOCKET_PROTOCOL_v1.5.md) | WebSocket Protocol | ws_agent / ws_hitl 메시지 |
| [22_error_codes_v1.1.md](22_error_codes_v1.1.md) | Error Codes | 11 code 카탈로그 |
| [24_sequence_diagrams_v1.3.md](24_sequence_diagrams_v1.3.md) | Sequence Diagrams | 10 시나리오 |
| [30_DATA_MODELS_v1.1.md](30_DATA_MODELS_v1.1.md) | Data Models | Pydantic schema 전수 |

---

## 변경 이력

> 프레임워크 추출(2026-06-19) 이전(마케팅 도메인 시기)의 상세 변경 이력은 git 히스토리를 참조하세요.
