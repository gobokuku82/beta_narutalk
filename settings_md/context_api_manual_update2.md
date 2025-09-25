# LangGraph 0.6.x Context API 완전 가이드

## 1. 핵심 개념

### 1.1 Context API란?
LangGraph 0.6.x에서 도입된 새로운 패러다임으로, 기존 `config['configurable']` 패턴을 대체합니다.

**기존 방식 (0.5.x)**
```python
def node(state: dict, config: RunnableConfig):
    user_id = config.get("configurable", {}).get("user_id")  # 복잡한 중첩
```

**새로운 방식 (0.6.x)**
```python
def node(state: State, runtime: Runtime[Context]):
    user_id = runtime.context["user_id"]  # 깔끔한 타입 안전 접근
```

### 1.2 세 가지 컨텍스트 레벨

1. **Static Runtime Context** (runtime.context)
   - 실행 중 변경되지 않는 메타데이터
   - user_id, session_id, API keys 등
   - `context` 인자로 전달

2. **Dynamic Runtime Context** (State)
   - 실행 중 변경되는 워크플로우 데이터
   - 메시지, 중간 결과, 처리 상태 등
   - 노드 반환값으로 업데이트

3. **Cross-Conversation Context** (Store)
   - 대화 간 지속되는 장기 메모리
   - 사용자 선호도, 히스토리 등
   - `runtime.store`로 접근

## 2. 핵심 규칙

### 2.1 노드 시그니처 규칙
```python
# ✅ 올바른 시그니처
async def node(
    state: ConcreteState,  # TypedDict 타입 사용
    runtime: Runtime[ConcreteContext]  # Context 타입 명시
) -> Dict[str, Any]:  # 부분 업데이트만 반환
    return {"field": value}

# ❌ 잘못된 시그니처
async def node(state: dict, runtime: Runtime):  # 타입 없음
    return state  # 전체 state 반환
```

### 2.2 Context 접근 규칙
```python
# TypedDict 필수 필드 (존재 보장)
user_id = runtime.context["user_id"]  # [] 사용

# Optional 필드 (None 가능)
api_key = runtime.context.get("api_key")  # .get() 사용

# ❌ 절대 금지
user_id = runtime.context.user_id  # 속성 접근 금지
```

### 2.3 State 업데이트 규칙
```python
# ✅ 부분 업데이트만
return {
    "status": "completed",
    "result": processed_data
}

# ❌ 전체 state 반환 금지
return state
```

### 2.4 리듀서 패턴 규칙
```python
from typing import Annotated
from operator import add

class State(TypedDict):
    # 덮어쓰기 (기본)
    status: str
    
    # 리스트 누적
    results: Annotated[List[Dict], add]
    
    # 딕셔너리 병합
    metadata: Annotated[Dict, lambda a, b: {**a, **b}]
```

## 3. 그래프 생성 패턴

### 3.1 기본 구조
```python
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# 1. State와 Context 정의
class MyState(TypedDict):
    messages: Annotated[List[str], add]
    status: str

class MyContext(TypedDict):
    user_id: str
    session_id: str
    api_key: Optional[str]

# 2. 그래프 생성
workflow = StateGraph(
    state_schema=MyState,
    context_schema=MyContext
)

# 3. 노드 추가
workflow.add_node("process", process_node)

# 4. 컴파일
async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
    app = workflow.compile(checkpointer=checkpointer)

# 5. 실행
result = await app.ainvoke(
    initial_state,
    config={"configurable": {"thread_id": "123"}},
    context={"user_id": "user1", "session_id": "sess1"}
)
```

## 4. 계층적 아키텍처 패턴

### 4.1 Supervisor → Agent → Subgraph → Tool
```
Supervisor (Orchestrator)
    ├── Context: SupervisorContext (전체 조정 정보)
    ├── State: OrchestratorState (전체 워크플로우)
    │
    └── Agent (작업 실행)
        ├── Context: AgentContext (에이전트 실행 정보)
        ├── State: AgentState (에이전트 워크플로우)
        │
        └── Subgraph (세부 작업)
            ├── Context: SubgraphContext (필터링된 정보)
            ├── State: SubgraphState (세부 워크플로우)
            │
            └── Tool (실제 작업)
                └── 최소 필요 정보만 전달
```

### 4.2 Context 전파 규칙
```python
# Supervisor → Agent
agent_context = {
    "user_id": supervisor_context["user_id"],  # 상속
    "session_id": supervisor_context["session_id"],
    "original_query": supervisor_context["original_query"],
    # Agent 전용 추가
    "agent_specific": value
}

# Agent → Subgraph  
subgraph_context = {
    "user_id": runtime.context["user_id"],  # 필수만 전달
    "session_id": runtime.context["session_id"],
    # Subgraph 전용
    "db_paths": specific_paths
}
```

## 5. 실행 플로우

### 5.1 초기화
```python
# 1. Context 준비
context = {
    "user_id": "user123",
    "session_id": "sess456",
    "original_query": "질문내용"
}

# 2. Initial State 준비
initial_state = {
    "status": "pending",
    "messages": [],
    "results": []
}

# 3. Config 준비
config = {
    "configurable": {
        "thread_id": "thread_789"
    }
}
```

### 5.2 노드 실행
```python
async def node(state: State, runtime: Runtime[Context]) -> Dict:
    # 1. Context에서 필요한 정보 추출
    user_id = runtime.context["user_id"]
    
    # 2. State에서 현재 데이터 확인
    current_status = state["status"]
    
    # 3. 처리 로직 실행
    result = await process_data(...)
    
    # 4. 부분 업데이트 반환
    return {
        "status": "completed",
        "results": [result]  # 리듀서가 자동 누적
    }
```

## 6. Store API 사용

### 6.1 장기 메모리 관리
```python
async def node_with_memory(state: State, runtime: Runtime[Context]):
    # Store 접근
    namespace = ("users", runtime.context["user_id"])
    
    # 읽기
    user_prefs = await runtime.store.aget(namespace, "preferences")
    
    # 쓰기
    await runtime.store.aput(namespace, "last_query", state["query"])
    
    # 검색
    memories = await runtime.store.asearch(namespace)
```

## 7. 에러 처리

### 7.1 Context 에러 처리
```python
try:
    user_id = runtime.context["user_id"]  # Required
except KeyError:
    logger.error("Missing required context: user_id")
    return {"status": "failed", "error": "Missing user_id"}

# Optional field
api_key = runtime.context.get("api_key", "default_key")
```

### 7.2 State 에러 처리
```python
# 안전한 State 접근
messages = state.get("messages", [])
if not messages:
    return {"status": "no_messages"}
```

## 8. 베스트 프랙티스

### DO ✅
1. TypedDict로 모든 스키마 정의
2. 부분 State 업데이트만 반환
3. Context는 읽기 전용으로 취급
4. 리듀서로 자동 병합 활용
5. async/await 일관되게 사용

### DON'T ❌
1. config['configurable'] 사용
2. 전체 state 반환
3. runtime.context.field 속성 접근
4. State에 메타데이터 저장
5. Context 직접 수정 시도

## 9. 마이그레이션 체크리스트

### 0.5.x → 0.6.x
- [ ] config["configurable"] → runtime.context 변경
- [ ] 전체 state 반환 → 부분 dict 반환
- [ ] StateGraph에 context_schema 추가
- [ ] invoke에 context 인자 추가
- [ ] 리듀서 패턴 적용
- [ ] AsyncSqliteSaver import 경로 수정

## 10. 디버깅 팁

### Context 확인
```python
print(f"Context keys: {runtime.context.keys()}")
print(f"User: {runtime.context.get('user_id', 'Unknown')}")
```

### State 추적
```python
logger.info(f"State before: {state}")
result = process()
logger.info(f"Update: {result}")
```

### Checkpointer 상태
```python
snapshot = await app.aget_state(config)
print(f"Current: {snapshot.values}")
```
