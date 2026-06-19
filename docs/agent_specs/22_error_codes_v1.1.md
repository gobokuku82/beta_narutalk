# Error Codes Catalog (Sprint 13+)

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 개발 - API 계약 |
| 진행상태 | **Active** (Sprint 14 A3 D7=A- 축소 3개 추가) |
| 버전 | **v1.1** |
| 최종 수정일 | 2026-04-23 |
| **진실 소스** | **`backend/app/core/error_codes.py`** (코드가 진실) — `layer_guard.py` 도 D10 (Sprint 14 A3) 로 동일 출처 사용 |
| 관련 명세 | `21_WEBSOCKET_PROTOCOL_v1.5.md` §6, `20_INTERFACE_CONTRACT_v1.1.md` §5 |

> 이 문서는 `error_codes.py`의 참조 문서. **추가/변경은 코드를 먼저**, 이 문서 갱신은 그 다음.

---

## 0. Error 이벤트 포맷

모든 error 이벤트는 `severity`/`layer`/`code`/`message` 4필드를 포함 (Sprint 13 I11-a 통일):

```json
{
  "type": "error",
  "code": "<ERROR_CODE>",
  "layer": "transport|cognitive|planning|execution|response|runtime",
  "severity": "fatal|warning",
  "message": "<사람이 읽을 수 있는 메시지>",
  "detail": { "...": "..." },                  // 선택, 디버그/컨텍스트
  "conversation_id": "conv_xxx",               // fan-out error만
  "turn_id": "turn_yyy"                        // fan-out error만
}
```

- **fatal**: run_turn 조기 종료 (transport/runtime) 또는 `complete(status="aborted")` 후 종료 (layer guard fatal)
- **warning**: 그래프 계속 진행. `complete.data.guard_warnings` 에 누적

**hitl_ack 에서의 code 사용** (Sprint 14 A3): ws_hitl 이 `hitl_ack.accepted=false` 응답 시 `code` + `reason` 필드로 enum 코드 전달 (D7=A- 에서 정의한 3개 중 하나 또는 free-form reason).

---

## 1. 전체 Error Code 카탈로그 (총 11개)

### 1.1 Transport (프로토콜/전송)

| Code | Severity | 발생 조건 | 송신 방식 | 기본 message |
|------|----------|----------|-----------|--------------|
| `INVALID_MESSAGE` | fatal | (1) `_parse_query_message` 검증 실패 (conversation_id/turn_id/user_input 누락) → direct-WS. (2) `resume_query` 에서 conv/turn_id 누락 → direct-WS. (3) `resume_query` 에서 thread_id에 pending interrupt 없음 (stale/이미 complete) → fan-out. (4) **Sprint 14 A3 B5**: ws_hitl todo_* 핸들러 입력 검증 실패 (session_id/todo_id 누락 / changes 빈 dict / new_todo 필수 필드 누락) | direct-WS 또는 fan-out (케이스별) | 케이스별 상세 메시지 |
| `CONCURRENT_LIMIT_EXCEEDED` | fatal | `ConcurrencyManager.try_acquire` 실패 (user당 MAX_CONCURRENT_TURNS_PER_USER 초과) | fan-out (`broadcast_to_user`) | "동시 실행 쿼리 개수 제한 초과" |

### 1.2 Runtime (실행 래퍼)

| Code | Severity | 발생 조건 | 송신 방식 | 기본 message |
|------|----------|----------|-----------|--------------|
| `EXECUTION_ERROR` | fatal | `run_turn` try/except에서 graph 실행 중 미처리 예외 | fan-out | "실행 중 오류가 발생했습니다." + 예외 메시지 |
| `LAYER_ERROR` | fatal | **(2026-06-11 신설)** stage 가 `Command(update={"error": ...}, goto=END)` 로 종료 (cognitive/planning 실패). 과거엔 이 경로가 `complete(status=success)` + 빈 화면("무언의 성공")으로 나가던 정직성 버그 — 이제 error 이벤트 + `complete(aborted, reason=LAYER_ERROR)` | fan-out + complete(aborted) | "처리 단계에서 오류가 발생해 중단되었습니다." + stage error 메시지 |
| **`TODO_EDIT_NOT_PAUSED`** | **warning** | **Sprint 14 A3** — ws_hitl 편집 요청 (todo_modify/delete/add/edit_nl) 시 progress 가 paused 가 아니거나 plan_review 요청 만료된 경우. hitl_ack.accepted=false + code=TODO_EDIT_NOT_PAUSED | hitl_ack | "편집하려면 일시정지 상태가 필요합니다." |

### 1.3 Layer Guard (Sprint 13 I11-a, 품질 검증)

| Code | Layer | Severity | 발생 조건 | 동작 | 기본 message |
|------|-------|----------|----------|------|--------------|
| `COGNITIVE_EMPTY_QUERY` | cognitive | fatal | `structured_query` 없음 또는 brand/tasks 모두 비어있음 | complete(aborted) | "인식 단계에서 구조화 쿼리를 생성하지 못했습니다." |
| `PLANNING_EMPTY_PLAN` | planning | fatal | `plan.todos == []` | complete(aborted) | "계획 단계에서 실행할 Todo가 생성되지 않았습니다." |
| **`INVALID_DAG`** | **planning** | **warning** | **Sprint 14 A3** — plan_editor.validate_edit 에서 DAG 무결성 위반 감지 (순환 / 미정의 의존 / reorder 에 new_position 누락 등) | hitl_ack | "Todo 의존 관계에 문제가 있습니다." |
| **`NL_INTENT_UNCLEAR`** | **planning** | **warning** | **Sprint 14 A3** — plan_editor.parse_instruction 결과 action=unknown (LLM 파싱 실패, 의도 불명, 길이 초과 포함) | hitl_ack | "어떤 작업을 원하시는지 이해하지 못했습니다 — 구조화 UI 로 시도해보세요." |
| `EXECUTION_ALL_FAILED` | execution | fatal | 모든 todo failed (success 0) | complete(aborted) | "모든 Todo 실행이 실패했습니다." |
| `EXECUTION_PARTIAL_FAILED` | execution | warning | 일부 todo failed (success > 0) | 계속 진행 + `guard_warnings` | "N개 Todo가 실패했습니다." |
| `RESPONSE_EMPTY` | response | fatal | `response.text` 공백 | complete(aborted) | "응답 단계에서 빈 응답이 생성되었습니다." |

### 1.4 Sprint 14 A3 D7=A- 축소 — free-form reason 사용 (enum 없음)

다음 4개는 **enum 추가 보류** (cost reversible). free-form `reason` 문자열로 처리:

| (Former code) | 발생 | hitl_ack 예시 |
|---|---|---|
| ~~TODO_NOT_FOUND~~ | delete 대상 todo_id 없음 | `{"accepted": false, "reason": "Todo 를 찾을 수 없습니다 (id=todo_005)"}` |
| ~~CASCADE_FAILED~~ | calculate_cascade 내부 실패 | 현재 실 발생 사례 없음 — 필요 시 승격 |
| ~~NL_LLM_UNAVAILABLE~~ | plan_editor.parse_instruction 예외 (API down/rate limit/timeout) | `{"accepted": false, "reason": "자연어 처리 중 오류: {e}"}` |
| ~~REORDER_INVALID_DAG~~ | reorder 후 DAG cycle 생성 | `INVALID_DAG` 로 대체 (DAG 문제 통합) |

**향후 승격 조건**: Sprint 15+ 에서 해당 케이스별 UX 차별화 필요 시 enum 추가 → 22_error_codes v1.2 bump.

### 1.5 Sprint 12 Legacy Error Codes (신 경로 미사용)

아래 코드들은 **Sprint 12 legacy `_run_agent` 경로 전용**. Sprint 13 `run_turn` 신 경로 에서는 사용되지 않음. Sprint 15+ legacy 제거 시 함께 정리.

| Code | 발생 위치 (legacy) | Sprint 13 신 경로 대체 |
|------|-----|---------|
| `INTERNAL_ERROR` | `_run_agent` 전역 except | `EXECUTION_ERROR` |
| `EMPTY_MESSAGE` | `_run_agent` start msg 검증 | `INVALID_MESSAGE` (user_input 누락) |
| `PAUSE_TIMEOUT` | `_run_agent` wait_for_response 타임아웃 | Sprint 14 A1 timeout 통일 |
| `HITL_TIMEOUT` | 동일 | 동일 |
| `AGENT_ERROR` | `_run_agent` agent 내부 예외 | `EXECUTION_ERROR` |

---

## 2. 사용 예시 (진실 소스 = 코드)

```python
from api.error_codes import ErrorCodes

# CONCURRENT_LIMIT_EXCEEDED emit
await conn_manager.broadcast_to_user(user_id, {
    "type": "error",
    **ErrorCodes.CONCURRENT_LIMIT_EXCEEDED,
    "conversation_id": conv_id,
    "turn_id": turn_id,
})

# Sprint 14 A3: hitl_ack 거부 응답 (TODO_EDIT_NOT_PAUSED)
await _safe_send(websocket, {
    "type": "hitl_ack",
    "data": {
        "action": "todo_modify",
        "accepted": False,
        "reason": "plan_review_expired",
        "code": ErrorCodes.TODO_EDIT_NOT_PAUSED["code"],
    },
})

# free-form reason (D7=A- 4개 케이스)
await _safe_send(websocket, {
    "type": "hitl_ack",
    "data": {
        "action": "todo_edit_nl",
        "accepted": False,
        "reason": f"자연어 처리 중 오류: {e}",
        # code 필드 없음 — free-form
    },
})
```

---

## 3. Layer Guard 동작 상세

상세: `backend/app/dream_agent/system_graph/layer_inspector.py::inspect_layer_output`.

**Sprint 14 A3 D10**: layer_guard 도 `ErrorCodes` 중앙 카탈로그 참조 (기존 dict literal 5곳 제거). DC-6 자동 검증 범위 확장.

Layer guard 는 `_graph_runner_with_resume` 의 `_broadcast_chunks` 내부에서 node_event 수신 직후 실행:

1. `inspect_layer_output(node, data)` → error 목록 반환 (`ErrorCodes.XXX` spread)
2. 각 error 에 대해:
   - `conn_manager.broadcast_to_user` 로 error 이벤트 fan-out
   - `append_guard_log` 로 JSONL (`logs/layer_guard.jsonl`) append
   - fatal 인 경우 abort flag 설정 → `complete(aborted)` 후 return
   - warning 인 경우 `guard_warnings` 리스트에 누적 → 최종 `complete.data.guard_warnings` 에 전달

### key-presence guard (R4 발견, I11-a)
각 layer inspector 는 **기대 key 없으면 skip** — planning reject 경로 `{"response": {...}}` 에서 `PLANNING_EMPTY_PLAN` 오판 방지.

```python
if node == "planning":
    if "plan" not in data:
        return []   # reject 경로 등 — 검증 대상 아님
```

---

## 4. JSONL 로그 포맷 (layer guard 전용)

파일: `logs/layer_guard.jsonl` (append-only, `.gitignore` 대상)

```jsonl
{"ts":"2026-04-21T01:23:45Z","conv_id":"c1","turn_id":"t1","user_id":"demo","layer":"planning","code":"PLANNING_EMPTY_PLAN","severity":"fatal","message":"...","detail":{...},"state_summary":{"entity":"<entity>","plan_todos":0,...}}
```

목적 (POC):
- 페어 누적 → 프롬프트 튜닝 / 규칙 추출 데이터
- Sprint 15 Memory 도입 시 DB로 이관 예정

---

## 변경 이력

> 프레임워크 추출(2026-06-19) 이전(마케팅 도메인 시기)의 상세 변경 이력은 git 히스토리를 참조하세요.
