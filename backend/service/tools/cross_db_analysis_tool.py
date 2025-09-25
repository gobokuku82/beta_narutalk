"""
Cross-Database Analysis Tool
여러 DB를 통합하여 분석하는 도구
"""

import sqlite3
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import asyncio

from .calculation_tool import CalculationTool
from .trend_analysis_tool import TrendAnalysisTool

logger = logging.getLogger(__name__)


class CrossDBAnalysisTool:
    """Tool for analyzing data across multiple databases"""

    def __init__(self):
        """Initialize cross-database analysis tool"""
        self.logger = logger

        # Database paths - use absolute paths from project root
        base_path = Path(__file__).parent.parent.parent.parent  # backend/service/tools -> project root
        self.db_paths = {
            "performance": base_path / "database" / "storage" / "sales_performance" / "sales_performance_db.db",
            "target": base_path / "database" / "storage" / "sales_performance" / "sales_target_db.db",
            "clients": base_path / "database" / "storage" / "sales_performance" / "clients_db.db"
        }

        # Initialize calculation tools
        self.calc_tool = CalculationTool()
        self.trend_tool = TrendAnalysisTool()

        self.logger.info("CrossDBAnalysisTool initialized")

    # ============== Analysis Methods for Subgraphs ==============

    def compare_entities(
        self,
        data: Dict[str, Any],
        entity_type: str = "entity"
    ) -> Dict[str, Any]:
        """
        Compare entities across dimensions

        Args:
            data: Dictionary with entity names as keys and values
            entity_type: Type of entity (employee, product, region)

        Returns:
            Comparison results
        """
        if not data or len(data) < 2:
            return {"comparison": "insufficient_data"}

        # Sort entities by value
        sorted_entities = sorted(data.items(), key=lambda x: x[1], reverse=True)

        # Calculate statistics
        values = list(data.values())
        mean_val = sum(values) / len(values) if values else 0
        max_val = max(values) if values else 0
        min_val = min(values) if values else 0

        # Identify top and bottom performers
        top_performers = sorted_entities[:3]
        bottom_performers = sorted_entities[-3:] if len(sorted_entities) > 3 else []

        return {
            "entity_type": entity_type,
            "total_entities": len(data),
            "top_performers": top_performers,
            "bottom_performers": bottom_performers,
            "average_value": mean_val,
            "max_value": max_val,
            "min_value": min_val,
            "spread": max_val - min_val
        }

    def analyze_gap(
        self,
        actual_data: Dict[str, Any],
        target_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze gap between actual and target

        Args:
            actual_data: Actual performance data
            target_data: Target data

        Returns:
            Gap analysis results
        """
        gap_analysis = {
            "gaps": {},
            "overall_gap": 0,
            "overall_gap_percentage": 0
        }

        # Compare monthly totals if available
        if "monthly_totals" in actual_data and "monthly_targets" in target_data:
            actual_totals = actual_data["monthly_totals"]
            target_totals = target_data["monthly_targets"]

            total_actual = 0
            total_target = 0

            for month in target_totals:
                target = target_totals[month]
                actual = actual_totals.get(month, 0)

                gap = actual - target
                gap_pct = (gap / target * 100) if target != 0 else 0

                gap_analysis["gaps"][month] = {
                    "actual": actual,
                    "target": target,
                    "gap": gap,
                    "gap_percentage": gap_pct
                }

                total_actual += actual
                total_target += target

            # Calculate overall gap
            if total_target > 0:
                gap_analysis["overall_gap"] = total_actual - total_target
                gap_analysis["overall_gap_percentage"] = ((total_actual - total_target) / total_target) * 100

        return gap_analysis

    # ============== Database Query Methods ==============

    def _query_database(
        self,
        db_name: str,
        query: str,
        params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute query on specified database

        Args:
            db_name: Database name (performance, target, clients)
            query: SQL query
            params: Query parameters

        Returns:
            Query results as list of dictionaries
        """
        db_path = self.db_paths.get(db_name)
        if not db_path or not db_path.exists():
            self.logger.error(f"Database not found: {db_name}")
            return []

        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            results = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return results

        except Exception as e:
            self.logger.error(f"Database query error: {e}")
            return []

    async def _async_query_database(
        self,
        db_name: str,
        query: str,
        params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """Async wrapper for database query"""
        return await asyncio.to_thread(
            self._query_database, db_name, query, params
        )

    # ============== Performance Analysis ==============

    async def analyze_personal_performance(
        self,
        person_name: str,
        period: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze individual's comprehensive performance

        Args:
            person_name: Employee name
            period: Period to analyze (e.g., "202401" or "2024")

        Returns:
            Comprehensive performance analysis
        """
        self.logger.info(f"Analyzing performance for {person_name}")

        # Determine period columns
        if period:
            if len(period) == 4:  # Year
                year = period
                columns = [f"`{year}{month:02d}`" for month in range(1, 13)]
            elif len(period) == 6:  # Specific month
                columns = [f"`{period}`"]
            else:
                columns = ["*"]
        else:
            # Default to current year
            current_year = datetime.now().year
            columns = [f"`{current_year}{month:02d}`" for month in range(1, 13)]

        # 1. Get performance data
        perf_query = f"""
        SELECT 사번, 담당자, {', '.join(columns) if columns[0] != '*' else '*'}
        FROM sales_performance
        WHERE 담당자 = ?
        """

        performance_data = await self._async_query_database(
            "performance", perf_query, (person_name,)
        )

        if not performance_data:
            return {
                "status": "not_found",
                "message": f"{person_name}님의 실적 데이터를 찾을 수 없습니다"
            }

        # 2. Get target data
        target_query = f"""
        SELECT {', '.join(columns) if columns[0] != '*' else '*'}
        FROM 영업목표
        WHERE 담당자 = ?
        """

        target_data = await self._async_query_database(
            "target", target_query, (person_name,)
        )

        # 3. Aggregate performance by month
        monthly_performance = {}
        monthly_totals = []

        for row in performance_data:
            for col in columns:
                if col != "*":
                    col_name = col.strip("`")
                    if col_name in row and row[col_name] is not None:
                        if col_name not in monthly_performance:
                            monthly_performance[col_name] = 0
                        monthly_performance[col_name] += row[col_name]

        # 4. Calculate achievement rates
        achievement_rates = {}
        if target_data:
            target_row = target_data[0]
            for month, actual in monthly_performance.items():
                if month in target_row and target_row[month]:
                    rate = self.calc_tool.calculate_achievement_rate(
                        actual, target_row[month]
                    )
                    achievement_rates[month] = rate

        # 5. Calculate statistics
        values = list(monthly_performance.values())
        total_performance = self.calc_tool.calculate_sum(values)
        average_performance = self.calc_tool.calculate_average(values)

        # 6. Trend analysis
        trend_analysis = self.trend_tool.analyze_historical_trend(
            values, list(monthly_performance.keys())
        )

        # 7. Calculate growth rates
        growth_analysis = self.calc_tool.calculate_mom_growth(monthly_performance)

        # 8. Determine performance grade
        avg_achievement = (
            self.calc_tool.calculate_average(list(achievement_rates.values()))
            if achievement_rates else 0
        )
        grade = self.calc_tool.get_performance_grade(avg_achievement)

        return {
            "status": "success",
            "employee_name": person_name,
            "period": period or f"{datetime.now().year}",
            "performance_summary": {
                "total": self.calc_tool.format_currency(total_performance),
                "average": self.calc_tool.format_currency(average_performance),
                "grade": grade
            },
            "monthly_performance": monthly_performance,
            "achievement_rates": achievement_rates,
            "average_achievement": avg_achievement,
            "trend": trend_analysis,
            "growth": growth_analysis,
            "insights": self._generate_performance_insights(
                achievement_rates, trend_analysis, grade
            )
        }

    # ============== Client Analysis ==============

    async def analyze_client_details(
        self,
        client_id: Optional[str] = None,
        client_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze client details and sales history

        Args:
            client_id: Client ID
            client_name: Client name (alternative to ID)

        Returns:
            Client analysis results
        """
        if not client_id and not client_name:
            return {
                "status": "error",
                "message": "거래처 ID 또는 이름이 필요합니다"
            }

        # 1. Get client information
        if client_id:
            client_query = "SELECT * FROM 거래처자료 WHERE 거래처ID = ?"
            client_params = (client_id,)
        else:
            client_query = "SELECT * FROM 거래처자료 WHERE 병원 LIKE ?"
            client_params = (f"%{client_name}%",)

        client_data = await self._async_query_database(
            "clients", client_query, client_params
        )

        if not client_data:
            return {
                "status": "not_found",
                "message": "거래처 정보를 찾을 수 없습니다"
            }

        client_info = client_data[0]
        client_id = client_info.get("거래처ID")

        # 2. Get sales data for this client
        sales_query = """
        SELECT * FROM sales_performance
        WHERE 거래처ID = ?
        """

        sales_data = await self._async_query_database(
            "performance", sales_query, (client_id,)
        )

        # 3. Aggregate sales by month
        monthly_sales = {}
        product_sales = {}

        for row in sales_data:
            product = row.get("품목", "Unknown")

            # Aggregate by month
            for key, value in row.items():
                if key.startswith("20") and len(key) == 6:  # Month column
                    if value:
                        if key not in monthly_sales:
                            monthly_sales[key] = 0
                        monthly_sales[key] += value

                        # Track by product
                        if product not in product_sales:
                            product_sales[product] = {}
                        if key not in product_sales[product]:
                            product_sales[product][key] = 0
                        product_sales[product][key] += value

        # 4. Calculate statistics
        total_sales = self.calc_tool.calculate_sum(list(monthly_sales.values()))
        average_sales = self.calc_tool.calculate_average(list(monthly_sales.values()))

        # 5. Trend analysis
        if monthly_sales:
            trend = self.trend_tool.analyze_historical_trend(
                list(monthly_sales.values()),
                list(monthly_sales.keys())
            )
        else:
            trend = {"trend_direction": "no_data"}

        # 6. Top products
        top_products = []
        for product, sales in product_sales.items():
            total = self.calc_tool.calculate_sum(list(sales.values()))
            top_products.append({
                "product": product,
                "total_sales": total,
                "formatted": self.calc_tool.format_currency(total)
            })
        top_products.sort(key=lambda x: x["total_sales"], reverse=True)

        return {
            "status": "success",
            "client_info": {
                "id": client_info.get("거래처ID"),
                "name": client_info.get("병원"),
                "region": client_info.get("지역"),
                "visit_frequency": client_info.get("월방문횟수"),
                "patients": client_info.get("외래 환자"),
                "employees": client_info.get("담당자")
            },
            "sales_summary": {
                "total": self.calc_tool.format_currency(total_sales),
                "average": self.calc_tool.format_currency(average_sales),
                "transaction_count": len(sales_data)
            },
            "monthly_sales": monthly_sales,
            "trend": trend,
            "top_products": top_products[:5],
            "insights": self._generate_client_insights(
                client_info, monthly_sales, trend
            )
        }

    # ============== Team Achievement Analysis ==============

    async def calculate_team_achievement(
        self,
        team_name: Optional[str] = None,
        period: str = None
    ) -> Dict[str, Any]:
        """
        Calculate team achievement rates

        Args:
            team_name: Team name (if None, all teams)
            period: Period to analyze

        Returns:
            Team achievement analysis
        """
        # Get all employees' performance
        if team_name:
            # In a real scenario, you'd have team membership data
            # For now, we'll get all employees
            perf_query = "SELECT DISTINCT 담당자 FROM sales_performance"
        else:
            perf_query = "SELECT DISTINCT 담당자 FROM sales_performance"

        employees = await self._async_query_database("performance", perf_query)

        team_results = []
        total_actual = 0
        total_target = 0

        for emp_row in employees:
            employee = emp_row["담당자"]

            # Get individual performance
            emp_performance = await self.analyze_personal_performance(
                employee, period
            )

            if emp_performance["status"] == "success":
                team_results.append({
                    "employee": employee,
                    "total": emp_performance["performance_summary"]["total"],
                    "average_achievement": emp_performance["average_achievement"],
                    "grade": emp_performance["performance_summary"]["grade"]
                })

                # Sum up for team totals
                for month, value in emp_performance["monthly_performance"].items():
                    total_actual += value

        # Calculate team statistics
        if team_results:
            achievement_rates = [r["average_achievement"] for r in team_results]
            team_avg_achievement = self.calc_tool.calculate_average(achievement_rates)

            # Sort by achievement
            team_results.sort(
                key=lambda x: x["average_achievement"], reverse=True
            )

            return {
                "status": "success",
                "team_name": team_name or "전체",
                "period": period or str(datetime.now().year),
                "team_summary": {
                    "total_sales": self.calc_tool.format_currency(total_actual),
                    "average_achievement": round(team_avg_achievement, 2),
                    "member_count": len(team_results)
                },
                "top_performers": team_results[:5],
                "bottom_performers": team_results[-3:] if len(team_results) > 3 else [],
                "grade_distribution": self._calculate_grade_distribution(team_results),
                "insights": self._generate_team_insights(
                    team_avg_achievement, team_results
                )
            }

        return {
            "status": "no_data",
            "message": "팀 데이터를 찾을 수 없습니다"
        }

    # ============== Comparative Analysis ==============

    async def compare_performance(
        self,
        entity1: str,
        entity2: str,
        period: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare performance between two entities

        Args:
            entity1: First entity (employee or client)
            entity2: Second entity
            period: Period to compare

        Returns:
            Comparative analysis results
        """
        # Get performance for both entities
        perf1 = await self.analyze_personal_performance(entity1, period)
        perf2 = await self.analyze_personal_performance(entity2, period)

        if perf1["status"] != "success" or perf2["status"] != "success":
            return {
                "status": "error",
                "message": "비교할 데이터를 찾을 수 없습니다"
            }

        # Compare key metrics
        comparison = {
            "entity1": {
                "name": entity1,
                "total": perf1["performance_summary"]["total"],
                "average": perf1["performance_summary"]["average"],
                "achievement": perf1["average_achievement"],
                "grade": perf1["performance_summary"]["grade"],
                "trend": perf1["trend"]["trend_direction"]
            },
            "entity2": {
                "name": entity2,
                "total": perf2["performance_summary"]["total"],
                "average": perf2["performance_summary"]["average"],
                "achievement": perf2["average_achievement"],
                "grade": perf2["performance_summary"]["grade"],
                "trend": perf2["trend"]["trend_direction"]
            }
        }

        # Calculate differences
        if perf1["monthly_performance"] and perf2["monthly_performance"]:
            monthly_diff = {}
            for month in perf1["monthly_performance"]:
                if month in perf2["monthly_performance"]:
                    diff = perf1["monthly_performance"][month] - perf2["monthly_performance"][month]
                    monthly_diff[month] = {
                        "difference": diff,
                        "percentage": self.calc_tool.calculate_percentage_change(
                            perf2["monthly_performance"][month],
                            perf1["monthly_performance"][month]
                        ) if perf2["monthly_performance"][month] else 0
                    }

            comparison["monthly_differences"] = monthly_diff

        # Determine winner
        if perf1["average_achievement"] > perf2["average_achievement"]:
            comparison["winner"] = entity1
            comparison["summary"] = f"{entity1}이(가) {entity2}보다 우수한 성과를 보였습니다"
        else:
            comparison["winner"] = entity2
            comparison["summary"] = f"{entity2}이(가) {entity1}보다 우수한 성과를 보였습니다"

        return {
            "status": "success",
            "comparison": comparison,
            "period": period or str(datetime.now().year)
        }

    # ============== Helper Methods ==============

    def _generate_performance_insights(
        self,
        achievement_rates: Dict[str, float],
        trend: Dict[str, Any],
        grade: str
    ) -> List[str]:
        """Generate performance insights"""
        insights = []

        # Achievement insight
        if achievement_rates:
            avg_achievement = self.calc_tool.calculate_average(
                list(achievement_rates.values())
            )
            if avg_achievement >= 100:
                insights.append(f"목표를 {avg_achievement-100:.1f}% 초과 달성했습니다")
            else:
                insights.append(f"목표 달성률이 {avg_achievement:.1f}%입니다")

        # Trend insight
        if trend.get("trend_direction") == "increasing":
            insights.append("실적이 상승 추세를 보이고 있습니다")
        elif trend.get("trend_direction") == "decreasing":
            insights.append("실적이 하락 추세를 보여 개선이 필요합니다")

        # Grade insight
        if grade in ["S", "A"]:
            insights.append("매우 우수한 성과를 보이고 있습니다")
        elif grade in ["D", "F"]:
            insights.append("성과 개선을 위한 전략 수립이 필요합니다")

        return insights

    def _generate_client_insights(
        self,
        client_info: Dict[str, Any],
        monthly_sales: Dict[str, float],
        trend: Dict[str, Any]
    ) -> List[str]:
        """Generate client insights"""
        insights = []

        # Visit frequency insight
        visit_freq = client_info.get("월방문횟수", 0)
        if visit_freq > 10:
            insights.append("방문 빈도가 높은 주요 거래처입니다")
        elif visit_freq < 3:
            insights.append("방문 빈도를 늘려 관계 강화가 필요합니다")

        # Sales trend insight
        if trend.get("trend_direction") == "increasing":
            insights.append("매출이 증가 추세에 있는 유망 거래처입니다")
        elif trend.get("trend_direction") == "decreasing":
            insights.append("매출 감소 원인 파악이 필요합니다")

        # Patient volume insight
        patients = client_info.get("외래 환자", 0)
        if patients > 1000:
            insights.append("환자 수가 많은 대형 병원입니다")

        return insights

    def _generate_team_insights(
        self,
        avg_achievement: float,
        team_results: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate team insights"""
        insights = []

        # Team achievement insight
        if avg_achievement >= 100:
            insights.append(f"팀 전체가 목표를 달성했습니다 ({avg_achievement:.1f}%)")
        else:
            insights.append(f"팀 목표 달성률이 {avg_achievement:.1f}%로 개선이 필요합니다")

        # Performance distribution insight
        high_performers = sum(1 for r in team_results if r["grade"] in ["S", "A"])
        low_performers = sum(1 for r in team_results if r["grade"] in ["D", "F"])

        if high_performers > len(team_results) * 0.5:
            insights.append("팀원 과반수가 우수한 성과를 보이고 있습니다")
        if low_performers > len(team_results) * 0.3:
            insights.append("저성과자 관리 및 교육이 필요합니다")

        return insights

    def _calculate_grade_distribution(
        self,
        team_results: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate grade distribution"""
        distribution = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0, "F": 0}

        for result in team_results:
            grade = result.get("grade", "F")
            if grade in distribution:
                distribution[grade] += 1

        return distribution


# Singleton instance
_cross_db_tool_instance = None


def get_cross_db_analysis_tool() -> CrossDBAnalysisTool:
    """Get singleton instance of CrossDBAnalysisTool"""
    global _cross_db_tool_instance
    if _cross_db_tool_instance is None:
        _cross_db_tool_instance = CrossDBAnalysisTool()
    return _cross_db_tool_instance