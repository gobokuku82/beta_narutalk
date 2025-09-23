"""
Fast version of ResponseGenerationSubGraph without LLM calls
"""

from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ResponseState(TypedDict):
    validated_results: Dict[str, Any]
    response_format: str
    user_context: Optional[Dict]
    formatted_response: str
    citations: List[str]
    confidence_score: float

class ResponseGenerationSubGraph:
    def __init__(self):
        self.workflow = StateGraph(ResponseState)
        self._build_graph()

    def _build_graph(self):
        self.workflow.add_node("format_selection", self.select_response_format)
        self.workflow.add_node("generate_text", self.generate_text_response)
        self.workflow.add_node("generate_table", self.generate_table_response)
        self.workflow.add_node("generate_chart", self.generate_chart_response)
        self.workflow.add_node("generate_document", self.generate_document_response)
        self.workflow.add_node("add_citations", self.add_citations_and_sources)
        self.workflow.add_node("final_review", self.final_quality_check)

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

        self.workflow.add_edge("generate_text", "add_citations")
        self.workflow.add_edge("generate_table", "add_citations")
        self.workflow.add_edge("generate_chart", "add_citations")
        self.workflow.add_edge("generate_document", "add_citations")
        self.workflow.add_edge("add_citations", "final_review")
        self.workflow.add_edge("final_review", END)

    async def select_response_format(self, state: ResponseState) -> ResponseState:
        """Fast version - default to text"""
        if not state.get("response_format"):
            state["response_format"] = "text"
        logger.info(f"Selected format: {state['response_format']} (fast mode)")
        return state

    async def generate_text_response(self, state: ResponseState) -> ResponseState:
        """Fast version - no LLM"""
        state["formatted_response"] = "분석 결과가 준비되었습니다. (Fast mode - 실제 LLM 응답이 아닙니다)"
        logger.info("Text response generated (fast mode)")
        return state

    async def generate_table_response(self, state: ResponseState) -> ResponseState:
        """Fast version - no LLM"""
        state["formatted_response"] = "| 항목 | 결과 |\n|------|------|\n| 테스트 | 데이터 |"
        logger.info("Table response generated (fast mode)")
        return state

    async def generate_chart_response(self, state: ResponseState) -> ResponseState:
        """Fast version - no LLM"""
        state["formatted_response"] = "차트 데이터가 준비되었습니다."
        logger.info("Chart response generated (fast mode)")
        return state

    async def generate_document_response(self, state: ResponseState) -> ResponseState:
        """Fast version - no LLM"""
        state["formatted_response"] = "## 분석 보고서\n\n결과가 준비되었습니다."
        logger.info("Document response generated (fast mode)")
        return state

    async def add_citations_and_sources(self, state: ResponseState) -> ResponseState:
        """Fast version - no processing"""
        state["citations"] = []
        logger.info("Citations added (fast mode)")
        return state

    async def final_quality_check(self, state: ResponseState) -> ResponseState:
        """Fast version - no LLM"""
        state["confidence_score"] = 0.8
        logger.info("Final review complete (fast mode)")
        return state

    def route_by_format(self, state: ResponseState) -> str:
        """Route by response format"""
        format_type = state.get("response_format", "text")
        if format_type in ["text", "table", "chart", "document"]:
            return format_type
        return "text"