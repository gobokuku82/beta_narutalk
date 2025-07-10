"""
거래처분석 에이전트

고객, 파트너, 거래처 데이터를 분석하는 전문 에이전트입니다.
관계 관리와 비즈니스 인사이트를 제공합니다.
"""

from typing import List, Dict, Any, Optional
import logging
from ..base_agent import BaseAgent, AgentContext, AgentResult, AgentAction
from .config import ClientAnalysisConfig, default_config
from .analyzer import ClientAnalyzer

logger = logging.getLogger(__name__)

class ClientAnalysisAgent(BaseAgent):
    """거래처분석 전문 에이전트"""
    
    def __init__(self, config: ClientAnalysisConfig = None):
        super().__init__("client_analysis_agent")
        self.config = config or default_config
        self.analyzer = ClientAnalyzer(self.config)
        
    def set_services(self, **services):
        """서비스 의존성 주입"""
        super().set_services(**services)
        self.analyzer.set_services(**services)
    
    @property
    def description(self) -> str:
        return "고객, 파트너, 거래처 데이터를 분석하는 전문 에이전트입니다. 고객 세분화, 관계 분석, 위험도 평가를 통해 비즈니스 인사이트를 제공합니다."
    
    @property
    def keywords(self) -> List[str]:
        return [
            # 한국어 키워드
            "거래처", "고객", "클라이언트", "파트너", "업체",
            "분석", "세분화", "평가", "관계", "관리",
            "위험도", "신용", "신뢰도", "안정성",
            "충성도", "만족도", "이탈", "retention",
            "매출기여", "수익성", "성장잠재력",
            "거래패턴", "구매행동", "계약", "협력",
            
            # 영어 키워드
            "client", "customer", "partner", "vendor",
            "analysis", "segmentation", "evaluation", "assessment",
            "relationship", "risk", "loyalty", "retention",
            "profitability", "performance", "behavior"
        ]
    
    @property
    def priority(self) -> int:
        return 7  # 높은 우선순위
    
    @property
    def supported_tasks(self) -> List[str]:
        return [
            "client_analysis",          # 거래처 분석
            "customer_segmentation",    # 고객 세분화
            "client_performance",       # 거래처 성과
            "relationship_analysis",    # 관계 분석
            "risk_assessment",         # 위험도 평가
            "loyalty_analysis",        # 충성도 분석
            "growth_potential",        # 성장 잠재력
            "transaction_pattern",     # 거래 패턴
            "profitability_analysis"   # 수익성 분석
        ]
    
    async def can_handle(self, context: AgentContext) -> float:
        """메시지를 처리할 수 있는지 신뢰도 반환"""
        message = context.current_message.lower()
        confidence = 0.0
        
        # 거래처/고객 관련 키워드 확인
        client_indicators = ["거래처", "고객", "클라이언트", "파트너", "업체", "client", "customer"]
        for indicator in client_indicators:
            if indicator in message:
                confidence += 0.4
                break
        
        # 분석 의도 확인
        analysis_indicators = ["분석", "평가", "세분화", "관리", "analysis", "evaluation"]
        for indicator in analysis_indicators:
            if indicator in message:
                confidence += 0.3
                break
        
        # 키워드 매칭
        keyword_matches = sum(1 for keyword in self.keywords if keyword in message)
        confidence += min(keyword_matches * 0.05, 0.3)
        
        return min(confidence, 1.0)
    
    async def process(self, context: AgentContext) -> AgentResult:
        """거래처분석 처리 메인 로직"""
        try:
            # 다른 에이전트로 전환 확인
            next_agent = await self.should_switch_agent(context)
            if next_agent:
                return AgentResult(
                    response=f"{next_agent.replace('_', ' ').title()}로 전환합니다.",
                    action=AgentAction.SWITCH,
                    next_agent=next_agent,
                    confidence=0.9
                )
            
            # 분석 유형 및 파라미터 추출
            analysis_type = await self.analyze_request_type(context)
            target_client = await self.extract_target_client(context)
            criteria = await self.extract_criteria(context)
            
            # 거래처 분석 실행
            analysis_result = await self.analyzer.analyze_clients(
                analysis_type=analysis_type,
                target_client=target_client,
                criteria=criteria
            )
            
            # 분석 결과 응답 생성
            response = await self.generate_analysis_response(context, analysis_result, analysis_type)
            
            # 결과 반환
            result = AgentResult(
                response=response,
                action=AgentAction.COMPLETE,
                confidence=0.9,
                sources=[analysis_result],
                metadata={
                    "agent_type": "client_analysis",
                    "analysis_type": analysis_type,
                    "target_client": target_client,
                    "criteria": criteria,
                    "query": context.current_message
                }
            )
            
            await self.log_interaction(context, result)
            return result
            
        except Exception as e:
            logger.error(f"거래처분석 처리 실패: {str(e)}")
            return AgentResult(
                response="죄송합니다. 거래처 분석 중 오류가 발생했습니다. 다시 시도해 주세요.",
                action=AgentAction.ERROR,
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def analyze_request_type(self, context: AgentContext) -> str:
        """요청 유형 분석"""
        message = context.current_message.lower()
        
        type_keywords = {
            "customer_segmentation": ["세분화", "그룹", "분류", "segmentation"],
            "client_performance": ["성과", "평가", "실적", "performance"],
            "risk_assessment": ["위험", "신용", "안정성", "risk"],
            "loyalty_analysis": ["충성도", "이탈", "retention", "loyalty"],
            "profitability_analysis": ["수익성", "profit", "수익"],
            "relationship_analysis": ["관계", "관리", "relationship"]
        }
        
        for analysis_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    return analysis_type
        
        return "client_performance"  # 기본값
    
    async def extract_target_client(self, context: AgentContext) -> Optional[str]:
        """대상 거래처 추출"""
        message = context.current_message
        
        # 간단한 회사명 패턴 매칭
        common_companies = ["삼성", "LG", "현대", "SK", "POSCO", "네이버", "카카오"]
        for company in common_companies:
            if company in message:
                return company
        
        return None
    
    async def extract_criteria(self, context: AgentContext) -> Optional[str]:
        """분석 기준 추출"""
        message = context.current_message.lower()
        
        criteria_keywords = {
            "거래규모": ["규모", "크기", "size"],
            "거래빈도": ["빈도", "frequency"],
            "지역": ["지역", "location", "region"]
        }
        
        for criteria, keywords in criteria_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    return criteria
        
        return None
    
    async def generate_analysis_response(self, context: AgentContext, analysis_result: Dict[str, Any], 
                                       analysis_type: str) -> str:
        """분석 결과 응답 생성"""
        try:
            if "error" in analysis_result:
                return f"분석 중 오류가 발생했습니다: {analysis_result['error']}"
            
            # OpenAI를 사용한 상세 응답 생성
            if self.openai_client:
                prompt = f"""
사용자가 거래처 분석을 요청했습니다.

사용자 질문: {context.current_message}
분석 유형: {analysis_type}
분석 결과: {self._format_analysis_for_prompt(analysis_result)}

분석 결과를 바탕으로 다음 내용을 포함한 거래처 분석 보고서를 작성해주세요:
1. 핵심 분석 결과 요약
2. 주요 인사이트 및 특징
3. 비즈니스 관점의 해석
4. 관계 관리 및 개선 방안

좋은제약 회사의 영업/마케팅 담당자 관점에서 작성해주세요.
"""
                return await self.generate_openai_response(prompt, context)
            
            # 기본 응답 생성
            response = f"🏢 **{self.get_analysis_type_name(analysis_type)} 결과**\n\n"
            
            # 분석 유형별 응답 생성
            if analysis_type == "customer_segmentation":
                segments = analysis_result.get("segments", {})
                response += f"📊 고객 세분화 결과 ({len(segments)}개 그룹):\n"
                for segment, clients in segments.items():
                    response += f"• {segment}: {len(clients)}개 거래처\n"
                response += "\n"
                
            elif analysis_type == "client_performance":
                if analysis_result.get("target_client"):
                    score = analysis_result.get("performance_score", 0)
                    response += f"📈 {analysis_result['target_client']} 성과 점수: {score:.1f}/100점\n\n"
                else:
                    top_performers = analysis_result.get("top_performers", [])
                    response += "🏆 상위 성과 거래처:\n"
                    for i, performer in enumerate(top_performers[:3], 1):
                        response += f"{i}. {performer['name']} ({performer['score']:.1f}점)\n"
                    response += "\n"
                    
            elif analysis_type == "risk_assessment":
                risk_assessments = analysis_result.get("risk_assessments", [])
                if risk_assessments:
                    response += "⚠️ 위험도 평가 결과:\n"
                    for assessment in risk_assessments[:5]:
                        level_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                        emoji = level_emoji.get(assessment["risk_level"], "⚪")
                        response += f"{emoji} {assessment['name']}: {assessment['risk_level']} 위험\n"
                    response += "\n"
            
            # 주요 인사이트
            insights = analysis_result.get("insights", [])
            if insights:
                response += "💡 **주요 인사이트:**\n"
                for insight in insights:
                    response += f"• {insight}\n"
                response += "\n"
            
            # 추천사항
            recommendations = analysis_result.get("recommendations", [])
            if recommendations:
                response += "🎯 **추천사항:**\n"
                for recommendation in recommendations:
                    response += f"• {recommendation}\n"
                response += "\n"
            
            response += "추가 분석이나 특정 거래처에 대한 상세 정보가 필요하시면 말씀해주세요."
            
            return response
            
        except Exception as e:
            logger.error(f"분석 응답 생성 실패: {str(e)}")
            return f"분석 결과를 처리하는 중 오류가 발생했습니다: {str(e)}"
    
    def _format_analysis_for_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """OpenAI 프롬프트용 분석 결과 포맷팅"""
        formatted = f"분석 유형: {analysis_result.get('analysis_type', 'unknown')}\n"
        
        if analysis_result.get("segments"):
            formatted += f"세그먼트 수: {len(analysis_result['segments'])}\n"
        
        if analysis_result.get("performance_score"):
            formatted += f"성과 점수: {analysis_result['performance_score']:.1f}/100\n"
        
        if analysis_result.get("insights"):
            formatted += f"인사이트: {', '.join(analysis_result['insights'])}\n"
        
        return formatted
    
    def get_analysis_type_name(self, analysis_type: str) -> str:
        """분석 유형 한국어 이름 반환"""
        type_names = {
            "customer_segmentation": "고객 세분화 분석",
            "client_performance": "거래처 성과 분석",
            "risk_assessment": "위험도 평가",
            "loyalty_analysis": "고객 충성도 분석",
            "profitability_analysis": "수익성 분석",
            "relationship_analysis": "관계 분석"
        }
        return type_names.get(analysis_type, "거래처 분석")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """에이전트 상태 정보"""
        return {
            **self.get_agent_info(),
            "config": {
                "confidence_threshold": self.config.confidence_threshold
            },
            "supported_analysis_types": self.config.supported_analysis_types,
            "segmentation_criteria": list(self.config.segmentation_criteria.keys()),
            "evaluation_metrics": list(self.config.evaluation_metrics.keys()),
            "data_sources": self.config.data_sources
        } 