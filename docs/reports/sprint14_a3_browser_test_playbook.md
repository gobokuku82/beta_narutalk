# Sprint 14 A3 — 브라우저 수동 검증 플레이북 (R-5 ~ R-18)

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-24 |
| 대상 Sprint | 14 A3 Phase 5 (Plan review 편집 경로 통합 완료 시점) |
| 목적 | 사용자 의도 ↔ 실제 endpoint/함수/신호가 일치하는지 검증 — **Acceptance + Contract Testing** |
| 실행 주체 | 사용자 (브라우저) + Claude (결과 해석) |
| 결과 기록 | [`sprint14_a3_test_log.md`](./sprint14_a3_test_log.md) 세션 #N 에 append |

---

## 0. 이 문서가 뭔지 (업계 용어)

### 0.1 왜 플레이북이 필요한가

기계가 돌리는 자동 테스트 (Group A~H, 238건) 로도 대부분 검증됩니다. 하지만 **"내가 의도한 대로 UI 에서 클릭했을 때 서버가 맞게 동작하는가"** 는 사람 눈이 필요합니다. 이게 Acceptance Testing.

### 0.2 이 문서의 포맷

각 시나리오마다:
- **Given** (사전 조건 — 준비된 상태)
- **When** (사용자 클릭·입력)
- **Then** (기대 결과)
- **신호 흐름** (WebSocket 메시지 ↔ 서버 함수 체인)
- **검증 포인트** (무엇을 보면 PASS)
- **FAIL 시 진단** (어디를 의심할지)

Given-When-Then 은 **BDD (Behavior-Driven Development)** 관행에서 온 것. "행동 기술 언어" 정도 의미.

---

## 1. 공통 준비

### 1.1 환경

```bash
# 서버 기동 (터미널 1)
uv run python run_server_v2.py
# → Uvicorn on http://localhost:8001

# 브라우저 접속
http://localhost:8001/dashboard
```

### 1.2 사전 체크

- [ ] 서버 로그에 `PostgreSQL Checkpointer` 초기화 로그 확인
- [ ] 브라우저 개발자도구 (F12) → **Console** 과 **Network** 탭 열어두기
- [ ] Network 에서 `ws` 필터로 `/ws/agent`, `/ws/hitl` 두 연결 확인 (상태 101 Switching Protocols)
- [ ] 대시보드 우상단 연결 상태 "🟢 연결됨"

### 1.3 공통 용어

| 약어 | 풀네임 | 역할 |
|------|--------|------|
| **C** | Client (Dashboard) | 브라우저 `dashboard/index.html` |
| **WA** | `/ws/agent` endpoint | 서버 → 클라 이벤트 스트림 |
| **WH** | `/ws/hitl` endpoint | 사용자 → 서버 명령 |
| **RT** | `run_turn` task | 1 쿼리 당 독립 asyncio task |
| **G** | LangGraph StateGraph | cognitive→planning→execution→response |
| **HM** | `hitl_manager` 싱글톤 | 편집·pause·resume 관리 |
| **TM** | `todo_manager` 싱글톤 | DAG·cascade 계산 |

---

## 2. R-5 — Plan review 단계 편집 (핵심 검증)

> **Phase 5 의 새 기능**. 이전 실패 케이스 재검증.

### 2.1 목적

사용자 5항목 요구사항 §4 "hitl=pause 같은 개념" 이 구현되었는지 검증. Plan review 모달에서도 execution pause 와 동일한 편집 UX.

### 2.2 Given

- 서버 기동 완료
- 브라우저 접속 완료
- 쿼리 입력란 비어있음, 모달 닫혀있음

### 2.3 When

1. 쿼리 입력란에 자연어 쿼리 입력 (예: "블루밍글로우 2024 Q3 리뷰 분석 요약해줘")
2. **[전송]** 버튼 클릭
3. Plan review 모달 팝업 대기 (~3~5초)
4. 모달 내 Todo 목록 중 하나의 🗑 버튼 클릭
5. Confirm 대화상자 **[확인]**
6. 모달 하단 **[✅ 승인]** 버튼 클릭

### 2.4 Then (기대 결과)

- 🗑 클릭 시 즉시 목록에서 Todo 제거 + 🔴 tint + ⛓ 라벨 표시
- 승인 시 모달 자동 close + execution 이 **편집된 plan** 으로 실행 시작
- 최종 complete 이벤트 수신 + 결과 블록 표시

### 2.5 신호 흐름

```
C            WA              RT              G          HM           WH           TM
│            │               │               │          │            │            │
│──query────▶│                                          │            │            │
│            │─spawn─────────▶│                          │            │            │
│            │                │─astream──────▶│          │            │            │
│            │                │               │◀─node(cognitive)                   │
│◀─node_event(cognitive)─────│                          │            │            │
│            │                │               │◀─node(planning)                    │
│◀─node_event(planning)──────│                          │            │            │
│            │                │               │─interrupt({plan_review, plan})    │
│            │                │               │◀─pending intr                     │
│            │                │               │                                   │
│            │                │─create_progress(turn_id, plan)────▶│ status="paused"│
│            │                │               │                                   │
│            │                │─broadcast hitl_request───────────────────────────▶│
│◀─hitl_request(plan)─────────│                                                    │
│                                                                                  │
│ [openHitlModal("plan_review", data)]                                              │
│                                                                                  │
│─todo_delete─────────────────▶ WH                                                  │
│                               │                                                   │
│                               │─_check_turn_active ✅                              │
│                               │─_get_lock────────▶│                              │
│                               │─handle_todo_delete───────────────▶│              │
│                               │                                    │─calculate_cascade─▶│
│                               │                                    │ progress.plan mutate│
│                               │                                    │ phases rebuild      │
│◀─hitl_ack(accepted:true, invalidated=[...], plan=edited)           │              │
│                                                                                   │
│ [renderCascade: 🔴 tint + ⛓ 라벨]                                                  │
│                                                                                   │
│─hitl_response({action:"approve"})──▶ WH                                           │
│                                    │                                              │
│                                    │─get_progress─▶│ (progress 존재)              │
│                                    │─request_resume▶│ status="running"            │
│                                    │─signal_resume({action:"modify",              │
│                                    │                  value:progress.plan})──────▶│
│◀─hitl_ack(approve accepted:true)   │                                              │
│                                    │                                              │
│            │                │◀─wait_for_resume 깨어남─┤                           │
│            │                │─Command(resume={modify, value:edited plan})────────▶│
│            │                │               │ [planning_stage L88-92]            │
│            │                │               │ plan_dict = value                   │
│            │                │               │─goto execution──▶                   │
│            │                │               │ (edited plan 으로 실행)              │
│            │                │               │◀─node(execution)                    │
│◀─node_event(execution)──────│                                                     │
│            │                │               │◀─complete(success)                 │
│◀─complete(success)──────────│                                                     │
│                             │─cleanup_turn────────────────────▶│ _progress.pop    │
```

### 2.6 호출되는 코드 체인

| 단계 | 파일:함수 |
|------|-----------|
| 쿼리 수신 | `ws_agent.py::stream_endpoint` → `run_turn` |
| graph 실행 | `ws_agent.py::_graph_runner_with_resume` |
| interrupt 감지 | `_graph_runner_with_resume` loop 내 `_has_pending_interrupts` |
| **임시 progress 생성 (Phase 5 신규)** | `hitl_manager.manager.py::create_progress` + `temp.status = "paused"` |
| hitl_request broadcast | `ws_agent._graph_runner_with_resume:381~` |
| Todo 삭제 요청 수신 | `ws_hitl.py::_handle_todo_delete` |
| turn_active 가드 | `ws_hitl.py::_check_turn_active` |
| Lock 획득 | `hitl_manager._get_lock(session_id)` |
| 삭제·cascade | `hitl_manager.handle_todo_delete` → `todo_manager.calculate_cascade` |
| 승인 수신 | `ws_hitl.py::_handle_hitl_response` |
| **approve→modify 변환 (Phase 5 신규)** | `_handle_hitl_response` 내 `action=="approve" and progress is not None` 분기 |
| graph 재개 | `hitl_manager.signal_resume` → `wait_for_resume` 깨어남 → `Command(resume=...)` |
| plan 교체 | `planning_stage.py:88-92` modify 분기 |
| execution | `execution_stage.py` |
| cleanup | `run_turn finally` → `hitl_manager.cleanup_turn` (→ `_progress.pop`) |

### 2.7 검증 포인트 (하나라도 실패하면 ❌)

| # | 항목 | 확인 방법 |
|---|------|----------|
| 1 | Plan review 모달이 자동 팝업 | 육안 |
| 2 | 🗑 클릭 시 "⚠️ 편집하려면 일시정지 상태가 필요합니다" **안 뜸** | 육안 |
| 3 | 🗑 클릭 직후 Todo 목록에서 해당 행 사라짐 | 육안 |
| 4 | 🔴 tint + ⛓ 라벨 표시 | 육안 |
| 5 | Console 에 `[hitl] ack: { accepted: true, ... }` | F12 Console |
| 6 | Network 탭에서 `/ws/hitl` WS 프레임에 `"todo_delete"` 송신 확인 | F12 Network → WS → Messages |
| 7 | 서버 로그: `todo deleted via HITL ... invalidated=[...]` | 터미널 1 |
| 8 | 승인 후 서버 로그: `planning modified by user` | 터미널 1 |
| 9 | execution 진입 로그: 편집된 Todo 목록으로 진행 | 터미널 1 |
| 10 | 최종 complete(success) 수신 + 결과 블록 표시 | 육안 |

### 2.8 FAIL 시 진단 순서

1. **1번 실패**: `openHitlModal` 호출 안 됨 → `handleHitlRequest` 진입 확인
2. **2번 실패**: Change #1 (임시 progress 생성) 미적용 확인 → `create_progress` 서버 로그 확인
3. **5번 실패**: ack 구조 확인 — `invalidated` 배열 비었는지
4. **8번 실패**: Change #2 (approve→modify 변환) 미적용 → `ws_hitl._handle_hitl_response` 의 `resume_payload` 내용 디버깅
5. **10번 실패**: execution 중 에러 로그 확인 (layer_guard fatal 가능)

---

## 3. R-6 — Cascade 무효화 시각화 (downstream 3+)

### 3.1 목적

`calculate_cascade` 가 BFS 로 downstream 을 찾아 UI 에 반영하는지 검증.

### 3.2 Given

- 쿼리로 t1→t2→t3→t4→t5 등 긴 체인 Plan 생성 (예: "10단계 분석 파이프라인 만들어줘")

### 3.3 When

1. Plan review 모달 팝업
2. **중간 Todo (예: t2) 의 🗑 클릭**

### 3.4 Then

- t2 + downstream (t3, t4, t5, ...) 모두 🔴 tint
- 통계 바 "N개 무효화 · 0개 유지 · ⚠️ 0 issues"
- ⛓ "Todo t2 부터 재실행됩니다" (plan_review 에선 "재실행" 표현이 어색할 수 있음 — 옵션 B 로 추후 개선 가능)

### 3.5 신호 흐름 요약

R-5 와 동일하되 `invalidated` 배열 크기가 3+ 인 것만 다름.

### 3.6 검증 포인트

| # | 항목 |
|---|------|
| 1 | `hitl_ack.data.invalidated.length >= 3` (F12 Console) |
| 2 | 🔴 tint 가 3개 이상 행에 적용 |
| 3 | 통계 바에 "N개 무효화" 숫자 정확 |
| 4 | ⛓ 라벨의 `restart_from` = 첫 번째 invalidated Todo ID |

---

## 4. R-7 — Todo 추가

### 4.1 Given

- Execution pause 중 또는 Plan review 중 모달 open

### 4.2 When

1. 모달 하단 **"+ Todo 추가"** 버튼 클릭
2. prompt 에 agent 이름 입력 (예: `analysis_agent`)
3. prompt 에 task 입력 (예: `추가 분석 작업`)

### 4.3 Then

- Todo 목록 맨 뒤에 신규 행 추가 (`depends_on` 은 빈 배열)
- ack accepted:true + `added_id` 필드 포함

### 4.4 신호 흐름

```
C ──todo_add{new_todo:{agent, task}}──▶ WH
                                        │─_check_turn_active ✅
                                        │─hitl.handle_todo_add
                                        │   (tm.add_todo → plan mutate)
                                        │   (phases rebuild)
C ◀──hitl_ack{accepted:true, added_id, plan}
```

### 4.5 검증 포인트

| # | 항목 |
|---|------|
| 1 | prompt 두 번 뜸 (agent / task) |
| 2 | Todo 목록 끝에 행 추가 |
| 3 | 신규 Todo 의 `depends_on=[]` (F12 Console 에서 plan 확인) |
| 4 | ack `added_id` 필드 존재 |

---

## 5. R-8 — Diamond DAG (t1 → {t2,t3} → t4)

### 5.1 목적

BFS cascade 가 "독립 경로 preserved" 를 정확히 계산하는지 검증. Diamond 구조는 classic 테스트 케이스.

### 5.2 Given

- Plan 구조: `t1 → t2, t3` 병렬 → `t4` 둘 다 depends
  - 생성 쿼리 예: "수집 후 두 분석 병렬 후 리포트 생성"

### 5.3 When

1. Plan review 또는 pause 모달 open
2. **t2** 만 🗑 삭제

### 5.4 Then

- invalidated = **[t2, t4]** (t4 는 t2 depends_on 이므로)
- preserved = **[t3]** (t3 는 t2 와 독립)

### 5.5 검증 포인트

| # | 항목 |
|---|------|
| 1 | `hitl_ack.data.invalidated` = `["t2", "t4"]` (순서는 BFS 순) |
| 2 | `preserved` 에 t3 포함 |
| 3 | t3 행은 🔴 tint **없음** |
| 4 | t2, t4 행만 🔴 tint |

### 5.6 FAIL 시 진단

- `todo_manager.calculate_cascade` 의 BFS 로직 의심 → `backend/app/dream_agent/workflow_managers/todo_manager/cascade.py` 확인

---

## 6. R-16 — 자연어 편집 (NL 삭제)

### 6.1 Given

- pause 또는 plan_review 모달 open
- OpenAI API 키 설정됨 (`.env`)

### 6.2 When

1. 모달 하단 🗣 textarea 에 **"4번 삭제"** 입력
2. **[⚡ 적용]** 클릭

### 6.3 Then

- 로딩 스피너 1~3초
- ack accepted:true, `nl_action: "remove"`
- 4번 Todo 제거 + cascade 시각화
- textarea 초기화 + "✓ remove 적용됨" 피드백

### 6.4 신호 흐름

```
C ──todo_edit_nl{instruction:"4번 삭제"}──▶ WH
                                            │─_check_turn_active ✅
                                            │─plan_editor.parse_instruction (LLM 호출 1~3s)
                                            │   → {action:"remove", target_todo_ids:["t4"]}
                                            │─plan_editor.validate_edit (DAG 무결성)
                                            │─plan_editor.apply_edit (Pydantic Plan mutate)
                                            │─tm.calculate_cascade (각 target 마다)
                                            │─progress.plan = new_plan_dict
C ◀──hitl_ack{accepted:true, nl_action, invalidated, plan}
```

### 6.5 검증 포인트

| # | 항목 |
|---|------|
| 1 | textarea 비활성화 (로딩 중) |
| 2 | 스피너 1~3초 후 사라짐 |
| 3 | Console: `nl_action: "remove"`, `invalidated` 배열 존재 |
| 4 | 4번 Todo 삭제됨 |
| 5 | 4번 depends 가 있다면 downstream 도 🔴 tint |
| 6 | textarea 내용 초기화 |

### 6.6 FAIL 시 진단

- LLM API 키 / 네트워크 확인
- 서버 로그 `plan_editor.parse_instruction 실패` 시 OpenAI 응답 확인
- `NL_INTENT_UNCLEAR` 반환 시 → R-18 경로

---

## 7. R-17 — 자연어 편집 (NL 순서 변경)

### 7.1 Given

- pause / plan_review 모달 open + Todo 3개 이상

### 7.2 When

1. 🗣 textarea: **"3번과 4번 순서 바꿔"**
2. 적용

### 7.3 Then

- `nl_action: "reorder"`
- Todo 목록에서 3번·4번 위치 교환
- cascade 는 depends 있으면 일부 invalidated

### 7.4 신호 흐름

R-16 과 동일하되 `apply_edit` 의 **reorder 분기** 호출 (Phase 3 신구현).

### 7.5 검증 포인트

| # | 항목 |
|---|------|
| 1 | `nl_action: "reorder"` |
| 2 | UI 순서 변경 |
| 3 | depends_on 관계 있으면 해당 invalidated |

---

## 8. R-18 — NL 파싱 실패 UX

### 8.1 목적

LLM 이 의도 파악 실패 시 사용자에게 친절한 안내.

### 8.2 Given

- pause / plan_review 모달 open

### 8.3 When

1. 🗣 textarea: **"asdf xyz 123"** (의미 불명)
2. 적용

### 8.4 Then

- ack accepted:**false**
- `code: "NL_INTENT_UNCLEAR"`
- 토스트 "⚠️ 어떤 작업을 원하시는지 이해하지 못했습니다..."
- textarea 내용 **보존** (재시도 가능)
- 모달 유지

### 8.5 신호 흐름

```
C ──todo_edit_nl{instruction:"asdf xyz 123"}──▶ WH
                                                │─plan_editor.parse_instruction
                                                │   → {action:"unknown", reason:...}
C ◀──hitl_ack{accepted:false, code:"NL_INTENT_UNCLEAR", reason}
```

### 8.6 검증 포인트

| # | 항목 |
|---|------|
| 1 | ack `accepted: false` |
| 2 | ack `code: "NL_INTENT_UNCLEAR"` |
| 3 | 토스트 한국어로 친절하게 |
| 4 | textarea 내용 남아있음 |
| 5 | 모달 유지 (auto-close 안 됨) |

---

## 9. 실행 순서 권고

**최초 Phase 5 검증**:
1. **R-5** (가장 중요 — 편집 경로 통합 최초 검증)
2. **R-6** (cascade 시각화)
3. **R-7** (Todo 추가)
4. **R-8** (Diamond DAG, preserved 검증)

**NL 편집**:
5. R-16 (NL 삭제)
6. R-17 (NL 순서 변경)
7. R-18 (NL 실패 UX)

**기존 회귀 (R-1~R-4)**: 이미 세션 #1 에서 ✅. 변경 크면 한 번 더 확인 권장.

---

## 10. 결과 기록 양식

각 시나리오 실행 후 [`sprint14_a3_test_log.md`](./sprint14_a3_test_log.md) 세션 #2 에 다음 형식으로 추가:

```markdown
## 세션 #2 — YYYY-MM-DD

### 환경
- 커밋 SHA: <git log --oneline -1>
- 브라우저: Chrome <version>

### 시나리오별 결과
| ID | 결과 | 소요 시간 | 비고 |
|----|------|----------|------|
| R-5 | ✅/❌ | Xs | 검증 포인트 10개 중 N개 통과 |
| R-6 | ... | ... | ... |

### 발견 & 수정
| # | 이슈 | 커밋 | 상태 |
|---|------|------|------|
| 1 | ... | ... | ... |
```

---

## 11. 이 문서의 확장 방식

신규 시나리오 추가 시:
- 번호 R-19 이상으로 증가
- §2~§8 의 동일 포맷 (Given/When/Then/신호 흐름/검증 포인트/진단) 따르기
- 호출 함수 체인 표는 현 코드 기준 (drift 시 문서 bump)

**문서 drift 방지**: 이 플레이북은 코드 변경 시 함께 갱신 — 특히 `ws_agent.py`, `ws_hitl.py`, `hitl_manager/manager.py` 시그니처 변경 시.

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-24 | 초안 — R-5~R-18 7개 시나리오 + Given-When-Then + 신호 흐름 + 호출 함수 체인 + 검증 포인트 + FAIL 진단. Sprint 14 A3 Phase 5 기준 |
