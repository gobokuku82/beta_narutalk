# 01. chat_hub — NL 라우팅 + 11 화면 컨텍스트 + HITL

## 메타

| 항목 | 값 |
|---|---|
| 소속 팀 | (team_catalog 외부 — Cognitive Stage 내부) |
| handles_tasks | (Tool 카탈로그 아님 — Cognitive 로직) |
| Tool 수 | 0 implemented (Tool 이 아닌 로직 Layer) |
| 현재 구현률 | ✅ 기본 (NL 의도 분류) / 🟡 11 매트릭스 미반영 / 🟡 HITL 4 카테고리 미세분 |

## 입출력

- **입력**: (a) 마케터 NL query / (b) 화면 컨텍스트 payload `{source_screen, trigger, context}`
- **출력**: `structured_query` → Planning Layer 진입
- **다음 에이전트**: Planning (Stage 1 team → Stage 2 agent → Stage 3 todo)

## Tool 목록

본 카드는 **에이전트 아닌 Layer** — Tool 카탈로그 외부. 다만 Cognitive Stage 내부 로직 = 다음:

| 영역 | 역할 |
|---|---|
| `intent_router` | NL → 의도 분류 (LLM) |
| `hitl_category_classifier` | 4 카테고리 (조회/생성후/실행전/외부발송) |
| `screen_context_handler` | 11 화면 payload schema 처리 (Phase 5 신규) |

## 데이터 흐름

```
[사용자 NL] + [화면 버튼 컨텍스트]
       │
       ▼
  Cognitive Stage (cognitive_stage.py)
       │ LLM 의도 분류 + StructuredQuery 생성
       ▼
  Planning Layer (planner.py)
       │ Stage 1: team
       │ Stage 2: agent (planning_stage2_agent.yaml)
       │ Stage 3: todo (planning_stage3_todo.yaml)
       ▼
  Execution Layer
```

## HITL 카테고리 (D12 결정)

| 카테고리 | 게이트 시점 | 본 에이전트 책임 |
|---|---|---|
| 조회·자동 | 없음 (자동) | 분류 후 바로 Planning 진입 |
| 생성 후 | 결과 표시 후 [채택/거부/재생성] | Tool 실행 완료 후 |
| 실행 전 | 실행 직전 게이트 | 광고 운영 영향 액션 — 사전 승인 |
| 외부 발송 | 발송 직전 별도 | 클라이언트 발송 액션 — 별도 승인 |

→ Phase 5 진입 시 본 에이전트의 Tool 1 (`hitl_category_classifier`) 신규.

## Phase 진입

| Phase | 본 에이전트의 작업 |
|---|---|
| 현재 | ✅ 기본 NL 의도 분류 (Cognitive Stage 동작) |
| **Phase 5** | LLM 라우터 강화 + 11 매트릭스 prompt + HITL 4 카테고리 분기 게이트 |

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 | 변경 시 |
|---|---|---|
| Cognitive Stage 로직 | `backend/app/dream_agent/cognitive/cognitive_stage.py` | NL 의도 분류 로직 |
| Cognitive prompt | `llm_manager/prompts/cognitive.yaml` | 의도 분류 prompt |
| WebSocket payload | `backend/api_v2/routes/ws_agent.py` (필요 시) | 11 화면 컨텍스트 schema |
| Frontend 진입 | `frontend/src/api/wsAgent*.ts` + 11 화면 버튼 핸들러 | 컨텍스트 전달 |
| **HITLManager** | `backend/app/dream_agent/workflow_managers/hitl_manager/` | 4 카테고리 분기 |
| Spec 16 (예정) | `docs/agent_specs/16_chat_routing_v1.0.md` | 신규 spec |
| Spec 64 (예정) | `docs/agent_specs/64_screen_chat_mapping_v1.0.md` | 11 매트릭스 |
| ADR (Phase 5 진입 시) | `docs/agent_specs/adr/ADR-XXX.md` | 결정 박제 |

→ 상세 = [40 §3.C 에이전트 변경](../../agent_specs/40_agent_tool_lifecycle_v1.0.md).

## 참조 코드

- Cognitive Stage: [`backend/app/dream_agent/cognitive/`](../../../backend/app/dream_agent/cognitive/)
- HITLManager: [`backend/app/dream_agent/workflow_managers/hitl_manager/`](../../../backend/app/dream_agent/workflow_managers/hitl_manager/)
- WS Agent: [`backend/api_v2/routes/ws_agent.py`](../../../backend/api_v2/routes/ws_agent.py)
- Cognitive prompt: [`llm_manager/prompts/cognitive.yaml`](../../../backend/app/dream_agent/llm_manager/prompts/cognitive.yaml)

## 참조 spec

- [14 System Agent Overview](../../agent_specs/14_system_agent_overview_v1.0.md) — Cognitive Layer 책임
- [15 End-to-End Flow](../../agent_specs/15_end_to_end_flow_v1.0.md) — query → 응답 sequence
- [12 Manager Layer](../../agent_specs/12_manager_layer_v1.4.md) §3 HITL
- [21 WebSocket Protocol](../../agent_specs/21_WEBSOCKET_PROTOCOL_v1.5.md) — payload schema
- [17 §5 I/O 메커니즘](../../agent_specs/17_functions_to_io_v1.0.md) — Cognitive → Planning 흐름

## 참조 비전 (한국어 narrative)

- [agent_design/01_에이전트_채팅_허브.md](../../_claude/referrence/agent_design/01_에이전트_채팅_허브.md) — 채팅 허브 비전
- [agent_design/08_화면_채팅_연결흐름.md](../../_claude/referrence/agent_design/08_화면_채팅_연결흐름.md) — 11 매트릭스

## 📍 Mock vs 실API 분기

본 에이전트는 LLM 호출 의존 — Anthropic / OpenAI API. mock 불가 (LLM 응답이 본질).
- 환경변수: `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` ([backend/app/core/config.py](../../../backend/app/core/config.py))

## Drift / 결정

- **D11** 🟢 Acknowledged — Chat Hub 11 매트릭스 미구현. Phase 5 로 이연
- **D12** 🟢 Acknowledged — HITL 4 카테고리 미세분. Phase 5
- ADR (Phase 5 진입 시): 16/64 spec 작성

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안 |
