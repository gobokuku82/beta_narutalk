# Human-in-the-Loop (HITL) Specification

**Version**: 2.0 | **Date**: 2026-02-06 | **Status**: Draft

---

## 1. Overview

Dream Agent V2의 Human-in-the-Loop 시스템 명세입니다. 사용자가 AI 에이전트의 실행 과정에 개입하여 검토, 수정, 승인할 수 있는 메커니즘을 정의합니다.

### 1.1 Design Goals

| Goal | Description |
|------|-------------|
| **Transparency** | 에이전트의 계획과 실행 과정을 투명하게 공개 |
| **Control** | 사용자가 언제든 개입하여 방향 수정 가능 |
| **Safety** | 비용이 드는 작업, 외부 API 호출 전 승인 |
| **Flexibility** | 다양한 개입 방식 지원 (승인, 수정, 건너뛰기, 취소) |
| **Non-blocking** | 타임아웃 시 기본 동작으로 진행 가능 |

### 1.2 HITL Types

| Type | Trigger | Description |
|------|---------|-------------|
| **Plan Review** | Planning 완료 후 | 전체 실행 계획 검토 및 승인 |
| **Clarification** | Cognitive 모호성 감지 | 의도 명확화를 위한 질문 |
| **Approval** | Todo requires_approval=true | 특정 작업 실행 전 승인 |
| **Input Request** | 추가 정보 필요 | 사용자 입력 요청 |
| **Pause** | 사용자 요청 | 실행 일시 정지 |
| **Verification** | 사용자 요청 | LLM이 중간 결과 검증 |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          HITL System Architecture                        │
└─────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                            Frontend                                     │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐   │
│  │  Plan Review   │  │  Approval      │  │  Input Form            │   │
│  │  Modal         │  │  Dialog        │  │  Components            │   │
│  └───────┬────────┘  └───────┬────────┘  └───────────┬────────────┘   │
│          └───────────────────┴───────────────────────┘                 │
│                               │                                         │
│                        WebSocket / REST                                │
└───────────────────────────────┼─────────────────────────────────────────┘
                                │
┌───────────────────────────────┼─────────────────────────────────────────┐
│                               │             Backend                     │
│  ┌────────────────────────────▼────────────────────────────────────┐   │
│  │                      HITL Manager                                │   │
│  │                                                                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │   │
│  │  │ Request      │  │ Response     │  │ Timeout              │   │   │
│  │  │ Handler      │  │ Handler      │  │ Manager              │   │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │   │
│  │         │                 │                      │               │   │
│  └─────────┼─────────────────┼──────────────────────┼───────────────┘   │
│            │                 │                      │                   │
│  ┌─────────▼─────────────────▼──────────────────────▼───────────────┐   │
│  │                     State Store (Redis/PostgreSQL)               │   │
│  │                                                                   │   │
│  │  session:{id}:hitl_pending → { request_id, type, data, timeout } │   │
│  │  session:{id}:hitl_history → [ ... ]                              │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                               │                                          │
│  ┌────────────────────────────▼────────────────────────────────────┐    │
│  │                    LangGraph Agent                               │    │
│  │                                                                  │    │
│  │  Cognitive ─┬─► Planning ─┬─► Execution ─┬─► Response            │    │
│  │             │             │              │                       │    │
│  │         interrupt     interrupt      interrupt                   │    │
│  │         (clarify)     (plan_review)  (approval)                  │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. LangGraph Integration

### 3.1 Interrupt Points

LangGraph의 `interrupt()` 함수를 사용하여 HITL 중단점을 구현합니다.

```python
# orchestrator/graph.py

from langgraph.graph import StateGraph
from langgraph.types import interrupt, Command

def build_graph() -> StateGraph:
    g = StateGraph(AgentState)

    g.add_node("cognitive", cognitive_node)
    g.add_node("planning", planning_node)
    g.add_node("execution_dispatcher", execution_dispatcher)
    g.add_node("execute_todo", execute_todo)
    g.add_node("response", response_node)

    # interrupt_before: 노드 실행 전 중단
    # interrupt_after: 노드 실행 후 중단
    return g.compile(
        checkpointer=checkpointer,
        interrupt_before=["planning"],  # Plan 생성 전 (실제로는 후)
    )
```

### 3.2 Interrupt in Node Functions

```python
# cognitive/cognitive_node.py

async def cognitive_node(state: AgentState) -> Command:
    result = await classify_intent(state["user_input"])

    # 모호성 감지 시 interrupt
    if result.requires_clarification:
        hitl_data = interrupt({
            "type": "clarification",
            "request_id": str(uuid4()),
            "question": result.clarification_question,
            "original_input": state["user_input"],
            "suggestions": result.suggestions
        })

        # 사용자 응답으로 재분류
        clarified_input = hitl_data.get("value")
        result = await classify_intent(clarified_input)

    return Command(
        update={"cognitive_result": result.model_dump()},
        goto="planning"
    )
```

```python
# planning/planning_node.py

async def planning_node(state: AgentState) -> Command:
    plan = await generate_plan(state["cognitive_result"])

    # Plan 검토 요청
    hitl_response = interrupt({
        "type": "plan_review",
        "request_id": str(uuid4()),
        "plan": plan.model_dump(),
        "message": "실행 계획을 검토해주세요."
    })

    action = hitl_response.get("action")

    if action == "reject":
        return Command(
            update={"error": "Plan rejected by user"},
            goto=END
        )
    elif action == "modify":
        instruction = hitl_response.get("instruction")
        plan = await modify_plan_with_llm(plan, instruction)

    return Command(
        update={"plan": plan.model_dump(), "todos": plan.todos},
        goto="execution_dispatcher"
    )
```

```python
# execution/execute_todo.py

async def execute_todo(state: dict) -> Command:
    todo = state["todo"]

    # 승인 필요한 작업
    if todo.requires_approval:
        hitl_response = interrupt({
            "type": "approval_request",
            "request_id": str(uuid4()),
            "todo_id": todo.id,
            "todo": todo.model_dump(),
            "reason": f"'{todo.tool}' 실행을 위해 승인이 필요합니다."
        })

        if hitl_response.get("action") == "skip":
            return Command(
                update={"todos": [todo.model_copy(update={"status": "skipped"})]},
                goto="execution_collector"
            )
        elif hitl_response.get("action") == "reject":
            return Command(
                update={"error": f"Todo {todo.id} rejected"},
                goto=END
            )

    # 실행
    result = await execute_tool(todo)

    return Command(
        update={
            "execution_results": {todo.id: result},
            "todos": [todo.model_copy(update={"status": "completed"})]
        }
    )
```

---

## 4. HITL Request Types

### 4.1 Plan Review

**Trigger**: Planning 레이어 완료 후 (interrupt_before 또는 노드 내 interrupt)

**Frontend UI**: 전체 Plan 카드뷰 + Mermaid 다이어그램

```typescript
interface PlanReviewRequest {
  type: "plan_review";
  request_id: string;
  plan_id: string;
  plan: {
    todos: TodoItem[];
    dependency_graph: Record<string, string[]>;
    estimated_duration_sec: number;
    estimated_cost_usd: number;
    mermaid_diagram: string;
  };
  message: string;
  options: ["approve", "modify", "reject"];
  timeout_sec: number;
}

interface PlanReviewResponse {
  request_id: string;
  action: "approve" | "modify" | "reject";
  instruction?: string;  // modify 시 자연어 수정 지시
  comment?: string;
}
```

### 4.2 Clarification

**Trigger**: Cognitive 레이어에서 모호성 감지

**Frontend UI**: 질문 + 텍스트 입력 또는 선택지

```typescript
interface ClarificationRequest {
  type: "clarification";
  request_id: string;
  original_input: string;
  ambiguity: string;
  question: string;
  input_type: "text" | "choice";
  suggestions?: string[];
  required: boolean;
  timeout_sec: number;
}

interface ClarificationResponse {
  request_id: string;
  value: string;
}
```

### 4.3 Approval Request

**Trigger**: Todo.requires_approval = true

**Frontend UI**: 작업 상세 정보 + 승인/건너뛰기/거부 버튼

```typescript
interface ApprovalRequest {
  type: "approval_request";
  request_id: string;
  todo_id: string;
  todo: {
    task: string;
    tool: string;
    estimated_cost_usd?: number;
    description?: string;
  };
  reason: string;
  options: ["approve", "skip", "reject"];
  timeout_sec: number;
}

interface ApprovalResponse {
  request_id: string;
  todo_id: string;
  action: "approve" | "skip" | "reject";
  reason?: string;
  comment?: string;
}
```

### 4.4 Input Request

**Trigger**: 실행 중 추가 정보 필요

**Frontend UI**: 동적 폼 (텍스트, 선택, 날짜 등)

```typescript
interface InputRequest {
  type: "input_request";
  request_id: string;
  field: string;
  question: string;
  input_type: "text" | "choice" | "number" | "date" | "multiselect";
  options?: Array<{ value: string; label: string }>;
  default_value?: any;
  validation?: {
    required?: boolean;
    min?: number;
    max?: number;
    pattern?: string;
  };
  timeout_sec: number;
}

interface InputResponse {
  request_id: string;
  field: string;
  value: any;
}
```

### 4.5 Pause Control

**Trigger**: 사용자가 Pause 요청

```typescript
interface PauseRequest {
  session_id: string;
  reason?: string;
}

interface PauseState {
  session_id: string;
  paused_at: string;
  paused_by: "user" | "system";
  current_todo?: string;
  completed_todos: string[];
  pending_todos: string[];
  can_resume: boolean;
}
```

### 4.6 Verification Request

**Trigger**: 사용자가 중간 결과 검증 요청

```typescript
interface VerificationRequest {
  session_id: string;
  verify_type: "intermediate_results" | "data_quality" | "progress";
  question?: string;
}

interface VerificationResponse {
  summary: string;
  quality_score: number;  // 0.0 ~ 1.0
  details: Record<string, any>;
  recommendations: string[];
  issues?: string[];
}
```

---

## 5. State Management

### 5.1 HITL State in AgentState

```python
class AgentState(TypedDict, total=False):
    # ... 기존 필드들 ...

    # HITL 상태
    hitl_pending: Optional[dict]  # 현재 대기 중인 HITL 요청
    hitl_history: Annotated[list, lambda a, b: a + b]  # HITL 이력 (append-only)
```

### 5.2 HITL Manager

```python
# workflow_managers/hitl_manager/manager.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import asyncio

@dataclass
class HITLRequest:
    request_id: str
    session_id: str
    type: str
    data: dict
    created_at: datetime
    timeout_at: datetime
    status: str = "pending"  # pending, completed, timeout, cancelled

class HITLManager:
    def __init__(self, redis_client, timeout_sec: int = 300):
        self.redis = redis_client
        self.default_timeout = timeout_sec

    async def create_request(
        self,
        session_id: str,
        request_type: str,
        data: dict,
        timeout_sec: Optional[int] = None
    ) -> HITLRequest:
        request = HITLRequest(
            request_id=str(uuid4()),
            session_id=session_id,
            type=request_type,
            data=data,
            created_at=datetime.utcnow(),
            timeout_at=datetime.utcnow() + timedelta(seconds=timeout_sec or self.default_timeout)
        )

        # Redis에 저장
        await self.redis.hset(
            f"session:{session_id}:hitl_pending",
            request.request_id,
            request.to_json()
        )

        # WebSocket으로 전송
        await self.notify_client(session_id, request)

        return request

    async def get_response(self, request_id: str, timeout_sec: int) -> Optional[dict]:
        """응답 대기 (blocking)"""
        key = f"hitl_response:{request_id}"

        # Redis BLPOP으로 응답 대기
        response = await self.redis.blpop(key, timeout=timeout_sec)

        if response:
            return json.loads(response[1])
        return None

    async def submit_response(
        self,
        session_id: str,
        request_id: str,
        response: dict
    ):
        """사용자 응답 처리"""
        # 응답 저장
        await self.redis.lpush(
            f"hitl_response:{request_id}",
            json.dumps(response)
        )

        # 대기 상태 제거
        await self.redis.hdel(f"session:{session_id}:hitl_pending", request_id)

        # 히스토리 기록
        await self.add_to_history(session_id, request_id, response)

    async def handle_timeout(self, request: HITLRequest) -> dict:
        """타임아웃 시 기본 동작"""
        default_actions = {
            "plan_review": {"action": "approve"},  # 자동 승인
            "approval_request": {"action": "skip"},  # 자동 건너뛰기
            "clarification": None,  # 취소
            "input_request": None  # 취소
        }

        return default_actions.get(request.type)
```

---

## 6. Timeout Handling

### 6.1 Timeout Configuration

```yaml
# config/hitl.yaml

hitl:
  timeouts:
    plan_review: 300        # 5분
    approval_request: 600   # 10분
    clarification: 180      # 3분
    input_request: 300      # 5분
    pause_max: 3600         # 1시간 (최대 일시정지)

  default_actions:
    plan_review: "approve"
    approval_request: "skip"
    clarification: "cancel"
    input_request: "cancel"

  notifications:
    warn_before_timeout_sec: 60  # 타임아웃 1분 전 경고
```

### 6.2 Timeout Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Timeout Flow                                   │
└─────────────────────────────────────────────────────────────────────┘

1. HITL 요청 생성
   ├── timeout_at 설정
   └── 타이머 시작

2. 타임아웃 1분 전
   └── 프론트엔드에 경고 메시지

3. 응답 없이 타임아웃 도달
   ├── 설정된 default_action 실행
   │   ├── plan_review: 자동 승인
   │   ├── approval_request: 자동 건너뛰기
   │   └── clarification/input: 세션 취소
   └── 히스토리에 "timeout" 기록

4. WebSocket으로 알림
   └── { type: "hitl_timeout", data: { request_id, action_taken } }
```

---

## 7. Pause & Resume

### 7.1 Pause Workflow

```
사용자: "pause" 명령
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  1. 현재 실행 중인 Todo 완료 대기                                    │
│     (실행 중이면 완료까지 대기, 새 Todo 시작 안 함)                   │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  2. 상태 저장 (Checkpointer)                                         │
│     • 완료된 todos                                                   │
│     • 남은 todos                                                     │
│     • execution_results                                              │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  3. WebSocket 알림                                                   │
│     { type: "hitl_paused", data: { ... } }                          │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  4. 사용자 액션 대기                                                 │
│     • 중간 결과 확인                                                 │
│     • Todo 수정/삭제                                                 │
│     • LLM 검증 요청                                                  │
│     • Resume / Cancel                                                │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Resume with Modifications

```python
# api/routes/hitl.py

@router.post("/hitl/{session_id}/resume")
async def resume_session(session_id: str, body: ResumeRequest):
    # 수정사항 적용
    if body.modifications:
        for mod in body.modifications:
            if mod.action == "skip_todo":
                await todo_manager.skip_todo(mod.todo_id)
            elif mod.action == "retry_todo":
                await todo_manager.retry_todo(mod.todo_id)
            elif mod.action == "update_todo":
                await todo_manager.update_todo(mod.todo_id, mod.params)

    # LangGraph 재개
    await agent.arun(
        {"session_id": session_id},
        config={"configurable": {"thread_id": session_id}}
    )

    return {"status": "resumed"}
```

---

## 8. Plan Modification

### 8.1 Natural Language Editing

```python
# planning/plan_editor.py

class PlanEditor:
    def __init__(self, llm_client):
        self.llm = llm_client

    async def edit_with_instruction(
        self,
        current_plan: Plan,
        instruction: str
    ) -> Plan:
        """자연어 지시로 Plan 수정"""

        prompt = f"""
        현재 Plan:
        {current_plan.to_yaml()}

        사용자 수정 지시:
        {instruction}

        다음 형식으로 수정된 Plan을 출력하세요:
        - todos: 수정된 Todo 리스트
        - changes: 변경 내역

        JSON 형식으로 응답:
        """

        response = await self.llm.generate(prompt)
        edits = json.loads(response)

        # 수정사항 적용
        updated_plan = current_plan.apply_edits(edits)

        # 새 버전 생성
        updated_plan.version += 1
        updated_plan.versions.append({
            "version": updated_plan.version,
            "change_type": "user_edit",
            "instruction": instruction,
            "changes": edits["changes"]
        })

        return updated_plan
```

### 8.2 Structured Editing

```python
# planning/plan_editor.py

class StructuredPlanEditor:
    async def apply_edits(self, plan: Plan, edits: List[EditAction]) -> Plan:
        updated_todos = list(plan.todos)

        for edit in edits:
            if edit.action == "add_todo":
                new_todo = TodoItem(
                    id=str(uuid4()),
                    task=edit.params["task"],
                    tool=edit.params["tool"],
                    status="pending",
                    depends_on=edit.params.get("depends_on", [])
                )
                # insert_after 위치에 삽입
                insert_idx = self._find_index(updated_todos, edit.params.get("insert_after"))
                updated_todos.insert(insert_idx + 1, new_todo)

            elif edit.action == "remove_todo":
                updated_todos = [t for t in updated_todos if t.id != edit.todo_id]
                # 의존성 업데이트
                self._update_dependencies(updated_todos, edit.todo_id)

            elif edit.action == "update_todo":
                for i, todo in enumerate(updated_todos):
                    if todo.id == edit.todo_id:
                        updated_todos[i] = todo.model_copy(update=edit.params)
                        break

            elif edit.action == "reorder":
                updated_todos = self._reorder(updated_todos, edit.params["order"])

        return plan.model_copy(update={
            "todos": updated_todos,
            "version": plan.version + 1
        })
```

---

## 9. Verification (LLM-based)

### 9.1 Verification Types

| Type | Description |
|------|-------------|
| `intermediate_results` | 중간 실행 결과 품질 검증 |
| `data_quality` | 수집된 데이터 품질 검사 |
| `progress` | 전체 진행 상황 평가 |
| `consistency` | Plan과 실행 결과 일관성 검사 |

### 9.2 Implementation

```python
# workflow_managers/hitl_manager/verifier.py

class LLMVerifier:
    async def verify(
        self,
        session_state: AgentState,
        verify_type: str,
        question: Optional[str] = None
    ) -> VerificationResult:

        context = self._build_context(session_state, verify_type)

        prompt = f"""
        {verify_type} 검증을 수행하세요.

        컨텍스트:
        {context}

        {f"사용자 질문: {question}" if question else ""}

        다음을 평가하세요:
        1. 현재 상태 요약
        2. 품질 점수 (0.0 ~ 1.0)
        3. 발견된 문제점
        4. 개선 권장사항

        JSON 형식으로 응답:
        {{
          "summary": "...",
          "quality_score": 0.85,
          "issues": [...],
          "recommendations": [...]
        }}
        """

        response = await self.llm.generate(prompt)
        return VerificationResult.model_validate_json(response)

    def _build_context(self, state: AgentState, verify_type: str) -> str:
        if verify_type == "intermediate_results":
            return f"""
            완료된 Todos: {[t for t in state.get('todos', []) if t['status'] == 'completed']}
            실행 결과: {state.get('execution_results', {})}
            """
        elif verify_type == "data_quality":
            return f"""
            수집된 데이터: {state.get('execution_results', {}).get('collector', {})}
            """
        # ...
```

---

## 10. Frontend Components

### 10.1 Plan Review Modal

```tsx
// components/hitl/PlanReviewModal.tsx

interface PlanReviewModalProps {
  request: PlanReviewRequest;
  onApprove: () => void;
  onModify: (instruction: string) => void;
  onReject: (reason: string) => void;
}

function PlanReviewModal({ request, onApprove, onModify, onReject }: PlanReviewModalProps) {
  const [modifyInstruction, setModifyInstruction] = useState("");

  return (
    <Modal open onClose={() => {}}>
      <ModalHeader>
        <h2>실행 계획 검토</h2>
        <TimeoutIndicator timeoutAt={request.timeout_at} />
      </ModalHeader>

      <ModalBody>
        <Tabs>
          <Tab label="Todo 목록">
            <TodoList todos={request.plan.todos} />
          </Tab>
          <Tab label="실행 흐름">
            <MermaidDiagram code={request.plan.mermaid_diagram} />
          </Tab>
          <Tab label="비용 예측">
            <CostEstimate
              duration={request.plan.estimated_duration_sec}
              cost={request.plan.estimated_cost_usd}
            />
          </Tab>
        </Tabs>
      </ModalBody>

      <ModalFooter>
        <Button onClick={onApprove} variant="primary">
          승인
        </Button>
        <Button onClick={() => setShowModifyInput(true)} variant="secondary">
          수정
        </Button>
        <Button onClick={() => onReject("")} variant="danger">
          거부
        </Button>
      </ModalFooter>

      {showModifyInput && (
        <ModifyInput
          value={modifyInstruction}
          onChange={setModifyInstruction}
          onSubmit={() => onModify(modifyInstruction)}
          placeholder="수정할 내용을 자연어로 입력하세요..."
        />
      )}
    </Modal>
  );
}
```

### 10.2 HITL Control Bar

```tsx
// components/hitl/HITLControlBar.tsx

function HITLControlBar({ sessionId, status }: { sessionId: string; status: string }) {
  const { pause, resume, cancel } = useAgentControl(sessionId);

  return (
    <ControlBar>
      {status === "running" && (
        <Button onClick={pause} icon={<PauseIcon />}>
          일시정지
        </Button>
      )}

      {status === "paused" && (
        <>
          <Button onClick={resume} icon={<PlayIcon />}>
            계속
          </Button>
          <Button onClick={() => setShowVerifyModal(true)}>
            결과 검증
          </Button>
        </>
      )}

      <Button onClick={cancel} variant="danger">
        취소
      </Button>
    </ControlBar>
  );
}
```

---

## 11. Error Handling

### 11.1 HITL-specific Errors

| Code | Description | Recovery |
|------|-------------|----------|
| `HITL_TIMEOUT` | 응답 타임아웃 | 기본 동작 실행 |
| `HITL_INVALID_RESPONSE` | 잘못된 응답 형식 | 재요청 |
| `HITL_REQUEST_EXPIRED` | 만료된 요청에 응답 | 무시, 현재 상태 반환 |
| `HITL_SESSION_NOT_PAUSED` | 일시정지 상태가 아님 | 상태 알림 |
| `HITL_MODIFICATION_FAILED` | Plan 수정 실패 | 원본 유지, 재시도 안내 |

### 11.2 Recovery Strategies

```python
# workflow_managers/hitl_manager/error_handler.py

class HITLErrorHandler:
    async def handle_error(self, error: HITLError, context: dict) -> dict:
        if isinstance(error, HITLTimeoutError):
            # 타임아웃: 기본 동작 실행
            default_action = self.get_default_action(context["request_type"])
            await self.notify_client(context["session_id"], {
                "type": "hitl_timeout",
                "data": {
                    "request_id": context["request_id"],
                    "action_taken": default_action
                }
            })
            return default_action

        elif isinstance(error, HITLModificationError):
            # 수정 실패: 원본 유지
            await self.notify_client(context["session_id"], {
                "type": "hitl_error",
                "data": {
                    "code": "MODIFICATION_FAILED",
                    "message": str(error),
                    "recoverable": True
                }
            })
            return {"action": "retry"}

        # 기타 에러
        raise error
```

---

## Related Documents

- [WEBSOCKET_PROTOCOL.md](WEBSOCKET_PROTOCOL.md) - WebSocket 프로토콜
- [API_SPEC.md](API_SPEC.md) - REST API 명세
- [SESSION_SPEC.md](SESSION_SPEC.md) - 세션 관리
- [ERROR_CODES.md](ERROR_CODES.md) - 에러 코드 체계

---

*Last Updated: 2026-02-06*
