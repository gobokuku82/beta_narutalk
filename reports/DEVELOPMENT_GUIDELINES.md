# LangGraph Development Guidelines
> 에이전트 개발 필수 가이드라인

## 🎯 개발 원칙

### 1. **함수형 프로그래밍 패러다임**
- 순수 함수 작성 (부작용 없음)
- 불변성 유지
- 명확한 입출력

### 2. **명시적 타입 정의**
- TypedDict 사용
- 타입 힌트 필수
- Any 타입 최소화

### 3. **에러 우선 처리**
- 예외 상황 먼저 체크
- 조기 반환 패턴
- 명확한 에러 메시지

## 📝 코드 작성 규칙

### 1. **노드 함수 템플릿**
```python
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def node_name(state: GlobalSessionState) -> Dict[str, Any]:
    """
    노드 설명

    Args:
        state: Global session state

    Returns:
        Dict with only changed fields
    """
    # 1. 로깅
    logger.info(f"Starting {node_name} for session {state['session_id']}")

    # 2. 필요 데이터 추출
    required_data = state.get("required_field")
    if not required_data:
        logger.error("Required data not found")
        return {
            "errors": [{"node": "node_name", "error": "Missing required_field"}],
            "execution_status": "failed"
        }

    # 3. 처리 로직
    try:
        result = await process_logic(required_data)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return {
            "errors": [{"node": "node_name", "error": str(e)}],
            "execution_status": "failed"
        }

    # 4. 변경사항만 반환
    return {
        "result_field": result,
        "current_phase": "next_phase",
        "audit_trail": [{
            "timestamp": datetime.now().isoformat(),
            "node": "node_name",
            "action": "processed",
            "result": "success"
        }]
    }
```

### 2. **에이전트 클래스 템플릿**
```python
class MyAgent:
    """에이전트 설명"""

    def __init__(self, config: Optional[Dict] = None):
        """초기화"""
        self.config = config or {}
        self.llm = self._initialize_llm()
        self.tools = self._initialize_tools()

    def _initialize_llm(self):
        """LLM 초기화"""
        provider = self.config.get("llm_provider", "openai")
        if provider == "openai":
            return ChatOpenAI(model="gpt-4-turbo-preview")
        elif provider == "anthropic":
            return ChatAnthropic(model="claude-3-opus-20240229")
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _initialize_tools(self):
        """도구 초기화"""
        return []

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """메인 실행 메서드"""
        # 구현
        pass
```

### 3. **State 정의 템플릿**
```python
from typing import TypedDict, List, Dict, Any, Optional, Literal

class MyAgentState(TypedDict):
    """에이전트 State 설명"""
    # 필수 필드
    task_id: str
    status: Literal['pending', 'running', 'completed', 'failed']

    # 선택 필드
    result: Optional[Any]
    error: Optional[str]

    # 컬렉션 필드
    logs: List[str]
    metadata: Dict[str, Any]
```

## 🚫 안티패턴 (DON'Ts)

### 1. **State 직접 수정**
```python
# ❌ 절대 금지
def bad_node(state):
    state["field"] = "new_value"  # 직접 수정
    state["list"].append(item)    # 직접 수정
    return state

# ✅ 올바른 방식
def good_node(state):
    return {
        "field": "new_value",
        "list": state["list"] + [item]
    }
```

### 2. **전체 State 반환**
```python
# ❌ 성능 저하
def bad_node(state):
    # 처리...
    return state  # 전체 반환

# ✅ 변경사항만
def good_node(state):
    # 처리...
    return {"changed_field": new_value}
```

### 3. **타입 불일치**
```python
# ❌ 타입 에러
class State(TypedDict):
    count: int

def bad_node(state):
    return {"count": "10"}  # str 반환

# ✅ 타입 일치
def good_node(state):
    return {"count": 10}  # int 반환
```

### 4. **에러 무시**
```python
# ❌ 에러 숨김
def bad_node(state):
    try:
        result = risky_operation()
    except:
        pass  # 에러 무시
    return {}

# ✅ 명시적 에러 처리
def good_node(state):
    try:
        result = risky_operation()
        return {"result": result}
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        return {"errors": [{"error": str(e)}]}
```

## ✅ 베스트 프랙티스 (DO's)

### 1. **명확한 로깅**
```python
logger.info(f"Starting {operation} for {context}")
logger.debug(f"Processing data: {data[:100]}")  # 일부만
logger.error(f"Failed: {error}", exc_info=True)
```

### 2. **조기 반환**
```python
def good_node(state):
    # 검증 먼저
    if not state.get("required"):
        return {"error": "Missing required field"}

    # 정상 처리
    return {"result": process(state["required"])}
```

### 3. **명시적 타입**
```python
from typing import Dict, List, Optional

def process(
    data: Dict[str, Any],
    options: Optional[List[str]] = None
) -> Dict[str, Any]:
    """명시적 타입 힌트"""
    pass
```

### 4. **Reducer 활용**
```python
from typing import Annotated
import operator

class State(TypedDict):
    messages: Annotated[List[str], operator.add]  # 자동 병합
    count: Annotated[int, operator.add]  # 자동 합산
```

## 🧪 테스트 작성

### 1. **단위 테스트**
```python
import pytest
from unittest.mock import Mock

@pytest.mark.asyncio
async def test_node_success():
    """성공 케이스 테스트"""
    state = {"required_field": "value"}
    result = await my_node(state)

    assert "result_field" in result
    assert result["current_phase"] == "next_phase"

@pytest.mark.asyncio
async def test_node_failure():
    """실패 케이스 테스트"""
    state = {}  # 필수 필드 누락
    result = await my_node(state)

    assert "errors" in result
    assert result["execution_status"] == "failed"
```

### 2. **통합 테스트**
```python
@pytest.mark.asyncio
async def test_workflow():
    """전체 워크플로우 테스트"""
    initial_state = initialize_state()

    # 각 단계 실행
    state = await intent_analyzer_node(initial_state)
    assert state["current_phase"] == "planning"

    state = await planner_node(state)
    assert state["current_phase"] == "execution"
```

## 🐛 디버깅 가이드

### 1. **State 추적**
```python
# State 변경 추적
def debug_state_changes(old_state, new_state):
    changes = {}
    for key in new_state:
        if key not in old_state or old_state[key] != new_state[key]:
            changes[key] = {
                "old": old_state.get(key),
                "new": new_state[key]
            }
    logger.debug(f"State changes: {changes}")
```

### 2. **실행 시간 측정**
```python
import time

async def timed_node(state):
    start = time.time()

    result = await actual_processing(state)

    execution_time = time.time() - start
    logger.info(f"Node executed in {execution_time:.2f}s")

    return {**result, "execution_time": execution_time}
```

### 3. **메모리 프로파일링**
```python
import tracemalloc

tracemalloc.start()

# 코드 실행
result = await node(state)

current, peak = tracemalloc.get_traced_memory()
logger.info(f"Memory: current={current/1024/1024:.1f}MB, peak={peak/1024/1024:.1f}MB")
tracemalloc.stop()
```

## 📋 코드 리뷰 체크리스트

- [ ] TypedDict 사용 여부
- [ ] 변경사항만 반환하는지
- [ ] 에러 처리 구현
- [ ] 로깅 구현
- [ ] 타입 힌트 작성
- [ ] 테스트 작성
- [ ] 문서화 (docstring)
- [ ] State 직접 수정 없음
- [ ] Reducer 함수 활용
- [ ] 성능 고려사항 체크

## 🔍 일반적인 문제 해결

### 1. **State가 업데이트되지 않음**
- 변경사항을 반환했는지 확인
- Reducer 함수가 올바른지 확인
- 노드가 graph에 연결되었는지 확인

### 2. **타입 에러**
- TypedDict 정의와 반환값 타입 일치 확인
- Optional 필드 처리 확인

### 3. **병렬 처리 충돌**
- Reducer 함수 사용 확인
- State 직접 수정 없는지 확인

### 4. **메모리 누수**
- 큰 데이터는 참조만 저장
- 불필요한 State 복사 제거
- 캐싱 크기 제한 설정

---

**Version**: 1.0.0
**Last Updated**: 2025-09-16
**Based on**: LangGraph 0.6.7