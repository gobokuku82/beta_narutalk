# Sprint 14 A3 — 시스템 동작 Walkthrough

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-24 |
| 대상 Sprint | Sprint 14 A3 Phase 5 완료 시점 (commit `75aa753` 이후) |
| 목적 | 서버 기동부터 Turn 종료까지 **어디서 / 어떤 신호가 / 어떤 함수가 / 어떤 분기에서 / 왜 / 기대 응답** 을 서사형으로 추적. 의도 ↔ 구현 대조 지도. |
| 독자 | 프로젝트 오너 (비전문가), 신규 협업자, Claude 재진입 시 context |
| 형식 | **L1 (한 줄 요약) / L2 (중급) / L3 (상세)** 3단계. 시스템 측 + 사용자 측 분리 |

---

## 0. 이 문서 읽는 법

### 0.1 3-Layer 구조

- **L1**: 한 줄 — 이 단계가 뭘 하는지
- **L2**: 5~10줄 — 일반적 이해
- **L3**: 상세 표·분기·이유·로그 예시

먼저 §1~§10 의 L1 만 훑어 전체 감 → 궁금한 곳의 L2/L3 파고들기.

### 0.2 관점 분리

각 단계는 **시스템 측** (코드가 뭘 하나) + **사용자 측** (브라우저가 뭘 보이나 / 가능한 액션) 으로 분리. 사용자 의도 ↔ 실제 동작 대조용.

### 0.3 이 문서 활용 예

- **리뷰**: "§6 편집 분기가 내 의도랑 맞나?" 읽고 판단 → 안 맞으면 Claude 에게 지적
- **테스트**: L3 의 "분기" 표를 기준으로 unit test 빠진 것 발견
- **onboarding**: 신규 협업자가 이 문서 1개만 읽으면 A3 범위 파악 가능
- **ADR 도출**: "이 분기를 왜 이렇게 설계했나" 의 이유들을 모아 정식 ADR 작성

---

## 1. 서버 기동

### 1.1 L1

`run_server_v2.py` 실행 시 Uvicorn 이 포트 8001 에 뜨고, PostgreSQL Checkpointer · LangGraph 그래프가 준비된 채 클라 연결 대기. Manager 싱글톤과 AgentPool 은 **이 시점엔 아직 로드 안 됨** (첫 호출 시 lazy init).

### 1.2 L2

`backend/api_v2/main.py::lifespan` 훅이 서버 시작 시 **한 번만** 수행:

1. `AsyncPostgresSaver.from_conn_string(settings.CHECKPOINT_DB_URI)` → `setup()` 호출 → Checkpoint 테이블 자동 생성
2. `build_graph(checkpointer=checkpointer)` → LangGraph StateGraph 빌드 (cognitive → planning → execution → response 4 노드)
3. `app.state.checkpointer`, `app.state.graph` 에 저장

PostgreSQL 연결 실패 시 `RuntimeError` 로 서버 기동 중단 (fail-fast). 성공 시 `yield` 이후 Uvicorn 이 `/ws/agent`, `/ws/hitl`, `/dashboard` endpoint 를 accept 대기.

### 1.3 L3 상세

#### 시스템 측

| 요소 | 내용 |
|------|------|
| **실행 파일** | [`run_server_v2.py`](../../run_server_v2.py) (8001 포트) |
| **FastAPI 앱 팩토리** | [`backend/api_v2/main.py::create_app`](../../backend/api_v2/main.py) |
| **lifespan 훅** | [`main.py:26-57`](../../backend/api_v2/main.py) — Checkpointer + Graph 만 init |
| **Graph 빌더** | `backend/app/dream_agent/system_graph/builder.py::build_graph(checkpointer)` — 4 노드 + edge + interrupt 설정 |
| **Checkpoint DB** | `settings.CHECKPOINT_DB_URI` (기본: `postgresql://...`) |
| **등록 라우터** | `health_router`, `ws_agent_router`, `ws_hitl_router` |
| **StaticFiles** | `/dashboard` — `dashboard/index.html` 서빙 |

#### 시스템 측 — 메모리 초기 상태

```python
app.state.checkpointer = <AsyncPostgresSaver>      # lifespan 에서 설정
app.state.graph        = <Compiled LangGraph>      # lifespan 에서 설정

# Manager 싱글톤 5개 — lazy, 첫 호출 시 생성
# (lifespan 에선 생성 안 됨)
conn_manager = <ConnectionManager 싱글톤 모듈 레벨>  # 이미 import 시 생성 (api_v2/connection_manager.py)
_hitl_manager = None                               # 첫 get_hitl_manager() 시 생성
_callback_manager = None                           # 첫 get_callback_manager() 시 생성
_todo_manager = None                               # 첫 get_todo_manager() 시 생성
concurrency = <ConcurrencyManager 싱글톤>           # 모듈 import 시 생성

# AgentPool — lazy (첫 get_agent_pool() 시 team_catalog.yaml 로드)
AgentPool._instance = None                         # 아직 load 안 됨
```

**주의 (memory drift 정정)**: 기존 memory `project_eager_agent_init.md` 에는 "서버 부팅 시 AgentPool eager init" 이라 되어있지만, **실제 코드는 lifespan 에서 AgentPool 을 건드리지 않음**. `get_agent_pool()` 첫 호출 (execution 진입 시) 에 yaml 메타데이터만 load, 실제 Tool 인스턴스는 더 lazy (`get_real_tool` 호출 시). 즉 "lazy with catalog-preload" 가 정확한 표현.

#### 시스템 측 — 분기

| 조건 | 결과 |
|------|------|
| PostgreSQL 연결 성공 | lifespan `yield` 로 진행, Uvicorn accept 대기 |
| PostgreSQL 연결 실패 | `logger.error` 3개 안내 + `RuntimeError` raise → **서버 기동 실패** |
| `.env` 의 `CHECKPOINT_DB_URI` 누락 | settings 검증에서 전 단계 실패 |

#### 사용자 측

- 터미널 1 에서 `uv run python run_server_v2.py` 실행
- 출력 예:
  ```
  ADALLPIN v2 server starting at http://localhost:8001
  INFO: Initializing Checkpointer (PostgreSQL)...
  INFO:   DB URI: postgresql://postgres:...
  INFO: ✅ Checkpointer connected + Graph compiled with PostgreSQL
  INFO: Application startup complete.
  INFO: Uvicorn running on http://0.0.0.0:8001
  ```
- 이 상태에서 브라우저 접속 가능. 아직 아무 Manager 도 메모리 안 씀

#### 왜 이렇게 설계했나

- **Checkpointer 는 lifespan 에서 eager**: LangGraph 빌드 시 Checkpointer 가 필요하므로 지연시킬 수 없음
- **Manager 는 lazy**: 쿼리 없으면 빈 dict 만 유지하는 자원인데 굳이 미리 생성할 필요 없음
- **AgentPool 은 lazy with catalog-preload**: yaml 로드는 가볍지만 서버 부팅 시간 늘림. 첫 쿼리 시 load 해도 execution 진입 전이라 사용자 체감 지연 없음

#### 기대 응답

- 로그에 `Application startup complete.` + `Uvicorn running on http://0.0.0.0:8001`
- `curl http://localhost:8001/health` 호출 시 200 응답

---

## 2. 클라이언트 접속

### 2.1 L1

브라우저가 `http://localhost:8001/dashboard` 접속 → HTML + JS 로드 → 자동으로 `/ws/agent`, `/ws/hitl` 2개 WebSocket 연결 → 서버 `conn_manager._connections[user_id]` 에 두 WS 등록됨.

### 2.2 L2

[`dashboard/index.html`](../../dashboard/index.html) 의 JS 가 페이지 로드 시:

1. `new WebSocket("ws://localhost:8001/ws/agent?user_id=demo")` — 이벤트 수신 채널
2. `new WebSocket("ws://localhost:8001/ws/hitl?user_id=demo")` — 명령 송신 채널

서버 측 [`ws_agent.py::stream_endpoint`](../../backend/api_v2/ws_agent.py) / [`ws_hitl.py::hitl_endpoint`](../../backend/api_v2/ws_hitl.py) 가 `accept()` 후 `conn_manager.connect(user_id, ws)` 호출. 최대 5 연결 초과 시 `close(1008)`.

연결 성공 시 각 채널에서 `{type:"connected", ...}` 메시지 수신 → UI 상태 "🟢 연결됨".

### 2.3 L3 상세

#### 시스템 측

| 이벤트 | 호출 함수 | 결과 |
|--------|-----------|------|
| ws_agent 접속 | `stream_endpoint` accept + `conn_manager.connect(user_id, ws)` | `_connections["demo"].append(ws_agent)` |
| ws_hitl 접속 | `hitl_endpoint` accept + `conn_manager.connect(user_id, ws)` | `_connections["demo"].append(ws_hitl)` |
| 동일 user 초과 연결 | 6번째 연결 시도 | `close(1008)` `connection_limit_exceeded` |
| 연결 해제 | `WebSocketDisconnect` 예외 | `conn_manager.disconnect(user_id, ws)` — idempotent |
| 송신 실패 (dead WS) | `broadcast_to_user` 중 예외 | 해당 ws 자동 제거 |

#### 시스템 측 — 싱글톤 접근

- `ConnectionManager` 는 모듈 레벨 싱글톤 (`conn_manager = ConnectionManager()` in `connection_manager.py`)
- 즉 이 시점에 `conn_manager._connections` 는 `{"demo": [<ws_agent>, <ws_hitl>]}` 같은 상태

#### 사용자 측

- UI: 우상단 "🟢 연결됨" 표시
- 브라우저 F12 Network → WS 필터: 2개 행 (ws/agent, ws/hitl), 상태 `101 Switching Protocols`
- 각 WS 첫 프레임: `{"type":"connected", "user_id":"demo", "timestamp":"..."}`

#### 사용자 측 — 분기

- 대시보드 접속 실패 → 서버가 안 떴거나 포트 오류
- "🔴 끊김" → `ws.onclose` 발동 → `setTimeout(connect, 3000)` 3초 후 재연결 루프
- 서버 재시작 후 브라우저가 재연결 시 `localStorage.last_turn_id` 가 있으면 `resume_query` 자동 전송

#### 왜 채널 2개인가

- **backpressure 분리**: 이벤트 스트림(agent)이 밀려도 사용자 명령(hitl)은 즉시 수신 가능
- **역할 분리**: agent = 서버→클라 push, hitl = 양방향 (클라→서버 명령 + 서버 ack)
- **Pause 중에도 수신**: execution_pause 로 agent 쪽이 interrupt 대기 중이어도 hitl 채널로 resume 수신 가능

#### 기대 응답

- 두 채널 모두 `connected` 프레임 수신
- 브라우저 Console `[wsAgent] connected`, `[wsHitl] connected` 로그 (디버그 모드)

---

## 3. 쿼리 입력

### 3.1 L1

사용자가 입력란에 자연어 쿼리 입력 + 전송 → `wsAgent` 로 `{type:"query", conversation_id, turn_id, user_input}` 송신 → 서버가 **독립 asyncio task (run_turn)** 생성 → LangGraph 실행 시작.

### 3.2 L2

클라 측: [`dashboard/index.html::sendMessage`](../../dashboard/index.html) 가 호출됨 (L361). 전송 버튼 `onclick` 또는 Enter 키로 triggered. `conversation_id`, `turn_id` 생성 (`crypto.randomUUID`) 후 `wsAgent.send` 로 송신.

서버 측: `ws_agent.py::stream_endpoint` 의 무한 루프에서 `msg_type == "query"` 분기 진입:
1. `_parse_query_message(data)` → 검증
2. 실패 시 → `INVALID_MESSAGE` direct-WS 반환 (이 WS 한 곳에만)
3. 성공 시 → `asyncio.create_task(run_turn(user_id, conv_id, turn_id, payload, app=...))` 로 독립 task spawn
4. 즉시 다음 메시지 받을 준비 (async 병렬)

`run_turn` 은 끝나지 않고 backgrounder 에서 계속 진행 — Graph astream 루프 전부 여기서 일어남.

### 3.3 L3 상세

#### 시스템 측 — `_parse_query_message` 검증

| 조건 | 결과 |
|------|------|
| `conversation_id` 누락/빈 문자열 | `INVALID_MESSAGE` direct-WS |
| `turn_id` 누락/빈 문자열 | `INVALID_MESSAGE` direct-WS |
| `user_input` 누락 (None) | `INVALID_MESSAGE` direct-WS |
| `user_input` 빈 문자열 "" | **허용** (그래프가 처리, layer_guard 가 나중에 잡음) |
| 모두 OK | `{"conversation_id", "turn_id", "payload"}` 반환 |

#### 시스템 측 — `run_turn` 진입

[`ws_agent.py::run_turn`](../../backend/api_v2/ws_agent.py) 실행:

```python
# 1. slot 점유
if not concurrency.try_acquire(user_id, turn_id):
    # → fan-out CONCURRENT_LIMIT_EXCEEDED → return
# 2. 활성 turn 등록
get_hitl_manager().register_turn(turn_id)
    # → _active_turns.add(turn_id)
# 3. graph runner 호출
await _graph_runner_with_resume(user_id, conv_id, turn_id, payload, _app=app)
# 4. finally
concurrency.release(user_id, turn_id)
get_hitl_manager().cleanup_turn(turn_id)
    # → _resume_queues.pop, _active_turns.discard,
    #   _paused.discard, _session_locks.pop, _progress.pop (Phase 5 신규)
get_callback_manager().unregister(turn_id)
```

#### 시스템 측 — 메모리 스냅샷 (쿼리 1개 수신 직후)

```python
conn_manager._connections   = {"demo": [<ws_agent>, <ws_hitl>]}
concurrency._slots          = {"demo": {"turn_abc123"}}   # slot 점유
hitl._active_turns          = {"turn_abc123"}              # run_turn 등록
hitl._progress              = {}                           # 아직 없음
hitl._paused                = set()                        # 아직 없음
hitl._resume_queues         = {}                           # 아직 없음
```

#### 시스템 측 — 분기

| 조건 | 결과 | 사용자에게 보이는 것 |
|------|------|---------------------|
| 검증 실패 | `INVALID_MESSAGE` direct-WS | 다른 탭 영향 없이 이 WS 만 에러 |
| slot 초과 (4번째 동시 쿼리) | `CONCURRENT_LIMIT_EXCEEDED` fan-out | 다른 탭도 에러 표시됨 |
| 정상 | `run_turn` 백그라운드 실행 | 수 초 내 `node_event(cognitive)` 수신 |

#### 사용자 측

- 입력: 입력란에 자연어 입력 후 [전송] 클릭 또는 Enter
- UI 변화:
  - 전송 버튼이 "취소" 로 바뀜 ([dashboard/index.html:392](../../dashboard/index.html))
  - `agentRunning = true` 플래그 세팅
  - `localStorage.set("octormate.last_turn_id", turn_id)` (R-9 복원 대비)
- F12 Network → `/ws/agent` 메시지:
  - 송신: `{"type":"query", "conversation_id":"conv_...", "turn_id":"turn_...", "user_input":"..."}`

#### 사용자 측 — 가능 액션

- 정상 흐름 진행 시: §4 로
- 취소 버튼 클릭 → `cancel` 타입 wsHitl 송신 (pause/cancel 는 §9 참조)
- 다른 탭에서 다른 쿼리 → slot 최대 3 까지 병행 가능

#### 왜 독립 task 로 분리했나

- WebSocket 연결과 쿼리 실행을 **생명주기 분리**: interrupt 대기 중에도 WS 는 다른 메시지 받을 수 있어야 함 (pause, todo_delete 등)
- 한 WS 가 쿼리 1개 처리 중이라고 다음 쿼리 전송 막히면 UX 나쁨
- `asyncio.create_task` 는 fire-and-forget. 서버가 task 참조를 명시적으로 잡지 않아도 loop 가 관리

#### 기대 응답

- 서버 로그: `run_turn entered`, `concurrency acquired`, `register_turn turn_abc`
- 수 초 내 브라우저에 `node_event(cognitive)` 수신 → Todo 목록 윤곽 나타남

---

## 4. Graph 실행 (cognitive → planning)

### 4.1 L1

LangGraph `agent.astream(state, config)` 루프에서 각 노드 완료 시 `chunk` 가 emit → 서버가 `node_event` 로 변환해 **conn_manager.broadcast_to_user** 로 같은 user 모든 탭에 fan-out.

### 4.2 L2

`_graph_runner_with_resume` 의 1차 astream 루프 ([ws_agent.py:341](../../backend/api_v2/ws_agent.py)):

```python
async for chunk in agent.astream(state, config=config):
    event = _chunk_to_event(chunk, conv_id, turn_id)
    if event:
        await conn_manager.broadcast_to_user(user_id, event)
    # layer_guard.inspect_layer_output — fatal 시 abort
```

노드별 순서:
1. **cognitive** → 자연어 → StructuredQuery 변환 (LLM 1~2 호출)
2. **planning** → StructuredQuery → Plan (todos + DAG) 생성 (LLM 1~2 호출)
3. planning 끝에 `interrupt({type:"plan_review", plan, message})` 발동 → §5

각 단계 끝에서 `layer_guard.inspect_layer_output` 이 실행됨. fatal (예: `COGNITIVE_EMPTY_QUERY`) 감지 시 즉시 abort + `complete(aborted, reason=<code>)` 송신.

### 4.3 L3 상세

#### 시스템 측 — 노드별 동작

| 노드 | 호출 함수 | 입력 | 출력 |
|------|-----------|------|------|
| cognitive | `cognitive/cognitive_stage.py::cognitive_stage` | `state.user_input` | `state.structured_query` |
| planning | `planning/planning_stage.py::planning_stage` | `state.structured_query` | `state.plan` + `interrupt(plan_review)` |

#### 시스템 측 — `_chunk_to_event`

LangGraph 의 chunk 형태는 `{"cognitive": {...state update...}}` 같은 dict. `_chunk_to_event` 가 이를 `{"type":"node_event", "node":"cognitive", "data":...}` 로 변환. `__interrupt__` 나 `__end__` chunk 는 None 반환 (클라 송신 skip).

#### 시스템 측 — 콜백 브릿지 (execution 때 활용)

`_graph_runner_with_resume` 진입 시 ([ws_agent.py:275](../../backend/api_v2/ws_agent.py)):
```python
cb_manager.unregister(turn_id)       # 중복 방지
cb_manager.register(turn_id, _callback_bridge)
```

`_callback_bridge` 는 executor 가 emit 한 `todo_start/complete/progress` 를 `conn_manager.broadcast_to_user` 로 forward. cognitive/planning 단계에선 emit 없음. execution 진입 후 활용됨.

#### 시스템 측 — Layer Guard

각 노드 완료 시 `layer_guard.inspect_layer_output(node, data)`:

| Guard code | layer | severity | 조건 |
|-----------|-------|----------|------|
| `COGNITIVE_EMPTY_QUERY` | cognitive | fatal | `structured_query` 비어있음 |
| `PLANNING_EMPTY_PLAN` | planning | fatal | `plan.todos` 없음 |
| `EXECUTION_PARTIAL_FAILED` | execution | warning | 일부 todo 실패 |
| `EXECUTION_ALL_FAILED` | execution | fatal | 모든 todo 실패 |
| `RESPONSE_EMPTY` | response | fatal | `response` 비어있음 |

fatal 시: `_emit_complete("aborted", reason=code)` → `run_turn` 종료

#### 시스템 측 — 메모리 변화

노드 완료마다 `final_state.update(node_state)` — walkthrough 의 이후 단계에서 final_state 참조에 사용.

#### 사용자 측

- Todo 목록 카드가 단계별로 "빈 상자" → "cognitive 완료" → "planning 완료" 채워짐
- F12 Network `/ws/agent` 수신:
  ```json
  {"type":"node_event","node":"cognitive","conversation_id":"...","turn_id":"...","data":{"structured_query":{...}}}
  {"type":"node_event","node":"planning","conversation_id":"...","turn_id":"...","data":{"plan":{...}}}
  ```

#### 사용자 측 — 분기

| 조건 | UI 반응 |
|------|---------|
| cognitive fatal (빈 쿼리) | 에러 토스트 + complete(aborted) 수신 + idle 복귀 |
| planning fatal (빈 플랜) | 에러 토스트 + complete(aborted) |
| 정상 | 다음 단계 (§5 Plan review) |

#### 왜 fan-out (broadcast) 인가

- 같은 user 가 여러 탭 열어도 이벤트 동일 전달
- `ConnectionManager._connections[user_id]` 에 list 로 WS 여러 개 유지
- 송신 실패 시 해당 WS 자동 제거 (dead WS 정리)

#### 기대 응답

- 서버 로그: `cognitive done`, `planning done teams=[...] todos=N issues=0`
- 브라우저에 Todo 목록 UI 나타남 (아직 모달은 안 뜸)

---

## 5. Plan review interrupt (Phase 5 핵심)

### 5.1 L1

planning 노드가 `interrupt({type:"plan_review", plan, message})` 호출 → Checkpoint 저장 + astream 중단 → 서버가 **임시 `_progress` 생성 (status="paused")** → `hitl_request` broadcast → 브라우저에 Plan review 모달 자동 팝업.

### 5.2 L2

[`planning/planning_stage.py:72`](../../backend/app/dream_agent/planning/planning_stage.py) 에서 `interrupt()` 호출되면 LangGraph 가 state 를 Checkpoint 에 저장하고 astream 을 **멈춤**. 서버의 while 루프가 `agent.aget_state(config)` 로 pending interrupt 감지.

`_graph_runner_with_resume` ([ws_agent.py:381](../../backend/api_v2/ws_agent.py)) 의 plan_review 분기:

```python
if intr_type == "plan_review":
    # Sprint 14 A3 Phase 5 — 사용자 §4 "hitl=pause 같은 개념"
    plan_dict = intr_value.get("plan") or final_state.get("plan") or {}
    if plan_dict and not hitl.get_progress(turn_id):
        temp = hitl.create_progress(turn_id, plan_dict)
        temp.status = "paused"    # 편집 가능 상태
    await conn_manager.broadcast_to_user(user_id, {
        "type": "hitl_request",
        "conversation_id": conv_id, "turn_id": turn_id,
        "data": {**_build_hitl_request_data(...), "turn_id": turn_id, ...}
    })
```

이후 `hitl.wait_for_resume(turn_id, timeout=...)` 로 사용자 응답 대기.

클라 [`handleEvent`](../../dashboard/index.html) (L448) 가 `hitl_request` 수신 → `handleHitlRequest` (L904) → `openHitlModal("plan_review", data)` (L599) 로 모달 표시.

### 5.3 L3 상세

#### 시스템 측 — interrupt 감지

[`ws_agent.py::_has_pending_interrupts`](../../backend/api_v2/ws_agent.py):
```python
def _has_pending_interrupts(gs) -> bool:
    if getattr(gs, "next", None): return True
    tasks = getattr(gs, "tasks", None)
    if tasks:
        for t in tasks:
            if getattr(t, "interrupts", None): return True
    return False
```

→ `gs.next` 가 비어도 `gs.tasks[].interrupts` 가 있으면 True. 같은 노드에서 resume 후 재interrupt 시 `.next` 가 빈 경우가 있어서 이 2중 체크 필요.

#### 시스템 측 — 임시 progress 생성 (Phase 5 신규)

`HITLManager.create_progress(turn_id, plan)` 호출 결과:

```python
_progress[turn_id] = ExecutionProgress(
    session_id=turn_id,
    plan=plan_dict,
    phases=tm._build_phases_from_plan(plan_dict),
    completed_todos={},
    status="running",   # 기본. 이후 temp.status = "paused" 로 덮어씀
    paused_at_phase=None,
)
```

그 직후 `temp.status = "paused"` 설정. 왜 이 순서? `create_progress` 는 `_paused` 체크로 status 결정하는데 plan_review 시점엔 `_paused` 에 없어서 기본 `"running"` 으로 생성됨 → 명시 override 필요.

#### 시스템 측 — `_build_hitl_request_data`

[`ws_agent.py:118-128`](../../backend/api_v2/ws_agent.py):
```python
{
    "request_id": f"req_{uuid.uuid4().hex[:8]}",
    "plan": _json_safe(plan),
    "options": ["approve", "reject", "modify"],
    "message": intr_value.get("message") or f"{todo_count}개 Todo 실행 계획...",
}
```

+ broadcast 시 `data` dict 에 `turn_id`, `conversation_id` 도 포함 (Phase 4 fallback 제거 계약).

#### 시스템 측 — wait_for_resume 대기

`hitl.wait_for_resume(turn_id, timeout=settings.HITL_RESUME_TIMEOUT_SEC)` 호출. `_resume_queues[turn_id]` 의 asyncio.Queue 에서 사용자 응답 대기. 기본 timeout 1800초 (30분).

#### 시스템 측 — 메모리 스냅샷 (plan_review interrupt 직후)

```python
hitl._active_turns = {"turn_abc"}
hitl._progress     = {"turn_abc": ExecutionProgress(status="paused", completed={}, plan=<...>, phases=[[...], ...])}
hitl._resume_queues = {"turn_abc": <asyncio.Queue 비어있음>}
```

#### 시스템 측 — 분기

| 조건 | 결과 |
|------|------|
| 정상 plan_review | 임시 progress 생성 + broadcast + wait_for_resume |
| `plan_dict` 빈 경우 | `if plan_dict and ...` 가드 — progress 생성 skip, broadcast 는 진행 |
| `hitl.is_paused(turn_id) == True` (사용자가 cognitive 중 pause 눌렀을 때) | **auto-approve 경로** — `Command(resume={"action":"approve"})` 자동 주입, 모달 안 뜸 |
| timeout (30분 무응답) | `{"action":"timeout"}` 수신 → `Command(resume={"action":"reject"})` 주입 → `complete(aborted, reason="hitl_timeout")` |

#### 사용자 측

- UI: 모달 자동 팝업 (어두운 overlay + 중앙 카드)
- 모달 헤더: "✋ Plan Review — 실행 계획 승인"
- 모달 본문: Todo 목록 (각 행에 🗑 + ≡ 드래그 핸들) + 🗣 자연어 textarea + [✅ 승인] / [❌ 거부] 버튼
- F12 Network `/ws/agent` 수신:
  ```json
  {"type":"hitl_request","conversation_id":"...","turn_id":"...",
   "data":{"request_id":"req_...","plan":{...},"options":["approve","reject","modify"],"message":"...","turn_id":"...","conversation_id":"..."}}
  ```

#### 사용자 측 — 가능 액션

- **편집** (🗑 / ≡ / + / 🗣) → §6 으로
- **승인** (✅) → §7 로 (approve 경로)
- **거부** (❌) → §7 로 (reject 경로)
- **30분 무응답** → 자동 aborted (timeout)

#### 왜 Phase 5 에서 임시 progress 생성하는가

- 사용자 요구사항 §4 "hitl/pause 는 같은 개념"
- plan_review 와 execution_pause 가 편집 측면에서 **완전히 같은 경로** 로 흐르도록 하려면 `_progress[turn_id]` 존재 전제가 동일해야 함
- 기존: plan_review 때만 `_progress` 가 없어서 `_handle_todo_*` 의 pause 분기가 진입 안 됨 → 편집 실패
- 해결: interrupt 직후 plan 으로 임시 progress 생성 → ws_hitl 핸들러가 단일 pause 분기로 처리

#### 기대 응답

- 모달이 자동 팝업 (사용자 클릭 없이)
- 서버 로그: `progress created ... todos=N`
- 브라우저 Console: `[hitl] hitl_request received`

---

## 6. Plan review — 편집 (구조화 / NL)

### 6.1 L1

사용자가 모달에서 🗑·드래그·+ (구조화) 또는 🗣 (자연어) 편집 → wsHitl 로 `todo_{modify|delete|add|edit_nl}` 전송 → 서버가 `progress.plan` 직접 mutate → `hitl_ack` 로 cascade + 업데이트된 plan 반환 → UI 에서 🔴 tint + ⛓ 라벨 렌더.

### 6.2 L2

**구조화 경로 (🗑 예시)**:
- 클라 `sendTodoDelete(todoId)` (L779) → `wsHitl.send({type:"todo_delete", data:{session_id, turn_id, todo_id}})`
- 서버 `_handle_todo_delete` ([ws_hitl.py:333](../../backend/api_v2/ws_hitl.py)):
  1. `_check_turn_active` (FR-13c 가드)
  2. 입력 검증 (session_id, todo_id 필수)
  3. `async with hitl._get_lock(session_id):` (D9 L1)
  4. `progress.status == "paused"` 확인 (Phase 5 이후 항상 True)
  5. `hitl.handle_todo_delete` → `tm.calculate_cascade` → plan mutate + phases rebuild
  6. `hitl_ack` 송신 (accepted, plan, invalidated, preserved, issues)
- 클라 `handleHitlAckTodo` → `renderCascade` → 🔴 tint + ⛓ 라벨

**자연어 경로**:
- 🗣 textarea 입력 + [⚡ 적용] → `sendTodoEditNl(instruction)` (L817) → `wsHitl.send({type:"todo_edit_nl", data:...})`
- 서버 `_handle_todo_edit_nl` ([ws_hitl.py:482](../../backend/api_v2/ws_hitl.py)):
  1. 가드 + 검증
  2. `async with _get_lock:`
  3. `progress.plan` dict → Pydantic `Plan.model_validate`
  4. `plan_editor.parse_instruction` — LLM 1회 호출 (~1~3초)
  5. `action == "unknown"` → `NL_INTENT_UNCLEAR` ack
  6. `plan_editor.validate_edit` — DAG 무결성
  7. `plan_editor.apply_edit` — Pydantic Plan mutate
  8. `tm._rebuild_dag` + `tm.calculate_cascade` → progress 반영
  9. `hitl_ack` 송신

### 6.3 L3 상세

#### 시스템 측 — 구조화 편집 4종 핸들러 공통 구조

| 단계 | 코드 | 실패 시 응답 |
|------|------|-------------|
| 1. `_check_turn_active` | [ws_hitl.py:48-86](../../backend/api_v2/ws_hitl.py) | `hitl_ack accepted:false, reason:"turn_not_active"` |
| 2. 입력 검증 | 각 핸들러 내부 | `error, code:"INVALID_MESSAGE"` |
| 3. Lock 획득 | `hitl._get_lock(session_id)` | (대기) |
| 4. progress 상태 확인 | `progress and progress.status == "paused"` | `hitl_ack accepted:false, code:"TODO_EDIT_NOT_PAUSED"` |
| 5. 실제 편집 | `hitl.handle_todo_{edit/delete/add}` | `result.error` 포함 시 accepted:false |
| 6. ack 송신 | `_safe_send` | — |

#### 시스템 측 — `calculate_cascade` (중요)

[`todo_manager/cascade.py`](../../backend/app/dream_agent/workflow_managers/todo_manager/):

```python
def calculate_cascade(todo_id, completed_todos, plan) -> CascadeResult:
    # 1. BFS: todo_id 의 downstream 찾기 (depends_on 역참조)
    # 2. invalidated_todos = [todo_id] + downstream  (공통)
    # 3. preserved_results = {id: result for id, result in completed_todos.items() if id not in invalidated}
    # 4. restart_from = invalidated_todos[0]  (UX 라벨용)
    return CascadeResult(invalidated_todos, preserved_results, restart_from)
```

**중요 (미믿 정정)**: `invalidated_todos` 는 `completed_todos` 여부와 **무관** — downstream BFS 결과 그대로 반환. `preserved_results` 만 `completed_todos` 로 필터링됨. 즉 plan_review 에서도 `invalidated` 는 비어있지 않음 (downstream 있으면).

#### 시스템 측 — 자연어 경로 L1/L2/L3 분기

| 분기 | 코드 위치 | 응답 |
|------|----------|------|
| Plan Pydantic 변환 실패 | `Plan.model_validate` 예외 | `hitl_ack accepted:false, reason:"Plan 변환 실패: ..."` (free-form) |
| LLM 호출 예외 | `parse_instruction` 예외 | `hitl_ack accepted:false, reason:"자연어 처리 중 오류: ..."` (free-form) |
| `parsed.action == "unknown"` | parse_instruction 응답 | `hitl_ack accepted:false, code:"NL_INTENT_UNCLEAR"` |
| `validate_edit` 실패 | DAG 무결성 위반 | `hitl_ack accepted:false, code:"INVALID_DAG"` |
| `apply_edit` 예외 | (reorder 시 new_position 오류 등) | `hitl_ack accepted:false, reason:"편집 적용 실패: ..."` |
| 성공 | — | `hitl_ack accepted:true, nl_action, invalidated, restart_from, preserved, issues, plan` |

#### 시스템 측 — Prompt Injection 방어 (D-13)

`plan_editor.parse_instruction` 은 user instruction 을 `_sanitize()` + `MAX_INSTRUCTION_LEN=500` 제한. 초과 시 action="unknown" + reason="명령 길이 초과".

#### 시스템 측 — 메모리 변화

편집 후:
```python
hitl._progress["turn_abc"].plan = <수정된 dict>    # 변경
hitl._progress["turn_abc"].phases = <rebuild>      # 변경
hitl._progress["turn_abc"].completed_todos         # 변화 없음 (비어있었음)
```

#### 사용자 측 — UI

- 🗑 클릭: `confirm()` → OK 시 `wsHitl.send` → ack 수신까지 **로딩 indicator 없음** (빠름)
- ≡ 드래그: HTML5 Drag&Drop API → 드롭 위치 결정 → `sendTodoEditNlReorder(fromId, toIdx)` 로 NL 경유
- + 클릭: `prompt()` 2회 (agent / task) → `sendTodoAdd`
- 🗣 textarea + [⚡ 적용]: `sendTodoEditNl` — 로딩 스피너 1~3초

ack 수신 후:
- `plan` 필드로 Todo 목록 다시 그림
- `invalidated` 배열을 `renderCascade` 에 전달 → 해당 Todo 행에 🔴 tint (배경색 `#450a0a`)
- `restart_from` 로 ⛓ "Todo X 부터 재실행" 라벨 (모달 상단)
- 통계 바: "N개 무효화 · M개 유지 · ⚠️ K issues"

#### 사용자 측 — 분기

| 시나리오 | UI 반응 |
|---------|---------|
| 🗑 성공 | 즉시 행 사라짐 + downstream 🔴 tint |
| 🗑 실패 (turn_not_active) | 토스트 "⚠️ 이 쿼리는 시간 초과로 종료되었습니다" + idle 복귀 |
| 🗣 "의미 불명" | 토스트 "⚠️ 어떤 작업을 원하시는지..." + textarea 내용 보존 |
| 🗣 LLM 타임아웃 | 토스트 free-form reason + textarea 보존 |
| 🗣 DAG 위반 | 토스트 "❌ 순환 의존성 발생" + 원 상태 유지 |

#### 왜 Lock 이 per-session 인가 (D9 L1)

- 같은 session 에 동시 편집 요청 (예: 🗑 연타) 시 → plan mutate race 위험
- `asyncio.Lock` 으로 직렬화 → 한 번에 하나만 처리
- per-session: 다른 user/turn 은 영향 없음 (글로벌 Lock 이면 전체 시스템 병목)
- LLM 호출 중에도 Lock 유지 (1~3초 블로킹) — L3 로 개선 여지 있지만 POC 단계 수용

#### 왜 cascade 자동 숨김 로직이 있는가

- Plan review 에선 `preserved` 가 항상 `{}` 이지만 `invalidated` 는 존재
- 기존 `renderCascade` 의 `invalidated.length === 0` 자동 숨김은 **실제로는 거의 작동 안 함** (초안 설명 정정)
- UI 는 실제로 🔴 tint + ⛓ 라벨 표시됨. 다만 "재실행" 표현이 실행 전이라 어색 (추후 data-mode 분기로 라벨 문구 개선 여지)

#### 기대 응답

- `hitl_ack` 1회 수신 per 편집 액션
- 서버 로그: `todo deleted via HITL ... invalidated=[...] issues=0`
- 브라우저에서 편집 반영

---

## 7. Plan review — 승인 / 거부

### 7.1 L1

사용자가 [✅ 승인] 또는 [❌ 거부] 클릭 → `wsHitl.send({type:"hitl_response", data:{action, turn_id}})` → 서버가 `signal_resume` → **approve 시 편집된 plan 이 있으면 modify+value 로 변환** → Graph 가 `Command(resume=...)` 로 재개 → planning_stage 의 modify 분기 → execution 진입.

### 7.2 L2

[`dashboard/index.html::hitlRespond`](../../dashboard/index.html) (L1140) 가 호출됨:
```javascript
wsHitl.send(JSON.stringify({
  type: "hitl_response",
  data: { request_id, action, turn_id: currentTurnId }
}));
```

서버 `_handle_hitl_response` ([ws_hitl.py:162](../../backend/api_v2/ws_hitl.py)):

```python
success = hitl.submit_response(request_id, action, value, comment)  # legacy dict 갱신
if turn_id:
    # Phase 5 — approve + progress 존재 시 modify 로 변환
    resume_payload = {"action": action, "value": value}
    if action == "approve":
        progress = hitl.get_progress(turn_id)
        if progress is not None:
            hitl.request_resume(turn_id)   # status="running" 복귀
            resume_payload = {"action": "modify", "value": progress.plan}
    hitl.signal_resume(turn_id, resume_payload)
```

`signal_resume` 는 `_resume_queues[turn_id].put_nowait(...)` → `wait_for_resume` 가 즉시 깨어남 → Command(resume=...) 로 Graph 재개.

[`planning_stage.py:88-92`](../../backend/app/dream_agent/planning/planning_stage.py) 의 modify 분기:
```python
if action == "modify" and isinstance(user_decision, dict):
    modified_plan = user_decision.get("value")
    if modified_plan:
        plan_dict = modified_plan    # edited plan 으로 교체
```

→ `Command(update={"plan": plan_dict}, goto="execution")` → execution_stage 진입.

### 7.3 L3 상세

#### 시스템 측 — 3 경로 분기

| action | 서버 내부 변환 | planning_stage 반응 | 결과 |
|--------|---------------|---------------------|------|
| `approve` + progress 존재 (편집 가능 상태) | `{action:"modify", value:progress.plan}` | L88-92 modify 분기 → plan 교체 | execution 진입 (edited plan) |
| `approve` + progress 없음 (legacy `_run_agent` 경로) | `{action:"approve", value:None}` 그대로 | L79 "approve" 기본 경로 | execution 진입 (원본 plan) |
| `reject` | `{action:"reject", value:None}` 그대로 | L81-86 reject 분기 → END | `complete(rejected)` |
| `modify` (클라가 직접 modify 전송, 이 흐름에선 미사용) | 그대로 | modify 분기 | execution 진입 |

#### 시스템 측 — `request_resume` 호출 이유

Phase 5 에서 approve + progress 존재 시 `hitl.request_resume(turn_id)` 를 호출:
```python
def request_resume(session_id):
    self._paused.discard(session_id)
    p = self._progress.get(session_id)
    if p:
        p.status = "running"       # "paused" → "running"
        p.paused_at_phase = None
```

이유: 임시 progress 의 status 를 "paused" 로 만들어뒀는데, execution_stage 가 이 progress 재사용할 때 `status` 가 아직 "paused" 면 `should_continue` 가 "pause" 반환하며 바로 execution_pause 로 들어가버림. `request_resume` 으로 running 으로 복귀시켜야 정상 execution 진행.

#### 시스템 측 — reject 경로

```python
# ws_agent _graph_runner_with_resume (ws_agent.py:448~)
if user_action == "reject":
    async for _ in agent.astream(LGCommand(resume=action), config=config):
        pass    # silent drain — planning_stage 가 END 로 보내는 동안 noop
    await _emit_complete("rejected")
    return
```

→ `planning_stage` 의 reject 분기는 `Command(update={"response":{"text":"실행 계획이 거부되었습니다."}}, goto=END)` 로 graph 종료.

#### 시스템 측 — 메모리 변화

| 시점 | _progress | _paused | _active_turns |
|------|-----------|---------|---------------|
| approve 직전 | `{turn_abc: ...status="paused"}` | `{}` | `{turn_abc}` |
| approve 직후 | `{turn_abc: ...status="running"}` | `{}` | `{turn_abc}` |
| execution 진입 | 동일 (execution_stage 가 재사용) | `{}` | `{turn_abc}` |

#### 시스템 측 — 분기

| 조건 | 결과 |
|------|------|
| progress 존재 + approve | modify 변환 → edited plan 으로 실행 |
| progress 없음 + approve | 원본 approve — execution 에서 state.plan 사용 |
| reject (progress 유무 무관) | silent drain → complete(rejected) |
| modify 클라 직접 전송 (legacy) | 변환 없이 modify 전달 |

#### 사용자 측

- [✅ 승인] 클릭: 모달 자동 close + idle 전환 UI 잠시 → `resumed(modify)` 이벤트 수신 → `node_event(execution)` 부터 재개
- [❌ 거부] 클릭: 모달 close + `complete(rejected)` 수신 + UI 에 "실행 계획이 거부되었습니다" 메시지
- F12 Network `/ws/hitl` 송신:
  ```json
  {"type":"hitl_response","data":{"request_id":"req_...","action":"approve","turn_id":"turn_..."}}
  ```
- `/ws/hitl` 수신:
  ```json
  {"type":"hitl_ack","data":{"action":"approve","request_id":"req_...","accepted":true/false}}
  ```
  (accepted 는 submit_response 반환값. Sprint 13 query 경로는 false 지만 flow 는 signal_resume 로 계속 됨)

#### 왜 approve→modify 변환인가

- 편집이 progress.plan 에 이미 저장돼있으나, planning_stage 가 state.plan (초기) 을 그대로 사용하면 **편집 내용 유실**
- Solution A: state 를 직접 업데이트 → LangGraph 와 싸워야 함
- Solution B (채택): Command(resume=...) 에 value 로 edited plan 실어보내고, planning_stage 가 modify 분기로 받아 처리
- 기존 `modify` 분기가 이미 구현돼있었으므로 최소 변경 (Phase 5 에서 3줄 추가)

#### 기대 응답

- `hitl_ack` 수신 + 모달 close
- 서버 로그: `planning modified by user` (approve 시) 또는 `planning rejected by user`
- execution 진행 또는 complete(rejected)

---

## 8. Execution + Pause interrupt

### 8.1 L1

approve 후 execution_stage 진입 → Phase 루프에서 each Todo 실행 → 사용자가 ⏸ 클릭 시 다음 Phase 경계에서 `execution_pause` interrupt → Pause 모달 자동 팝업.

### 8.2 L2

[`execution/execution_stage.py::execution_stage`](../../backend/app/dream_agent/execution/execution_stage.py):

```python
# 1. progress 재사용 or 신규 (Phase 5 덕에 plan_review 임시 progress 재사용됨)
if not hitl.get_progress(session_id):
    hitl.create_progress(session_id, plan_dict)
progress = hitl.get_progress(session_id)

# 2. Phase 루프
while True:
    remaining_phases = hitl.get_remaining_phases(session_id)
    if not remaining_phases: break
    for phase_idx, phase in enumerate(remaining_phases, start=1):
        decision = hitl.should_continue(session_id)
        if decision["action"] == "pause":
            user_decision = interrupt({
                "type": "execution_pause",
                "progress": hitl.get_progress_snapshot(session_id),
            })
            # resume 후 여기로 복귀
            ...
        # Phase 내 Todo 동시 실행 (executor.execute_phase)
        results = await executor.execute_phase(phase, ...)
        hitl.report_phase_complete(session_id, results)
```

사용자 ⏸ 클릭 → `_handle_pause` → `hitl.request_pause(session_id)` → `_paused.add(session_id)` + `progress.status = "paused"` + `progress.paused_at_phase = current_phase`.

다음 Phase 경계에서 `should_continue` 가 `{"action":"pause"}` 반환 → interrupt 발동 → ws_agent 가 `paused` 이벤트 broadcast → 모달 팝업.

### 8.3 L3 상세

#### 시스템 측 — `should_continue` 분기

[`hitl_manager/manager.py:344-357`](../../backend/app/dream_agent/workflow_managers/hitl_manager/manager.py):

```python
def should_continue(self, session_id) -> dict:
    p = self._progress.get(session_id)
    if p and p.status == "cancelled":
        return {"action": "cancel"}
    if session_id in self._paused:
        return {"action": "pause"}
    return {"action": "continue"}
```

우선순위: cancel > pause > continue.

#### 시스템 측 — executor 동작

`execute_phase(phase, ...)` 는 phase 내 Todo 를 `asyncio.gather` 로 **병렬 실행**. 각 Todo 마다:
1. `AgentPool.get_real_tool(tool_name)` — 첫 호출 시 lazy load
2. `executor.py::execute_todo` 가 tool 실행
3. 결과를 `TodoResult` 로 포장
4. `callback_manager.emit(session_id, {type:"todo_start", ...})` / `todo_complete` / `progress`

이벤트들은 `_callback_bridge` 통해 `conn_manager.broadcast_to_user` 로 fan-out.

#### 시스템 측 — `execution_pause` interrupt

[`execution_stage.py:194`](../../backend/app/dream_agent/execution/execution_stage.py):
```python
user_decision = interrupt({
    "type": "execution_pause",
    "progress": hitl.get_progress_snapshot(session_id),
})
```

`get_progress_snapshot` 은 `completed_todos` 의 keys + results + plan + status + current_phase 를 dict 로 반환. LangGraph 가 이를 Checkpoint 에 저장 → 서버 재시작 후에도 복원 가능.

#### 시스템 측 — ws_agent 의 execution_pause 분기

[`ws_agent.py:391-405`](../../backend/api_v2/ws_agent.py):
```python
elif intr_type == "execution_pause":
    progress_snap = intr_value.get("progress", {})
    if not hitl.get_progress(turn_id):
        hitl.restore_progress(turn_id, progress_snap)
    await conn_manager.broadcast_to_user(user_id, {
        "type": "paused",
        "conversation_id": conv_id, "turn_id": turn_id,
        "data": {**_build_paused_data(intr_value), "turn_id": turn_id, ...}
    })
```

`restore_progress` 는 **서버 재시작 후 resume_query 복원 시점에만 의미** 있음 (싱글톤 비어있으므로 Checkpoint 에서 복원). 일반 흐름에선 이미 `_progress` 에 있어 skip.

#### 시스템 측 — 메모리 변화

| 시점 | _progress[turn].status | _paused | current_phase |
|------|-----------------------|---------|---------------|
| approve 직후 | running | {} | 0 |
| Phase 0 실행 중 | running | {} | 0 |
| Phase 0 완료 → report_phase_complete | running | {} | 1 |
| 사용자 ⏸ | running | {turn} | 1 |
| Phase 1 경계 should_continue | paused (request_pause 가 즉시 갱신) | {turn} | 1 |
| interrupt 발동 | paused | {turn} | 1 (paused_at_phase=1) |
| 사용자 resume | running | {} | 1 |
| Phase 1 실행 | running | {} | 1 |

#### 시스템 측 — 분기

| 조건 | 결과 |
|------|------|
| ⏸ 클릭 (정상 Phase 중) | 다음 Phase 경계에서 pause |
| ⏸ 클릭 (마지막 Phase 후) | `remaining_phases` 비어서 루프 탈출 — pause 발동 안 함 (이미 종료) |
| cognitive/planning 중 ⏸ | `_paused.add` 됨 → plan_review interrupt 에서 `is_paused` 확인 → **auto-approve** 경로 → execution 진입 후 즉시 execution_pause |
| execution 중 ❌ (cancel) | `request_cancel` → `progress.status="cancelled"` → 다음 phase 경계에서 `should_continue` 가 cancel 반환 → interrupt 없이 바로 종료 |

#### 사용자 측

- ⏸ 버튼: [dashboard/index.html:L420](../../dashboard/index.html) `requestPause()`
- ⏸ 클릭 → `wsHitl.send({type:"pause", data:{turn_id}})`
- 즉시 UI 는 "⏸ 일시정지 요청..." 표시
- 다음 Phase 경계에서 `paused` 이벤트 수신 → `handlePaused` → `openHitlModal("pause", data)` 자동 팝업
- 모달 헤더: "⏸ 실행 일시정지됨 — Phase N 에서 정지"
- 본문: 남은 Todo 목록 + 완료 Todo 표시 + 편집 컨트롤 + [▶️ 재개] / [🛑 취소] 버튼
- F12 `/ws/hitl` 송신: `{"type":"pause","data":{"turn_id":"..."}}`
- F12 `/ws/agent` 수신: `{"type":"paused","data":{...progress snapshot...}}`

#### 사용자 측 — 가능 액션

- 편집 (§6 와 동일 경로) — pause 중이므로 progress 는 이미 paused
- [▶️ 재개] → §9 resume 경로
- [🛑 취소] → §9 cancel 경로
- 30분 무응답 → timeout → `complete(aborted, reason="hitl_timeout")`

#### 왜 Phase 경계에서만 pause 되는가 (NFR-5 제약)

- Phase 내부는 `asyncio.gather` 로 여러 Todo 동시 실행 중 — 중간에 멈추면 "일부 완료 / 일부 진행" 상태 모호
- Phase 경계 = 동시 실행 Todo 그룹이 모두 완료된 명확한 시점
- Sprint 14 A2 에서 "should_continue Todo 단위 세밀화" 검토 중 (out of scope 현재)

#### 기대 응답

- ⏸ 클릭 후 **실제 pause 까지** 최대 1~2초 지연 (진행 중 phase 완료 대기)
- 서버 로그: `pause requested session_id=...`, `executor phase complete results=...`, `interrupt execution_pause`
- 모달 자동 팝업

---

## 9. Resume / Cancel

### 9.1 L1

[▶️ 재개] → `{type:"resume", data:{turn_id}}` → `request_resume` + `signal_resume({action:"continue"})` → Graph 가 Command(resume=continue) 주입 → Phase 루프 재개.
[🛑 취소] → `{type:"cancel", data:{turn_id}}` → `request_cancel` + `signal_resume({action:"cancel"})` → should_continue 가 cancel 반환 → complete(cancelled).

### 9.2 L2

[`ws_hitl.py::_handle_resume`](../../backend/api_v2/ws_hitl.py) (L715):
```python
hitl.request_resume(session_id)    # _paused.discard + status="running"
hitl.signal_resume(turn_id, {"action": "continue"})
```

`_handle_cancel` (L750):
```python
hitl.request_cancel(session_id)    # status="cancelled"
hitl.signal_resume(turn_id, {"action": "cancel"})
```

서버의 wait_for_resume 가 깨어나 `Command(resume=action)` 주입. execution_stage 의 `interrupt()` 반환값이 이 action 이 되어 그 다음 라인부터 실행:

```python
user_decision = interrupt({...})
action = user_decision.get("action", "resume")
if action == "cancel":
    return Command(update={"execution_result":...}, goto=END)
# resume/continue 시 계속 while True 루프
```

### 9.3 L3 상세

#### 시스템 측 — resume 경로

```
ws_hitl._handle_resume
  ↓
hitl.request_resume(session_id)
  → _paused.discard(session_id)
  → progress.status = "running"
  → progress.paused_at_phase = None
  ↓
hitl.signal_resume(turn_id, {"action":"continue"})
  → _resume_queues[turn_id].put_nowait(...)
  ↓
ws_agent._graph_runner_with_resume 의 wait_for_resume 깨어남
  ↓
Command(resume={"action":"continue"}) 주입
  ↓
execution_stage interrupt() 반환값 = {"action":"continue"}
  ↓
while True 루프 다음 iteration
  ↓
should_continue → {"action":"continue"} (paused 해제됐으므로)
  ↓
execute_phase 다음 phase 실행
```

#### 시스템 측 — cancel 경로

```
ws_hitl._handle_cancel
  ↓
hitl.request_cancel(session_id)
  → _paused.discard (cancel 우선)
  → progress.status = "cancelled"
  ↓
hitl.signal_resume(turn_id, {"action":"cancel"})
  ↓
ws_agent wait_for_resume 깨어남 → {"action":"cancel"}
  ↓
user_action == "cancel" 분기 (ws_agent.py:442)
  ↓
silent drain (agent.astream(Command(resume=cancel))) — execution_stage 가 END 로 보냄
  ↓
_emit_complete("cancelled")
  ↓
run_turn 종료 → finally → cleanup_turn
```

#### 시스템 측 — 분기

| 조건 | 결과 |
|------|------|
| resume 클릭 | execution 재개 |
| resume 클릭 but 이미 cancelled | `_paused.discard` 해도 status=cancelled 는 유지 → 다음 Phase 에서 should_continue가 cancel 반환 → 무의미 |
| cancel 클릭 (pause 중) | 정상 cancel 경로 |
| cancel 클릭 (plan_review 중) | `_handle_hitl_response` 의 reject 와 다르지만, plan_review 에선 cancel UI 없음 (거부만) |
| timeout (30분 무응답, pause 상태) | `wait_for_resume` timeout → `{"action":"timeout"}` → execution_pause 는 `timeout_action = "cancel"` → 자동 cancel |

#### 시스템 측 — 메모리 변화

resume:
```python
_paused.discard(turn)
progress.status: "paused" → "running"
progress.paused_at_phase: 1 → None
_resume_queues[turn] 에 {"action":"continue"} 넣었다가 wait_for_resume 이 get 해서 비어짐
```

cancel:
```python
_paused.discard(turn)
progress.status: "paused" → "cancelled"
_resume_queues[turn] 에 {"action":"cancel"} 넣었다가 get
```

#### 사용자 측

- [▶️ 재개] 클릭 → 모달 close + `resumed(continue)` 이벤트 수신 + `node_event` 재개
- [🛑 취소] 클릭 → 모달 close + `resumed(cancel)` + `complete(cancelled)` 수신 + UI 에 "실행 취소됨" 메시지
- F12 `/ws/hitl` 송신: `{"type":"resume"/"cancel", "data":{"turn_id":"..."}}`
- F12 `/ws/agent` 수신 순차:
  ```json
  {"type":"resumed","data":{"action":"continue"/"cancel"}}
  // resume 시: node_event(execution) 계속
  // cancel 시: complete(cancelled)
  ```

#### 왜 pause/resume 을 Manager state 와 Queue 이중으로 관리하나

- **Manager state** (`_paused`, `progress.status`): Graph 의 `should_continue` 가 polling
- **Queue** (`_resume_queues`): interrupt 된 task 가 사용자 응답을 기다리는 수단
- Manager state 만 있으면 Graph 가 polling 루프 돌아야 함 (비효율)
- Queue 만 있으면 execution_stage 의 Phase 루프가 매 Phase 마다 Queue 체크해야 함 (복잡)
- 이중으로 사용: Graph 는 Manager state 로 빠른 체크, interrupt 후엔 Queue 로 대기

#### 기대 응답

- resume: `resumed(continue)` + Phase 계속 실행
- cancel: `resumed(cancel)` + `complete(cancelled)`
- 서버 로그: `resume requested`, `cancel requested`

---

## 10. Turn 종료

### 10.1 L1

그래프가 `__end__` 도달 → `_emit_complete("success")` (또는 rejected/cancelled/aborted) → `run_turn` finally → `concurrency.release` + `hitl.cleanup_turn` + `cb_manager.unregister` → 메모리 클린.

### 10.2 L2

`_graph_runner_with_resume` 의 while 루프 탈출 시 `_emit_complete("success", ...)` 호출. response_payload + execution_result + structured_query + plan 등 포함해 `complete` 이벤트 송신.

`run_turn` 의 finally 블록에서:
```python
concurrency.release(user_id, turn_id)            # _slots[user_id].discard(turn_id)
get_hitl_manager().cleanup_turn(turn_id)          # 5가지 자원 모두 해제
get_callback_manager().unregister(turn_id)        # listener 제거
```

클라 측 `handleEvent` 가 `complete` 수신 → UI idle 복귀 + 결과 블록 표시 + `localStorage.remove("octormate.last_turn_id")`.

### 10.3 L3 상세

#### 시스템 측 — complete 이벤트 구조

4가지 status:

| status | 언제 | data 필드 |
|--------|------|----------|
| `success` | 정상 종료 | response, execution_result, structured_query, plan, guard_warnings |
| `rejected` | 사용자 plan_review reject | message, guard_warnings |
| `cancelled` | 사용자 pause 후 cancel | guard_warnings |
| `aborted` | layer_guard fatal 또는 hitl_timeout | reason, guard_warnings |

#### 시스템 측 — `cleanup_turn` 상세

[`manager.py:594-611`](../../backend/app/dream_agent/workflow_managers/hitl_manager/manager.py):
```python
def cleanup_turn(self, turn_id):
    self._resume_queues.pop(turn_id, None)
    self._active_turns.discard(turn_id)
    self._paused.discard(turn_id)
    self._session_locks.pop(turn_id, None)
    self._progress.pop(turn_id, None)   # Phase 5 신규
```

Phase 5 이전엔 `_progress.pop` 없어서 leak 가능성 있었음. 임시 progress 도입하며 반드시 정리 필요.

#### 시스템 측 — 분기

| 종료 경로 | `_graph_runner_with_resume` 탈출 지점 | complete 이벤트 |
|-----------|--------------------------------------|----------------|
| Graph 자연 종료 | while 루프 `_has_pending_interrupts` False | `success` |
| Plan review reject | `if user_action == "reject":` 분기 | `rejected` |
| Pause 중 cancel | `if user_action == "cancel":` 분기 | `cancelled` |
| Layer guard fatal | `abort_reason` 설정 후 `_emit_complete("aborted", reason=...)` | `aborted` (reason=<code>) |
| HITL timeout | `if user_action == "timeout":` 분기 | `aborted` (reason="hitl_timeout") |
| run_turn 예외 | `except Exception` 분기 — `EXECUTION_ERROR` error 이벤트 | error (complete 안 보냄) |

#### 시스템 측 — 메모리 변화 (정리 후)

```python
conn_manager._connections   = {"demo": [<ws_agent>, <ws_hitl>]}  # 유지
concurrency._slots          = {"demo": set()}                    # 비움
hitl._active_turns          = set()                               # 비움
hitl._progress              = {}                                  # 비움 (Phase 5)
hitl._paused                = set()                               # 비움
hitl._resume_queues         = {}                                  # 비움
hitl._session_locks         = {}                                  # 비움
callback_manager._listeners = {}                                  # turn 해당 키 제거
```

즉 다음 쿼리가 "깨끗한 상태" 에서 시작 가능.

#### 시스템 측 — idempotent 보장

`cleanup_turn`, `disconnect`, `unregister` 모두 idempotent (key 없으면 no-op). run_turn 예외 발생 시 finally 가 항상 호출되도록 try/except/finally 구조.

#### 사용자 측

- 모달 close (success/rejected/cancelled)
- 결과 블록 렌더 (성공 시 마크다운 응답 + 실행 결과)
- UI: 상단 상태 "🟢 연결됨 — idle"
- 전송 버튼 복원: "전송", `onclick = sendMessage`
- `agentRunning = false`
- `localStorage.remove("octormate.last_turn_id")`
- F12 `/ws/agent` 수신:
  ```json
  {"type":"complete","data":{"status":"success","response":{...},"execution_result":{...},...}}
  ```

#### 사용자 측 — 분기

| complete.status | UI 반응 |
|----------------|---------|
| success | 결과 마크다운 블록 표시 |
| rejected | "실행 계획이 거부되었습니다" 메시지 |
| cancelled | "실행 취소됨" 메시지 |
| aborted (hitl_timeout) | 토스트 "⏱ 자동 종료됨" + idle |
| aborted (layer_guard fatal) | 토스트 reason 코드 표시 + idle |

#### 왜 finally 에서 반드시 cleanup 하는가

- 예외로 종료됐을 때도 자원이 남으면 leak → 장기 운영 시 메모리 누적 / concurrency slot 소진
- `try/except/finally` 패턴으로 보장: 예외도 다시 raise 하되 자원 정리는 반드시
- 싱글톤 상태를 깔끔히 유지해 다음 turn 에 영향 안 주기

#### 기대 응답

- UI idle + 결과 표시
- 서버 로그: `run_turn finished status=success`, `cleanup_turn turn=...`
- 다음 쿼리 입력 가능

---

## 11. 에러 / 엣지 경로

사용자 의도 대조 시 놓치기 쉬운 경로들.

### 11.1 Concurrent Limit Exceeded

| 조건 | 4번째 동시 쿼리 (같은 user) |
|------|---------------------------|
| 코드 | `concurrency.try_acquire` 반환 False |
| 응답 | `error` fan-out `CONCURRENT_LIMIT_EXCEEDED` |
| UI | 4번째 쿼리 탭에 에러 토스트, 앞 3 쿼리는 영향 없음 |
| 왜 | 사용자당 3 동시 실행 제한 (NFR-1, `MAX_CONCURRENT_TURNS_PER_USER`) |

### 11.2 Invalid Message

| 조건 | `type:"query"` payload 에서 conv_id/turn_id/user_input 누락 |
|------|-------------------------------------------------------------|
| 응답 | `error` **direct-WS** `INVALID_MESSAGE` (이 WS 만) |
| 왜 direct | 다른 탭엔 무관한 에러 — 보낸 WS 만 보면 됨 |

### 11.3 Auto-Approve (plan_review 자동 승인)

| 조건 | 사용자가 cognitive/planning 중에 pause 클릭 |
|------|-------------------------------------------|
| 동작 | planning 끝에 plan_review interrupt 발동 → `is_paused(turn_id) == True` → **자동 approve 주입** → 모달 안 뜸 → execution 진입 → 즉시 execution_pause |
| 왜 | 사용자 의도 ("잠깐 멈춰") 를 planning 내부에서 끊는 건 복잡 → pause 가 의미 있는 건 execution 경계이므로 plan_review 를 스킵 |
| 코드 | [`ws_agent.py:368-376`](../../backend/api_v2/ws_agent.py) `if intr_type == "plan_review" and hitl.is_paused(turn_id)` 분기 |

### 11.4 HITL Timeout

| 조건 | interrupt 후 `HITL_RESUME_TIMEOUT_SEC` (기본 1800s) 동안 사용자 무응답 |
|------|-----------------------------------------------------------------------|
| 동작 | `wait_for_resume(timeout=...)` 반환 `{"action":"timeout"}` → intr_type 별 처리 |
| plan_review timeout | `timeout_action = "reject"` → Command(resume=reject) → `_emit_complete("aborted", reason="hitl_timeout")` |
| execution_pause timeout | `timeout_action = "cancel"` → Command(resume=cancel) → `_emit_complete("aborted", reason="hitl_timeout")` |
| 후속 | 동일 turn_id 로 뒤늦은 hitl 요청 → `_check_turn_active` 에서 `turn_not_active` 거부 |

### 11.5 Resume Query (서버 재시작 복원, R-9)

| 조건 | 서버 재시작 후 브라우저 자동 재연결 시 `localStorage.last_turn_id` 존재 |
|------|-----------------------------------------------------------------------|
| 동작 | 브라우저가 `{"type":"resume_query", "conversation_id":..., "turn_id":...}` 송신 → 서버가 `run_turn(resume_only=True)` spawn → `_graph_runner_with_resume` 가 초기 astream skip, 바로 resume 루프 → Checkpoint 에서 state 복원 → pending interrupt 있으면 hitl_request/paused 재emit |
| 실패 케이스 | thread_id 에 pending interrupt 없음 → `INVALID_MESSAGE` 에러 |
| 복원되는 것 | `_progress` (restore_progress 호출), `_paused`, pending interrupt. `_resume_queues` 는 재생성 |

### 11.6 NL 편집 실패 UX

R-18 과 동일. `plan_editor` 의 여러 실패 경로:

| 실패 | 반환 |
|------|------|
| LLM API 연결 실패 | `hitl_ack accepted:false, reason:"자연어 처리 중 오류: ..."` (free-form) |
| instruction 500자 초과 | `action:"unknown", reason:"명령 길이 초과"` → `NL_INTENT_UNCLEAR` |
| 의도 불명확 | `action:"unknown"` → `NL_INTENT_UNCLEAR` |
| DAG 순환 | `validate_edit` False → `INVALID_DAG` |
| reorder new_position 오류 | `apply_edit` 예외 → free-form reason |

---

## 12. 검증 로그 (4-Pass Review)

이 walkthrough 를 쓰며 **실제 코드와 대조** 한 결과. 이 문서의 신뢰성 확보 + 발견된 drift 기록.

### Pass 1 — Self-consistency (내부 논리)

전체 훑으며 단계 간 연결 확인:

| 단계 간 연결 | 상태 | 비고 |
|-------------|------|------|
| §1 서버 기동 → §2 클라 접속 | ✅ | `app.state.graph` 생성 후 endpoint accept |
| §3 쿼리 입력 → §4 graph 실행 | ✅ | `asyncio.create_task(run_turn)` 으로 비동기 |
| §4 planning → §5 plan_review | ✅ | interrupt 감지 후 임시 progress 생성 |
| §5 → §6 편집 | ✅ | progress.status="paused" 덕분에 pause 분기 진입 |
| §7 approve → §8 execution | ✅ | modify 변환 → planning_stage L88-92 → execution_stage 가 기존 progress 재사용 (status 는 running 복귀됨) |
| §8 pause → §9 resume/cancel | ✅ | Queue + Manager state 이중 관리 |
| §10 종료 → 다음 쿼리 | ✅ | cleanup_turn 이 5가지 자원 모두 정리 |

**결과: 통과**

### Pass 2 — Code Cross-check (실제 코드 대조)

| 주장 | 검증 방법 | 결과 |
|------|----------|------|
| lifespan 에서 Checkpointer + Graph init | `main.py:26-57` Read | ✅ 확인 |
| **AgentPool eager init** (memory 주장) | `agent_pool.py:54-95` Read | ❌ **Drift 발견** — lazy with catalog-preload |
| `_handle_todo_modify/delete` plan_review 분기 제거 | `ws_hitl.py` Read | ✅ Phase 5 반영 |
| `_handle_hitl_response` approve → modify 변환 | `ws_hitl.py:210` Read | ✅ |
| `cleanup_turn._progress.pop` | `manager.py:610` Read | ✅ |
| planning_stage modify 분기 | `planning_stage.py:88-92` Read | ✅ 이미 존재 |
| `calculate_cascade` invalidated 에 downstream 포함 | TE-H02 결과 + todo_manager 동작 | ✅ (initial draft 의 "invalidated=[]" 은 잘못 — 정정됨) |
| 대시보드 `handleEvent/handlePaused/handleHitlRequest` 위치 | `dashboard/index.html` Grep | ✅ L448/919/904 |

**발견한 drift 2건**:
1. **memory `project_eager_agent_init.md`** — "서버 부팅 시 AgentPool 에 미리 생성" → 실제는 첫 `get_agent_pool()` 호출 시 lazy load. 개선 필요.
2. **`sprint14_a3_missed_points.md §B` 초안** — "Plan review 에선 `invalidated=[]`" → 실제는 downstream 포함. 이미 v1.1 에서 정정.

**결과: 대체로 통과. memory 1건 업데이트 필요**

### Pass 3 — R-5~R-18 Coverage

플레이북의 각 시나리오가 walkthrough 의 어느 단계에 매핑되는지:

| 시나리오 | Walkthrough 섹션 | 커버 여부 |
|---------|-----------------|----------|
| R-5 Plan review 편집 | §5 + §6 + §7 | ✅ 상세 |
| R-6 Cascade 3+ downstream | §6 (calculate_cascade 설명) | ✅ |
| R-7 Todo 추가 | §6 (구조화 경로) | ✅ |
| R-8 Diamond DAG | §6 (calculate_cascade BFS) | ✅ |
| R-16 NL 삭제 | §6 (자연어 경로) | ✅ |
| R-17 NL 순서 변경 | §6 (자연어 경로) | ✅ (reorder 는 apply_edit 내부) |
| R-18 NL 파싱 실패 | §6 (NL 분기 표) + §11.6 | ✅ |
| (추가) 서버 재시작 | §11.5 | ✅ |
| (추가) Timeout | §11.4 | ✅ |
| (추가) Concurrent limit | §11.1 | ✅ |
| (추가) Auto-approve | §11.3 | ✅ |

**결과: 모든 플레이북 시나리오가 walkthrough 로 설명됨**

### Pass 4 — 사용자 5항 의도 정렬

사용자 5항목 요구사항이 각 섹션에서 어떻게 반영되는지:

| 사용자 요구 | Walkthrough 반영 위치 | 일치도 |
|------------|---------------------|-------|
| §1 "ws_agent/ws_hitl 2통로, pause=hitl=interrupt 같은 선상" | §2 (채널 분리 이유), §5/§8 (둘 다 interrupt 로 통일) | ✅ |
| §2 "hitl_manager 가 hitl/pause 관리" | §5 (임시 progress 생성), §8 (request_pause), §9 (request_resume) 모두 hitl_manager 에서 | ✅ |
| §3 "todo_manager 가 todo 관리, hitl/pause 상태 관리 명확" | §6 (calculate_cascade, _build_phases_from_plan 모두 todo_manager) | ✅ |
| §4 "hitl/pause 는 같은 개념, 승인/수정/재개 로직, NL 가능, 단순 작업 간단, UI 완벽" | §5-§9 의 통합 경로 전체. §6 구조화/NL 분기 | ✅ **핵심** |
| §5 "gap 작음, 타이밍·구조·연결만 맞추면 됨" | §5 임시 progress (타이밍), §6 분기 통합 (구조), §7 approve→modify (연결) | ✅ |

**결과: 5항목 모두 walkthrough 에 반영됨**

---

## 13. 의도 ↔ 구현 매트릭스 (요약)

사용자가 설계 시 의도한 것과 실제 구현이 일치하는지 한눈에 확인:

| 의도 | 구현 위치 | 일치 |
|------|----------|------|
| 2 채널 WebSocket | `ws_agent.py` + `ws_hitl.py` | ✅ |
| pause = hitl = interrupt | 모두 `interrupt()` primitive + `signal_resume` Queue 사용 | ✅ |
| hitl_manager 가 모든 pause/hitl 관리 | `HITLManager` 싱글톤 + 5가지 자원 | ✅ |
| todo_manager 가 DAG·cascade | `TodoManager.calculate_cascade` + `_build_phases_from_plan` | ✅ |
| 사용자 개입 = 승인/수정/재개 | `_handle_hitl_response` + `_handle_resume/cancel` + `_handle_todo_*` | ✅ |
| 자연어 편집 가능 | `plan_editor` + `_handle_todo_edit_nl` | ✅ (1차 범위) |
| 단순 작업 간단 | 구조화 핸들러 = 서버 왕복 1회 | ✅ |
| UI 변경 없음 | Phase 5 에서 UI 수정 0 | ✅ |
| gap 은 타이밍·구조·연결만 | 변경 4건, +50/-40 줄 | ✅ |

---

## 14. 이 walkthrough 로 할 수 있는 후속 작업

- **의도 대조 리뷰**: 본 문서 전체를 읽으며 "이건 내 의도와 다르다" 지점 찾기 → Claude 에게 수정 지시
- **분기 테스트 보강**: §11 에러 경로들에 unit test 있는지 확인 → 부족하면 추가
- **ADR 도출**: §5~§9 의 "왜" 섹션들을 모아 `adr/ADR-001_pause_hitl_unification.md` 형식으로 정식 문서화
- **onboarding**: 신규 협업자에게 이 문서 먼저 → 15~20분 읽으면 A3 범위 이해
- **memory 업데이트**: Pass 2 발견한 `project_eager_agent_init.md` drift 수정

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-24 | 초안 — §1~§11 서버 기동부터 에러 경로까지 10+1 단계. L1/L2/L3 3단계 깊이. 시스템 측 + 사용자 측 관점 분리. §12 4-Pass 검증 로그 (drift 2건 발견). §13 의도 ↔ 구현 매트릭스. §14 후속 작업 가이드. Sprint 14 A3 Phase 5 commit `75aa753` 기준 |
