# LangGraph 0.6.7 Runtime Pattern Documentation

## 검증 완료: Context 전달 방식

### ✅ 올바른 패턴 (작동 확인)

```python
# 별도 context 파라미터로 전달
result = await app.ainvoke(
    initial_state,
    config={"configurable": {"thread_id": "session_id"}},
    context=context  # ✅ 별도 파라미터로 전달
)
```

### ❌ 작동하지 않는 패턴들

```python
# Method 1 - 작동 안함
result = await app.ainvoke(
    initial_state,
    config={
        "configurable": {
            "thread_id": "session_id",
            "context": context  # ❌ Runtime.context가 None이 됨
        }
    }
)

# Method 2 - 작동 안함
result = await app.ainvoke(
    initial_state,
    config={
        "configurable": {"thread_id": "session_id"},
        "context": context  # ❌ Runtime.context가 None이 됨
    }
)
```

## Runtime 객체 구조

### Runtime 타입
- `langgraph.runtime.Runtime` 클래스가 실제로 존재
- Generic 타입: `Runtime[T]` 형태로 사용
- LangGraph가 자동으로 생성하여 노드에 전달

### Runtime.context 접근
```python
async def node(state: State, runtime: Runtime[AgentContext]) -> Dict:
    # Runtime.context는 dict 타입
    user_id = runtime.context["user_id"]  # 필수 필드는 []
    language = runtime.context.get("language", "ko")  # 선택 필드는 .get()
```

## 노드 시그니처

### 올바른 시그니처
```python
# Runtime을 사용하는 노드
async def my_node(
    state: MyState,
    runtime: Runtime[MyContext]
) -> Dict[str, Any]:
    # runtime.context로 컨텍스트 접근
    pass
```

### StateGraph 설정
```python
workflow = StateGraph(
    state_schema=MyState,
    context_schema=MyContext  # Context 스키마 지정
)
```

## 주의사항

1. **context는 반드시 별도 파라미터로 전달**
   - `app.ainvoke(state, config={...}, context=context)`
   - config 내부에 넣으면 전달되지 않음

2. **Runtime은 import 가능**
   - `from langgraph.runtime import Runtime`
   - LangGraph 0.6.7에서 정상 지원

3. **Context는 dict로 전달**
   - TypedDict로 정의하되, 실제 전달은 dict
   - `runtime.context`는 dict 타입으로 접근

## 테스트 결과 요약

| Method | Description | Result |
|--------|-------------|---------|
| Method 1 | `config["configurable"]["context"]` | ❌ Context = None |
| Method 2 | `config["context"]` | ❌ Context = None |
| Method 3 | 별도 `context` 파라미터 | ✅ 정상 작동 |

## 현재 구현 상태

`sales_analytics_agent.py`의 `run()` 메서드는 이미 올바른 패턴 사용 중:

```python
result = await app.ainvoke(
    initial_state,
    config={"configurable": {"thread_id": f"{session_id}_sales"}},
    context=context  # ✅ 올바른 패턴
)
```

---

*Last verified: 2025-09-25 with LangGraph 0.6.7*