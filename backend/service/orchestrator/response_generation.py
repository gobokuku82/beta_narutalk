from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any

class ResponseState(TypedDict):
    response_format: str
    raw_data: Dict[str, Any]
    formatted_response: str
    citations: List[str]
    confidence_score: float

class ResponseGenerationSubGraph:
    def __init__(self):
        self.workflow = StateGraph(ResponseState)
        self._build_graph()
    
    def _build_graph(self):
        self.workflow.add_node("format_selection", self.select_format)
        self.workflow.add_node("generate_text", self.generate_text_response)
        self.workflow.add_node("generate_table", self.generate_table_response)
        self.workflow.add_node("generate_chart", self.generate_chart_response)
        self.workflow.add_node("generate_document", self.generate_document_response)
        self.workflow.add_node("add_citations", self.add_references)
        self.workflow.add_node("final_review", self.final_quality_check)
        
        # 엔트리 포인트 정의 (LangGraph 0.6.7 방식)
        self.workflow.add_edge(START, "format_selection")
        
        self.workflow.add_conditional_edges(
            "format_selection",
            self.route_by_format,
            {
                "text": "generate_text",
                "table": "generate_table", 
                "chart": "generate_chart",
                "document": "generate_document"
            }
        )
        
        # 모든 생성 노드는 citations로
        for node in ["generate_text", "generate_table", "generate_chart", "generate_document"]:
            self.workflow.add_edge(node, "add_citations")
        
        self.workflow.add_edge("add_citations", "final_review")
        self.workflow.add_edge("final_review", END)

    # 노드 메서드들
    async def select_format(self, state: ResponseState) -> ResponseState:
        """응답 형식 선택"""
        state["response_format"] = "text"
        return state

    async def generate_text_response(self, state: ResponseState) -> ResponseState:
        """텍스트 응답 생성"""
        state["formatted_response"] = "텍스트 응답입니다."
        return state

    async def generate_table_response(self, state: ResponseState) -> ResponseState:
        """테이블 응답 생성"""
        state["formatted_response"] = "테이블 응답입니다."
        return state

    async def generate_chart_response(self, state: ResponseState) -> ResponseState:
        """차트 응답 생성"""
        state["formatted_response"] = "차트 응답입니다."
        return state

    async def generate_document_response(self, state: ResponseState) -> ResponseState:
        """문서 응답 생성"""
        state["formatted_response"] = "문서 응답입니다."
        return state

    async def add_references(self, state: ResponseState) -> ResponseState:
        """참조/인용 추가"""
        state["citations"] = []
        return state

    async def final_quality_check(self, state: ResponseState) -> ResponseState:
        """최종 품질 확인"""
        state["confidence_score"] = 0.95
        return state

    def route_by_format(self, state: ResponseState) -> str:
        """포맷별 라우팅"""
        format_type = state.get("response_format", "text")
        if format_type in ["text", "table", "chart", "document"]:
            return format_type
        return "text"