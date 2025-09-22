from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any

class ComplianceState(TypedDict):
    checkpoint: str
    document_to_check: Dict[str, Any]
    relevant_regulations: List[Dict]
    violations: List[Dict]
    compliance_score: float
    report: str

class ComplianceCheckAgent:
    def __init__(self):
        self.workflow = StateGraph(ComplianceState)
        self.vector_db = self._init_chroma_db()
        self._build_graph()
    
    def _build_graph(self):
        self.workflow.add_node("extract_checkpoints", self.extract_compliance_points)
        self.workflow.add_node("search_regulations", self.vector_search_regulations)
        self.workflow.add_node("cross_reference", self.cross_reference_rules)
        self.workflow.add_node("evaluate_compliance", self.evaluate_compliance_status)
        self.workflow.add_node("generate_report", self.generate_compliance_report)
        
        # 엔트리 포인트 정의 (LangGraph 0.6.7 방식)
        self.workflow.add_edge(START, "extract_checkpoints")
        self.workflow.add_edge("extract_checkpoints", "search_regulations")
        self.workflow.add_edge("search_regulations", "cross_reference")
        self.workflow.add_edge("cross_reference", "evaluate_compliance")
        
        self.workflow.add_conditional_edges(
            "evaluate_compliance",
            self.check_violation,
            {
                "violation_found": "generate_report",
                "compliant": END
            }
        )
        self.workflow.add_edge("generate_report", END)
    
    async def vector_search_regulations(self, state):
        """ChromaDB에서 관련 규정 검색"""
        query_embedding = self.embed_query(state['checkpoint'])
        results = self.vector_db.similarity_search(
            query_embedding,
            k=10
        )
        
        # Reranker 적용
        reranked = self.reranker.rerank(
            query=state['checkpoint'],
            documents=results
        )
        
        state['relevant_regulations'] = reranked[:5]
        return state