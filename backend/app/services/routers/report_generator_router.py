"""
보고서 생성 라우터

보고서 생성 기능을 담당하는 라우터입니다.
"""

from typing import List, Dict, Any
import logging
from .base_router import BaseRouter, RouterContext, RouterResult, RouterAction

logger = logging.getLogger(__name__)

class ReportGeneratorRouter(BaseRouter):
    """보고서 생성 라우터"""
    
    def __init__(self):
        super().__init__("report_generator_router")
    
    def get_description(self) -> str:
        return "보고서 생성 기능을 제공합니다. 다양한 형태의 보고서를 자동으로 생성합니다."
    
    def get_keywords(self) -> List[str]:
        return [
            "보고서", "리포트", "report", "문서", "생성", "작성", "create", "generate",
            "document", "템플릿", "template", "양식", "format", "요약", "summary",
            "정리", "compilation", "월간", "주간", "연간", "업무", "프로젝트"
        ]
    
    def get_priority(self) -> int:
        return 4
    
    async def can_handle(self, context: RouterContext) -> float:
        """보고서 생성 라우터가 메시지를 처리할 수 있는지 확인"""
        message = context.current_message.lower()
        
        confidence = 0.0
        
        # 보고서 관련 키워드 확인
        report_patterns = ["보고서", "리포트", "report", "문서", "생성", "작성"]
        for pattern in report_patterns:
            if pattern in message:
                confidence += 0.3
        
        # 키워드 매칭
        keyword_matches = sum(1 for keyword in self.keywords if keyword in message)
        confidence += min(keyword_matches * 0.1, 0.4)
        
        return min(confidence, 1.0)
    
    async def process(self, context: RouterContext) -> RouterResult:
        """보고서 생성 처리 로직"""
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
            
            # 보고서 생성 요청 처리
            prompt = f"""
사용자가 보고서 생성을 요청했습니다.
요청 내용: {context.current_message}

보고서 작성 전문가로서 사용자의 요청을 분석하고, 어떤 종류의 보고서가 필요한지 파악해주세요.
보고서의 구조, 포함되어야 할 내용, 형식 등을 제안하고, 
실제 데이터가 필요한 경우 어떤 정보를 수집해야 하는지 안내해주세요.

보고서 생성 절차와 필요한 단계들을 순서대로 설명해주세요.
"""
            
            response = await self.generate_openai_response(prompt, context)
            
            # 결과 반환
            result = RouterResult(
                response=response,
                action=RouterAction.COMPLETE,
                confidence=0.8,
                sources=[],
                metadata={
                    "router_type": "report_generator",
                    "report_request": context.current_message
                }
            )
            
            await self.log_interaction(context, result)
            return result
            
        except Exception as e:
            logger.error(f"보고서 생성 처리 실패: {str(e)}")
            return RouterResult(
                response="죄송합니다. 보고서 생성 처리 중 오류가 발생했습니다. 다시 시도해 주세요.",
                action=RouterAction.ERROR,
                confidence=0.0,
                metadata={"error": str(e)}
            ) 