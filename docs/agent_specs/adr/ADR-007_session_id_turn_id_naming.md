# ADR-007: session_id ↔ turn_id 네이밍 정책

## Status

Accepted (2026-04-27)

## Context

코드·문서·메시지 페이로드 전반에 걸쳐 동일한 식별자가 두 이름으로 혼재.

| 위치 | 사용 이름 | 출신 |
|------|----------|------|
| `state["session_id"]` | session_id | Sprint 12 legacy |
| `agent.invoke({"configurable": {"thread_id": ...}})` | thread_id (`f"{conv}_{turn}"`) | LangGraph |
| `_chunk_to_event(chunk, conv_id, turn_id)` | turn_id | Sprint 13 신경로 |
| `ws_hitl.py` `_check_turn_active` 의 `payload.get("turn_id") or payload.get("session_id")` | 둘 다 fallback | 호환 처리 |
| `dashboard/index.html` `_currentHitlSessionId = payload.session_id \|\| payload.turn_id` | 둘 다 fallback | 호환 처리 |
| HITLManager API: `create_progress(session_id, ...)`, `request_pause(session_id)` | session_id | 내부 매니저 |
| `_active_turns: set[turn_id]`, `_resume_queues: dict[turn_id]` | turn_id | A1 도입 |

특히 HITLManager 내부에서도 `_progress` 의 키는 `session_id` 라 이름붙여졌는데 `_active_turns` 의 키는 `turn_id` — 같은 dict 키 의미인데 이름이 다름.

`agent_state.py:30` 주석에:
> `session_id: str` — deprecated alias of turn_id

상태이지만 실제로는 코드 곳곳에서 **양쪽 이름 모두 사용** 중. dashboard 까지 fallback 패턴 (`||`) 으로 방어.

## Decision

### 단기 (현 상태) — 호환 fallback 유지

다음을 **계약** 으로 명시:
1. **외부 송수신 (WebSocket payload)**: 클라이언트는 `turn_id` 송신 권장. 서버는 `turn_id` → `session_id` 순으로 fallback (역호환). 신규 메시지 타입은 **반드시 `turn_id` 만** 사용
2. **AgentState 필드**: `session_id` 유지 (Sprint 12 호환), 단 docstring 에 "= turn_id alias, 신규 코드는 turn_id 사용 권장" 명시
3. **HITLManager API**: 신규 메서드는 `turn_id` 매개변수 사용. 기존 `session_id` 매개변수 메서드는 유지 (다음 cleanup sprint 까지)
4. **내부 dict 키**: 모두 동일한 turn_id 값 (이건 이미 사실). 다만 dict 변수명은 `_progress` (legacy 명명) 와 `_active_turns` 가 일관되지 않음 — 점진 정리

### 중기 (Sprint 15 cleanup sprint) — `session_id` 점진 제거

ADR-005 의 cleanup sprint 와 함께 일괄 처리:

1. **`AgentState.session_id` 필드 제거** — `state["session_id"] = state["turn_id"]` 라인이 cognitive/planning/execution_stage 에 있다면 그것도 제거
2. **HITLManager 내부 `_progress`, `_paused`, `_session_locks` 변수명 → `_progress` 유지하되 docstring 갱신** (변수명 변경은 ripple cost 큼). dict 의 키 이름은 `turn_id` 로 통일 (이미 그러함)
3. **HITLManager 메서드 매개변수**: `create_progress(session_id, ...)` → `create_progress(turn_id, ...)` rename. 호출자도 일괄 수정
4. **dashboard fallback `||` 제거**: `payload.turn_id` 만 사용
5. **`ws_hitl._check_turn_active` 의 `payload.get("session_id")` fallback 제거**

### 장기 (Sprint 16+) — 단일 명칭

`session_id` 라는 단어를 **로그·문서·코드 어디에도 안 쓰도록** 전수 정리. `turn_id` 단일.

## Consequences

### 좋은 점

- **명료성**: 같은 식별자 두 이름 → 한 이름. 신규 개발자 혼선 0
- **dashboard fallback 제거 가능**: `||` 우회 코드가 사라져 단순화
- **테스트 단순화**: payload 검증에서 한 키만 보면 됨

### 나쁜 점 / 비용

- **변경 범위 큼**: 매개변수 rename 은 file 다수에 영향. cleanup sprint 비용
- **Sprint 12 호환 깨짐**: legacy `_run_agent` 가 `session_id` 매개변수 받는데 ADR-005 cleanup 와 같이 처리되므로 자연 해소

### 위험

- **외부 클라가 `session_id` 만 보내는 경우**: 현재는 dashboard 만 클라. fallback 단계 (단기) 동안 전수 점검 후 중기 제거
- **AgentState rename 시 LangGraph state schema 변경**: pickling/checkpoint 형식 영향 가능 — 마이그레이션 검토 필요 (Sprint 15 cleanup 시 별도 ADR)

## Alternatives Considered

### Alt-1. 즉시 일괄 rename (Big-Bang)

지금 모든 곳을 `turn_id` 로 통일.

- 장점: 깔끔
- 단점: A3 마무리 단계에 위험 큰 변경. regression 폭증 가능
- **불채택**

### Alt-2. `session_id` 를 정식 이름으로 채택 (Sprint 12 명칭 유지)

`turn_id` 를 alias 로 격하.

- 장점: legacy 와 일관
- 단점: LangGraph/`thread_id` 와 의미적으로 더 가까운 건 `turn_id`. Sprint 13+ 흐름과 어긋남
- **불채택**

### Alt-3. 양쪽 모두 영구 유지

현 상태 그대로 fallback 패턴 영구.

- 장점: 변경 없음
- 단점: 본 ADR 의 존재 이유 (네이밍 혼선 해소) 미충족
- **불채택**

## Related

- **AgentState 정의**: `backend/app/dream_agent/states/agent_state.py:30`
- **HITLManager**: `backend/app/dream_agent/workflow_managers/hitl_manager/manager.py`
- **fallback 사례**:
  - `backend/api_v2/ws_hitl.py:66, 686-687, 720-721, 758-759` (`turn_id or session_id`)
  - `dashboard/index.html` (`||` fallback)
- **관련 ADR**: ADR-005 (legacy `_run_agent` cleanup 시 동시 처리)
- **WebSocket 계약**: `21_WEBSOCKET_PROTOCOL_v1.5.md` §3.1 호환 명시 절

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-27 | 초안 + Accepted. 단기 (호환 유지) / 중기 (Sprint 15 cleanup) / 장기 (Sprint 16+ 단일 명칭) 3단계 정책 명시 |
