"""
Subgraph Architecture for LangGraph 0.6.x
서브그래프 아키텍처 - 모듈화된 워크플로우 관리
"""

from typing import Dict, Any, List, Optional, TypeVar, Generic, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime
import asyncio
from langgraph.graph import StateGraph, END, START
from langgraph.types import Command
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import uuid

logger = logging.getLogger(__name__)

# 제네릭 State 타입
StateType = TypeVar('StateType', bound=Dict[str, Any])


class SubgraphType(str, Enum):
    """서브그래프 타입"""
    ANALYSIS = "analysis"          # 분석 워크플로우
    RETRIEVAL = "retrieval"        # 검색 워크플로우
    GENERATION = "generation"      # 생성 워크플로우
    VALIDATION = "validation"      # 검증 워크플로우
    TRANSFORMATION = "transformation"  # 변환 워크플로우


@dataclass
class SubgraphConfig:
    """서브그래프 설정"""
    name: str
    type: SubgraphType
    description: str
    max_iterations: int = 10
    timeout: float = 30.0
    retry_on_failure: bool = True
    max_retries: int = 3
    shared_state_keys: List[str] = field(default_factory=list)
    input_transformer: Optional[Callable] = None
    output_transformer: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubgraphResult:
    """서브그래프 실행 결과"""
    subgraph_name: str
    success: bool
    output: Dict[str, Any]
    execution_time: float
    iterations: int
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Subgraph(Generic[StateType]):
    """
    재사용 가능한 서브그래프
    - 독립적인 State 스키마
    - 부모 그래프와 통신
    """

    def __init__(
        self,
        config: SubgraphConfig,
        state_class: type = Dict[str, Any]
    ):
        """
        Initialize Subgraph

        Args:
            config: 서브그래프 설정
            state_class: State 클래스
        """
        self.config = config
        self.state_class = state_class
        self.graph: Optional[StateGraph] = None
        self.nodes: Dict[str, Callable] = {}
        self.edges: List[Tuple[str, str, Optional[Callable]]] = []

        logger.info(f"Subgraph '{config.name}' initialized")

    def add_node(
        self,
        node_name: str,
        node_func: Callable[[StateType], StateType]
    ):
        """
        노드 추가

        Args:
            node_name: 노드 이름
            node_func: 노드 함수
        """
        self.nodes[node_name] = node_func
        logger.debug(f"Added node '{node_name}' to subgraph '{self.config.name}'")

    def add_edge(
        self,
        from_node: str,
        to_node: str,
        condition: Optional[Callable] = None
    ):
        """
        엣지 추가

        Args:
            from_node: 시작 노드
            to_node: 대상 노드
            condition: 조건 함수
        """
        self.edges.append((from_node, to_node, condition))
        logger.debug(f"Added edge '{from_node}' -> '{to_node}' in subgraph '{self.config.name}'")

    def build(self) -> StateGraph:
        """서브그래프 빌드"""
        if not self.nodes:
            raise ValueError(f"Subgraph '{self.config.name}' has no nodes")

        # StateGraph 생성
        self.graph = StateGraph(self.state_class)

        # 노드 추가
        for node_name, node_func in self.nodes.items():
            self.graph.add_node(node_name, node_func)

        # 엣지 추가
        for from_node, to_node, condition in self.edges:
            if condition:
                self.graph.add_conditional_edges(from_node, condition, {to_node: to_node})
            else:
                self.graph.add_edge(from_node, to_node)

        logger.info(f"Built subgraph '{self.config.name}' with {len(self.nodes)} nodes")
        return self.graph

    async def execute(
        self,
        input_state: Dict[str, Any],
        parent_state: Optional[Dict[str, Any]] = None
    ) -> SubgraphResult:
        """
        서브그래프 실행

        Args:
            input_state: 입력 State
            parent_state: 부모 State

        Returns:
            실행 결과
        """
        start_time = datetime.now()
        errors = []
        iterations = 0

        try:
            # 입력 변환
            if self.config.input_transformer:
                input_state = self.config.input_transformer(input_state, parent_state)

            # State 병합 (공유 키)
            if parent_state and self.config.shared_state_keys:
                for key in self.config.shared_state_keys:
                    if key in parent_state:
                        input_state[key] = parent_state[key]

            # 서브그래프 실행
            if not self.graph:
                self.build()

            compiled_graph = self.graph.compile()

            # 비동기 실행 with 타임아웃
            result = await asyncio.wait_for(
                compiled_graph.ainvoke(input_state),
                timeout=self.config.timeout
            )

            # 출력 변환
            if self.config.output_transformer:
                result = self.config.output_transformer(result, parent_state)

            execution_time = (datetime.now() - start_time).total_seconds()

            return SubgraphResult(
                subgraph_name=self.config.name,
                success=True,
                output=result,
                execution_time=execution_time,
                iterations=iterations,
                errors=errors,
                metadata={"config": self.config.metadata}
            )

        except asyncio.TimeoutError:
            errors.append(f"Subgraph '{self.config.name}' timed out after {self.config.timeout}s")
            logger.error(errors[-1])
        except Exception as e:
            errors.append(f"Subgraph '{self.config.name}' error: {str(e)}")
            logger.error(errors[-1])

        execution_time = (datetime.now() - start_time).total_seconds()

        return SubgraphResult(
            subgraph_name=self.config.name,
            success=False,
            output={},
            execution_time=execution_time,
            iterations=iterations,
            errors=errors
        )


class SubgraphManager:
    """
    서브그래프 관리자
    - 서브그래프 레지스트리
    - 병렬 실행
    - 의존성 관리
    """

    def __init__(self):
        """Initialize SubgraphManager"""
        self.subgraphs: Dict[str, Subgraph] = {}
        self.execution_history: List[SubgraphResult] = []
        self.dependencies: Dict[str, List[str]] = {}  # 서브그래프 의존성

        logger.info("SubgraphManager initialized")

    def register_subgraph(
        self,
        subgraph: Subgraph,
        dependencies: Optional[List[str]] = None
    ):
        """
        서브그래프 등록

        Args:
            subgraph: 서브그래프 인스턴스
            dependencies: 의존하는 서브그래프 이름 목록
        """
        name = subgraph.config.name
        self.subgraphs[name] = subgraph

        if dependencies:
            self.dependencies[name] = dependencies

        logger.info(f"Registered subgraph '{name}'")

    def create_analysis_subgraph(self) -> Subgraph:
        """분석 서브그래프 생성 예제"""
        config = SubgraphConfig(
            name="data_analysis",
            type=SubgraphType.ANALYSIS,
            description="데이터 분석 워크플로우",
            shared_state_keys=["user_id", "session_id", "context"]
        )

        subgraph = Subgraph(config)

        # 노드 정의
        async def preprocess_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """데이터 전처리"""
            state["preprocessed"] = True
            state["data_cleaned"] = True
            return state

        async def analyze_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """데이터 분석"""
            state["analysis_result"] = {
                "patterns": ["pattern1", "pattern2"],
                "insights": ["insight1", "insight2"]
            }
            return state

        async def summarize_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """결과 요약"""
            state["summary"] = "분석 완료: 2개 패턴, 2개 인사이트 발견"
            return state

        # 노드 추가
        subgraph.add_node("preprocess", preprocess_node)
        subgraph.add_node("analyze", analyze_node)
        subgraph.add_node("summarize", summarize_node)

        # 엣지 추가
        subgraph.add_edge(START, "preprocess")
        subgraph.add_edge("preprocess", "analyze")
        subgraph.add_edge("analyze", "summarize")
        subgraph.add_edge("summarize", END)

        return subgraph

    def create_retrieval_subgraph(self) -> Subgraph:
        """검색 서브그래프 생성 예제"""
        config = SubgraphConfig(
            name="information_retrieval",
            type=SubgraphType.RETRIEVAL,
            description="정보 검색 워크플로우",
            max_iterations=5
        )

        subgraph = Subgraph(config)

        async def search_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """검색 실행"""
            state["search_results"] = [
                {"id": 1, "relevance": 0.9, "content": "Result 1"},
                {"id": 2, "relevance": 0.8, "content": "Result 2"}
            ]
            return state

        async def rank_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """결과 랭킹"""
            results = state.get("search_results", [])
            state["ranked_results"] = sorted(
                results,
                key=lambda x: x["relevance"],
                reverse=True
            )
            return state

        async def filter_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """결과 필터링"""
            ranked = state.get("ranked_results", [])
            state["filtered_results"] = [
                r for r in ranked if r["relevance"] > 0.7
            ]
            return state

        # 노드 및 엣지 구성
        subgraph.add_node("search", search_node)
        subgraph.add_node("rank", rank_node)
        subgraph.add_node("filter", filter_node)

        subgraph.add_edge(START, "search")
        subgraph.add_edge("search", "rank")
        subgraph.add_edge("rank", "filter")
        subgraph.add_edge("filter", END)

        return subgraph

    async def execute_subgraph(
        self,
        subgraph_name: str,
        input_state: Dict[str, Any],
        parent_state: Optional[Dict[str, Any]] = None
    ) -> SubgraphResult:
        """
        단일 서브그래프 실행

        Args:
            subgraph_name: 서브그래프 이름
            input_state: 입력 State
            parent_state: 부모 State

        Returns:
            실행 결과
        """
        if subgraph_name not in self.subgraphs:
            raise ValueError(f"Subgraph '{subgraph_name}' not found")

        subgraph = self.subgraphs[subgraph_name]
        result = await subgraph.execute(input_state, parent_state)

        # 히스토리 저장
        self.execution_history.append(result)

        return result

    async def execute_parallel(
        self,
        subgraph_names: List[str],
        input_states: Union[Dict[str, Any], List[Dict[str, Any]]],
        parent_state: Optional[Dict[str, Any]] = None
    ) -> List[SubgraphResult]:
        """
        병렬 서브그래프 실행

        Args:
            subgraph_names: 서브그래프 이름 목록
            input_states: 입력 State (단일 또는 리스트)
            parent_state: 부모 State

        Returns:
            실행 결과 목록
        """
        # 입력 State 정규화
        if isinstance(input_states, dict):
            input_states = [input_states] * len(subgraph_names)

        if len(input_states) != len(subgraph_names):
            raise ValueError("Number of input states must match number of subgraphs")

        # 병렬 실행
        tasks = [
            self.execute_subgraph(name, state, parent_state)
            for name, state in zip(subgraph_names, input_states)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 예외 처리
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    SubgraphResult(
                        subgraph_name=subgraph_names[i],
                        success=False,
                        output={},
                        execution_time=0,
                        iterations=0,
                        errors=[str(result)]
                    )
                )
            else:
                processed_results.append(result)

        return processed_results

    async def execute_with_dependencies(
        self,
        subgraph_name: str,
        input_state: Dict[str, Any]
    ) -> Dict[str, SubgraphResult]:
        """
        의존성을 고려한 서브그래프 실행

        Args:
            subgraph_name: 서브그래프 이름
            input_state: 입력 State

        Returns:
            실행 결과 (의존성 포함)
        """
        results = {}

        # 의존성 실행
        if subgraph_name in self.dependencies:
            for dep_name in self.dependencies[subgraph_name]:
                if dep_name not in results:
                    dep_result = await self.execute_subgraph(dep_name, input_state)
                    results[dep_name] = dep_result

                    # 의존성 결과를 입력에 병합
                    if dep_result.success:
                        input_state.update(dep_result.output)

        # 메인 서브그래프 실행
        main_result = await self.execute_subgraph(subgraph_name, input_state)
        results[subgraph_name] = main_result

        return results

    def get_execution_stats(self) -> Dict[str, Any]:
        """실행 통계 반환"""
        if not self.execution_history:
            return {"total_executions": 0}

        total = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r.success)

        avg_time = sum(r.execution_time for r in self.execution_history) / total

        return {
            "total_executions": total,
            "successful_executions": successful,
            "success_rate": (successful / total) * 100,
            "average_execution_time": avg_time,
            "subgraph_stats": self._get_per_subgraph_stats()
        }

    def _get_per_subgraph_stats(self) -> Dict[str, Dict[str, Any]]:
        """서브그래프별 통계"""
        stats = {}

        for result in self.execution_history:
            name = result.subgraph_name
            if name not in stats:
                stats[name] = {
                    "executions": 0,
                    "successes": 0,
                    "total_time": 0
                }

            stats[name]["executions"] += 1
            if result.success:
                stats[name]["successes"] += 1
            stats[name]["total_time"] += result.execution_time

        # 평균 계산
        for name, stat in stats.items():
            stat["success_rate"] = (stat["successes"] / stat["executions"]) * 100
            stat["average_time"] = stat["total_time"] / stat["executions"]

        return stats


# 전역 매니저 인스턴스
_global_manager: Optional[SubgraphManager] = None


def get_subgraph_manager() -> SubgraphManager:
    """전역 서브그래프 매니저 반환"""
    global _global_manager
    if _global_manager is None:
        _global_manager = SubgraphManager()

        # 기본 서브그래프 등록
        _global_manager.register_subgraph(_global_manager.create_analysis_subgraph())
        _global_manager.register_subgraph(_global_manager.create_retrieval_subgraph())

    return _global_manager