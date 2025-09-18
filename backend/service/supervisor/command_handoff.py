"""
Command-based Agent Handoff System for LangGraph 0.6.x
Command 기반 에이전트 핸드오프 시스템
"""

from typing import Dict, Any, List, Optional, Union, Callable, TypeVar
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import logging
import asyncio
import json
from langgraph.types import Command
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
import uuid

logger = logging.getLogger(__name__)

# 제네릭 타입
StateType = TypeVar('StateType', bound=Dict[str, Any])


class HandoffPriority(str, Enum):
    """핸드오프 우선순위"""
    CRITICAL = "critical"      # 즉시 실행
    HIGH = "high"             # 높은 우선순위
    NORMAL = "normal"          # 일반
    LOW = "low"               # 낮은 우선순위
    DEFERRED = "deferred"      # 지연 실행


class HandoffStrategy(str, Enum):
    """핸드오프 전략"""
    SEQUENTIAL = "sequential"   # 순차 실행
    PARALLEL = "parallel"       # 병렬 실행
    CONDITIONAL = "conditional" # 조건부 실행
    FALLBACK = "fallback"      # 폴백 실행
    BROADCAST = "broadcast"    # 브로드캐스트


@dataclass
class HandoffContext:
    """핸드오프 컨텍스트"""
    source_agent: str
    target_agent: str
    task_id: str
    priority: HandoffPriority
    strategy: HandoffStrategy
    created_at: datetime
    parent_task_id: Optional[str] = None
    timeout: float = 30.0
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            **asdict(self),
            "created_at": self.created_at.isoformat()
        }


@dataclass
class HandoffRequest:
    """핸드오프 요청"""
    context: HandoffContext
    task: Dict[str, Any]
    state_updates: Dict[str, Any] = field(default_factory=dict)
    required_capabilities: List[str] = field(default_factory=list)
    expected_output_schema: Optional[Dict[str, Any]] = None

    def to_command(self) -> Command:
        """LangGraph Command로 변환"""
        return Command(
            goto=self.context.target_agent,
            update=self.state_updates,
            metadata={
                "handoff_context": self.context.to_dict(),
                "task": self.task,
                "required_capabilities": self.required_capabilities
            }
        )


@dataclass
class HandoffResponse:
    """핸드오프 응답"""
    request: HandoffRequest
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    agent_chain: List[str] = field(default_factory=list)

    def to_state_update(self) -> Dict[str, Any]:
        """State 업데이트로 변환"""
        return {
            "handoff_results": {
                self.request.context.task_id: {
                    "success": self.success,
                    "result": self.result,
                    "error": self.error,
                    "execution_time": self.execution_time
                }
            },
            "agent_chain": self.agent_chain
        }


class CommandHandoffManager:
    """
    Command 기반 핸드오프 관리자
    - 에이전트 간 작업 위임
    - 실행 전략 관리
    - 결과 추적
    """

    def __init__(self):
        """Initialize CommandHandoffManager"""
        self.active_handoffs: Dict[str, HandoffRequest] = {}
        self.completed_handoffs: List[HandoffResponse] = []
        self.agent_capabilities: Dict[str, List[str]] = {}
        self.handoff_rules: Dict[str, Callable] = {}

        # 통계
        self.stats = {
            "total_handoffs": 0,
            "successful_handoffs": 0,
            "failed_handoffs": 0,
            "average_execution_time": 0.0
        }

        logger.info("CommandHandoffManager initialized")

    def register_agent_capabilities(
        self,
        agent_name: str,
        capabilities: List[str]
    ):
        """
        에이전트 능력 등록

        Args:
            agent_name: 에이전트 이름
            capabilities: 능력 목록
        """
        self.agent_capabilities[agent_name] = capabilities
        logger.info(f"Registered capabilities for {agent_name}: {capabilities}")

    def create_handoff(
        self,
        source_agent: str,
        target_agent: str,
        task: Dict[str, Any],
        priority: HandoffPriority = HandoffPriority.NORMAL,
        strategy: HandoffStrategy = HandoffStrategy.SEQUENTIAL,
        state_updates: Optional[Dict[str, Any]] = None,
        required_capabilities: Optional[List[str]] = None
    ) -> HandoffRequest:
        """
        핸드오프 생성

        Args:
            source_agent: 소스 에이전트
            target_agent: 대상 에이전트
            task: 작업 내용
            priority: 우선순위
            strategy: 실행 전략
            state_updates: State 업데이트
            required_capabilities: 필요 능력

        Returns:
            핸드오프 요청
        """
        task_id = f"{source_agent}_to_{target_agent}_{uuid.uuid4().hex[:8]}"

        context = HandoffContext(
            source_agent=source_agent,
            target_agent=target_agent,
            task_id=task_id,
            priority=priority,
            strategy=strategy,
            created_at=datetime.now()
        )

        request = HandoffRequest(
            context=context,
            task=task,
            state_updates=state_updates or {},
            required_capabilities=required_capabilities or []
        )

        self.active_handoffs[task_id] = request
        self.stats["total_handoffs"] += 1

        logger.info(f"Created handoff: {task_id}")
        return request

    def create_conditional_handoff(
        self,
        source_agent: str,
        condition: Callable[[StateType], str],
        agent_mapping: Dict[str, str],
        task: Dict[str, Any],
        state: StateType
    ) -> HandoffRequest:
        """
        조건부 핸드오프 생성

        Args:
            source_agent: 소스 에이전트
            condition: 조건 함수
            agent_mapping: 조건 결과 -> 에이전트 매핑
            task: 작업
            state: 현재 State

        Returns:
            핸드오프 요청
        """
        # 조건 평가
        condition_result = condition(state)
        target_agent = agent_mapping.get(condition_result)

        if not target_agent:
            raise ValueError(f"No agent mapped for condition result: {condition_result}")

        return self.create_handoff(
            source_agent=source_agent,
            target_agent=target_agent,
            task=task,
            strategy=HandoffStrategy.CONDITIONAL,
            state_updates={"condition_result": condition_result}
        )

    async def execute_handoff(
        self,
        request: HandoffRequest,
        agent_executor: Callable
    ) -> HandoffResponse:
        """
        핸드오프 실행

        Args:
            request: 핸드오프 요청
            agent_executor: 에이전트 실행 함수

        Returns:
            핸드오프 응답
        """
        start_time = datetime.now()
        agent_chain = [request.context.source_agent, request.context.target_agent]

        try:
            # 능력 검증
            if request.required_capabilities:
                if not self._validate_capabilities(
                    request.context.target_agent,
                    request.required_capabilities
                ):
                    raise ValueError(
                        f"Agent {request.context.target_agent} lacks required capabilities"
                    )

            # 에이전트 실행
            result = await asyncio.wait_for(
                agent_executor(request.context.target_agent, request.task),
                timeout=request.context.timeout
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            response = HandoffResponse(
                request=request,
                success=True,
                result=result,
                execution_time=execution_time,
                agent_chain=agent_chain
            )

            self.stats["successful_handoffs"] += 1

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            response = HandoffResponse(
                request=request,
                success=False,
                error=str(e),
                execution_time=execution_time,
                agent_chain=agent_chain
            )

            self.stats["failed_handoffs"] += 1
            logger.error(f"Handoff failed: {e}")

        # 완료 처리
        self._complete_handoff(request.context.task_id, response)

        return response

    async def execute_parallel_handoffs(
        self,
        requests: List[HandoffRequest],
        agent_executor: Callable
    ) -> List[HandoffResponse]:
        """
        병렬 핸드오프 실행

        Args:
            requests: 핸드오프 요청 목록
            agent_executor: 에이전트 실행 함수

        Returns:
            응답 목록
        """
        tasks = [
            self.execute_handoff(request, agent_executor)
            for request in requests
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 예외 처리
        processed = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                processed.append(
                    HandoffResponse(
                        request=requests[i],
                        success=False,
                        error=str(response)
                    )
                )
            else:
                processed.append(response)

        return processed

    async def execute_fallback_chain(
        self,
        source_agent: str,
        fallback_agents: List[str],
        task: Dict[str, Any],
        agent_executor: Callable
    ) -> HandoffResponse:
        """
        폴백 체인 실행

        Args:
            source_agent: 소스 에이전트
            fallback_agents: 폴백 에이전트 목록
            task: 작업
            agent_executor: 실행 함수

        Returns:
            성공한 첫 번째 응답
        """
        for target_agent in fallback_agents:
            request = self.create_handoff(
                source_agent=source_agent,
                target_agent=target_agent,
                task=task,
                strategy=HandoffStrategy.FALLBACK
            )

            response = await self.execute_handoff(request, agent_executor)

            if response.success:
                return response

            logger.warning(f"Fallback to {target_agent} failed, trying next")

        # 모두 실패
        return HandoffResponse(
            request=request,
            success=False,
            error="All fallback agents failed"
        )

    def _validate_capabilities(
        self,
        agent_name: str,
        required: List[str]
    ) -> bool:
        """능력 검증"""
        if agent_name not in self.agent_capabilities:
            return False

        agent_caps = set(self.agent_capabilities[agent_name])
        required_caps = set(required)

        return required_caps.issubset(agent_caps)

    def _complete_handoff(self, task_id: str, response: HandoffResponse):
        """핸드오프 완료 처리"""
        if task_id in self.active_handoffs:
            del self.active_handoffs[task_id]

        self.completed_handoffs.append(response)

        # 통계 업데이트
        self._update_stats(response)

    def _update_stats(self, response: HandoffResponse):
        """통계 업데이트"""
        total = self.stats["successful_handoffs"] + self.stats["failed_handoffs"]
        if total > 0:
            current_avg = self.stats["average_execution_time"]
            new_avg = (
                (current_avg * (total - 1) + response.execution_time) / total
            )
            self.stats["average_execution_time"] = new_avg

    def create_handoff_tool(
        self,
        source_agent: str,
        target_agent: str,
        task_template: str
    ) -> Callable:
        """
        핸드오프 도구 생성

        Args:
            source_agent: 소스 에이전트
            target_agent: 대상 에이전트
            task_template: 작업 템플릿

        Returns:
            핸드오프 도구 함수
        """
        async def handoff_tool(task_params: Dict[str, Any]) -> Command:
            """생성된 핸드오프 도구"""
            # 작업 생성
            task = {
                "template": task_template,
                "params": task_params,
                "timestamp": datetime.now().isoformat()
            }

            # 핸드오프 생성
            request = self.create_handoff(
                source_agent=source_agent,
                target_agent=target_agent,
                task=task
            )

            # Command 반환
            return request.to_command()

        handoff_tool.__name__ = f"handoff_to_{target_agent}"
        handoff_tool.__doc__ = f"Handoff task to {target_agent}"

        return handoff_tool

    def get_handoff_stats(self) -> Dict[str, Any]:
        """핸드오프 통계 반환"""
        total = self.stats["total_handoffs"]

        return {
            **self.stats,
            "active_handoffs": len(self.active_handoffs),
            "completed_handoffs": len(self.completed_handoffs),
            "success_rate": (
                self.stats["successful_handoffs"] / total * 100
                if total > 0 else 0
            ),
            "agent_handoff_matrix": self._get_handoff_matrix()
        }

    def _get_handoff_matrix(self) -> Dict[str, Dict[str, int]]:
        """에이전트 간 핸드오프 매트릭스"""
        matrix = {}

        for response in self.completed_handoffs:
            source = response.request.context.source_agent
            target = response.request.context.target_agent

            if source not in matrix:
                matrix[source] = {}

            if target not in matrix[source]:
                matrix[source][target] = 0

            matrix[source][target] += 1

        return matrix


class HandoffOrchestrator:
    """
    핸드오프 오케스트레이터
    - 복잡한 핸드오프 패턴 관리
    - 워크플로우 실행
    """

    def __init__(self, handoff_manager: CommandHandoffManager):
        """
        Initialize HandoffOrchestrator

        Args:
            handoff_manager: 핸드오프 매니저
        """
        self.manager = handoff_manager
        self.workflows: Dict[str, List[HandoffRequest]] = {}

        logger.info("HandoffOrchestrator initialized")

    def create_workflow(
        self,
        workflow_name: str,
        steps: List[Tuple[str, str, Dict[str, Any]]]
    ) -> str:
        """
        워크플로우 생성

        Args:
            workflow_name: 워크플로우 이름
            steps: (소스, 대상, 작업) 튜플 리스트

        Returns:
            워크플로우 ID
        """
        workflow_id = f"{workflow_name}_{uuid.uuid4().hex[:8]}"
        requests = []

        for i, (source, target, task) in enumerate(steps):
            request = self.manager.create_handoff(
                source_agent=source,
                target_agent=target,
                task=task,
                state_updates={"workflow_step": i + 1}
            )

            # 이전 단계와 연결
            if i > 0:
                request.context.parent_task_id = requests[i-1].context.task_id

            requests.append(request)

        self.workflows[workflow_id] = requests

        logger.info(f"Created workflow '{workflow_id}' with {len(steps)} steps")
        return workflow_id

    async def execute_workflow(
        self,
        workflow_id: str,
        agent_executor: Callable,
        parallel: bool = False
    ) -> List[HandoffResponse]:
        """
        워크플로우 실행

        Args:
            workflow_id: 워크플로우 ID
            agent_executor: 에이전트 실행 함수
            parallel: 병렬 실행 여부

        Returns:
            응답 목록
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow '{workflow_id}' not found")

        requests = self.workflows[workflow_id]

        if parallel:
            # 병렬 실행
            return await self.manager.execute_parallel_handoffs(
                requests, agent_executor
            )
        else:
            # 순차 실행
            responses = []
            for request in requests:
                response = await self.manager.execute_handoff(
                    request, agent_executor
                )
                responses.append(response)

                # 실패시 중단
                if not response.success:
                    logger.warning(f"Workflow '{workflow_id}' stopped at step {len(responses)}")
                    break

            return responses


# 전역 인스턴스
_global_handoff_manager: Optional[CommandHandoffManager] = None


def get_handoff_manager() -> CommandHandoffManager:
    """전역 핸드오프 매니저 반환"""
    global _global_handoff_manager
    if _global_handoff_manager is None:
        _global_handoff_manager = CommandHandoffManager()

        # 기본 에이전트 능력 등록
        _global_handoff_manager.register_agent_capabilities(
            "sql_analysis",
            ["query_generation", "data_analysis", "statistics"]
        )
        _global_handoff_manager.register_agent_capabilities(
            "information_retrieval",
            ["search", "ranking", "filtering"]
        )
        _global_handoff_manager.register_agent_capabilities(
            "document_generation",
            ["template_processing", "formatting", "export"]
        )
        _global_handoff_manager.register_agent_capabilities(
            "compliance_validation",
            ["rule_checking", "risk_assessment", "reporting"]
        )

    return _global_handoff_manager