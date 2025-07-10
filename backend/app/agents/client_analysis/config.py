"""
거래처분석 에이전트 설정

거래처 및 고객 분석과 관련된 모든 설정을 관리합니다.
"""

from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ClientAnalysisConfig:
    """거래처분석 에이전트 설정"""
    
    # 기본 설정
    agent_name: str = "client_analysis_agent"
    confidence_threshold: float = 0.7
    
    # 분석 유형
    supported_analysis_types: List[str] = None
    
    # 고객 세분화 기준
    segmentation_criteria: Dict[str, Dict[str, Any]] = None
    
    # 거래처 평가 지표
    evaluation_metrics: Dict[str, Dict[str, Any]] = None
    
    # 위험도 임계값
    risk_thresholds: Dict[str, float] = None
    
    # 데이터 소스
    data_sources: Dict[str, str] = None
    
    def __post_init__(self):
        if self.supported_analysis_types is None:
            self.supported_analysis_types = [
                "customer_segmentation",    # 고객 세분화
                "client_performance",       # 거래처 성과
                "relationship_analysis",    # 관계 분석
                "risk_assessment",         # 위험도 평가
                "loyalty_analysis",        # 충성도 분석
                "growth_potential",        # 성장 잠재력
                "transaction_pattern",     # 거래 패턴
                "profitability_analysis"   # 수익성 분석
            ]
        
        if self.segmentation_criteria is None:
            self.segmentation_criteria = {
                "거래규모": {
                    "large": {"min_value": 100000000, "description": "대형 거래처"},
                    "medium": {"min_value": 50000000, "description": "중형 거래처"},
                    "small": {"min_value": 10000000, "description": "소형 거래처"},
                    "micro": {"min_value": 0, "description": "영세 거래처"}
                },
                "거래빈도": {
                    "high": {"min_frequency": 12, "description": "고빈도 (월 1회 이상)"},
                    "medium": {"min_frequency": 6, "description": "중빈도 (격월)"},
                    "low": {"min_frequency": 1, "description": "저빈도 (연 1-2회)"}
                },
                "지역": {
                    "seoul": {"description": "서울/수도권"},
                    "regional": {"description": "지방"},
                    "overseas": {"description": "해외"}
                }
            }
        
        if self.evaluation_metrics is None:
            self.evaluation_metrics = {
                "매출기여도": {
                    "weight": 0.3,
                    "unit": "%",
                    "description": "전체 매출 대비 기여도"
                },
                "수익성": {
                    "weight": 0.25,
                    "unit": "%",
                    "description": "거래 수익률"
                },
                "안정성": {
                    "weight": 0.2,
                    "unit": "점",
                    "description": "거래 안정성 점수"
                },
                "성장성": {
                    "weight": 0.15,
                    "unit": "%",
                    "description": "연간 성장률"
                },
                "관계지속성": {
                    "weight": 0.1,
                    "unit": "년",
                    "description": "거래 지속 기간"
                }
            }
        
        if self.risk_thresholds is None:
            self.risk_thresholds = {
                "high_risk": 70,      # 고위험
                "medium_risk": 40,    # 중위험
                "low_risk": 20        # 저위험
            }
        
        if self.data_sources is None:
            self.data_sources = {
                "clients": "clients_db.companies",
                "transactions": "clients_db.transactions",
                "contacts": "clients_db.contacts",
                "contracts": "clients_db.contracts"
            }

# 기본 설정 인스턴스
default_config = ClientAnalysisConfig() 