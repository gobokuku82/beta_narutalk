# Orchestrator - 워크플로우 오케스트레이션

슈퍼바이저와 서브그래프를 통합하여 전체 워크플로우를 조율하는 오케스트레이터입니다.

## 구조

```
orchestrator/
├── __init__.py                 # 모듈 초기화
├── workflow_orchestrator.py    # 메인 오케스트레이터
├── routing.py                  # 라우팅 로직
├── factory.py                  # 팩토리 함수들
├── example_usage.py            # 사용 예제
└── README.md                   # 문서
```

## 주요 컴포넌트

### 1. WorkflowOrchestrator
전체 워크플로우를 통합하고 조율합니다.

```python
from backend.service.orchestrator import WorkflowOrchestrator

# 오케스트레이터 생성
orchestrator = WorkflowOrchestrator(
    supervisor_model="gpt-4o",
    supervisor_temperature=0.2
)

# 그래프 빌드
graph = orchestrator.build_graph()
```

### 2. Supervisor Agent
추론(Reasoning)과 실행 통제(Execution Control)를 담당합니다.

**주요 기능:**
- 사용자 질의 이해 및 분석
- 작업 분해 및 실행 계획 수립
- 서브그래프 선택 및 실행 통제
- 결과 통합 및 최종 응답 생성

### 3. Subgraphs
실제 데이터 수집과 분석을 수행하는 하위 그래프들입니다.

- **DataCollectionSubgraph**: 데이터베이스에서 데이터 수집
- **AnalysisSubgraph**: 수집된 데이터 분석

## 워크플로우 흐름

```
User Query
    ↓
[Supervisor: Understand Query]
    ↓
[Supervisor: Decompose Tasks]
    ↓
[Supervisor: Create Plan]
    ↓
[Supervisor: Route]
    ↓
┌─────────────────────┐
│ Data Collection?    │ → [DataCollectionSubgraph] → Route
├─────────────────────┤
│ Analysis?           │ → [AnalysisSubgraph] → Aggregate
├─────────────────────┤
│ Final Report?       │ → [Generate Final Answer]
└─────────────────────┘
    ↓
Final Answer
```

## 사용 방법

### 기본 사용

```python
from backend.service.orchestrator.factory import run_workflow

# 워크플로우 실행
result = await run_workflow(
    user_query="김철수의 2024년 실적을 분석해주세요",
    session_id="session_001",
    user_id="user_123"
)

print(result['answer'])
```

### 스트리밍 방식

```python
from backend.service.orchestrator.factory import create_streaming_workflow

# 스트리밍 워크플로우 생성
stream = create_streaming_workflow(
    user_query="전체 영업실적 추세를 분석해주세요",
    session_id="session_002"
)

# 스트림 처리
async for update in stream:
    if update["type"] == "state_update":
        print(f"Processing: {update['data']}")
    elif update["type"] == "error":
        print(f"Error: {update['error']}")
```

### 커스텀 설정

```python
from backend.service.orchestrator.factory import create_workflow_instance, run_workflow

# 커스텀 오케스트레이터 생성
orchestrator = create_workflow_instance(
    supervisor_model="gpt-4o",
    supervisor_temperature=0.1,
    config={
        "enable_caching": True,
        "max_retries": 3
    }
)

# 실행
result = await run_workflow(
    user_query="거래처별 실적 비교 분석",
    session_id="session_003",
    orchestrator=orchestrator
)
```

### 빠른 테스트 (동기식)

```python
from backend.service.orchestrator.factory import quick_run

# 블로킹 방식으로 실행 (테스트용)
result = quick_run("이번달 목표 달성률은?")
print(result['answer'])
```

## Supervisor 추론 과정

Supervisor는 다음 3단계로 추론합니다:

### 1. Query Understanding (질의 이해)
```python
{
    "intent": "analysis",
    "entities": {
        "person_name": "김철수",
        "period": "2024"
    },
    "required_data": ["sales_performance", "sales_target"],
    "analysis_type": "comprehensive",
    "complexity": "moderate"
}
```

### 2. Task Decomposition (작업 분해)
```python
[
    {
        "task_id": "collect_sales",
        "task_type": "data_collection",
        "description": "Collect sales performance data",
        "dependencies": [],
        "required_subgraph": "data_collection",
        "priority": 10
    },
    {
        "task_id": "analyze_performance",
        "task_type": "analysis",
        "description": "Analyze sales performance",
        "dependencies": ["collect_sales"],
        "required_subgraph": "analysis",
        "priority": 8
    }
]
```

### 3. Execution Plan (실행 계획)
```python
{
    "execution_order": ["collect_sales", "analyze_performance"],
    "subgraphs_required": ["data_collection", "analysis"],
    "parallel_execution": [["collect_sales"], ["analyze_performance"]],
    "estimated_steps": 4
}
```

## 라우팅 로직

Router는 Supervisor의 결정에 따라 다음 노드를 결정합니다:

```python
from backend.service.orchestrator.routing import Router

router = Router()

# 서브그래프로 라우팅
next_node = router.route_to_subgraph(state)
# Returns: "data_collection" | "analysis" | "final_report" | "END"

# 실행 경로 분석
path = get_execution_path(state)
# Returns: {"total_steps": 3, "completed_steps": 1, "next_step": "analysis"}
```

## 상태 관리

### SupervisorState
```python
{
    # Input
    "user_query": str,
    "session_id": str,

    # Reasoning
    "query_understanding": Dict,
    "task_decomposition": List[Dict],
    "execution_plan": Dict,

    # Execution Control
    "current_step": str,
    "next_action": str,
    "subgraph_selection": List[str],

    # Results
    "collected_data": Dict,
    "analysis_results": Dict,
    "insights": List[str],

    # Output
    "final_answer": str,
    "final_report": Dict
}
```

## 에러 처리

```python
result = await run_workflow(
    user_query="",  # Invalid query
    session_id="session_001"
)

if not result['success']:
    print(f"Error: {result['error']}")
    print(f"Errors: {result['errors']}")
```

## 예제 실행

```bash
# 모든 예제 실행
python -m backend.service.orchestrator.example_usage

# 특정 예제만 실행
python -c "
import asyncio
from backend.service.orchestrator.example_usage import example_basic_usage
asyncio.run(example_basic_usage())
"
```

## API Reference

### Factory Functions

#### `create_workflow_instance()`
```python
def create_workflow_instance(
    supervisor_model: str = "gpt-4o",
    supervisor_temperature: float = 0.2,
    config: Optional[Dict[str, Any]] = None
) -> WorkflowOrchestrator
```

#### `run_workflow()`
```python
async def run_workflow(
    user_query: str,
    session_id: str,
    user_id: Optional[str] = None,
    orchestrator: Optional[WorkflowOrchestrator] = None,
    **kwargs
) -> Dict[str, Any]
```

#### `create_streaming_workflow()`
```python
def create_streaming_workflow(
    user_query: str,
    session_id: str,
    user_id: Optional[str] = None,
    orchestrator: Optional[WorkflowOrchestrator] = None,
    **kwargs
) -> AsyncGenerator
```

#### `quick_run()`
```python
def quick_run(
    user_query: str,
    **kwargs
) -> Dict[str, Any]
```

## 설정 파일

JSON 형식의 설정 파일을 사용할 수 있습니다:

```json
{
    "supervisor_model": "gpt-4o",
    "supervisor_temperature": 0.2,
    "additional_config": {
        "enable_caching": true,
        "max_retries": 3,
        "timeout": 300
    }
}
```

사용:
```python
from backend.service.orchestrator.factory import create_workflow_with_config
from pathlib import Path

orchestrator = create_workflow_with_config(
    config_path=Path("config/workflow_config.json")
)
```

## 로깅

```python
import logging

# 로깅 레벨 설정
logging.basicConfig(level=logging.INFO)

# 특정 모듈만 디버그
logging.getLogger("backend.service.orchestrator").setLevel(logging.DEBUG)
```

## 성능 최적화

1. **병렬 실행**: 독립적인 작업은 병렬로 실행
2. **캐싱**: LLM 응답 캐싱 (설정 필요)
3. **스트리밍**: 대용량 데이터는 스트리밍 방식 사용

## 트러블슈팅

### Q: 워크플로우가 너무 느려요
A: `supervisor_temperature`를 낮추고, 캐싱을 활성화하세요.

### Q: 에러가 발생했어요
A: `execution_trace`를 확인하여 어느 단계에서 실패했는지 파악하세요.

### Q: 서브그래프가 실행되지 않아요
A: `execution_plan`을 확인하여 올바른 서브그래프가 선택되었는지 확인하세요.

## 기여

새로운 서브그래프나 라우팅 로직을 추가하려면:
1. `subgraphs/`에 새 서브그래프 추가
2. `workflow_orchestrator.py`에 실행 노드 추가
3. `routing.py`에 라우팅 로직 추가

## 라이선스

MIT License
