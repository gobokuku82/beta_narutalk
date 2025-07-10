"""
거래처분석 핵심 로직

고객 및 거래처 데이터 분석을 위한 핵심 알고리즘을 담당합니다.
"""

from typing import Dict, List, Any, Optional
import logging
import random
from .config import ClientAnalysisConfig

logger = logging.getLogger(__name__)

class ClientAnalyzer:
    """거래처분석 핵심 로직 클래스"""
    
    def __init__(self, config: ClientAnalysisConfig):
        self.config = config
        self.database_service = None
        
    def set_services(self, database_service=None, **kwargs):
        """서비스 의존성 주입"""
        self.database_service = database_service
    
    async def analyze_clients(self, analysis_type: str, target_client: str = None, 
                            criteria: str = None) -> Dict[str, Any]:
        """거래처 분석 메인 함수"""
        try:
            if analysis_type == "customer_segmentation":
                return await self.analyze_customer_segmentation(criteria)
            elif analysis_type == "client_performance":
                return await self.analyze_client_performance(target_client)
            elif analysis_type == "risk_assessment":
                return await self.analyze_risk_assessment(target_client)
            elif analysis_type == "loyalty_analysis":
                return await self.analyze_loyalty(target_client)
            else:
                return await self.analyze_general_clients(analysis_type)
                
        except Exception as e:
            logger.error(f"거래처 분석 실패 ({analysis_type}): {str(e)}")
            return {"error": str(e), "analysis_type": analysis_type}
    
    async def analyze_customer_segmentation(self, criteria: str = None) -> Dict[str, Any]:
        """고객 세분화 분석"""
        try:
            # 가상의 고객 데이터
            client_data = await self.get_mock_client_data()
            
            segments = {}
            criteria = criteria or "거래규모"
            
            if criteria == "거래규모":
                for client in client_data:
                    revenue = client.get("annual_revenue", 0)
                    if revenue >= 100000000:
                        segment = "large"
                    elif revenue >= 50000000:
                        segment = "medium"
                    elif revenue >= 10000000:
                        segment = "small"
                    else:
                        segment = "micro"
                    
                    if segment not in segments:
                        segments[segment] = []
                    segments[segment].append(client)
            
            return {
                "analysis_type": "customer_segmentation",
                "criteria": criteria,
                "segments": segments,
                "insights": [
                    f"총 {len(client_data)}개 거래처를 {len(segments)}개 세그먼트로 분류했습니다.",
                    f"가장 큰 세그먼트는 {max(segments.keys(), key=lambda k: len(segments[k]))}입니다."
                ],
                "recommendations": [
                    "대형 거래처에는 전담 계정 관리자를 배정하세요.",
                    "소형 거래처는 디지털 채널을 통해 효율적으로 관리하세요."
                ]
            }
            
        except Exception as e:
            logger.error(f"고객 세분화 분석 실패: {str(e)}")
            return {"error": str(e)}
    
    async def analyze_client_performance(self, target_client: str = None) -> Dict[str, Any]:
        """거래처 성과 분석"""
        try:
            client_data = await self.get_mock_client_data()
            
            if target_client:
                # 특정 거래처 분석
                client_info = next((c for c in client_data if c["name"] == target_client), None)
                if not client_info:
                    return {"error": f"거래처 '{target_client}'을 찾을 수 없습니다."}
                
                performance_score = await self.calculate_performance_score(client_info)
                
                return {
                    "analysis_type": "client_performance",
                    "target_client": target_client,
                    "client_info": client_info,
                    "performance_score": performance_score,
                    "insights": [
                        f"{target_client}의 종합 성과 점수는 {performance_score:.1f}점입니다.",
                        "주요 강점과 개선점을 확인하세요."
                    ]
                }
            else:
                # 전체 거래처 성과 분석
                performance_data = []
                for client in client_data:
                    score = await self.calculate_performance_score(client)
                    performance_data.append({
                        "name": client["name"],
                        "score": score,
                        "revenue": client.get("annual_revenue", 0)
                    })
                
                # 성과 순으로 정렬
                performance_data.sort(key=lambda x: x["score"], reverse=True)
                
                return {
                    "analysis_type": "client_performance",
                    "performance_data": performance_data,
                    "top_performers": performance_data[:5],
                    "insights": [
                        f"총 {len(performance_data)}개 거래처의 성과를 분석했습니다.",
                        f"최고 성과 거래처는 {performance_data[0]['name']}입니다."
                    ]
                }
            
        except Exception as e:
            logger.error(f"거래처 성과 분석 실패: {str(e)}")
            return {"error": str(e)}
    
    async def analyze_risk_assessment(self, target_client: str = None) -> Dict[str, Any]:
        """위험도 평가"""
        try:
            client_data = await self.get_mock_client_data()
            risk_assessments = []
            
            for client in client_data:
                if target_client and client["name"] != target_client:
                    continue
                    
                risk_score = await self.calculate_risk_score(client)
                risk_level = self.get_risk_level(risk_score)
                
                risk_assessments.append({
                    "name": client["name"],
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "factors": client.get("risk_factors", [])
                })
            
            return {
                "analysis_type": "risk_assessment",
                "target_client": target_client,
                "risk_assessments": risk_assessments,
                "insights": [
                    f"위험도 평가를 완료했습니다.",
                    "고위험 거래처에 대한 모니터링을 강화하세요."
                ]
            }
            
        except Exception as e:
            logger.error(f"위험도 평가 실패: {str(e)}")
            return {"error": str(e)}
    
    async def get_mock_client_data(self) -> List[Dict[str, Any]]:
        """가상의 거래처 데이터 생성"""
        import random
        
        companies = [
            "삼성전자", "LG화학", "현대자동차", "SK하이닉스", "POSCO",
            "네이버", "카카오", "신세계", "롯데", "GS"
        ]
        
        client_data = []
        for i, company in enumerate(companies):
            revenue = random.randint(10000000, 200000000)  # 1천만~2억
            duration = random.randint(1, 10)  # 거래기간 1-10년
            
            client_data.append({
                "id": i + 1,
                "name": company,
                "annual_revenue": revenue,
                "transaction_frequency": random.randint(4, 24),
                "relationship_duration": duration,
                "payment_history": random.choice(["excellent", "good", "average", "poor"]),
                "growth_rate": random.uniform(-10, 30),
                "risk_factors": random.choice([
                    ["none"],
                    ["payment_delay"],
                    ["market_volatility"],
                    ["payment_delay", "market_volatility"]
                ])
            })
        
        return client_data
    
    async def calculate_performance_score(self, client_info: Dict[str, Any]) -> float:
        """거래처 성과 점수 계산"""
        score = 0
        weights = self.config.evaluation_metrics
        
        # 매출기여도 (0-100)
        revenue_contribution = min(client_info.get("annual_revenue", 0) / 1000000, 100)
        score += revenue_contribution * weights["매출기여도"]["weight"]
        
        # 수익성 (임의 계산)
        profitability = random.uniform(10, 30)  # 10-30%
        score += profitability * weights["수익성"]["weight"] * 3
        
        # 안정성
        payment_scores = {"excellent": 100, "good": 80, "average": 60, "poor": 30}
        stability = payment_scores.get(client_info.get("payment_history", "average"), 60)
        score += stability * weights["안정성"]["weight"]
        
        # 성장성
        growth_rate = max(0, client_info.get("growth_rate", 0))
        score += min(growth_rate * 2, 100) * weights["성장성"]["weight"]
        
        # 관계지속성
        duration_score = min(client_info.get("relationship_duration", 0) * 10, 100)
        score += duration_score * weights["관계지속성"]["weight"]
        
        return min(score, 100)
    
    async def calculate_risk_score(self, client_info: Dict[str, Any]) -> float:
        """위험도 점수 계산 (높을수록 위험)"""
        risk_score = 0
        
        # 결제 이력
        payment_risks = {"poor": 40, "average": 20, "good": 10, "excellent": 0}
        risk_score += payment_risks.get(client_info.get("payment_history", "average"), 20)
        
        # 위험 요소
        risk_factors = client_info.get("risk_factors", [])
        risk_score += len([f for f in risk_factors if f != "none"]) * 15
        
        # 성장률 (음수면 위험)
        growth_rate = client_info.get("growth_rate", 0)
        if growth_rate < 0:
            risk_score += abs(growth_rate)
        
        # 거래 빈도 (낮으면 위험)
        frequency = client_info.get("transaction_frequency", 12)
        if frequency < 6:
            risk_score += 20
        
        return min(risk_score, 100)
    
    def get_risk_level(self, risk_score: float) -> str:
        """위험도 레벨 결정"""
        if risk_score >= self.config.risk_thresholds["high_risk"]:
            return "high"
        elif risk_score >= self.config.risk_thresholds["medium_risk"]:
            return "medium"
        else:
            return "low"
    
    async def analyze_loyalty(self, target_client: str = None) -> Dict[str, Any]:
        """충성도 분석"""
        try:
            client_data = await self.get_mock_client_data()
            loyalty_assessments = []
            
            for client in client_data:
                if target_client and client["name"] != target_client:
                    continue
                
                loyalty_score = await self.calculate_loyalty_score(client)
                loyalty_level = self.get_loyalty_level(loyalty_score)
                
                loyalty_assessments.append({
                    "name": client["name"],
                    "loyalty_score": loyalty_score,
                    "loyalty_level": loyalty_level,
                    "relationship_duration": client.get("relationship_duration", 0)
                })
            
            return {
                "analysis_type": "loyalty_analysis",
                "target_client": target_client,
                "loyalty_assessments": loyalty_assessments,
                "insights": [
                    "고객 충성도 분석을 완료했습니다.",
                    "장기 관계 고객에 대한 유지 전략을 수립하세요."
                ]
            }
            
        except Exception as e:
            logger.error(f"충성도 분석 실패: {str(e)}")
            return {"error": str(e)}
    
    async def analyze_general_clients(self, analysis_type: str) -> Dict[str, Any]:
        """일반 거래처 분석"""
        try:
            # 기본적으로 거래처 성과 분석 수행
            return await self.analyze_client_performance()
            
        except Exception as e:
            logger.error(f"일반 거래처 분석 실패: {str(e)}")
            return {"error": str(e)}
    
    async def calculate_loyalty_score(self, client_info: Dict[str, Any]) -> float:
        """충성도 점수 계산"""
        score = 0
        
        # 거래 지속 기간 (최대 50점)
        duration = client_info.get("relationship_duration", 0)
        score += min(duration * 5, 50)
        
        # 거래 빈도 (최대 30점)
        frequency = client_info.get("transaction_frequency", 0)
        score += min(frequency * 2, 30)
        
        # 결제 이력 (최대 20점)
        payment_scores = {"excellent": 20, "good": 15, "average": 10, "poor": 5}
        score += payment_scores.get(client_info.get("payment_history", "average"), 10)
        
        return min(score, 100)
    
    def get_loyalty_level(self, loyalty_score: float) -> str:
        """충성도 레벨 결정"""
        if loyalty_score >= 80:
            return "high"
        elif loyalty_score >= 60:
            return "medium"
        else:
            return "low" 