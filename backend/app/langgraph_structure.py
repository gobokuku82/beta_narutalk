"""
정확한 LangGraph 구조 구현 예시

4개 전문 에이전트를 LangGraph로 구현하는 방법
"""

from typing import TypedDict, List, Dict, Any, Annotated, Optional
from typing_extensions import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# 1. STATE 정의 (LangGraph의 핵심)
# =============================================================================

class AgentState(TypedDict):
    """LangGraph 상태 정의 - 모든 노드에서 공유되는 상태"""
    
    # 메시지 관련
    messages: Annotated[List[BaseMessage], add_messages]
    current_message: str
    
    # 라우팅 관련
    current_agent: Optional[str]
    agent_switches: int
    routing_confidence: float
    
    # 사용자 관련
    user_id: str
    session_id: str
    user_preferences: Dict[str, Any]
    
    # 분석 결과
    search_results: List[Dict[str, Any]]
    analysis_results: List[Dict[str, Any]]
    document_drafts: List[Dict[str, Any]]
    
    # 워크플로우 제어
    next_action: Optional[str]
    is_complete: bool
    error_message: Optional[str]
    
    # 메타데이터
    workflow_history: List[str]
    confidence_scores: Dict[str, float]

# =============================================================================
# 2. NODE 함수들 정의
# =============================================================================

def router_node(state: AgentState) -> AgentState:
    """라우터 노드 - 최적의 에이전트 선택"""
    try:
        message = state["current_message"].lower()
        
        # 각 에이전트별 신뢰도 계산
        confidence_scores = {
            "document_search": calculate_search_confidence(message),
            "document_draft": calculate_draft_confidence(message),
            "performance_analysis": calculate_performance_confidence(message),
            "client_analysis": calculate_client_confidence(message)
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

def document_search_node(state: AgentState) -> AgentState:
    """문서검색 에이전트 노드"""
    try:
        message = state["current_message"]
        
        # 벡터DB 검색 수행
        search_results = perform_document_search(message)
        
        # 검색 결과가 충분한지 확인
        if len(search_results) >= 3:
            state["search_results"] = search_results
            state["is_complete"] = True
            state["next_action"] = "complete"
            
            # AI 메시지 추가
            response = generate_search_response(search_results, message)
            state["messages"].append(AIMessage(content=response))
        else:
            # 검색 결과 부족시 다른 에이전트로 전환
            state["next_action"] = "switch_agent"
        
        state["workflow_history"].append("document_search_completed")
        return state
        
    except Exception as e:
        logger.error(f"문서검색 노드 오류: {str(e)}")
        state["error_message"] = str(e)
        state["next_action"] = "error"
        return state

def document_draft_node(state: AgentState) -> AgentState:
    """문서작성 에이전트 노드"""
    try:
        message = state["current_message"]
        
        # 문서 유형 분석
        doc_type = analyze_document_type(message)
        
        # 문서 초안 생성
        draft = generate_document_draft(message, doc_type)
        
        state["document_drafts"].append({
            "type": doc_type,
            "content": draft,
            "timestamp": "now"  # 실제로는 datetime 사용
        })
        
        state["is_complete"] = True
        state["next_action"] = "complete"
        
        # AI 메시지 추가
        response = format_draft_response(draft, doc_type)
        state["messages"].append(AIMessage(content=response))
        
        state["workflow_history"].append("document_draft_completed")
        return state
        
    except Exception as e:
        logger.error(f"문서작성 노드 오류: {str(e)}")
        state["error_message"] = str(e)
        state["next_action"] = "error"
        return state

def performance_analysis_node(state: AgentState) -> AgentState:
    """실적분석 에이전트 노드"""
    try:
        message = state["current_message"]
        
        # 분석 유형 결정
        analysis_type = determine_analysis_type(message)
        
        # 실적 분석 수행
        analysis_result = perform_performance_analysis(analysis_type, message)
        
        state["analysis_results"].append(analysis_result)
        state["is_complete"] = True
        state["next_action"] = "complete"
        
        # AI 메시지 추가
        response = format_analysis_response(analysis_result)
        state["messages"].append(AIMessage(content=response))
        
        state["workflow_history"].append("performance_analysis_completed")
        return state
        
    except Exception as e:
        logger.error(f"실적분석 노드 오류: {str(e)}")
        state["error_message"] = str(e)
        state["next_action"] = "error"
        return state

def client_analysis_node(state: AgentState) -> AgentState:
    """거래처분석 에이전트 노드"""
    try:
        message = state["current_message"]
        
        # 분석 유형 결정
        analysis_type = determine_client_analysis_type(message)
        
        # 거래처 분석 수행
        analysis_result = perform_client_analysis(analysis_type, message)
        
        state["analysis_results"].append(analysis_result)
        state["is_complete"] = True
        state["next_action"] = "complete"
        
        # AI 메시지 추가
        response = format_client_analysis_response(analysis_result)
        state["messages"].append(AIMessage(content=response))
        
        state["workflow_history"].append("client_analysis_completed")
        return state
        
    except Exception as e:
        logger.error(f"거래처분석 노드 오류: {str(e)}")
        state["error_message"] = str(e)
        state["next_action"] = "error"
        return state

def error_handler_node(state: AgentState) -> AgentState:
    """오류 처리 노드"""
    error_msg = state.get("error_message", "알 수 없는 오류가 발생했습니다.")
    
    state["messages"].append(AIMessage(
        content=f"죄송합니다. 처리 중 오류가 발생했습니다: {error_msg}"
    ))
    state["is_complete"] = True
    state["next_action"] = "complete"
    state["workflow_history"].append("error_handled")
    
    return state

# =============================================================================
# 3. 조건부 EDGE 함수들
# =============================================================================

def route_after_router(state: AgentState) -> Literal["document_search", "document_draft", "performance_analysis", "client_analysis", "error"]:
    """라우터 이후 에이전트 선택"""
    if state.get("error_message"):
        return "error"
    
    current_agent = state.get("current_agent")
    confidence = state.get("routing_confidence", 0.0)
    
    # 신뢰도가 너무 낮으면 오류 처리
    if confidence < 0.3:
        return "error"
    
    return current_agent

def should_continue_or_end(state: AgentState) -> Literal["END", "router", "error"]:
    """워크플로우 계속 진행 여부 결정"""
    if state.get("error_message"):
        return "error"
    
    if state.get("is_complete", False):
        return "END"
    
    # 에이전트 전환이 필요한 경우
    if state.get("next_action") == "switch_agent":
        if state.get("agent_switches", 0) < 3:  # 최대 3번 전환
            state["agent_switches"] += 1
            return "router"
        else:
            return "error"  # 너무 많은 전환 시 오류
    
    return "END"

# =============================================================================
# 4. 헬퍼 함수들 (실제 구현 필요)
# =============================================================================

def calculate_search_confidence(message: str) -> float:
    """문서검색 신뢰도 계산"""
    search_keywords = ["검색", "찾아", "문서", "자료", "정책", "규정"]
    confidence = 0.0
    for keyword in search_keywords:
        if keyword in message:
            confidence += 0.2
    return min(confidence, 1.0)

def calculate_draft_confidence(message: str) -> float:
    """문서작성 신뢰도 계산"""
    draft_keywords = ["작성", "초안", "만들어", "생성", "보고서", "계획서"]
    confidence = 0.0
    for keyword in draft_keywords:
        if keyword in message:
            confidence += 0.2
    return min(confidence, 1.0)

def calculate_performance_confidence(message: str) -> float:
    """실적분석 신뢰도 계산"""
    performance_keywords = ["실적", "성과", "매출", "분석", "트렌드", "KPI"]
    confidence = 0.0
    for keyword in performance_keywords:
        if keyword in message:
            confidence += 0.2
    return min(confidence, 1.0)

def calculate_client_confidence(message: str) -> float:
    """거래처분석 신뢰도 계산"""
    client_keywords = ["거래처", "고객", "클라이언트", "세분화", "위험도"]
    confidence = 0.0
    for keyword in client_keywords:
        if keyword in message:
            confidence += 0.2
    return min(confidence, 1.0)

def perform_document_search(message: str) -> List[Dict[str, Any]]:
    """실제 문서 검색 수행"""
    # 실제 구현에서는 벡터DB 검색
    return [
        {"title": "샘플 문서 1", "content": "...", "relevance": 0.9},
        {"title": "샘플 문서 2", "content": "...", "relevance": 0.8}
    ]

def generate_document_draft(message: str, doc_type: str) -> str:
    """문서 초안 생성"""
    # 실제 구현에서는 템플릿 + AI 생성
    return f"{doc_type} 초안이 생성되었습니다..."

def perform_performance_analysis(analysis_type: str, message: str) -> Dict[str, Any]:
    """실적 분석 수행"""
    # 실제 구현에서는 데이터베이스 조회 + 분석
    return {"type": analysis_type, "result": "분석 완료"}

def perform_client_analysis(analysis_type: str, message: str) -> Dict[str, Any]:
    """거래처 분석 수행"""
    # 실제 구현에서는 고객 데이터 분석
    return {"type": analysis_type, "result": "분석 완료"}

# 응답 포맷팅 함수들 (생략)
def generate_search_response(results, message): return "검색 결과..."
def format_draft_response(draft, doc_type): return "문서 초안..."
def format_analysis_response(result): return "분석 결과..."
def format_client_analysis_response(result): return "거래처 분석..."
def analyze_document_type(message): return "report"
def determine_analysis_type(message): return "sales"
def determine_client_analysis_type(message): return "segmentation"

# =============================================================================
# 5. LANGGRAPH 워크플로우 구성
# =============================================================================

class NaruTalkWorkflow:
    """NaruTalk LangGraph 워크플로우"""
    
    def __init__(self):
        self.workflow = None
        self.app = None
        self._build_workflow()
    
    def _build_workflow(self):
        """워크플로우 구성"""
        
        # StateGraph 생성
        workflow = StateGraph(AgentState)
        
        # 노드 추가
        workflow.add_node("router", router_node)
        workflow.add_node("document_search", document_search_node)
        workflow.add_node("document_draft", document_draft_node)
        workflow.add_node("performance_analysis", performance_analysis_node)
        workflow.add_node("client_analysis", client_analysis_node)
        workflow.add_node("error_handler", error_handler_node)
        
        # 엣지 추가
        workflow.add_edge(START, "router")
        
        # 조건부 엣지
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
        
        # 완료 조건부 엣지
        workflow.add_conditional_edges(
            "document_search",
            should_continue_or_end,
            {
                "END": END,
                "router": "router",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "document_draft",
            should_continue_or_end,
            {
                "END": END,
                "router": "router",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "performance_analysis",
            should_continue_or_end,
            {
                "END": END,
                "router": "router",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "client_analysis",
            should_continue_or_end,
            {
                "END": END,
                "router": "router",
                "error": "error_handler"
            }
        )
        
        workflow.add_edge("error_handler", END)
        
        # 워크플로우 컴파일
        self.workflow = workflow
        self.app = workflow.compile()
    
    async def process_message(self, message: str, user_id: str = "user", session_id: str = "session") -> Dict[str, Any]:
        """메시지 처리"""
        
        # 초기 상태 생성
        initial_state = AgentState(
            messages=[HumanMessage(content=message)],
            current_message=message,
            current_agent=None,
            agent_switches=0,
            routing_confidence=0.0,
            user_id=user_id,
            session_id=session_id,
            user_preferences={},
            search_results=[],
            analysis_results=[],
            document_drafts=[],
            next_action=None,
            is_complete=False,
            error_message=None,
            workflow_history=[],
            confidence_scores={}
        )
        
        # 워크플로우 실행
        final_state = await self.app.ainvoke(initial_state)
        
        # 결과 반환
        return {
            "response": final_state["messages"][-1].content if final_state["messages"] else "응답을 생성할 수 없습니다.",
            "workflow_history": final_state["workflow_history"],
            "confidence_scores": final_state["confidence_scores"],
            "current_agent": final_state["current_agent"],
            "is_complete": final_state["is_complete"],
            "error": final_state.get("error_message")
        }

# =============================================================================
# 6. 사용 예시
# =============================================================================

async def main():
    """LangGraph 워크플로우 사용 예시"""
    
    # 워크플로우 초기화
    workflow = NaruTalkWorkflow()
    
    # 테스트 메시지들
    test_messages = [
        "좋은제약 복리후생 정책 문서 찾아줘",
        "월간 실적 보고서 작성해줘",
        "올해 매출 분석 결과 보여줘",
        "고객 세분화 분석해줘"
    ]
    
    for message in test_messages:
        print(f"\n🔵 입력: {message}")
        result = await workflow.process_message(message)
        print(f"📝 응답: {result['response']}")
        print(f"🔄 경로: {' → '.join(result['workflow_history'])}")
        print(f"🎯 에이전트: {result['current_agent']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 