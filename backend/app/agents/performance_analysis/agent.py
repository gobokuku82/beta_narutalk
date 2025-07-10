"""
실적분석 에이전트

매출, 수익성, KPI 등 성과 데이터를 분석하는 전문 에이전트입니다.
데이터 기반 인사이트와 예측을 제공하여 의사결정을 지원합니다.
"""

from typing import List, Dict, Any, Optional
import logging
from ..base_agent import BaseAgent, AgentContext, AgentResult, AgentAction
from .config import PerformanceAnalysisConfig, default_config
from .analyzer import PerformanceAnalyzer

logger = logging.getLogger(__name__)

class PerformanceAnalysisAgent(BaseAgent):
    """실적분석 전문 에이전트"""
    
    def __init__(self, config: PerformanceAnalysisConfig = None):
        super().__init__("performance_analysis_agent")
        self.config = config or default_config
        self.analyzer = PerformanceAnalyzer(self.config)
        
    def set_services(self, **services):
        """서비스 의존성 주입"""
        super().set_services(**services)
        self.analyzer.set_services(**services)
    
    @property
    def description(self) -> str:
        return "매출, 수익성, KPI 등 성과 데이터를 분석하는 전문 에이전트입니다. 트렌드 분석, 예측, 인사이트 제공을 통해 의사결정을 지원합니다."
    
    @property
    def keywords(self) -> List[str]:
        return [
            # 한국어 키워드
            "실적", "성과", "매출", "수익", "이익", "분석",
            "KPI", "지표", "성장률", "트렌드", "추세",
            "매출액", "순이익", "영업이익", "수익률",
            "비교", "대비", "증가", "감소", "변화",
            "월별", "분기별", "연도별", "기간별",
            "목표", "달성", "성취", "평가", "측정",
            
            # 영어 키워드  
            "performance", "sales", "revenue", "profit", "growth",
            "kpi", "metrics", "analysis", "trend", "increase",
            "decrease", "compare", "target", "achievement",
            "monthly", "quarterly", "yearly", "roi"
        ]
    
    @property
    def priority(self) -> int:
        return 8  # 높은 우선순위 (실적 분석은 중요한 기능)
    
    @property
    def supported_tasks(self) -> List[str]:
        return [
            "performance_analysis",     # 성과 분석
            "sales_analysis",          # 매출 분석
            "profit_analysis",         # 수익성 분석
            "growth_analysis",         # 성장률 분석
            "trend_analysis",          # 트렌드 분석
            "kpi_analysis",           # KPI 분석
            "comparative_analysis",    # 비교 분석
            "forecast_analysis",       # 예측 분석
            "period_analysis"         # 기간별 분석
        ]
    
    async def can_handle(self, context: AgentContext) -> float:
        """메시지를 처리할 수 있는지 신뢰도 반환"""
        message = context.current_message.lower()
        confidence = 0.0
        
        # 실적/성과 분석 의도 확인
        analysis_indicators = ["분석", "실적", "성과", "매출", "수익", "analysis", "performance"]
        for indicator in analysis_indicators:
            if indicator in message:
                confidence += 0.4
                break
        
        # 숫자/데이터 관련 키워드 확인
        data_indicators = ["트렌드", "증가", "감소", "비교", "대비", "growth", "trend", "compare"]
        for indicator in data_indicators:
            if indicator in message:
                confidence += 0.3
                break
        
        # 키워드 매칭
        keyword_matches = sum(1 for keyword in self.keywords if keyword in message)
        confidence += min(keyword_matches * 0.05, 0.3)
        
        # 기간 관련 키워드
        period_indicators = ["월별", "분기별", "연도별", "monthly", "quarterly", "yearly"]
        for indicator in period_indicators:
            if indicator in message:
                confidence += 0.1
                break
        
        return min(confidence, 1.0)
    
    async def process(self, context: AgentContext) -> AgentResult:
        """실적분석 처리 메인 로직"""
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
            period = await self.extract_analysis_period(context)
            target_kpi = await self.extract_target_kpi(context)
            
            # 실적 분석 실행
            analysis_result = await self.analyzer.analyze_performance(
                analysis_type=analysis_type,
                period=period,
                target_kpi=target_kpi
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
                    "agent_type": "performance_analysis",
                    "analysis_type": analysis_type,
                    "period": period,
                    "target_kpi": target_kpi,
                    "query": context.current_message
                }
            )
            
            await self.log_interaction(context, result)
            return result
            
        except Exception as e:
            logger.error(f"실적분석 처리 실패: {str(e)}")
            return AgentResult(
                response="죄송합니다. 실적 분석 중 오류가 발생했습니다. 다시 시도해 주세요.",
                action=AgentAction.ERROR,
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def analyze_request_type(self, context: AgentContext) -> str:
        """요청 유형 분석"""
        message = context.current_message.lower()
        
        # 분석 유형별 키워드 매핑
        type_keywords = {
            "sales_analysis": ["매출", "sales", "revenue"],
            "profit_analysis": ["수익", "이익", "profit", "margin"],
            "growth_analysis": ["성장", "증가", "growth"],
            "trend_analysis": ["트렌드", "추세", "변화", "trend"],
            "kpi_analysis": ["kpi", "지표", "성과", "metrics"],
            "comparative_analysis": ["비교", "대비", "compare"],
            "forecast_analysis": ["예측", "전망", "forecast"],
            "period_analysis": ["기간", "월별", "분기", "period"]
        }
        
        for analysis_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    return analysis_type
        
        return "sales_analysis"  # 기본값
    
    async def extract_analysis_period(self, context: AgentContext) -> str:
        """분석 기간 추출"""
        message = context.current_message.lower()
        
        period_keywords = {
            "daily": ["일별", "daily"],
            "weekly": ["주별", "weekly"],
            "monthly": ["월별", "monthly"],
            "quarterly": ["분기별", "quarterly"],
            "yearly": ["연별", "연도별", "yearly", "annual"]
        }
        
        for period, keywords in period_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    return period
        
        return self.config.default_analysis_period
    
    async def extract_target_kpi(self, context: AgentContext) -> Optional[str]:
        """대상 KPI 추출"""
        message = context.current_message.lower()
        
        for kpi_name in self.config.kpi_definitions.keys():
            if kpi_name.lower() in message:
                return kpi_name
        
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
사용자가 실적 분석을 요청했습니다.

사용자 질문: {context.current_message}
분석 유형: {analysis_type}
분석 결과: {self._format_analysis_for_prompt(analysis_result)}

분석 결과를 바탕으로 다음 내용을 포함한 전문적인 분석 보고서를 작성해주세요:
1. 핵심 지표와 수치
2. 주요 인사이트 및 트렌드
3. 성과 평가 및 해석
4. 개선 방안 및 추천사항

좋은제약 회사의 실적 분석 담당자 관점에서 작성해주세요.
"""
                return await self.generate_openai_response(prompt, context)
            
            # 기본 응답 생성
            response = f"📊 **{self.get_analysis_type_name(analysis_type)} 결과**\n\n"
            
            # 기간 정보
            if analysis_result.get("period"):
                response += f"📅 분석 기간: {analysis_result['period']}\n"
            
            # 핵심 지표
            if analysis_result.get("growth_rate") is not None:
                response += f"📈 성장률: {analysis_result['growth_rate']:.2f}%\n"
            
            if analysis_result.get("profit_margin") is not None:
                response += f"💰 수익률: {analysis_result['profit_margin']:.2f}%\n"
            
            if analysis_result.get("average_sales"):
                response += f"💵 평균 매출: {analysis_result['average_sales']:,.0f}원\n"
            
            # 성과 평가
            performance_rating = analysis_result.get("performance_rating", "average")
            rating_emoji = {"excellent": "🟢", "good": "🔵", "average": "🟡", "poor": "🔴"}
            response += f"\n{rating_emoji.get(performance_rating, '⚪')} **성과 평가: {performance_rating.upper()}**\n\n"
            
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
            
            # KPI 결과 (KPI 분석인 경우)
            if analysis_type == "kpi_analysis" and analysis_result.get("kpi_results"):
                response += "📋 **KPI 상세 결과:**\n"
                for kpi_name, kpi_result in analysis_result["kpi_results"].items():
                    score = kpi_result.get("score", 0)
                    level = kpi_result.get("performance_level", "unknown")
                    response += f"• {kpi_name}: {score:.1f}점 ({level})\n"
                response += "\n"
            
            response += "더 자세한 분석이나 다른 기간의 데이터가 필요하시면 말씀해주세요."
            
            return response
            
        except Exception as e:
            logger.error(f"분석 응답 생성 실패: {str(e)}")
            return f"분석 결과를 처리하는 중 오류가 발생했습니다: {str(e)}"
    
    def _format_analysis_for_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """OpenAI 프롬프트용 분석 결과 포맷팅"""
        formatted = f"분석 유형: {analysis_result.get('analysis_type', 'unknown')}\n"
        
        if analysis_result.get("growth_rate") is not None:
            formatted += f"성장률: {analysis_result['growth_rate']:.2f}%\n"
        
        if analysis_result.get("profit_margin") is not None:
            formatted += f"수익률: {analysis_result['profit_margin']:.2f}%\n"
        
        if analysis_result.get("performance_rating"):
            formatted += f"성과 평가: {analysis_result['performance_rating']}\n"
        
        if analysis_result.get("insights"):
            formatted += f"인사이트: {', '.join(analysis_result['insights'])}\n"
        
        return formatted
    
    def get_analysis_type_name(self, analysis_type: str) -> str:
        """분석 유형 한국어 이름 반환"""
        type_names = {
            "sales_analysis": "매출 분석",
            "profit_analysis": "수익성 분석", 
            "growth_analysis": "성장률 분석",
            "trend_analysis": "트렌드 분석",
            "kpi_analysis": "KPI 분석",
            "comparative_analysis": "비교 분석",
            "forecast_analysis": "예측 분석",
            "period_analysis": "기간별 분석"
        }
        return type_names.get(analysis_type, "실적 분석")
    
    async def get_analysis_suggestions(self, context: AgentContext) -> List[str]:
        """분석 제안사항 생성"""
        suggestions = [
            "월별 매출 분석 해주세요",
            "수익률 트렌드 분석해주세요", 
            "올해 성장률 분석 부탁드립니다",
            "KPI 달성도 분석해주세요",
            "분기별 실적 비교 분석해주세요"
        ]
        return suggestions
    
    def get_agent_status(self) -> Dict[str, Any]:
        """에이전트 상태 정보"""
        return {
            **self.get_agent_info(),
            "config": {
                "default_period": self.config.default_analysis_period,
                "max_historical_months": self.config.max_historical_months,
                "confidence_threshold": self.config.confidence_threshold
            },
            "supported_analysis_types": self.config.supported_analysis_types,
            "kpi_definitions": list(self.config.kpi_definitions.keys()),
            "performance_thresholds": self.config.performance_thresholds,
            "data_sources": self.config.data_sources
        } 