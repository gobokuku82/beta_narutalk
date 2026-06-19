# Sequence Diagrams — 주요 시나리오

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | API 계약 (시퀀스/타이밍) |
| 진행상태 | **Active** (Sprint 14 A3 Phase 5 반영) |
| 버전 | **v1.3** |
| 최종 수정일 | 2026-04-24 |
| 관련 명세 | `13_lifecycle_v1.3.md`, `21_WEBSOCKET_PROTOCOL_v1.5.md`, `12_manager_layer_v1.4.md` |

**v1.3 (2026-04-24) 변경점** — Sprint 14 A3 Phase 5:
- §N **Plan review 편집 시퀀스** 신규 추가 (사용자 §4 "hitl=pause 같은 개념")

> 참여자 약어: **C**=Client(Dashboard), **WA**=/ws/agent, **WH**=/ws/hitl, **RT**=run_turn task, **G**=LangGraph, **HM**=hitl_manager, **CM**=callback_manager, **CN**=connection_manager

---

## 1. Happy Path — Plan 승인 → Execution → 완료

```
C   WA          RT              G               HM        CM         CN
│   │           │               │               │         │          │
│──query──▶    │               │               │         │          │
│   │──spawn──▶│               │               │         │          │
│   │           │──register────▶│               │         │          │
│   │           │──register────────────────────▶│         │          │
│   │           │──register─────────────────────────────▶│          │
│   │           │──ainvoke─────▶│               │         │          │
│   │           │               │ cognitive done │         │          │
│   │           │◀─node_event──│               │         │          │
│   │           │──fan-out──────────────────────────────────────────▶│
│◀──node_event─│               │               │         │          │
│   │           │               │ planning done  │         │          │
│   │           │               │ interrupt(plan_review)  │          │
│   │           │◀───chunk──────│               │         │          │
│   │           │──fan-out──────────────────────────────────────────▶│
│◀──hitl_request               │               │         │          │
│───approve──▶ WH              │               │         │          │
│   │         │───signal_resume(turn_id, approve)────▶│         │          │
│   │           │◀──Queue.get──────────────────│         │          │
│   │           │──ainvoke(Command(resume))───▶│         │          │
│   │           │               │ execution phase 1      │          │
│   │           │               │               │         │──progress─▶ bridge
│   │           │◀────────(todo_start/complete/progress via CM bridge)─────────│
│◀──todo_*─────│               │               │         │          │
│   │           │               │ response done  │         │          │
│   │           │◀─node_event──│               │         │          │
│   │           │──fan-out──────────────────────────────────────────▶│
│◀──complete──│               │               │         │          │
│   │           │──unregister──▶│──release slot                          │
```

**핵심 포인트**:
- `run_turn`은 WS 핸들러가 spawn하는 task — WS 메시지 루프와 독립
- interrupt 시 state는 Checkpointer에 저장되므로 서버 재시작 OK
- CM(callback_manager) bridge는 execution_stage의 내부 emit을 conn_manager fan-out으로 변환 (Sprint 13 I11-b2)

---

## 2. Plan Reject

```
... (Planning interrupt까지 동일) ...
│◀──hitl_request(plan_review)
│───reject────▶ WH
│          │───signal_resume(turn_id, {action: reject})──▶ HM
│   │           │◀──Queue.get──────────────────│
│   │           │──ainvoke(Command(resume={action:reject}))──▶ G
│   │           │               │ planning_stage: action=="reject"
│   │           │               │   update(response={text:"계획 거부..."})
│   │           │               │   goto=END
│   │           │◀─chunks(silent drain)
│   │           │──fan-out──complete(status=rejected)───────▶ CN ───▶ C
│   │           │──cleanup (unregister, release)
```

**포인트**: reject는 run_turn이 silent drain(이벤트 무시)한 뒤 `complete(status=rejected)`만 발신.

---

## 3. Execution Pause / Resume

```
... (Plan approve 후 execution 진행 중) ...
│───pause────▶ WH
│          │─── hitl.request_pause(turn_id)──▶ HM
│          │       (HM._paused에 turn_id 추가, progress.status=paused)
│          │───hitl_ack──▶ C
│   │           │              (Phase A 계속 실행 중)
│   │           │               │ Phase A 완료
│   │           │               │ should_continue → "pause"
│   │           │               │ interrupt(execution_pause, progress)
│   │           │◀──chunk──────│
│   │           │──fan-out──paused (execution_pause interrupt)──────▶ CN ──▶ C
│◀──paused────│
│───resume───▶ WH
│          │───hitl.request_resume(turn_id)──▶ HM (HM._paused 제거)
│          │───hitl.signal_resume(turn_id, {action: continue})──▶ HM
│   │           │◀──Queue.get──────────────────│
│   │           │──ainvoke(Command(resume={continue}))──▶ G
│   │           │               │ execution while 재진입
│   │           │               │ remaining_phases 재조회 → Phase B
│   │           │               │ ...
```

**포인트**: 
- Pause 요청 순간은 HM flag만 세팅, 실제 interrupt는 **phase 경계**에서 발생
- Pause 중에도 이전 phase의 완료 이벤트는 계속 emit될 수 있음
- Resume은 2단계: `request_resume` (flag 해제) + `signal_resume` (Queue signal)

### 3.1 payload 상세

| 이벤트 | from | to | 필드 |
|--------|------|----|------|
| `pause` | C | WH | `{type:"pause", data:{turn_id}}` |
| `hitl_ack` | WH | C | `{type:"hitl_ack", data:{action:"pause", session_id, accepted:true}}` |
| `paused` | RT | C (fan-out) | `{type:"paused", conversation_id, turn_id, data:{request_id, completed, total, current_phase, progress, turn_id, conversation_id}}` — `_build_paused_data` 산출. `reason` 필드 **없음** (검증 사이클 2 정정) |
| `resume` | C | WH | `{type:"resume", data:{turn_id}}` |

---

## 4. Server Restart Recovery (resume_query 경로)

```
(시점 T0 — pause 상태, Checkpoint 저장됨)
C ──query 전송 시점에 LS.set("last_turn_id", turn_id)
<서버 재시작>
(시점 T1 — 브라우저는 ws.onclose 수신, agentRunning=false 로 내리고 UI 리셋)
C ──(3s 후 자동 재연결)──▶ WA
WA──"connected" ──▶ C
C ──[onopen] LS.get("last_turn_id") 존재 확인──▶
C ───{"type":"resume_query","conversation_id":"...","turn_id":"..."}──▶ WA
WA──asyncio.create_task(run_turn(payload={"resume_only": True}))──▶ RT
RT──concurrency.try_acquire (멱등)──OK
RT──cb_manager.unregister → register (중복 누적 방지)
RT──_graph_runner_with_resume (resume_only=True)
   ├ 초기 astream SKIP (중요!)
   └ resume loop 진입
RT──agent.aget_state(config)──▶ G (Checkpointer에서 state 로드)
G──tasks[].interrupts[0].value = {type: "execution_pause", progress}──▶ RT
RT──_extract_interrupt_value──▶ intr_value
RT──[execution_pause 분기] 싱글톤에 progress 없으면 hitl.restore_progress()
RT──fan-out──{"type":"paused", data:{...}}──▶ CN ──▶ C
C ──버튼 "▶ 재개"로 복원──▶
C ───resume──▶ WH (이전 pause/resume 흐름과 동일)
WH──hitl.signal_resume(turn_id, {action:"continue"})──▶ HM
RT──wait_for_resume 에서 signal 수신──
RT──agent.astream(LGCommand(resume={continue}))──▶ 다음 phase 진행
```

**포인트**:
- `thread_id = f"{conv}_{turn}"`가 복원 키
- 대시보드가 **`resume_query` 를 명시적으로 발사** — 자동 recovery trigger
- 브라우저 onopen 에서 `last_turn_id` 있으면 무조건 resume_query 전송. `agentRunning` 조건 X (onclose 에서 이미 false)
- `resume_only=True` → 초기 astream skip. 같은 state로 다시 그래프 실행 안 함
- first_iter 플래그로 "pending 없음" 검사는 첫 이터레이션에서만 (정상 종료 시 false-positive error 방지)
- `hitl_manager` 싱글톤 — 서버 재시작 시 `_paused`/`_progress` 메모리 소실 → **Checkpoint의 interrupt payload가 진실 소스**
- `restore_progress` (I11-a) 포팅: Checkpoint progress snapshot을 `hitl.create_progress` 없이 직접 복원
- `cb_manager.register` 중복 누적 방지 (RO-11 리스크 대응)

**resume_query 실패 시**:
- pending interrupt 없음 (stale turn_id / 이미 complete) → `INVALID_MESSAGE` fatal emit → 대시보드 handleError → resetSendButton → idle 복귀
- conv_id / turn_id 누락 → `INVALID_MESSAGE` fatal direct-WS

---

## 5. Concurrent Limit Exceeded

```
C(탭A) ──query(turn_1)──▶ WA ──acquire slot 1──▶ Concurrency OK, run_turn 시작
C(탭B) ──query(turn_2)──▶ WA ──acquire slot 2──▶ OK
C(탭C) ──query(turn_3)──▶ WA ──acquire slot 3──▶ OK
C(탭D) ──query(turn_4)──▶ WA ──try_acquire 실패 (MAX=3)
                             │
                             └──fan-out CONCURRENT_LIMIT_EXCEEDED error──▶ 모든 탭
                                (conversation_id, turn_id=turn_4)
```

**포인트**:
- fan-out이므로 **해당 쿼리 보낸 탭만이 아니라 같은 user 전체 탭**이 error 수신
- 다른 탭은 conversation_id로 자기 conv면 알림, 아니면 무시 (대시보드 로직)

---

## 6. Layer Guard Fatal (aborted)

```
... (cognitive 완료, structured_query 비어있음) ...
RT──_broadcast_chunks──inspect_layer_output(cognitive, data)──▶ [COGNITIVE_EMPTY_QUERY]
RT──fan-out──error(severity=fatal, layer=cognitive)────────────▶ C
RT──append_guard_log──▶ logs/layer_guard.jsonl
RT──fan-out──complete(status=aborted, reason="COGNITIVE_EMPTY_QUERY")──▶ C
RT──cleanup
```

**포인트**: fatal error는 항상 **error + complete(aborted)** 쌍으로 emit. warning은 `guard_warnings`에 누적 후 최종 complete에 포함.

---

## 5a. HITL Timeout — plan_review 대기 (Sprint 14 A1, FR-13a / G-11)

```
C                  WA                RT                HM                G
│                   │                 │                 │                 │
├─ query ───────────▶                 │                 │                 │
│                   │─ run_turn ─────▶│                 │                 │
│                   │                 │─ register_turn ─▶ HM              │
│                   │                 │                                   │
│                   │                 │─ astream(state) ──────────────────▶
│                   │                 │◀── interrupt(plan_review) ────────┤
│                   │◀─ hitl_request ─┤                                   │
│◀─── hitl_request ─┤                                                     │
│                                                                         │
│   [30분 경과 — 사용자 무응답]                                              │
│                                                                         │
│                   │                 │─ wait_for_resume(timeout) ──────▶ HM
│                   │                 │◀── {"action":"timeout"} ─────────┤
│                                                                         │
│                   │                 │─ logger.warning("hitl timeout aborted turn")
│                   │                 │                                   │
│                   │                 │─ astream(Cmd(resume={action:reject})) ──▶
│                   │                 │    (planning_stage → goto END)    │
│                   │                 │◀── (silent drain) ────────────────┤
│                   │◀─ complete(aborted, reason=hitl_timeout)            │
│◀─── complete ─────┤                                                     │
│                                                                         │
│                   │                 │─ finally: concurrency.release + cleanup_turn
│                   │                 │   (_active_turns + _paused + _resume_queues 정리)
```

**핵심 포인트**:
- `plan_review` 인터럽트 → `wait_for_resume(timeout=1800s)` 대기
- timeout 시 `LGCommand(resume={"action":"reject"})` 주입 → planning_stage 가 `goto=END`
- `{"action":"cancel"}` 주입 금지 — planning_stage 가 cancel 미처리, fallthrough 로 execution 진입 (G-11)

---

## 5b. HITL Timeout — execution_pause 대기

```
(5a 와 거의 동일. 차이점만 표기)

│                   │                 │◀── interrupt(execution_pause) ────┤
│                   │◀─── paused ─────┤
│                                                                         │
│   [30분 경과]                                                             │
│                                                                         │
│                   │                 │◀── {"action":"timeout"} ─────────┤
│                   │                 │─ astream(Cmd(resume={action:cancel})) ──▶
│                   │                 │    (execution_stage → goto END)   │
│                   │◀─ complete(aborted, reason=hitl_timeout)            │
```

**핵심 포인트**:
- `execution_pause` 인터럽트 → 주입값 `"cancel"` (execution_stage 가 cancel 로 END)
- `"reject"` 금지 — execution_stage 는 reject 미처리

---

## 5c. Timeout 이후 뒤늦은 HITL 요청 (FR-13b, UX-5)

```
  (상기 5a 완료 후, _active_turns 에서 turn_A 제거됨)

C ──resume msg (turn_A)──▶ WH
             │
             │─ hitl.is_turn_active(turn_A) → False ──┐
             │                                        │
             │◀── (가드 통과 못 함)                     │
             │                                        │
             │─ hitl_ack {accepted:false, reason:"turn_not_active"} ──▶ C
             │                                                          │
                                                    대시보드 토스트 + idle 복귀
```

**핵심 포인트**: `_active_turns` 는 run_turn 수명주기만 추적. timeout/종료 후 자동 제거.
pause/resume/cancel 3개 핸들러 모두 동일 가드. 3번째 인자 `action` 으로 로그 구분.

---

## 7. Multi-Tab Fan-out

```
C(탭A, conv=c1) ──query──▶ WA ──run_turn(turn_1 on c1)──▶
C(탭B, conv=c2, 같은 user=demo) ──query──▶ WA ──run_turn(turn_2 on c2)──▶

RT(turn_1) ──broadcast_to_user(demo, event{conv:c1})──▶ CN ──▶ 탭A, 탭B
RT(turn_2) ──broadcast_to_user(demo, event{conv:c2})──▶ CN ──▶ 탭A, 탭B

탭A: conv_id=c1 매치 → render. conv_id=c2 → console.log, 무시
탭B: 반대
```

**포인트**: user 단위 fan-out은 서버 단순성 우선. 클라이언트가 conv_id로 필터링. Sprint 17+ 에서 conversation 단위 라우팅 검토.

---

## 8. Plan Review 편집 (Sprint 14 A3 Phase 5 신규)

사용자 §4 "hitl=pause 같은 개념" 반영. Plan review 에서 execution_pause 와 동일한 편집 경로.

```
C   WA                     RT                G             HM                         TM
│   │                      │                 │             │                           │
│──query─▶                 │                 │             │                           │
│   │──spawn──────────────▶│                 │             │                           │
│   │                      │──astream───────▶│             │                           │
│   │                      │◀─node(cognitive)│             │                           │
│   │                      │◀─node(planning) │             │                           │
│   │                      │                 │──interrupt──▶ [plan_review]              │
│   │                      │◀─pending intr──│             │                           │
│   │                      │                 │             │                           │
│   │                      │──create_progress(plan)───────▶│                           │
│   │                      │                 │             │ (status="paused" 덮어쓰기) │
│   │                      │──broadcast hitl_request────────────────────────────────▶  │
│◀──hitl_request───────────│                 │             │                           │
│   │                      │──wait_for_resume─────────────▶│                           │
│                          │                 │             │                           │
│ [사용자 🗑 클릭]           │                 │             │                           │
│─todo_delete──▶ WH        │                 │             │                           │
│               │          │                 │             │                           │
│               │──_get_lock────────────────────────────────▶│                          │
│               │──handle_todo_delete─────────────────────▶│──calculate_cascade───────▶│
│               │                                          │ progress.plan mutate      │
│               │                                          │ phases rebuild            │
│◀─hitl_ack(invalidated=[t2,t3], plan=...)                │                           │
│                                                          │                           │
│ [사용자 ✅ 승인]                                          │                           │
│─hitl_response(approve)──▶ WH                             │                           │
│               │──get_progress─────────────────────────▶ │                           │
│               │               (progress 존재)           │                           │
│               │──request_resume───────────────────────▶│ (status="running")          │
│               │──signal_resume({action:"modify",        │                           │
│               │                  value:progress.plan})▶ │                           │
│◀─hitl_ack(approve)                                       │                           │
│                          │◀─wake wait_for_resume────────│                           │
│                          │──Command(resume={modify,val})▶│                           │
│                          │                 │ [planning_stage L88-92]                │
│                          │                 │ plan_dict = value                       │
│                          │                 │──goto execution──▶                     │
│                          │                 │ (edited plan 실행)                      │
│                          │◀─node(execution)│             │                           │
│                          │                 │◀─complete(success)                     │
│◀──complete──────────────│                 │             │                           │
│                          │──cleanup_turn──────────────▶│ _progress.pop               │
```

**핵심 차이점 (vs §3 Execution Pause)**:
- `_progress` 가 **execution_stage 가 아닌 `_graph_runner_with_resume` 의 plan_review 분기에서 생성됨** (status="paused" 직접 세팅)
- 승인 시 `approve` 가 서버 내부에서 `modify + value=progress.plan` 으로 변환 (클라는 여전히 `approve` 전송)
- cascade 의 `completed_todos` 가 비어있어 `preserved={}` 이지만 `invalidated` 는 정상적으로 downstream 을 포함

---

## 변경 이력

> 프레임워크 추출(2026-06-19) 이전(마케팅 도메인 시기)의 상세 변경 이력은 git 히스토리를 참조하세요.
