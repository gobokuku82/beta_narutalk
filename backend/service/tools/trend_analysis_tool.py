"""
Trend Analysis Tool for Sales Analytics
트렌드 분석 및 예측 도구
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
import warnings

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')  # Suppress numpy warnings


class TrendAnalysisTool:
    """Sales trend analysis and prediction utilities"""

    def __init__(self):
        """Initialize trend analysis tool"""
        self.logger = logger
        self.logger.info("TrendAnalysisTool initialized")

    # ============== Historical Trend Analysis ==============

    def analyze_trend(
        self,
        values: List[float]
    ) -> Dict[str, Any]:
        """
        Analyze trend from values (simplified interface for subgraphs)

        Args:
            values: List of numeric values

        Returns:
            Trend analysis dictionary
        """
        if not values or len(values) < 2:
            return {"trend_type": "insufficient_data"}

        # Calculate trend using linear regression
        x = np.arange(len(values))
        y = np.array(values)

        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        # Determine trend type
        if slope > 0.01:
            trend_type = "increasing"
        elif slope < -0.01:
            trend_type = "decreasing"
        else:
            trend_type = "stable"

        return {
            "trend_type": trend_type,
            "slope": float(slope),
            "r_squared": float(r_value ** 2)
        }

    def calculate_moving_average(
        self,
        values: List[float],
        window: int = 3
    ) -> List[float]:
        """
        Calculate moving average

        Args:
            values: List of values
            window: Window size for moving average

        Returns:
            List of moving averages
        """
        if len(values) < window:
            return values

        moving_avg = []
        for i in range(len(values) - window + 1):
            avg = sum(values[i:i+window]) / window
            moving_avg.append(avg)

        return moving_avg

    def calculate_growth_rates(
        self,
        values: List[float]
    ) -> List[float]:
        """
        Calculate period-over-period growth rates

        Args:
            values: List of values

        Returns:
            List of growth rates (as percentages)
        """
        if len(values) < 2:
            return []

        growth_rates = []
        for i in range(1, len(values)):
            if values[i-1] != 0:
                rate = ((values[i] - values[i-1]) / values[i-1]) * 100
                growth_rates.append(rate)
            else:
                growth_rates.append(0)

        return growth_rates

    def detect_seasonality(
        self,
        values: List[float]
    ) -> bool:
        """
        Simple seasonality detection

        Args:
            values: List of values

        Returns:
            True if seasonality detected
        """
        if len(values) < 12:  # Need at least 12 months
            return False

        # Simple check: compare quarters or months
        # This is a simplified version
        return len(values) >= 12

    def calculate_volatility(
        self,
        values: List[float]
    ) -> float:
        """
        Calculate volatility (coefficient of variation)

        Args:
            values: List of values

        Returns:
            Volatility percentage
        """
        if not values:
            return 0

        mean_val = np.mean(values)
        std_val = np.std(values)

        if mean_val != 0:
            return (std_val / mean_val) * 100
        return 0

    def analyze_historical_trend(
        self,
        data: List[float],
        period_labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze historical trend from time series data

        Args:
            data: List of values over time
            period_labels: Optional labels for each period

        Returns:
            Trend analysis results
        """
        if not data or len(data) < 2:
            return {
                "trend_direction": "insufficient_data",
                "trend_strength": 0.0,
                "volatility": 0.0,
                "summary": "데이터가 부족합니다"
            }

        # Clean data
        clean_data = [float(v) if v is not None else 0 for v in data]

        # Calculate trend using linear regression
        x = np.arange(len(clean_data))
        y = np.array(clean_data)

        # Perform linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        # Determine trend direction
        if slope > 0.01:
            trend_direction = "increasing"
            trend_desc = "상승"
        elif slope < -0.01:
            trend_direction = "decreasing"
            trend_desc = "하락"
        else:
            trend_direction = "stable"
            trend_desc = "안정"

        # Calculate volatility (coefficient of variation)
        mean_val = np.mean(clean_data)
        std_val = np.std(clean_data)
        volatility = (std_val / mean_val * 100) if mean_val != 0 else 0

        # Find peak and trough
        peak_index = np.argmax(clean_data)
        trough_index = np.argmin(clean_data)

        result = {
            "trend_direction": trend_direction,
            "trend_strength": abs(r_value),  # R-squared value
            "slope": round(slope, 2),
            "volatility": round(volatility, 2),
            "peak": {
                "value": clean_data[peak_index],
                "period": period_labels[peak_index] if period_labels else peak_index
            },
            "trough": {
                "value": clean_data[trough_index],
                "period": period_labels[trough_index] if period_labels else trough_index
            },
            "summary": f"트렌드: {trend_desc} (강도: {abs(r_value)*100:.1f}%)"
        }

        return result

    def calculate_moving_average(
        self,
        data: List[float],
        window: int = 3
    ) -> List[float]:
        """
        Calculate moving average

        Args:
            data: List of values
            window: Window size for moving average

        Returns:
            List of moving average values
        """
        if not data or len(data) < window:
            return data if data else []

        clean_data = [float(v) if v is not None else 0 for v in data]
        moving_avg = []

        for i in range(len(clean_data)):
            if i < window - 1:
                # Not enough data for full window
                moving_avg.append(clean_data[i])
            else:
                # Calculate average of window
                window_data = clean_data[i - window + 1:i + 1]
                moving_avg.append(sum(window_data) / window)

        return [round(v, 2) for v in moving_avg]

    def detect_seasonality(
        self,
        monthly_data: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Detect seasonal patterns in monthly data

        Args:
            monthly_data: Dictionary of month -> value

        Returns:
            Seasonality analysis results
        """
        if len(monthly_data) < 12:
            return {
                "has_seasonality": False,
                "seasonal_pattern": {},
                "peak_season": None,
                "low_season": None,
                "summary": "계절성 분석을 위한 데이터가 부족합니다 (최소 12개월 필요)"
            }

        # Group by month across years
        monthly_aggregates = {}
        for period, value in monthly_data.items():
            if len(period) >= 6:  # Format: YYYYMM
                month = period[-2:]  # Extract month
                if month not in monthly_aggregates:
                    monthly_aggregates[month] = []
                monthly_aggregates[month].append(value if value is not None else 0)

        # Calculate average for each month
        seasonal_pattern = {}
        for month, values in monthly_aggregates.items():
            seasonal_pattern[month] = sum(values) / len(values)

        # Find peak and low seasons
        if seasonal_pattern:
            peak_month = max(seasonal_pattern, key=seasonal_pattern.get)
            low_month = min(seasonal_pattern, key=seasonal_pattern.get)

            # Calculate seasonality strength
            values = list(seasonal_pattern.values())
            seasonality_strength = (max(values) - min(values)) / (sum(values) / len(values)) * 100

            return {
                "has_seasonality": seasonality_strength > 20,
                "seasonal_pattern": seasonal_pattern,
                "peak_season": f"{peak_month}월",
                "low_season": f"{low_month}월",
                "seasonality_strength": round(seasonality_strength, 2),
                "summary": f"성수기: {peak_month}월, 비수기: {low_month}월 (계절성 강도: {seasonality_strength:.1f}%)"
            }

        return {
            "has_seasonality": False,
            "seasonal_pattern": {},
            "peak_season": None,
            "low_season": None,
            "summary": "계절성 패턴을 찾을 수 없습니다"
        }

    # ============== Future Prediction ==============

    def predict_future_trend(
        self,
        historical_data: List[float],
        periods_ahead: int = 3
    ) -> Dict[str, Any]:
        """
        Predict future values based on historical trend

        Args:
            historical_data: Historical values
            periods_ahead: Number of periods to predict

        Returns:
            Prediction results
        """
        if not historical_data or len(historical_data) < 3:
            return {
                "predictions": [],
                "confidence_interval": [],
                "method": "insufficient_data",
                "summary": "예측을 위한 데이터가 부족합니다"
            }

        # Clean data
        clean_data = [float(v) if v is not None else 0 for v in historical_data]

        # Use linear regression for prediction
        x = np.arange(len(clean_data))
        y = np.array(clean_data)

        # Fit linear model
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        # Make predictions
        predictions = []
        confidence_intervals = []

        for i in range(1, periods_ahead + 1):
            future_x = len(clean_data) + i - 1
            predicted_y = slope * future_x + intercept

            # Calculate confidence interval (95%)
            confidence_margin = 1.96 * std_err * np.sqrt(1 + 1/len(clean_data) +
                                                          (future_x - np.mean(x))**2 / np.var(x))

            predictions.append(round(predicted_y, 2))
            confidence_intervals.append({
                "lower": round(predicted_y - confidence_margin, 2),
                "upper": round(predicted_y + confidence_margin, 2)
            })

        # Determine prediction quality
        if abs(r_value) > 0.7:
            quality = "높음"
        elif abs(r_value) > 0.4:
            quality = "보통"
        else:
            quality = "낮음"

        return {
            "predictions": predictions,
            "confidence_intervals": confidence_intervals,
            "method": "linear_regression",
            "prediction_quality": quality,
            "r_squared": round(r_value ** 2, 3),
            "summary": f"예측 신뢰도: {quality} (R²: {r_value**2:.3f})"
        }

    def predict_with_seasonality(
        self,
        monthly_data: Dict[str, float],
        months_ahead: int = 3
    ) -> Dict[str, Any]:
        """
        Predict future values considering seasonal patterns

        Args:
            monthly_data: Historical monthly data
            months_ahead: Number of months to predict

        Returns:
            Seasonal prediction results
        """
        if len(monthly_data) < 12:
            # Fall back to simple prediction
            values = list(monthly_data.values())
            return self.predict_future_trend(values, months_ahead)

        # Detect seasonality
        seasonality = self.detect_seasonality(monthly_data)

        # Extract trend and seasonal components
        sorted_months = sorted(monthly_data.keys())
        values = [monthly_data[m] for m in sorted_months]

        # Calculate trend
        trend_analysis = self.analyze_historical_trend(values, sorted_months)

        # Make predictions
        predictions = []
        last_month = sorted_months[-1]
        last_year = int(last_month[:4])
        last_month_num = int(last_month[4:6])

        for i in range(1, months_ahead + 1):
            # Calculate next month
            next_month_num = (last_month_num + i - 1) % 12 + 1
            next_year = last_year + (last_month_num + i - 1) // 12

            # Get seasonal factor
            month_key = f"{next_month_num:02d}"
            seasonal_factor = 1.0
            if seasonality["has_seasonality"] and month_key in seasonality["seasonal_pattern"]:
                avg_value = sum(values) / len(values) if values else 1
                seasonal_factor = seasonality["seasonal_pattern"][month_key] / avg_value if avg_value else 1

            # Apply trend and seasonality
            base_prediction = values[-1] * (1 + trend_analysis["slope"] / 100)
            seasonal_prediction = base_prediction * seasonal_factor

            predictions.append({
                "period": f"{next_year}{next_month_num:02d}",
                "value": round(seasonal_prediction, 2),
                "trend_component": round(base_prediction, 2),
                "seasonal_factor": round(seasonal_factor, 2)
            })

        return {
            "predictions": predictions,
            "method": "seasonal_decomposition",
            "has_seasonality": seasonality["has_seasonality"],
            "summary": f"계절성을 고려한 {months_ahead}개월 예측 완료"
        }

    # ============== Anomaly Detection ==============

    def detect_anomalies(
        self,
        data: List[float],
        threshold: float = 2.0
    ) -> Dict[str, Any]:
        """
        Detect anomalies in data using statistical methods

        Args:
            data: List of values
            threshold: Z-score threshold for anomaly detection

        Returns:
            Anomaly detection results
        """
        if not data or len(data) < 3:
            return {
                "anomalies": [],
                "anomaly_count": 0,
                "summary": "이상치 탐지를 위한 데이터가 부족합니다"
            }

        # Clean data
        clean_data = [float(v) if v is not None else 0 for v in data]

        # Calculate statistics
        mean = np.mean(clean_data)
        std = np.std(clean_data)

        if std == 0:
            return {
                "anomalies": [],
                "anomaly_count": 0,
                "summary": "데이터 변동이 없어 이상치를 탐지할 수 없습니다"
            }

        # Detect anomalies using Z-score
        anomalies = []
        for i, value in enumerate(clean_data):
            z_score = abs((value - mean) / std)
            if z_score > threshold:
                anomalies.append({
                    "index": i,
                    "value": value,
                    "z_score": round(z_score, 2),
                    "deviation": round(value - mean, 2)
                })

        return {
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "mean": round(mean, 2),
            "std": round(std, 2),
            "threshold": threshold,
            "summary": f"{len(anomalies)}개의 이상치 발견 (기준: Z-score > {threshold})"
        }

    def find_patterns(
        self,
        data: List[float],
        pattern_length: int = 3
    ) -> Dict[str, Any]:
        """
        Find recurring patterns in data

        Args:
            data: List of values
            pattern_length: Length of pattern to search for

        Returns:
            Pattern analysis results
        """
        if not data or len(data) < pattern_length * 2:
            return {
                "patterns_found": False,
                "recurring_patterns": [],
                "summary": "패턴 분석을 위한 데이터가 부족합니다"
            }

        clean_data = [float(v) if v is not None else 0 for v in data]

        # Convert to trend patterns (up/down/stable)
        patterns = []
        for i in range(1, len(clean_data)):
            if clean_data[i] > clean_data[i-1] * 1.05:
                patterns.append("up")
            elif clean_data[i] < clean_data[i-1] * 0.95:
                patterns.append("down")
            else:
                patterns.append("stable")

        # Find recurring patterns
        pattern_counts = {}
        for i in range(len(patterns) - pattern_length + 1):
            pattern = tuple(patterns[i:i+pattern_length])
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        # Filter patterns that occur more than once
        recurring_patterns = [
            {
                "pattern": list(pattern),
                "occurrences": count,
                "frequency": round(count / (len(patterns) - pattern_length + 1) * 100, 2)
            }
            for pattern, count in pattern_counts.items()
            if count > 1
        ]

        # Sort by frequency
        recurring_patterns.sort(key=lambda x: x["occurrences"], reverse=True)

        return {
            "patterns_found": len(recurring_patterns) > 0,
            "recurring_patterns": recurring_patterns[:5],  # Top 5 patterns
            "total_patterns": len(recurring_patterns),
            "summary": f"{len(recurring_patterns)}개의 반복 패턴 발견"
        }

    # ============== Utility Methods ==============

    def get_trend_interpretation(self, trend_data: Dict[str, Any]) -> str:
        """
        Get human-readable interpretation of trend

        Args:
            trend_data: Trend analysis results

        Returns:
            Interpretation string
        """
        direction = trend_data.get("trend_direction", "unknown")
        strength = trend_data.get("trend_strength", 0)
        volatility = trend_data.get("volatility", 0)

        interpretation = []

        # Trend direction
        if direction == "increasing":
            interpretation.append("매출이 상승 추세를 보이고 있습니다")
        elif direction == "decreasing":
            interpretation.append("매출이 하락 추세를 보이고 있습니다")
        else:
            interpretation.append("매출이 안정적인 수준을 유지하고 있습니다")

        # Trend strength
        if strength > 0.7:
            interpretation.append("매우 명확한 트렌드입니다")
        elif strength > 0.4:
            interpretation.append("뚜렷한 트렌드를 보입니다")
        else:
            interpretation.append("트렌드가 약하거나 불규칙합니다")

        # Volatility
        if volatility > 30:
            interpretation.append("변동성이 매우 높습니다")
        elif volatility > 15:
            interpretation.append("적당한 변동성을 보입니다")
        else:
            interpretation.append("변동성이 낮고 안정적입니다")

        return ". ".join(interpretation)


# Singleton instance
_trend_analysis_tool_instance = None


def get_trend_analysis_tool() -> TrendAnalysisTool:
    """Get singleton instance of TrendAnalysisTool"""
    global _trend_analysis_tool_instance
    if _trend_analysis_tool_instance is None:
        _trend_analysis_tool_instance = TrendAnalysisTool()
    return _trend_analysis_tool_instance