# LangGraph 0.6.x Context API Development Rules

## 🚨 CRITICAL: LangGraph 0.6.x는 완전히 새로운 버전
- 0.5.x와 호환되지 않음
- config['configurable'] 패턴은 deprecated
- Context API가 새로운 표준

## Context API 핵심 원칙

### 1. Runtime Context 사용
```python
# ❌ NEVER (구버전)
def node(state, config):
    user = config["configurable"]["user_id"]
    
# ✅ ALWAYS (0.6.x+)
def node(state: State, runtime: Runtime[Context]) -> dict:
    user = runtime.context["user_id"]
    return {"field": value}  # 부분 업데이트만
```

### 2. State vs Context 구분
- **State**: 변경되는 데이터 (messages, steps, results)
- **Context**: 불변 설정 (user_id, api_keys, permissions)
- **Store**: 장기 메모리 (user preferences, history)

### 3. 그래프 생성 패턴
```python
# 항상 context_schema 지정
graph = StateGraph(
    state_schema=State,
    context_schema=ContextSchema,  # 필수!
    input_schema=InputSchema,      # 선택
    output_schema=OutputSchema      # 선택
)
```

## AsyncSqliteSaver 규칙

### 설치 및 Import
```python
# 설치: pip install langgraph-checkpoint-sqlite

# ✅ 올바른 import
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# ❌ 잘못된 import (구버전)
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver
```

### 사용 패턴
```python
# 항상 async with 사용
async with AsyncSqliteSaver.from_conn_string("app.db") as checkpointer:
    app = workflow.compile(checkpointer=checkpointer)
    
# thread_id 필수
config = {"configurable": {"thread_id": "unique_id"}}
```

## State 리듀서 패턴

### 기본 리듀서
```python
from typing import Annotated
from langgraph.graph.message import add_messages

class State(TypedDict):
    # 자동 메시지 누적
    messages: Annotated[list, add_messages]
    
    # 리스트 추가
    history: Annotated[list, operator.add]
    
    # 딕셔너리 머지
    metadata: Annotated[dict, lambda a, b: {**a, **b}]
    
    # 기본 (덮어쓰기)
    current: str
```

## 노드 구현 규칙

### 올바른 노드 시그니처
```python
# 동기 노드
def sync_node(
    state: State, 
    runtime: Runtime[Context]
) -> dict:
    return {"field": value}

# 비동기 노드
async def async_node(
    state: State,
    runtime: Runtime[Context],
    store: Store  # 선택적
) -> dict:
    return {"field": value}
```

### 반환값 규칙
- **절대 전체 state 반환 금지**
- **변경된 필드만 dict로 반환**
- **리듀서가 자동으로 머지 처리**

## 실행 패턴

### invoke 호출
```python
# Context 전달 필수
result = await app.ainvoke(
    state,
    config=config,
    context=context  # 0.6.x 필수!
)
```

### Stream 처리
```python
async for chunk in app.astream(
    state,
    config=config,
    context=context,
    stream_mode="updates"
):
    process(chunk)
```

## Store API 사용

### 네임스페이스 규칙
```python
# 튜플 형식 사용
namespace = ("category", "identifier")

# 계층 구조
user_ns = ("users", user_id)
session_ns = ("users", user_id, "sessions", session_id)
```

### CRUD 작업
```python
# Create/Update
await store.aput(namespace, key, value)

# Read
value = await store.aget(namespace, key)

# Search
results = await store.asearch(namespace)

# Delete
await store.adelete(namespace, key)
```

## 마이그레이션 체크리스트

### 구버전 → 0.6.x
- [ ] config["configurable"] → runtime.context 변경
- [ ] 전체 state 반환 → 부분 dict 반환
- [ ] StateGraph에 context_schema 추가
- [ ] invoke에 context 인자 추가
- [ ] add_messages 리듀서 사용
- [ ] AsyncSqliteSaver import 경로 수정

## 일반 Best Practices

### DO ✅
1. TypedDict로 모든 스키마 정의
2. 비동기 우선 (async/await)
3. Store로 장기 메모리 관리
4. 부분 state 업데이트
5. Context로 설정 전달
6. thread_id로 세션 관리

### DON'T ❌
1. config['configurable'] 사용
2. 전체 state 반환
3. state에 설정값 저장
4. 동기/비동기 혼용
5. Store 없이 장기 메모리 구현
6. context_schema 생략

## 에러 트러블슈팅

```python
# ModuleNotFoundError: langgraph.checkpoint.sqlite
pip install langgraph-checkpoint-sqlite

# TypeError: Runtime not subscriptable
runtime.context["key"]  # runtime["key"] X

# ValueError: No context_schema
StateGraph(State, context_schema=Context)

# Thread consistency error
AsyncSqliteSaver.from_conn_string(":memory:")  # 메모리 DB 사용
```

## 성능 최적화

1. **Checkpointer 선택**
   - 개발: InMemorySaver
   - 테스트: AsyncSqliteSaver
   - 프로덕션: AsyncPostgresSaver

2. **State 크기 관리**
   - 필요한 데이터만 State에 유지
   - 대용량 데이터는 Store 사용
   - 임시 데이터는 노드 내부 변수 활용

3. **비동기 처리**
   - I/O 작업은 항상 async
   - 동시 실행 가능한 노드는 병렬 처리
   - aiohttp, httpx 등 비동기 라이브러리 사용

## 버전 호환성
- LangGraph >= 0.6.0
- langgraph-checkpoint-sqlite >= 2.0.0
- Python >= 3.9
- LangChain Core >= 0.3.0

## 참고: 자주 변경되는 API
LangGraph는 빠르게 발전 중. v1.0이 2025년 10월 예정이므로:
- 공식 문서 항상 확인
- 마이너 버전 업데이트 주의
- Context API는 핵심이므로 유지될 가능성 높음
