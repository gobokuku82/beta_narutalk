"""
실적분석 핵심 로직

성과 데이터 분석을 위한 핵심 알고리즘과 계산 로직을 담당합니다.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
from .config import PerformanceAnalysisConfig

logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    """실적분석 핵심 로직 클래스"""
    
    def __init__(self, config: PerformanceAnalysisConfig):
        self.config = config
        self.database_service = None
        
    def set_services(self, database_service=None, **kwargs):
        """서비스 의존성 주입"""
        self.database_service = database_service
    
    async def analyze_performance(self, analysis_type: str, period: str = None, 
                                target_kpi: str = None) -> Dict[str, Any]:
        """성과 분석 메인 함수"""
        try:
            period = period or self.config.default_analysis_period
            
            if analysis_type == "sales_analysis":
                return await self.analyze_sales_performance(period)
            elif analysis_type == "profit_analysis":
                return await self.analyze_profit_performance(period)
            elif analysis_type == "growth_analysis":
                return await self.analyze_growth_rate(period)
            elif analysis_type == "trend_analysis":
                return await self.analyze_trends(period, target_kpi)
            elif analysis_type == "comparative_analysis":
                return await self.analyze_comparative_performance(period)
            elif analysis_type == "kpi_analysis":
                return await self.analyze_kpi_performance(target_kpi)
            else:
                return await self.analyze_general_performance(period)
                
        except Exception as e:
            logger.error(f"성과 분석 실패 ({analysis_type}): {str(e)}")
            return {"error": str(e), "analysis_type": analysis_type}
    
    async def analyze_sales_performance(self, period: str) -> Dict[str, Any]:
        """매출 성과 분석"""
        try:
            # 가상의 매출 데이터 (실제 환경에서는 데이터베이스에서 조회)
            sales_data = await self.get_mock_sales_data(period)
            
            analysis_result = {
                "analysis_type": "sales_analysis",
                "period": period,
                "data": sales_data,
                "insights": [],
                "recommendations": [],
                "performance_rating": "good"
            }
            
            # 매출 트렌드 분석
            if len(sales_data) >= 2:
                latest_sales = sales_data[-1]["value"]
                previous_sales = sales_data[-2]["value"]
                growth_rate = ((latest_sales - previous_sales) / previous_sales) * 100
                
                analysis_result["growth_rate"] = growth_rate
                
                if growth_rate > 10:
                    analysis_result["insights"].append("매출이 크게 증가하고 있습니다.")
                    analysis_result["performance_rating"] = "excellent"
                elif growth_rate > 0:
                    analysis_result["insights"].append("매출이 증가 추세입니다.")
                else:
                    analysis_result["insights"].append("매출이 감소하고 있어 주의가 필요합니다.")
                    analysis_result["performance_rating"] = "poor"
            
            # 평균 매출 계산
            avg_sales = sum(item["value"] for item in sales_data) / len(sales_data)
            analysis_result["average_sales"] = avg_sales
            
            # 추천사항 생성
            if analysis_result["performance_rating"] == "poor":
                analysis_result["recommendations"].extend([
                    "마케팅 전략을 재검토하여 고객 확보에 집중하세요.",
                    "제품/서비스의 경쟁력을 강화하세요.",
                    "영업팀의 활동을 점검하고 개선하세요."
                ])
            elif analysis_result["performance_rating"] == "good":
                analysis_result["recommendations"].extend([
                    "현재 성과를 유지하며 추가 성장 기회를 모색하세요.",
                    "성공 요인을 분석하여 다른 영역에 적용하세요."
                ])
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"매출 성과 분석 실패: {str(e)}")
            return {"error": str(e)}
    
    async def analyze_profit_performance(self, period: str) -> Dict[str, Any]:
        """수익성 분석"""
        try:
            profit_data = await self.get_mock_profit_data(period)
            
            analysis_result = {
                "analysis_type": "profit_analysis",
                "period": period,
                "data": profit_data,
                "insights": [],
                "recommendations": [],
                "performance_rating": "average"
            }
            
            # 수익률 계산
            if profit_data:
                total_revenue = sum(item.get("revenue", 0) for item in profit_data)
                total_profit = sum(item.get("profit", 0) for item in profit_data)
                
                if total_revenue > 0:
                    profit_margin = (total_profit / total_revenue) * 100
                    analysis_result["profit_margin"] = profit_margin
                    
                    if profit_margin > 20:
                        analysis_result["insights"].append("수익률이 우수합니다.")
                        analysis_result["performance_rating"] = "excellent"
                    elif profit_margin > 10:
                        analysis_result["insights"].append("수익률이 양호한 수준입니다.")
                        analysis_result["performance_rating"] = "good"
                    else:
                        analysis_result["insights"].append("수익률 개선이 필요합니다.")
                        analysis_result["performance_rating"] = "poor"
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"수익성 분석 실패: {str(e)}")
            return {"error": str(e)}
    
    async def analyze_growth_rate(self, period: str) -> Dict[str, Any]:
        """성장률 분석"""
        try:
            growth_data = await self.calculate_growth_rates(period)
            
            analysis_result = {
                "analysis_type": "growth_analysis",
                "period": period,
                "data": growth_data,
                "insights": [],
                "recommendations": [],
                "performance_rating": "average"
            }
            
            # 평균 성장률 계산
            if growth_data:
                avg_growth = sum(growth_data) / len(growth_data)
                analysis_result["average_growth_rate"] = avg_growth
                
                target_growth = self.config.kpi_definitions["성장률"]["target_value"]
                
                if avg_growth >= target_growth:
                    analysis_result["insights"].append(f"목표 성장률({target_growth}%)을 달성했습니다.")
                    analysis_result["performance_rating"] = "excellent"
                elif avg_growth >= target_growth * 0.7:
                    analysis_result["insights"].append("목표에 근접한 성장률을 보이고 있습니다.")
                    analysis_result["performance_rating"] = "good"
                else:
                    analysis_result["insights"].append("목표 성장률에 미치지 못하고 있습니다.")
                    analysis_result["performance_rating"] = "poor"
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"성장률 분석 실패: {str(e)}")
            return {"error": str(e)}
    
    async def analyze_trends(self, period: str, target_kpi: str = None) -> Dict[str, Any]:
        """트렌드 분석"""
        try:
            trend_data = await self.get_trend_data(period, target_kpi)
            
            analysis_result = {
                "analysis_type": "trend_analysis",
                "period": period,
                "target_kpi": target_kpi,
                "data": trend_data,
                "trend_direction": "stable",
                "insights": [],
                "recommendations": []
            }
            
            # 트렌드 방향 분석
            if len(trend_data) >= 3:
                # 간단한 선형 회귀로 트렌드 방향 결정
                x_values = list(range(len(trend_data)))
                y_values = [item["value"] for item in trend_data]
                
                trend_slope = self.calculate_trend_slope(x_values, y_values)
                
                if trend_slope > 0.1:
                    analysis_result["trend_direction"] = "increasing"
                    analysis_result["insights"].append("상승 트렌드를 보이고 있습니다.")
                elif trend_slope < -0.1:
                    analysis_result["trend_direction"] = "decreasing"
                    analysis_result["insights"].append("하락 트렌드를 보이고 있습니다.")
                else:
                    analysis_result["trend_direction"] = "stable"
                    analysis_result["insights"].append("안정적인 추세를 보이고 있습니다.")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"트렌드 분석 실패: {str(e)}")
            return {"error": str(e)}
    
    async def analyze_kpi_performance(self, target_kpi: str = None) -> Dict[str, Any]:
        """KPI 성과 분석"""
        try:
            kpi_results = {}
            
            if target_kpi and target_kpi in self.config.kpi_definitions:
                kpis_to_analyze = [target_kpi]
            else:
                kpis_to_analyze = list(self.config.kpi_definitions.keys())
            
            for kpi_name in kpis_to_analyze:
                kpi_data = await self.get_kpi_data(kpi_name)
                kpi_results[kpi_name] = await self.evaluate_kpi_performance(kpi_name, kpi_data)
            
            analysis_result = {
                "analysis_type": "kpi_analysis",
                "target_kpi": target_kpi,
                "kpi_results": kpi_results,
                "overall_performance": await self.calculate_overall_kpi_performance(kpi_results),
                "insights": [],
                "recommendations": []
            }
            
            # 전체 KPI 성과 평가
            overall_score = analysis_result["overall_performance"]["score"]
            
            if overall_score >= self.config.performance_thresholds["excellent"]:
                analysis_result["insights"].append("전반적인 KPI 성과가 우수합니다.")
            elif overall_score >= self.config.performance_thresholds["good"]:
                analysis_result["insights"].append("KPI 성과가 양호한 수준입니다.")
            else:
                analysis_result["insights"].append("KPI 성과 개선이 필요합니다.")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"KPI 분석 실패: {str(e)}")
            return {"error": str(e)}
    
    async def get_mock_sales_data(self, period: str) -> List[Dict[str, Any]]:
        """가상의 매출 데이터 생성 (실제 환경에서는 DB 조회)"""
        import random
        
        base_value = 1000000  # 기본 매출 100만원
        data = []
        
        periods = {
            "daily": 30,
            "weekly": 12,
            "monthly": 12,
            "quarterly": 4,
            "yearly": 3
        }
        
        num_periods = periods.get(period, 12)
        
        for i in range(num_periods):
            # 약간의 성장과 랜덤 변동 적용
            growth_factor = 1 + (i * 0.02)  # 2% 성장
            random_factor = random.uniform(0.8, 1.2)  # ±20% 변동
            
            value = int(base_value * growth_factor * random_factor)
            
            data.append({
                "period": f"{period}_{i+1}",
                "value": value,
                "date": (datetime.now() - timedelta(days=30*(num_periods-i))).strftime("%Y-%m-%d")
            })
        
        return data
    
    async def get_mock_profit_data(self, period: str) -> List[Dict[str, Any]]:
        """가상의 수익 데이터 생성"""
        sales_data = await self.get_mock_sales_data(period)
        profit_data = []
        
        for item in sales_data:
            revenue = item["value"]
            # 수익률 10-25% 범위에서 랜덤
            import random
            profit_rate = random.uniform(0.1, 0.25)
            profit = int(revenue * profit_rate)
            
            profit_data.append({
                "period": item["period"],
                "revenue": revenue,
                "profit": profit,
                "date": item["date"]
            })
        
        return profit_data
    
    async def calculate_growth_rates(self, period: str) -> List[float]:
        """성장률 계산"""
        sales_data = await self.get_mock_sales_data(period)
        growth_rates = []
        
        for i in range(1, len(sales_data)):
            previous_value = sales_data[i-1]["value"]
            current_value = sales_data[i]["value"]
            
            if previous_value > 0:
                growth_rate = ((current_value - previous_value) / previous_value) * 100
                growth_rates.append(growth_rate)
        
        return growth_rates
    
    async def get_trend_data(self, period: str, target_kpi: str = None) -> List[Dict[str, Any]]:
        """트렌드 데이터 조회"""
        if target_kpi == "매출액":
            return await self.get_mock_sales_data(period)
        else:
            # 기본적으로 매출 데이터 반환
            return await self.get_mock_sales_data(period)
    
    async def get_kpi_data(self, kpi_name: str) -> Dict[str, Any]:
        """KPI 데이터 조회"""
        # 가상의 KPI 데이터 반환
        import random
        
        kpi_config = self.config.kpi_definitions.get(kpi_name, {})
        target_increase = kpi_config.get("target_increase", 10)
        
        current_value = random.randint(80, 120)  # 목표 대비 80-120%
        
        return {
            "kpi_name": kpi_name,
            "current_value": current_value,
            "target_value": 100,
            "achievement_rate": current_value,
            "unit": kpi_config.get("unit", "")
        }
    
    async def evaluate_kpi_performance(self, kpi_name: str, kpi_data: Dict[str, Any]) -> Dict[str, Any]:
        """개별 KPI 성과 평가"""
        achievement_rate = kpi_data["achievement_rate"]
        
        if achievement_rate >= self.config.performance_thresholds["excellent"]:
            performance_level = "excellent"
        elif achievement_rate >= self.config.performance_thresholds["good"]:
            performance_level = "good"
        elif achievement_rate >= self.config.performance_thresholds["average"]:
            performance_level = "average"
        else:
            performance_level = "poor"
        
        return {
            **kpi_data,
            "performance_level": performance_level,
            "score": achievement_rate
        }
    
    async def calculate_overall_kpi_performance(self, kpi_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """전체 KPI 성과 계산"""
        if not kpi_results:
            return {"score": 0, "level": "poor"}
        
        total_score = sum(result["score"] for result in kpi_results.values())
        average_score = total_score / len(kpi_results)
        
        if average_score >= self.config.performance_thresholds["excellent"]:
            level = "excellent"
        elif average_score >= self.config.performance_thresholds["good"]:
            level = "good"
        elif average_score >= self.config.performance_thresholds["average"]:
            level = "average"
        else:
            level = "poor"
        
        return {
            "score": average_score,
            "level": level,
            "total_kpis": len(kpi_results)
        }
    
    def calculate_trend_slope(self, x_values: List[float], y_values: List[float]) -> float:
        """트렌드 기울기 계산 (단순 선형 회귀)"""
        n = len(x_values)
        if n < 2:
            return 0
        
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x_squared = sum(x * x for x in x_values)
        
        denominator = n * sum_x_squared - sum_x * sum_x
        if denominator == 0:
            return 0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope
    
    async def analyze_comparative_performance(self, period: str) -> Dict[str, Any]:
        """비교 성과 분석"""
        try:
            current_data = await self.get_mock_sales_data(period)
            
            analysis_result = {
                "analysis_type": "comparative_analysis",
                "period": period,
                "data": current_data,
                "insights": [],
                "recommendations": []
            }
            
            # 기간별 비교
            if len(current_data) >= 2:
                first_half = current_data[:len(current_data)//2]
                second_half = current_data[len(current_data)//2:]
                
                first_avg = sum(item["value"] for item in first_half) / len(first_half)
                second_avg = sum(item["value"] for item in second_half) / len(second_half)
                
                change_rate = ((second_avg - first_avg) / first_avg) * 100
                analysis_result["change_rate"] = change_rate
                
                if change_rate > 5:
                    analysis_result["insights"].append("후반기 성과가 전반기 대비 개선되었습니다.")
                elif change_rate < -5:
                    analysis_result["insights"].append("후반기 성과가 전반기 대비 하락했습니다.")
                else:
                    analysis_result["insights"].append("전반기와 후반기 성과가 비슷한 수준입니다.")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"비교 성과 분석 실패: {str(e)}")
            return {"error": str(e)}
    
    async def analyze_general_performance(self, period: str) -> Dict[str, Any]:
        """일반 성과 분석"""
        try:
            # 기본적으로 매출 분석 수행
            return await self.analyze_sales_performance(period)
            
        except Exception as e:
            logger.error(f"일반 성과 분석 실패: {str(e)}")
            return {"error": str(e)} 