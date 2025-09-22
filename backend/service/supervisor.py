from langgraph.graph import StateGraph, END
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver
from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum

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
        self.checkpointer = AsyncSqliteSaver.from_path("database/checkpointer/main.db")
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
        
        # 엣지 정의
        self.workflow.set_entry_point("authenticate")
        
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