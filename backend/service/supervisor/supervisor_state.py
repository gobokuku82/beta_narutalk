"""
Supervisor State Definitions
슈퍼바이저의 상태 관리 - 추론과 실행 계획
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from operator import add
from datetime import datetime


def merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Merge dictionaries, b overwrites a"""
    if not a:
        return b or {}
    if not b:
        return a
    return {**a, **b}


def append_unique(a: List[Any], b: List[Any]) -> List[Any]:
    """Append only unique items to list"""
    if not a:
        a = []
    if not b:
        return a
    result = a.copy()
    for item in b:
        if item not in result:
            result.append(item)
    return result


class SupervisorState(TypedDict):
    """
    Supervisor State
    슈퍼바이저가 관리하는 전체 워크플로우 상태
    """

    # ====== Input ======
    user_query: str  # 사용자의 원본 질의
    session_id: str  # 세션 ID
    user_id: Optional[str]  # 사용자 ID

    # ====== Reasoning (추론) ======
    query_understanding: Optional[Dict[str, Any]]  # 질의 이해 결과
    task_decomposition: Optional[List[Dict[str, Any]]]  # 작업 분해
    execution_plan: Optional[Dict[str, Any]]  # 실행 계획

    # ====== Execution Control (실행 통제) ======
    current_step: str  # 현재 실행 단계
    next_action: Optional[str]  # 다음 액션 (route, data_collection, analysis, report, END)
    subgraph_selection: Optional[List[str]]  # 실행할 서브그래프 목록

    # ====== Subgraph Communication ======
    data_collection_input: Optional[Dict[str, Any]]  # 데이터 수집 서브그래프 입력
    analysis_input: Optional[Dict[str, Any]]  # 분석 서브그래프 입력

    data_collection_output: Optional[Dict[str, Any]]  # 데이터 수집 서브그래프 출력
    analysis_output: Optional[Dict[str, Any]]  # 분석 서브그래프 출력

    # ====== Results Aggregation ======
    collected_data: Annotated[Dict[str, Any], merge_dicts]  # 수집된 데이터
    analysis_results: Annotated[Dict[str, Any], merge_dicts]  # 분석 결과
    insights: Annotated[List[str], append_unique]  # 인사이트

    # ====== Final Output ======
    final_answer: Optional[str]  # 최종 답변
    final_report: Optional[Dict[str, Any]]  # 최종 보고서

    # ====== Status & Monitoring ======
    status: str  # pending, reasoning, executing, completed, failed
    errors: Annotated[List[str], add]  # 에러 메시지
    execution_trace: Annotated[List[Dict[str, Any]], add]  # 실행 추적

    # ====== Timing ======
    start_time: Optional[str]
    end_time: Optional[str]

    # ====== Metadata ======
    metadata: Annotated[Dict[str, Any], merge_dicts]  # 추가 메타데이터


def create_supervisor_initial_state(
    user_query: str,
    session_id: str,
    user_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create initial supervisor state

    Args:
        user_query: User's query
        session_id: Session identifier
        user_id: User identifier
        **kwargs: Additional metadata

    Returns:
        Initial state dictionary
    """
    return {
        # Input
        "user_query": user_query,
        "session_id": session_id,
        "user_id": user_id,

        # Reasoning
        "query_understanding": None,
        "task_decomposition": None,
        "execution_plan": None,

        # Execution Control
        "current_step": "initialization",
        "next_action": None,
        "subgraph_selection": None,

        # Subgraph Communication
        "data_collection_input": None,
        "analysis_input": None,
        "data_collection_output": None,
        "analysis_output": None,

        # Results
        "collected_data": {},
        "analysis_results": {},
        "insights": [],

        # Output
        "final_answer": None,
        "final_report": None,

        # Status
        "status": "pending",
        "errors": [],
        "execution_trace": [],

        # Timing
        "start_time": datetime.now().isoformat(),
        "end_time": None,

        # Metadata
        "metadata": kwargs
    }


def get_supervisor_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get summary of supervisor state

    Args:
        state: Current supervisor state

    Returns:
        State summary
    """
    return {
        "session_id": state.get("session_id"),
        "status": state.get("status"),
        "current_step": state.get("current_step"),
        "next_action": state.get("next_action"),
        "subgraphs_used": state.get("subgraph_selection", []),
        "has_data": bool(state.get("collected_data")),
        "has_analysis": bool(state.get("analysis_results")),
        "has_final_answer": bool(state.get("final_answer")),
        "errors_count": len(state.get("errors", [])),
        "execution_steps": len(state.get("execution_trace", [])),
        "start_time": state.get("start_time"),
        "end_time": state.get("end_time")
    }
