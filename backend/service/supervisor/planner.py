"""
Smart Planner for Medical Supervisor
실행 계획 수립 및 최적화
"""

from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging
from collections import defaultdict
import networkx as nx

from .state import MedicalSupervisorState, PlanningState
from .context_manager import MedicalContext

logger = logging.getLogger(__name__)


@dataclass
class TaskNode:
    """작업 노드 정의"""

    id: str
    name: str
    agent: str
    estimated_time: float
    required_capabilities: List[str]
    dependencies: List[str] = field(default_factory=list)
    priority: int = 0
    can_parallel: bool = True
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    """실행 계획"""

    tasks: List[TaskNode]
    execution_order: List[List[str]]  # 병렬 실행 그룹
    estimated_total_time: float
    optimization_applied: bool
    fallback_strategies: List[Dict[str, Any]]
    resource_allocation: Dict[str, float]


class SmartPlanner:
    """
    스마트 실행 계획 수립
    - 의존성 분석
    - 병렬 실행 기회 식별
    - 리소스 최적화
    """

    def __init__(self):
        """Initialize Smart Planner"""

        self.task_templates = self._load_task_templates()
        self.optimization_rules = self._load_optimization_rules()

    def _load_task_templates(self) -> Dict[str, TaskNode]:
        """작업 템플릿 로드"""

        return {
            "data_query": TaskNode(
                id="data_query",
                name="데이터 쿼리 실행",
                agent="data_analysis_expert",
                estimated_time=10.0,
                required_capabilities=["sql_query", "data_aggregation"]
            ),
            "trend_analysis": TaskNode(
                id="trend_analysis",
                name="트렌드 분석",
                agent="data_analysis_expert",
                estimated_time=15.0,
                required_capabilities=["trend_analysis", "data_aggregation"]
            ),
            "hr_search": TaskNode(
                id="hr_search",
                name="인사정보 검색",
                agent="info_retrieval_expert",
                estimated_time=5.0,
                required_capabilities=["search", "retrieval"]
            ),
            "regulation_search": TaskNode(
                id="regulation_search",
                name="규정 검색",
                agent="info_retrieval_expert",
                estimated_time=8.0,
                required_capabilities=["regulation_search"]
            ),
            "web_search": TaskNode(
                id="web_search",
                name="웹 검색",
                agent="info_retrieval_expert",
                estimated_time=12.0,
                required_capabilities=["web_search", "api_integration"]
            ),
            "report_generation": TaskNode(
                id="report_generation",
                name="보고서 생성",
                agent="doc_generation_expert",
                estimated_time=20.0,
                required_capabilities=["document_generation", "formatting"],
                can_parallel=False  # 순차 실행 필요
            ),
            "compliance_check": TaskNode(
                id="compliance_check",
                name="규정 준수 확인",
                agent="compliance_expert",
                estimated_time=15.0,
                required_capabilities=["compliance_check", "regulation_validation"],
                priority=10,  # 높은 우선순위
                can_parallel=False
            ),
            "data_storage": TaskNode(
                id="data_storage",
                name="데이터 저장",
                agent="doc_generation_expert",
                estimated_time=5.0,
                required_capabilities=["data_storage", "db_write"]
            )
        }

    def _load_optimization_rules(self) -> Dict[str, Any]:
        """최적화 규칙 로드"""

        return {
            "parallel_threshold": 0.7,  # 병렬 실행 임계값
            "max_parallel_tasks": 3,    # 최대 동시 실행 작업 수
            "resource_limits": {
                "cpu": 0.8,
                "memory": 0.7,
                "api_calls": 100
            },
            "priority_weights": {
                "compliance": 2.0,
                "user_request": 1.5,
                "background": 0.5
            }
        }

    async def create_plan(
        self,
        state: MedicalSupervisorState,
        context: MedicalContext
    ) -> ExecutionPlan:
        """
        실행 계획 생성
        """

        # 1. 필요한 작업 식별
        tasks = await self._identify_required_tasks(state, context)

        # 2. 의존성 그래프 구축
        dependency_graph = self._build_dependency_graph(tasks)

        # 3. 병렬 실행 기회 식별
        parallel_groups = self._identify_parallel_opportunities(dependency_graph)

        # 4. 리소스 할당 최적화
        resource_allocation = self._optimize_resource_allocation(tasks, context)

        # 5. 실행 순서 결정
        execution_order = self._determine_execution_order(
            tasks,
            dependency_graph,
            parallel_groups
        )

        # 6. Fallback 전략 수립
        fallback_strategies = self._create_fallback_strategies(tasks, context)

        # 7. 예상 시간 계산
        estimated_time = self._calculate_estimated_time(tasks, execution_order)

        plan = ExecutionPlan(
            tasks=tasks,
            execution_order=execution_order,
            estimated_total_time=estimated_time,
            optimization_applied=True,
            fallback_strategies=fallback_strategies,
            resource_allocation=resource_allocation
        )

        logger.info(
            f"Execution plan created: {len(tasks)} tasks, "
            f"{len(execution_order)} phases, "
            f"estimated time: {estimated_time:.1f}s"
        )

        return plan

    async def _identify_required_tasks(
        self,
        state: MedicalSupervisorState,
        context: MedicalContext
    ) -> List[TaskNode]:
        """
        필요한 작업 식별
        """

        tasks = []
        task_counter = 0

        # 의도 분석 결과 기반
        if state["intent_analysis"]:
            intents = state["intent_analysis"]["analyzed_intents"]
            capabilities = state["intent_analysis"]["required_capabilities"]

            # 각 capability에 대한 작업 생성
            for capability in capabilities:
                if capability == "sql_query":
                    task = TaskNode(
                        id=f"task_{task_counter}",
                        name="데이터 쿼리 실행",
                        agent="data_analysis_expert",
                        estimated_time=10.0,
                        required_capabilities=["sql_query"],
                        metadata={"target": context.target_entity}
                    )
                    tasks.append(task)
                    task_counter += 1

                elif capability == "trend_analysis":
                    # 데이터 쿼리가 선행되어야 함
                    query_task_id = f"task_{task_counter - 1}" if task_counter > 0 else None
                    task = TaskNode(
                        id=f"task_{task_counter}",
                        name="트렌드 분석",
                        agent="data_analysis_expert",
                        estimated_time=15.0,
                        required_capabilities=["trend_analysis"],
                        dependencies=[query_task_id] if query_task_id else [],
                        metadata={"time_range": context.time_range}
                    )
                    tasks.append(task)
                    task_counter += 1

                elif capability == "search":
                    task = TaskNode(
                        id=f"task_{task_counter}",
                        name="정보 검색",
                        agent="info_retrieval_expert",
                        estimated_time=8.0,
                        required_capabilities=["search", "retrieval"],
                        metadata={"sources": context.data_sources}
                    )
                    tasks.append(task)
                    task_counter += 1

                elif capability == "document_generation":
                    # 이전 작업들의 결과가 필요
                    dependencies = [t.id for t in tasks if t.agent != "doc_generation_expert"]
                    task = TaskNode(
                        id=f"task_{task_counter}",
                        name="문서 생성",
                        agent="doc_generation_expert",
                        estimated_time=20.0,
                        required_capabilities=["document_generation"],
                        dependencies=dependencies,
                        can_parallel=False
                    )
                    tasks.append(task)
                    task_counter += 1

        # 규정 검토가 필요한 경우
        if context.compliance_level == "strict" or context.domain_type == "규정검토":
            # 모든 작업 후 규정 검토
            all_task_ids = [t.id for t in tasks]
            compliance_task = TaskNode(
                id=f"task_{task_counter}",
                name="규정 준수 최종 확인",
                agent="compliance_expert",
                estimated_time=15.0,
                required_capabilities=["compliance_check"],
                dependencies=all_task_ids,
                priority=10,
                can_parallel=False
            )
            tasks.append(compliance_task)

        return tasks

    def _build_dependency_graph(self, tasks: List[TaskNode]) -> nx.DiGraph:
        """
        의존성 그래프 구축
        """

        graph = nx.DiGraph()

        # 노드 추가
        for task in tasks:
            graph.add_node(
                task.id,
                task=task,
                agent=task.agent,
                priority=task.priority
            )

        # 엣지 추가 (의존성)
        for task in tasks:
            for dep in task.dependencies:
                if dep:  # None 체크
                    graph.add_edge(dep, task.id)

        # 순환 의존성 체크
        if not nx.is_directed_acyclic_graph(graph):
            cycles = list(nx.simple_cycles(graph))
            logger.warning(f"Circular dependencies detected: {cycles}")
            # 순환 의존성 제거 로직
            for cycle in cycles:
                if len(cycle) > 1:
                    graph.remove_edge(cycle[-1], cycle[0])

        return graph

    def _identify_parallel_opportunities(
        self,
        dependency_graph: nx.DiGraph
    ) -> List[List[str]]:
        """
        병렬 실행 기회 식별
        """

        # 위상 정렬로 레벨별 그룹화
        levels = defaultdict(list)

        # 각 노드의 레벨 계산 (최대 경로 길이)
        for node in nx.topological_sort(dependency_graph):
            predecessors = list(dependency_graph.predecessors(node))
            if not predecessors:
                level = 0
            else:
                level = max(levels[pred] for pred in predecessors) + 1
            levels[node] = level

        # 레벨별로 그룹화
        level_groups = defaultdict(list)
        for node, level in levels.items():
            level_groups[level].append(node)

        # 병렬 실행 가능 여부 확인
        parallel_groups = []
        for level in sorted(level_groups.keys()):
            group = level_groups[level]

            # 같은 레벨의 작업들 중 병렬 실행 가능한 것들 필터링
            parallel_tasks = []
            sequential_tasks = []

            for task_id in group:
                task = dependency_graph.nodes[task_id]["task"]
                if task.can_parallel:
                    parallel_tasks.append(task_id)
                else:
                    sequential_tasks.append(task_id)

            # 병렬 작업 그룹 추가
            if len(parallel_tasks) > 1:
                # 리소스 제한에 따라 분할
                max_parallel = self.optimization_rules["max_parallel_tasks"]
                for i in range(0, len(parallel_tasks), max_parallel):
                    parallel_groups.append(parallel_tasks[i:i+max_parallel])
            elif parallel_tasks:
                parallel_groups.append(parallel_tasks)

            # 순차 작업은 개별 그룹으로
            for task_id in sequential_tasks:
                parallel_groups.append([task_id])

        return parallel_groups

    def _optimize_resource_allocation(
        self,
        tasks: List[TaskNode],
        context: MedicalContext
    ) -> Dict[str, float]:
        """
        리소스 할당 최적화
        """

        allocation = {}
        total_priority = sum(task.priority for task in tasks) or 1

        # 에이전트별 작업량 계산
        agent_workload = defaultdict(float)
        for task in tasks:
            agent_workload[task.agent] += task.estimated_time

        # 우선순위 기반 리소스 할당
        for agent, workload in agent_workload.items():
            # 기본 할당
            base_allocation = workload / sum(agent_workload.values())

            # 우선순위 가중치 적용
            priority_weight = 1.0
            if context.priority == "high":
                priority_weight = 1.5
            elif context.priority == "low":
                priority_weight = 0.7

            allocation[agent] = min(base_allocation * priority_weight, 1.0)

        # 규정 검토가 필요한 경우 compliance_expert에 더 많은 리소스
        if context.compliance_level == "strict":
            allocation["compliance_expert"] = min(
                allocation.get("compliance_expert", 0) * 1.5,
                1.0
            )

        return allocation

    def _determine_execution_order(
        self,
        tasks: List[TaskNode],
        dependency_graph: nx.DiGraph,
        parallel_groups: List[List[str]]
    ) -> List[List[str]]:
        """
        실행 순서 결정
        """

        # 우선순위 기반 재정렬
        execution_order = []

        for group in parallel_groups:
            # 그룹 내 작업들의 우선순위 확인
            group_tasks = [
                next(t for t in tasks if t.id == task_id)
                for task_id in group
            ]

            # 높은 우선순위 작업이 있으면 분리
            high_priority = [t.id for t in group_tasks if t.priority >= 8]
            normal_priority = [t.id for t in group_tasks if t.priority < 8]

            if high_priority:
                execution_order.append(high_priority)
            if normal_priority:
                execution_order.append(normal_priority)

        # 빈 그룹 제거
        execution_order = [group for group in execution_order if group]

        return execution_order

    def _create_fallback_strategies(
        self,
        tasks: List[TaskNode],
        context: MedicalContext
    ) -> List[Dict[str, Any]]:
        """
        Fallback 전략 수립
        """

        strategies = []

        # 각 에이전트별 fallback
        agent_fallbacks = {
            "data_analysis_expert": {
                "primary": "sql_query",
                "fallback": "cached_data",
                "condition": "database_timeout"
            },
            "info_retrieval_expert": {
                "primary": "web_search",
                "fallback": "local_search",
                "condition": "api_limit_exceeded"
            },
            "doc_generation_expert": {
                "primary": "template_generation",
                "fallback": "simple_text",
                "condition": "template_error"
            },
            "compliance_expert": {
                "primary": "automated_check",
                "fallback": "manual_review_flag",
                "condition": "validation_error"
            }
        }

        for task in tasks:
            if task.agent in agent_fallbacks:
                fallback = agent_fallbacks[task.agent].copy()
                fallback["task_id"] = task.id
                fallback["retry_limit"] = task.max_retries
                strategies.append(fallback)

        # 전체 실패 시 fallback
        strategies.append({
            "type": "global_fallback",
            "action": "return_partial_results",
            "condition": "multiple_agent_failures",
            "threshold": 0.5  # 50% 이상 실패 시
        })

        return strategies

    def _calculate_estimated_time(
        self,
        tasks: List[TaskNode],
        execution_order: List[List[str]]
    ) -> float:
        """
        예상 실행 시간 계산
        """

        total_time = 0.0

        for phase in execution_order:
            # 각 페이즈에서 가장 오래 걸리는 작업의 시간
            phase_time = 0.0
            for task_id in phase:
                task = next(t for t in tasks if t.id == task_id)
                phase_time = max(phase_time, task.estimated_time)

            total_time += phase_time

        # 오버헤드 추가 (10%)
        total_time *= 1.1

        return total_time

    async def optimize_plan(
        self,
        plan: ExecutionPlan,
        runtime_metrics: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        런타임 메트릭 기반 계획 최적화
        """

        # 실제 실행 시간 기반 조정
        if "actual_times" in runtime_metrics:
            for task in plan.tasks:
                if task.id in runtime_metrics["actual_times"]:
                    # 실제 시간으로 예상 시간 업데이트
                    actual = runtime_metrics["actual_times"][task.id]
                    task.estimated_time = actual * 0.7 + task.estimated_time * 0.3

        # 실패율 기반 재시도 전략 조정
        if "failure_rates" in runtime_metrics:
            for task in plan.tasks:
                if task.agent in runtime_metrics["failure_rates"]:
                    failure_rate = runtime_metrics["failure_rates"][task.agent]
                    if failure_rate > 0.3:
                        task.max_retries = min(task.max_retries + 1, 5)

        # 병렬 실행 그룹 재조정
        if "resource_usage" in runtime_metrics:
            avg_usage = runtime_metrics["resource_usage"].get("average", 0.5)
            if avg_usage < 0.5:
                # 리소스 여유가 있으면 병렬 실행 증가
                self.optimization_rules["max_parallel_tasks"] = min(
                    self.optimization_rules["max_parallel_tasks"] + 1,
                    5
                )

        return plan

    def validate_plan(self, plan: ExecutionPlan) -> Tuple[bool, List[str]]:
        """
        계획 유효성 검증
        """

        issues = []

        # 순환 의존성 체크
        task_map = {task.id: task for task in plan.tasks}
        visited = set()
        rec_stack = set()

        def has_cycle(task_id):
            visited.add(task_id)
            rec_stack.add(task_id)

            task = task_map.get(task_id)
            if task:
                for dep in task.dependencies:
                    if dep not in visited:
                        if has_cycle(dep):
                            return True
                    elif dep in rec_stack:
                        return True

            rec_stack.remove(task_id)
            return False

        for task in plan.tasks:
            if task.id not in visited:
                if has_cycle(task.id):
                    issues.append(f"Circular dependency detected involving {task.id}")

        # 리소스 할당 검증
        total_allocation = sum(plan.resource_allocation.values())
        if total_allocation > len(plan.resource_allocation):
            issues.append(f"Resource over-allocation: {total_allocation:.2f}")

        # 실행 순서 검증
        executed_tasks = set()
        for phase in plan.execution_order:
            for task_id in phase:
                task = task_map.get(task_id)
                if task:
                    # 의존성이 모두 실행되었는지 확인
                    for dep in task.dependencies:
                        if dep and dep not in executed_tasks:
                            issues.append(
                                f"Task {task_id} scheduled before dependency {dep}"
                            )
                executed_tasks.add(task_id)

        is_valid = len(issues) == 0
        return is_valid, issues


async def planning_node(state: MedicalSupervisorState) -> Dict[str, Any]:
    """
    Graph node for planning
    """

    planner = SmartPlanner()

    # 컨텍스트 추출
    context = MedicalContext(**state.get("optimized_context", {}))

    # 계획 생성
    plan = await planner.create_plan(state, context)

    # 계획 검증
    is_valid, issues = planner.validate_plan(plan)

    if not is_valid:
        logger.warning(f"Plan validation issues: {issues}")

    # 상태 업데이트
    return {
        "execution_plan": [
            {
                "task_id": task.id,
                "agent": task.agent,
                "estimated_time": task.estimated_time,
                "dependencies": task.dependencies
            }
            for task in plan.tasks
        ],
        "parallel_groups": plan.execution_order,
        "current_phase": "agent_selection"
    }