"""
Simplified SearchAgent - 모델 로딩 없이 빠르게 동작하는 버전
원본은 search_agent_old.py에 백업됨
"""

from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
import sqlite3
import asyncio
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SearchState(TypedDict):
    query: str
    search_type: str  # hr_info, hr_rules, both
    filters: Dict[str, Any]
    hr_results: List[Dict[str, Any]]
    rules_results: List[Dict[str, Any]]
    reranked_results: List[Dict[str, Any]]
    relevance_scores: Dict[str, float]
    sources: List[str]
    final_results: Dict[str, Any]
    execution_status: str

class SearchAgent:
    def __init__(self):
        """간소화된 초기화 - 모델 로딩 없음"""
        self.workflow = StateGraph(SearchState)
        self._initialize_databases()
        self._build_graph()
        logger.info("SearchAgent initialized (simplified version - no model loading)")

    def _initialize_databases(self):
        """데이터베이스 초기화 - ChromaDB와 모델 제외"""
        # SQLite만 설정 (인사정보)
        self.hr_info_path = Path("database/storage/hr_information/hr_data.db")

        # 모델은 로드하지 않음
        self.embedding_model = None
        self.reranker_model = None
        self.reranker_tokenizer = None

        logger.info("Database initialized (SQLite only, no ChromaDB or models)")

    def _build_graph(self):
        """간소화된 그래프 구성"""
        # 노드 추가
        self.workflow.add_node("analyze_query", self.analyze_search_query)
        self.workflow.add_node("search_hr_info", self.search_hr_information)
        self.workflow.add_node("format_response", self.format_final_response)

        # 엔트리 포인트 설정
        self.workflow.add_edge(START, "analyze_query")
        self.workflow.add_edge("analyze_query", "search_hr_info")
        self.workflow.add_edge("search_hr_info", "format_response")
        self.workflow.add_edge("format_response", END)

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 실행 인터페이스"""
        initial_state = SearchState(
            query=input_data.get("query", ""),
            search_type=input_data.get("search_type", "hr_info"),
            filters=input_data.get("filters", {}),
            hr_results=[],
            rules_results=[],
            reranked_results=[],
            relevance_scores={},
            sources=[],
            final_results={},
            execution_status="initializing"
        )

        # 워크플로우 컴파일 및 실행
        app = self.workflow.compile()

        try:
            # 타임아웃 설정 (5초)
            result = await asyncio.wait_for(
                app.ainvoke(initial_state),
                timeout=5.0
            )
            return result.get("final_results", {
                "status": "success",
                "data": {"results": [], "message": "No results found"}
            })
        except asyncio.TimeoutError:
            logger.error("SearchAgent execution timed out")
            return {
                "status": "error",
                "data": {"message": "Search timed out"},
                "error": "Timeout"
            }
        except Exception as e:
            logger.error(f"SearchAgent execution failed: {e}")
            return {
                "status": "error",
                "data": {"message": str(e)},
                "error": str(e)
            }

    async def analyze_search_query(self, state: SearchState) -> SearchState:
        """쿼리 분석 - 간단한 키워드 추출만"""
        state["execution_status"] = "analyzing"

        query = state.get("query", "")
        keywords = self._extract_keywords(query)

        state["filters"]["keywords"] = keywords
        state["sources"] = []

        logger.info(f"Query analyzed - Keywords: {keywords}")
        return state

    async def search_hr_information(self, state: SearchState) -> SearchState:
        """인사정보 검색 - 간단한 SQL 검색"""
        state["execution_status"] = "searching_hr_info"

        try:
            if not self.hr_info_path.exists():
                logger.warning(f"HR database not found: {self.hr_info_path}")
                state["hr_results"] = []
                return state

            conn = sqlite3.connect(str(self.hr_info_path))
            cursor = conn.cursor()

            # 간단한 검색 쿼리 (전체 데이터 제한적으로 가져오기)
            query = "SELECT * FROM 인사자료 LIMIT 10"

            try:
                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                hr_results = []
                for row in rows:
                    result = dict(zip(columns, row))
                    # 인코딩 안전한 문자열 변환
                    try:
                        content = str(result).encode('utf-8', errors='ignore').decode('utf-8')
                    except:
                        content = "Data encoding error"

                    hr_results.append({
                        "content": content[:200],  # 길이 제한
                        "type": "hr_info",
                        "relevance_score": 0.7  # 고정값
                    })

                state["hr_results"] = hr_results[:5]  # 최대 5개
                logger.info(f"Found {len(hr_results)} HR results")

            except Exception as e:
                logger.error(f"SQL execution error: {e}")
                state["hr_results"] = []

            conn.close()

        except Exception as e:
            logger.error(f"Error searching HR information: {e}")
            state["hr_results"] = []

        state["sources"].append("HR Database")
        return state

    async def format_final_response(self, state: SearchState) -> SearchState:
        """최종 응답 포맷팅"""
        state["execution_status"] = "formatting"

        all_results = state.get("hr_results", [])

        state["final_results"] = {
            "status": "success",
            "data": {
                "results": all_results,
                "total_results": len(all_results),
                "sources": state.get("sources", []),
                "search_type": state.get("search_type", "hr_info")
            },
            "message": f"Found {len(all_results)} results"
        }

        logger.info("Search completed and formatted")
        return state

    def _extract_keywords(self, query: str) -> List[str]:
        """간단한 키워드 추출"""
        if not query:
            return []

        stopwords = {"을", "를", "이", "가", "은", "는", "의", "에", "와", "과", "도", "로"}
        words = query.split()
        keywords = [w for w in words if w not in stopwords and len(w) > 1]
        return keywords