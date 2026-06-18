# 계획 — 작업 ⑪ client_id agent path 흐름 복구

> **상태**: **v3** (2차 적대적 검증 반영 = minor_fix_then_proceed). **사용자 승인 대기**.
> v1 → v2 → v3: 1차 16 + 2차 9 = 25 변경 반영. 3차 round 우회 (ROI 한계).

---

## 0. 메타

| 항목 | 값 |
|---|---|
| 작업 번호 | ⑪ |
| 작업명 | client_id agent path 흐름 복구 (helper-B 활성화) |
| 작성일 | 2026-05-31 (v3) |
| 패턴 | 작업 ⑤·⑨ (계획서 → 1차 → v2 → 2차 → v3 → 사용자 승인 → 단계별 commit) |
| 분량 | 작음 (백엔드 3 진입점 · frontend 2 파일 · 계약 spec 3 갱신 · 테스트 3 신규 = **11 파일**) |
| 후속 | 작업 ⑫ sprint15 broken 정리 (병렬 진행 가능 = **독립**, 의존 X — §6.5) + 작업 ⑬ 死코드 cleanup |

---

## 1. 배경 (본질 진단 인용)

작업 ⑩ 완료 후 본질 진단 workflow (9 agent 적대적 검증, 2026-05-31) Q3 인용:

> **가장 결정적 단절** — `BaseTool.fetch` 가 `context.client_id` 비면 fail-fast 인데, `AgentState`·`init_agent_state`·`ExecutionContext` 진입점 3 곳 모두 client 미흡. helper-B = pipeline path 에서만 작동, **agent path 에서 항상 실패**.

→ recent commit `52bf5ac`(①.6a) · `ebfd17a`(①.6c) 6 batch 의 90 tool client-free refactor 노력이 **agent path 에서 활성화 안 됨**. 사용자 원칙 [v1/v2 섞임 금지] 정합 (recent ①.x batch 마무리 본 작업).

---

## 2. 현황 spot-check (실 파일 박제, 1·2차 검증 통과)

### 2.1 BaseTool.fetch — 활성화 대기 (작동 OK)

[backend/app/dream_agent/tools/base_tool.py:29-42](../../backend/app/dream_agent/tools/base_tool.py#L29-L42):

```python
def fetch(self, source_id: str, context: ExecutionContext) -> Any:
    client = context.client_id
    if not client:
        raise ValueError("client 미지정: ExecutionContext.client_id 가 비어있음 ...")
    return self.ds.get(client, source_id)
```

→ 정상 작동, 진입점에서 client_id 채우면 됨.

### 2.2 ExecutionContext — 필드 이미 존재

[backend/app/dream_agent/models/execution.py:17-42](../../backend/app/dream_agent/models/execution.py#L17-L42):

```python
class ExecutionContext(BaseModel):
    session_id: str
    plan_id: str
    client_id: Optional[str] = None     # ← 이미 존재, 채우기만 하면 됨
    ...
```

### 2.3 채워야 할 3 진입점 (현재 누락)

> 1차 검증 결과 Executor 클래스 (executor.py:259-280) = **死코드**. §6.2 별 작업 분리.

| # | 파일:라인 | 현 코드 | 변경 |
|---|---|---|---|
| 1 | [agent_state.py:67-126](../../backend/app/dream_agent/states/agent_state.py#L67-L126) | `init_agent_state(*, user_input, conversation_id, turn_id, user_id=None, language="ko", ...)` — `client_id` 파라미터 없음 | `client_id: str \| None = None` 파라미터 추가 + AgentState 필드 추가 |
| 2 | [ws_agent.py:168·238](../../backend/api_v2/ws_agent.py#L168-L177) | `init_agent_state(...)` 호출 2 곳 (`_graph_runner` + `_graph_runner_with_resume`) — `client_id` 전달 없음 | `client_id=payload.get("client_id")` 전달 (2 곳) |
| 3 | [execution_stage.py:175](../../backend/app/dream_agent/execution/execution_stage.py#L175) | `context = ExecutionContext(session_id=session_id, plan_id=session_id)` | `client_id=state.get("client_id")` 전달 |

### 2.4 참조 패턴 (이미 작동 중)

| 위치 | 패턴 | 주석 |
|---|---|---|
| [api_v2/routes/dashboard1.py:104](../../backend/api_v2/routes/dashboard1.py#L104) | `ExecutionContext(session_id="api", plan_id="dashboard1", client_id=client)` | REST API path 정상 |
| [pipelines/runner.py:187](../../backend/app/pipelines/runner.py#L187) | `client_id=client` 전달 | pipeline path 정상 |
| 테스트 `backend/tests/dashboard1/` 16 파일 | `ExecutionContext(..., client_id="clumi")` | **mock raw 경로 의도 지정** (data/clumi/raw/), 운영 default 와 무관. 사용자 원칙 [feedback_convention_over_hardcoding] 정합. 별 cleanup 분리 |

### 2.5 ws_agent payload pass-through (단계 B 안전성 확인)

[backend/api_v2/ws_agent.py:572](../../backend/api_v2/ws_agent.py#L572) `_parse_query_message`:

```python
payload = {k: v for k, v in msg.items() if k not in ('type', 'conversation_id', 'turn_id')}
```

→ frontend 가 `client_id` 키 보내면 자동으로 payload 안에 포함. 단계 B `payload.get("client_id")` 안전.

### 2.6 resume_query Checkpointer 보존 (2차 검증 사전 확정)

[backend/api_v2/ws_agent.py:342](../../backend/api_v2/ws_agent.py#L342) `_graph_runner_with_resume`:

```python
if not resume_only:
    state = init_agent_state(...)           # resume_only=True 시 astream skip
    async for chunk in agent.astream(state, ...): ...
# resume_only=True → 위 astream skip, 아래 resume loop 가 agent.aget_state() 로 persisted state 읽음
```

→ resume_only 시 init_agent_state 가 호출되지만 astream 에 미주입 → Checkpointer 의 직전 turn client_id **자동 보존**. 단계 A 의 `if client_id is not None` 박제 정합. **별 commit 단계 불요** (§5 6 commit 단순화 근거).

### 2.7 도메인 client 호출 grep (무영향 확정)

- Cognitive·Planner·Response 노드: `state.get("client_id")` / `client_id` 호출 = **0 hit**
- workspace/base.py + data_sources/base.py ABC: 이미 client 필수 시그니처 = 변경 0
- hitl_manager + callback_manager: 도메인 client 무관 = 변경 0
- frontend `type: 'start'` 송신: **0 hit** → `_run_agent` legacy (ws_agent.py:685) = 死코드 (§6.6)
- 활성 `Executor()` 인스턴스화: **0 hit** (_old/_domains 만) → Executor 클래스 = 死코드 (§6.2)

---

## 3. 변경 명세 (단계별, 6 commit)

> 2차 검증: 단계 E (resume 정책) = 단계 A 자동 구현 → commit 단계 흡수. 7 commit → **6 commit** 단순화.

### 단계 A — AgentState + init_agent_state (1 파일)

**파일**: [backend/app/dream_agent/states/agent_state.py](../../backend/app/dream_agent/states/agent_state.py)

#### A.1 AgentState 필드 추가 (line 21-64)

```python
class AgentState(TypedDict, total=False):
    ...
    # ─── 입력 ───
    user_input: str
    language: str
    client_id: str                        # 진입점 명시 시 set, 미명시 시 키 자체 absent (total=False)
    ...
```

→ user_id (line 27) `str` 표기와 일관.

**컨벤션 박제** (2차 검증 발견): AgentState.client_id 접근 = **항상 `state.get("client_id")`** (TypedDict total=False 정합). 직접 인덱싱 `state["client_id"]` 금지 — sprint16+ 신규 노드 KeyError 함정 예방.

#### A.2 init_agent_state 파라미터 추가 (line 67-126)

```python
def init_agent_state(
    *,
    user_input: str,
    conversation_id: str,
    turn_id: str,
    user_id: str | None = None,
    client_id: str | None = None,         # ← 추가
    language: str = "ko",
    conversation_history: list[dict[str, Any]] | None = None,
    history_limit: int | None = None,
    require_review: bool | None = None,
) -> AgentState:
    ...
    state: AgentState = {
        ...
        "language": language,
        "trace": [],
    }
    if client_id is not None:              # ← line 124 `if require_review is not None` 패턴 일관
        state["client_id"] = client_id
    if require_review is not None:
        state["require_review"] = require_review
    return state
```

**원칙 정합**: [feedback_convention_over_hardcoding] — default "clumi" 강제 X. payload 명시 시만 채움. 빈 문자열 처리는 BaseTool.fetch (single source of truth) 위임.

**resume_query 정합 (2차 검증 사전 확정)**: §2.6 spot-check 결과 단계 A 의 `if client_id is not None` 박제가 resume_only=True 시나리오를 자동 흡수 (state 가 init_agent_state 호출되지만 astream 미주입 → Checkpointer 직전 client_id 보존). 별 단계 불요.

### 단계 B — ws_agent payload → init_agent_state (1 파일, 2 곳)

**파일**: [backend/api_v2/ws_agent.py](../../backend/api_v2/ws_agent.py)

#### B.1 `_graph_runner` (line 168-177)

```python
state = init_agent_state(
    user_input=payload.get("user_input", ""),
    conversation_id=conv_id,
    turn_id=turn_id,
    user_id=user_id,
    client_id=payload.get("client_id"),    # ← 추가
    language=payload.get("language", "ko"),
    ...
)
```

#### B.2 `_graph_runner_with_resume` (line 238-247)

동일 패턴 추가.

**원칙 정합**: payload 인터페이스 확장만 (run_turn 시그니처 불변 — `payload: dict` 안에 client_id 키 추가).

### 단계 C — execution_stage ExecutionContext (1 파일)

**파일**: [backend/app/dream_agent/execution/execution_stage.py:175](../../backend/app/dream_agent/execution/execution_stage.py#L175)

```python
context = ExecutionContext(
    session_id=session_id,
    plan_id=session_id,
    client_id=state.get("client_id"),     # ← 추가 (AgentState 에서 흐름, state.get 컨벤션)
)
```

**원칙 정합**: AgentState → ExecutionContext 흐름은 단방향 단순 전달.

### 단계 D — frontend payload + UI 가드 (2 파일)

> 2차 검증: `showToast` = 가공의 함수 (frontend 전역 0 hit). 단일 권장 = **disabled 패턴** (SideChatPanel.tsx:63 기존 silent return on !connected 패턴 일관). sonner toast 는 backup 만.

**파일 1**: [frontend/src/api/ws.ts:122-137](../../frontend/src/api/ws.ts#L122-L137) `sendQuery`

```ts
export function sendQuery(params: {
  conversationId: string;
  turnId: string;
  userInput: string;
  clientId?: string;                       // ← 추가
  language?: string;
  requireReview?: boolean;
}): boolean {
  return sendAgentMessage({
    type: 'query',
    conversation_id: params.conversationId,
    turn_id: params.turnId,
    user_input: params.userInput,
    client_id: params.clientId,            // ← 추가 (undefined 시 키 자체 송신 안 됨 — backend Optional 정합)
    language: params.language ?? 'ko',
    require_review: params.requireReview ?? true,
  });
}
```

**파일 2**: [frontend/src/features/agent/SideChatPanel.tsx:71](../../frontend/src/features/agent/SideChatPanel.tsx#L71) `handleSend`

```tsx
// 상단 import 추가
import { useCurrentClient } from '@/api/clients';

// 컴포넌트 안
const client = useCurrentClient();         // ← 추가 (api/clients.ts:43, 반환 string | undefined)

const handleSend = () => {
  if (!connected || !client || !input.trim()) return;   // ← silent return 단일 패턴
  sendQuery({
    conversationId, turnId, userInput: input,
    clientId: client,                      // ← 추가
    requireReview,
  });
};

// textarea
<textarea
  disabled={!connected || !client || !input.trim()}
  placeholder={client ? '메시지를 입력...' : 'client 미선택 — 좌측 상단 드롭다운에서 선택'}
  ...
/>
```

**원칙 정합**: 
- [project_poc_single_client_clumi] — useCurrentClient 가 자동 첫 client 반환 (clumi). undefined edge = clients API 로딩 중만 (UI disabled 로 사용자 noise 0).
- [feedback_user_beginner_recommend_actively] — disabled 단일 패턴 권장 (toast backup 옵션 제거).
- 기존 [SideChatPanel.tsx:63](../../frontend/src/features/agent/SideChatPanel.tsx#L63) `!connected` silent return 패턴 일관.

### 단계 E — 계약 spec 갱신 (3 파일, 필수)

> 2차 검증: sprint13 i6 spec 권장 → **필수** 격상 (init_agent_state 시그니처 변경 = i6 spec 핵심 박제, handoff drift 방지).

#### E.1 [docs/agent_specs/21_WEBSOCKET_PROTOCOL_v1.5.md](../agent_specs/21_WEBSOCKET_PROTOCOL_v1.5.md) §2.1 query schema

`client_id?: string` 옵션 필드 추가. 예시 메시지·테이블 갱신.

#### E.2 [docs/agent_specs/11_main_graph_state_v1.5.md](../agent_specs/11_main_graph_state_v1.5.md) §2.0 스키마 표

`client_id` 행 추가 + Writer=진입점(ws_agent) / Reader=execution_stage(→ExecutionContext) 매트릭스 명시.

#### E.3 [docs/_claude/checkpointer/sprint13_integration_i6_agent_state_spec.md](../_claude/checkpointer/sprint13_integration_i6_agent_state_spec.md) (또는 동등 spec)

init_agent_state 시그니처 박제 갱신 (`client_id: str | None = None` 파라미터 추가). 사용자 원칙 [feedback_code_status_markers] = handoff drift 방지 정합.

#### E.4 사후 검토 (필수 X)

- [docs/agent_specs/63_frontend_backend_contract_v1.0.md](../agent_specs/63_frontend_backend_contract_v1.0.md) — frontend payload 변경 박제
- ADR 신규 (client_id 흐름 결정) — 필요 시 진입

### 단계 F — 테스트 신규 (3 파일)

> 2차 검증: E2E 파일 위치 sprint15 → **sprint13** 이동 (sprint13 = ws_agent + state 통합 e2e 영역, sprint15 = 작업 ⑫ broken collector 격리. 회귀 baseline 추적성).

| 신규 파일 | 검증 |
|---|---|
| `backend/tests/sprint13/test_init_agent_state_client_id.py` | init_agent_state 가 client_id 받으면 state 에 포함, 안 받으면 키 자체 absent. is not None 패턴 |
| `backend/tests/sprint13/test_execution_stage_client_id_propagation.py` | AgentState.client_id → ExecutionContext.client_id 흐름 (mock executor) |
| **`backend/tests/sprint13/test_agent_path_helper_b_e2e.py`** (신규 E2E, sprint13) | ws_agent query → init_agent_state(client_id='clumi') → execution_stage → ExecutionContext → 실 helper-B tool (revenue_total 등) `self.fetch` 호출 → load 성공. negative = client_id 미전달 시 BaseTool.fetch ValueError 명확 메시지. fixture: `# clumi = POC 단일 client fixture, mock raw 의도 지정 (project_poc_single_client_clumi 정합)` |

### 단계 G — 회귀 검증 (commit 단계 아님, doc-only check)

각 commit 후 §7 회귀 baseline 명령 실행. 변동 0 확인.

---

## 4. 영향 범위 요약

### 4.1 변경

| 영역 | 변경 |
|---|---|
| 백엔드 | 3 파일 (agent_state.py · ws_agent.py · execution_stage.py) |
| 프론트엔드 | 2 파일 (api/ws.ts sendQuery · features/agent/SideChatPanel.tsx handleSend) |
| 계약 spec | 3 파일 (21_WEBSOCKET_PROTOCOL_v1.5 · 11_main_graph_state_v1.5 · sprint13 i6 spec) |
| 테스트 신규 | 3 파일 (init_agent_state · execution_stage · E2E helper-B in sprint13) |
| 테스트 회귀 검증 필요 | 5 곳 (sprint13 test_agent_state(11)·test_cognitive(7)·test_ws_agent_query_routing·test_ws_agent_parse + dashboard1 16 파일 spot-check) |
| **합** | **11 파일** |
| 문서 (사후 검토) | 63_frontend_backend_contract · ADR (신규 검토) |

### 4.2 무영향 (사용자 안심 박제)

| 영역 | 사유 |
|---|---|
| `workspace/base.py` + `data_sources/base.py` ABC | 이미 client 필수 시그니처 → 변경 0 |
| `hitl_manager` + `callback_manager` | 도메인 client 무관 → 변경 0 |
| Cognitive/Planner/Response 노드 | state.get('client_id') 호출 안 함 확인 → read 측 무영향 (TypedDict total=False 호환) |
| REST API path (dashboard1.py:104) + pipeline runner | 별 진입점 → 회귀 baseline 303/3 변동 0 |
| 박제 단일소스 사슬 9 곳 (compact v4 §0.1) | 무변경 → compact v5 작성 불요 |

---

## 5. 단계별 commit (6 commit, 회귀 baseline 유지)

> 2차 검증: Grep `helper.*fetch|self\.fetch` backend/tests/sprint13 backend/tests/sprint14 = **0 hit 재확인** → **5.1 안전 시나리오 사실상 확정**. 진입 직전 Grep 1 회 재확인 권장. 5.2 위험 시나리오 = 예비책 강등.

### 5.1 안전 시나리오 (확정 — 6 commit)

| commit | 단계 | 회귀 명령 |
|---|---|---|
| 1 | A — AgentState 필드 + init_agent_state 파라미터 | `uv run pytest backend/tests/sprint13/test_agent_state_unit.py backend/tests/sprint13/test_cognitive_prepare_prompt_unit.py -v` + dashboard1 |
| 2 | C — execution_stage ExecutionContext 전달 | sprint13+14 전체 (275/11/2) + dashboard1 (303/3) |
| 3 | B — ws_agent payload → init_agent_state (2 곳) | sprint13 ws_agent (test_ws_agent_query_routing_unit·test_ws_agent_parse_unit) + 전체 회귀 |
| 4 | D — frontend payload + UI 가드 (2 파일) | `cd frontend && pnpm exec tsc --noEmit` (exit 0) + 채팅 smoke (clumi 호출) |
| 5 | E — 21·11·i6 spec 갱신 (3 파일) | doc-only, 회귀 무관 |
| 6 | F — 신규 테스트 3 파일 (단위 2 + E2E 1, sprint13) | 신규 테스트 통과 + 전체 회귀 (303/3 + 275/11/2 + 17/54 불변) |

### 5.2 예비책 시나리오 (위험 발견 시)

A → (B+C atomic 1 commit) → D → E → F = 5 commit. e2e 회귀 위험 = sprint13+14 안 helper-B 호출 e2e 존재 시. 진입 직전 Grep 재확인 후 결정.

---

## 6. 미해결 결정 + 사용자 원칙 정합 검토

### 6.1 StructuredQuery 에 client_id 포함?

**옵션 (a) 권장 (본 작업 범위 외)** — Cognitive 산출은 "무엇" 만, "어느 client" 는 진입점 (payload → AgentState → ExecutionContext) 흐름.

**근거 강화 (1차 검증)**: Cognitive·Planner·Response 노드 grep 결과 도메인 client 참조 0 hit (LLM client 만 = `get_llm_client`). StructuredQuery 에 client 추가 = over-engineering 확정. multi-client (MVP+) 진입 시에도 무변경 — 한 turn 1 client = AgentState 흐름만으로 충분. (b) trigger = 한 turn 에서 여러 client 비교 시나리오 (MVP+ 외 H 시나리오).

### 6.2 executor.py:259-280 Executor 클래스 = 死코드

> **1차 검증 발견** — Grep 결과 활성 `Executor()` 인스턴스화 0 hit (`backend/_old/` · `backend/_domains/` 만 매치). 활성 entry = `execute_phase` 함수 (executor.py:226, execution_stage.py:228 호출).

**결정 = 작업 ⑬ 死코드 cleanup batch** (recent ①.x batch 연장). 사용자 원칙 [死코드 즉시 폐기] 정합. 작업 ⑪ 완료 직후 자동 이어짐 — 별 계획서 불요 (소규모 cleanup).

### 6.3 default client = "clumi" 강제?

**옵션 (a) default 없음** (본 계획) — payload 명시 시만 채움. 명시 안 하면 helper-B fail-fast.

**근거**: 사용자 메모리 [기본값은 있으면 안 되는거야] · [feedback_convention_over_hardcoding] · recent commit `52bf5ac` ①.6a "client 필수화" 일관. frontend useCurrentClient 가 자동 첫 client 반환하므로 UX 무영향 (disabled 가드로 undefined edge 차단).

### 6.4 frontend 정확한 진입점 (1차 검증으로 해소)

확정:
- [frontend/src/api/ws.ts:122-137](../../frontend/src/api/ws.ts#L122-L137) `sendQuery` (시그니처 + payload 키)
- [frontend/src/features/agent/SideChatPanel.tsx:71](../../frontend/src/features/agent/SideChatPanel.tsx#L71) `handleSend` (useCurrentClient + disabled 가드)
- [frontend/src/api/clients.ts:43](../../frontend/src/api/clients.ts#L43) `useCurrentClient()` (반환 `string | undefined`)

§3.D 참조.

### 6.5 작업 ⑫ (sprint15 broken collector 정리) 의존성

> **1차 검증 발견** — sprint15 broken 6 collector = `load_mock_csv` 직접 호출 (helper-B 아님) + client_id Grep 0 hit. 원인 = mock CSV 삭제 (33_collection.md:50) **이지 client_id 누락 아님**.

**정정**: 작업 ⑪ 선행 의무 → **독립 가능 (병렬 진행 가능)**.

작업 ⑫ 시나리오 분기:
- (a) **단순 폐기/skip** = ⑪ 무관
- (b) **재구현 (helper-B 패턴)** = ⑪ 선행 필요

작업 ⑫ 계획서 작성 시점 결정.

### 6.6 ws_agent.py:685 _run_agent (legacy 'start') = 死코드 (별 작업)

> **1차 검증 발견** — frontend api/ws.ts 에 `type: 'start'` 송신 0 hit. legacy Sprint 12 진입점, frontend 미사용.

**결정 = 작업 ⑬ 死코드 cleanup batch** (§6.2 Executor 와 동반). 사용자 원칙 [死코드 즉시 폐기] 정합.

### 6.7 resume_query 경로 client_id 정책 (사전 확정)

> 2차 검증 §2.6: ws_agent.py:342 `if not resume_only:` 분기로 astream skip 확인 → Checkpointer 가 직전 turn client_id 자동 보존. 단계 A `if client_id is not None` 박제로 자동 흡수. **별 단계 불요** (commit 5 단계 흡수).

### 6.8 multi-conversation client 격리 (2차 검증 박제)

**박제**: `useNavigation.selectedClientId` = browser-wide singleton (localStorage persist). 한 turn 1 client 캡처 시점 = `handleSend` 시점 → in-flight turn 의 client_id 는 backend state 박제로 격리됨. 사용자가 turn 중간에 client 전환 시 다음 turn 부터 신규 client 적용 — **POC 의도된 동작**. multi-conversation 동시 진행 시 격리는 MVP+ 외 시나리오.

---

## 7. 회귀 baseline 검증 명령

```bash
# 1. sprint13 agent_state + cognitive 회귀
uv run pytest backend/tests/sprint13/test_agent_state_unit.py backend/tests/sprint13/test_cognitive_prepare_prompt_unit.py -v
# 기대: 11 + 7 = 18 호출 모두 통과 (Optional 파라미터 호환)

# 2. sprint13+14 분석 team 회귀 (불변)
uv run pytest backend/tests/sprint13 backend/tests/sprint14 -q
# 기대: 275 passed / 11 failed (HITL) / 2 skipped — 변동 0

# 3. dashboard1 영역 회귀 (불변)
uv run pytest backend/tests/{pipelines,dashboard1,data_sources,workspace,permissions,ml_models} -q
# 기대: 303 passed / 3 failed (pyarrow) — 변동 0

# 4. sprint15 (불변)
uv run pytest backend/tests/sprint15 -q
# 기대: 17 passed / 54 failed — 변동 0 (작업 ⑫ 에서 해결)

# 5. frontend type-check
cd frontend && pnpm exec tsc --noEmit
# 기대: exit 0

# 6. agent path helper-B smoke (신규 E2E)
uv run pytest backend/tests/sprint13/test_agent_path_helper_b_e2e.py -v
# 기대: ws_agent → helper-B 흐름 통과 (clumi 호출 성공) + negative (ValueError) 검증

# 7. sprint13 resume 회귀 (단계 A 자동 흡수 확인)
uv run pytest backend/tests/sprint13/test_resume_only_unit.py backend/tests/sprint13/test_run_turn_shell_unit.py -v
# 기대: resume_query client_id 보존 통과 (Checkpointer 직전 turn 보존)

# 8. 진입 직전 spot-check (commit 1 전)
grep -rn "self\.fetch\|\.fetch(" backend/tests/sprint13 backend/tests/sprint14 | grep -v test_
# 기대: 0 hit → §5.1 안전 시나리오 확정, 결과 hit 있으면 §5.2 위험 시나리오 전환
```

---

## 8. rollback

단계 commit 단위 git revert 가능:
- A revert → init_agent_state 파라미터 제거 (sprint13 회귀만 영향)
- B revert → payload 전달 제거 (frontend 변경 무관)
- C revert → ExecutionContext.client_id 미전달 (helper-B agent path 다시 fail-fast)
- D revert → frontend payload 키 + UI 가드 제거
- E revert → 21·11·i6 spec 갱신 제거 (doc-only)
- F revert → 신규 테스트 3 파일 제거

**rollback 순서**: F → E → D → B → C → A (commit 역순). POC 단순화 = `git reset` 통째 가능.

전체 revert 시 작업 ⑩ 종료 시점 baseline (303/3 + 275/11/2 + 17/54) 회귀.

---

## 9. 검증 체크리스트 (사용자 승인 전 final)

### 9.1 정확성 (1·2차 검증 통과)
- [x] 영향 3 백엔드 + 2 frontend + 3 spec + 3 신규 테스트 = 11 파일 정확
- [x] 단계 A·B·C·D·E·F 의 코드 박제 실 파일과 일치
- [x] frontend useCurrentClient (api/clients.ts:43) + SideChatPanel.tsx:71 + api/ws.ts:122 정확
- [x] sonner toast 라이브러리 정합 (showToast 가공 함수 제거, disabled 단일 패턴)

### 9.2 완전성 (1·2차 검증 통과)
- [x] StructuredQuery 결정 (a) 근거 정합 (Cognitive·Planner·Response client 참조 0)
- [x] Executor 死코드 (§6.2) 작업 ⑬ 분리
- [x] _run_agent legacy (§6.6) 작업 ⑬ 분리
- [x] 21·11·i6 spec 갱신 = 필수 (commit E 동반)
- [x] resume_query 정합 확인 (§2.6 spot-check) → 단계 A 자동 흡수

### 9.3 실행 안전 (2차 검증 통과)
- [x] commit 순서 5.1 안전 시나리오 6 commit 확정 (Grep 0 hit 재확인)
- [x] Optional 파라미터 정합 (기존 호출 호환)
- [x] 회귀 baseline 변동 없음 (303/3 + 275/11/2 + 17/54)
- [x] frontend UI 가드 (disabled 단일 패턴, useCurrentClient undefined edge)
- [x] state.get("client_id") 컨벤션 박제 (KeyError 함정 예방)

### 9.4 사용자 원칙 정합
- [x] POC 단계 적합 (over-engineering 없음, silver bullet 없음)
- [x] convention 우선 · default 없음 · 死코드 폐기 · v1/v2 섞임 X
- [x] 한 turn ONE 변경 원칙 (단계 commit 단위)
- [x] 전문가 단일 권장 (옵션 surface 자제)

### 9.5 의존성
- [x] 작업 ⑫ 의존성 정정 (병렬 가능) 박제
- [x] 작업 ⑬ 死코드 cleanup 후속 박제 (Executor + _run_agent legacy)
- [x] 박제 단일소스 사슬 9 곳 무영향 확정 (compact v5 불요)

---

## 10. 참조

- **본질 진단 workflow** (2026-05-31, 9 agent) — Q3 client_id agent path 단절
- **1차 적대적 검증 workflow** (2026-05-31, 5 agent, 4 perspective) — minor_fix, 16 항목 → v2
- **2차 적대적 검증 workflow** (2026-05-31, 5 agent, 4 perspective) — minor_fix_then_proceed, 9 항목 → v3 + ROI 한계 (3차 우회)
- [ADR-022](../agent_specs/adr/ADR-022_data_source_workspace_layer_separation.md) — DataSource DI helper-B 패턴
- 메모리 [project_poc_single_client_clumi] — POC 단일 client clumi
- 메모리 [tool_data_agent_separation] — P1 tool 순수, data 별도 진입점
- 메모리 [feedback_convention_over_hardcoding] — default 강제 X
- 메모리 [feedback_no_mixed_codebases] — recent ①.x batch 마무리
- 메모리 [기본값은 있으면 안 되는거야] (compact v4 §6.3) — default 폐기
- 메모리 [死코드 즉시 폐기] — Executor·_run_agent legacy 분리
- 메모리 [feedback_user_beginner_recommend_actively] — 전문가 단일 권장 (disabled 단일 패턴)
- 메모리 [feedback_code_status_markers] — handoff drift 방지 (i6 spec 갱신 필수)
- 메모리 [검증 ROI 감소] — 3차 round 우회 정합
- recent commit `52bf5ac`(①.6a) · `ebfd17a`(①.6c) · `62f46b2`(①.5) · `ba04bc0`(①.4) · `8dee1ec`(①.3) — runner·pipeline client 필수화
- 작업 ⑤·⑨ 계획서 패턴 (1차 → v2 → 2차 → v3 → 승인 → commit)
- [compact v4 §0](session_compact_recovery_2026-05-31_v4.md) — 박제 단일소스 사슬 9 곳

### 10.1 docs 영향 우선순위

| # | 문서 | 우선 |
|---|---|---|
| 1 | 21_WEBSOCKET_PROTOCOL_v1.5 §2.1 | **필수** (계약 변경) |
| 2 | 11_main_graph_state_v1.5 §2.0 | **필수** (state 계약) |
| 3 | sprint13_integration_i6_agent_state_spec.md | **필수 (commit E 동반)** — init_agent_state 시그니처 핵심 박제 |
| 4 | 63_frontend_backend_contract_v1.0 | 권장 (frontend payload 변경) |
| 5-9 | 32/40/41/30/ADR-022/ADR-027/17 | 사후 검토 |
| - | test_doc_code_contract.py DC2 | 갱신 불요 (이름 단위 contract) |

---

## 11. 변경 이력

| 버전 | 날짜 | 내용 |
|---|---|---|
| v1 | 2026-05-31 | 최초 작성 (본질 진단 Q3 기반) |
| v2 | 2026-05-31 | 1차 적대적 검증 (5 agent, 4 perspective) minor_fix 반영. must 7 + should 5 + optional 4 = 16 변경 |
| v3 | 2026-05-31 | 2차 적대적 검증 (5 agent, 4 perspective) minor_fix_then_proceed 반영. must 3 (showToast 정정·commit 단순화 6→5+1=6·E2E sprint13 이동) + should 3 (i6 필수 격상·5.1 확정·state.get 컨벤션) + optional 3 (E2E fixture 박제·死코드 cleanup 작업 ⑬·multi-conversation 격리) = 9 변경. **3차 round 우회 (ROI 한계 권장)** |

---

## 12. 사용자 결정 5 (승인 surface)

> 2차 검증 ROI 한계 도달, 3차 round 우회 권장. v3 즉시 commit 진입 OK. 사용자 결정 5 항목 (모두 전문가 단일 권장 명시):

| # | 결정 | 권장 |
|---|---|---|
| 1 | 작업 ⑪ vs ⑫ 순서 | **⑪ 먼저** (recent ①.x batch 활성화 가장 시급, 본질 진단 Q3 해소). ⑫ 는 별 계획서 작성 시 (a) 단순 폐기/skip vs (b) 재구현 분기 결정. 병렬 진행 충돌 0 |
| 2 | §3.D frontend UI 가드 패턴 | **disabled 단일 패턴** (SideChatPanel.tsx:63 기존 silent return 일관). showToast 가공 함수 제거 (type-check 실패 직결) |
| 3 | §5 commit 시나리오 | **5.1 안전 시나리오 6 commit** (Grep 0 hit 재확인). 진입 직전 1 회 재확인 후 확정. 5.2 위험 시나리오 = 예비책 강등 |
| 4 | 死코드 cleanup 후속 작업 번호 | **작업 ⑬** (Executor + _run_agent legacy 동반 폐기, recent ①.x batch 연장 패턴). 별 계획서 불요 (소규모) |
| 5 | sprint13 i6 spec 갱신 우선순위 | **필수 격상 (commit E 동반)** — init_agent_state 시그니처 = i6 spec 핵심 박제, handoff drift 방지 |

**기본 = 모든 권장 적용 진입**. 사용자 다른 결정 시 surface 후 v4 갱신 (3차 round 가치 < cost — 우회 권장).

---

**상태**: v3 작성 완료. **다음 단계**: 사용자 승인 → 단계 A (commit 1) 진입.
