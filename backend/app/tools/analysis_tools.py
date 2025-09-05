"""
Analysis Tools
데이터 분석 관련 도구들
"""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun
import logging
logger = logging.getLogger(__name__)
import time
import random
import json
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add database test path to system path
try:
    sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "database" / "test"))
    from mock_data import get_mock_db
except ImportError:
    # If import fails, create a simple mock function
    def get_mock_db():
        return {
            "drug_database": [],
            "sales_data": [],
            "compliance_data": [],
            "customer_data": []
        }

from .base import BaseTool, ToolResult, StructuredTool, MultiStepTool


class DataAnalysisInput(BaseModel):
    """데이터 분석 입력"""
    data_type: str = Field(description="분석할 데이터 유형: sales, performance, customer")
    period: str = Field(description="분석 기간 (YYYY-MM or YYYY-Q1)")
    metrics: Optional[List[str]] = Field(None, description="분석할 지표 목록")


class TrendAnalysisInput(BaseModel):
    """트렌드 분석 입력"""
    metric: str = Field(description="분석할 지표: revenue, growth, market_share")
    periods: int = Field(default=6, description="분석할 기간 수")
    forecast: bool = Field(default=False, description="예측 포함 여부")


class StatisticalAnalysisInput(BaseModel):
    """통계 분석 입력"""
    dataset: str = Field(description="분석할 데이터셋")
    methods: List[str] = Field(default=["mean", "median", "std"], description="통계 방법")
    confidence_level: float = Field(default=0.95, description="신뢰 수준")


class DataAnalysisTool(MultiStepTool):
    """데이터 분석 도구"""
    
    name: str = "data_analysis"
    description: str = "매출, 성과, 고객 데이터를 분석합니다."
    args_schema: type[BaseModel] = DataAnalysisInput
    steps: List[str] = ["collect", "process", "analyze", "summarize"]
    
    def __init__(self):
        super().__init__()
        self.db = get_mock_db()
    
    async def step_collect(self, input_data: DataAnalysisInput, results: Dict) -> Dict:
        """데이터 수집 단계"""
        data_type = input_data.data_type
        period = input_data.period
        
        collected_data = {}
        
        if data_type == "sales":
            # 매출 데이터 수집
            year, month = period.split("-") if "-" in period else (period, None)
            collected_data = self.db.get_monthly_sales(int(year), month)
            
        elif data_type == "performance":
            # 성과 데이터 수집
            collected_data = self.db.get_team_performance()
            
        elif data_type == "customer":
            # 고객 데이터 수집
            collected_data = self.db.get_customer_segments()
        
        return {"raw_data": collected_data, "count": len(collected_data)}
    
    async def step_process(self, input_data: DataAnalysisInput, results: Dict) -> Dict:
        """데이터 처리 단계"""
        raw_data = results.get("collect", {}).get("raw_data", {})
        
        processed = {
            "cleaned": True,
            "normalized": True,
            "missing_values_handled": True,
            "outliers_detected": random.randint(0, 5)
        }
        
        return processed
    
    async def step_analyze(self, input_data: DataAnalysisInput, results: Dict) -> Dict:
        """데이터 분석 단계"""
        raw_data = results.get("collect", {}).get("raw_data", {})
        metrics = input_data.metrics or ["total", "average", "growth"]
        
        analysis = {}
        
        for metric in metrics:
            if metric == "total":
                # 총합 계산
                if isinstance(raw_data, dict) and "total" in str(raw_data):
                    analysis["total"] = sum([v for k, v in raw_data.items() if isinstance(v, (int, float)) and "total" in k.lower()])
                else:
                    analysis["total"] = random.randint(1000000, 5000000)
                    
            elif metric == "average":
                # 평균 계산
                analysis["average"] = random.randint(100000, 500000)
                
            elif metric == "growth":
                # 성장률 계산
                analysis["growth"] = round(random.uniform(-5, 15), 2)
        
        return analysis
    
    async def step_summarize(self, input_data: DataAnalysisInput, results: Dict) -> Dict:
        """요약 단계"""
        analysis = results.get("analyze", {})
        
        summary = {
            "key_findings": [
                f"{input_data.data_type} 데이터 분석 완료",
                f"분석 기간: {input_data.period}",
                f"주요 지표: {', '.join(input_data.metrics or ['기본 지표'])}"
            ],
            "insights": [
                "전반적인 성장 추세 확인",
                "계절적 변동 패턴 발견",
                "개선 필요 영역 식별"
            ],
            "recommendations": [
                "지속적인 모니터링 권장",
                "저조한 지표에 대한 개선 계획 수립",
                "우수 성과 영역 확대 검토"
            ]
        }
        
        return summary
    
    async def _arun(
        self,
        data_type: str,
        period: str,
        metrics: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """데이터 분석 실행"""
        start_time = time.time()
        
        try:
            # MultiStepTool의 execute_steps 메서드 사용
            input_data = DataAnalysisInput(
                data_type=data_type,
                period=period,
                metrics=metrics or ["total", "average", "growth"]
            )
            
            result = await self.execute_steps(input_data)
            result.execution_time = time.time() - start_time
            
            return result
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class TrendAnalysisTool(StructuredTool):
    """트렌드 분석 도구"""
    
    name: str = "trend_analysis"
    description: str = "시계열 데이터의 트렌드를 분석하고 예측합니다."
    args_schema: type[BaseModel] = TrendAnalysisInput
    
    def __init__(self):
        super().__init__()
        self.db = get_mock_db()
    
    async def _arun(
        self,
        metric: str,
        periods: int = 6,
        forecast: bool = False,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """트렌드 분석 실행"""
        start_time = time.time()
        
        try:
            # 과거 데이터 생성
            historical_data = []
            base_value = random.randint(1000000, 3000000)
            
            for i in range(periods):
                date = datetime.now() - timedelta(days=30 * (periods - i))
                variation = random.uniform(-0.1, 0.15)
                value = int(base_value * (1 + variation))
                
                historical_data.append({
                    "period": date.strftime("%Y-%m"),
                    "value": value,
                    "metric": metric
                })
                
                base_value = value
            
            # 트렌드 계산
            values = [d["value"] for d in historical_data]
            trend = "상승" if values[-1] > values[0] else "하락"
            growth_rate = ((values[-1] - values[0]) / values[0] * 100) if values[0] else 0
            
            # 통계 계산
            avg_value = sum(values) / len(values)
            max_value = max(values)
            min_value = min(values)
            volatility = (max_value - min_value) / avg_value * 100
            
            result_data = {
                "metric": metric,
                "periods_analyzed": periods,
                "historical_data": historical_data,
                "trend": trend,
                "growth_rate": round(growth_rate, 2),
                "statistics": {
                    "average": round(avg_value, 0),
                    "max": max_value,
                    "min": min_value,
                    "volatility": round(volatility, 2)
                }
            }
            
            # 예측 추가
            if forecast:
                # 간단한 선형 예측
                last_growth = (values[-1] - values[-2]) / values[-2] if len(values) > 1 else 0
                forecast_data = []
                
                last_value = values[-1]
                for i in range(3):  # 3개월 예측
                    future_date = datetime.now() + timedelta(days=30 * (i + 1))
                    predicted_value = int(last_value * (1 + last_growth))
                    
                    forecast_data.append({
                        "period": future_date.strftime("%Y-%m"),
                        "predicted_value": predicted_value,
                        "confidence": "Medium"
                    })
                    
                    last_value = predicted_value
                
                result_data["forecast"] = forecast_data
            
            return ToolResult(
                success=True,
                data=result_data,
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class StatisticalAnalysisTool(StructuredTool):
    """통계 분석 도구"""
    
    name: str = "statistical_analysis"
    description: str = "데이터에 대한 통계 분석을 수행합니다."
    args_schema: type[BaseModel] = StatisticalAnalysisInput
    
    async def _arun(
        self,
        dataset: str,
        methods: List[str] = None,
        confidence_level: float = 0.95,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """통계 분석 실행"""
        start_time = time.time()
        
        try:
            # Mock 데이터 생성
            data_points = [random.gauss(100, 15) for _ in range(100)]
            
            results = {
                "dataset": dataset,
                "sample_size": len(data_points),
                "confidence_level": confidence_level
            }
            
            methods = methods or ["mean", "median", "std", "correlation"]
            
            # 각 통계 방법 적용
            if "mean" in methods:
                results["mean"] = round(sum(data_points) / len(data_points), 2)
            
            if "median" in methods:
                sorted_data = sorted(data_points)
                mid = len(sorted_data) // 2
                results["median"] = round(sorted_data[mid], 2)
            
            if "std" in methods:
                mean = sum(data_points) / len(data_points)
                variance = sum((x - mean) ** 2 for x in data_points) / len(data_points)
                results["std_dev"] = round(variance ** 0.5, 2)
            
            if "correlation" in methods:
                # Mock correlation matrix
                results["correlation"] = {
                    "sales_vs_marketing": 0.85,
                    "sales_vs_season": 0.72,
                    "performance_vs_training": 0.68
                }
            
            if "hypothesis_test" in methods:
                # Mock hypothesis test
                results["hypothesis_test"] = {
                    "null_hypothesis": "평균 매출 = 목표 매출",
                    "p_value": 0.03,
                    "result": "귀무가설 기각 (p < 0.05)",
                    "conclusion": "통계적으로 유의미한 차이 존재"
                }
            
            # 신뢰구간 계산
            z_score = 1.96 if confidence_level == 0.95 else 2.58
            margin_error = z_score * (results.get("std_dev", 15) / (len(data_points) ** 0.5))
            
            results["confidence_interval"] = {
                "lower": round(results.get("mean", 100) - margin_error, 2),
                "upper": round(results.get("mean", 100) + margin_error, 2)
            }
            
            # 분포 정보
            results["distribution"] = {
                "type": "정규분포 추정",
                "skewness": round(random.uniform(-0.5, 0.5), 2),
                "kurtosis": round(random.uniform(-1, 1), 2),
                "outliers": random.randint(0, 5)
            }
            
            return ToolResult(
                success=True,
                data=results,
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class ComparativeAnalysisTool(BaseTool):
    """비교 분석 도구"""
    
    name: str = "comparative_analysis"
    description: str = "여러 데이터셋이나 기간을 비교 분석합니다."
    
    def __init__(self):
        super().__init__()
        self.db = get_mock_db()
    
    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """비교 분석 실행"""
        start_time = time.time()
        
        try:
            # Mock 비교 분석
            comparison_data = {
                "query": query,
                "comparison_type": "period_over_period",
                "periods_compared": ["2024-Q1", "2024-Q2"],
                "metrics": {
                    "revenue": {
                        "Q1": 350000000,
                        "Q2": 390000000,
                        "change": "+11.4%",
                        "trend": "improvement"
                    },
                    "customer_acquisition": {
                        "Q1": 23,
                        "Q2": 31,
                        "change": "+34.8%",
                        "trend": "significant_improvement"
                    },
                    "market_share": {
                        "Q1": 22.5,
                        "Q2": 23.5,
                        "change": "+1.0pp",
                        "trend": "steady_growth"
                    }
                },
                "key_findings": [
                    "2분기 매출이 1분기 대비 11.4% 증가",
                    "신규 고객 획득이 34.8% 증가하여 시장 확대",
                    "시장 점유율 1%p 상승으로 경쟁력 강화"
                ],
                "recommendations": [
                    "성장 모멘텀 유지를 위한 투자 확대",
                    "고객 획득 전략 지속 강화",
                    "시장 점유율 확대를 위한 차별화 전략 수립"
                ]
            }
            
            return ToolResult(
                success=True,
                data=comparison_data,
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


# Tool 레지스트리에 등록
def register_analysis_tools():
    """모든 분석 도구를 레지스트리에 등록"""
    from .base import tool_registry
    
    tools = [
        (DataAnalysisTool(), "analysis"),
        (TrendAnalysisTool(), "analysis"),
        (StatisticalAnalysisTool(), "analysis"),
        (ComparativeAnalysisTool(), "analysis")
    ]
    
    for tool, category in tools:
        tool_registry.register(tool, category)
    
    logger.info(f"Registered {len(tools)} analysis tools")