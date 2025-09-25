# LangGraph 0.6.x Context API 업데이트 가이드 (2025년 9월 기준)

## 📌 현재 상태 및 버전 정보
- **현재 최신 버전**: LangGraph 0.6.7 (2025년 9월 기준)
- **v1.0 출시 예정**: 2025년 10월 (현재 alpha 1.0.0a3 버전 테스트 중)
- **중요**: 0.6.x 문서는 v1.0 출시와 함께 deprecated 예정

## 🔄 주요 업데이트 및 수정 사항

### 1. Context API 정식 출시 확인
LangGraph 0.6.0부터 Context API가 정식으로 도입되어 기존 `config['configurable']` 패턴을 대체하게 되었습니다. 이는 더 깔끔하고 타입 안전한 런타임 의존성 주입을 제공합니다.

### 2. Runtime 객체 구조 업데이트
```python
from langgraph.runtime import Runtime
from typing_extensions import TypedDict

# Runtime 객체가 제공하는 속성들
class Runtime[ContextT]:
    context: ContextT          # 정적 런타임 컨텍스트
    store: BaseStore           # Store API 접근
    stream_writer: StreamWriter # 스트리밍 유틸리티
    # config는 더 이상 중첩된 'configurable' 없이 직접 접근
```

### 3. Store API 통합 개선
Runtime 객체를 통해 Store에 직접 접근 가능하며, 장기 메모리 관리가 더욱 간편해졌습니다:

```python
async def memory_node(state: State, runtime: Runtime[Context]) -> dict:
    # runtime.store로 직접 접근
    namespace = ("users", runtime.context["user_id"])
    
    # Store 작업
    memories = await runtime.store.asearch(namespace)
    await runtime.store.aput(namespace, "key", value)
    
    return {"field": updated_value}
```

### 4. Subgraph Context 전파 이슈 해결
초기 버전(0.6.0)에서 발생했던 서브그래프에 런타임 컨텍스트가 전달되지 않던 문제가 해결되었습니다:

```python
# 서브그래프도 자동으로 context 상속
parent_graph = StateGraph(State, context_schema=Context)
sub_graph = StateGraph(SubState, context_schema=Context)

# parent에서 전달된 context가 subgraph에도 자동 전파
parent_graph.add_node("subgraph", sub_graph.compile())
```

### 5. AsyncSqliteSaver Import 경로 확정
```python
# ✅ 올바른 import (langgraph-checkpoint-sqlite 패키지 필요)
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# ❌ 구버전 import (더 이상 사용 안 함)
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver
```

## 🆕 추가된 기능 및 패턴

### 1. Functional API (대체 접근법)
LangGraph는 Graph API 외에 Functional API도 제공하여, 그래프 구조를 생각하지 않고 표준 Python 구문으로 워크플로우를 정의할 수 있습니다:

```python
from langgraph.func import entrypoint, task

@task
async def process_data(data: dict) -> dict:
    # 비동기 작업 수행
    return processed_data

@entrypoint(checkpointer=checkpointer, context_schema=Context)
async def workflow(input_data: dict, *, runtime: Runtime[Context]) -> dict:
    # context는 runtime을 통해 접근
    user_id = runtime.context["user_id"]
    
    # 병렬 실행
    futures = [process_data(item) for item in input_data["items"]]
    results = await asyncio.gather(*futures)
    
    return {"results": results}
```

### 2. Pydantic 모델 지원 강화
StateGraph는 이제 Pydantic 모델을 직접 state로 사용할 수 있습니다:

```python
from pydantic import BaseModel

class ChatState(BaseModel):
    messages: List[AnyMessage]
    context: str
    metadata: dict

# Pydantic 모델을 직접 사용
workflow = StateGraph(ChatState, context_schema=ContextSchema)

def process_node(state: ChatState, runtime: Runtime[ContextSchema]) -> dict:
    # state는 Pydantic 객체로 전달됨
    assert isinstance(state, ChatState)
    
    # 부분 업데이트 반환
    return {"messages": state.messages + [new_message]}
```

### 3. 동적 도구 및 모델 선택
0.6.x에서 create_react_agent가 동적 도구 및 모델 선택을 지원:

```python
from langgraph.prebuilt import create_react_agent

def get_dynamic_tools(runtime: Runtime[Context]) -> list:
    """Context에 따라 다른 도구 세트 반환"""
    if runtime.context.get("premium_user"):
        return [premium_tool1, premium_tool2]
    return [basic_tool]

agent = create_react_agent(
    model="openai:gpt-4",
    tools=get_dynamic_tools,  # 함수로 전달
    context_schema=ContextSchema
)
```

### 4. Stream Writer 개선
```python
async def streaming_node(
    state: State, 
    runtime: Runtime[Context]
) -> dict:
    # stream_writer를 통한 중간 결과 스트리밍
    for chunk in process_chunks():
        runtime.stream_writer.write({"chunk": chunk})
    
    return {"final_result": combined_chunks}
```

## ⚠️ 알려진 이슈 및 주의사항

### 1. Stream 엔드포인트 Context 이슈
특정 상황에서 stream 엔드포인트를 통해 전달된 runtime.context가 null일 수 있는 이슈가 보고되었습니다. 이는 주로 설정 문제이며, 다음을 확인해야 합니다:

```python
# stream 사용 시 context 명시적 전달 필수
async for chunk in app.astream(
    state,
    config=config,
    context=context  # 반드시 포함
):
    process(chunk)
```

### 2. 비동기 도구 처리
ToolNode는 그래프를 ainvoke나 astream으로 호출할 때만 비동기 도구를 자동으로 비동기로 실행합니다:

```python
# 비동기 도구 정의
@tool
async def async_search(query: str) -> str:
    result = await async_api_call(query)
    return result

# 그래프를 비동기로 실행해야 비동기 도구가 제대로 작동
result = await app.ainvoke(state, context=context)  # ✅
# result = app.invoke(state, context=context)  # ❌ 동기 호출시 에러
```

## 🔧 마이그레이션 체크리스트 (업데이트)

### 0.5.x → 0.6.7 마이그레이션
- [ ] `config["configurable"]` → `runtime.context` 변경
- [ ] 전체 state 반환 → 부분 dict 반환
- [ ] `StateGraph`에 `context_schema` 추가
- [ ] `invoke`/`stream`에 `context` 인자 추가
- [ ] `add_messages` 리듀서 적용
- [ ] AsyncSqliteSaver import 경로 수정
- [ ] Subgraph 사용 시 context 전파 확인
- [ ] 비동기 도구 사용 시 `ainvoke`/`astream` 사용

### 0.6.x → 1.0 준비사항
- [ ] alpha 버전으로 테스트 환경 구축
- [ ] Functional API 평가 (필요시 적용)
- [ ] Pydantic 모델 기반 State 고려
- [ ] 동적 도구/모델 선택 패턴 적용

## 📚 핵심 디자인 원칙

### Context 계층 구조
1. **Static Runtime Context** (`runtime.context`)
   - 실행 중 불변
   - 사용자 정보, API 키, 권한 등
   - `context` 인자로 전달

2. **Dynamic Runtime Context** (State)
   - 실행 중 변경 가능
   - 대화 히스토리, 중간 결과
   - 노드 반환값으로 업데이트

3. **Cross-Conversation Context** (Store)
   - 대화 간 지속
   - 사용자 선호도, 장기 메모리
   - `runtime.store`로 접근

## 🎯 Best Practices (2025년 9월 기준)

### DO ✅
1. **타입 힌트 철저히 사용**
   ```python
   def node(state: State, runtime: Runtime[ContextSchema]) -> dict:
   ```

2. **Context Schema 명확히 정의**
   ```python
   class ContextSchema(TypedDict):
       user_id: str
       permissions: List[str]
       feature_flags: Dict[str, bool]
   ```

3. **부분 State 업데이트만 반환**
   ```python
   return {"changed_field": new_value}  # ✅
   # return state  # ❌
   ```

4. **비동기 우선 설계**
   ```python
   async def node(...) -> dict:
       result = await async_operation()
       return {"field": result}
   ```

5. **Store 네임스페이스 계층화**
   ```python
   user_ns = ("users", user_id)
   session_ns = ("users", user_id, "sessions", session_id)
   ```

### DON'T ❌
1. `config['configurable']` 사용
2. 전체 state 객체 반환
3. State에 설정값 저장
4. 동기/비동기 혼용
5. `context_schema` 생략
6. Store 없이 장기 메모리 구현

## 🔍 디버깅 팁

### Runtime Context 확인
```python
def debug_node(state: State, runtime: Runtime[Context]) -> dict:
    print(f"Context: {runtime.context}")
    print(f"Has store: {runtime.store is not None}")
    print(f"Thread ID: {runtime.config.get('thread_id')}")
    
    # Context 내용 검증
    assert "user_id" in runtime.context
    
    return {}
```

### Checkpointer 상태 검사
```python
# 체크포인트 히스토리 확인
async with AsyncSqliteSaver.from_conn_string("app.db") as checkpointer:
    config = {"configurable": {"thread_id": "test_thread"}}
    
    # 현재 상태
    snapshot = await app.aget_state(config)
    print(f"Current state: {snapshot.values}")
    
    # 히스토리
    history = []
    async for state in app.aget_state_history(config):
        history.append(state)
    print(f"History length: {len(history)}")
```

## 🚀 성능 최적화 팁

1. **Checkpointer 선택**
   - 개발: `InMemorySaver` (빠름, 비영구적)
   - 테스트: `AsyncSqliteSaver` (로컬 파일)
   - 프로덕션: `AsyncPostgresSaver` (확장 가능)

2. **State 크기 관리**
   - 큰 데이터는 Store에 저장하고 State에는 참조만
   - 불필요한 중간 데이터는 즉시 삭제

3. **병렬 처리 활용**
   ```python
   # Functional API의 task 데코레이터 활용
   futures = [process_task(item) for item in items]
   results = await asyncio.gather(*futures)
   ```

## 📦 필수 패키지 및 버전

```bash
# 핵심 패키지
pip install "langgraph>=0.6.7"
pip install "langgraph-checkpoint-sqlite>=2.0.0"  # SQLite 체크포인터
pip install "langchain-core>=0.3.0"

# 선택적 패키지
pip install "langgraph-checkpoint-postgres"  # PostgreSQL 체크포인터
pip install "langsmith>=0.3.45"  # 모니터링 및 디버깅
```

## 🔗 참고 자료
- [LangGraph 공식 문서](https://langchain-ai.github.io/langgraph/)
- [v1.0 Alpha 문서](https://langchain-ai.github.io/langgraph/v1.0/)
- [GitHub 이슈 트래커](https://github.com/langchain-ai/langgraph/issues)
- [Community Forum](https://forum.langchain.com/)

## ⚡ 빠른 시작 예제

```python
import asyncio
from typing import TypedDict, Annotated, List
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.runtime import Runtime
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.store.memory import InMemoryStore

# 1. Schema 정의
class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    summary: str

class Context(TypedDict):
    user_id: str
    model: str
    max_tokens: int

# 2. 노드 구현
async def chat_node(state: State, runtime: Runtime[Context]) -> dict:
    # Context 활용
    user_id = runtime.context["user_id"]
    model_name = runtime.context["model"]
    
    # Store에서 사용자 정보 조회
    user_info = await runtime.store.aget(
        ("users", user_id), 
        "profile"
    )
    
    # 응답 생성 (예시)
    response = f"Hello {user_info.get('name', 'User')}! Using {model_name}"
    
    return {
        "messages": [AIMessage(content=response)],
        "summary": f"Greeted user {user_id}"
    }

# 3. 그래프 구성
async def create_app():
    # Store 초기화
    store = InMemoryStore()
    await store.aput(
        ("users", "user123"), 
        "profile", 
        {"name": "Alice"}
    )
    
    # 그래프 생성
    workflow = StateGraph(State, context_schema=Context)
    workflow.add_node("chat", chat_node)
    workflow.add_edge(START, "chat")
    workflow.add_edge("chat", END)
    
    # Checkpointer와 함께 컴파일
    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        return workflow.compile(
            checkpointer=checkpointer,
            store=store
        )

# 4. 실행
async def main():
    app = await create_app()
    
    # Context와 함께 실행
    result = await app.ainvoke(
        {"messages": [HumanMessage(content="Hello!")]},
        config={"configurable": {"thread_id": "conv_001"}},
        context={
            "user_id": "user123",
            "model": "gpt-4",
            "max_tokens": 1000
        }
    )
    
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

*마지막 업데이트: 2025년 9월 25일*
*LangGraph 버전: 0.6.7*
*문서 상태: v1.0 출시 전 최종 버전*
