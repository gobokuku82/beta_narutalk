"""
LangGraph 기반 라우터 시스템

4개 전문 에이전트를 LangGraph 워크플로우로 관리하는 라우터 시스템입니다.
TypedDict 기반 상태 관리와 조건부 엣지를 통한 강력한 라우팅을 제공합니다.
"""

from typing import TypedDict, List, Dict, Any, Annotated, Optional, Literal
from typing_extensions import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import logging
import asyncio
from dataclasses import asdict

# 기존 에이전트 import
from ..agents import (
    DocumentSearchAgent, 
    DocumentDraftAgent,
    PerformanceAnalysisAgent,
    ClientAnalysisAgent,
    AgentContext,
    AgentResult,
    AgentAction
)

logger = logging.getLogger(__name__)

# =============================================================================
# 1. LANGGRAPH STATE 정의 (TypedDict 기반)
# =============================================================================

class RouterState(TypedDict):
    """LangGraph 라우터 상태 - 모든 노드에서 공유되는 상태"""
    
    # 메시지 관련 (LangGraph 표준)
    messages: Annotated[List[BaseMessage], add_messages]
    current_message: str
    
    # 라우팅 관련
    current_agent: Optional[str]
    agent_switches: int
    routing_confidence: float
    confidence_scores: Dict[str, float]
    
    # 사용자 관련
    user_id: str
    session_id: str
    user_preferences: Dict[str, Any]
    conversation_history: List[Dict[str, str]]
    
    # 처리 결과
    final_response: str
    agent_response: str
    search_results: List[Dict[str, Any]]
    document_drafts: List[Dict[str, Any]]
    analysis_results: List[Dict[str, Any]]
    
    # 워크플로우 제어
    next_action: Optional[str]
    is_complete: bool
    error_message: Optional[str]
    should_continue: bool
    
    # 메타데이터
    workflow_history: List[str]
    processing_time: float
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]

# =============================================================================
# 2. NODE 함수들 정의 (LangGraph 노드)
# =============================================================================

def router_node(state: RouterState) -> RouterState:
    """라우터 노드 - 최적의 에이전트 선택"""
    try:
        message = state["current_message"].lower()
        
        # 각 에이전트별 신뢰도 계산
        confidence_scores = {
            "document_search": _calculate_search_confidence(message),
            "document_draft": _calculate_draft_confidence(message),
            "performance_analysis": _calculate_performance_confidence(message),
            "client_analysis": _calculate_client_confidence(message)
        }
        
        # 최고 신뢰도 에이전트 선택
        best_agent = max(confidence_scores.keys(), key=lambda k: confidence_scores[k])
        best_confidence = confidence_scores[best_agent]
        
        # 상태 업데이트
        state["current_agent"] = best_agent
        state["routing_confidence"] = best_confidence
        state["confidence_scores"] = confidence_scores
        state["workflow_history"].append(f"routed_to_{best_agent}")
        
        logger.info(f"라우터: {best_agent} 선택 (신뢰도: {best_confidence:.3f})")
        
        return state
        
    except Exception as e:
        logger.error(f"라우터 노드 오류: {str(e)}")
        state["error_message"] = str(e)
        state["next_action"] = "error"
        return state


def document_search_node(state: RouterState) -> RouterState:
    """문서검색 에이전트 노드"""
    try:
        logger.info("문서검색 에이전트 실행")
        
        # AgentContext 생성 (기존 에이전트와 호환성)
        context = _create_agent_context(state)
        
        # 문서검색 에이전트 실행 (동기적으로 실행)
        agent = _get_document_search_agent()
        result = asyncio.run(_execute_agent(agent, context))
        
        # 결과를 상태에 반영
        state = _update_state_from_result(state, result, "document_search")
        state["workflow_history"].append("executed_document_search")
        
        return state
        
    except Exception as e:
        logger.error(f"문서검색 노드 오류: {str(e)}")
        state["error_message"] = str(e)
        state["next_action"] = "error"
        return state


def document_draft_node(state: RouterState) -> RouterState:
    """문서작성 에이전트 노드"""
    try:
        logger.info("문서작성 에이전트 실행")
        
        context = _create_agent_context(state)
        agent = _get_document_draft_agent()
        result = asyncio.run(_execute_agent(agent, context))
        
        state = _update_state_from_result(state, result, "document_draft")
        state["workflow_history"].append("executed_document_draft")
        
        return state
        
    except Exception as e:
        logger.error(f"문서작성 노드 오류: {str(e)}")
        state["error_message"] = str(e)
        state["next_action"] = "error"
        return state


def performance_analysis_node(state: RouterState) -> RouterState:
    """실적분석 에이전트 노드"""
    try:
        logger.info("실적분석 에이전트 실행")
        
        context = _create_agent_context(state)
        agent = _get_performance_analysis_agent()
        result = asyncio.run(_execute_agent(agent, context))
        
        state = _update_state_from_result(state, result, "performance_analysis")
        state["workflow_history"].append("executed_performance_analysis")
        
        return state
        
    except Exception as e:
        logger.error(f"실적분석 노드 오류: {str(e)}")
        state["error_message"] = str(e)
        state["next_action"] = "error"
        return state


def client_analysis_node(state: RouterState) -> RouterState:
    """거래처분석 에이전트 노드"""
    try:
        logger.info("거래처분석 에이전트 실행")
        
        context = _create_agent_context(state)
        agent = _get_client_analysis_agent()
        result = asyncio.run(_execute_agent(agent, context))
        
        state = _update_state_from_result(state, result, "client_analysis")
        state["workflow_history"].append("executed_client_analysis")
        
        return state
        
    except Exception as e:
        logger.error(f"거래처분석 노드 오류: {str(e)}")
        state["error_message"] = str(e)
        state["next_action"] = "error"
        return state


def error_handler_node(state: RouterState) -> RouterState:
    """오류 처리 노드"""
    try:
        error_msg = state.get("error_message", "알 수 없는 오류가 발생했습니다.")
        
        state["final_response"] = f"죄송합니다. 처리 중 오류가 발생했습니다: {error_msg}"
        state["is_complete"] = True
        state["should_continue"] = False
        state["workflow_history"].append("error_handled")
        
        logger.error(f"오류 처리: {error_msg}")
        
        return state
        
    except Exception as e:
        logger.error(f"오류 핸들러 노드 오류: {str(e)}")
        state["final_response"] = "시스템 오류가 발생했습니다."
        state["is_complete"] = True
        state["should_continue"] = False
        return state


# =============================================================================
# 3. 조건부 엣지 함수들 (LangGraph 라우팅)
# =============================================================================

def route_after_router(state: RouterState) -> Literal["document_search", "document_draft", "performance_analysis", "client_analysis", "error"]:
    """라우터 후 조건부 라우팅"""
    current_agent = state.get("current_agent")
    confidence = state.get("routing_confidence", 0.0)
    
    # 신뢰도가 너무 낮은 경우 오류 처리
    if confidence < 0.3:
        logger.warning(f"신뢰도가 낮아 오류 처리: {confidence:.3f}")
        return "error"
    
    # 에이전트별 라우팅
    if current_agent == "document_search":
        return "document_search"
    elif current_agent == "document_draft":
        return "document_draft"
    elif current_agent == "performance_analysis":
        return "performance_analysis"
    elif current_agent == "client_analysis":
        return "client_analysis"
    else:
        logger.warning(f"알 수 없는 에이전트: {current_agent}")
        return "error"


def should_continue_or_end(state: RouterState) -> Literal["continue", "end"]:
    """계속 처리할지 종료할지 결정"""
    # 오류가 있거나 완료된 경우 종료
    if state.get("error_message") or state.get("is_complete"):
        return "end"
    
    # 에이전트 전환 필요한지 확인
    result_action = state.get("next_action")
    if result_action == "switch" and state.get("agent_switches", 0) < 3:
        return "continue"
    
    # 기본적으로 종료
    return "end"


# =============================================================================
# 4. HELPER 함수들
# =============================================================================

def _calculate_search_confidence(message: str) -> float:
    """문서검색 신뢰도 계산"""
    search_keywords = ["검색", "찾아", "조회", "문서", "자료", "정보", "찾기", "search", "find", "document"]
    confidence = 0.0
    for keyword in search_keywords:
        if keyword in message:
            confidence += 0.2
    return min(confidence, 1.0)


def _calculate_draft_confidence(message: str) -> float:
    """문서작성 신뢰도 계산"""
    draft_keywords = ["작성", "초안", "문서", "보고서", "제안서", "계획서", "만들어", "생성", "draft", "create", "write"]
    confidence = 0.0
    for keyword in draft_keywords:
        if keyword in message:
            confidence += 0.2
    return min(confidence, 1.0)


def _calculate_performance_confidence(message: str) -> float:
    """실적분석 신뢰도 계산"""
    performance_keywords = ["실적", "성과", "분석", "매출", "수익", "KPI", "performance", "sales", "revenue"]
    confidence = 0.0
    for keyword in performance_keywords:
        if keyword in message:
            confidence += 0.2
    return min(confidence, 1.0)


def _calculate_client_confidence(message: str) -> float:
    """거래처분석 신뢰도 계산"""
    client_keywords = ["거래처", "고객", "파트너", "클라이언트", "업체", "client", "customer", "partner"]
    confidence = 0.0
    for keyword in client_keywords:
        if keyword in message:
            confidence += 0.2
    return min(confidence, 1.0)


def _create_agent_context(state: RouterState) -> AgentContext:
    """RouterState에서 AgentContext 생성"""
    return AgentContext(
        current_message=state["current_message"],
        user_id=state["user_id"],
        session_id=state["session_id"],
        conversation_history=state["conversation_history"],
        current_agent=state.get("current_agent", ""),
        agent_switches=state.get("agent_switches", 0),
        user_preferences=state["user_preferences"]
    )


async def _execute_agent(agent, context: AgentContext) -> AgentResult:
    """에이전트 실행"""
    return await agent.process(context)


def _update_state_from_result(state: RouterState, result: AgentResult, agent_name: str) -> RouterState:
    """AgentResult에서 RouterState 업데이트"""
    state["agent_response"] = result.response
    state["final_response"] = result.response
    state["sources"].extend(result.sources or [])
    state["metadata"].update(result.metadata or {})
    
    # 액션에 따른 처리
    if result.action == AgentAction.COMPLETE:
        state["is_complete"] = True
        state["should_continue"] = False
    elif result.action == AgentAction.SWITCH:
        state["next_action"] = "switch"
        state["current_agent"] = result.next_agent
        state["agent_switches"] += 1
    elif result.action == AgentAction.ERROR:
        state["error_message"] = result.response
        state["next_action"] = "error"
    
    return state


# 에이전트 인스턴스들 (전역으로 관리)
_agents = {}

def _get_document_search_agent():
    if "document_search" not in _agents:
        _agents["document_search"] = DocumentSearchAgent()
    return _agents["document_search"]

def _get_document_draft_agent():
    if "document_draft" not in _agents:
        _agents["document_draft"] = DocumentDraftAgent()
    return _agents["document_draft"]

def _get_performance_analysis_agent():
    if "performance_analysis" not in _agents:
        _agents["performance_analysis"] = PerformanceAnalysisAgent()
    return _agents["performance_analysis"]

def _get_client_analysis_agent():
    if "client_analysis" not in _agents:
        _agents["client_analysis"] = ClientAnalysisAgent()
    return _agents["client_analysis"]


# =============================================================================
# 5. LANGGRAPH 워크플로우 클래스
# =============================================================================

class LangGraphRouter:
    """LangGraph 기반 라우터 시스템"""
    
    def __init__(self):
        self.workflow = None
        self.compiled_workflow = None
        self._initialize_workflow()
        logger.info("LangGraph 라우터 초기화 완료")
    
    def _initialize_workflow(self):
        """LangGraph 워크플로우 구성"""
        try:
            # StateGraph 생성
            workflow = StateGraph(RouterState)
            
            # 노드 추가
            workflow.add_node("router", router_node)
            workflow.add_node("document_search", document_search_node)
            workflow.add_node("document_draft", document_draft_node)
            workflow.add_node("performance_analysis", performance_analysis_node)
            workflow.add_node("client_analysis", client_analysis_node)
            workflow.add_node("error_handler", error_handler_node)
            
            # 시작점 설정
            workflow.set_entry_point("router")
            
            # 조건부 엣지 추가 (라우터 → 에이전트들)
            workflow.add_conditional_edges(
                "router",
                route_after_router,
                {
                    "document_search": "document_search",
                    "document_draft": "document_draft", 
                    "performance_analysis": "performance_analysis",
                    "client_analysis": "client_analysis",
                    "error": "error_handler"
                }
            )
            
            # 각 에이전트에서 종료점으로의 엣지
            workflow.add_edge("document_search", END)
            workflow.add_edge("document_draft", END)
            workflow.add_edge("performance_analysis", END)
            workflow.add_edge("client_analysis", END)
            workflow.add_edge("error_handler", END)
            
            # 워크플로우 컴파일
            self.workflow = workflow
            self.compiled_workflow = workflow.compile()
            
            logger.info("LangGraph 워크플로우 구성 완료")
            
        except Exception as e:
            logger.error(f"워크플로우 초기화 실패: {str(e)}")
            raise
    
    def set_agent_services(self, **services):
        """모든 에이전트에 서비스 설정"""
        try:
            for agent in _agents.values():
                agent.set_services(**services)
            logger.info("에이전트 서비스 설정 완료")
        except Exception as e:
            logger.error(f"에이전트 서비스 설정 실패: {str(e)}")
    
    async def process_message(self, message: str, user_id: str, session_id: str,
                            conversation_history: List[Dict[str, str]] = None,
                            user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """메시지 처리"""
        try:
            # 초기 상태 생성
            initial_state = RouterState(
                messages=[HumanMessage(content=message)],
                current_message=message,
                current_agent=None,
                agent_switches=0,
                routing_confidence=0.0,
                confidence_scores={},
                user_id=user_id,
                session_id=session_id,
                user_preferences=user_preferences or {},
                conversation_history=conversation_history or [],
                final_response="",
                agent_response="",
                search_results=[],
                document_drafts=[],
                analysis_results=[],
                next_action=None,
                is_complete=False,
                should_continue=True,
                error_message=None,
                workflow_history=[],
                processing_time=0.0,
                sources=[],
                metadata={}
            )
            
            # 워크플로우 실행
            final_state = await self.compiled_workflow.ainvoke(initial_state)
            
            # 결과 반환
            return {
                "response": final_state.get("final_response", "응답을 생성할 수 없습니다."),
                "agent_type": final_state.get("current_agent", "unknown"),
                "confidence": final_state.get("routing_confidence", 0.0),
                "sources": final_state.get("sources", []),
                "metadata": {
                    "workflow_history": final_state.get("workflow_history", []),
                    "confidence_scores": final_state.get("confidence_scores", {}),
                    "agent_switches": final_state.get("agent_switches", 0),
                    **final_state.get("metadata", {})
                }
            }
            
        except Exception as e:
            logger.error(f"메시지 처리 실패: {str(e)}")
            return {
                "response": f"죄송합니다. 메시지 처리 중 오류가 발생했습니다: {str(e)}",
                "agent_type": "error",
                "confidence": 0.0,
                "sources": [],
                "metadata": {"error": str(e)}
            }
    
    def get_workflow_visualization(self) -> str:
        """워크플로우 시각화 정보 반환"""
        return """
LangGraph 워크플로우 구조:

START → router → [document_search, document_draft, performance_analysis, client_analysis, error_handler] → END

조건부 라우팅:
- router: 신뢰도 기반 에이전트 선택
- 각 에이전트: 처리 후 바로 종료
- error_handler: 오류 발생 시 처리
        """
    
    def get_router_statistics(self) -> Dict[str, Any]:
        """라우터 통계 정보"""
        return {
            "total_nodes": 6,
            "agent_nodes": 4,
            "total_agents": len(_agents),
            "available_agents": list(_agents.keys()),
            "workflow_compiled": bool(self.compiled_workflow)
        } 