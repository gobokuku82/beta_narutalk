# Turn Lifecycle & State Machine

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 아키텍처 (Lifecycle / State Machine) |
| 진행상태 | **Active** (Sprint 13) |
| 버전 | **v1.3** |
| 최종 수정일 | 2026-04-27 |
| **진실 소스** | WS 라우팅: `backend/api/ws_agent.py` (`run_turn`, `_graph_runner_with_resume`). 실행 제어: `backend/app/dream_agent/execution/execution_stage.py` (phase 루프). HITL 신호: `workflow_managers/hitl_manager/manager.py` (Queue 기반 interrupt + `_active_turns` 레지스트리 + Phase 5 임시 progress) |
| 관련 명세 | `10_system_architecture_v1.9.md`, `24_sequence_diagrams_v1.3.md`, `21_WEBSOCKET_PROTOCOL_v1.5.md`, `12_manager_layer_v1.4.md` |

**v1.3 (2026-04-27) 변경점** — Sprint 14 A3 Phase 5:
- 관련 명세 링크 갱신 (10 v1.9 / 24 v1.3 / 21 v1.4 / 12 v1.3)
- 본문 변경 없음 (`_progress` 수명주기 확장은 12_manager v1.3 참조)
- Phase 5 의 plan_review 임시 progress 도입은 Turn 상태머신 자체엔 영향 없음 (`pause` 가 plan_review 시점에도 의미 있게 됨)

> "타이밍이 주먹구구"를 없애기 위한 문서. 
> 각 transition의 **트리거 / 감지 지점 / 지연 특성**을 명확히.

---

## 1. Turn 상태 머신

```
                       ┌─────── reject ────────┐
                       │                       ▼
idle ──query──▶ cognitive ──▶ planning ──hitl_request──▶ waiting_approval
                                  │                         │
                               (skip)                 approve / modify
                                  │                         │
                                  ▼                         ▼
                               response ◀── cancel ── execution
                                  │                         │
                                  │                    pause 요청
                                  │                         │
                                  │                         ▼
                                  │                      paused ──resume──▶ execution
                                  │                         │                (같은 phase)
                                  │                      cancel
                                  │                         ▼
                                  ▼                        end (cancelled)
                                 end (success)
```

### 상태 정의

| 상태 | 의미 | emit 이벤트 |
|------|------|-------------|
| `idle` | Turn 미시작 | — |
| `cognitive` | 의도 분석 중 | `node_event(node=cognitive)` |
| `planning` | 계획 생성 중 (LLM) | `node_event(node=planning)` |
| `waiting_approval` | Plan 승인 interrupt 대기 | `hitl_request(type=plan_review)` |
| `execution` | Todo 실행 중 | `node_event(node=execution)`, `layer_start`, `todo_start`, `todo_complete`, `progress` |
| `paused` | Execution pause interrupt 대기 | `paused`, `hitl_request(type=execution_pause)` |
| `response` | 최종 응답 생성 중 | `node_event(node=response)` |
| `end (success)` | 정상 완료 | `complete(status=success)` |
| `end (rejected)` | Plan 거부로 조기 종료 | `complete(status=rejected)` |
| `end (cancelled)` | 사용자 cancel | `complete(status=cancelled)` |
| `end (aborted)` | Layer guard fatal | `complete(status=aborted)` + `error(severity=fatal)` |

---

## 2. Interrupt / Resume 메커니즘

### 2.1 Interrupt 발생 지점 (2개)

| 위치 | 트리거 | payload |
|------|--------|---------|
| `planning_stage.py:L72` | Planner 완료 직후 무조건 | `{type: "plan_review", plan, message}` |
| `execution_stage.py:L194` | **phase 경계**에서 `hitl.should_continue()` == "pause" | `{type: "execution_pause", progress}` |

### 2.2 Interrupt 처리 (2-step 비동기)

`interrupt()`는 LangGraph 원시:
1. 현재 state를 Checkpointer(PostgreSQL)에 저장
2. astream 중단 → `_graph_runner_with_resume`의 `_broadcast_chunks` 복귀
3. `hitl_request` 또는 `paused` 이벤트 fan-out
4. `hitl.wait_for_resume(turn_id)` — **asyncio.Queue**에서 signal 대기 (I7)
5. `/ws/hitl`에서 approve/reject/cancel → `hitl.signal_resume(turn_id, {action})`
6. `_graph_runner_with_resume` while 루프 재진입 → `agent.ainvoke(Command(resume=...))`

### 2.3 Resume signal 채널

- `hitl_manager` 내 `_resume_queues: dict[turn_id, asyncio.Queue]`
- Queue는 **Turn 단위**로 dynamic 생성 (`register_resume_channel`)
- Cleanup은 `run_turn` finally에서 `unregister_resume_channel`

---

## 3. Pause 타이밍 (중요)

### 3.1 Pause 감지는 "phase 경계"에서만

`execution_stage.py` while 루프:
```
for phase in remaining_phases:
    decision = hitl.should_continue(session_id)  # ← 감지 지점
    if decision["action"] == "pause":
        interrupt(...)                            # ← Checkpoint + astream 중단
    ...
    await execute_phase(...)                      # phase 실행 (병렬 Todo)
```

즉:
- Phase A 실행 중에 사용자가 pause 버튼 → **Phase A가 끝나야 pause interrupt 발생**
- Phase 내부 Todo가 오래 걸리면 pause 응답 지연
- 단일 phase(Todo 1개)로만 구성된 Plan은 pause가 의미 없음 (phase 경계 없음)

### 3.2 Pause 상태 흐름

| 순간 | `hitl._paused` | `progress.status` | execution_stage |
|------|---------------|-------------------|-----------------|
| 사용자 pause 클릭 | 추가됨 | `paused` | Phase A 실행 중 |
| Phase A 완료 | 추가된 상태 | `paused` | should_continue 확인 → interrupt |
| `hitl_request(execution_pause)` emit | 추가된 상태 | `paused` | astream 중단 |
| 사용자 resume | 제거됨 | `running` | Queue signal 대기 |
| Queue signal 수신 | 제거됨 | `running` | 루프 재진입, 다음 phase |

### 3.3 Sprint 14 A1 — HITL 응답 타임아웃 (구현 완료 2026-04-22)

**동작**:
- `_graph_runner_with_resume` 가 `wait_for_resume(turn_id, timeout=settings.HITL_RESUME_TIMEOUT_SEC)` 호출
- 기본 30분 (`.env HITL_RESUME_TIMEOUT_SEC` override)
- timeout 초과 시 `{"action":"timeout"}` 반환

**timeout 분기** (interrupt 타입별, G-11):
- `plan_review` 대기 중 timeout → `LGCommand(resume={"action":"reject"})` 주입 → planning_stage 가 END
- `execution_pause` 대기 중 timeout → `LGCommand(resume={"action":"cancel"})` 주입 → execution_stage 가 END
- 이후 `complete(status="aborted", reason="hitl_timeout")` emit

**상태 흐름**:
```
(pause|plan_review 대기)
    │ wait_for_resume timeout
    ▼
timeout 분기 (intr_type 별 주입)
    │ silent astream drain
    ▼
complete(aborted, hitl_timeout)
    │ run_turn finally
    ▼
concurrency.release + cleanup_turn (_active_turns + _paused + _resume_queues 정리)
```

**활성 turn 레지스트리** (`HITLManager._active_turns`):
- `run_turn` try 블록 첫 줄 `register_turn(turn_id)` — 활성 표시
- `finally` 에서 `cleanup_turn(turn_id)` — 해제 (3 구조 동시)
- `ws_hitl` 3 핸들러(pause/resume/cancel) 앞단 `is_turn_active` 가드 — timeout 된 turn 에 대한 요청 거부: `{accepted:False, reason:"turn_not_active"}`

**시나리오**:
- **T-1** (timeout 후 복귀 — 신규 쿼리로 재시작): 안전 장치 역할. 재개 UI 는 Sprint 15 Memory 범위
- **T-2** (늦은 resume 클릭): 서버 `turn_not_active` ack + 대시보드 토스트 + idle 복귀
- **T-3** (timeout↔resume race): 30분 말미 μs 단위 race, 2택 결과 허용. 그룹 F 테스트 100회 결정성 확인

### 3.4 Sprint 14 A2 범위 (예정)

- 현재 phase 내 Todo 완료 후 stop 시그널 (phase 중간 중단은 out of scope)

---

## 4. 동시성 제어

### 4.1 ConcurrencyManager

`workflow_managers/concurrency_manager.py`:
- `try_acquire(user_id, turn_id)` — user당 MAX_CONCURRENT_TURNS_PER_USER (=3) slot
- 실패 시 `CONCURRENT_LIMIT_EXCEEDED` error
- `release(user_id, turn_id)` — `run_turn` finally

### 4.2 ConnectionManager

`backend/api/connection_manager.py`:
- user당 MAX_WS_CONNECTIONS_PER_USER (=5) 탭 허용
- `broadcast_to_user(user_id, event)` — fan-out (같은 user 모든 탭)
- 이벤트에 `conversation_id/turn_id` 포함 → 다른 conv_id 이벤트는 클라 무시

---

## 5. Checkpoint 복원

- `thread_id = f"{conversation_id}_{turn_id}"`
- 서버 재시작 → 새 WS 연결 → 대시보드가 localStorage의 `last_turn_id`를 보고 `resume_query` 메시지 전송
- 백엔드는 `run_turn(payload={"resume_only": True})` 재스폰 → `_graph_runner_with_resume` 가 **초기 astream skip** → 바로 resume 루프 진입
- `_has_pending_interrupts(gs)` 확인 → pending 있으면 기존 interrupt payload 재emit → 사용자 재승인 → resume
- pending 없으면 `INVALID_MESSAGE` fatal emit (stale turn_id 방어)

**resume_query 메시지 포맷** (`/ws/agent`):
```json
{ "type": "resume_query", "conversation_id": "conv_...", "turn_id": "turn_..." }
```

**대시보드 동작**:
- 쿼리 전송 시 `LS.set("last_turn_id", turn_id)` 저장
- `complete` 이벤트 수신 시 `LS.remove("last_turn_id")` 정리
- `ws.onclose` 에서 `agentRunning=false`, `setButtonState("idle")` (단 `last_turn_id`는 보존)
- `ws.onopen` 에서 `last_turn_id` 있으면 `resume_query` 자동 전송

**중복 register 방지** (callback_manager):
- `_graph_runner_with_resume` 진입 시 `cb_manager.unregister(turn_id)` + `register(...)` 패턴. resume_query 여러 번 시 이벤트 중복 fan-out 방지.

상세 시퀀스: `24_sequence_diagrams_v1.3.md` §4 Server Restart Recovery

---

## 6. Turn 종료 경로 (cleanup 순서)

`run_turn` finally 블록에서 순서대로:
1. `callback_manager.unregister(turn_id)` — bridge 해제
2. `hitl_manager.unregister_resume_channel(turn_id)` — Queue 제거
3. `concurrency_manager.release(user_id, turn_id)` — slot 반납

`_graph_runner_with_resume` 내 예외는 상위에서 캐치 → `EXECUTION_ERROR` fan-out + cleanup.

---

## 7. 알려진 타이밍 한계

| 한계 | 원인 | 영향 | 계획 |
|------|------|------|------|
| Pause 지연 (phase 내) | `should_continue`가 phase 경계에서만 호출 | UX — 최대 phase 실행 시간만큼 지연 | Sprint 14 A2 |
| Resume Queue 무한 대기 | 탭 닫고 안 오면 run_turn task 영원히 대기 | MAX_CONCURRENT=3에서 slot 누수 | Sprint 14 A1 (timeout) |
| Checkpoint 동시 접근 | 같은 thread_id 두 run_turn 동시 실행 | LangGraph 내부 lock에 의존 | 현재 fan-out + 싱글 task로 회피 |
| callback_manager 다중 turn | register(turn_id) 키 충돌 | 없음 (turn_id 고유) | — |

---

## 변경 이력

> 프레임워크 추출(2026-06-19) 이전(마케팅 도메인 시기)의 상세 변경 이력은 git 히스토리를 참조하세요.
