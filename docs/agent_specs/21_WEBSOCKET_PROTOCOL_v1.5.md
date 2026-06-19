# WebSocket Protocol Specification (Sprint 13+)

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 개발 - API 계약 |
| 진행상태 | **Active** (ws_contract 브랜치 Stage 4 정식) |
| 버전 | **v1.5** |
| 최종 수정일 | 2026-05-16 |
| 이전 버전 | v1.4 (2026-04-24), v1.3 (2026-04-23), v1.2 (2026-04-22), v1.1 (2026-04-10) |
| 관련 명세 | `20_INTERFACE_CONTRACT_v1.1.md`, `22_error_codes_v1.1.md`, `24_sequence_diagrams_v1.3.md`, `30_DATA_MODELS_v1.1.md`, `10_system_architecture_v1.9.md`, `12_manager_layer_v1.4.md` |

**v1.5 (2026-05-15) 변경점** — ADR-011 ConnectionManager 채널 분리:

- §1.2 `ConnectionManager` 의 fan-out 키가 `user_id` → **`(user_id, channel)`** 로 변경. 한 사용자의 *같은 채널에 연결된 여러 WS* 에만 broadcast. multi-tab 동기화 의도 보존, **다른 채널로의 leak 제거**.
- §1.3 `MAX_WS_CONNECTIONS_PER_USER = 5` 가 **`(user_id, channel)` 별 5** 로 의미 변경. 한 사용자가 탭 5개 열면 agent 5 + hitl 5 = 총 10 WS 가능.
- §3.2 `/ws/hitl` Server→Client 카탈로그 (`connected` / `pong` / `error` / `hitl_ack`) **엄격 적용** — agent 채널 이벤트가 hitl 소켓에 leak 되던 v1.4 이전 버그 해소 (ADR-011).
- **클라이언트 영향 없음** — 프론트 코드 변경 0. agent 채널 broadcast 가 더 이상 hitl 소켓에 leak 안 되므로 메시지 자연 dedup.

**v1.4 (2026-04-24) 변경점** — Sprint 14 A3 Phase 5 (편집 경로 통합):

- `hitl_response {action:"approve"}` 의 **서버 내부 변환** 명시 — plan_review 편집이 있던 경우 서버가 `{action:"modify", value:progress.plan}` 로 변환해 planning_stage 에 전달. **클라이언트 측 계약 변경 없음** (클라는 여전히 `approve` 전송).
- `hitl_request` (plan_review) 수신 후 서버는 **임시 `_progress` 생성** 하므로, 편집 요청 (`todo_modify/delete/add/edit_nl`) 이 `progress.status=="paused"` 가드를 통과함 — §3.1 편집 메시지 가드 조건 단일화.
- plan_review 중 cascade 동작: `calculate_cascade` 가 `completed_todos` 와 무관하게 downstream todo_id 를 `invalidated` 에 포함 → UI 가 🔴 tint + ⛓ 라벨 표시 (동작 자체는 execution_pause 와 동일, 단 `preserved_results` 는 빈 dict).

**v1.3 (2026-04-23) 변경점** — Sprint 14 A3 Phase 6:

- 신규 수신 메시지 타입 `todo_edit_nl` (Y-a 자연어 편집):
  ```json
  {"type": "todo_edit_nl", "data": {"session_id": "...", "turn_id": "...", "instruction": "4번 삭제"}}
  ```
- `hitl_ack` action 카탈로그 확장 (총 5종): `hitl_response` / `todo_modify` / `todo_delete` / `todo_add` / `todo_edit_nl`
- `hitl_ack` 응답 공통 필드:
  - `accepted: bool` — 성공/거부
  - `reason?: str` — 거부 시 free-form 설명
  - `code?: str` — 거부 시 ErrorCodes enum 코드 (`TODO_EDIT_NOT_PAUSED` / `INVALID_DAG` / `NL_INTENT_UNCLEAR` — D7=A-)
  - `plan?: dict` — 편집 후 전체 Plan
  - `invalidated?: list[str]` — cascade 결과
  - `restart_from?: str` — UX 라벨
  - `preserved?: list[str]` — 유지 todo_id
  - `issues?: list[str]` — validate 결과
  - `nl_action?: str` — todo_edit_nl 성공 시 parsed action (`add|remove|modify|reorder`)
- 기존 수신 메시지 `todo_modify/delete/add` payload 에 `turn_id` 권장 (`is_turn_active` 가드 — FR-13c 8종 핸들러 완성)

---

## 0. 개요

DreamAgent V2는 **WebSocket 이중 채널**로 클라이언트와 통신한다.

| 채널 | 경로 | 방향 | 용도 |
|------|------|------|------|
| Agent | `/ws/agent` | Server → Client (주) | 노드 이벤트, interrupt 알림, 최종 결과, 에러 |
| HITL | `/ws/hitl` | 양방향 | 사용자 명령 (승인/거부/pause/resume/todo 조작) + ack |

**왜 이중 채널?** — 이벤트 스트림과 사용자 명령의 backpressure/생명주기 분리. Pause 중에도 명령은 계속 받기 위함.

---

## 1. 연결 관리

### 1.1 URL 형식

```
ws://<host>/ws/agent?user_id=<user_id>
ws://<host>/ws/hitl?user_id=<user_id>
```

`user_id` query parameter는 **필수**. 현재 POC에서는 `"demo"` 고정 (Sprint 16+ 로그인 시 변경).

### 1.2 ConnectionManager (v1.5 — 채널 분리)

서버는 **`(user_id, channel)` 쌍** 기준으로 WebSocket 을 관리. `channel` ∈ `{"agent", "hitl"}`.

- **MAX_WS_CONNECTIONS_PER_USER = 5** — **`(user_id, channel)` 별** 5 (한 사용자가 탭 5개 열면 agent 5 + hitl 5 = 총 10 ws 가능). 초과 시 close(1008) `connection_limit_exceeded`.
- **broadcast fan-out**: 한 `(user_id, channel)` 의 모든 연결에만 이벤트 동일 전송. **다른 채널로 leak 없음**.
- **dead WS 자동 정리**: 송신 실패 시 해당 (user, channel) 의 list 에서 제거.

자료구조 (참고):
```python
# ConnectionManager._connections
dict[str, dict[Channel, list[WebSocket]]]
# 예: {"demo": {"agent": [ws1, ws2], "hitl": [ws3]}}
```

API:
```python
async def connect(user_id: str, channel: Channel, ws) -> bool
async def disconnect(user_id: str, channel: Channel, ws) -> None
async def broadcast_to_user(user_id: str, channel: Channel, message: dict) -> None
```

상세: `10_system_architecture_v1.9.md` §4.2 (Connection Manager) / `12_manager_layer_v1.4.md` §3 (ConnectionManager).

**왜 채널 분리?** v1.4 이전: 한 `user_id` 의 모든 WS 에 broadcast → 같은 탭의 agent 채널 broadcast 가 hitl 소켓으로도 leak → 프론트 메시지 중복 처리 (특히 P1-6 자동 approve + complete). v1.5 = §3.2 카탈로그 계약 회복.

**Multi-tab 동기화 의도 보존**: 같은 `(user_id, channel)` 안의 여러 WS 에 대해 fan-out 유지. 한 사용자가 탭 2개 열어도 두 탭의 ws_agent 둘 다 같은 broadcast 받음.

### 1.3 재연결 정책

| 버전 | 정책 |
|------|------|
| Sprint 13 | **고정 3초 재연결** (close → 3s 대기 → 재시도 반복) |
| Sprint 17+ | exponential backoff 도입 예정 (1/2/4/8/16s) |

대시보드: `ws.onclose = () => setTimeout(connect, 3000)`

### 1.4 식별 체계

| 용어 | 생성 | 용도 |
|------|------|------|
| `user_id` | URL query | 사용자 식별. v1.5 부터 broadcast fan-out 키는 `(user_id, channel)` 쌍 (§1.2). |
| `conversation_id` | 클라이언트 (`crypto.randomUUID`) | 대화방 단위 |
| `turn_id` | 클라이언트 (매 쿼리) | 쿼리 단위, HITL signal 키 |
| `session_id` (deprecated) | — | Sprint 12 호환용 — `turn_id` alias, 외부 계약 사용 금지 |

---

## 2. `/ws/agent` 메시지

### 2.1 Client → Server

#### `type: "query"` (Sprint 13 신 경로)

```json
{
  "type": "query",
  "conversation_id": "conv_a1b2c3d4",
  "turn_id": "turn_e5f6g7h8",
  "user_input": "도메인 작업 요청",
  "client_id": "<client>",
  "language": "ko",
  "conversation_history": [],
  "history_limit": 3
}
```

**필수**: `conversation_id`, `turn_id`, `user_input`
**옵션**: `client_id` (ADR-022 helper-B agent path 활성화, 미명시 시 BaseTool.fetch fail-fast), `language` (기본 "ko"), `conversation_history`, `history_limit` (Settings fallback)

> **`client_id`** (작업 ⑪, 2026-05-31 도입) — 진입점이 ExecutionContext.client_id 채워 tool.helper-B 활성화. frontend `useCurrentClient()` (api/clients.ts:43) 가 자동 첫 client 반환, undefined 시 UI disabled 가드 (사용자 noise 0). default 강제 X — 사용자 원칙 [기본값은 있으면 안 되는거야].

검증 (`_parse_query_message`):
- `conversation_id` 누락/빈 문자열 → `INVALID_MESSAGE`
- `turn_id` 누락/빈 문자열 → `INVALID_MESSAGE`
- `user_input` 누락 → `INVALID_MESSAGE` (빈 문자열은 허용)

#### `type: "resume_query"` (Sprint 13 I11-c, 서버 재시작 복원)

```json
{
  "type": "resume_query",
  "conversation_id": "conv_a1b2c3d4",
  "turn_id": "turn_e5f6g7h8"
}
```

서버 재시작 후 브라우저가 재연결될 때, 진행 중이던 turn을 복원하기 위해 사용.

**필수**: `conversation_id`, `turn_id`  
**금지**: `user_input` (query 재실행이 아니라 **Checkpoint 복원**이므로 입력 없음)

**백엔드 동작**:
1. `run_turn(payload={"resume_only": True})` 재스폰
2. `_graph_runner_with_resume` 가 **초기 astream skip** → 바로 resume 루프 진입
3. `agent.aget_state(thread_id)` 로 Checkpoint에서 state 로드
4. pending interrupt 있으면 `hitl_request` 또는 `paused` 재emit
5. pending 없으면 `INVALID_MESSAGE` fatal emit + 조기 return

**검증**:
- `conversation_id` 누락 → `INVALID_MESSAGE` (direct-WS)
- `turn_id` 누락 → `INVALID_MESSAGE` (direct-WS)
- 해당 thread_id에 pending interrupt 없음 → `INVALID_MESSAGE` fatal (fan-out)

**대시보드 트리거**:
- 쿼리 전송 시 `localStorage.set("dreamagent.last_turn_id", turn_id)`
- `complete` 이벤트 수신 시 `localStorage.remove(...)`
- `ws.onopen` 에서 `last_turn_id` 존재 시 무조건 자동 전송 (agentRunning 조건 X — onclose 에서 이미 리셋됨)
- `ws.onclose` 에서 `agentRunning=false`, UI idle로 내림 (`last_turn_id`는 보존)

상세 시퀀스: `24_sequence_diagrams_v1.3.md §4`

#### `type: "start"` (Sprint 12 legacy, 유지)

```json
{"type": "start", "message": "도메인 작업 요청", "language": "ko"}
```

Sprint 14 regression 완료까지 유지. 신규 개발은 `"query"` 사용.

#### `type: "ping"`

```json
{"type": "ping"}
```

응답: `{"type": "pong", "timestamp": "..."}`

### 2.2 Server → Client

#### `connected` (연결 직후)

```json
{
  "type": "connected",
  "session_id": "sess_abc12345",
  "user_id": "demo",
  "timestamp": "2026-04-21T00:00:00Z"
}
```

`session_id` 필드는 Sprint 12 호환용 — 매 WS 연결마다 서버 생성된 의미 없는 라벨. 신 경로에서는 무시 OK.

#### `node_event` (각 노드 완료 시)

```json
{
  "type": "node_event",
  "node": "cognitive",
  "conversation_id": "conv_a1b2c3d4",
  "turn_id": "turn_e5f6g7h8",
  "data": {"structured_query": {...}}
}
```

`node` ∈ `{"cognitive", "planning", "execution", "response"}` (Sprint 12 `_stage` suffix 제거됨).

`data`는 해당 노드가 chunk로 emit한 State update dict. 예:
- cognitive → `{"structured_query": {...}}`
- planning → `{"plan": {...}}` (정상) 또는 `{"response": {...}}` (reject 경로)
- execution → `{"execution_result": {...}, "execution_progress": {...}}`
- response → `{"response": {...}}`

**내부 필터**: `__interrupt__` / `__end__` chunk는 클라이언트 송신 안 함.

#### `hitl_request` (plan_review interrupt 진입, Sprint 13 I11-a)

```json
{
  "type": "hitl_request",
  "conversation_id": "conv_xxx",
  "turn_id": "turn_yyy",
  "data": {
    "request_id": "req_<8자>",
    "plan": {
      "todos": [...],
      "dag": {...},
      ...
    },
    "options": ["approve", "reject", "modify"],
    "message": "N개 Todo 실행 계획...",
    "turn_id": "turn_yyy",
    "conversation_id": "conv_xxx"
  }
}
```

`request_id`는 server-side UUID 라벨 (Sprint 12 `hitl.create_request` 반환값과 다른 트랙).

**`data.turn_id` / `data.conversation_id`**: Sprint 14 A3 Phase 4 (2026-04-23) — 클라이언트가 fallback 없이 `data` 단일 경로로 읽을 수 있도록 envelope 의 `turn_id`/`conversation_id` 를 `data` 안에도 복제 포함. envelope 값과 항상 동일.

#### `paused` (execution_pause interrupt 진입)

```json
{
  "type": "paused",
  "conversation_id": "conv_xxx",
  "turn_id": "turn_yyy",
  "data": {
    "request_id": "req_<8자>",
    "completed": ["todo_001", "todo_002"],
    "total": 5,
    "current_phase": 2,
    "progress": {...},
    "turn_id": "turn_yyy",
    "conversation_id": "conv_xxx"
  }
}
```

`hitl_request` 와 동일하게 `data.turn_id` / `data.conversation_id` 가 envelope 값으로 복제 포함된다 (Sprint 14 A3 Phase 4).

#### `resumed` (wait_for_resume 반환 직후)

```json
{
  "type": "resumed",
  "conversation_id": "conv_xxx",
  "turn_id": "turn_yyy",
  "data": {"action": "approve"|"modify"|"reject"|"continue"|"cancel"}
}
```

`data.action` 은 `wait_for_resume` 가 반환한 `action` 값 그대로다.
**`modify` 주의**: Sprint 14 A3 Phase 5 편집 경로 통합으로, 클라이언트가 `hitl_response {action:"approve"}` 를 보내도 편집된 임시 progress 가 있으면 `ws_hitl` 이 서버 내부에서 `{action:"modify", value:progress.plan}` 으로 변환해 signal 한다 (§3.1 참조). 따라서 클라이언트가 `approve` 를 보냈어도 `resumed.data.action` 은 `modify` 로 올 수 있다. `timeout` 은 `resumed` 를 emit 하지 않고 `complete(aborted)` 로 직행한다 (C-7).

#### `complete` (그래프 종료 — turn 당 정확히 1회)

```json
// status: "success"
{
  "type": "complete",
  "conversation_id": "conv_xxx",
  "turn_id": "turn_yyy",
  "data": {
    "status": "success",
    "response": {"text": "...", "attachments": [...]},
    "execution_result": {...},
    "structured_query": {...},
    "plan": {...},
    "guard_warnings": [{"layer": "execution", "code": "EXECUTION_PARTIAL_FAILED"}]
  }
}

// status: "rejected" (사용자 reject)
{"type": "complete", ..., "data": {"status": "rejected", "message": "실행 계획이 거부되었습니다.", "guard_warnings": []}}

// status: "cancelled" (사용자 cancel)
{"type": "complete", ..., "data": {"status": "cancelled", "guard_warnings": []}}

// status: "aborted" (layer guard fatal)
{"type": "complete", ..., "data": {"status": "aborted", "reason": "COGNITIVE_EMPTY_QUERY", "guard_warnings": [...]}}

// status: "aborted" (Sprint 14 A1 — HITL 응답 타임아웃)
{"type": "complete", ..., "data": {"status": "aborted", "reason": "hitl_timeout", "guard_warnings": []}}
```

**`complete.data.reason` 필드 값 카탈로그** (status=="aborted" 일 때):
| 값 | 의미 | 출처 |
|----|------|------|
| `COGNITIVE_EMPTY_QUERY` / `PLANNING_EMPTY_PLAN` / `EXECUTION_ALL_FAILED` / `RESPONSE_EMPTY` | layer guard fatal | `22_error_codes_v1.1.md` |
| `hitl_timeout` | HITL 응답 타임아웃 — 사용자 무응답 상태에서 `HITL_RESUME_TIMEOUT_SEC` 초과 (Sprint 14 A1) | `_graph_runner_with_resume` timeout 분기 |

#### `error` (Error 이벤트 — §6 카탈로그 참조)

#### `layer_start` / `todo_start` / `todo_complete` / `progress` (callback_manager bridge 경유)

Execution 내부에서 `callback_manager.emit(session_id, ...)` 호출 → `run_turn` bridge가 `conn_manager.broadcast_to_user` 로 fan-out. I11-b2에서 bridge 활성화됨.

```json
// layer_start (execution 진입 직후)
{"type": "layer_start", "session_id": "turn_xxx", "timestamp": "...", "data": {"layer": "execution"}}

// todo_start (개별 Todo 실행 시작)
{"type": "todo_start", "session_id": "turn_xxx", "data": {"todo_id": "todo_001", "tool": "<tool>", ...}}

// todo_complete (개별 Todo 종료)
{"type": "todo_complete", "session_id": "turn_xxx", "data": {"todo_id": "todo_001", "status": "success", "duration_ms": 2341.5, "summary": "..."}}

// progress (Phase 진행률)
{"type": "progress", "session_id": "turn_xxx", "data": {"completed": 3, "total": 7}}
```

**주의**:
- `session_id` 필드는 Sprint 12 호환으로 포함 (= `turn_id` 값). 신 클라이언트는 `turn_id` 사용.
- bridge가 `conversation_id` / `turn_id` 필드를 자동 보강 (conv 필터 통과용).

---

## 3. `/ws/hitl` 메시지

### 3.1 Client → Server

#### `hitl_response` (plan_review 응답)

```json
{
  "type": "hitl_response",
  "data": {
    "request_id": "req_xxx",        // hitl_request의 request_id (추적용)
    "turn_id": "turn_yyy",          // 필수 (signal 키)
    "action": "approve"|"reject"|"modify",
    "value": {...}                  // modify 시 수정된 plan
  }
}
```

서버 동작: `hitl.signal_resume(turn_id, {"action": ..., "value": ...})` → `/ws/agent` 측 `wait_for_resume` 반환.

#### `pause` (Execution 일시중단 요청)

```json
{"type": "pause", "data": {"turn_id": "turn_yyy"}}
```

서버 동작: `hitl.request_pause(turn_id)` → 다음 Phase 직전 `execution_pause` interrupt 발동.

**payload 필드 호환**: `session_id` 와 `turn_id` 둘 다 지원 (`session_id = session_id or turn_id`). 현재 대시보드는 `turn_id` 만 전송.

#### `resume` (일시중단 해제)

```json
{"type": "resume", "data": {"turn_id": "turn_yyy"}}
```

서버 동작: `hitl.signal_resume(turn_id, {"action": "continue"})`.

**payload 필드 호환**: `pause` 와 동일 (`session_id` / `turn_id` 둘 다 지원).

#### `cancel` (실행 취소)

```json
{"type": "cancel", "data": {"turn_id": "turn_yyy"}}
```

서버 동작: `hitl.signal_resume(turn_id, {"action": "cancel"})` → `_graph_runner_with_resume` silent drain 후 `complete(status="cancelled")` emit.

**payload 필드 호환**: `pause`/`resume` 와 동일.

#### `todo_modify` / `todo_delete` / `todo_add` (Sprint 14 예정)

Plan 수정 관련. 현재 구조는 있으나 Sprint 14 A1/A2에서 전면 활성화.

### 3.2 Server → Client

> **v1.5 — 카탈로그 엄격 적용 (ADR-011)**. `/ws/hitl` Server→Client 메시지는 **`connected` / `pong` / `error` / `hitl_ack` 4종만**. v1.4 이전에는 `ConnectionManager` 가 user_id 만 봤기 때문에 `/ws/agent` 의 모든 broadcast (`node_event` / `hitl_request` / `paused` / `resumed` / `complete` / `todo_*` / `progress` / `layer_start` / `error`) 이 hitl 소켓에도 leak 되었음 — *spec 위반 leak*. v1.5 에서 `ConnectionManager._connections` 의 키를 `(user_id, channel)` 로 분리하여 leak 제거.

#### `connected`

```json
{"type": "connected", "channel": "hitl", "user_id": "demo", "timestamp": "..."}
```

`channel: "hitl"` 필드는 `/ws/agent` 의 `connected` 와 구분하기 위한 라벨 (`/ws/agent` 는 `session_id` 포함, `/ws/hitl` 는 `channel` 포함).

#### `pong` (ping 응답)

```json
{"type": "pong", "timestamp": "..."}
```

#### `error` (명령 처리 실패)

`/ws/hitl` 의 `error` 는 §6 통일 포맷을 **부분적으로만** 따른다 (Sprint 13 시점 미정비):
- 입력 검증 실패 (`todo_modify`/`todo_delete`/`todo_add`/`todo_edit_nl`): `{type:"error", timestamp, code, layer, severity, message}` — `ErrorCodes.INVALID_MESSAGE` spread (평탄, §6 준수)
- `hitl_response` request_id/action 누락, 핸들러 미상 예외: `{type:"error", timestamp, data:{message}}` — 중첩 (§6 미준수, legacy)

> ⚠️ Sprint 16+ 정비 대상: `/ws/hitl` error 를 §6 평탄 포맷으로 단일화. 클라이언트는 당분간 `error.code ?? error.data?.code`, `error.message ?? error.data?.message` 양쪽 모두 읽어야 함.

#### `hitl_ack` (명령 처리 확인)

```json
// 정상 수락
{
  "type": "hitl_ack",
  "timestamp": "...",
  "data": {"action": "pause"|"resume"|"cancel"|"approve"|..., "session_id": "...", "accepted": true}
}

// Sprint 14 A1 — 비활성 turn 거부 (timeout 이후 또는 이미 종료된 turn)
{
  "type": "hitl_ack",
  "timestamp": "...",
  "data": {
    "action": "pause"|"resume"|"cancel",
    "session_id": "...",
    "accepted": false,
    "reason": "turn_not_active"
  }
}
```

**`hitl_ack.data.reason` 필드 값 카탈로그** (accepted==false 일 때):
| 값 | 의미 | 조건 |
|----|------|------|
| `turn_not_active` | 해당 turn_id 가 `HITLManager._active_turns` 에 없음 — 이미 완료/취소/timeout 된 turn 에 대한 뒤늦은 요청 (Sprint 14 A1 FR-13b) | `ws_hitl._handle_pause/resume/cancel` 가드 |

---

## 4. 이벤트 순서 (happy path)

```
Client                    Server (/ws/agent)             Server (/ws/hitl)
  │                              │                              │
  ├─ type:"query" ────────────────→                              │
  │                              │                              │
  │←── connected ─────────────────┤                              │
  │←── node_event(cognitive) ─────┤                              │
  │←── node_event(planning) ──────┤   [plan_review interrupt]    │
  │←── hitl_request ──────────────┤                              │
  │                              │                              │
  │ (사용자 승인)                  │                              │
  │ hitl_response ─────────────────────────────────────────────→ │
  │                              │      signal_resume(turn_id) ←─│
  │←─────────────────────── hitl_ack ────────────────────────────│
  │                              │                              │
  │←── resumed(approve) ──────────┤                              │
  │←── node_event(execution) ─────┤                              │
  │←── node_event(response) ──────┤                              │
  │←── complete(success) ─────────┤                              │
```

---

## 5. 시나리오

### 5.1 Happy path (approve)
위 이벤트 순서 그대로.

### 5.2 Plan reject
```
→ hitl_request (plan_review)
→ /ws/hitl: hitl_response {action:"reject"}
→ resumed(action:"reject")
→ complete(status:"rejected")
```
reject 시 execution 노드는 실행 안 됨. planning 내부에서 reject 처리 후 조기 종료.

### 5.3 Execution pause → resume
```
→ node_event(execution) [Phase 0 완료]
→ /ws/hitl: pause  (서버: hitl.request_pause)
→ [다음 Phase 진입 직전 execution_pause interrupt]
→ paused event
→ /ws/hitl: resume  (서버: signal_resume continue)
→ resumed(action:"continue")
→ node_event(execution) [Phase 1+ 진행]
→ node_event(response)
→ complete(success)
```

### 5.4 Execution cancel
```
→ paused event (pause 상태)
→ /ws/hitl: cancel
→ resumed(action:"cancel")
→ complete(status:"cancelled")
```

### 5.5 Concurrent limit exceeded

```
→ type:"query" (1st, slot 점유)
→ type:"query" (2nd, 동일 user_id 다른 turn_id)
→ error {code:"CONCURRENT_LIMIT_EXCEEDED", turn_id: <2nd>}
```

2nd 는 서버에서 즉시 거부. 1st 실행은 계속.

### 5.6 Invalid message

```
→ type:"query" {conversation_id:"", turn_id:"...", ...}
→ error {code:"INVALID_MESSAGE", layer:"transport", severity:"fatal", message:"conversation_id is required (non-empty)"}
```

direct-WS 송신 (sender only, 다른 탭 fan-out 없음).

---

## 6. Error 이벤트 카탈로그

모든 error 이벤트는 아래 필드 포함 (Sprint 13 I11-a 포맷 통일):
- `type: "error"`
- `code`: 코드
- `layer`: "transport"|"cognitive"|"planning"|"execution"|"response"|"runtime"
- `severity`: "fatal"|"warning"
- `message`: 사람 읽을 수 있는 메시지
- `detail`: 컨텍스트 dict (선택)
- `conversation_id` / `turn_id`: fan-out error만 포함 (direct-WS는 생략 가능)

| code | layer | severity | emit 경로 | 설명 |
|------|-------|----------|-----------|------|
| `INVALID_MESSAGE` | transport | fatal | direct (sender WS) | `_parse_query_message` 검증 실패 |
| `CONCURRENT_LIMIT_EXCEEDED` | transport | fatal | fan-out | user당 MAX 슬롯 초과 |
| `EXECUTION_ERROR` | runtime | fatal | fan-out | run_turn 내부 예외 (graph error 등) |
| `COGNITIVE_EMPTY_QUERY` | cognitive | fatal | fan-out | layer guard — structured_query 비어있음 |
| `PLANNING_EMPTY_PLAN` | planning | fatal | fan-out | layer guard — plan.todos 없음 |
| `EXECUTION_ALL_FAILED` | execution | fatal | fan-out | layer guard — 모든 todo 실패 |
| `EXECUTION_PARTIAL_FAILED` | execution | warning | fan-out | layer guard — 일부 todo 실패 |
| `RESPONSE_EMPTY` | response | fatal | fan-out | layer guard — response 비어있음 |

**fatal 동작**: layer guard fatal → `complete(status="aborted", reason=code)` emit 후 run_turn 종료.
**warning 동작**: 그래프 계속 진행. `complete.data.guard_warnings` 에 누적되어 전달됨.

**JSONL 로그**: `logs/layer_guard.jsonl` (append-only, fatal+warning 모두 기록) — 프롬프트 튜닝 / 학습 데이터 누적용.

---

## 7. interrupt payload 실제 구조

`10_system_architecture_v1.9.md §4.3.4` 참조. 요약:

- **plan_review**: `{"type": "plan_review", "plan": {...Plan dump...}, "message": "..."}`
- **execution_pause**: `{"type": "execution_pause", "progress": {...ExecutionProgress dump...}}`

`_extract_interrupt_value` (ws_agent.py)이 `graph_state.tasks[0].interrupts[0].value` 에서 추출 → `_build_hitl_request_data` / `_build_paused_data` 로 클라이언트 payload 구성.

---

## 8. 하위 호환 정책

| 영역 | Sprint 13 | Sprint 14 계획 |
|------|-----------|---------------|
| `type: "start"` legacy | 유지 (`_run_agent` 호출) | Sprint 14 regression 완료 후 제거 |
| `session_id` 필드 | 호환 alias 유지 (내부 변수) | 유지 (외부 계약 계속 사용 금지) |
| Sprint 12 이벤트 (`layer_start`, `todo_start`, `todo_complete`, `progress`) | **신 경로에서도 emit** (I11-b2 fix — callback_manager bridge 경유) | Sprint 14에서 `layer_complete` 등 추가 이벤트 검토 |

---

## 9. 코드 참조

| 기능 | 파일 |
|------|------|
| `/ws/agent` 엔드포인트 | `backend/api/ws_agent.py::stream_endpoint` |
| `/ws/hitl` 엔드포인트 | `backend/api/ws_hitl.py::hitl_endpoint` |
| `run_turn` (신 경로) | `backend/api/ws_agent.py::run_turn` |
| `_graph_runner_with_resume` | `backend/api/ws_agent.py` (I11-a) |
| `ConnectionManager` | `backend/api/connection_manager.py` (Sprint 13 T1) |
| `ConcurrencyManager` | `backend/app/dream_agent/workflow_managers/concurrency_manager.py` (T2) |
| `hitl_manager.wait_for_resume` / `signal_resume` | `backend/app/dream_agent/workflow_managers/hitl_manager/manager.py` (I7) |
| Layer Guard | `backend/app/dream_agent/system_graph/layer_inspector.py` (I11-a) |
| `_parse_query_message` | `backend/api/ws_agent.py` (I10a) |

---

## 변경 이력

> 프레임워크 추출(2026-06-19) 이전(마케팅 도메인 시기)의 상세 변경 이력은 git 히스토리를 참조하세요.
