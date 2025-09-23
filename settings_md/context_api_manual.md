# LangGraph 0.6.x Context API 완전 가이드

## 🚨 중요: LangGraph 0.6.x의 대규모 변경사항
LangGraph 0.6.x는 이전 버전과 **완전히 다른 아키텍처**를 도입했습니다. 특히 Context API는 기존 `config['configurable']` 패턴을 대체하는 핵심 기능입니다.

## Context API란?

Context API는 세 가지 유형의 컨텍스트를 관리합니다:

1. **Static Runtime Context**: 실행 중 변경되지 않는 데이터 (사용자 정보, API 키 등)
2. **Dynamic Conversation Context**: 대화 내에서 진화하는 상태 (메시지, 중간 결과)
3. **Cross-Conversation Context**: Store API를 통한 장기 메모리

## 핵심 변경사항 비교

### ❌ 이전 방식 (0.5.x 이하)
```python
# 노드가 전체 state를 받고 반환
def my_node(state: dict, config: RunnableConfig) -> dict:
    # config에서 설정값 추출
    user_id = config.get("configurable", {}).get("user_id")
    messages = state["messages"]
    
    # 전체 state를 복사하고 수정
    new_state = state.copy()
    new_state["messages"] = messages + [new_message]
    return new_state  # 전체 state 반환

# 실행 시
app.invoke(state, {"configurable": {"user_id": "123"}})
```

### ✅ 새로운 방식 (0.6.x Context API)
```python
from langgraph.runtime import Runtime
from typing_extensions import TypedDict

# Context 스키마 정의 (실행 시 전달될 정적 데이터)
class ContextSchema(TypedDict):
    user_id: str
    api_key: str
    environment: str

# 노드는 Runtime 객체를 통해 context 접근
def my_node(state: State, runtime: Runtime[ContextSchema]) -> dict:
    # runtime.context로 접근
    user_id = runtime.context.get("user_id")
    
    # 변경된 부분만 반환 (자동 머지)
    return {"messages": [new_message]}  # 부분 업데이트만!

# 그래프 생성 시 context_schema 지정
graph = StateGraph(State, context_schema=ContextSchema)

# 실행 시 context 인자로 전달
app.invoke(
    {"messages": []}, 
    context={"user_id": "123", "api_key": "sk-...", "environment": "prod"}
)
```

## Context API 상세 가이드

### 1. Runtime Context 패턴

```python
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

# State 정의 (그래프 내부에서 변경되는 데이터)
class State(TypedDict):
    messages: Annotated[list, add_messages]
    current_step: str
    results: dict

# Context 정의 (실행 중 변경되지 않는 설정)
class AppContext(TypedDict):
    user_id: str
    user_name: str
    api_keys: dict
    feature_flags: dict
    max_retries: int

# 노드에서 Runtime 사용
async def smart_agent_node(
    state: State, 
    runtime: Runtime[AppContext]
) -> dict:
    """Runtime을 활용한 스마트 노드"""
    
    # Context 데이터 접근
    user_name = runtime.context["user_name"]
    openai_key = runtime.context["api_keys"].get("openai")
    
    # Feature flag 확인
    if runtime.context["feature_flags"].get("use_gpt4"):
        model = "gpt-4"
    else:
        model = "gpt-3.5-turbo"
    
    # 실제 로직
    response = f"안녕하세요 {user_name}님, {model}을 사용합니다."
    
    # 부분 state 업데이트
    return {
        "messages": [AIMessage(content=response)],
        "current_step": "greeted"
    }

# 그래프 구성
workflow = StateGraph(State, context_schema=AppContext)
workflow.add_node("agent", smart_agent_node)
```

### 2. Store API - 장기 메모리 관리

```python
from langgraph.store import InMemoryStore

# Store 초기화
store = InMemoryStore()

# 노드에서 Store 사용
async def memory_aware_node(
    state: State, 
    runtime: Runtime[AppContext],
    store: InMemoryStore  # Store 주입
) -> dict:
    user_id = runtime.context["user_id"]
    
    # 사용자별 메모리 저장/조회
    namespace = ("users", user_id)
    
    # 기존 메모리 조회
    memories = await store.asearch(namespace)
    
    # 새로운 메모리 추가
    await store.aput(
        namespace, 
        "last_interaction",
        {
            "timestamp": datetime.now().isoformat(),
            "summary": state["messages"][-1].content
        }
    )
    
    # 사용자 선호도 업데이트
    preferences = await store.aget(namespace, "preferences") or {}
    preferences["last_topic"] = extract_topic(state["messages"])
    await store.aput(namespace, "preferences", preferences)
    
    return {"messages": [response_with_memory]}
```

### 3. AsyncSqliteSaver 전체 구현

```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import StateGraph, START, END
import asyncio

# 완전한 비동기 앱 구현
class ChatState(TypedDict):
    messages: Annotated[list, add_messages]
    user_context: dict
    tool_calls: list

class ChatContext(TypedDict):
    user_id: str
    session_id: str
    permissions: list

async def create_app():
    """AsyncSqliteSaver를 사용한 앱 생성"""
    
    # 노드 정의
    async def process_message(state: ChatState, runtime: Runtime[ChatContext]) -> dict:
        # Context 활용
        can_use_tools = "use_tools" in runtime.context.get("permissions", [])
        
        if can_use_tools:
            # 도구 사용 로직
            tool_calls = plan_tool_calls(state["messages"][-1])
            return {"tool_calls": tool_calls}
        
        # 일반 응답
        return {"messages": [AIMessage(content="도구 사용 권한이 없습니다.")]}
    
    async def execute_tools(state: ChatState) -> dict:
        results = []
        for tool_call in state["tool_calls"]:
            result = await execute_tool(tool_call)
            results.append(result)
        return {"messages": results}
    
    # 그래프 구성
    workflow = StateGraph(ChatState, context_schema=ChatContext)
    workflow.add_node("process", process_message)
    workflow.add_node("tools", execute_tools)
    
    # 조건부 엣지
    def should_use_tools(state: ChatState) -> str:
        return "tools" if state.get("tool_calls") else END
    
    workflow.add_edge(START, "process")
    workflow.add_conditional_edges("process", should_use_tools)
    workflow.add_edge("tools", END)
    
    # AsyncSqliteSaver로 컴파일
    async with AsyncSqliteSaver.from_conn_string("chat.db") as checkpointer:
        return workflow.compile(checkpointer=checkpointer)

# 실행 예제
async def main():
    app = await create_app()
    
    # Context와 함께 실행
    context = {
        "user_id": "user123",
        "session_id": "session456",
        "permissions": ["use_tools", "access_memory"]
    }
    
    config = {"configurable": {"thread_id": "conv_001"}}
    
    # 첫 번째 메시지
    result1 = await app.ainvoke(
        {"messages": [HumanMessage(content="날씨 알려줘")]},
        config=config,
        context=context  # Context 전달!
    )
    
    # 두 번째 메시지 (이전 대화 기억)
    result2 = await app.ainvoke(
        {"messages": [HumanMessage(content="더 자세히 알려줘")]},
        config=config,
        context=context
    )

asyncio.run(main())
```

### 4. 리듀서 패턴 완전 가이드

```python
from typing import Annotated
from operator import add

# 다양한 리듀서 예제
class AdvancedState(TypedDict):
    # 기본 덮어쓰기
    current_value: int
    
    # 리스트 추가 (add 연산자)
    history: Annotated[list, add]
    
    # 메시지 전용 리듀서
    messages: Annotated[list, add_messages]
    
    # 커스텀 리듀서 - 최대값 유지
    max_score: Annotated[float, lambda a, b: max(a, b)]
    
    # 커스텀 리듀서 - 딕셔너리 머지
    metadata: Annotated[dict, lambda a, b: {**a, **b}]
    
    # 커스텀 리듀서 - 고유값만 유지
    unique_items: Annotated[set, lambda a, b: a.union(b)]

def node_with_reducers(state: AdvancedState) -> dict:
    # 각 필드별로 리듀서가 자동 적용
    return {
        "current_value": 42,  # 덮어쓰기
        "history": [state["current_value"]],  # 리스트에 추가
        "messages": [AIMessage(content="응답")],  # 메시지 추가
        "max_score": 95.5,  # 기존값과 비교해서 큰 값 유지
        "metadata": {"new_key": "value"},  # 딕셔너리 머지
        "unique_items": {"item1", "item2"}  # 집합에 추가
    }
```

### 5. Input/Output 스키마 분리 패턴

```python
# 사용자 입력 스키마 (간단)
class UserInput(TypedDict):
    question: str
    language: str

# 출력 스키마 (필요한 것만)
class BotOutput(TypedDict):
    answer: str
    confidence: float

# 내부 작업 스키마 (복잡한 전체 상태)
class InternalState(UserInput, BotOutput):
    messages: Annotated[list, add_messages]
    intermediate_steps: list
    tool_results: dict
    thinking_process: str

# 스키마 분리로 그래프 생성
workflow = StateGraph(
    state_schema=InternalState,
    input_schema=UserInput,    # 입력은 간단하게
    output_schema=BotOutput,    # 출력도 필요한 것만
    context_schema=ChatContext  # Context 스키마
)

# 사용자는 간단한 입력만
result = await app.ainvoke(
    {"question": "파리의 날씨는?", "language": "ko"},
    context={"user_id": "123"}
)
# 결과도 BotOutput 형태로만 받음
print(result)  # {"answer": "...", "confidence": 0.95}
```

## 실전 팁 & 주의사항

### 1. Context vs State 구분
```python
# ✅ Context에 넣을 것 (변경되지 않는 설정)
context = {
    "user_id": "123",
    "api_keys": {"openai": "sk-..."},
    "feature_flags": {"new_ui": True},
    "rate_limits": {"max_requests": 100}
}

# ✅ State에 넣을 것 (변경되는 상태)
state = {
    "messages": [...],
    "current_step": "processing",
    "accumulated_tokens": 1500,
    "tool_results": {...}
}
```

### 2. 마이그레이션 체크리스트
```python
# 1단계: config['configurable'] 찾기
# OLD: config["configurable"]["key"]
# NEW: runtime.context["key"]

# 2단계: 전체 state 반환 제거
# OLD: return state
# NEW: return {"changed_field": value}

# 3단계: context_schema 추가
# OLD: StateGraph(State)
# NEW: StateGraph(State, context_schema=Context)

# 4단계: invoke 시 context 전달
# OLD: app.invoke(state, {"configurable": {...}})
# NEW: app.invoke(state, context={...})
```

## 에러 해결 가이드

```python
# ImportError: langgraph.checkpoint.sqlite
# 해결: pip install langgraph-checkpoint-sqlite

# ImportError: from langgraph.checkpoint.aiosqlite (구버전)
# 해결: from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# TypeError: 'Runtime' object is not subscriptable
# 해결: runtime.context["key"] 사용 (runtime["key"] X)

# ValueError: context_schema not defined
# 해결: StateGraph 생성 시 context_schema 지정
```

## 참고사항
- LangGraph 0.6.0+ 필수
- langgraph-checkpoint-sqlite 2.0.0+ 별도 설치
- Python 3.9+ 권장
- async 사용 시 모든 체인을 async로 통일
- v1.0이 2025년 10월 출시 예정 (또 바뀔 수 있음)
