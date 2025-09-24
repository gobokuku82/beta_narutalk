"""
Calculation Tool for Sales Analytics
기본 계산 및 비즈니스 메트릭 계산 도구
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


class CalculationTool:
    """Sales data calculation utilities"""

    def __init__(self):
        """Initialize calculation tool"""
        self.logger = logger
        self.logger.info("CalculationTool initialized")

    # ============== Basic Arithmetic ==============

    def calculate_sum(self, values: List[Union[int, float]]) -> float:
        """
        Calculate sum of values

        Args:
            values: List of numeric values

        Returns:
            Sum of values
        """
        if not values:
            return 0.0

        # Filter out None values
        clean_values = [v for v in values if v is not None]
        return float(sum(clean_values))

    def calculate_average(self, values: List[Union[int, float]]) -> float:
        """
        Calculate average of values

        Args:
            values: List of numeric values

        Returns:
            Average of values
        """
        if not values:
            return 0.0

        clean_values = [v for v in values if v is not None]
        if not clean_values:
            return 0.0

        return float(sum(clean_values) / len(clean_values))

    def calculate_min_max(self, values: List[Union[int, float]]) -> Dict[str, float]:
        """
        Calculate minimum and maximum values

        Args:
            values: List of numeric values

        Returns:
            Dictionary with min and max values
        """
        if not values:
            return {"min": 0.0, "max": 0.0}

        clean_values = [v for v in values if v is not None]
        if not clean_values:
            return {"min": 0.0, "max": 0.0}

        return {
            "min": float(min(clean_values)),
            "max": float(max(clean_values))
        }

    def calculate_median(self, values: List[Union[int, float]]) -> float:
        """
        Calculate median of values

        Args:
            values: List of numeric values

        Returns:
            Median value
        """
        if not values:
            return 0.0

        clean_values = sorted([v for v in values if v is not None])
        if not clean_values:
            return 0.0

        n = len(clean_values)
        if n % 2 == 0:
            return float((clean_values[n//2-1] + clean_values[n//2]) / 2)
        else:
            return float(clean_values[n//2])

    # ============== Business Metrics ==============

    def calculate_achievement_rate(
        self,
        actual: Union[int, float],
        target: Union[int, float]
    ) -> float:
        """
        Calculate achievement rate (달성률)

        Args:
            actual: Actual performance value
            target: Target value

        Returns:
            Achievement rate as percentage
        """
        if target == 0 or target is None:
            return 0.0

        if actual is None:
            actual = 0

        rate = (actual / target) * 100
        return round(rate, 2)

    def calculate_growth_rate(
        self,
        current: Union[int, float],
        previous: Union[int, float]
    ) -> float:
        """
        Calculate growth rate (성장률)

        Args:
            current: Current period value
            previous: Previous period value

        Returns:
            Growth rate as percentage
        """
        if previous == 0 or previous is None:
            if current and current > 0:
                return 100.0  # 100% growth from 0
            return 0.0

        if current is None:
            current = 0

        growth = ((current - previous) / previous) * 100
        return round(growth, 2)

    def calculate_percentage_change(
        self,
        old_value: Union[int, float],
        new_value: Union[int, float]
    ) -> float:
        """
        Calculate percentage change between two values

        Args:
            old_value: Original value
            new_value: New value

        Returns:
            Percentage change
        """
        return self.calculate_growth_rate(new_value, old_value)

    def calculate_market_share(
        self,
        individual: Union[int, float],
        total: Union[int, float]
    ) -> float:
        """
        Calculate market share or contribution percentage

        Args:
            individual: Individual's value
            total: Total market/team value

        Returns:
            Market share as percentage
        """
        if total == 0 or total is None:
            return 0.0

        if individual is None:
            individual = 0

        share = (individual / total) * 100
        return round(share, 2)

    # ============== Period Calculations ==============

    def calculate_yoy_growth(
        self,
        current_year_data: Dict[str, float],
        previous_year_data: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculate Year-over-Year growth

        Args:
            current_year_data: Current year monthly data (e.g., {"202401": 100, "202402": 150})
            previous_year_data: Previous year monthly data (e.g., {"202301": 80, "202302": 120})

        Returns:
            YoY growth analysis
        """
        result = {
            "monthly_growth": {},
            "total_growth": 0.0,
            "average_growth": 0.0
        }

        # Calculate monthly YoY growth
        growth_rates = []
        for month in range(1, 13):
            current_month_key = f"{datetime.now().year}{month:02d}"
            previous_month_key = f"{datetime.now().year - 1}{month:02d}"

            if current_month_key in current_year_data and previous_month_key in previous_year_data:
                current_val = current_year_data.get(current_month_key, 0)
                previous_val = previous_year_data.get(previous_month_key, 0)

                growth = self.calculate_growth_rate(current_val, previous_val)
                result["monthly_growth"][f"{month:02d}"] = growth
                growth_rates.append(growth)

        # Calculate total YoY growth
        current_total = sum(current_year_data.values())
        previous_total = sum(previous_year_data.values())
        result["total_growth"] = self.calculate_growth_rate(current_total, previous_total)

        # Calculate average growth
        if growth_rates:
            result["average_growth"] = round(sum(growth_rates) / len(growth_rates), 2)

        return result

    def calculate_mom_growth(
        self,
        monthly_data: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculate Month-over-Month growth

        Args:
            monthly_data: Monthly data (e.g., {"202401": 100, "202402": 150})

        Returns:
            MoM growth analysis
        """
        result = {
            "monthly_growth": {},
            "average_growth": 0.0,
            "trend": "stable"
        }

        # Sort months chronologically
        sorted_months = sorted(monthly_data.keys())

        if len(sorted_months) < 2:
            return result

        growth_rates = []
        for i in range(1, len(sorted_months)):
            prev_month = sorted_months[i-1]
            curr_month = sorted_months[i]

            growth = self.calculate_growth_rate(
                monthly_data[curr_month],
                monthly_data[prev_month]
            )

            result["monthly_growth"][curr_month] = growth
            growth_rates.append(growth)

        # Calculate average MoM growth
        if growth_rates:
            result["average_growth"] = round(sum(growth_rates) / len(growth_rates), 2)

            # Determine trend
            if result["average_growth"] > 5:
                result["trend"] = "increasing"
            elif result["average_growth"] < -5:
                result["trend"] = "decreasing"
            else:
                result["trend"] = "stable"

        return result

    # ============== Statistical Calculations ==============

    def calculate_variance(self, values: List[Union[int, float]]) -> float:
        """
        Calculate variance of values

        Args:
            values: List of numeric values

        Returns:
            Variance
        """
        if not values or len(values) < 2:
            return 0.0

        clean_values = [v for v in values if v is not None]
        if len(clean_values) < 2:
            return 0.0

        mean = self.calculate_average(clean_values)
        variance = sum((x - mean) ** 2 for x in clean_values) / len(clean_values)
        return round(variance, 2)

    def calculate_standard_deviation(self, values: List[Union[int, float]]) -> float:
        """
        Calculate standard deviation

        Args:
            values: List of numeric values

        Returns:
            Standard deviation
        """
        variance = self.calculate_variance(values)
        return round(variance ** 0.5, 2)

    def calculate_percentile(
        self,
        values: List[Union[int, float]],
        percentile: int
    ) -> float:
        """
        Calculate percentile value

        Args:
            values: List of numeric values
            percentile: Percentile to calculate (0-100)

        Returns:
            Value at the given percentile
        """
        if not values:
            return 0.0

        clean_values = sorted([v for v in values if v is not None])
        if not clean_values:
            return 0.0

        index = (len(clean_values) - 1) * percentile / 100
        lower = int(index)
        upper = lower + 1

        if upper >= len(clean_values):
            return float(clean_values[lower])

        weight = index - lower
        return float(clean_values[lower] * (1 - weight) + clean_values[upper] * weight)

    # ============== Utility Methods ==============

    def format_currency(self, value: Union[int, float]) -> str:
        """
        Format value as Korean currency

        Args:
            value: Numeric value

        Returns:
            Formatted currency string
        """
        if value is None:
            return "0원"

        if value >= 100000000:  # 1억 이상
            return f"{value/100000000:,.1f}억원"
        elif value >= 10000:  # 1만 이상
            return f"{value/10000:,.0f}만원"
        else:
            return f"{value:,.0f}원"

    def format_percentage(self, value: float) -> str:
        """
        Format value as percentage

        Args:
            value: Percentage value

        Returns:
            Formatted percentage string
        """
        if value is None:
            return "0.0%"

        return f"{value:,.1f}%"

    def get_performance_grade(self, achievement_rate: float) -> str:
        """
        Get performance grade based on achievement rate

        Args:
            achievement_rate: Achievement rate percentage

        Returns:
            Performance grade (S, A, B, C, D, F)
        """
        if achievement_rate >= 120:
            return "S"
        elif achievement_rate >= 100:
            return "A"
        elif achievement_rate >= 80:
            return "B"
        elif achievement_rate >= 60:
            return "C"
        elif achievement_rate >= 40:
            return "D"
        else:
            return "F"


# Singleton instance
_calculation_tool_instance = None


def get_calculation_tool() -> CalculationTool:
    """Get singleton instance of CalculationTool"""
    global _calculation_tool_instance
    if _calculation_tool_instance is None:
        _calculation_tool_instance = CalculationTool()
    return _calculation_tool_instance