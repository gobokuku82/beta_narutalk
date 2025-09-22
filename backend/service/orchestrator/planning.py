from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict
import json
import logging
from ..utils import LLMManager, PromptTemplates

logger = logging.getLogger(__name__)

class PlanningState(TypedDict):
    intents: List[Dict]
    execution_steps: List[Dict]
    agent_sequence: List[str]
    dependencies: Dict[str, List[str]]
    parallel_groups: List[List[str]]
    estimated_time: float

class PlanningSubGraph:
    def __init__(self):
        self.workflow = StateGraph(PlanningState)
        self.llm_manager = LLMManager()
        self.prompt_templates = PromptTemplates()
        self._build_graph()
    
    def _build_graph(self):
        self.workflow.add_node("analyze_dependencies", self.analyze_dependencies)
        self.workflow.add_node("optimize_sequence", self.optimize_execution_sequence)
        self.workflow.add_node("allocate_resources", self.allocate_resources)
        self.workflow.add_node("create_execution_plan", self.create_execution_plan)
        
        # 엔트리 포인트 정의 (LangGraph 0.6.7 방식)
        self.workflow.add_edge(START, "analyze_dependencies")
        self.workflow.add_edge("analyze_dependencies", "optimize_sequence")
        self.workflow.add_edge("optimize_sequence", "allocate_resources")
        self.workflow.add_edge("allocate_resources", "create_execution_plan")
        self.workflow.add_edge("create_execution_plan", END)
    
    async def optimize_execution_sequence(self, state: PlanningState):
        """병렬/순차 실행 최적화 - LLM 활용"""
        try:
            # 가용 에이전트 정보
            available_agents = {
                "sales_analytics": "매출/실적 데이터 분석",
                "internal_search": "내부 정보(인사, 규정) 검색",
                "doc_generation": "문서/보고서 생성",
                "compliance_check": "규정 준수 검토"
            }

            # LLM에게 최적 실행 계획 요청
            prompt = self.prompt_templates.get_prompt(
                category="planning",
                version="v1",
                intents=json.dumps(state.get('intents', []), ensure_ascii=False),
                available_agents=json.dumps(available_agents, ensure_ascii=False)
            )

            response = await self.llm_manager.generate(
                prompt=prompt,
                model="openai",
                category="planning",
                temperature=0.3
            )

            # 응답 파싱
            try:
                plan = json.loads(response['content'])
                state['parallel_groups'] = plan.get('parallel_groups', [])
                state['dependencies'] = plan.get('dependencies', {})
                state['estimated_time'] = plan.get('estimated_time', 10.0)

                logger.info(f"Execution plan optimized: {len(state['parallel_groups'])} parallel groups")

            except json.JSONDecodeError:
                # JSON 파싱 실패 시 폴백
                logger.warning("Failed to parse planning response, using fallback")
                state['parallel_groups'] = []
                for intent in state.get('intents', []):
                    state['parallel_groups'].append([intent.get('type', 'unknown')])

        except Exception as e:
            logger.error(f"Planning optimization failed: {e}")
            # 에러 시 기본 순차 실행
            state['parallel_groups'] = []

        return state

    async def analyze_dependencies(self, state: PlanningState) -> PlanningState:
        """의존성 분석 - LLM 기반"""
        try:
            intents = state.get('intents', [])

            if not intents:
                state["dependencies"] = {}
                return state

            # 의도 간 의존성 분석 프롬프트
            prompt = f"""다음 의도들 사이의 의존성을 분석하세요:
{json.dumps(intents, ensure_ascii=False, indent=2)}

어떤 작업이 다른 작업의 결과를 필요로 하는지 파악하고,
의존성 관계를 JSON 형식으로 반환하세요.

예시:
{{
    "sales_analysis": [],  // 의존성 없음
    "compliance_check": ["sales_analysis"],  // sales_analysis 결과 필요
    "doc_generation": ["sales_analysis", "compliance_check"]  // 두 결과 모두 필요
}}

의존성 분석:"""

            response = await self.llm_manager.generate(
                prompt=prompt,
                model="openai_mini",
                category="dependency_analysis",
                temperature=0.2
            )

            try:
                dependencies = json.loads(response['content'])
                state["dependencies"] = dependencies
                logger.info(f"Dependencies analyzed: {dependencies}")
            except:
                state["dependencies"] = {}

        except Exception as e:
            logger.error(f"Dependency analysis failed: {e}")
            state["dependencies"] = {}

        return state

    async def allocate_resources(self, state: PlanningState) -> PlanningState:
        """리소스 할당 - 예상 시간 계산"""
        # 각 에이전트별 예상 실행 시간 (초)
        agent_times = {
            "sales_analytics": 3.0,
            "internal_search": 2.0,
            "doc_generation": 4.0,
            "compliance_check": 3.5
        }

        total_time = 0.0
        parallel_groups = state.get('parallel_groups', [])

        for group in parallel_groups:
            # 병렬 그룹은 가장 오래 걸리는 작업 시간
            if isinstance(group, list):
                group_time = max([agent_times.get(agent, 2.0) for agent in group], default=2.0)
            else:
                group_time = agent_times.get(group, 2.0)
            total_time += group_time

        state["estimated_time"] = total_time
        logger.info(f"Estimated execution time: {total_time} seconds")

        return state

    async def create_execution_plan(self, state: PlanningState) -> PlanningState:
        """실행 계획 생성 - 구체적 단계 수립"""
        try:
            intents = state.get('intents', [])
            parallel_groups = state.get('parallel_groups', [])
            dependencies = state.get('dependencies', {})

            # 실행 단계 생성
            execution_steps = []
            agent_sequence = []

            for i, group in enumerate(parallel_groups):
                if isinstance(group, list):
                    step = {
                        "step": i + 1,
                        "type": "parallel",
                        "agents": group,
                        "description": f"병렬 실행: {', '.join(group)}"
                    }
                    agent_sequence.extend(group)
                else:
                    step = {
                        "step": i + 1,
                        "type": "sequential",
                        "agents": [group],
                        "description": f"순차 실행: {group}"
                    }
                    agent_sequence.append(group)

                execution_steps.append(step)

            state["execution_steps"] = execution_steps
            state["agent_sequence"] = agent_sequence

            logger.info(f"Execution plan created with {len(execution_steps)} steps")

        except Exception as e:
            logger.error(f"Execution plan creation failed: {e}")
            state["execution_steps"] = []
            state["agent_sequence"] = []

        return state