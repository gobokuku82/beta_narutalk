# Manager Layer Specification (Sprint 13+)

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 개발 - 아키텍처 |
| 진행상태 | **Active** (ws_contract 브랜치 Stage 4) |
| 버전 | **v1.4** |
| 최종 수정일 | 2026-05-16 |
| 이전 버전 | v1.3 (2026-04-24), v1.2 (2026-04-23), `legacy/12_manager_layer_v1.1.md` |
| 선행 문서 | `10_system_architecture_v1.9.md` §4 (Manager 개요) |
| 관련 명세 | `11_main_graph_state_v1.5.md`, `21_WEBSOCKET_PROTOCOL_v1.5.md`, `22_error_codes_v1.1.md` |

**v1.4 (2026-05-16) 변경점** — ADR-011 ConnectionManager 채널 분리:

- §1 ConnectionManager 시그니처 변경 — `connect/disconnect/broadcast_to_user` 가 `channel: Channel` 인자 추가 (Channel = `Literal["agent", "hitl"]`).
- `_connections` 자료구조 변경 — `dict[str, list[ws]]` → `dict[str, dict[Channel, list[ws]]]`.
- MAX_WS_CONNECTIONS_PER_USER 정책 = `(user, channel)` 별 5.
- Multi-tab 동기화 의도 보존 — 같은 (user, channel) 안의 fan-out 유지.
- 호출자 영향: `ws_agent.py` 가 `channel="agent"` 명시, `ws_hitl.py` 가 `channel="hitl"` 명시.

**v1.3 (2026-04-24) 변경점** — Sprint 14 A3 Phase 5 (편집 경로 통합):
- `HITLManager._progress` 수명주기 확장 — 기존 execution_stage 만 생성하던 것을 **`_graph_runner_with_resume` 의 plan_review 분기에서도 임시 progress 생성** (status="paused"). 사용자 요구사항 §4 "hitl=pause 같은 개념" 반영.
- `cleanup_turn` 확장: `_progress.pop` 추가 — 임시 progress leak 방지 (기존엔 execution 완료 후에도 잔류)
- `_handle_hitl_response` 의 approve 분기가 progress 존재 시 `{action:"modify", value:progress.plan}` 로 signal_resume 변환 — planning_stage L88-92 modify 분기 활용

**v1.2 (2026-04-23) 변경점**:
- Sprint 14 A3 Phase 2 반영 — `HITLManager` 에 `_get_lock(session_id) → asyncio.Lock` 추가 (D9 L1 per-session Lock)
- `_session_locks: dict[str, asyncio.Lock]` 필드 추가
- `cleanup_turn` 확장: `_session_locks.pop` (Lock 누수 방지)
- `handle_todo_edit/delete/add` Status 마커 추가 (Sprint 12 partial → A3 Phase 2 complete — 가드/Lock/테스트 완성)
- `plan_editor.py` Y-a NL 편집 경로 (Phase 3) — parse_instruction / apply_edit (reorder 신구현) / validate_edit / `MAX_INSTRUCTION_LEN=500` + `_sanitize` prompt injection 방어 (D-13)
- 12_manager_layer 은 본 bump 에서 Sprint 14 A3 가 도입한 API 만 요약. 상세는 코드 + 10_v1.9 §4.3 참조

> **진실 소스**: 각 매니저 구현 파일 (`backend/app/...` / `backend/api/...`).
> 이 문서는 매니저 간 관계 + 수명주기 + 등록/해제 주체를 통합 설명.

---

## 0. 개요

DreamAgent V2의 **Manager 계층** 단일 문서.

### 0.1 왜 이 문서가 필요했나 (drift 사례)

Sprint 13 I11-a 초기 구현에서 **`run_turn`이 `callback_manager`에 등록 안 하는 누락** 발생 → Executor가 emit한 `todo_start/complete/progress` 이벤트가 리스너 없이 버려짐 → 대시보드 Todo 실시간 표시 안 됨 (I11-b2에서 발견 + 수정).

근본 원인: **매니저별 "누가 언제 register/unregister 하는가"가 단일 문서에 없었음**. 각 매니저가 system_architecture §4에 개략 설명만 있음.

이 문서는 이런 drift 재발 방지 목적.

### 0.2 매니저 목록

| # | 매니저 | 카테고리 | Sprint | 코드 |
|---|--------|----------|--------|------|
| 1 | ConnectionManager | 전송(WS) | 13 T1 | `backend/api/connection_manager.py` |
| 2 | ConcurrencyManager | 실행 제어 | 13 T2 | `backend/app/dream_agent/workflow_managers/concurrency_manager.py` |
| 3 | CallbackManager | 내부 이벤트 라우팅 | 10~ | `backend/app/dream_agent/workflow_managers/callback_manager/callback_manager.py` |
| 4 | HITLManager | PM + HITL | 12~ | `backend/app/dream_agent/workflow_managers/hitl_manager/manager.py` |
| 5 | TodoManager | Plan / DAG / Cascade | 12~ | `backend/app/dream_agent/workflow_managers/todo_manager/` |

```
전송 계층:         ConnectionManager         (WebSocket fan-out)
제어 계층:         ConcurrencyManager        (slot)
                  HITLManager (PM)          (Plan 승인 + pause/resume + Queue)
내부 이벤트:       CallbackManager           (session_id 라우팅)
Plan 조작:         TodoManager               (DAG 분석, cascade 무효화)
```

---

## 1. ConnectionManager (Sprint 13 T1 + ADR-011 채널 분리)

### 1.1 책임
- `(user_id, channel)` 기반 WebSocket 다중 연결 관리 (**탭 다중 지원** + **채널 분리**)
- `broadcast_to_user(user_id, channel, message)` → 해당 (user, channel) 의 모든 WS 에 **fan-out**. **다른 채널로 leak 없음**.
- MAX_WS_CONNECTIONS_PER_USER 초과 시 `close(1008)` — **(user, channel) 별** 카운트.
- 송신 실패 WS 자동 정리 (dead WS) — 해당 (user, channel) 리스트에서만.

### 1.2 싱글톤
```python
# 싱글톤 (프로덕션)
from api.connection_manager import conn_manager, Channel
```

### 1.3 API (v1.4 — ADR-011)

```python
Channel = Literal["agent", "hitl"]

class ConnectionManager:
    async def connect(user_id: str, channel: Channel, ws) -> bool
        # True 성공, False 한도 초과 — (user, channel) 별 MAX 카운트
    async def disconnect(user_id: str, channel: Channel, ws) -> None
        # idempotent
    async def broadcast_to_user(user_id: str, channel: Channel, message: dict) -> None
        # fan-out + dead WS 정리 — 호출된 (user, channel) 안에서만
    # 내부: _connections: dict[str, dict[Channel, list[WebSocket]]]
    #       _max_connections (Settings.MAX_WS_CONNECTIONS_PER_USER, 기본 5)
```

자료구조 예:
```python
{"demo": {"agent": [ws1, ws2], "hitl": [ws3]}}
```

### 1.4 등록/해제 주체
| 경로 | 등록 | 해제 | 채널 |
|------|------|------|------|
| `/ws/agent` | `stream_endpoint` 시작 시 accept 후 connect | `WebSocketDisconnect` or except에서 disconnect | `"agent"` |
| `/ws/hitl` | `hitl_endpoint` 시작 시 동일 | 동일 | `"hitl"` |

### 1.5 테스트
- 단일 채널 회귀 (agent 기준).
- 실 ASGI WS 회귀.
- ADR-011 채널 분리 검증.
- dual-channel leak 방지 통합.
- spec 21 §3.2 contract.
- Fixture: `reset_conn_manager` (conftest.py)

---

## 2. ConcurrencyManager (Sprint 13 T2)

### 2.1 책임
- **user_id당 동시 실행 turn 슬롯 제한** (MAX_CONCURRENT_TURNS_PER_USER, 기본 3)
- `try_acquire(user_id, turn_id)` → 성공 시 slot 점유, 실패 시 `CONCURRENT_LIMIT_EXCEEDED`
- `release(user_id, turn_id)` → slot 반환
- `active_count(user_id)` → 현재 점유 slot 수

### 2.2 싱글톤
```python
from app.dream_agent.workflow_managers.concurrency_manager import concurrency
```

### 2.3 API

```python
class ConcurrencyManager:
    def try_acquire(user_id: str, turn_id: str) -> bool
    def release(user_id: str, turn_id: str) -> None
    def active_count(user_id: str) -> int
    def _reset_for_test() -> None   # 테스트 전용
    # 내부: _slots: dict[str, set[str]]
    #       _max_concurrent (Settings.MAX_CONCURRENT_TURNS_PER_USER)
```

### 2.4 등록/해제 주체
| 시점 | 주체 | 메서드 |
|------|------|--------|
| `run_turn` 진입 | ws_agent | `try_acquire` |
| `run_turn` finally | ws_agent | `release` (idempotent) |

### 2.5 테스트
- `test_concurrency_manager_unit.py` (9)
- Fixture: `fresh_concurrency_singleton` (개별 테스트 파일 내)

---

## 3. CallbackManager (Sprint 10~)

### 3.1 책임 (⚠️ drift 주의 모듈)
- **내부 이벤트 라우팅** — Executor / execution_stage 등 내부 컴포넌트가 emit한 이벤트를 외부 리스너(WS)에게 전달
- `session_id` 기반 라우팅 (Sprint 13에서 `session_id = turn_id` alias)
- 다중 리스너 지원 (list[callback])

### 3.2 싱글톤
```python
from app.dream_agent.workflow_managers.callback_manager import get_callback_manager
cb = get_callback_manager()
```

### 3.3 API

```python
class CallbackManager:
    def register(session_id: str, callback: async_fn) -> None
    def unregister(session_id: str) -> None
    async def emit(session_id: str, event: dict) -> None   # 모든 리스너에 전달
    # 내부: _listeners: dict[str, list[CallbackType]]
```

### 3.4 등록/해제 주체 (⚠️ Sprint 13 bridge 포함)

| 경로 | 등록 | 해제 | 등록하는 callback |
|------|------|------|-------------------|
| Sprint 12 legacy `_run_agent` | 진입 시 `register(session_id, lambda evt: _safe_send(ws, evt))` | try/finally unregister | WS 직접 송신 |
| **Sprint 13 `run_turn` (query)** | `_graph_runner_with_resume` 진입 시 **`unregister(turn_id)` 후 `register(turn_id, _callback_bridge)`** (중복 누적 방지) | `run_turn` finally `unregister(turn_id)` | **`conn_manager.broadcast_to_user(user_id, "agent", ...)` fan-out** (I11-b2, v1.4 부터 channel 명시 — ADR-011) |
| **Sprint 13 `run_turn` (resume_query)** | 동일 — unregister→register 패턴 | 동일 | 동일 |

**중복 register 방지** (R-9 구현 시 RO-11 테스트로 발견):
`register`는 내부 list 에 append 구조라 같은 `turn_id`로 재진입 시 listener가 누적 → 이벤트 2배/3배 중복 fan-out 위험.  
`_graph_runner_with_resume` 진입 시 항상 `unregister → register` 순서로 호출해 **listener는 turn_id 당 정확히 1개** 유지.

Sprint 13 bridge 코드 (`ws_agent.py::_graph_runner_with_resume`):
```python
async def _callback_bridge(evt: dict) -> None:
    enriched = dict(evt)
    enriched.setdefault("conversation_id", conv_id)
    enriched.setdefault("turn_id", turn_id)
    await conn_manager.broadcast_to_user(user_id, "agent", enriched)

# 중복 누적 방지 (R-9 resume_query 재진입 대응)
cb_manager.unregister(turn_id)
cb_manager.register(turn_id, _callback_bridge)
```

### 3.5 emit 이벤트 (진실 소스 = 코드)

| 이벤트 | emit 위치 | 데이터 |
|--------|-----------|--------|
| `layer_start` | `execution_stage.py:61` (execution 진입 즉시) | `{"layer": "execution"}` |
| `todo_start` | `executor.py:295` | `{"todo_id", "tool", "agent", "team", "priority"}` |
| `todo_complete` | `executor.py:324` | `{"todo_id", "tool", "status", "duration_ms", "is_mock", "summary"}` |
| `progress` | `executor.py:341` | `{"completed", "total", "percent", "phase", "phases_total"}` |
| `paused` | `executor.py:368` | `pause_controller` 경로 — **Sprint 13에서는 emit 안 됨** (run_turn은 langgraph interrupt 사용) |
| `resumed` | `executor.py:383` | 위와 동일 — Sprint 13 경로에서 emit 안 됨 |

**주의**: `paused` / `resumed` 는 Sprint 13 경로에서 executor 아닌 **`_graph_runner_with_resume`가 직접 `conn_manager`로 emit** (callback 경유 X).

### 3.6 체크리스트 — Executor/Stage에서 새 이벤트 추가 시
- [ ] `execution_stage.py` 또는 `executor.py`에 `cb_manager.emit(session_id, ...)` 추가
- [ ] 이 문서 §3.5 표에 행 추가
- [ ] `21_WEBSOCKET_PROTOCOL_v1.4.md` §2.2 이벤트 카탈로그에 추가
- [ ] 대시보드 `handleEvent`에 핸들러 추가
- [ ] `22_error_codes_v1.1.md` (error 이벤트인 경우)

### 3.7 테스트
- 현재 직접 단위 테스트 없음 — 통합 테스트에서 간접 검증 (e.g., `test_ws_agent_query_routing_unit.py`)
- Sprint 14+에서 unit 테스트 추가 검토

---

## 4. HITLManager (Sprint 12 + 13)

### 4.1 책임
- **PM / HITL Layer** — Plan 분해 → Phase → 실행 통제
- Plan 승인 / Execution Pause / Resume / Cancel
- Todo 수정/삭제/추가 + Cascade 무효화 (TodoManager 연계)
- Progress 영속화 (`ExecutionProgress`)
- **Sprint 13 I7 추가**: `asyncio.Queue` 기반 resume signal (`wait_for_resume` / `signal_resume` / `cleanup_turn`)

### 4.2 싱글톤
```python
from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager
hitl = get_hitl_manager()
```

### 4.3 API (주요)

```python
class HITLManager:
    # ❌ (2026-06-11 폐기) Sprint 12 event 트랙 — create_request / wait_for_response /
    #    submit_response / get_pending_request / cancel_request / cleanup 및
    #    HITLRequest/HITLResponse/HITLRequestType 모델 전부 삭제.
    #    _run_agent 폐기(533a632, 05-31) 후 빈 장부 조회로 hitl_ack.accepted 가 항상
    #    False 였던 거짓 신호 버그의 원인. 복원은 git 히스토리 참조.

    # Pause / Resume (Sprint 12)
    def request_pause(session_id: str, reason: str = "user_request") -> None
    def request_resume(session_id: str) -> None
    def request_cancel(session_id: str) -> None
    def is_paused(session_id: str) -> bool

    # Progress (Sprint 12)
    def create_progress(session_id: str, plan: dict) -> ExecutionProgress
    def restore_progress(session_id: str, saved: dict) -> ExecutionProgress
    def get_progress(session_id: str) -> Optional[ExecutionProgress]
    def get_progress_snapshot(session_id: str) -> dict
    def report_phase_complete(session_id: str, phase_results: list) -> None
    def should_continue(session_id: str) -> dict

    # 🔴 Sprint 13 I7 신규 (asyncio.Queue 트랙)
    async def wait_for_resume(turn_id: str, timeout: Optional[float] = None) -> dict
    def signal_resume(turn_id: str, action: dict) -> None
    def cleanup_turn(turn_id: str) -> None
    def _reset_resume_queues_for_test() -> None

    # 🟢 Sprint 14 A1 신규 (HITL resume timeout)
    def register_turn(turn_id: str) -> None          # run_turn 진입 시 호출
    def is_turn_active(turn_id: str) -> bool          # ws_hitl 가드에서 검사
    # wait_for_resume 확장: timeout 초과 시 {"action":"timeout"} 반환 (Sprint 14)
    # cleanup_turn 확장: _active_turns + _paused.discard 추가 (CS-2 잔류 방지)

    # 내부 state  (장부 3종 _pending_requests/_response_events/_responses 는 2026-06-11 폐기)
    _progress: dict[str, ExecutionProgress]      # ExecutionProgress dataclass (L20)
    _paused: set[str]                            # Sprint 12 pause 플래그
    _resume_queues: dict[str, asyncio.Queue]     # Sprint 13 I7
    _active_turns: set[str]                      # 🟢 Sprint 14 A1 — 활성 turn 레지스트리
```

### 4.4 ~~이중 트랙 주의~~ → 단일 트랙 (2026-06-11 해소)

| 트랙 | API | 경로 | 사용 주체 |
|------|-----|------|-----------|
| ~~Sprint 12 Event~~ | ~~`create_request` / `wait_for_response` / `submit_response`~~ | **폐기(2026-06-11)** — `_run_agent` 폐기 후 빈 장부가 hitl_ack accepted=False 거짓 신호를 만들던 잔재 | — |
| **Sprint 13 Queue** (유일) | `wait_for_resume` / `signal_resume` / `cleanup_turn` | `_graph_runner_with_resume` | `/ws/hitl` handlers → `signal_resume(turn_id, action)`. `hitl_ack.accepted` = 재개 신호 전달 여부 |

**공유 상태**:
- `_paused`: 두 트랙 공통 사용 (auto-approve 로직에서 `is_paused(turn_id)` 체크)
- `_progress`: 두 트랙 공통 사용 (ExecutionProgress 영속화)
- `_active_turns` (Sprint 14~): run_turn 수명주기 추적, ws_hitl 가드에서 사용

**격리된 상태**:
- `_pending_requests` / `_response_events` / `_responses`: Sprint 12 전용
- `_resume_queues`: Sprint 13 전용

### 4.5 테스트
- `test_hitl_resume_queue_unit.py` (8, I7)
- `test_ws_hitl_integration.py` (7, I9) — Sprint 14 에 register_turn fixture 보강
- `sprint14/test_hitl_timeout_unit.py` (6, 그룹 A)
- `sprint14/test_hitl_timeout_guard_unit.py` (7, 그룹 B)
- `sprint14/test_hitl_timeout_integration.py` (13, 그룹 C)
- `sprint14/test_settings_validator_unit.py` (5, 그룹 D)
- `sprint14/test_hitl_timeout_resume_query_unit.py` (1, 그룹 E)
- `sprint14/test_hitl_timeout_race_unit.py` (2 × 100회, 그룹 F)
- `sprint14/test_hitl_timeout_e2e_live.py` (4, 그룹 G, @live)
- Fixture: `fresh_hitl` (conftest.py) — 모든 내부 state clear (`_active_turns` 포함)

---

## 5. TodoManager (Sprint 12)

### 5.1 책임
- Todo 상태 전이 (pending → in_progress → completed/failed)
- **DAG cascade 계산** (`calculate_cascade`) — Todo 수정 시 downstream BFS 무효화
- **Phase 빌드** (`_build_phases_from_plan`) — DAG → Phase(동시 실행 가능한 Todo 묶음) 변환

### 5.2 위치
```python
from app.dream_agent.workflow_managers.todo_manager import todo_manager
# 또는 hitl_manager 내부에서 직접 사용
```

### 5.3 API

```python
class TodoManager:
    def calculate_cascade(plan: dict, modified_todo_ids: list[str]) -> CascadeResult
    def _build_phases_from_plan(plan: dict) -> list[list[str]]   # [[t1], [t2,t3], [t4]]
    def transition(todo_id: str, new_status: TodoStatus) -> None
    # final 상태 (completed/failed/skipped/cancelled) 덮어쓰기 차단
```

### 5.4 HITLManager와의 관계
- HITLManager가 Todo 수정/삭제/추가 요청 받음
- 내부에서 TodoManager.calculate_cascade 호출
- 결과로 `_progress.completed_todos` 에서 invalidated 제거
- `_progress.phases` 재구성

### 5.5 테스트
- 단위 테스트 별도 없음 (HITLManager 통해 간접 검증)
- Sprint 14+ 단위 테스트 추가 검토

---

## 6. 매니저 간 의존성 다이어그램

```
┌─────────────────────────────────────────────────────┐
│               /ws/agent / /ws/hitl (엔드포인트)       │
└───────────────┬─────────────────────┬───────────────┘
                │                     │
                ▼                     ▼
     ┌──────────────────┐   ┌────────────────────┐
     │ ConnectionManager │   │  ConcurrencyManager │
     │  (user_id 등록)   │   │   (slot 획득)       │
     └────────┬─────────┘   └─────────┬──────────┘
              │                       │
              │  broadcast_to_user    │
              │                       ▼
              │            ┌───────────────────────┐
              │            │   run_turn            │
              │            │   + _graph_runner_    │
              │            │     with_resume       │
              │            └─────┬────┬────────────┘
              │                  │    │
              │      register    │    │ wait_for_resume / signal_resume
              │◄─────(bridge)────┤    │ restore_progress / is_paused
              │                  ▼    ▼
              │         ┌─────────────────┐  ┌─────────────────┐
              │         │ CallbackManager │  │  HITLManager    │
              │         │ (session 이벤트)│  │  (PM + Queue)   │
              │         └────────┬────────┘  └────────┬────────┘
              │                  │                    │
              │       emit       │                    │ calculate_cascade
              │◄─────(bridge)────┤                    ▼
              │                  │           ┌────────────────┐
              │                  │           │  TodoManager   │
              ▼                  │           │  (DAG / Phase) │
       (클라이언트 WS)            │           └────────────────┘
                                 │
                     ┌───────────▼──────────┐
                     │  Executor /          │
                     │  execution_stage     │
                     │  (todo_* emit)       │
                     └──────────────────────┘
```

**핵심 흐름**:
1. `run_turn`은 `ConcurrencyManager.try_acquire` 로 slot 점유
2. `_graph_runner_with_resume`가 `CallbackManager.register(turn_id, bridge)` 등록
3. Executor emit → CallbackManager → bridge → `ConnectionManager.broadcast_to_user(user_id, "agent", ...)` (v1.4 — ADR-011 channel 명시)
4. interrupt 발생 시 `HITLManager.wait_for_resume(turn_id)` 대기
5. `/ws/hitl` 수신 → `HITLManager.signal_resume(turn_id, action)` → 재개
6. finally: `ConcurrencyManager.release` + `HITLManager.cleanup_turn` + `CallbackManager.unregister`

---

## 7. 신규 매니저 추가 체크리스트

Sprint 14+ 에서 매니저 추가 시:

- [ ] 파일 생성: `backend/app/dream_agent/workflow_managers/<new_manager>/`
- [ ] 싱글톤 get 함수 제공 (`get_xxx_manager()`)
- [ ] `_reset_for_test()` 구현 (테스트 격리용)
- [ ] 이 문서 §N 신규 섹션 추가 (책임/API/등록 주체/테스트/의존성)
- [ ] §0.2 매니저 목록 표 갱신
- [ ] §6 의존성 다이어그램 갱신
- [ ] `10_system_architecture_v1.9.md` §4.2 Manager 목록 표 갱신
- [ ] 테스트 fixture 추가 (`conftest.py`)

---

## 변경 이력

> 프레임워크 추출(2026-06-19) 이전(마케팅 도메인 시기)의 상세 변경 이력은 git 히스토리를 참조하세요.
