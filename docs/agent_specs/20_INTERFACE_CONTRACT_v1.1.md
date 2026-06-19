# Interface Contract (Sprint 13+)

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 개발 - API 계약 |
| 진행상태 | **Active** (Sprint 13 Integration 반영) |
| 버전 | **v1.1** |
| 최종 수정일 | 2026-04-22 |
| 관련 명세 | `21_WEBSOCKET_PROTOCOL_v1.5.md`, `30_DATA_MODELS_v1.1.md`, `11_main_graph_state_v1.5.md`, `12_manager_layer_v1.4.md` |

---

## 0. 개요

DreamAgent V2의 **API 계약** (Layer I/O + REST 엔드포인트 + AgentState + 에러 규약).

- **WebSocket 프로토콜** → `21_WEBSOCKET_PROTOCOL_v1.5.md`
- **Pydantic / dataclass 모델** → `30_DATA_MODELS_v1.1.md`
- **AgentState 스키마 상세** → `11_main_graph_state_v1.5.md`
- **내부 Manager API (HITLManager / ConcurrencyManager 등)** → `12_manager_layer_v1.4.md`

### Sprint 14 A1 변경 (HITL timeout)
- `HITLManager.wait_for_resume(turn_id, timeout=None)` — timeout 인자 추가 (하위 호환, 기본 None)
- `HITLManager.register_turn(turn_id)` / `is_turn_active(turn_id)` — 신규 공개 메서드
- `HITLManager.cleanup_turn(turn_id)` — 시맨틱 확장 (`_active_turns`, `_paused` 도 정리)
- Settings `HITL_RESUME_TIMEOUT_SEC: int = Field(ge=1, default=1800)` — 신규 env override
- `complete` 이벤트 `data.reason` 값에 `"hitl_timeout"` 추가
- `hitl_ack` 이벤트 `data.accepted=False, reason="turn_not_active"` 케이스 추가
- 상세 시그니처는 `12_manager_layer_v1.4.md` §4.3, 이벤트 스키마는 `21_WEBSOCKET_PROTOCOL_v1.5.md` 참조

---

## 1. REST API

### 1.1 Sprint 13 현재 구현

| Method | 경로 | 목적 | 응답 |
|--------|------|------|------|
| GET | `/health/` | Health check (router prefix `/health`) | `{"status": "ok", ...}` |
| GET | `/health/detail` | 상세 health (4-Layer graph compile 검사 포함) | JSON |
| GET | `/` | Dashboard 서빙 (`dashboard/index.html`) | HTML |
| GET | `/dashboard/*` | Dashboard 정적 리소스 (StaticFiles 마운트) | Static |
| WS | `/ws/agent` | Agent 이벤트 채널 | WebSocket |
| WS | `/ws/hitl` | HITL 명령 채널 | WebSocket |

### 1.2 Sprint 15 예정 (placeholder)

| Method | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/conversations` | 새 대화방 생성 |
| GET | `/api/v1/conversations` | 대화방 목록 |
| DELETE | `/api/v1/conversations/{id}` | 대화방 삭제 |
| GET | `/api/v1/conversations/{id}/turns` | 대화 턴 이력 페이징 |
| POST | `/api/v1/conversations/{id}/title` | 제목 재생성 (LLM) |

**스펙 확정 시점**: Sprint 15 Memory 착수 (예정).

### 1.3 Auth (현재 없음)

Sprint 16+ 로그인 도입 전까지 `user_id="demo"` 고정.

향후 (Sprint 17+):
```
Authorization: Bearer <jwt_token>
```

---

## 2. WebSocket 채널

상세: `21_WEBSOCKET_PROTOCOL_v1.5.md`

| 채널 | Client → Server | Server → Client |
|------|------|------|
| `/ws/agent` | `query` (신 경로 — user_input 포함), `resume_query` (R-9 서버 재시작 복원 — user_input 없이 conv/turn_id만), `start` (Sprint 12 legacy), `ping` | `connected`, `node_event`, `hitl_request`, `paused`, `resumed`, `complete`, `error`, `layer_start`, `todo_start`, `todo_complete`, `progress`, `pong` |
| `/ws/hitl` | `hitl_response` (approve/reject/modify), `pause`, `resume`, `cancel`, `todo_modify`/`todo_delete`/`todo_add` (Sprint 14 예정) | `connected`, `hitl_ack`, `error` |

---

## 3. Layer Contract

각 Layer의 Input → Output 계약.

### 3.1 Cognitive

| 항목 | 내용 |
|------|------|
| **Input** | `AgentState` 중 `user_input`, `language`, `conversation_history`, `history_limit` |
| **Output (state update)** | `{"structured_query": <StructuredQuery.model_dump>}` |
| **실패 케이스** | `{"error": "Cognitive failed: ..."}` (goto END) |
| **코드** | `backend/app/dream_agent/cognitive/cognitive_stage.py::cognitive_stage` |
| **주입 헬퍼** | `prepare_cognitive_prompt` (Sprint 13 I8 — history 주입) |

**StructuredQuery 스키마** — 진실 소스: `backend/app/dream_agent/schemas/structured_query.py`
```python
{
    "targets": {                       # Targets
        "brand": str | None, "product": str | None,
        "competitors": [str], "source": str,   # source = open-vocab 자유 문자열 (예: "unknown"|"multi")
        "period": {"raw": str, "start": str|None, "end": str|None, "window": str|None} | None,
        "keywords": [str], "extra_filters": {}
    },
    "goal": {                          # Goal
        "type": "answer|metric|insight|report|creative|mixed",   # GoalType enum
        "output_format": "text|pdf|image|chart|video|mixed",   # 필수
        "depth": "brief|standard|detailed",
        "audience": str | None
    },
    "tasks": [                         # list[Task]
        {"id": "<TaskType 자유 문자열>", "priority": int, "params_override": {}}
    ],
    "meta": {                          # QueryMeta
        "confidence": float, "ambiguity": {"is_ambiguous": bool, "severity": str, ...},
        "missing": [str], "raw_input": str, "language": str, "original_domain": str|None
    }
}
```
> ⚠️ **TaskType / Source 는 open-vocab(자유 문자열)** — 고정 enum 아님. 예시 값: `data_collection`, `metric_calculation`, `analysis`, `comparison`, `insight_generation`, `summary_generation`, `report_generation`, `recommendation`, `factual_lookup`.
> ⚠️ `brand` 는 `targets.brand` 중첩 — `structured_query["brand"]` 최상위 접근 아님.
> `layer_guard.py::inspect_layer_output` 의 `sq.get("brand")` 는 최상위 접근이라 항상 None → COGNITIVE_EMPTY_QUERY 는 실질적으로 `tasks` 비어있음만 검사 (검증 사이클 2 발견).

### 3.2 Planning

| 항목 | 내용 |
|------|------|
| **Input** | `structured_query` |
| **Output** | `{"plan": <Plan.model_dump>}` (정상) 또는 `{"response": {...}}` (reject) 또는 `{"error": ...}` |
| **Interrupt** | `plan_review` (Planning 종료 후 `interrupt()` 호출) |
| **코드** | `backend/app/dream_agent/planning/planning_stage.py::planning_stage` |

**Plan 스키마** — 진실 소스: `backend/app/dream_agent/planning/planner.py` (`Plan` + `PlannedTodo`)
```python
{
    "teams_selected": [str],           # Stage 1 선택 팀
    "todos": [                         # list[PlannedTodo]
        {
            "id": str,
            "task_type": str,          # ⚠️ "task" 아님
            "team": str | None,
            "agent": str | None,
            "tool": str | None,
            "tool_params": {},
            "depends_on": [str],
            "priority": int,           # 1=최우선
            "rationale": str
        }
    ],
    "dag": {todo_id: [depends_on_ids]},   # ⚠️ "dependency_graph" 아님
    "plan_notes": str
}
```
> ⚠️ 이전 버전 문서에 있던 `plan_id` / `intent_summary` / `strategy` / `estimated_duration_sec` / `mermaid_diagram` / `visualization` 필드는 **실제 `Plan` 모델에 없음** (검증 사이클 2 정정). 프론트 `schemas.ts` Plan 타입은 위 실제 구조로 작성할 것.

### 3.3 Execution

| 항목 | 내용 |
|------|------|
| **Input** | `plan` + `execution_progress` (Sprint 12 HITL pause/resume 영속화) |
| **Output** | `{"execution_result": <ExecutionResult>, "execution_progress": <ExecutionProgress>}` |
| **Interrupt** | `execution_pause` (사용자 pause 요청 시 Phase 사이 interrupt) |
| **코드** | `backend/app/dream_agent/execution/execution_stage.py::execution_stage` |

**ExecutionResult 스키마** — 진실 소스: `backend/app/dream_agent/schemas/execution_result.py`
```python
{
    "plan_id": str,
    "todos": {                         # dict[str, TodoResult]
        todo_id: {
            "todo_id": str, "task_type": str,
            "tool": str|None, "agent": str|None,
            "status": "pending|in_progress|completed|failed|skipped",   # ⚠️ TodoStatus enum
            "data": {}, "error": str|None,
            "is_mock": bool,           # stub Tool 이 mock 반환했는지
            "started_at": float, "ended_at": float, "duration_ms": float
        }
    },
    "phase_timings": [{"phase": int, "duration_ms": float, ...}],
    "total_duration_ms": float,
    "overall_status": "completed|failed",     # ⚠️ TodoStatus enum — "success"/"partial" 아님
    "halted_at": str | None,           # 실패한 todo_id
    "halt_reason": str | None
}
```
> ⚠️ `status` / `overall_status` 값은 `TodoStatus` enum (`completed`/`failed`/...) — **`"success"` 값은 존재하지 않음**.
> 🔴 **백엔드 버그 (검증 사이클 2 발견)**: `layer_guard.py::inspect_layer_output` 의 execution 검사가 `t.get("status") == "success"` 를 보는데, 실제 값은 `"completed"` → `succeeded` 리스트가 항상 비어 **부분 실패가 EXECUTION_ALL_FAILED(fatal) 로 오분류**됨. 백엔드 수정 필요 (문서 작업 범위 밖, 사용자 결정 대기).

### 3.4 Response

| 항목 | 내용 |
|------|------|
| **Input** | `execution_result`, `structured_query`, `plan`, `language` |
| **Output** | `{"response": <ResponsePayload>}` |
| **코드** | `backend/app/dream_agent/response/responder.py::response_stage` |

**ResponsePayload 스키마** — 진실 소스: `backend/app/dream_agent/schemas/response_payload.py`
```python
{
    "format": "text|pdf|image|chart|video|mixed|error",   # ⚠️ ResponseFormat enum — "markdown" 없음
    "text": str,              # 메인 텍스트 응답 (항상 존재)
    "summary": str | None,    # 1~2 문장 핵심 요약
    "next_actions": [str],    # 추천 후속 작업
    "attachments": [          # list[Attachment]
        {"kind": str, "path": str|None, "url": str|None, "caption": str|None, "meta": {}}
    ],
    "meta": {},               # 처리 시간, 완료 Todo 수 등
    "error": str | None       # format=error 일 때
}
```

---

## 4. AgentState Contract

상세: `11_main_graph_state_v1.5.md`

### 4.1 초기화 (Sprint 13 I6)

```python
from app.dream_agent.states.agent_state import init_agent_state

state = init_agent_state(
    user_input="도메인 작업 요청",
    conversation_id="conv_xxx",
    turn_id="turn_yyy",
    user_id="demo",                 # Settings fallback
    language="ko",
    conversation_history=[],        # Sprint 15에서 MemoryManager가 채움
    history_limit=3,                # Settings fallback
)
```

### 4.2 Reader/Writer 매트릭스

`11_main_graph_state_v1.5.md §3` 참조. 핵심:
- `ws_agent` — Sprint 13 식별 필드 writer (`init_agent_state` 시점)
- `cognitive` — structured_query writer, conversation_history/user_input/language reader
- `planning` — plan writer
- `execution` — execution_result/execution_progress writer
- `response` — response writer
- `hitl_manager` — plan/execution_progress reader/writer (PM)

### 4.3 thread_id (LangGraph Checkpointer 키)

```python
thread_id = f"{conversation_id}_{turn_id}"
config = {"configurable": {"thread_id": thread_id}}
```

헬퍼: `api.thread_id.make_thread_id(conversation_id, turn_id)` (Sprint 13 T3).

---

## 5. Error Contract

Sprint 13 I11-a에서 **severity/layer 필드 통일**. 모든 에러는 아래 필드 포함:

```python
{
    "type": "error",
    "code": str,                                                    # 카테고리 코드
    "layer": "transport"|"cognitive"|"planning"|"execution"|"response"|"runtime",
    "severity": "fatal"|"warning",
    "message": str,                                                 # 사용자 표시용
    "detail": dict,                                                 # 디버그/추가 컨텍스트 (선택)
    "conversation_id": str,                                         # fan-out error만 (direct-WS는 생략 가능)
    "turn_id": str,                                                 # fan-out error만
}
```

### 5.1 Error Code 목록 — `error` 이벤트용 (8개)

아래 8개는 `/ws/agent` 의 `error` 이벤트로 emit 되는 코드. **전체 11개 카탈로그(+ `TODO_EDIT_NOT_PAUSED`/`INVALID_DAG`/`NL_INTENT_UNCLEAR` — 이 3개는 `error` 이벤트가 아니라 `hitl_ack.code` 로 전달)** 는 `22_error_codes_v1.1.md` 와 진실 소스 `backend/app/core/error_codes.py` 참조.

| code | layer | severity | 발생 경로 |
|------|-------|----------|-----------|
| `INVALID_MESSAGE` | transport | fatal | `_parse_query_message` (direct-WS) |
| `CONCURRENT_LIMIT_EXCEEDED` | transport | fatal | `run_turn` slot 초과 (fan-out) |
| `EXECUTION_ERROR` | runtime | fatal | `run_turn` try/except (fan-out) |
| `COGNITIVE_EMPTY_QUERY` | cognitive | fatal | layer guard (fan-out) |
| `PLANNING_EMPTY_PLAN` | planning | fatal | layer guard (fan-out) |
| `EXECUTION_ALL_FAILED` | execution | fatal | layer guard (fan-out) |
| `EXECUTION_PARTIAL_FAILED` | execution | warning | layer guard (fan-out) |
| `RESPONSE_EMPTY` | response | fatal | layer guard (fan-out) |

### 5.2 fatal/warning 동작 차이

- **fatal** (layer guard): `complete(status="aborted", reason=code)` emit 후 run_turn 종료
- **warning** (layer guard): 그래프 계속 진행. `complete.data.guard_warnings` 에 누적
- **fatal** (transport/runtime): run_turn 조기 종료 (CONCURRENT/EXECUTION_ERROR) 또는 메시지 거부 (INVALID_MESSAGE)

### 5.3 JSONL 로그 (POC 페어 누적)

모든 layer guard 발견 사항은 `logs/layer_guard.jsonl` 에 append:
```jsonl
{"ts":"2026-04-21T01:23:45Z","conv_id":"c1","turn_id":"t1","user_id":"demo","layer":"planning","code":"PLANNING_EMPTY_PLAN","severity":"fatal","message":"...","detail":{...},"state_summary":{...}}
```

Sprint 15 Memory 도입 시 DB로 이관 예정.

---

## 6. Session/Thread 식별 체계 (Sprint 13 확정)

| 용어 | 생성 | 수명 | 용도 |
|------|------|------|------|
| `user_id` | 클라 (URL query) | 영구 (localStorage) | 사용자 식별, broadcast fan-out 키 |
| `conversation_id` | 클라 (`crypto.randomUUID`, localStorage 저장) | 사용자가 "새 대화" 누를 때까지 | 대화방 단위 |
| `turn_id` | 클라 (매 쿼리마다 새 UUID) | 쿼리 1회 | 쿼리 단위 + HITL signal 키 |
| `thread_id` | 서버 (`make_thread_id`) | Checkpoint 영속 | LangGraph Checkpointer 키 |
| `session_id` (**deprecated**) | 내부 alias of turn_id | — | Sprint 12 호환만 유지, 외부 계약 사용 금지 |

---

## 7. 하위 호환 정책

| 영역 | Sprint 13 | Sprint 14 계획 |
|------|-----------|---------------|
| `type: "start"` legacy 경로 | 유지 | 제거 검토 |
| `session_id` 필드 | 내부 alias 유지 | 유지 |
| Sprint 12 대시보드 이벤트 (`layer_start`, `todo_start`, `todo_complete`, `progress`) | **신 경로에서도 emit** (I11-b2 — callback_manager bridge) | `layer_complete` 등 추가 이벤트 Sprint 14 검토 |

---

## 8. 코드 참조

| 기능 | 파일 |
|------|------|
| `init_agent_state` | `backend/app/dream_agent/states/agent_state.py` |
| `StructuredQuery` | `backend/app/dream_agent/schemas/structured_query.py` |
| `Plan` + `PlannedTodo` | `backend/app/dream_agent/planning/planner.py` |
| `ExecutionResult` | `backend/app/dream_agent/schemas/execution_result.py` |
| `ResponsePayload` | `backend/app/dream_agent/schemas/response_payload.py` |
| `ExecutionProgress` | `backend/app/dream_agent/workflow_managers/hitl_manager/manager.py:20` (dataclass) |
| `prepare_cognitive_prompt` | `backend/app/dream_agent/cognitive/cognitive_stage.py` |
| `make_thread_id` | `backend/api/thread_id.py` |
| Layer Guard | `backend/app/dream_agent/system_graph/layer_inspector.py` |

---

## 변경 이력

> 프레임워크 추출(2026-06-19) 이전(마케팅 도메인 시기)의 상세 변경 이력은 git 히스토리를 참조하세요.
