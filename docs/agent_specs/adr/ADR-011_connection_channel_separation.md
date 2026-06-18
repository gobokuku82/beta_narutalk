# ADR-011: ConnectionManager 채널 분리 — multi-tab vs multi-channel fan-out 구분

## Status

**Accepted** (2026-05-16) — Stage 5 통과. ws_contract 브랜치 main merge.

이전 이력:
- Proposed (2026-05-15) — Stage 0 ~ 4 작업 중.

## Context

### 발견 — Phase 1 통합 직후 회귀 보고 (2026-05-15)

사용자 보고: 검토 OFF 모드 query 송신 시 **assistant 응답 메시지가 두 번 표시됨**.

코드 추적 결과:

1. [connection_manager.py:62-75](../../../backend/api_v2/connection_manager.py#L62) 의 `broadcast_to_user(user_id, message)` 가 **채널을 모름**. user_id 만 보고 그 사용자의 *모든* WS 에 송신.

2. [`/ws/agent`](../../../backend/api_v2/ws_agent.py) 와 [`/ws/hitl`](../../../backend/api_v2/ws_hitl.py) 가 **같은 conn_manager 싱글톤** 사용. 한 user_id="demo" 의 list 에 `agent_socket` + `hitl_socket` 함께 등록됨.

3. 프론트 [useWebSocket.ts:22-26](../../../frontend/src/api/hooks/useWebSocket.ts#L22) 가 **양 채널 onmessage 에 같은 fanout** 등록. 같은 `complete` 메시지가:
   - agent_socket.onmessage → fanout → `useAgent.handleWSMessage('complete')` → `appendAssistantMessage(text)` ✓
   - hitl_socket.onmessage → fanout → `useAgent.handleWSMessage('complete')` → `appendAssistantMessage(text)` ✗ (두 번째 push)

### 의도 vs 현실의 괴리

spec 21 v1.4 의 *의도*:

| 채널 | Server→Client 카탈로그 (§3.2) |
|------|---------|
| `/ws/agent` | node_event / hitl_request / paused / resumed / complete / error / todo_* / progress / layer_start / connected / pong |
| `/ws/hitl` | **hitl_ack / connected / pong / error 만** |

즉 *두 채널의 내용은 분리되어야 한다*. spec 21 §1.2 의 fan-out 의도 = **multi-tab 동기화** (한 사용자가 탭 두 개 열면 양 탭 ws_agent 둘 다 받음).

### 근본 원인

`ConnectionManager._connections: dict[str, list[WebSocket]]` 자료구조가 **multi-tab + multi-channel 을 한 차원으로 묶음**. user_id 만 키로 사용하므로 *같은 탭 안의 두 채널* 도 같은 user_id 라 같이 broadcast 받음.

→ multi-tab 동기화 + 채널 분리 두 의도를 동시에 만족할 수 없음.

### 호출처 매트릭스 (Stage 0 점검 결과)

| 파일 | 호출 | 채널 |
|------|------|------|
| [`ws_agent.py`](../../../backend/api_v2/ws_agent.py) | 12 broadcast + 1 connect + 2 disconnect | **agent** |
| [`ws_hitl.py`](../../../backend/api_v2/ws_hitl.py) | 0 broadcast + 1 connect + 2 disconnect | **hitl** |
| [`tests/sprint13/test_ws_agent_query_routing_unit.py`](../../../backend/tests/sprint13/test_ws_agent_query_routing_unit.py) | 3 broadcast (mock) | **agent** |
| [`error_codes.py`](../../../backend/api_v2/error_codes.py) | 0 (docstring 예시만) | — |

ws_hitl 의 `hitl_ack` 송신은 [`_safe_send(websocket, ...)`](../../../backend/api_v2/ws_hitl.py) — `websocket.send_json` 직접 호출이라 conn_manager 미경유. **leak 방향은 agent → hitl 단방향만** (hitl 쪽은 leak 송신 없음).

### 대안 검토

| 옵션 | 본질 vs 회피 | 분량 |
|------|---------|------|
| **A. 프론트 hitlFanout 가 spec 외 type drop** | 회피 — 백엔드 leak 을 프론트가 흡수. 부채 잔존 | 1 commit |
| **B. 메시지 dedup (key + TTL)** | 회피 — 부작용 가능 (정당한 두 다른 메시지를 dedup 위험) | 1~2 commit |
| **C. 백엔드 conn_manager 채널 분리 (본 ADR)** | **본질** — spec 21 §3.2 의도와 정합 | 5 Stage / 14 commit (TDD) |

옵션 A/B 는 회피책이라 *기억해야 할 부채* 누적. 본질 해결은 백엔드 conn_manager 가 채널을 인식하는 것.

## Decision

**ConnectionManager 의 자료구조와 시그니처를 채널 분리하도록 변경**.

### 자료구조 변경

```python
# Before
_connections: dict[str, list[WebSocket]]              # user_id → ws[]

# After
Channel = Literal["agent", "hitl"]
_connections: dict[str, dict[Channel, list[WebSocket]]]  # user_id → channel → ws[]
```

### 시그니처 변경

```python
async def connect(user_id: str, channel: Channel, ws) -> bool
async def disconnect(user_id: str, channel: Channel, ws) -> None
async def broadcast_to_user(user_id: str, channel: Channel, message: dict) -> None
```

### MAX_WS_CONNECTIONS_PER_USER 정책

`(user_id, channel)` **별** 5. 즉 한 사용자가 탭 5개 열면 agent 5 + hitl 5 = 총 10 ws 가능. 채널 분리의 본질 정합.

### Multi-tab 동기화 의도 보존

같은 `(user_id, channel)` 안의 여러 ws 에 대해 fan-out 은 유지. 한 사용자가 탭 두 개 열면 두 탭의 ws_agent 둘 다 broadcast 받음. spec 21 §1.2 multi-tab 동기화 의도 손실 X.

### 호출처 갱신 범위

| 파일 | 변경 |
|------|------|
| `ws_agent.py` | 12 broadcast + 1 connect + 2 disconnect 에 `channel="agent"` 추가 |
| `ws_hitl.py` | 1 connect + 2 disconnect 에 `channel="hitl"` 추가 |
| `test_ws_agent_query_routing_unit.py` | 3 mock broadcast 에 채널 인자 추가 |
| `error_codes.py` | docstring 예시 갱신 (실제 호출 0) |

## Consequences

### Positive

1. **답변 중복 자동 해소** — agent 채널 broadcast 가 더 이상 hitl 소켓에 leak 안 됨 → 프론트 fanout 그대로 두어도 메시지 1회만 처리.
2. **spec 21 §3.2 카탈로그 계약 회복** — hitl 채널이 정의된 4종 (hitl_ack / connected / pong / error) 만 받음.
3. **Multi-tab 동기화 유지** — 같은 (user, channel) 안의 fan-out 보존.
4. **확장성** — 향후 채널 추가 (예: `/ws/observability`) 시 동일 패턴.
5. **프론트 변경 0** — 자연 dedup.

### Negative

1. **회귀 가능성** — sprint13 의 41+ 테스트가 옛 시그니처에 hard-coded. 점진 갱신 필요.
2. **분량** — 5 Stage / 14 atomic commit / ~3~4 시간.
3. **spec 21 minor bump** — v1.4 → v1.5 동반. stale 링크 sed 13 active spec 갱신.

### Risk Mitigation

- TDD (Stage 1 RED → Stage 2 GREEN) 로 회귀 사전 차단.
- Stage 3 의 점진 갱신 (한 파일씩) 으로 fail 격리.
- 5 Stage self-review 체크리스트로 단계마다 정합 검증.

## Alternatives Considered

### Alt A: 프론트 hitlFanout 가 spec 외 type drop

```ts
const HITL_ALLOWED = ['hitl_ack', 'connected', 'pong', 'error'];
const hitlFanout = (msg) => {
  if (!HITL_ALLOWED.includes(msg.type)) return;
  // ...
};
```

**기각 사유**: 백엔드 spec 위반 leak 을 프론트가 흡수. 부채가 *프론트 코드 한 줄* 로 영구 잔존. 향후 spec 21 변경 시 fragile.

### Alt B: 메시지 dedup (key + TTL)

```ts
const recentKeys = new Set<string>();
const dedup = (msg) => {
  const key = dedupKey(msg);
  if (recentKeys.has(key)) return null;
  recentKeys.add(key);
  setTimeout(() => recentKeys.delete(key), 1000);
  return msg;
};
```

**기각 사유**: 정당한 두 다른 메시지를 dedup 할 위험. key 함수 잘못 짜면 silent fail. 백엔드 leak 의 *증상만 가림*.

### Alt D: hitl 채널을 폐지하고 단일 `/ws/main` 으로 통합

**기각 사유**: spec 21 §0 의 *분리 이유* 가 명료 — backpressure / 생명주기 분리, **pause 중에도 명령 받기 위함**. 통합 시 본질 손실.

## Verification Plan (Stage 별)

본 ADR 의 *implementation* 은 [docs/_claude/ws_channel_separation_plan_2026-05-15.md](../../_claude/ws_channel_separation_plan_2026-05-15.md) 의 5 Stage TDD 계획으로 수행. 통과 시 본 ADR 의 Status 를 Accepted 로 갱신.

| Stage | 검증 |
|-------|------|
| 0 | ADR-011 + spec 21 v1.5 초안 + 호출처 매트릭스 |
| 1 | 신규 단위/통합/contract 테스트 RED 확인 |
| 2 | ConnectionManager GREEN — 모든 신규 + 영향받은 기존 테스트 통과 |
| 3 | ws_agent / ws_hitl / tests 점진 갱신 + 부팅 smoke |
| 4 | spec 21 v1.5 정식 + spec 12 + INDEX 정합 |
| 5 | E2E — 답변 중복 해소 + multi-tab 동기화 회귀 X + P1-10 시나리오 회귀 X |

## 관련 명세 / 결정

- spec 21 v1.4 → v1.5 (`21_WEBSOCKET_PROTOCOL_v1.5.md`) §1.2 §1.3 §3.2 갱신
- spec 12 v1.3 → v1.4 (Manager Layer) ConnectionManager API 갱신
- spec 10 (System Architecture) §4.2 Connection Manager 링크 갱신
- spec 15 v1.0 (End-to-End Flow) — 그대로 (사용자 보이는 흐름 동일)

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-15 | 초안 (Stage 0) — Proposed |
| 2026-05-16 | 5 Stage 통과 (Stage 1 RED 35건 → Stage 2 GREEN → Stage 3 호출부 점진 + sprint13 172/172 회귀 통과 → Stage 4 spec 21 v1.5 + spec 12 v1.4 + INDEX 정합 → Stage 5 사용자 E2E 검증 답변 중복 해소 확인). 추가 발견 — assistant 메시지 순서 (Stage 6) 동반 fix. Accepted. ws_contract 브랜치 main merge |
