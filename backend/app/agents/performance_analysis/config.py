"""
실적분석 에이전트 설정

실적 분석과 관련된 모든 설정을 관리합니다.
"""

from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class PerformanceAnalysisConfig:
    """실적분석 에이전트 설정"""
    
    # 기본 설정
    agent_name: str = "performance_analysis_agent"
    confidence_threshold: float = 0.7
    
    # 분석 기간 설정
    default_analysis_period: str = "monthly"  # daily, weekly, monthly, quarterly, yearly
    max_historical_months: int = 24  # 최대 24개월 과거 데이터
    
    # 지원하는 분석 유형
    supported_analysis_types: List[str] = None
    
    # KPI 설정
    kpi_definitions: Dict[str, Dict[str, Any]] = None
    
    # 임계값 설정
    performance_thresholds: Dict[str, float] = None
    
    # 차트 설정
    chart_settings: Dict[str, Any] = None
    
    # 데이터 소스 설정
    data_sources: Dict[str, str] = None
    
    def __post_init__(self):
        if self.supported_analysis_types is None:
            self.supported_analysis_types = [
                "sales_analysis",       # 매출 분석
                "profit_analysis",      # 수익성 분석
                "growth_analysis",      # 성장률 분석
                "trend_analysis",       # 트렌드 분석
                "comparative_analysis", # 비교 분석
                "forecast_analysis",    # 예측 분석
                "kpi_analysis",        # KPI 분석
                "period_analysis"      # 기간별 분석
            ]
        
        if self.kpi_definitions is None:
            self.kpi_definitions = {
                "매출액": {
                    "description": "총 매출 금액",
                    "unit": "원",
                    "target_increase": 10,  # 목표 증가율 (%)
                    "data_source": "sales_table"
                },
                "순이익": {
                    "description": "순 이익 금액",
                    "unit": "원", 
                    "target_increase": 15,
                    "data_source": "profit_table"
                },
                "성장률": {
                    "description": "전년 동기 대비 성장률",
                    "unit": "%",
                    "target_value": 10,
                    "data_source": "calculated"
                },
                "고객수": {
                    "description": "총 고객 수",
                    "unit": "명",
                    "target_increase": 5,
                    "data_source": "customer_table"
                }
            }
        
        if self.performance_thresholds is None:
            self.performance_thresholds = {
                "excellent": 90,    # 우수
                "good": 70,        # 양호
                "average": 50,     # 보통
                "poor": 30         # 부진
            }
        
        if self.chart_settings is None:
            self.chart_settings = {
                "default_chart_type": "line",
                "color_scheme": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
                "show_trend_line": True,
                "show_data_labels": True
            }
        
        if self.data_sources is None:
            self.data_sources = {
                "sales": "performance_db.sales",
                "profit": "performance_db.profit", 
                "customers": "clients_db.customers",
                "products": "performance_db.products"
            }

# 기본 설정 인스턴스
default_config = PerformanceAnalysisConfig() 