# NaruTalk Backend Developer Manual

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [LangGraph 0.6.x Context API](#langgraph-06x-context-api)
3. [Component Development Guide](#component-development-guide)
4. [Agent Implementation](#agent-implementation)
5. [Subgraph Patterns](#subgraph-patterns)
6. [Tool Development](#tool-development)
7. [State Management](#state-management)
8. [API Reference](#api-reference)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## 1. Architecture Overview

### System Architecture Pattern

```
┌─────────────────────────────────────────────────────┐
│                    Orchestrator                      │
│              (Main Router - 미구현)                   │
└────────┬────────────────────────────────────────────┘
         │
         ├──────────────┬──────────────┬──────────────┐
         ▼              ▼              ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
    │  Sales   │  │  Search  │  │Compliance│  │ Document │
    │  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │
    └────┬─────┘  └──────────┘  └──────────┘  └──────────┘
         │
         ├──────────────┬──────────────┐
         ▼              ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │   Data   │  │ Analysis │  │  Report  │
    │Collection│  │ Subgraph │  │ Subgraph │
    │ Subgraph │  │          │  │          │
    └────┬─────┘  └────┬─────┘  └──────────┘
         │              │
         ▼              ▼
    ┌──────────────────────────────┐
    │          Tools               │
    │ (SQL, Calculation, Analysis) │
    └──────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns**: Config, Context, State 완벽 분리
2. **Composability**: 재사용 가능한 서브그래프
3. **Type Safety**: TypedDict를 통한 타입 안정성
4. **Asynchronous**: 비동기 처리 기본
5. **Checkpointing**: 상태 영속성 지원

---

## 2. LangGraph 0.6.x Context API

### Core Concepts

#### Config (정적 설정)
시스템 시작 시 로드되어 변경되지 않는 설정값:

```python
# backend/service/core/config.py
class Config:
    # 시스템 경로
    BASE_DIR = Path(__file__).parent.parent.parent.parent
    DB_DIR = BASE_DIR / "database" / "storage"

    # 모델 설정
    DEFAULT_MODELS = {
        "planning": "gpt-4o",
        "intent": "gpt-4o-mini"
    }

    # 시스템 한계
    LIMITS = {
        "max_recursion": 25,
        "max_sql_results": 1000
    }
```

#### Context (런타임 메타데이터)
실행 시점에 전달되는 읽기 전용 메타데이터:

```python
# backend/service/core/context.py
class AgentContext(TypedDict):
    # 필수 필드
    user_id: str
    session_id: str

    # 선택 필드
    request_id: Optional[str]
    language: Optional[str]
    api_keys: Optional[Dict[str, str]]
    debug_mode: Optional[bool]
```

#### State (워크플로우 데이터)
워크플로우 실행 중 변경되는 데이터:

```python
# backend/service/core/states.py
class SalesState(BaseState):
    # 입력 (덮어쓰기)
    query: str

    # 수집 (누적)
    sql_result: Annotated[List[Dict], add]

    # 집계 (병합)
    aggregated_data: Annotated[Dict, merge_dicts]

    # 분석 (고유값 추가)
    insights: Annotated[List[str], append_unique]
```

### Reducer Patterns

상태 업데이트를 제어하는 리듀서 함수들:

```python
# 덮어쓰기 (기본)
status: str  # 새 값이 이전 값을 완전히 대체

# 누적 (add)
errors: Annotated[List[str], add]  # 리스트에 항목 추가

# 병합 (merge_dicts)
statistics: Annotated[Dict, merge_dicts]  # 딕셔너리 병합

# 고유값 추가 (append_unique)
insights: Annotated[List[str], append_unique]  # 중복 제거하며 추가
```

---

## 3. Component Development Guide

### Directory Structure Convention

```
backend/service/
├── core/          # 핵심 컴포넌트 (Config, Context, State, Base classes)
├── agents/        # 에이전트 구현체
├── subgraphs/     # 재사용 가능한 서브그래프
├── tools/         # 도구 구현체
├── orchestrator/  # 메인 오케스트레이터
└── utils/         # 유틸리티 함수
```

### Naming Conventions

- **Agents**: `{domain}_agent.py` (예: sales_analytics_agent.py)
- **Subgraphs**: `{function}_subgraph.py` (예: data_collection_subgraph.py)
- **Tools**: `{action}_tool.py` 또는 `{action}_{object}.py` (예: sql_executor.py)
- **States**: `{Component}State` (예: SalesState, DataCollectionState)
- **Contexts**: `{Level}Context` (예: AgentContext, SubgraphContext)

---

## 4. Agent Implementation

### Step 1: Define State

```python
# backend/service/core/states.py
class MyAgentState(BaseState):
    """에이전트 상태 정의"""

    # 입력
    user_query: str
    parameters: Dict[str, Any]

    # 처리 중 데이터
    processed_data: Annotated[List[Dict], add]

    # 결과
    final_result: Optional[Dict]
```

### Step 2: Create Agent Class

```python
# backend/service/agents/my_agent.py
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from ..core.config import Config
from ..core.context import AgentContext
from ..core.states import MyAgentState

class MyAgent:
    """새로운 에이전트 구현"""

    def __init__(self, config: Optional[Config] = None):
        self.agent_name = "my_agent"
        self.config = config or Config()
        self._init_llm()
        self._build_graph()

    def _init_llm(self):
        """LLM 초기화"""
        model_config = self.config.get_model_config("planning")
        self.planner_llm = ChatOpenAI(**model_config)

    def _build_graph(self):
        """워크플로우 그래프 구성"""
        self.workflow = StateGraph(
            state_schema=MyAgentState,
            context_schema=AgentContext
        )

        # 노드 추가
        self.workflow.add_node("plan", self.plan_execution)
        self.workflow.add_node("execute", self.execute_plan)
        self.workflow.add_node("format", self.format_results)

        # 엣지 추가
        self.workflow.add_edge(START, "plan")
        self.workflow.add_edge("plan", "execute")
        self.workflow.add_edge("execute", "format")
        self.workflow.add_edge("format", END)
```

### Step 3: Implement Node Functions

모든 노드 함수는 동일한 시그니처를 가져야 합니다:

```python
async def node_function(
    self,
    state: MyAgentState,
    runtime: Runtime[AgentContext]
) -> Dict[str, Any]:
    """
    노드 함수 구현

    Args:
        state: 현재 상태
        runtime: 런타임 컨텍스트

    Returns:
        상태 업데이트 딕셔너리
    """
    try:
        # 컨텍스트 접근
        user_id = runtime.context["user_id"]  # 필수 필드는 []
        language = runtime.context.get("language", "ko")  # 선택 필드는 .get()

        # 처리 로직
        result = await self.process_something(state)

        # 상태 업데이트 반환
        return {
            "processed_data": [result],
            "execution_step": "completed"
        }
    except Exception as e:
        return {
            "status": "failed",
            "errors": [str(e)]
        }
```

### Step 4: Implement Run Method

```python
async def run(
    self,
    query: str,
    user_id: str,
    session_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    에이전트 실행

    Args:
        query: 사용자 쿼리
        user_id: 사용자 ID
        session_id: 세션 ID
        **kwargs: 추가 컨텍스트 필드

    Returns:
        최종 상태
    """
    # 컨텍스트 생성
    context = create_agent_context(
        user_id=user_id,
        session_id=session_id,
        original_query=query,
        **kwargs
    )

    # 초기 상태 생성
    initial_state = {
        "user_query": query,
        "status": "pending",
        "execution_step": "starting",
        "errors": [],
        "processed_data": []
    }

    # 체크포인트 설정
    checkpoint_path = self.config.get_checkpoint_path(
        self.agent_name, session_id
    )

    # 실행
    async with AsyncSqliteSaver.from_conn_string(str(checkpoint_path)) as checkpointer:
        app = self.workflow.compile(checkpointer=checkpointer)

        result = await app.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": f"{session_id}_{self.agent_name}"}},
            context=context
        )

        return result
```

---

## 5. Subgraph Patterns

### Creating a Subgraph

```python
# backend/service/subgraphs/my_subgraph.py
class MySubgraph:
    """재사용 가능한 서브그래프"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tools = self._init_tools()

    def _init_tools(self):
        """도구 초기화"""
        return {
            "calculator": CalculationTool(),
            "analyzer": AnalysisTool()
        }

    def build_graph(self):
        """그래프 빌드"""
        workflow = StateGraph(
            state_schema=MySubgraphState,
            context_schema=SubgraphContext
        )

        # 노드 추가
        workflow.add_node("process", self.process_data)
        workflow.add_node("analyze", self.analyze_results)

        # 엣지 추가
        workflow.add_edge(START, "process")
        workflow.add_edge("process", "analyze")
        workflow.add_edge("analyze", END)

        return workflow
```

### Invoking a Subgraph from Agent

```python
async def _invoke_subgraph(
    self,
    subgraph_name: str,
    state: AgentState,
    runtime: Runtime[AgentContext],
    params: Optional[Dict] = None
) -> Dict[str, Any]:
    """서브그래프 호출"""

    # 서브그래프 컨텍스트 생성
    subgraph_context = create_subgraph_context(
        parent_context=dict(runtime.context),
        parent_agent=self.agent_name,
        subgraph_name=subgraph_name,
        **params or {}
    )

    # 서브그래프 임포트 및 실행
    if subgraph_name == "data_collection":
        from ..subgraphs.data_collection_subgraph import DataCollectionSubgraph

        subgraph = DataCollectionSubgraph()
        graph = subgraph.build_graph()
        app = graph.compile()

        # 서브그래프 상태 준비
        subgraph_state = {
            "query_params": state.get("parsed_query"),
            "target_databases": ["performance", "targets"],
            # ... 기타 필드
        }

        # 실행
        result = await app.ainvoke(subgraph_state, context=subgraph_context)

        return {
            "status": "completed",
            "data": result
        }
```

---

## 6. Tool Development

### Tool Template

```python
# backend/service/tools/my_tool.py
class MyTool:
    """도구 구현"""

    def __init__(self):
        self.name = "my_tool"
        self.description = "도구 설명"
        self.logger = logging.getLogger(__name__)

    def validate_input(self, **kwargs) -> bool:
        """입력 검증"""
        required = ["param1", "param2"]
        return all(k in kwargs for k in required)

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """도구 실행"""
        try:
            # 입력 검증
            if not self.validate_input(**kwargs):
                return {"error": "Invalid input parameters"}

            # 처리 로직
            result = await self._process(kwargs)

            # 결과 반환
            return {
                "status": "success",
                "data": result
            }

        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _process(self, params: Dict) -> Any:
        """실제 처리 로직"""
        # 구현
        pass
```

### SQL Executor Example

```python
class SQLExecutor:
    """SQL 실행 도구"""

    def __init__(self):
        base_path = Path(__file__).parent.parent.parent.parent
        self.db_paths = {
            "sales_performance": base_path / "database" / "storage" / "sales_performance" / "sales_performance_db.db",
            # ... 기타 DB
        }
        self.max_execution_time = 30
        self.max_result_rows = 10000

    def execute_query(
        self,
        sql: str,
        db_name: str = "sales_performance",
        params: Optional[List] = None
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        SQL 쿼리 실행

        Returns:
            (results, error_message)
        """
        try:
            db_path = self.db_paths.get(db_name)
            if not db_path or not db_path.exists():
                return [], f"Database {db_name} not found"

            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)

                rows = cursor.fetchmany(self.max_result_rows)
                results = [dict(row) for row in rows]

                return results, None

        except Exception as e:
            return [], str(e)
```

---

## 7. State Management

### State Update Patterns

#### Pattern 1: Partial Updates
노드는 변경할 필드만 반환:

```python
async def node_function(self, state, runtime):
    # 일부 필드만 업데이트
    return {
        "status": "processing",
        "execution_step": "data_collected"
    }
```

#### Pattern 2: Accumulated Updates
리듀서를 통한 누적:

```python
async def collect_data(self, state, runtime):
    data = await fetch_data()
    return {
        "collected_data": [data],  # add 리듀서로 누적
        "errors": []  # 빈 리스트는 무시됨
    }
```

#### Pattern 3: Conditional Updates
조건부 업데이트:

```python
async def process(self, state, runtime):
    result = {}

    if state.get("need_analysis"):
        analysis = await analyze()
        result["analysis_result"] = analysis

    if state.get("need_summary"):
        summary = await summarize()
        result["summary"] = summary

    return result
```

### State Factory Functions

```python
def create_sales_initial_state(**kwargs) -> Dict[str, Any]:
    """초기 상태 생성"""
    return {
        "status": "pending",
        "execution_step": "initializing",
        "errors": [],
        "start_time": datetime.now().isoformat(),
        "query": kwargs.get("query", ""),
        "period": kwargs.get("period", "monthly"),
        # ... 기타 필드
    }

def merge_state_updates(*updates: Dict[str, Any]) -> Dict[str, Any]:
    """여러 상태 업데이트 병합"""
    result = {}
    for update in updates:
        for key, value in update.items():
            if value is not None:
                result[key] = value
    return result
```

---

## 8. API Reference

### Agent Methods

```python
class Agent:
    async def run(
        self,
        query: str,
        user_id: str,
        session_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """에이전트 실행"""
        pass

    async def plan_execution(
        self,
        state: State,
        runtime: Runtime[Context]
    ) -> Dict[str, Any]:
        """실행 계획 수립"""
        pass

    async def execute_plan(
        self,
        state: State,
        runtime: Runtime[Context]
    ) -> Dict[str, Any]:
        """계획 실행"""
        pass

    async def format_results(
        self,
        state: State,
        runtime: Runtime[Context]
    ) -> Dict[str, Any]:
        """결과 포맷팅"""
        pass
```

### Context Functions

```python
def create_agent_context(
    user_id: str,
    session_id: str,
    **kwargs
) -> Dict[str, Any]:
    """에이전트 컨텍스트 생성"""
    pass

def create_subgraph_context(
    parent_context: Dict[str, Any],
    parent_agent: str,
    subgraph_name: str,
    **kwargs
) -> Dict[str, Any]:
    """서브그래프 컨텍스트 생성"""
    pass

def merge_with_config_defaults(
    context: Dict[str, Any],
    config: Config
) -> Dict[str, Any]:
    """컨텍스트와 설정 병합"""
    pass
```

### Config Methods

```python
class Config:
    @classmethod
    def get_database_path(cls, db_name: str) -> Path:
        """DB 경로 조회"""
        pass

    @classmethod
    def get_checkpoint_path(
        cls,
        agent_name: str,
        session_id: str
    ) -> Path:
        """체크포인트 경로 생성"""
        pass

    @classmethod
    def get_model_config(cls, model_type: str) -> Dict[str, Any]:
        """모델 설정 조회"""
        pass

    @classmethod
    def validate(cls) -> bool:
        """설정 검증"""
        pass
```

---

## 9. Best Practices

### 1. Error Handling

```python
async def node_function(self, state, runtime):
    try:
        # 메인 로직
        result = await process()
        return {"result": result}

    except asyncio.TimeoutError:
        logger.error("Timeout occurred")
        return {
            "status": "failed",
            "errors": ["Operation timed out"]
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "status": "failed",
            "errors": [str(e)]
        }
```

### 2. Logging

```python
import logging

logger = logging.getLogger(__name__)

class MyAgent:
    def __init__(self):
        self.logger = logging.getLogger(f"agent.{self.agent_name}")

    async def process(self, state, runtime):
        self.logger.info(f"Processing for user {runtime.context['user_id']}")
        self.logger.debug(f"State: {state}")

        try:
            result = await operation()
            self.logger.info("Operation successful")
            return result
        except Exception as e:
            self.logger.error(f"Operation failed: {e}", exc_info=True)
            raise
```

### 3. Type Hints

```python
from typing import Dict, Any, List, Optional, TypedDict
from langgraph.runtime import Runtime

async def process_data(
    self,
    state: MyState,
    runtime: Runtime[AgentContext]
) -> Dict[str, Any]:
    """타입 힌트 사용"""
    pass
```

### 4. Context Access Pattern

```python
async def node_function(self, state, runtime):
    # 필수 필드는 [] 사용
    user_id = runtime.context["user_id"]
    session_id = runtime.context["session_id"]

    # 선택 필드는 .get() 사용
    language = runtime.context.get("language", "ko")
    debug = runtime.context.get("debug_mode", False)

    # API 키 접근
    api_keys = runtime.context.get("api_keys", {})
    openai_key = api_keys.get("openai_api_key")
```

### 5. Subgraph Invocation

```python
# 서브그래프는 항상 명시적으로 임포트
if subgraph_name == "data_collection":
    from ..subgraphs.data_collection_subgraph import DataCollectionSubgraph

    # 인스턴스 생성 후 그래프 빌드
    subgraph = DataCollectionSubgraph()
    graph = subgraph.build_graph()
    app = graph.compile()

    # 컨텍스트 전달
    result = await app.ainvoke(subgraph_state, context=subgraph_context)
```

---

## 10. Troubleshooting

### Common Issues

#### Issue 1: Context Not Accessible
**문제**: `runtime.context` 접근 시 오류
**해결**:
```python
# 올바른 방법
self.workflow = StateGraph(
    state_schema=MyState,
    context_schema=AgentContext  # 반드시 지정
)
```

#### Issue 2: State Not Updating
**문제**: 상태가 업데이트되지 않음
**해결**:
```python
# 리듀서 확인
class MyState(TypedDict):
    # 누적이 필요한 경우
    data: Annotated[List[Dict], add]

    # 병합이 필요한 경우
    metrics: Annotated[Dict, merge_dicts]
```

#### Issue 3: Subgraph Import Error
**문제**: 서브그래프 임포트 실패
**해결**:
```python
# 동적 임포트 사용
if subgraph_name == "analysis":
    from ..subgraphs.analysis_subgraph import AnalysisSubgraph
```

#### Issue 4: Database Connection Error
**문제**: DB 연결 실패
**해결**:
```python
# 절대 경로 사용
base_path = Path(__file__).parent.parent.parent.parent
db_path = base_path / "database" / "storage" / "db.db"

# 존재 여부 확인
if not db_path.exists():
    logger.error(f"Database not found: {db_path}")
```

#### Issue 5: LLM Timeout
**문제**: LLM 응답 시간 초과
**해결**:
```python
# 타임아웃 설정
timeout = runtime.context.get("timeout_overrides", {}).get(
    "llm",
    self.config.TIMEOUTS["llm"]
)

response = await asyncio.wait_for(
    self.llm.ainvoke(messages),
    timeout=timeout
)
```

### Debugging Tips

1. **Enable Debug Mode**:
```python
context = create_agent_context(
    user_id="test",
    session_id="debug",
    debug_mode=True
)
```

2. **State Inspection**:
```python
def get_state_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """상태 요약"""
    return {
        "status": state.get("status"),
        "step": state.get("execution_step"),
        "errors": state.get("errors", []),
        "has_results": bool(state.get("final_report"))
    }
```

3. **Checkpoint Analysis**:
```python
# 체크포인트 DB 직접 조회
import sqlite3
conn = sqlite3.connect("checkpoints/agent/session.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM checkpoints")
```

4. **Logging Configuration**:
```env
LOG_LEVEL=DEBUG
```

---

## Appendix A: Complete Agent Example

```python
"""
완전한 에이전트 구현 예제
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ..core.config import Config
from ..core.context import AgentContext, create_agent_context
from ..core.states import CustomState

logger = logging.getLogger(__name__)


class CompleteAgent:
    """완전한 에이전트 구현"""

    def __init__(self, config: Optional[Config] = None):
        self.agent_name = "complete_agent"
        self.config = config or Config()
        self.logger = logging.getLogger(f"agent.{self.agent_name}")

        # LLM 초기화
        self._init_llm()

        # 워크플로우 빌드
        self._build_graph()

        # 서브그래프 레지스트리
        self.subgraphs = {}

        self.logger.info(f"{self.agent_name} initialized")

    def _init_llm(self):
        """LLM 초기화"""
        if not self.config.FEATURES.get("enable_llm_planning", True):
            self.planner_llm = None
            return

        model_config = self.config.get_model_config("planning")
        self.planner_llm = ChatOpenAI(**model_config)

    def _build_graph(self):
        """워크플로우 그래프 빌드"""
        self.workflow = StateGraph(
            state_schema=CustomState,
            context_schema=AgentContext
        )

        # 노드 추가
        self.workflow.add_node("validate", self.validate_input)
        self.workflow.add_node("plan", self.plan_execution)
        self.workflow.add_node("execute", self.execute_plan)
        self.workflow.add_node("format", self.format_results)

        # 엣지 추가
        self.workflow.add_edge(START, "validate")
        self.workflow.add_conditional_edges(
            "validate",
            self.route_after_validation,
            {
                "plan": "plan",
                "end": END
            }
        )
        self.workflow.add_edge("plan", "execute")
        self.workflow.add_edge("execute", "format")
        self.workflow.add_edge("format", END)

    async def validate_input(
        self,
        state: CustomState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """입력 검증"""
        try:
            query = state.get("query", "")

            if not query:
                return {
                    "status": "failed",
                    "errors": ["Query is required"]
                }

            return {
                "status": "validated",
                "execution_step": "input_validated"
            }

        except Exception as e:
            return {
                "status": "failed",
                "errors": [str(e)]
            }

    def route_after_validation(
        self,
        state: CustomState
    ) -> str:
        """검증 후 라우팅"""
        if state.get("status") == "failed":
            return "end"
        return "plan"

    async def plan_execution(
        self,
        state: CustomState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """실행 계획 수립"""
        # 구현...
        pass

    async def execute_plan(
        self,
        state: CustomState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """계획 실행"""
        # 구현...
        pass

    async def format_results(
        self,
        state: CustomState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """결과 포맷팅"""
        # 구현...
        pass

    async def run(
        self,
        query: str,
        user_id: str,
        session_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """에이전트 실행"""
        # 컨텍스트 생성
        context = create_agent_context(
            user_id=user_id,
            session_id=session_id,
            original_query=query,
            **kwargs
        )

        # 초기 상태
        initial_state = {
            "query": query,
            "status": "pending",
            "execution_step": "starting",
            "errors": [],
            "start_time": datetime.now().isoformat()
        }

        # 체크포인트 경로
        checkpoint_path = self.config.get_checkpoint_path(
            self.agent_name, session_id
        )

        # 실행
        async with AsyncSqliteSaver.from_conn_string(
            str(checkpoint_path)
        ) as checkpointer:
            app = self.workflow.compile(checkpointer=checkpointer)

            result = await app.ainvoke(
                initial_state,
                config={
                    "configurable": {
                        "thread_id": f"{session_id}_{self.agent_name}"
                    }
                },
                context=context
            )

            self.logger.info(f"Execution complete for session {session_id}")
            return result


# 사용 예제
async def main():
    agent = CompleteAgent()

    result = await agent.run(
        query="분석 요청",
        user_id="user123",
        session_id="session456",
        language="ko"
    )

    print("Result:", result.get("formatted_result"))


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Appendix B: Testing Guide

### Unit Testing

```python
# tests/test_agent.py
import pytest
import asyncio
from backend.service.agents.my_agent import MyAgent

@pytest.mark.asyncio
async def test_agent_execution():
    """에이전트 실행 테스트"""
    agent = MyAgent()

    result = await agent.run(
        query="test query",
        user_id="test_user",
        session_id="test_session"
    )

    assert result["status"] == "completed"
    assert "final_report" in result
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_agent_with_subgraph():
    """서브그래프 통합 테스트"""
    agent = MyAgent()

    # Mock subgraph response
    with patch.object(agent, '_invoke_subgraph') as mock:
        mock.return_value = {
            "status": "completed",
            "data": {"test": "data"}
        }

        result = await agent.run(
            query="test with subgraph",
            user_id="test_user",
            session_id="test_session"
        )

        mock.assert_called_once()
```

---

## Appendix C: Migration Guide

### Migrating from LangGraph 0.5.x to 0.6.x

1. **Context API 적용**:
```python
# Before (0.5.x)
workflow = StateGraph(MyState)

# After (0.6.x)
workflow = StateGraph(
    state_schema=MyState,
    context_schema=AgentContext
)
```

2. **노드 시그니처 변경**:
```python
# Before (0.5.x)
async def node(state: State) -> Dict:
    pass

# After (0.6.x)
async def node(
    self,
    state: State,
    runtime: Runtime[Context]
) -> Dict:
    pass
```

3. **컨텍스트 전달**:
```python
# Before (0.5.x)
result = await app.ainvoke(initial_state)

# After (0.6.x)
result = await app.ainvoke(
    initial_state,
    context=context
)
```

---

**Version**: 1.0.0
**Last Updated**: 2025-01-26
**Author**: NaruTalk Development Team