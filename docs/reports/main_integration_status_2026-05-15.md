# OctorAD main 브랜치 통합 현황 보고서

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-05-15 |
| 브랜치 | `main` (`a5c4fc3` 기준) |
| 목적 | 프론트↔백엔드↔에이전트↔데이터 실제 연결 — 전체 스택 진단 + 정상화 경로 + 좀비/데드코드 방지 |
| 권위 계약 | **`docs/agent_specs/21_WEBSOCKET_PROTOCOL_v1.4.md`** (백엔드 = 완성, 이 스펙 준수) |
| 조사 범위 | 서버 부팅 → query 라운드트립 전 hop → mock/데드코드 전수 → 아키텍처 검증 (백엔드+프론트 전체) |

---

## 0. 한 줄 요약

**백엔드는 완성돼 있고 spec 21 을 정확히 따른다. 백본 아키텍처도 사용자 이해대로다.**
막힌 단 하나의 지점 = **프론트 WS 수신부**: 백엔드가 보낸 진짜 응답이 `ws.ts` 의 zod 검증(`WSMessageSchema.safeParse`)에서 100% 폐기된다. 프론트 `schemas.ts` 가 spec 21 과 다른 — 일부는 실재하지 않는 — 포맷으로 작성됐기 때문.
→ 할 일: **프론트 WS 레이어를 spec 21 에 정합 + 데드코드 삭제.** 백엔드는 무수정.

---

## 1. 서버 시작 — ✅ 맞음 (전제: PostgreSQL)

| 대상 | 확인 | 비고 |
|------|------|------|
| 백엔드 | `run_server_v2.py` → `api_v2.main:app`, **포트 8001**, Windows selector loop | `uv run python run_server_v2.py` |
| 프론트 | `vite` → **포트 5173**, `vite.config.ts` 가 `/api`·`/ws` → `localhost:8001` 프록시 | `pnpm dev` |
| 라우터 | `main.py` 에 health / `mock_data`(`/api/mock/*`) / `ws_agent`(`/ws/agent`) / `ws_hitl`(`/ws/hitl`) 등록 | |

**⚠️ 전제 — PostgreSQL 하드 의존**: `main.py` lifespan 이 `AsyncPostgresSaver` 연결 → 실패 시 `RuntimeError` 로 **서버 기동 거부**. graceful degradation 없음. 필요: `CHECKPOINT_DB_URI`, `OPENAI_API_KEY` (`.env`).

→ "서버 켜면 백엔드+프론트 켜짐"은 맞다. 단 **PostgreSQL 이 떠 있어야** 백엔드가 산다.

---

## 2. 쿼리 라운드트립 — 흐름 ✅, 정정 2개

흐름 자체(`SideChatPanel → ws.ts → /ws/agent → run_turn → 4-layer graph → broadcast → 프론트`)는 코드로 전 hop 확인됨.

### hop별 상태

| hop | 위치 | 상태 | 비고 |
|-----|------|------|------|
| FE query 송신 | `SideChatPanel.tsx:51` → `ws.ts:sendQuery` | ✅ | `{type:'query', conversation_id, turn_id, user_input, language}` — spec 21 §2.1 일치 |
| BE 수신/파싱 | `ws_agent.py` `/ws/agent` → `_parse_query_message` → `run_turn` | ✅ | 비동기 task 스폰 |
| 그래프 실행 | `run_turn` → `_graph_runner_with_resume` → `agent.astream` | ✅ | `system_graph/builder.py` 4노드 컴파일 |
| 4-Layer | cognitive → planning → execution → response | ✅ | |
| **데이터 접근** | execution 도구 → `load_mock_csv` → `data/mock/*.csv` **파일 직독** | ✅ | **정정 A 참고** |
| BE emit | `_chunk_to_event` / `_emit_complete` → `conn_manager.broadcast_to_user` | ✅ | spec 21 §2.2 포맷 |
| **FE 수신/파싱** | `ws.ts:32-36` `WSMessageSchema.safeParse` | ❌ **여기서 끊김** | **정정 B 참고** |
| FE store 반영 | `useAgent`/`useHitl` `handleWSMessage` | ❌ 도달 안 함 | 위에서 폐기되므로 |

### ⚠️ 정정 A — 데이터는 2갈래

사용자는 "agent + DATA" 한 갈래로 봤으나 실제로는:
- **에이전트 실행 도구**: `data/mock/*.csv` 를 **파일 I/O 로 직접** 읽음 (`load_mock_csv`). `/api/mock/*` HTTP 안 거침.
- **`/api/mock/*` HTTP**: **프론트 대시보드 페이지 전용**. 에이전트는 안 씀.
- 같은 CSV 를 두 경로가 각자 읽음 (POC 의도된 구조).

### ⚠️ 정정 B — 끊긴 지점 = 프론트 zod 파싱

직접 `ws_agent.py` emit ↔ `schemas.ts` 대조:
- 백엔드: `{type:'node_event', node:'cognitive', conversation_id, turn_id, data:<노드 State dict>}`
- 프론트 `NodeEventSchema`: `{type:'node_event', data:{turn_id, layer, node_name, status, timestamp}}`
- → `safeParse` 실패 → `ws.ts:34` `console.error` → `return` 으로 **메시지 폐기**.
- `complete`(`data.status` vs `data.reason`), `hitl_request`(`request_type` 가공 필드), `error`(평탄 vs 중첩), `paused`/`resumed`/`todo_*`(프론트 스키마 없음) — **전부 동일하게 폐기**.
- `connected` 만 통과 (ConnectedSchema 가 전부 optional).

→ **답은 백엔드에서 실제로 온다.** 단 프론트 현관(zod 게이트)에서 전량 버려져 화면에 도달 못 함. 콘솔에 `[ws] invalid message` 만 쌓임.

---

## 3. mock / stub / 데드코드 전수 — 4갈래로 분류

사용자 지시 "data 이외 mock 모두 삭제"는 **(C) 도구 stub 을 같이 날려 에이전트를 깨뜨릴 위험**이 있다. 4갈래로 본다:

| 분류 | 정체 | 위치 | 처리 |
|------|------|------|------|
| **(A) 데이터 mock** | `data/mock/*.csv` 12개 + `/api/mock/*` 12 endpoint + `load_mock_csv` | 백엔드 | **유지** — 의도된 POC 데이터 레이어, MVP 에서 실 API 교체 |
| **(B) 데드코드** | ① `backend/app/dream_agent/_old_v1/` (40여 파일, import 0건 — **최대 좀비**) ② `schemas.ts` `AgentMessageSchema`/`AgentMessageCompleteSchema` + `useAgent` 핸들러 (백엔드 미발행) ③ `useAgent` `streamingBuffer`/`appendStreamingChunk`/`finalizeMessage` (②와 연동) | 백엔드+프론트 | **삭제** |
| **(C) 도구 stub** | `team_catalog.yaml` `status: stub` 도구 ~30개 + `execution/mock_tools.py` `mock_result()` 폴백 | 백엔드 | **삭제 금지** — 의도된 POC 골격. 지우면 execution 깨짐. 추후 도구 실구현으로 *교체* |
| **(D) 프론트 stub** | `WorkflowPage` `SAMPLE_PLAN`, `PagePlaceholder` | 프론트 | 실 연결로 **교체** |
| **(검토)** | `ws_agent.py` legacy `start` 경로 + `_run_agent()` (Sprint 13 `query` 로 대체) | 백엔드 | Sprint 14 regression 후 제거 예정 — 지금은 보류 |

---

## 4. 실제 구동 아키텍처 — ✅ 확인

```
query → backend(FastAPI /ws/agent) → run_turn → 4-Layer graph
                                       ├ cognitive  (의도 추출 + 이력 주입)
                                       ├ planning   (StructuredQuery → Plan, HITL interrupt)
                                       ├ execution  (DAG phase 실행, 도구 → data/mock CSV 직독)
                                       └ response   (최종 응답 조립)
       ← broadcast (node_event/hitl_request/paused/resumed/complete/error)
       → frontend (WebSocket /ws/agent + /ws/hitl)
```
코드가 이 구조 그대로다. 사용자 이해 일치.

---

## 5. 정상 작동 단계

| Phase | 내용 | 범위 |
|-------|------|------|
| **0. 문서 정합** | 스펙 63(이번 세션에 생성한 frontend-backend contract 문서)의 WS 계약 부분을 spec 21 v1.4 에 맞춰 정정 — 또는 WS 계약은 21 단일 출처로 위임. 틀린 문서를 두면 또 틀리게 코딩함 | 문서만 |
| **1. 프론트 WS 스키마 재작성** | `schemas.ts` WS 섹션을 spec 21 그대로 — 평탄 envelope, `node`/`code` 최상위, `paused`/`resumed`/`layer_start`/`todo_start`/`todo_complete`/`progress` 추가, `agent_message`* 삭제, `error` 평탄화 | 프론트만 |
| **2. WS 핸들러 재배선 + 데드코드 삭제** | `useAgent`/`useHitl`/`useWebSocket` `handleWSMessage` 를 새 스키마에 맞춤. `node_event.data`(노드 State dict)에서 plan/structured_query/response 추출. `streamingBuffer` 계열 삭제 | 프론트만 |
| **3. 엔드투엔드 검증** | 실 백엔드(PostgreSQL+`run_server_v2.py`) + 프론트 띄우고 spec 21 §4 happy path 관통: query→node_event→hitl_request→승인→resumed→complete | 검증 |
| **4. WorkflowPage 실 plan 연결** | `SAMPLE_PLAN` **삭제** → `hitl_request.data.plan` 캔버스 연결. `todo_start`/`todo_complete`/`progress` 로 노드 실시간 상태 | 프론트만 |
| **5. 응답 표시 + `_old_v1/` 삭제** | `complete.data.response` 채팅 최종 표시 (spec 21 엔 토큰 스트리밍 없음). `_old_v1/` 디렉터리 삭제 | 프론트 + 백엔드 정리 |

> Phase 1~4 는 전부 프론트. 백엔드는 완성이라 무수정 → 회귀 위험이 백엔드로 안 번진다.

---

## 6. 좀비/데드코드 방지 원칙

1. **단일 계약 출처 = spec 21** — WS 포맷은 `21_WEBSOCKET_PROTOCOL_v1.4.md` 만 본다. 스펙 63 WS 부분은 어긋난 문서 → Phase 0 에서 먼저 정정.
2. **(C) 도구 stub 은 건드리지 않는다** — "data 이외 모두 삭제" 금지. stub 은 의도된 POC 골격. 삭제 대상은 (B) 데드코드뿐.
3. **가공 코드 완전 삭제** — `agent_message`* 스키마·핸들러는 spec 21 에 없음. "혹시 나중에" 두지 말고 삭제. (스트리밍은 백엔드 스펙 변경 후 별도 작업)
4. **stub 은 주석처리 X, 삭제/교체** — `SAMPLE_PLAN` 은 실 plan 연결 시 삭제.
5. **어댑터 금지** — 옛 포맷+신 포맷 동시 지원 레이어 두지 말 것. (memory: `feedback_no_mixed_codebases`)
6. **계약 변경 = 코드 + 문서 한 커밋** — `schemas.ts` 고치면 스펙 63 도 같은 커밋.
7. **`_old_v1/` 삭제는 import 0건 재확인 후** — 안전하지만 grep 으로 한 번 더 확인하고 삭제.
8. **단계마다 typecheck + 검증 + 커밋.** (memory: `feedback_test_no_resource_limit`, `feedback_commit_auto_on_completion`)

---

## 7. 권장 시작점

**Phase 0(스펙 63 정정) → Phase 1(프론트 WS 스키마 재작성)** 순.
- 계약 출처는 spec 21 단일. 백엔드 무수정. 프론트가 spec 21 에 맞춘다.
- Phase 1~2 끝나면 백본이 화면에서 실제로 흐른다 (query → node 이벤트 → HITL 모달 → 승인 → 완료).
- `_old_v1/` 삭제는 Phase 5 또는 별도 정리 커밋으로.

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-15 (초안) | **오진** — "백엔드가 스펙에서 드리프트" 로 잘못 판단 |
| 2026-05-15 (정정) | 사용자 정정 + spec 21 확인 → 진실 = 백엔드 완성·정확, 프론트 WS 레이어가 가공 계약 기준 |
| 2026-05-15 (전수 검증) | 서버 부팅~라운드트립 전 hop + mock/데드코드 전수 조사. ① PostgreSQL 하드 의존 ② 데이터 2갈래(에이전트=CSV 직독 / 대시보드=`/api/mock` HTTP) ③ 끊긴 지점=프론트 zod 파싱 ④ mock 4갈래 분류 — 도구 stub(C)은 삭제 금지 ⑤ `_old_v1/` 40여 파일 = 최대 좀비 |
