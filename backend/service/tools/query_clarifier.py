"""
Query Clarifier for handling ambiguous queries
Provides clarification requests instead of making assumptions
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class QueryClarifier:
    """Handle ambiguous queries by requesting clarification from users"""

    def __init__(self):
        self.current_date = datetime.now()
        self.current_year = self.current_date.year
        self.current_month = self.current_date.month

        # Define ambiguous time expressions
        self.ambiguous_time_expressions = {
            "어제": "daily",
            "오늘": "daily",
            "내일": "daily",
            "최근": "vague",
            "요즘": "vague",
            "얼마전": "vague",
            "예전": "vague"
        }

    def check_ambiguity(self, query: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if query contains ambiguous elements that need clarification

        Args:
            query: Original user query
            entities: Extracted entities from query

        Returns:
            Dictionary with clarification status and suggestions
        """
        result = {
            "needs_clarification": False,
            "clarification_type": None,
            "message": None,
            "suggestions": [],
            "alternative_query": None
        }

        # Check for ambiguous time expressions
        time_expr = entities.get("time_expression")
        if time_expr:
            clarification = self._handle_time_ambiguity(time_expr)
            if clarification:
                return clarification

        # Check for vague expressions in the original query
        for expr, expr_type in self.ambiguous_time_expressions.items():
            if expr in query:
                return self._create_clarification_response(expr, expr_type)

        # Check for incomplete information
        if entities.get("action_type") == "sales" and not any([
            entities.get("person_name"),
            entities.get("month"),
            entities.get("year"),
            entities.get("team")
        ]):
            result["needs_clarification"] = True
            result["clarification_type"] = "scope"
            result["message"] = "조회 범위를 명확히 지정해주세요."
            result["suggestions"] = [
                "특정 직원 실적 (예: 최수아의 실적)",
                "특정 월 실적 (예: 2024년 3월 실적)",
                "전체 실적 순위 (예: 이번달 실적 TOP 10)"
            ]
            return result

        return result

    def _handle_time_ambiguity(self, time_expression: str) -> Optional[Dict[str, Any]]:
        """
        Handle ambiguous time expressions

        Args:
            time_expression: Time expression to handle

        Returns:
            Clarification response if needed
        """
        expr_type = self.ambiguous_time_expressions.get(time_expression)
        if expr_type:
            return self._create_clarification_response(time_expression, expr_type)

        return None

    def _create_clarification_response(self, expression: str, expr_type: str) -> Dict[str, Any]:
        """
        Create clarification response for ambiguous expressions

        Args:
            expression: The ambiguous expression
            expr_type: Type of ambiguity

        Returns:
            Clarification response dictionary
        """
        response = {
            "needs_clarification": True,
            "clarification_type": expr_type,
            "message": None,
            "suggestions": [],
            "alternative_query": None
        }

        if expr_type == "daily":
            response["message"] = f"'{expression}'은 일별 데이터를 의미하지만, 시스템은 월 단위 데이터만 제공합니다."
            response["suggestions"] = [
                f"{self.current_year}년 {self.current_month}월 (이번달)",
                f"{self.current_year}년 {self.current_month - 1 if self.current_month > 1 else 12}월 (지난달)",
                f"최근 3개월 추이"
            ]

        elif expr_type == "vague":
            response["message"] = f"'{expression}'의 정확한 기간을 지정해주세요."
            response["suggestions"] = [
                "최근 3개월",
                "최근 6개월",
                f"{self.current_year}년",
                f"{self.current_year}년 상반기",
                f"{self.current_year}년 하반기"
            ]

        return response

    def suggest_alternatives(self, query: str, error: str) -> Dict[str, Any]:
        """
        Suggest alternatives when query fails

        Args:
            query: Original query
            error: Error message from execution

        Returns:
            Suggestions for alternative queries
        """
        suggestions = {
            "original_query": query,
            "error": error,
            "suggestions": [],
            "tips": []
        }

        # Handle non-existent person
        if "해당 직원" in error or (not error and "조회 결과가 없습니다" in error):
            suggestions["suggestions"] = [
                "실제 직원명으로 다시 조회 (예: 최수아, 윤하은)",
                "전체 직원 목록 확인",
                "팀 단위 조회"
            ]
            suggestions["tips"].append("직원명은 정확한 실명을 사용해주세요")

        # Handle column errors
        elif "no such column" in error:
            if "2025" in error or "2026" in error:
                suggestions["suggestions"] = [
                    "2024년 11월까지의 데이터 조회",
                    "2024년 데이터 조회",
                    "가용한 최신 월 조회"
                ]
                suggestions["tips"].append("데이터는 2022년 12월부터 2024년 11월까지 제공됩니다")

        # Handle table errors
        elif "no such table" in error:
            suggestions["suggestions"] = [
                "sales_performance 테이블 직접 조회",
                "단순 집계 쿼리로 재시도"
            ]
            suggestions["tips"].append("일부 테이블은 JOIN이 지원되지 않을 수 있습니다")

        return suggestions

    def format_clarification_message(self, clarification: Dict[str, Any]) -> str:
        """
        Format clarification response for user display

        Args:
            clarification: Clarification dictionary

        Returns:
            Formatted message string
        """
        if not clarification.get("needs_clarification"):
            return ""

        lines = []
        lines.append("\n⚠️ 명확한 정보가 필요합니다")
        lines.append("=" * 50)

        if clarification.get("message"):
            lines.append(f"\n📝 {clarification['message']}")

        if clarification.get("suggestions"):
            lines.append("\n💡 다음과 같이 시도해보세요:")
            for i, suggestion in enumerate(clarification["suggestions"], 1):
                lines.append(f"  {i}. {suggestion}")

        if clarification.get("alternative_query"):
            lines.append(f"\n🔄 또는 이렇게 입력하세요: {clarification['alternative_query']}")

        lines.append("=" * 50)

        return "\n".join(lines)