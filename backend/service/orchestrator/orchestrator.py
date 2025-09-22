from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum
import logging

# 서브그래프 임포트
from .intent_analysis import IntentAnalysisSubGraph
from .planning import PlanningSubGraph
from .agent_execution import AgentExecutionSubGraph
from .result_evaluation import ResultEvaluationSubGraph
from .response_generation import ResponseGenerationSubGraph

logger = logging.getLogger(__name__)

# 상태 정의
class MainState(TypedDict):
    # 기본 정보
    user_id: str
    session_id: str
    user_query: str
    timestamp: str
    
    # 의도 및 계획
    intents: List[Dict[str, Any]]
    execution_plan: Dict[str, Any]
    priority_level: str  # high, medium, low
    
    # 실행 관련
    active_agents: List[str]
    agent_results: Dict[str, Any]
    parallel_execution: bool
    
    # 결과 및 검증
    raw_results: Dict[str, Any]
    validated_results: Dict[str, Any]
    compliance_status: Dict[str, Any]
    
    # 응답
    final_response: str
    response_format: str  # text, table, chart, document
    confidence_score: float
    
    # 메타데이터
    error_logs: List[str]
    execution_time: float
    tokens_used: int
    need_human_review: bool
    conversation_history: List[Dict]

# Main Graph 구성
class MainOrchestrator:
    def __init__(self):
        self.workflow = StateGraph(MainState)
        # Checkpointer는 선택사항으로 변경 (테스트 시 문제 발생)
        self.checkpointer = None  # AsyncSqliteSaver는 별도 초기화 필요

        # 서브그래프 초기화
        self.intent_analyzer = IntentAnalysisSubGraph()
        self.planner = PlanningSubGraph()
        self.agent_executor = AgentExecutionSubGraph()
        self.evaluator = ResultEvaluationSubGraph()
        self.response_generator = ResponseGenerationSubGraph()

        self._build_graph()
    
    def _build_graph(self):
        # 노드 추가
        self.workflow.add_node("authenticate", self.authenticate_user)
        self.workflow.add_node("analyze_intent", self.analyze_intent_subgraph)
        self.workflow.add_node("create_plan", self.planning_subgraph)
        self.workflow.add_node("execute_agents", self.agent_execution_subgraph)
        self.workflow.add_node("evaluate_results", self.evaluation_subgraph)
        self.workflow.add_node("generate_response", self.response_generation_subgraph)
        self.workflow.add_node("store_memory", self.store_conversation)
        
        # 엔트리 포인트 정의 (LangGraph 0.6.7 방식)
        self.workflow.add_edge(START, "authenticate")

        self.workflow.add_edge("authenticate", "analyze_intent")
        self.workflow.add_edge("analyze_intent", "create_plan")
        
        # 조건부 엣지 - 계획 검증
        self.workflow.add_conditional_edges(
            "create_plan",
            self.check_plan_validity,
            {
                "valid": "execute_agents",
                "need_clarification": "generate_response",
                "invalid": END
            }
        )
        
        # 조건부 엣지 - 실행 결과 확인
        self.workflow.add_conditional_edges(
            "execute_agents",
            self.check_execution_status,
            {
                "success": "evaluate_results",
                "partial_success": "evaluate_results",
                "retry": "execute_agents",
                "failure": "generate_response"
            }
        )
        
        # 조건부 엣지 - 평가 결과
        self.workflow.add_conditional_edges(
            "evaluate_results",
            self.check_evaluation,
            {
                "approved": "generate_response",
                "need_revision": "execute_agents",
                "compliance_issue": "generate_response"
            }
        )
        
        self.workflow.add_edge("generate_response", "store_memory")
        self.workflow.add_edge("store_memory", END)

    # 노드 메서드들 (임시 구현)
    async def authenticate_user(self, state: MainState) -> MainState:
        """사용자 인증"""
        # 필수 필드 초기화
        if "error_logs" not in state:
            state["error_logs"] = []
        if "conversation_history" not in state:
            state["conversation_history"] = []
        if "tokens_used" not in state:
            state["tokens_used"] = 0
        if "execution_time" not in state:
            state["execution_time"] = 0.0
        if "priority_level" not in state:
            state["priority_level"] = "medium"

        # TODO: 실제 인증 로직 구현
        logger.info(f"User authenticated: {state.get('user_id', 'unknown')}")
        return state

    async def analyze_intent_subgraph(self, state: MainState) -> MainState:
        """의도 분석 서브그래프"""
        try:
            # 서브그래프 상태 준비
            intent_state = {
                "user_query": state.get("user_query", ""),
                "tokens": [],
                "entities": [],
                "intents": [],
                "confidence_scores": {},
                "ambiguous": False
            }

            # 서브그래프 실행
            app = self.intent_analyzer.workflow.compile()
            result = await app.ainvoke(intent_state)

            # 결과를 메인 상태에 병합
            state["intents"] = result.get("intents", [])
            state["confidence_score"] = max(result.get("confidence_scores", {}).values(), default=0.0)

            logger.info(f"Intent analysis complete: {[i.get('type') for i in state['intents']]}")

        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            state["intents"] = []
            state["error_logs"] = state.get("error_logs", [])
            state["error_logs"].append(f"Intent analysis: {str(e)}")

        return state

    async def planning_subgraph(self, state: MainState) -> MainState:
        """계획 수립 서브그래프"""
        try:
            # 서브그래프 상태 준비
            planning_state = {
                "intents": state.get("intents", []),
                "execution_steps": [],
                "agent_sequence": [],
                "dependencies": {},
                "parallel_groups": [],
                "estimated_time": 0.0
            }

            # 서브그래프 실행
            app = self.planner.workflow.compile()
            result = await app.ainvoke(planning_state)

            # 결과를 메인 상태에 병합
            state["execution_plan"] = {
                "steps": result.get("execution_steps", []),
                "agents": result.get("agent_sequence", []),
                "parallel_groups": result.get("parallel_groups", [])
            }
            state["parallel_execution"] = len(result.get("parallel_groups", [])) > 0

            logger.info(f"Planning complete: {len(state['execution_plan'].get('steps', []))} steps")

        except Exception as e:
            logger.error(f"Planning failed: {e}")
            state["execution_plan"] = {}
            state["error_logs"] = state.get("error_logs", [])
            state["error_logs"].append(f"Planning: {str(e)}")

        return state

    async def agent_execution_subgraph(self, state: MainState) -> MainState:
        """에이전트 실행 서브그래프"""
        try:
            # 서브그래프 상태 준비
            execution_state = {
                "execution_plan": state.get("execution_plan", {}),
                "active_agents": [],
                "agent_inputs": {},
                "agent_results": {},
                "parallel_groups": state.get("execution_plan", {}).get("parallel_groups", []),
                "execution_status": "",
                "error_logs": [],
                "retry_count": 0,
                "start_time": 0,
                "end_time": None
            }

            # 서브그래프 실행
            app = self.agent_executor.workflow.compile()
            result = await app.ainvoke(execution_state)

            # 결과를 메인 상태에 병합
            state["agent_results"] = result.get("agent_results", {})
            state["active_agents"] = result.get("active_agents", [])
            state["raw_results"] = result.get("agent_results", {})

            logger.info(f"Agent execution complete: {len(state['agent_results'])} results")

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            state["agent_results"] = {}
            state["error_logs"] = state.get("error_logs", [])
            state["error_logs"].append(f"Agent execution: {str(e)}")

        return state

    async def evaluation_subgraph(self, state: MainState) -> MainState:
        """평가 서브그래프"""
        try:
            # 서브그래프 상태 준비
            eval_state = {
                "raw_results": state.get("raw_results", {}),
                "validation_rules": [],
                "quality_scores": {},
                "compliance_checks": {},
                "validated_results": {},
                "issues_found": [],
                "recommendations": []
            }

            # 서브그래프 실행
            app = self.evaluator.workflow.compile()
            result = await app.ainvoke(eval_state)

            # 결과를 메인 상태에 병합
            state["validated_results"] = result.get("validated_results", {})
            state["compliance_status"] = result.get("compliance_checks", {})
            state["need_human_review"] = len(result.get("issues_found", [])) > 0

            logger.info(f"Evaluation complete: {len(result.get('issues_found', []))} issues found")

        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            state["validated_results"] = state.get("raw_results", {})
            state["error_logs"] = state.get("error_logs", [])
            state["error_logs"].append(f"Evaluation: {str(e)}")

        return state

    async def response_generation_subgraph(self, state: MainState) -> MainState:
        """응답 생성 서브그래프"""
        try:
            # 서브그래프 상태 준비
            response_state = {
                "response_format": state.get("response_format", "text"),
                "raw_data": state.get("validated_results", {}),
                "formatted_response": "",
                "citations": [],
                "confidence_score": state.get("confidence_score", 0.0)
            }

            # 서브그래프 실행
            app = self.response_generator.workflow.compile()
            result = await app.ainvoke(response_state)

            # 결과를 메인 상태에 병합
            state["final_response"] = result.get("formatted_response", "응답을 생성할 수 없습니다.")
            state["response_format"] = result.get("response_format", "text")

            # 에러가 있었다면 응답에 포함
            if state.get("error_logs"):
                state["final_response"] += f"\n\n⚠️ 일부 오류가 발생했습니다: {', '.join(state['error_logs'][:3])}"

            logger.info(f"Response generated: {len(state['final_response'])} chars")

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            state["final_response"] = f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"
            state["error_logs"] = state.get("error_logs", [])
            state["error_logs"].append(f"Response generation: {str(e)}")

        return state

    async def store_conversation(self, state: MainState) -> MainState:
        """대화 저장"""
        # TODO: 대화 내용 저장 로직
        return state

    # 조건 메서드들
    def check_plan_validity(self, state: MainState) -> str:
        """계획 유효성 검사"""
        if state.get("execution_plan"):
            return "valid"
        return "invalid"

    def check_execution_status(self, state: MainState) -> str:
        """실행 상태 확인"""
        if state.get("agent_results"):
            return "success"
        return "failure"

    def check_evaluation(self, state: MainState) -> str:
        """평가 결과 확인"""
        if state.get("validated_results"):
            return "approved"
        return "need_revision"