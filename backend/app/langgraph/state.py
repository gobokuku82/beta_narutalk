"""
LangGraph 0.6.6 State 정의
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    멀티 에이전트 시스템의 공유 State
    LangGraph 0.6.6 StateGraph에서 사용
    """
    
    # 메시지 히스토리 (reducer 패턴)
    messages: Annotated[List[Dict[str, Any]], add_messages]
    
    # 현재 활성 에이전트
    current_agent: str
    
    # 다음 실행할 에이전트
    next_agent: Optional[str]
    
    # 세션 정보
    session_id: str
    user_id: Optional[str]
    
    # 컨텍스트 정보
    context: Dict[str, Any]
    
    # 각 에이전트의 출력 결과
    agent_outputs: Dict[str, Any]
    
    # 도구 실행 결과
    tool_outputs: List[Dict[str, Any]]
    
    # 에러 정보
    error: Optional[str]
    
    # 실행 메타데이터
    metadata: Dict[str, Any]
    
    # 반복 카운터 (무한 루프 방지)
    iteration_count: int
    
    # 종료 플래그
    should_end: bool


class RoutingState(TypedDict):
    """라우팅 결정을 위한 State"""
    intent: str
    confidence: float
    suggested_agent: str
    fallback_agent: Optional[str]


class ToolState(TypedDict):
    """도구 실행을 위한 State"""
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Any
    execution_time: float
    success: bool
    error_message: Optional[str]


# State 초기화 함수
def initialize_state(session_id: str, user_id: Optional[str] = None) -> AgentState:
    """새로운 State 인스턴스 생성"""
    return {
        "messages": [],
        "current_agent": "supervisor",
        "next_agent": None,
        "session_id": session_id,
        "user_id": user_id,
        "context": {},
        "agent_outputs": {},
        "tool_outputs": [],
        "error": None,
        "metadata": {},
        "iteration_count": 0,
        "should_end": False
    }


# State 업데이트 헬퍼 함수
def update_agent_state(
    state: AgentState,
    agent_name: str,
    output: Any,
    next_agent: Optional[str] = None
) -> Dict[str, Any]:
    """에이전트 실행 후 State 업데이트"""
    return {
        "current_agent": agent_name,
        "next_agent": next_agent,
        "agent_outputs": {**state.get("agent_outputs", {}), agent_name: output},
        "iteration_count": state.get("iteration_count", 0) + 1
    }


def add_tool_output(state: AgentState, tool_output: ToolState) -> Dict[str, Any]:
    """도구 실행 결과를 State에 추가"""
    current_outputs = state.get("tool_outputs", [])
    return {
        "tool_outputs": current_outputs + [tool_output]
    }


def should_continue(state: AgentState) -> bool:
    """계속 실행할지 결정"""
    # 종료 조건 체크
    if state.get("should_end", False):
        return False
    
    # 최대 반복 횟수 체크
    if state.get("iteration_count", 0) >= 10:
        return False
    
    # 에러 발생 체크
    if state.get("error"):
        return False
    
    return True