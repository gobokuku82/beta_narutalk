"""
Planner - Step 2 of Supervisor Workflow
실행 계획 수립 및 의존성 관리
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
import logging

from ..state import PlanningState, GlobalSessionState, QueryAnalyzerState

logger = logging.getLogger(__name__)


class Planner:
    """실행 계획을 수립하고 의존성을 관리하는 에이전트"""

    def __init__(self, llm_provider: str = "openai"):
        """Initialize with LLM provider"""
        if llm_provider == "openai":
            self.llm = ChatOpenAI(model="gpt-4o", temperature=0)  # Using GPT-4o
        elif llm_provider == "anthropic":
            self.llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0)
        else:
            self.llm = ChatOpenAI(model="gpt-4o", temperature=0)  # Default to GPT-4o

    async def create_plan(self, analyzer_state: QueryAnalyzerState) -> PlanningState:
        """실행 계획 수립 메인 메서드"""

        # 의존성 그래프 구축
        dependency_graph = self._build_dependency_graph(analyzer_state["suggested_agents"])

        # 실행 순서 결정 (토폴로지 정렬)
        execution_order = self._topological_sort(dependency_graph)

        # 병렬 실행 기회 식별
        parallel_groups = self._identify_parallel_opportunities(execution_order, dependency_graph)

        # 리소스 요구사항 계산
        resource_requirements = self._calculate_resource_requirements(
            analyzer_state["suggested_agents"],
            analyzer_state["complexity_score"]
        )

        # 실행 계획 생성
        execution_plan = self._create_execution_plan(
            parallel_groups,
            resource_requirements,
            analyzer_state
        )

        # Fallback 계획 수립
        fallback_plans = self._create_fallback_plans(execution_plan, analyzer_state)

        # Contingency triggers 정의
        contingency_triggers = self._define_contingency_triggers(analyzer_state)

        # Create state as dictionary (not TypedDict instance)
        planning_result = {
            "analyzed_query": dict(analyzer_state),
            "execution_plan": execution_plan,
            "task_dependencies": dependency_graph,
            "dependency_graph": {"nodes": list(dependency_graph.keys()), "edges": dependency_graph},
            "resource_requirements": resource_requirements,
            "estimated_steps": len(execution_plan),
            "priority_order": execution_order,
            "parallel_opportunities": parallel_groups,
            "fallback_plans": fallback_plans,
            "contingency_triggers": contingency_triggers
        }

        logger.info(f"Plan created with {len(execution_plan)} steps, {len(parallel_groups)} parallel groups")

        return planning_result

    def _build_dependency_graph(self, agents: List[str]) -> Dict[str, List[str]]:
        """에이전트 간 의존성 그래프 구축"""

        # 기본 의존성 규칙
        base_dependencies = {
            "DataAnalysisAgent": [],  # 독립적
            "InformationRetrievalAgent": [],  # 독립적
            "DocumentGenerationAgent": [
                "DataAnalysisAgent",
                "InformationRetrievalAgent"
            ],  # 데이터와 정보가 필요
            "ComplianceValidationAgent": [
                "DocumentGenerationAgent"
            ],  # 문서 생성 후 검증
            "StorageDecisionAgent": [
                "DataAnalysisAgent",
                "DocumentGenerationAgent"
            ]  # 데이터와 문서 저장
        }

        # 실제 필요한 에이전트만 필터링
        graph = {}
        for agent in agents:
            deps = base_dependencies.get(agent, [])
            # 실제 존재하는 의존성만 포함
            graph[agent] = [d for d in deps if d in agents]

        return graph

    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """토폴로지 정렬로 실행 순서 결정"""

        # 진입 차수 계산
        in_degree = {node: 0 for node in graph}
        for node in graph:
            for neighbor in graph[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] += 1

        # 진입 차수가 0인 노드로 시작
        queue = [node for node in in_degree if in_degree[node] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            # 인접 노드의 진입 차수 감소
            for neighbor in graph.get(node, []):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return result

    def _identify_parallel_opportunities(
        self,
        execution_order: List[str],
        dependency_graph: Dict[str, List[str]]
    ) -> List[List[str]]:
        """병렬 실행 가능한 그룹 식별"""

        parallel_groups = []
        processed = set()

        for agent in execution_order:
            if agent in processed:
                continue

            # 같은 레벨의 독립적인 에이전트 찾기
            group = [agent]
            processed.add(agent)

            for other in execution_order:
                if other in processed:
                    continue

                # 서로 의존성이 없으면 병렬 실행 가능
                if (other not in dependency_graph.get(agent, []) and
                    agent not in dependency_graph.get(other, [])):

                    # 같은 의존성을 가지면 그룹화
                    if dependency_graph.get(agent, []) == dependency_graph.get(other, []):
                        group.append(other)
                        processed.add(other)

            parallel_groups.append(group)

        return parallel_groups

    def _calculate_resource_requirements(
        self,
        agents: List[str],
        complexity: float
    ) -> Dict[str, Any]:
        """리소스 요구사항 계산"""

        base_resources = {
            "DataAnalysisAgent": {"cpu": 2, "memory": 2, "api_calls": 5},
            "InformationRetrievalAgent": {"cpu": 1, "memory": 1, "api_calls": 10},
            "DocumentGenerationAgent": {"cpu": 1, "memory": 1, "api_calls": 3},
            "ComplianceValidationAgent": {"cpu": 1, "memory": 0.5, "api_calls": 2},
            "StorageDecisionAgent": {"cpu": 0.5, "memory": 0.5, "api_calls": 1}
        }

        total_resources = {
            "cpu_cores": 0,
            "memory_gb": 0,
            "api_calls": {},
            "db_connections": len(agents),
            "estimated_cost": 0
        }

        # 각 에이전트의 리소스 합산
        for agent in agents:
            if agent in base_resources:
                resources = base_resources[agent]
                total_resources["cpu_cores"] += resources["cpu"] * (1 + complexity)
                total_resources["memory_gb"] += resources["memory"] * (1 + complexity)
                total_resources["api_calls"][agent] = resources["api_calls"]

        # 비용 추정
        total_resources["estimated_cost"] = (
            total_resources["cpu_cores"] * 0.1 +
            total_resources["memory_gb"] * 0.05 +
            sum(total_resources["api_calls"].values()) * 0.01
        )

        return total_resources

    def _create_execution_plan(
        self,
        parallel_groups: List[List[str]],
        resource_requirements: Dict,
        analyzer_state: QueryAnalyzerState
    ) -> List[Dict[str, Any]]:
        """상세 실행 계획 생성"""

        execution_plan = []

        for idx, group in enumerate(parallel_groups):
            step = {
                "step_id": f"step_{idx + 1}",
                "agents": group,
                "parallel": len(group) > 1,
                "timeout": self._calculate_timeout(group, analyzer_state["complexity_score"]),
                "retry_count": 3,
                "checkpoint": True,  # 체크포인트 저장
                "dependencies": self._get_step_dependencies(idx, parallel_groups),
                "resources": {
                    "cpu": sum(resource_requirements.get("cpu_cores", 0) for _ in group) / len(parallel_groups),
                    "memory": sum(resource_requirements.get("memory_gb", 0) for _ in group) / len(parallel_groups)
                },
                "interrupt_before": self._needs_approval(group),
                "description": self._generate_step_description(group)
            }
            execution_plan.append(step)

        return execution_plan

    def _calculate_timeout(self, agents: List[str], complexity: float) -> int:
        """타임아웃 계산 (초)"""

        base_timeouts = {
            "DataAnalysisAgent": 30,
            "InformationRetrievalAgent": 20,
            "DocumentGenerationAgent": 25,
            "ComplianceValidationAgent": 15,
            "StorageDecisionAgent": 10
        }

        max_timeout = max(
            base_timeouts.get(agent, 20) for agent in agents
        )

        # 복잡도에 따라 조정
        adjusted_timeout = int(max_timeout * (1 + complexity))

        return min(adjusted_timeout, 120)  # 최대 2분

    def _get_step_dependencies(self, idx: int, parallel_groups: List[List[str]]) -> List[str]:
        """단계별 의존성 추출"""

        if idx == 0:
            return []

        # 이전 단계들을 의존성으로
        return [f"step_{i + 1}" for i in range(idx)]

    def _needs_approval(self, agents: List[str]) -> bool:
        """승인이 필요한 단계인지 확인"""

        # 중요한 작업은 승인 필요
        critical_agents = ["DocumentGenerationAgent", "StorageDecisionAgent"]

        return any(agent in critical_agents for agent in agents)

    def _generate_step_description(self, agents: List[str]) -> str:
        """단계 설명 생성"""

        descriptions = {
            "DataAnalysisAgent": "데이터 분석 및 통계 처리",
            "InformationRetrievalAgent": "정보 검색 및 수집",
            "DocumentGenerationAgent": "문서 생성 및 포맷팅",
            "ComplianceValidationAgent": "규정 준수 검증",
            "StorageDecisionAgent": "저장 전략 결정 및 실행"
        }

        agent_descriptions = [descriptions.get(agent, agent) for agent in agents]

        if len(agent_descriptions) == 1:
            return agent_descriptions[0]
        else:
            return " 및 ".join(agent_descriptions)

    def _create_fallback_plans(
        self,
        execution_plan: List[Dict],
        analyzer_state: QueryAnalyzerState
    ) -> List[Dict[str, Any]]:
        """대체 계획 수립"""

        fallback_plans = []

        for step in execution_plan:
            # 각 단계별 대체 계획
            fallback = {
                "step_id": step["step_id"],
                "trigger": "failure",
                "alternative_agents": self._get_alternative_agents(step["agents"]),
                "simplified_approach": self._get_simplified_approach(step["agents"]),
                "skip_conditions": self._get_skip_conditions(step["agents"])
            }
            fallback_plans.append(fallback)

        return fallback_plans

    def _get_alternative_agents(self, agents: List[str]) -> List[str]:
        """대체 에이전트 목록"""

        alternatives = {
            "DataAnalysisAgent": ["InformationRetrievalAgent"],
            "InformationRetrievalAgent": ["DataAnalysisAgent"],
            "DocumentGenerationAgent": [],  # 대체 불가
            "ComplianceValidationAgent": [],  # 대체 불가
            "StorageDecisionAgent": []  # 대체 불가
        }

        alt_agents = []
        for agent in agents:
            alt_agents.extend(alternatives.get(agent, []))

        return list(set(alt_agents))

    def _get_simplified_approach(self, agents: List[str]) -> Dict[str, Any]:
        """단순화된 접근 방법"""

        simplifications = {
            "DataAnalysisAgent": {"reduce_scope": True, "use_cache": True},
            "InformationRetrievalAgent": {"limit_sources": 1, "top_k": 5},
            "DocumentGenerationAgent": {"use_template": True, "minimal_format": True},
            "ComplianceValidationAgent": {"basic_check": True},
            "StorageDecisionAgent": {"default_storage": "structured_db"}
        }

        approach = {}
        for agent in agents:
            if agent in simplifications:
                approach[agent] = simplifications[agent]

        return approach

    def _get_skip_conditions(self, agents: List[str]) -> Dict[str, Any]:
        """건너뛸 조건"""

        skip_conditions = {
            "DataAnalysisAgent": {"no_data_available": True},
            "InformationRetrievalAgent": {"no_search_needed": True},
            "DocumentGenerationAgent": {"template_only": True},
            "ComplianceValidationAgent": {"low_risk": True},
            "StorageDecisionAgent": {"temporary_data": True}
        }

        conditions = {}
        for agent in agents:
            if agent in skip_conditions:
                conditions[agent] = skip_conditions[agent]

        return conditions

    def _define_contingency_triggers(self, analyzer_state: QueryAnalyzerState) -> Dict[str, Any]:
        """비상 계획 트리거 정의"""

        triggers = {
            "timeout": {
                "threshold": 120,  # 2분
                "action": "simplify_plan"
            },
            "error_rate": {
                "threshold": 0.5,  # 50% 에러율
                "action": "activate_fallback"
            },
            "resource_exhaustion": {
                "threshold": 0.9,  # 90% 리소스 사용
                "action": "reduce_parallel"
            },
            "user_cancellation": {
                "action": "graceful_shutdown"
            }
        }

        # 복잡도에 따라 조정
        if analyzer_state["complexity_score"] > 0.7:
            triggers["timeout"]["threshold"] = 180  # 3분으로 증가

        return triggers


async def planner_node(state: GlobalSessionState) -> Dict[str, Any]:
    """Planner node for graph"""

    planner = Planner()

    # Get analyzer state
    analyzer_state = state.get("query_analyzer_state")
    if not analyzer_state:
        logger.error("No analyzer state found")
        return state

    # Create plan
    planning_state = await planner.create_plan(analyzer_state)

    # Return only changes (not entire state)
    return {
        "planning_state": planning_state,
        "current_phase": "agent_selection",
        "audit_trail": [{
            "timestamp": datetime.now().isoformat(),
            "agent": "planner",
            "action": "planned",
            "steps": len(planning_state["execution_plan"]),
            "parallel_groups": len(planning_state["parallel_opportunities"])
        }]  # Reducer will append this
    }

    logger.info(f"Planning completed for session {state['session_id']}")