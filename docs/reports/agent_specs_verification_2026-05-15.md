# agent_specs 다중 사이클 검증 로그 — 2026-05-15

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-05-15 |
| 목적 | 프론트 통합(트랙 2) 진입 전, `docs/agent_specs/` 문서가 백엔드 코드(=진실)와 정합하는지 다중 사이클 검증 |
| 원칙 | **백엔드 코드 = 진실.** 문서가 코드와 어긋나면 문서를 고친다. "오류 1개가 걷잡을 수 없이 번진다" (사용자 명시 우려) |
| 방법 | 사이클 = 검증 → 수정 → 재검증. 코드 직독으로 emit/수신 포맷 대조 |

---

## 사이클 1 — spec 21 (WS 프로토콜) ↔ `ws_agent.py` / `ws_hitl.py`

**상태**: ✅ 완료 (2026-05-15)

**결론**: spec 21 본문은 백엔드 코드와 **근본적으로 정합**. 코어 계약(`query`/`node_event`/`hitl_request`/`paused`/`resumed`/`complete`/`error` 평탄)이 코드와 정확히 일치. → 복원 가이드의 "spec 21 = 진실" 판단 확인.

**발견·정정한 drift 4건** (코드가 스펙보다 약간 더 함 — 프론트가 이 스펙으로 재작성되므로 정정):

| # | 항목 | 스펙(정정 전) | 코드 실제 | 정정 |
|---|------|--------------|-----------|------|
| 1 | `resumed.data.action` 카탈로그 | `approve\|reject\|continue\|cancel` | `modify` 가능 (Phase 5 approve→modify 내부 변환, ws_agent.py:421 / ws_hitl.py:217-222) | `modify` 추가 + 변환 경로 설명 |
| 2 | `hitl_request.data` / `paused.data` | `{request_id,plan,options,message}` 등 | 코드가 `turn_id`+`conversation_id` 도 data 에 복제 주입 (ws_agent.py:393-396, 408-411) | data 예시에 두 필드 추가 + Phase 4 설명 |
| 3 | `/ws/hitl` `connected` | `{type,user_id,timestamp}` | `channel:"hitl"` 포함 (ws_hitl.py:106-111) | `channel` 필드 명시 |
| 4 | `/ws/hitl` `error` / `pong` | 미정의 | `error` 2종 포맷(평탄: 입력검증 / 중첩: legacy), `pong` emit | §3.2 에 `error`·`pong` 추가 + Sprint 16+ 정비 대상 명시 |

**커밋**: (다음 커밋에 포함)

### 사이클 1 상세 대조표 — 정합 확인된 항목

| 메시지 | 방향 | 스펙 §  | 코드 위치 | 정합 |
|--------|------|--------|-----------|------|
| `query` | C→S | 2.1 | `_parse_query_message` (conv_id/turn_id/user_input 검증) | ✅ |
| `resume_query` | C→S | 2.1 | ws_agent.py:639-653 | ✅ |
| `start` (legacy) | C→S | 2.1/8 | ws_agent.py:654-657 `_run_agent` | ✅ 유지 |
| `ping`→`pong` | C↔S | 2.1 | ws_agent.py:658-659 | ✅ |
| `connected` | S→C | 2.2 | ws_agent.py:613-618 `{type,session_id,user_id,timestamp}` | ✅ |
| `node_event` | S→C | 2.2 | `_chunk_to_event` ws_agent.py:90-96 | ✅ |
| `hitl_request` | S→C | 2.2 | ws_agent.py:389-397 + `_build_hitl_request_data` | ✅ (drift #2 정정) |
| `paused` | S→C | 2.2 | ws_agent.py:404-412 + `_build_paused_data` | ✅ (drift #2 정정) |
| `resumed` | S→C | 2.2 | ws_agent.py:443-447 | ✅ (drift #1 정정) |
| `complete` (success/rejected/cancelled/aborted) | S→C | 2.2 | `_emit_complete` ws_agent.py:278-296 | ✅ |
| `error` (평탄, §6) | S→C | 6 | ws_agent.py:310-321 / run_turn:502-530 | ✅ |
| `layer_start`/`todo_start`/`todo_complete`/`progress` | S→C | 2.2 | `_callback_bridge` ws_agent.py:263-276 (enrich) | ⚠️ 사이클 2 에서 execution 측 emit 포맷 확인 필요 |
| `hitl_response`/`pause`/`resume`/`cancel` | C→S | 3.1 | ws_hitl.py 핸들러 | ✅ |
| `todo_modify`/`todo_delete`/`todo_add`/`todo_edit_nl` | C→S | 3.1 | ws_hitl.py 핸들러 | ✅ |
| `hitl_ack` | S→C | 3.2 | ws_hitl.py 각 핸들러 | ✅ |

### 사이클 1 미해결 — 다음 사이클로 이월

- `layer_start`/`todo_start`/`todo_complete`/`progress` 의 **실제 emit 포맷**은 `execution` 측 `callback_manager` 호출부에서 결정됨 — ws_agent.py 의 bridge 는 conv_id/turn_id 만 보강. → 사이클 2 에서 execution 코드 확인.
- 레거시 `start` 경로(`_run_agent`)는 `complete.data.result` (vs 신경로 `data.response`) 등 다른 포맷 — 프론트는 `query` 만 쓰므로 통합엔 무관, 단 spec §8 에 "Sprint 14 regression 후 제거" 로 남아있음.

---

## 사이클 2 — spec 20/22/24 ↔ 백엔드 코드

**상태**: ✅ 완료 (2026-05-15)

**결론**: spec 22(error codes)·spec 24(sequence)는 코드와 거의 정합. **spec 20(interface contract) §3 Layer Contract 스키마는 심각하게 drift** — 특히 Plan 스키마가 실제 모델과 전혀 다름. 모두 정정. **추가로 백엔드 코드 버그 2건 발견** (문서 아님 — 사용자 결정 대기).

### 정정한 문서 drift

| # | 문서 | 항목 | 스펙(정정 전) | 코드 실제 | 정정 |
|---|------|------|--------------|-----------|------|
| 1 | spec 20 §3.1 | StructuredQuery | `{targets:{brand},goal:{type,depth},tasks,meta}` 축약 | `targets`/`goal`/`tasks`/`meta` 각각 중첩 구조. `brand` 는 `targets.brand` | 전체 중첩 구조 전개 |
| 2 | spec 20 §3.2 | **Plan (심각)** | `plan_id`/`intent_summary`/`dependency_graph`/`strategy`/`estimated_duration_sec`/`mermaid_diagram`/`visualization` | 실제 = `teams_selected`/`todos`/`dag`/`plan_notes` 4필드. todo 는 `task_type`(≠`task`) | **전면 재작성** — planner.py `Plan`+`PlannedTodo` 기준 |
| 3 | spec 20 §3.3 | ExecutionResult | `overall_status: success\|failed\|partial`, todo `status: success\|...` | `TodoStatus` enum = `completed\|failed\|...` — `"success"` 값 없음. `halted_at`/`halt_reason` 누락 | enum 값 정정 + 누락 필드 추가 + TodoResult 전체 필드 |
| 4 | spec 20 §3.4 | ResponsePayload | `format: text\|markdown` | `ResponseFormat` enum = `text\|pdf\|image\|chart\|video\|mixed\|error` — `markdown` 없음 | enum 정정 + `meta`/`error` 필드 추가 |
| 5 | spec 20 §5.1 | "Error Code 전체 목록" | 8개만 나열하며 "전체" | 실제 전체 11개 (3개는 hitl_ack용) | "error 이벤트용 8개" 로 명확화 + spec 22 참조 |
| 6 | spec 20/22 헤더 | 관련 명세 링크 | `21_WEBSOCKET_PROTOCOL_v1.2.md` | 현 권위 = v1.4 | v1.2→v1.4 (sed, 5곳) |
| 7 | spec 24 §3 | 다이어그램 | `paused / hitl_request(execution_pause)` | execution_pause → `paused` 단일 emit | `paused` 만 |
| 8 | spec 24 §3.1 | payload 표 `paused` | `data:{progress, reason}` | `_build_paused_data` = `{request_id,completed,total,current_phase,progress}` | 실제 필드로 정정, `reason` 제거 |

### 🔴 백엔드 코드 버그 — 발견 (문서 작업 범위 밖, 사용자 결정 대기)

| # | 위치 | 내용 | 영향 |
|---|------|------|------|
| **B1** | `backend/api_v2/layer_guard.py:51` | `inspect_layer_output` cognitive 검사가 `sq.get("brand")` 로 **최상위** 접근 — 실제 `brand` 는 `targets.brand` 중첩 → 항상 `None`. COGNITIVE_EMPTY_QUERY 가드는 실질적으로 `tasks` 비어있음만 검사 | 낮음 — `brand` 는 Optional 이라 의도와 우연히 비슷. dead clause |
| **B2** | `backend/api_v2/layer_guard.py:81` | `inspect_layer_output` execution 검사가 `t.get("status") == "success"` — 실제 `TodoStatus` enum 값은 `"completed"`. `succeeded` 리스트가 **항상 빈 리스트** → 일부 todo 만 실패해도 `len(succeeded)==0 and len(failed)>0` 성립 → **부분 실패가 `EXECUTION_ALL_FAILED`(fatal) 로 오분류되어 turn abort**. `EXECUTION_PARTIAL_FAILED` 분기 도달 불가 | **높음** — 실 도구가 하나라도 실패하면 전체 turn 중단. 현재는 stub 도구가 다 success 라 잠복. 1줄 수정 (`"success"`→`"completed"`) |

> B1/B2 는 백엔드 코드 수정이라 "백엔드 무수정" 원칙상 본 검증 작업에서 고치지 않음. 사용자 승인 시 별도 1-2줄 패치로 처리 권장.

### 정합 확인된 항목

- **spec 22 (error codes)**: 11개 enum 카탈로그가 `error_codes.py` 와 **완전 정합**. `layer_guard.py` 도 §1.3 조건과 정합 (단 B2 오타 제외).
- **spec 24 (sequence)**: 8종 시퀀스 모두 `ws_agent.py`/`ws_hitl.py` 흐름과 정합 (정정 2건은 payload 표기 수준).
- **spec 20 §4 (AgentState)**: `init_agent_state` 시그니처·State 키 16종이 `agent_state.py` 와 정합.
- **spec 20 §8 (코드 참조)**: 9개 파일 경로 모두 실재 확인.

### 사이클 2 미해결 — 다음 사이클 또는 별도 트랙

- `ExecutionProgress` (hitl_manager) 스키마는 spec 30(`30_DATA_MODELS`) 영역 — 사이클 미지정. `paused.data.progress` 가 이 구조라 프론트가 필요로 함.
- `layer_start`/`todo_*`/`progress` 의 실제 emit 포맷 (callback_manager 측) — 사이클 1 이월분, 미확인.
- 잔존 파일 `docs/agent_specs/21_WEBSOCKET_PROTOCOL_v1.2.md` — 구버전, 혼동 유발. v1.3 파일은 이미 삭제됨(불일치). 삭제 권장 — 사용자 확인 필요.

---

## 사이클 3 — spec 63 + 60-series 프론트 스펙 ↔ 백엔드 현실

**상태**: ✅ 완료 (2026-05-15)

**결론**: **spec 63 이 spec 21/20/22 와 광범위하게 어긋나 있었다** — WS 계약뿐 아니라 REST 엔드포인트·에러코드·시퀀스까지. 이것이 프론트 `schemas.ts` 가 잘못 작성되어 백엔드 응답을 `safeParse` 에서 전량 폐기한 **근본 원인**. 4개 섹션 전면 정정. spec 61 도 같은 계열 오류 2곳 정정. spec 60 Tailwind 버전 정정. spec 62 는 정합 (설계 제안 문서).

### spec 63 정정 (4개 섹션 전면)

| # | 섹션 | 정정 전 | 실제 | 정정 |
|---|------|---------|------|------|
| 1 | §2.1 REST | `/api/agent/stream`(POST)·`/api/agent/runs/{turn_id}`·`/api/agent/feedback` | 백엔드에 **존재 안 함**. 쿼리는 WS `{type:"query"}` | 가공 3개 제거, 실재 REST(`/health*`,`/api/mock/*`)만 + WS 경로 명시 |
| 2 | §4.1/4.2 WS 카탈로그 | `agent_message`/`agent_message_complete` 수신, `hitl_request` 가 `/ws/hitl` | `agent_message*` **미발행**, `hitl_request`/`paused`/`resumed` 는 `/ws/agent` | `agent_message*` 제거, 채널 정정, `connected`/`paused`/`resumed`/`layer_start`/`todo_*`/`progress`/`pong` 추가 |
| 3 | §4.3 zod schema | `node_event.data`={layer,node_name,status,timestamp}, `hitl_request.data`={request_type,...}, `WSMessageSchema` 에 `AgentMessage*` | 평탄 envelope, `node_event`={type,node,conv_id,turn_id,data:<State dict>}, `hitl_request` 에 `request_type` 없음 | 전 schema 재작성 (spec 21 §2.2 기준) — **이게 통합 break 의 직접 원인** |
| 4 | §7.1 error code | 11개 중 7개가 가공 (`PLAN_REQUEST_NONE`/`TURN_NOT_ACTIVE`/`SESSION_NOT_FOUND`/`LAYER_GUARD_FATAL`/`HITL_TIMEOUT`/`LLM_UNAVAILABLE`/`INTERNAL_ERROR`) | `error_codes.py` 실제 11개 | 가공 제거, 실제 11개 + layer/severity/전달경로 + `errorMessages.ts` 11개 |
| 5 | §8.1/8.2 시퀀스 | REST POST 로 시작, `agent_message` 스트리밍, reject→`complete(reason=)` | WS `query` 시작, 스트리밍 없음, reject→`complete(status="rejected")` | 시퀀스 정정 |

> §6 Plan/PlannedTodo zod 는 `planner.py` 와 **정합 확인** — 무수정. (이 문서에서 유일하게 맞던 부분)

### spec 61 정정

| # | 섹션 | 정정 |
|---|------|------|
| 1 | §1.2 agent store | `streamingMessage`/`appendMessage` (백엔드 미발행 `agent_message` 의존) 제거 → `appendUserMessage`/`finalizeFromComplete` |
| 2 | §1.5 WS 통합 예시 | 단일 핸들러 → `/ws/agent`·`/ws/hitl` 채널별 분리, `agent_message` 케이스 제거, 실제 이벤트만 라우팅 |

### spec 60 정정

- §2.1/§2.4 Tailwind 버전 — 문서 `v4` → 실제 `tailwindcss ^3.4.0` (`frontend/package.json` 확인)

### 정합 확인 / 미정정 (별도 트랙)

- **spec 62 (Workflow Canvas)**: 정합. `PlannedTodo` 의 `position`/`node_type`/`visualization_meta` 는 "Sprint 15+ 신규" 로 명시된 *제안* — 현 `planner.py` 에 없는 게 맞음 (드리프트 아님).
- **spec 61 §1.2 store 경로**: 문서 `src/stores/*` ↔ 실제 코드 `features/*/store.ts` — 설계 문서 표기 차이, 계약 아님. 미정정 (코드가 진실).
- **spec 61 §4 Design System**: 색상 토큰이 Warm Neutral 재설계(`a5c4fc3`) 이전 shadcn 기본값. 계약 아님 — `globals.css`/`tailwind.config.ts` 가 진실. 미정정 (설계 문서, 재작성은 별도 작업).
- **라우터**: spec 60/61 "TanStack Router 또는 React Router v7 — PoC 후 결정" — 실제 `@tanstack/react-router ^1.45` 로 결정 완료. 문서 표기만 미해소.

### 사이클 3 부수 작업

- `docs/agent_specs/21_WEBSOCKET_PROTOCOL_v1.2.md` 삭제 (사용자 승인) — 현 권위 v1.4, 구버전 혼동 제거.
- ⚠️ 잔존: `21_WEBSOCKET_PROTOCOL_v1.2.md` / `22_error_codes_v1.0.md` 로의 stale 링크가 다수 문서(`10`/`12`/`30` spec, `_claude/*` handoff 문서 등)에 남음 — 별도 hygiene 패스 필요.

---

## 재검증 사이클 — 정정 문서 간 상호 정합성 교차 확인

**상태**: ✅ 완료 (2026-05-15)

3개 사이클에서 정정한 문서들이 **서로 일치하는지** 교차 확인:

| 교차 대조 | 결과 |
|-----------|------|
| spec 21 ↔ spec 63 §4.3 zod (`resumed.action`/`hitl_request.data`/`paused.data`/`connected`) | ✅ 일치 |
| spec 20 §3.2 Plan ↔ spec 63 §6.1 `PlanSchema`/`PlannedTodoSchema` | ⚠️→✅ `PlannedTodoSchema` 에 `team` 필드 누락 발견 → 추가 정정 |
| spec 22 11개 ↔ spec 63 §7.1 11개 | ✅ 일치 |
| spec 24 §3.1 `paused` payload ↔ spec 21 §2.2 `paused` | ✅ 일치 |
| spec 20 §3.3 ExecutionResult ↔ spec 63 `CompleteSchema.execution_result` | ✅ 충돌 없음 (spec 63 은 loose `z.record`) |

**재검증 정정**: spec 63 §6.1 `PlannedTodoSchema` 에 `team: z.string().nullable().optional()` 추가 — `planner.py` `PlannedTodo.team` 과 정합.

→ 재검증 후 **3개 사이클의 정정 문서가 상호 정합**. 트랙 1 (문서 검증) 종료.

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-15 | 초안 — 사이클 1 (spec 21 ↔ WS 백엔드 코드) 완료. drift 4건 정정. 사이클 2/3 예정 |
| 2026-05-15 | 사이클 2 (spec 20/22/24 ↔ 백엔드 코드) 완료. spec 20 §3 스키마 drift 8건 정정 (Plan 전면 재작성 포함). 백엔드 코드 버그 2건(B1/B2) 발견 — 사용자 결정 대기 |
| 2026-05-15 | 사이클 3 (spec 63 + 60-series ↔ 백엔드 현실) 완료. spec 63 4개 섹션 전면 정정 (safeParse 전량 폐기 근본 원인), spec 61 2곳·spec 60 Tailwind 버전 정정. `21_WEBSOCKET_PROTOCOL_v1.2.md` 삭제. **3개 사이클 완료** — 트랙 1 종료, 트랙 2(프론트 통합) 진입 가능 |
| 2026-05-15 | 사이클 4 (추가) — spec 30 (data models) 전면 정정. v1.0 → v1.1 (legacy/ 백업 보존). v1.0 의 12 항목 drift 정정: Targets/Goal/Task/QueryMeta 필드, GoalType/OutputFormat/ResponseFormat enum, TaskType 17 값, Plan 전체 재작성, TodoStatus 5값(`success`/`cancelled` 가공 제거), `overall_status` enum 화. 이름 충돌(`Plan`/`ExecutionResult`/`TodoStatus` 각각 2곳) 명시 |
| 2026-05-15 | **사이클 5 (별 트랙) — models/ cleanup A1~A7 실행 완료**. 5사이클 검증(usage matrix → enums 미확정 → docstring·git 이력 → baseline 13/13 OK → Plan 12 메서드 호출 0 + pytest collect 311/336) 후 atomic 7 커밋으로 실행. 삭제: intent.py / approval.py / plan.py / todo.py + enums 7개 + execution.ExecutionResult. **이름 충돌 3건 모두 해소** (Plan/ExecutionResult/TodoStatus 각 1곳만). 코드 -680줄, 동작 변경 0. 계획서 = `docs/_claude/models_cleanup_plan_2026-05-15.md` v0.4 |
