"""
Search Agent - HR information and rules search
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
import sqlite3
import asyncio
from pathlib import Path
import logging

from ..core.base_agent import BaseAgent
from ..core.states import SearchState
from ..core.config import Config


logger = logging.getLogger(__name__)


class SearchAgent(BaseAgent):
    """Agent for searching HR information and rules"""

    def __init__(self):
        super().__init__("search_agent")
        self.hr_db_path = Config.get_database_path("hr_info")
        self.rules_db_path = Config.get_database_path("hr_rules")

    def _build_graph(self):
        """Build the search workflow"""
        self.workflow = StateGraph(SearchState)

        # Add nodes
        self.workflow.add_node("analyze_query", self.analyze_query)
        self.workflow.add_node("search_hr_info", self.search_hr_info)
        self.workflow.add_node("search_rules", self.search_rules)
        self.workflow.add_node("merge_results", self.merge_results)

        # Add edges
        self.workflow.add_edge(START, "analyze_query")

        # Conditional routing based on search type
        self.workflow.add_conditional_edges(
            "analyze_query",
            self.determine_search_type,
            {
                "hr_only": "search_hr_info",
                "rules_only": "search_rules",
                "both": "search_hr_info"
            }
        )

        # After HR search
        self.workflow.add_conditional_edges(
            "search_hr_info",
            lambda state: "search_rules" if state.get("search_type") == "both" else "merge_results",
            {
                "search_rules": "search_rules",
                "merge_results": "merge_results"
            }
        )

        self.workflow.add_edge("search_rules", "merge_results")
        self.workflow.add_edge("merge_results", END)

    async def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        required_fields = ["query"]
        for field in required_fields:
            if field not in input_data:
                self.logger.error(f"Missing required field: {field}")
                return False
        return True

    async def analyze_query(self, state: SearchState) -> SearchState:
        """Analyze the search query"""
        try:
            query = state.get("query", "")
            state["status"] = "processing"

            # Extract keywords
            keywords = self._extract_keywords(query)
            state["keywords"] = keywords

            # Determine search type
            if "규정" in query or "정책" in query or "지침" in query:
                if "인사" in query or "직원" in query:
                    state["search_type"] = "both"
                else:
                    state["search_type"] = "rules_only"
            else:
                state["search_type"] = "hr_only"

            self.logger.info(f"Query analyzed - Type: {state['search_type']}, Keywords: {keywords}")
            return state

        except Exception as e:
            self.logger.error(f"Error analyzing query: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]
            state["status"] = "failed"
            return state

    def determine_search_type(self, state: SearchState) -> str:
        """Determine which search to perform"""
        search_type = state.get("search_type", "hr_only")
        if search_type == "both":
            return "both"
        elif search_type == "rules_only":
            return "rules_only"
        return "hr_only"

    async def search_hr_info(self, state: SearchState) -> SearchState:
        """Search HR information database"""
        try:
            state["hr_results"] = []

            if not self.hr_db_path.exists():
                self.logger.warning(f"HR database not found: {self.hr_db_path}")
                return state

            conn = sqlite3.connect(str(self.hr_db_path))
            cursor = conn.cursor()

            # Build search query
            keywords = state.get("keywords", [])
            query = state.get("query", "")

            # Simple keyword search
            sql = "SELECT * FROM 인사자료 WHERE 1=1"
            params = []

            if keywords:
                conditions = []
                for keyword in keywords[:3]:  # Limit keywords
                    conditions.append("(성명 LIKE ? OR 부서 LIKE ? OR 직급 LIKE ?)")
                    params.extend([f"%{keyword}%"] * 3)

                if conditions:
                    sql += " AND (" + " OR ".join(conditions) + ")"

            sql += " LIMIT 20"

            cursor.execute(sql, params)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            hr_results = []
            for row in rows:
                result = dict(zip(columns, row))
                hr_results.append({
                    "type": "hr_info",
                    "content": result,
                    "relevance_score": 0.7  # Simple fixed score
                })

            state["hr_results"] = hr_results
            state["sources"] = state.get("sources", []) + ["HR Database"]

            conn.close()
            self.logger.info(f"Found {len(hr_results)} HR results")

        except Exception as e:
            self.logger.error(f"Error searching HR info: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]

        return state

    async def search_rules(self, state: SearchState) -> SearchState:
        """Search rules database (keyword-based for now)"""
        try:
            state["rules_results"] = []

            # For now, return mock results
            # TODO: Implement ChromaDB keyword search later
            keywords = state.get("keywords", [])

            if keywords:
                mock_rules = [
                    {
                        "type": "rule",
                        "content": {
                            "title": "인사 규정",
                            "description": "직원 채용 및 평가 관련 규정",
                            "text": "채용 프로세스 및 평가 기준..."
                        },
                        "relevance_score": 0.6
                    }
                ]
                state["rules_results"] = mock_rules
                state["sources"] = state.get("sources", []) + ["Rules Database"]

            self.logger.info(f"Found {len(state.get('rules_results', []))} rule results")

        except Exception as e:
            self.logger.error(f"Error searching rules: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]

        return state

    async def merge_results(self, state: SearchState) -> SearchState:
        """Merge and format final results"""
        try:
            hr_results = state.get("hr_results", [])
            rules_results = state.get("rules_results", [])

            all_results = hr_results + rules_results

            # Sort by relevance score
            all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

            state["final_results"] = {
                "status": "success",
                "query": state.get("query", ""),
                "total_results": len(all_results),
                "results": all_results[:10],  # Top 10 results
                "sources": list(set(state.get("sources", [])))
            }

            state["status"] = "completed"
            self.logger.info(f"Search completed with {len(all_results)} total results")

        except Exception as e:
            self.logger.error(f"Error merging results: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]
            state["status"] = "failed"
            state["final_results"] = {
                "status": "error",
                "error": str(e)
            }

        return state

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query"""
        if not query:
            return []

        # Simple Korean stopword removal
        stopwords = {"을", "를", "이", "가", "은", "는", "의", "에", "와", "과", "도", "로", "에서", "으로"}
        words = query.split()
        keywords = [w for w in words if w not in stopwords and len(w) > 1]

        return keywords[:5]  # Limit to 5 keywords