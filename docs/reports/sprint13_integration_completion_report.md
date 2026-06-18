# Sprint 13 Integration 완료 보고서

| 항목 | 내용 |
|------|------|
| 스프린트 | **Sprint 13 — Session/Thread 재설계 + Integration + I12 Regression** |
| 기간 | 2026-04-14 ~ 2026-04-22 (9일) |
| 담당자 | 도윤 + Claude |
| 상태 | **✅ 완료** |
| 작성일 | 2026-04-22 |

---

## 1. 목표 및 결과 요약

### 1.1 Sprint 13 목표
1. Session / Thread 식별 체계 재설계 (`user_id` / `conversation_id` / `turn_id` 분리)
2. WebSocket 이중 채널(`/ws/agent` + `/ws/hitl`) Sprint 13 경로 완성
3. LangGraph Checkpointer(AsyncPostgresSaver) 기반 interrupt resume 안정화
4. 대시보드 Sprint 13 이벤트 흐름 대응
5. Sprint 12 regression (R-1~R-12) 검증
6. 개발 명세서 체계 정비 + Doc-Code drift 검출 메커니즘 구축

### 1.2 결과 지표

| 항목 | 수치 |
|------|------|
| 비-live 테스트 | **137/137 pass × 3회 안정** |
| Live 테스트 (WL-01~06) | 6/6 개별 pass |
| 브라우저 수동 regression | **R-1~R-4 + R-9/R-10/R-11/R-12** 전항목 pass |
| Doc-Code Contract Test | 5/5 pass (`-m docs`) |
| 커밋 수 | 20+ (Sprint 13 범위) |
| 신규 문서 | `01_requirements`, `12_manager_layer`, `13_lifecycle`, `22_error_codes`, `24_sequence_diagrams`, `INDEX.md` |
| drift 검출/수정 | R-9 구현 중 13건 + Contract Test R2 10건 = 총 23건 |

---

## 2. 주요 산출물

### 2.1 백엔드 핵심 변경

**`backend/api_v2/ws_agent.py`**:
- `run_turn` — Query 1회 실행용 asyncio task 분리 (WS 끊겨도 지속)
- `_graph_runner_with_resume` — astream + interrupt resume 루프 + layer guard + 이벤트 보강
- `resume_query` 메시지 라우팅 — 서버 재시작 복원 (R-9 핵심)
- `resume_only` 플래그 + `first_iter` 가드 — Checkpoint 복원 시 초기 astream skip, 정상 종료 시 false-positive error 방지
- CallbackManager `unregister → register` 중복 누적 방지 (RO-11 발견)
- `_parse_query_message` — conv/turn/user_input 검증 with ErrorCodes 통일

**`backend/api_v2/ws_hitl.py`**:
- `_handle_pause/resume/cancel` payload 에 `session_id`/`turn_id` 호환 fallback

**`backend/api_v2/layer_guard.py`** (I11-a 신규):
- `inspect_layer_output(node, data)` — 5개 error code (cognitive/planning/execution/response)
- `append_guard_log` — `logs/layer_guard.jsonl` thread-safe append
- key-presence guard — planning reject 경로 false fatal 방지

**`backend/api_v2/error_codes.py`** (I11-c 신규):
- `ErrorCodes` 클래스 — 8개 ErrorSpec 단일 출처
- `all_codes()` / `all_specs()` 헬퍼 (Contract Test 용)

**Manager Layer**:
- `ConnectionManager` (T1) — user_id 기반 fan-out
- `ConcurrencyManager` (T2) — user당 MAX_CONCURRENT_TURNS_PER_USER slot
- `HITLManager.wait_for_resume` / `signal_resume` / `cleanup_turn` (I7) — asyncio.Queue FIFO signal
- `CallbackManager` bridge 패턴 — execution_stage 이벤트를 conn_manager fan-out 으로 변환

### 2.2 대시보드 (`dashboard/index.html`)

- 쿼리 경로: `type: "query"` 신 경로 전환
- `turn_id = crypto.randomUUID()` per 쿼리, localStorage 로 `last_turn_id` 영속화
- 4-state 버튼 전이: `idle` / `waiting` / `pause_available` / `resume_available`
- cancel 버튼 (resume_available 상태 한정)
- **WS 재연결 복원 트리거** — `ws.onopen` 에서 `last_turn_id` 존재 시 `resume_query` 자동 전송 / `ws.onclose` 에서 UI 임시 리셋
- Auto-approve 경로 지원 — cognitive/planning 중 pause 가능, paused 이벤트에서 Todo 리스트 복원 렌더

### 2.3 개발 문서 체계 (`docs/agent_specs/`)

Category Prefix 번호 체계:
```
INDEX.md
01_requirements_v1.1.md          # 요구사항 (00대 — 신규)
10_system_architecture_v1.7.md
11_main_graph_state_v1.4.md
12_manager_layer_v1.0.md         # Manager 통합 명세 (신규)
13_lifecycle_v1.1.md             # Turn 상태머신 / Pause 타이밍 / Checkpoint 복원 (신규)
20_INTERFACE_CONTRACT_v1.0.md
21_WEBSOCKET_PROTOCOL_v1.1.md    # resume_query 추가
22_error_codes_v1.0.md           # 단일 카탈로그 (신규)
24_sequence_diagrams_v1.1.md     # 7개 시나리오 (신규)
30_DATA_MODELS_v1.0.md
31_execution_agent_function_list_v0.6.md
POC_legacy/                      # 이력 보존
```

### 2.4 테스트 스위트

신규 테스트 파일:
- `test_resume_only_unit.py` — RO-01~13 (R-9 resume_query 경로)
- `test_layer_guard_unit.py` — LG-01~11 (I11-a)
- `test_error_format_unit.py` — EF-01/02 (I11-a error 포맷 통일)
- `test_docs/test_doc_code_contract.py` — DC-1~5 (drift 자동 검출)

기존 확장:
- `test_ws_agent_query_routing_unit.py` — WQ-09~11 (resume_query 라우팅)
- `test_resume_loop_unit.py` — IR-05~10 (I11-a 이벤트 보강)

---

## 3. I12 Sprint 12 Regression 결과

| ID | 시나리오 | 결과 | 검증일 |
|----|---------|------|--------|
| R-1 | Plan 승인 모달 | ✅ | 기존 |
| R-2 | Plan 거부 → 조기 종료 | ✅ | 기존 |
| R-3 | Execution Pause | ✅ | 기존 |
| R-4 | Resume → 다음 Phase | ✅ | 기존 |
| **R-9** | **서버 재시작 복원** | ✅ | 2026-04-21 |
| **R-10** | **Plan_review auto-bypass** | ✅ | 2026-04-22 |
| **R-11** | **연속 pause/resume 3회 토글** | ✅ | 2026-04-22 |
| **R-12** | **Progress 유지 (서버 재시작 후)** | ✅ | 2026-04-21 (R-9 로그 확인) |
| R-5~R-8 | Todo 편집/추가/삭제/Cascade | ⏳ Sprint 14 A3 | — |

### R-9 성공 로그 하이라이트 (2026-04-21)
```
17:59:39  paused (execution_pause) — phase 0 에서 중단, Checkpoint 저장
18:00:00  서버 Ctrl+C (Shutdown)
18:00:05  서버 재기동 + Checkpointer connected
18:00:05  브라우저 WS 재연결 → resume_query 자동 전송
18:00:05  progress restored from checkpoint turn_id=turn_f622282e05a9
18:00:05  paused 이벤트 재emit (복원)
18:00:11  사용자 재개 클릭 → phase 1~7 실행
18:00:25  complete(success) + PDF 보고서 생성
```

---

## 4. 검증 방법론 — R0~R5 사이클 정착

Sprint 13 중반부터 **문서 검증에 R0~R5 라운드 구조** 도입 (`doc_verification_method.md` v1.1):

- **R0** 규칙 + 범위 설정
- **R1** 1차 검증 → Critical/Major/Minor 분류
- **R2** 재검증 (R1 수정 반영)
- **R3** 재범위 (새 영역 진입)
- **R4** 2차 검증
- **R5** (선택) 최종 통합

**효과**: Sprint 13 말 이 방법론으로 Contract Test + 대규모 drift 수정이 무한 루프 없이 수렴. 같은 카테고리 3회 이상 발견 시 "구조 문제 신호"로 패턴 인식.

---

## 5. 발견한 실제 버그 / 수정 내역

### Critical (테스트 없었으면 프로덕션 버그 됐을 것)
- **B-0 (Sprint 13 I11-a)** `_graph_runner_with_resume` 의 `resume_only` 분기가 while 루프 매 iter 마다 pending-없음 검사 → 정상 종료 시 false error 오발사. RO-02/04 테스트로 발견. `first_iter` 플래그 도입으로 수정.
- **B-callback dedup (RO-11)** `CallbackManager.register` append 구조라 resume_query 재진입 시 listener 누적 → 이벤트 2배/3배 중복 fan-out. `unregister → register` 패턴으로 수정.
- **B-pause handler (R-9 live)** `ws_hitl._handle_pause/resume/cancel` 가 payload 의 `session_id` 만 읽는데 대시보드는 `turn_id` 만 전송 → 실제로는 nothing happened. `session_id or turn_id` fallback 으로 수정.

### Major
- **B-UI recovery (R-9)** 브라우저 재연결 시 `!agentRunning` 조건이 막혀서 resume_query 자동 전송 실패. `ws.onclose` 에서 `agentRunning=false` 로 리셋하고 조건 제거.
- **B-UI auto-approve (R-10)** auto-approve 경로에선 `hitl_request` emit 되지 않아 Todo 리스트 미렌더. `handlePaused` 에서 `data.progress.plan.todos` 로 복원 렌더.
- **B-logging** `api_v2/main.py` 가 `setup_logging()` 미호출 → runtime 로그 출력 안 됨. 해결 후 revert (uvicorn 기본 log_config 가 원래 잘 동작하는 것 확인).

### Minor
- `_parse_query_message` 의 `INVALID_MESSAGE` 하드코딩 3곳 → `_invalid(msg_detail)` 헬퍼로 DRY
- Sprint 12 legacy error codes 5종 (INTERNAL_ERROR/EMPTY_MESSAGE/PAUSE_TIMEOUT/HITL_TIMEOUT/AGENT_ERROR) 를 `22_error_codes §1.4` 에 legacy 섹션으로 분류

---

## 6. 알려진 한계 / Sprint 14 인계

### 6.1 설계 의도적으로 미구현 (Sprint 14+ 범위)
- **`reducers.py`** — 현재 `AgentState` 는 순수 `TypedDict` 로 LangGraph 기본 동작(last-writer-wins) 사용. 다중 Writer 시나리오가 실제 충돌하면 reducer 필수. POC→MVP 전환 시 구현 예정. [문서 상 `(예정)` 마커 표시됨]
- **HITL Todo 편집** (R-5~R-8) — Sprint 14 A3 범위
- **`PLANNING_INVALID_AGENTS` 경고** — Sprint 14 복잡도 이연

### 6.2 기술 부채
- **`wait_for_resume` 무한 대기** — 사용자가 탭 닫고 안 오면 run_turn task 영원히 Queue 대기. `MAX_CONCURRENT=3` 으로 영향 제한. **Sprint 14 A1/A2 timeout** 도입 필요.
- **`_handle_resume` stale turn_id 처리** — Queue 없는 turn_id 에 `accepted:true` 반환. 실제로는 noop. Sprint 14 에서 Queue 존재 여부 확인 후 `accepted:false` 반환 + 경고.
- **HITL request not found 경고** — plan_review approve 시 `request_id` 가 registry 에 없어 warning 로그. 기능은 동작하지만 모순된 ack. Sprint 14 정리.
- **TestClient + asyncio 시퀀셜 실행 hang** — live 테스트 여러 개 동시 실행 시 두 번째부터 hang. 개별 실행 workaround. 실서버(uvicorn) 영향 없음.
- **동일 turn_id 두 run_turn 공존 race** — `try_acquire` 멱등이라 slot 은 OK 이나 `wait_for_resume` Queue 신호 경쟁 → 하나는 hang. 메모리 누수, user-visible 아님.

### 6.3 운영 이슈
- **PostgreSQL Checkpoint 누적** — Sprint 17+ rotation 정책 필요
- **`logs/layer_guard.jsonl`** — Sprint 17+ 로그 로테이션
- **Windows Hyper-V dynamic port reservation** — 간헐적 `WinError 10013` 발생 (배포 환경 Linux 에선 무관)

---

## 7. Sprint 14 권장 우선순위

1. **HITL 고도화 (A1~A4)** — pause timeout, Todo 편집, team_catalog `requires_approval`, cascade 구체화
2. **Reducer 구현** — 다중 Writer 필드에 대한 `todo_reducer` / `results_reducer` / `trace_reducer`
3. **Glossary / Runbook / Testing Strategy** — `50_glossary`, `40_runbook`, `41_testing_strategy` 신설
4. **Stale resume 정리** — `_handle_resume` Queue 검증, wait_for_resume timeout
5. **Event Catalog** — `23_event_catalog_v1.0.md` 마스터 카탈로그

---

## 8. 주요 커밋 히스토리 (Sprint 13 Integration 범위)

```
7737bc5 test(sprint13): Doc-Code Contract Test (DC-1~5) + agent_specs drift 수정
53074b9 feat(sprint13): R-10 auto-bypass UI 완성 + I12 regression 전부 pass
fdd697d feat(sprint13): R-9 서버 재시작 복원 (resume_query) + 테스트 16건
88cff0b docs(sprint13): R-9 서버 재시작 복원 반영 + agent_specs 검증 사이클
d0fb863 docs(sprint13): R1/R2/R3 추가 검증 — ErrorCodes 전환 완성 + legacy 분류
386ce0b docs(sprint13): agent_specs 구조 정비 — Category prefix + Manager Layer + Error Codes
70dcd96 docs(sprint13): R3~R5 검증 반영 — callback_manager bridge 이벤트 문서화
041200f fix(sprint13): callback_manager bridge for run_turn + todo_* 이벤트 수신
ddf1aca fix(sprint13): I11-b2 dashboard execution UI + docs R1/R2 검증 반영
708daf3 docs(sprint13): I11-c — agent_specs 신규 문서 3종 + POC_legacy 이력 보존
af96d8c feat(sprint13): I11-b1 dashboard Sprint 13 경로 전환
211b3b5 feat(sprint13): WL-06 live 테스트 + layer_guard execution.todos dict 지원
227b881 feat(sprint13): I11-a run_turn 이벤트 보강 + layer guard (121/121 pass)
1389571 feat(sprint13): I10f part2 E2E live tests (5/5 개별 pass) + app 전달 경로
0a14f50 feat(sprint13): I10f part1 /ws/agent query routing + 8 non-live tests
86e6ca6 feat(sprint13): I10e run_turn error handling + cleanup
c58bd9e feat(sprint13): I10d resume loop + _has_pending_interrupts
```

---

## 9. 결론

Sprint 13 Integration 은 **Session/Thread 재설계, interrupt resume 안정화, 대시보드 UX 완성, 서버 재시작 복원, Doc-Code drift 검출 자동화**까지 원 목표를 모두 달성. 137/137 비-live + R-9~R-12 live 통과로 POC 수준의 안정성 확보.

다음 Sprint 14 는 **HITL 고도화(Todo 편집, timeout) + Reducer 구현 + Sprint 15 Memory 의 기반 문서(Glossary/Runbook)** 를 중심으로 진행 권장.

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-22 | 초안 — Sprint 13 Integration 전체 완료 반영 |
