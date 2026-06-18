# Error Codes Catalog (Sprint 13+)

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 개발 - API 계약 |
| 진행상태 | **Active** (Sprint 13 I11-a 기준) |
| 버전 | **v1.0** |
| 최종 수정일 | 2026-04-21 |
| **진실 소스** | **`backend/api_v2/error_codes.py`** (코드가 진실) |
| 관련 명세 | `21_WEBSOCKET_PROTOCOL_v1.2.md` §6, `20_INTERFACE_CONTRACT_v1.1.md` §5 |

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

---

## 1. 전체 Error Code 카탈로그 (8개)

### 1.1 Transport (프로토콜/전송)

| Code | Severity | 발생 조건 | 송신 방식 | 기본 message |
|------|----------|----------|-----------|--------------|
| `INVALID_MESSAGE` | fatal | (1) `_parse_query_message` 검증 실패 (conversation_id/turn_id/user_input 누락) → direct-WS. (2) `resume_query` 에서 conv/turn_id 누락 → direct-WS. (3) `resume_query` 에서 thread_id에 pending interrupt 없음 (stale/이미 complete) → fan-out | direct-WS 또는 fan-out (케이스별) | "메시지 형식이 올바르지 않습니다." / "해당 turn에 대기 중인 interrupt가 없습니다" |
| `CONCURRENT_LIMIT_EXCEEDED` | fatal | `ConcurrencyManager.try_acquire` 실패 (user당 MAX_CONCURRENT_TURNS_PER_USER 초과) | fan-out (`broadcast_to_user`) | "동시 실행 쿼리 개수 제한 초과" |

### 1.2 Runtime (실행 래퍼)

| Code | Severity | 발생 조건 | 송신 방식 | 기본 message |
|------|----------|----------|-----------|--------------|
| `EXECUTION_ERROR` | fatal | `run_turn` try/except에서 graph 실행 중 미처리 예외 | fan-out | "실행 중 오류가 발생했습니다." + 예외 메시지 |

### 1.3 Layer Guard (Sprint 13 I11-a, 품질 검증)

| Code | Layer | Severity | 발생 조건 | 동작 | 기본 message |
|------|-------|----------|----------|------|--------------|
| `COGNITIVE_EMPTY_QUERY` | cognitive | fatal | `structured_query` 없음 또는 brand/tasks 모두 비어있음 | complete(aborted) | "인식 단계에서 구조화 쿼리를 생성하지 못했습니다." |
| `PLANNING_EMPTY_PLAN` | planning | fatal | `plan.todos == []` | complete(aborted) | "계획 단계에서 실행할 Todo가 생성되지 않았습니다." |
| `EXECUTION_ALL_FAILED` | execution | fatal | 모든 todo failed (success 0) | complete(aborted) | "모든 Todo 실행이 실패했습니다." |
| `EXECUTION_PARTIAL_FAILED` | execution | warning | 일부 todo failed (success > 0) | 계속 진행 + `guard_warnings` | "N개 Todo가 실패했습니다." |
| `RESPONSE_EMPTY` | response | fatal | `response.text` 공백 | complete(aborted) | "응답 단계에서 빈 응답이 생성되었습니다." |

**Sprint 14 예정** (현재 미구현):
- `PLANNING_INVALID_AGENTS` (warning) — `team_catalog.yaml` 외 agent 사용 시. 복잡도 ↑ 로 Sprint 14로 연기.

### 1.4 Sprint 12 Legacy Error Codes (신 경로 미사용)

아래 코드들은 **Sprint 12 legacy `_run_agent` 경로 전용** — Sprint 13 `run_turn` 신 경로에서는 사용되지 않음. Sprint 14 regression 완료 후 legacy 제거 시 함께 정리.

| Code | 발생 위치 (legacy) | Sprint 13 신 경로 대체 |
|------|-----|---------|
| `INTERNAL_ERROR` | `_run_agent` 전역 except | `EXECUTION_ERROR` |
| `EMPTY_MESSAGE` | `_run_agent` start msg 검증 | `INVALID_MESSAGE` (user_input 누락) |
| `PAUSE_TIMEOUT` | `_run_agent` wait_for_response 타임아웃 | Sprint 14 timeout 도입 후 통일 예정 |
| `HITL_TIMEOUT` | 동일 | 동일 |
| `AGENT_ERROR` | `_run_agent` agent 내부 예외 | `EXECUTION_ERROR` |

이 코드들은 `ErrorCodes` 클래스에 포함되지 않음 (진실 소스 = legacy 코드 직접).

---

## 2. 사용 예시 (진실 소스 = 코드)

```python
from api_v2.error_codes import ErrorCodes

# CONCURRENT_LIMIT_EXCEEDED emit
await conn_manager.broadcast_to_user(user_id, {
    "type": "error",
    **ErrorCodes.CONCURRENT_LIMIT_EXCEEDED,
    "conversation_id": conv_id,
    "turn_id": turn_id,
})

# 특정 상황 message 오버라이드
spec = dict(ErrorCodes.EXECUTION_ERROR)
spec["message"] = f"그래프 실행 실패: {str(e)}"
await conn_manager.broadcast_to_user(user_id, {"type": "error", **spec, ...})
```

---

## 3. Layer Guard 동작 상세

상세: `backend/api_v2/layer_guard.py::inspect_layer_output`.

Layer guard는 `_graph_runner_with_resume`의 `_broadcast_chunks` 내부에서 node_event 수신 직후 실행:

1. `inspect_layer_output(node, data)` → error 목록 반환
2. 각 error 에 대해:
   - `conn_manager.broadcast_to_user` 로 error 이벤트 fan-out
   - `append_guard_log` 로 JSONL (`logs/layer_guard.jsonl`) append
   - fatal인 경우 abort flag 설정 → `complete(aborted)` 후 return
   - warning인 경우 `guard_warnings` 리스트에 누적 → 최종 `complete.data.guard_warnings` 에 전달

### key-presence guard (R4 발견, I11-a)
각 layer inspector는 **기대 key 없으면 skip** — planning reject 경로 `{"response": {...}}` 에서 `PLANNING_EMPTY_PLAN` 오판 방지.

```python
if node == "planning":
    if "plan" not in data:
        return []   # reject 경로 등 — 검증 대상 아님
```

---

## 4. JSONL 로그 포맷 (layer guard 전용)

파일: `logs/layer_guard.jsonl` (append-only, `.gitignore` 대상)

```jsonl
{"ts":"2026-04-21T01:23:45Z","conv_id":"c1","turn_id":"t1","user_id":"demo","layer":"planning","code":"PLANNING_EMPTY_PLAN","severity":"fatal","message":"...","detail":{...},"state_summary":{"brand":"블루밍글로우","plan_todos":0,...}}
```

목적 (POC):
- 페어 누적 → 프롬프트 튜닝 / 규칙 추출 데이터
- Sprint 15 Memory 도입 시 DB로 이관 예정

---

## 5. 새 Error Code 추가 절차

### 5.1 체크리스트
- [ ] `backend/api_v2/error_codes.py::ErrorCodes` 에 ErrorSpec dict 추가
- [ ] `ErrorCodes.all_codes()` / `all_specs()` 에 추가 (문서 검증용)
- [ ] 이 문서 §1 해당 카테고리 표에 행 추가
- [ ] `21_WEBSOCKET_PROTOCOL_v1.2.md` §6 Error 카탈로그 표에 행 추가
- [ ] `20_INTERFACE_CONTRACT_v1.1.md` §5.1 표에 행 추가
- [ ] Layer guard인 경우 `layer_guard.py::inspect_layer_output` 에 로직 추가
- [ ] Unit 테스트: `test_layer_guard_unit.py` 또는 `test_error_format_unit.py` 에 케이스 추가
- [ ] 대시보드 `handleError(msg)` 에 특수 처리 필요한지 확인 (예: CONCURRENT_LIMIT은 alert)

### 5.2 코드 vs 문서 drift 방지

모든 error code는 `ErrorCodes.all_codes()` 에 한 번에 포함. Sprint 14+ 에서 Doc-Code Contract Test로 자동 검증 예정:

```python
# 예시 (Sprint 14 도입 예정)
def test_doc_has_all_error_codes():
    from api_v2.error_codes import ErrorCodes
    doc_text = open("docs/agent_specs/22_error_codes_v1.0.md").read()
    for code in ErrorCodes.all_codes():
        assert f"`{code}`" in doc_text, f"Doc missing: {code}"
```

---

## 6. 대시보드 처리 가이드

`dashboard/index.html::handleError(msg)` 는 code별 분기:

| Code | UI 동작 |
|------|---------|
| `INVALID_MESSAGE` | 채팅 에러 메시지만 |
| `CONCURRENT_LIMIT_EXCEEDED` | `alert("...")` + 채팅 메시지 |
| `EXECUTION_ERROR` | 채팅 에러 + `resetSendButton` |
| Layer guard (fatal) | 채팅 에러 + 후속 `complete(aborted)` 수신 시 resetSendButton |
| Layer guard (warning) | 채팅 warning 메시지만 (그래프 계속 진행) |

대시보드는 `severity === "fatal"` 일 때 버튼 리셋.

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-21 | 초안 — 8개 error code (Transport 2 + Runtime 1 + Layer Guard 5). 진실 소스 = `error_codes.py`. JSONL 로그 포맷, Dashboard 처리 가이드, 신규 추가 체크리스트 |
