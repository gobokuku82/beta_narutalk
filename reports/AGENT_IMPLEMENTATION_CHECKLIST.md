# Agent Implementation Checklist
> 새로운 에이전트 구현 시 필수 체크리스트

## 🚀 Quick Start Checklist

### Phase 1: 설계 (Design)
- [ ] 에이전트 역할 정의
- [ ] 입력/출력 스펙 정의
- [ ] State 스키마 설계
- [ ] 의존성 파악
- [ ] 에러 시나리오 정의

### Phase 2: 구현 (Implementation)
- [ ] State TypedDict 생성
- [ ] 에이전트 클래스 구현
- [ ] 노드 함수 작성
- [ ] Reducer 함수 정의
- [ ] 에러 처리 구현

### Phase 3: 통합 (Integration)
- [ ] Graph에 노드 추가
- [ ] Edge 연결
- [ ] 라우팅 로직 구현
- [ ] 캐싱 정책 설정
- [ ] 로깅 구현

### Phase 4: 검증 (Verification)
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성
- [ ] 성능 테스트
- [ ] 메모리 프로파일링
- [ ] 문서화

## 📝 상세 구현 가이드

### 1. State 정의 ✅

#### 1.1 TypedDict 생성
```python
# ✅ GOOD: TypedDict 사용
from typing import TypedDict, List, Dict, Any, Optional, Literal

class MyAgentState(TypedDict):
    """에이전트 State 정의"""
    # 필수 필드
    task_id: str
    status: Literal['pending', 'running', 'completed', 'failed']

    # 데이터 필드
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]

    # 메타데이터
    execution_time: float
    confidence_score: float
    error_message: Optional[str]
```

#### 1.2 BaseAgentState 상속 (선택)
```python
class MyAgentState(BaseAgentState):
    """BaseAgentState를 상속한 커스텀 State"""
    # 추가 필드만 정의
    custom_field: str
    special_data: List[Dict]
```

#### 체크포인트
- [ ] TypedDict 사용 (Pydantic 금지)
- [ ] 모든 필드 타입 힌트
- [ ] Optional 필드 명시
- [ ] Literal 타입 활용
- [ ] 문서화 (docstring)

### 2. 에이전트 클래스 구현 ✅

#### 2.1 기본 구조
```python
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MyAgent:
    """에이전트 구현"""

    def __init__(self, config: Optional[Dict] = None):
        """초기화"""
        self.config = config or {}
        self.llm = self._initialize_llm()
        self.tools = self._initialize_tools()
        logger.info(f"MyAgent initialized with config: {config}")

    def _initialize_llm(self):
        """LLM 초기화"""
        provider = self.config.get("llm_provider", "openai")
        if provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model="gpt-4-turbo-preview")
        # ...

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """메인 실행 메서드"""
        try:
            # 실행 로직
            result = await self._process(task)
            return {
                "status": "success",
                "result": result
            }
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
```

#### 체크포인트
- [ ] 초기화 메서드
- [ ] LLM 설정
- [ ] 도구 초기화
- [ ] 비동기 execute 메서드
- [ ] 에러 처리
- [ ] 로깅 구현

### 3. 노드 함수 작성 ✅

#### 3.1 표준 노드 패턴
```python
async def my_agent_node(state: GlobalSessionState) -> Dict[str, Any]:
    """
    에이전트 노드 함수

    중요: 변경사항만 반환!
    """
    # 1. 로깅
    logger.info(f"MyAgent node started for session {state['session_id']}")

    # 2. 필요 데이터 추출
    task = state.get("current_task")
    if not task:
        return {
            "errors": [{"node": "my_agent", "error": "No task found"}],
            "execution_status": "failed"
        }

    # 3. 에이전트 실행
    agent = MyAgent()
    try:
        result = await agent.execute(task)
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return {
            "errors": [{"node": "my_agent", "error": str(e)}],
            "execution_status": "failed"
        }

    # 4. 변경사항만 반환 ⚠️ 중요!
    return {
        "agent_states": {
            "my_agent": result  # 특정 에이전트 State만 업데이트
        },
        "current_phase": "next_phase",
        "audit_trail": [{
            "timestamp": datetime.now().isoformat(),
            "agent": "my_agent",
            "action": "completed"
        }]
    }
```

#### 체크포인트
- [ ] 비동기 함수
- [ ] GlobalSessionState 타입
- [ ] 변경사항만 반환
- [ ] 에러 처리
- [ ] audit_trail 업데이트
- [ ] 로깅

### 4. Reducer 함수 정의 ✅

#### 4.1 커스텀 Reducer
```python
# state.py에 추가
from typing import Annotated
import operator

def merge_agent_states(current: Dict, update: Dict) -> Dict:
    """에이전트 State 병합 reducer"""
    result = current.copy()
    result.update(update)
    return result

class GlobalSessionState(TypedDict):
    # Reducer 적용
    agent_states: Annotated[Dict[str, Any], merge_agent_states]
    errors: Annotated[List[Dict], operator.add]
    total_executions: Annotated[int, operator.add]
```

#### 체크포인트
- [ ] 필요한 Reducer 식별
- [ ] 커스텀 Reducer 구현
- [ ] State에 Annotated 적용
- [ ] 병렬 처리 고려
- [ ] 테스트 작성

### 5. Graph 통합 ✅

#### 5.1 노드 추가
```python
# graph.py
from agents.workers.my_agent import my_agent_node

# Graph에 노드 추가
graph.add_node("my_agent", my_agent_node)
```

#### 5.2 Edge 연결
```python
# 실행 관리자에서 라우팅
graph.add_conditional_edges(
    "execution_manager",
    route_to_agent,
    {
        "my_agent": "my_agent",
        # ...
    }
)

# 에이전트에서 다음 노드로
graph.add_edge("my_agent", "evaluator")
```

#### 5.3 캐싱 정책
```python
cache_policy = {
    "my_agent": {
        "ttl": 300,  # 5분 캐시
        "key_func": lambda x: f"{x['task_id']}_{x['version']}"
    }
}
```

#### 체크포인트
- [ ] 노드 등록
- [ ] Edge 연결
- [ ] 조건부 라우팅
- [ ] 캐싱 설정
- [ ] 타임아웃 설정

### 6. 테스트 작성 ✅

#### 6.1 단위 테스트
```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_my_agent_success():
    """성공 케이스"""
    agent = MyAgent()
    result = await agent.execute({"task": "test"})

    assert result["status"] == "success"
    assert "result" in result

@pytest.mark.asyncio
async def test_my_agent_node():
    """노드 함수 테스트"""
    state = {
        "session_id": "test",
        "current_task": {"task": "test"}
    }

    result = await my_agent_node(state)

    assert "agent_states" in result
    assert "my_agent" in result["agent_states"]
```

#### 체크포인트
- [ ] 성공 케이스
- [ ] 실패 케이스
- [ ] Edge 케이스
- [ ] Mock 사용
- [ ] 비동기 테스트

### 7. 성능 검증 ✅

#### 7.1 메모리 프로파일
```python
import tracemalloc

tracemalloc.start()
result = await my_agent_node(state)
current, peak = tracemalloc.get_traced_memory()
print(f"Memory: {peak / 1024 / 1024:.1f}MB")
tracemalloc.stop()
```

#### 7.2 실행 시간
```python
import time

start = time.time()
result = await my_agent_node(state)
execution_time = time.time() - start
assert execution_time < 5.0  # 5초 이내
```

#### 체크포인트
- [ ] 메모리 사용량 < 50MB
- [ ] 실행 시간 < 5초
- [ ] State 크기 < 10KB
- [ ] CPU 사용률 체크
- [ ] 병렬 처리 테스트

### 8. 문서화 ✅

#### 8.1 README.md
```markdown
# MyAgent

## 개요
에이전트 설명...

## 사용법
```python
from agents.workers.my_agent import MyAgent

agent = MyAgent()
result = await agent.execute(task)
```

## API
- execute(task): 태스크 실행
- ...

## 설정
- llm_provider: LLM 제공자
- ...
```

#### 체크포인트
- [ ] README 작성
- [ ] API 문서
- [ ] 사용 예제
- [ ] 설정 옵션
- [ ] 트러블슈팅

## 🚨 Common Pitfalls

### ❌ 피해야 할 실수

1. **전체 State 반환**
```python
# ❌ BAD
return state  # 전체 State 반환

# ✅ GOOD
return {"changed_field": value}  # 변경사항만
```

2. **State 직접 수정**
```python
# ❌ BAD
state["field"] = value  # 직접 수정

# ✅ GOOD
return {"field": value}  # 새 값 반환
```

3. **동기 함수 사용**
```python
# ❌ BAD
def my_node(state):  # 동기 함수

# ✅ GOOD
async def my_node(state):  # 비동기 함수
```

4. **에러 무시**
```python
# ❌ BAD
try:
    # ...
except:
    pass  # 에러 무시

# ✅ GOOD
except Exception as e:
    logger.error(f"Error: {e}")
    return {"errors": [{"error": str(e)}]}
```

## 📊 성능 기준

### 최소 요구사항
| 메트릭 | 기준값 | 측정 방법 |
|--------|--------|-----------|
| 실행 시간 | < 5초 | time.time() |
| 메모리 사용 | < 50MB | tracemalloc |
| State 크기 | < 10KB | sys.getsizeof() |
| 에러율 | < 1% | 로그 분석 |
| 테스트 커버리지 | > 80% | pytest-cov |

### 권장 사항
| 메트릭 | 기준값 | 이유 |
|--------|--------|------|
| 실행 시간 | < 2초 | 사용자 경험 |
| 메모리 사용 | < 20MB | 리소스 효율 |
| State 크기 | < 5KB | 네트워크 효율 |
| 캐시 히트율 | > 50% | 성능 향상 |

## 🎯 Final Checklist

### 배포 전 최종 확인
- [ ] 모든 테스트 통과
- [ ] 성능 기준 충족
- [ ] 문서화 완료
- [ ] 코드 리뷰 완료
- [ ] 보안 검토 완료
- [ ] 로깅 구현 확인
- [ ] 에러 처리 확인
- [ ] State 관리 최적화
- [ ] Reducer 함수 적용
- [ ] 모니터링 설정

---

**Version**: 1.0.0
**Last Updated**: 2025-09-16
**Based on**: LangGraph 0.6.7
**Status**: Production Ready