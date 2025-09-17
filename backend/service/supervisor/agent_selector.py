"""
Dynamic Agent Selector for Medical Supervisor
에이전트 동적 선택 및 워크로드 분산
"""

from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import logging
from collections import defaultdict
import numpy as np

from .state import MedicalSupervisorState, AgentSelectionState
from .context_manager import MedicalContext

logger = logging.getLogger(__name__)


@dataclass
class AgentProfile:
    """에이전트 프로필"""

    name: str
    capabilities: List[str]
    specialties: List[str]
    max_concurrent_tasks: int = 3
    average_response_time: float = 10.0
    success_rate: float = 0.95
    cost_per_call: float = 0.01
    current_load: int = 0
    last_used: Optional[datetime] = None
    total_calls: int = 0
    failed_calls: int = 0


@dataclass
class SelectionCriteria:
    """에이전트 선택 기준"""

    required_capabilities: List[str]
    preferred_capabilities: List[str]
    priority: str  # high, medium, low
    max_latency: float
    budget_constraint: Optional[float] = None
    load_balancing: bool = True


class DynamicAgentSelector:
    """
    동적 에이전트 선택기
    - 능력 기반 매칭
    - 워크로드 분산
    - 성능 기반 선택
    """

    def __init__(self):
        """Initialize Dynamic Agent Selector"""

        self.agent_profiles = self._initialize_agent_profiles()
        self.performance_history = defaultdict(list)
        self.selection_history = []
        self.cooldown_period = timedelta(seconds=5)

    def _initialize_agent_profiles(self) -> Dict[str, AgentProfile]:
        """에이전트 프로필 초기화"""

        return {
            "sql_analysis_agent": AgentProfile(
                name="sql_analysis_agent",
                capabilities=[
                    "sql_query",
                    "data_aggregation",
                    "trend_analysis",
                    "statistical_analysis",
                    "visualization"
                ],
                specialties=["실적분석", "트렌드분석", "데이터집계"],
                max_concurrent_tasks=5,
                average_response_time=12.0,
                success_rate=0.96,
                cost_per_call=0.02
            ),
            "information_retrieval_agent": AgentProfile(
                name="information_retrieval_agent",
                capabilities=[
                    "search",
                    "retrieval",
                    "filtering",
                    "web_search",
                    "api_integration",
                    "document_search"
                ],
                specialties=["정보검색", "웹검색", "문서검색"],
                max_concurrent_tasks=10,
                average_response_time=8.0,
                success_rate=0.94,
                cost_per_call=0.01
            ),
            "document_generation_agent": AgentProfile(
                name="document_generation_agent",
                capabilities=[
                    "document_generation",
                    "template_processing",
                    "formatting",
                    "data_storage",
                    "db_write",
                    "report_creation"
                ],
                specialties=["문서생성", "보고서작성", "양식작성"],
                max_concurrent_tasks=3,
                average_response_time=20.0,
                success_rate=0.92,
                cost_per_call=0.03
            ),
            "compliance_validation_agent": AgentProfile(
                name="compliance_validation_agent",
                capabilities=[
                    "compliance_check",
                    "regulation_validation",
                    "risk_assessment",
                    "policy_review"
                ],
                specialties=["규정검토", "위험평가", "정책검토"],
                max_concurrent_tasks=2,
                average_response_time=15.0,
                success_rate=0.98,
                cost_per_call=0.04
            )
        }

    async def select_agents(
        self,
        state: MedicalSupervisorState,
        context: MedicalContext
    ) -> AgentSelectionState:
        """
        에이전트 선택 메인 메서드
        """

        # 선택 기준 생성
        criteria = self._create_selection_criteria(state, context)

        # 사용 가능한 에이전트 확인
        available_agents = self._get_available_agents()

        # 능력 기반 필터링
        capable_agents = self._filter_by_capabilities(available_agents, criteria)

        # 점수 계산
        agent_scores = await self._score_agents(capable_agents, criteria, context)

        # 최적 에이전트 선택
        selected_agents = self._select_optimal_agents(
            agent_scores,
            criteria,
            context
        )

        # 워크로드 분산
        workload_distribution = self._distribute_workload(
            selected_agents,
            state.get("execution_plan", [])
        )

        # 선택 이유 생성
        selection_reasoning = self._generate_reasoning(
            selected_agents,
            criteria,
            agent_scores
        )

        # 에이전트 프로필 업데이트
        self._update_agent_profiles(selected_agents)

        selection_state = AgentSelectionState(
            available_agents=[a.name for a in available_agents],
            selected_agents=selected_agents,
            selection_criteria={
                "required": criteria.required_capabilities,
                "preferred": criteria.preferred_capabilities,
                "priority": criteria.priority
            },
            agent_capabilities={
                agent.name: agent.capabilities
                for agent in capable_agents
            },
            workload_distribution=workload_distribution,
            selection_reasoning=selection_reasoning
        )

        logger.info(
            f"Selected agents: {selected_agents} based on "
            f"{len(criteria.required_capabilities)} required capabilities"
        )

        return selection_state

    def _create_selection_criteria(
        self,
        state: MedicalSupervisorState,
        context: MedicalContext
    ) -> SelectionCriteria:
        """
        선택 기준 생성
        """

        # 의도 분석에서 필요한 능력 추출
        required_capabilities = []
        preferred_capabilities = []

        if state["intent_analysis"]:
            required_capabilities = state["intent_analysis"].get(
                "required_capabilities",
                []
            )

        # 도메인별 선호 능력
        domain_preferences = {
            "실적분석": ["trend_analysis", "statistical_analysis"],
            "정보검색": ["web_search", "document_search"],
            "문서생성": ["template_processing", "formatting"],
            "규정검토": ["risk_assessment", "policy_review"]
        }

        if context.domain_type in domain_preferences:
            preferred_capabilities = domain_preferences[context.domain_type]

        # 우선순위 결정
        priority = context.priority

        # 최대 지연시간
        max_latency = 30.0  # 기본값
        if priority == "high":
            max_latency = 15.0
        elif priority == "low":
            max_latency = 60.0

        return SelectionCriteria(
            required_capabilities=required_capabilities,
            preferred_capabilities=preferred_capabilities,
            priority=priority,
            max_latency=max_latency,
            budget_constraint=None,  # 필요시 설정
            load_balancing=True
        )

    def _get_available_agents(self) -> List[AgentProfile]:
        """
        사용 가능한 에이전트 확인
        """

        available = []
        current_time = datetime.now()

        for agent in self.agent_profiles.values():
            # 부하 확인
            if agent.current_load >= agent.max_concurrent_tasks:
                continue

            # 쿨다운 확인
            if agent.last_used:
                time_since_last_use = current_time - agent.last_used
                if time_since_last_use < self.cooldown_period:
                    continue

            available.append(agent)

        return available

    def _filter_by_capabilities(
        self,
        agents: List[AgentProfile],
        criteria: SelectionCriteria
    ) -> List[AgentProfile]:
        """
        능력 기반 필터링
        """

        capable_agents = []

        for agent in agents:
            # 필수 능력 확인
            has_required = all(
                cap in agent.capabilities
                for cap in criteria.required_capabilities
            )

            if has_required:
                capable_agents.append(agent)

        # 필수 능력을 가진 에이전트가 없으면 부분 매칭
        if not capable_agents and criteria.required_capabilities:
            # 가장 많은 필수 능력을 가진 에이전트 선택
            for agent in agents:
                match_count = sum(
                    1 for cap in criteria.required_capabilities
                    if cap in agent.capabilities
                )
                if match_count > 0:
                    capable_agents.append(agent)

        return capable_agents

    async def _score_agents(
        self,
        agents: List[AgentProfile],
        criteria: SelectionCriteria,
        context: MedicalContext
    ) -> Dict[str, float]:
        """
        에이전트 점수 계산
        """

        scores = {}

        for agent in agents:
            score = 0.0

            # 1. 능력 매칭 점수 (40%)
            capability_score = self._calculate_capability_score(agent, criteria)
            score += capability_score * 0.4

            # 2. 성능 점수 (30%)
            performance_score = self._calculate_performance_score(agent, criteria)
            score += performance_score * 0.3

            # 3. 워크로드 점수 (20%)
            workload_score = self._calculate_workload_score(agent)
            score += workload_score * 0.2

            # 4. 전문성 점수 (10%)
            specialty_score = self._calculate_specialty_score(agent, context)
            score += specialty_score * 0.1

            # 우선순위 가중치
            if criteria.priority == "high":
                score *= 1.2
            elif criteria.priority == "low":
                score *= 0.8

            scores[agent.name] = score

        return scores

    def _calculate_capability_score(
        self,
        agent: AgentProfile,
        criteria: SelectionCriteria
    ) -> float:
        """
        능력 매칭 점수 계산
        """

        score = 0.0

        # 필수 능력
        required_matches = sum(
            1 for cap in criteria.required_capabilities
            if cap in agent.capabilities
        )
        if criteria.required_capabilities:
            score += (required_matches / len(criteria.required_capabilities)) * 0.7

        # 선호 능력
        preferred_matches = sum(
            1 for cap in criteria.preferred_capabilities
            if cap in agent.capabilities
        )
        if criteria.preferred_capabilities:
            score += (preferred_matches / len(criteria.preferred_capabilities)) * 0.3

        return score

    def _calculate_performance_score(
        self,
        agent: AgentProfile,
        criteria: SelectionCriteria
    ) -> float:
        """
        성능 점수 계산
        """

        score = 0.0

        # 성공률 (50%)
        score += agent.success_rate * 0.5

        # 응답 시간 (30%)
        if agent.average_response_time <= criteria.max_latency:
            latency_score = 1.0 - (agent.average_response_time / criteria.max_latency)
            score += latency_score * 0.3
        else:
            score += 0.0

        # 비용 효율성 (20%)
        if criteria.budget_constraint:
            if agent.cost_per_call <= criteria.budget_constraint:
                cost_score = 1.0 - (agent.cost_per_call / criteria.budget_constraint)
                score += cost_score * 0.2
        else:
            # 비용 제약이 없으면 기본 점수
            score += 0.2

        return score

    def _calculate_workload_score(self, agent: AgentProfile) -> float:
        """
        워크로드 점수 계산
        """

        if agent.max_concurrent_tasks == 0:
            return 0.0

        # 현재 부하가 적을수록 높은 점수
        load_ratio = agent.current_load / agent.max_concurrent_tasks
        return 1.0 - load_ratio

    def _calculate_specialty_score(
        self,
        agent: AgentProfile,
        context: MedicalContext
    ) -> float:
        """
        전문성 점수 계산
        """

        # 도메인 타입과 전문 분야 매칭
        if context.domain_type in agent.specialties:
            return 1.0

        # 부분 매칭 확인
        partial_matches = {
            "실적분석": ["데이터집계", "트렌드분석"],
            "정보검색": ["웹검색", "문서검색"],
            "문서생성": ["보고서작성", "양식작성"],
            "규정검토": ["위험평가", "정책검토"]
        }

        if context.domain_type in partial_matches:
            for specialty in partial_matches[context.domain_type]:
                if specialty in agent.specialties:
                    return 0.5

        return 0.0

    def _select_optimal_agents(
        self,
        agent_scores: Dict[str, float],
        criteria: SelectionCriteria,
        context: MedicalContext
    ) -> List[str]:
        """
        최적 에이전트 선택
        """

        # 점수순 정렬
        sorted_agents = sorted(
            agent_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        selected = []

        # 도메인별 선택 전략
        if context.domain_type == "실적분석":
            # 데이터 분석 전문가 우선
            for agent_name, score in sorted_agents:
                if "sql_analysis" in agent_name:
                    selected.append(agent_name)
                    break

        elif context.domain_type == "정보검색":
            # 정보 검색 전문가 우선
            for agent_name, score in sorted_agents:
                if "information_retrieval" in agent_name:
                    selected.append(agent_name)
                    break

        elif context.domain_type == "문서생성":
            # 문서 생성 전문가 필수
            for agent_name, score in sorted_agents:
                if "document_generation" in agent_name:
                    selected.append(agent_name)
                    break

        # 규정 준수가 필요한 경우 compliance_validation_agent 추가
        if context.compliance_level == "strict":
            if "compliance_validation_agent" not in selected:
                selected.append("compliance_validation_agent")

        # 최소 1개 에이전트는 선택
        if not selected and sorted_agents:
            selected.append(sorted_agents[0][0])

        # 복잡도가 높은 경우 추가 에이전트 선택
        if context.domain_type in ["실적분석", "문서생성"]:
            complexity_score = getattr(context, "complexity_score", 0.5)
            if complexity_score > 0.7 and len(sorted_agents) > 1:
                # 두 번째로 높은 점수의 에이전트 추가
                for agent_name, score in sorted_agents[1:]:
                    if agent_name not in selected:
                        selected.append(agent_name)
                        break

        return selected

    def _distribute_workload(
        self,
        selected_agents: List[str],
        execution_plan: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        워크로드 분산
        """

        distribution = {}

        if not execution_plan:
            # 균등 분배
            equal_share = 1.0 / len(selected_agents) if selected_agents else 1.0
            for agent in selected_agents:
                distribution[agent] = equal_share
        else:
            # 작업 계획 기반 분배
            agent_tasks = defaultdict(list)
            for task in execution_plan:
                agent = task.get("agent")
                if agent in selected_agents:
                    agent_tasks[agent].append(task)

            total_time = sum(
                sum(task.get("estimated_time", 10) for task in tasks)
                for tasks in agent_tasks.values()
            ) or 1.0

            for agent in selected_agents:
                tasks = agent_tasks.get(agent, [])
                agent_time = sum(task.get("estimated_time", 10) for task in tasks)
                distribution[agent] = agent_time / total_time if total_time > 0 else 0.0

        return distribution

    def _generate_reasoning(
        self,
        selected_agents: List[str],
        criteria: SelectionCriteria,
        agent_scores: Dict[str, float]
    ) -> str:
        """
        선택 이유 생성
        """

        reasoning_parts = []

        # 선택된 에이전트와 점수
        for agent in selected_agents:
            score = agent_scores.get(agent, 0.0)
            profile = self.agent_profiles.get(agent)
            if profile:
                reasoning_parts.append(
                    f"{agent}: 점수 {score:.2f}, "
                    f"성공률 {profile.success_rate:.0%}, "
                    f"평균 응답시간 {profile.average_response_time:.1f}s"
                )

        # 필수 능력
        if criteria.required_capabilities:
            reasoning_parts.append(
                f"필수 능력: {', '.join(criteria.required_capabilities)}"
            )

        # 우선순위
        reasoning_parts.append(f"우선순위: {criteria.priority}")

        return " | ".join(reasoning_parts)

    def _update_agent_profiles(self, selected_agents: List[str]):
        """
        에이전트 프로필 업데이트
        """

        current_time = datetime.now()

        for agent_name in selected_agents:
            if agent_name in self.agent_profiles:
                agent = self.agent_profiles[agent_name]
                agent.current_load += 1
                agent.last_used = current_time
                agent.total_calls += 1

    async def update_performance_metrics(
        self,
        agent_name: str,
        execution_result: Dict[str, Any]
    ):
        """
        실행 결과 기반 성능 메트릭 업데이트
        """

        if agent_name not in self.agent_profiles:
            return

        agent = self.agent_profiles[agent_name]

        # 부하 감소
        agent.current_load = max(0, agent.current_load - 1)

        # 성공/실패 업데이트
        if execution_result.get("status") == "failed":
            agent.failed_calls += 1
            agent.success_rate = 1.0 - (agent.failed_calls / agent.total_calls)

        # 응답 시간 업데이트 (이동 평균)
        if "execution_time" in execution_result:
            new_time = execution_result["execution_time"]
            agent.average_response_time = (
                agent.average_response_time * 0.9 + new_time * 0.1
            )

        # 성능 히스토리 저장
        self.performance_history[agent_name].append({
            "timestamp": datetime.now(),
            "success": execution_result.get("status") != "failed",
            "execution_time": execution_result.get("execution_time", 0),
            "task_type": execution_result.get("task_type")
        })

        # 히스토리 크기 제한 (최근 100개)
        if len(self.performance_history[agent_name]) > 100:
            self.performance_history[agent_name] = \
                self.performance_history[agent_name][-100:]

    def get_agent_statistics(self) -> Dict[str, Any]:
        """
        에이전트 통계 반환
        """

        stats = {}

        for name, agent in self.agent_profiles.items():
            stats[name] = {
                "total_calls": agent.total_calls,
                "success_rate": agent.success_rate,
                "average_response_time": agent.average_response_time,
                "current_load": agent.current_load,
                "max_concurrent_tasks": agent.max_concurrent_tasks,
                "utilization": (
                    agent.current_load / agent.max_concurrent_tasks
                    if agent.max_concurrent_tasks > 0
                    else 0
                )
            }

        return stats


async def agent_selection_node(state: MedicalSupervisorState) -> Dict[str, Any]:
    """
    Graph node for agent selection
    """

    selector = DynamicAgentSelector()

    # 컨텍스트 추출
    context = MedicalContext(**state.get("optimized_context", {}))

    # 에이전트 선택
    selection_state = await selector.select_agents(state, context)

    # 상태 업데이트
    return {
        "selected_agents": selection_state["selected_agents"],
        "agent_states": {
            agent: {"status": "ready", "assigned_tasks": []}
            for agent in selection_state["selected_agents"]
        },
        "current_phase": "execution"
    }