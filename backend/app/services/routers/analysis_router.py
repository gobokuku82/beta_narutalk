"""
분석 라우터

데이터 분석 기능을 담당하는 라우터입니다.
"""

from typing import List, Dict, Any
import logging
from .base_router import BaseRouter, RouterContext, RouterResult, RouterAction

logger = logging.getLogger(__name__)

class AnalysisRouter(BaseRouter):
    """분석 라우터"""
    
    def __init__(self):
        super().__init__("analysis_router")
    
    def get_description(self) -> str:
        return "데이터 분석 기능을 제공합니다. 통계, 트렌드, 패턴 분석 등을 수행합니다."
    
    def get_keywords(self) -> List[str]:
        return [
            "분석", "통계", "데이터", "차트", "그래프", "트렌드", "패턴", "analysis",
            "statistics", "data", "chart", "graph", "trend", "pattern", "리포트",
            "보고서", "report", "dashboard", "대시보드", "metrics", "지표", "성과"
        ]
    
    def get_priority(self) -> int:
        return 5
    
    async def can_handle(self, context: RouterContext) -> float:
        """분석 라우터가 메시지를 처리할 수 있는지 확인"""
        message = context.current_message.lower()
        
        confidence = 0.0
        
        # 분석 관련 키워드 확인
        analysis_patterns = ["분석", "통계", "analysis", "statistics", "데이터", "data"]
        for pattern in analysis_patterns:
            if pattern in message:
                confidence += 0.3
        
        # 키워드 매칭
        keyword_matches = sum(1 for keyword in self.keywords if keyword in message)
        confidence += min(keyword_matches * 0.1, 0.4)
        
        return min(confidence, 1.0)
    
    async def process(self, context: RouterContext) -> RouterResult:
        """분석 처리 로직"""
        try:
            # 다른 라우터로 전환 확인
            next_router = await self.should_switch_router(context)
            if next_router:
                return RouterResult(
                    response=f"{next_router.replace('_', ' ').title()}로 전환합니다.",
                    action=RouterAction.SWITCH,
                    next_router=next_router,
                    confidence=0.9
                )
            
            # 분석 요청 처리
            prompt = f"""
사용자가 분석을 요청했습니다. 
요청 내용: {context.current_message}

데이터 분석 전문가로서 사용자의 요청을 이해하고, 어떤 종류의 분석이 필요한지 설명해주세요.
실제 데이터가 있다면 분석 방법과 절차를 안내하고, 데이터가 없다면 필요한 데이터와 수집 방법을 제안해주세요.
"""
            
            response = await self.generate_openai_response(prompt, context)
            
            # 결과 반환
            result = RouterResult(
                response=response,
                action=RouterAction.COMPLETE,
                confidence=0.8,
                sources=[],
                metadata={
                    "router_type": "analysis",
                    "analysis_request": context.current_message
                }
            )
            
            await self.log_interaction(context, result)
            return result
            
        except Exception as e:
            logger.error(f"분석 처리 실패: {str(e)}")
            return RouterResult(
                response="죄송합니다. 분석 처리 중 오류가 발생했습니다. 다시 시도해 주세요.",
                action=RouterAction.ERROR,
                confidence=0.0,
                metadata={"error": str(e)}
            ) 