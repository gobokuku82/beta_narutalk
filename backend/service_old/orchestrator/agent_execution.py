from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AgentExecutionState(TypedDict):
    execution_plan: Dict[str, Any]
    active_agents: List[str]
    agent_inputs: Dict[str, Any]
    agent_results: Dict[str, Any]
    parallel_groups: List[List[str]]
    execution_status: str
    error_logs: List[str]
    retry_count: int
    start_time: float
    end_time: Optional[float]

class AgentExecutionSubGraph:
    def __init__(self):
        self.workflow = StateGraph(AgentExecutionState)
        self.max_retries = 3
        self._build_graph()

    def _build_graph(self):
        # 노드 추가
        self.workflow.add_node("prepare_execution", self.prepare_agent_execution)
        self.workflow.add_node("execute_parallel", self.execute_parallel_agents)
        self.workflow.add_node("execute_sequential", self.execute_sequential_agents)
        self.workflow.add_node("merge_results", self.merge_agent_results)
        self.workflow.add_node("validate_results", self.validate_execution_results)
        self.workflow.add_node("handle_failures", self.handle_execution_failures)

        # 엔트리 포인트 설정 (LangGraph 0.6.7 방식)
        self.workflow.add_edge(START, "prepare_execution")

        # 실행 전략에 따른 분기
        self.workflow.add_conditional_edges(
            "prepare_execution",
            self.determine_execution_strategy,
            {
                "parallel": "execute_parallel",
                "sequential": "execute_sequential",
                "mixed": "execute_parallel"
            }
        )

        # 병렬/순차 실행 후 결과 병합
        self.workflow.add_edge("execute_parallel", "merge_results")
        self.workflow.add_edge("execute_sequential", "merge_results")

        # 결과 검증
        self.workflow.add_edge("merge_results", "validate_results")

        # 검증 결과에 따른 분기
        self.workflow.add_conditional_edges(
            "validate_results",
            self.check_validation_status,
            {
                "success": END,
                "partial_success": END,
                "retry_needed": "handle_failures",
                "failure": "handle_failures"
            }
        )

        # 실패 처리 후 재시도 또는 종료
        self.workflow.add_conditional_edges(
            "handle_failures",
            self.decide_retry,
            {
                "retry": "prepare_execution",
                "abort": END
            }
        )

    async def prepare_agent_execution(self, state: AgentExecutionState) -> AgentExecutionState:
        """에이전트 실행 준비"""
        state["start_time"] = datetime.now().timestamp()
        state["execution_status"] = "preparing"

        # 실행 계획에서 에이전트 정보 추출
        execution_plan = state.get("execution_plan", {})
        active_agents = execution_plan.get("agents", [])

        # 에이전트별 입력 데이터 준비
        agent_inputs = {}
        for agent in active_agents:
            agent_inputs[agent] = {
                "query": execution_plan.get("query"),
                "context": execution_plan.get("context", {}),
                "parameters": execution_plan.get("agent_params", {}).get(agent, {})
            }

        state["active_agents"] = active_agents
        state["agent_inputs"] = agent_inputs
        state["agent_results"] = {}

        logger.info(f"Prepared execution for agents: {active_agents}")
        return state

    def determine_execution_strategy(self, state: AgentExecutionState) -> str:
        """실행 전략 결정 (병렬/순차/혼합)"""
        parallel_groups = state.get("parallel_groups", [])

        if parallel_groups and len(parallel_groups) > 0:
            if len(parallel_groups) == 1:
                return "parallel"
            else:
                return "mixed"
        return "sequential"

    async def execute_parallel_agents(self, state: AgentExecutionState) -> AgentExecutionState:
        """병렬 에이전트 실행"""
        state["execution_status"] = "executing_parallel"
        parallel_groups = state.get("parallel_groups", [[]])

        for group in parallel_groups:
            if not group:
                continue

            # 그룹 내 에이전트 병렬 실행
            tasks = []
            for agent_name in group:
                if agent_name in state["active_agents"]:
                    task = self._execute_single_agent(
                        agent_name,
                        state["agent_inputs"].get(agent_name, {})
                    )
                    tasks.append((agent_name, task))

            # 병렬 실행 및 결과 수집
            if tasks:
                results = await asyncio.gather(
                    *[task for _, task in tasks],
                    return_exceptions=True
                )

                for (agent_name, _), result in zip(tasks, results):
                    if isinstance(result, Exception):
                        state["error_logs"].append(f"{agent_name}: {str(result)}")
                        state["agent_results"][agent_name] = {
                            "status": "error",
                            "error": str(result)
                        }
                    else:
                        state["agent_results"][agent_name] = result

        return state

    async def execute_sequential_agents(self, state: AgentExecutionState) -> AgentExecutionState:
        """순차 에이전트 실행"""
        state["execution_status"] = "executing_sequential"

        for agent_name in state["active_agents"]:
            try:
                # 이전 에이전트 결과를 컨텍스트에 추가
                input_data = state["agent_inputs"].get(agent_name, {})
                input_data["previous_results"] = state["agent_results"]

                result = await self._execute_single_agent(agent_name, input_data)
                state["agent_results"][agent_name] = result

            except Exception as e:
                logger.error(f"Error executing agent {agent_name}: {e}")
                state["error_logs"].append(f"{agent_name}: {str(e)}")
                state["agent_results"][agent_name] = {
                    "status": "error",
                    "error": str(e)
                }

        return state

    async def _execute_single_agent(self, agent_name: str, input_data: Dict) -> Dict:
        """단일 에이전트 실행"""
        logger.info(f"Executing agent: {agent_name}")

        # 동적 에이전트 임포트 및 실행
        try:
            # 에이전트 이름 매핑 (의도 타입 -> 에이전트)
            agent_mapping = {
                "sales_analytics": "sales_analytics",
                "sales_analysis": "sales_analytics",  # 별칭 지원
                "internal_search": "internal_search",
                "search": "internal_search",  # 별칭 지원
                "general_query": "internal_search",  # general_query를 internal_search로 매핑
                "doc_generation": "doc_generation",
                "document_generation": "doc_generation",  # 별칭 지원
                "compliance_check": "compliance_check",
                "compliance": "compliance_check"  # 별칭 지원
            }

            # 매핑된 에이전트 이름 가져오기
            mapped_agent_name = agent_mapping.get(agent_name, agent_name)

            if mapped_agent_name == "sales_analytics":
                from ..agents.sales_analytics_agent import SalesAnalyticsAgent
                agent = SalesAnalyticsAgent()
            elif mapped_agent_name == "internal_search":
                from ..agents.search_agent import SearchAgent
                agent = SearchAgent()
            elif mapped_agent_name == "doc_generation":
                from ..agents.document_generation_agent import DocumentGenerationAgent
                agent = DocumentGenerationAgent()
            elif mapped_agent_name == "compliance_check":
                from ..agents.compliance_check_agent import ComplianceCheckAgent
                agent = ComplianceCheckAgent()
            else:
                # 알 수 없는 에이전트는 기본적으로 internal_search 사용
                logger.warning(f"Unknown agent: {agent_name}, falling back to internal_search")
                from ..agents.search_agent import SearchAgent
                agent = SearchAgent()

            # 에이전트 실행
            result = await agent.execute(input_data)

            return {
                "status": "success",
                "data": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Agent {agent_name} execution failed: {e}")
            raise

    async def merge_agent_results(self, state: AgentExecutionState) -> AgentExecutionState:
        """에이전트 실행 결과 병합"""
        state["execution_status"] = "merging_results"

        # 결과 통합 로직
        merged_data = {}
        for agent_name, result in state["agent_results"].items():
            if result.get("status") == "success":
                merged_data[agent_name] = result.get("data", {})

        state["agent_results"]["merged"] = merged_data
        return state

    async def validate_execution_results(self, state: AgentExecutionState) -> AgentExecutionState:
        """실행 결과 검증"""
        state["execution_status"] = "validating"

        total_agents = len(state["active_agents"])
        successful_agents = sum(
            1 for result in state["agent_results"].values()
            if result.get("status") == "success"
        )

        if successful_agents == total_agents:
            state["execution_status"] = "success"
        elif successful_agents > 0:
            state["execution_status"] = "partial_success"
        else:
            state["execution_status"] = "failure"

        state["end_time"] = datetime.now().timestamp()

        logger.info(f"Validation complete: {successful_agents}/{total_agents} agents succeeded")
        return state

    def check_validation_status(self, state: AgentExecutionState) -> str:
        """검증 상태 확인"""
        status = state.get("execution_status", "failure")

        if status == "success":
            return "success"
        elif status == "partial_success":
            return "partial_success"
        elif state.get("retry_count", 0) < self.max_retries:
            return "retry_needed"
        else:
            return "failure"

    async def handle_execution_failures(self, state: AgentExecutionState) -> AgentExecutionState:
        """실행 실패 처리"""
        state["execution_status"] = "handling_failure"

        # 실패한 에이전트 식별
        failed_agents = [
            agent for agent, result in state["agent_results"].items()
            if result.get("status") == "error"
        ]

        logger.warning(f"Handling failures for agents: {failed_agents}")

        # 재시도를 위한 에이전트 목록 업데이트
        if failed_agents:
            state["active_agents"] = failed_agents
            state["retry_count"] = state.get("retry_count", 0) + 1

        return state

    def decide_retry(self, state: AgentExecutionState) -> str:
        """재시도 여부 결정"""
        if state.get("retry_count", 0) < self.max_retries:
            logger.info(f"Retrying execution (attempt {state['retry_count']}/{self.max_retries})")
            return "retry"
        else:
            logger.error("Max retries exceeded, aborting execution")
            return "abort"