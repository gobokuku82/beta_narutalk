"""
직원 정보 라우터

직원 정보 조회 기능을 담당하는 라우터입니다.
"""

from typing import List, Dict, Any
import logging
from .base_router import BaseRouter, RouterContext, RouterResult, RouterAction

logger = logging.getLogger(__name__)

class EmployeeInfoRouter(BaseRouter):
    """직원 정보 라우터"""
    
    def __init__(self):
        super().__init__("employee_info_router")
    
    def get_description(self) -> str:
        return "직원 정보 조회 기능을 제공합니다. 직원의 연락처, 부서, 직책 등을 검색할 수 있습니다."
    
    def get_keywords(self) -> List[str]:
        return [
            "직원", "사원", "동료", "부서", "팀", "연락처", "전화", "이메일", "employee",
            "staff", "team", "department", "contact", "phone", "email", "담당자",
            "관리자", "상사", "팀장", "대표", "임원", "조직도", "인사", "HR"
        ]
    
    def get_priority(self) -> int:
        return 6
    
    async def can_handle(self, context: RouterContext) -> float:
        """직원 정보 라우터가 메시지를 처리할 수 있는지 확인"""
        message = context.current_message.lower()
        
        confidence = 0.0
        
        # 직원 관련 키워드 확인
        employee_patterns = ["직원", "사원", "동료", "employee", "staff", "담당자"]
        for pattern in employee_patterns:
            if pattern in message:
                confidence += 0.3
        
        # 조직 관련 키워드 확인
        org_patterns = ["부서", "팀", "department", "team", "조직", "관리자"]
        for pattern in org_patterns:
            if pattern in message:
                confidence += 0.2
        
        # 키워드 매칭
        keyword_matches = sum(1 for keyword in self.keywords if keyword in message)
        confidence += min(keyword_matches * 0.1, 0.4)
        
        return min(confidence, 1.0)
    
    async def process(self, context: RouterContext) -> RouterResult:
        """직원 정보 처리 로직"""
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
            
            # 직원 정보 검색 (데이터베이스 사용)
            employee_data = None
            if self.database_service:
                try:
                    employee_data = await self.database_service.search_employee_info(
                        context.current_message
                    )
                except Exception as e:
                    logger.error(f"직원 정보 검색 실패: {str(e)}")
            
            # 응답 생성
            if employee_data:
                prompt = f"""
직원 정보 검색 결과를 사용자에게 친근하게 제공해주세요.

검색 키워드: {context.current_message}
검색 결과: {employee_data}

직원의 정보를 정리해서 보기 좋게 제공하고, 개인정보 보호를 위해 민감한 정보는 적절히 처리해주세요.
"""
                response = await self.generate_openai_response(prompt, context)
            else:
                response = "해당 직원 정보를 찾을 수 없습니다. 다른 검색어로 시도해보시거나, 정확한 이름이나 부서명을 입력해주세요."
            
            # 결과 반환
            result = RouterResult(
                response=response,
                action=RouterAction.COMPLETE,
                confidence=0.8,
                sources=[],
                metadata={
                    "router_type": "employee_info",
                    "search_query": context.current_message,
                    "employee_found": bool(employee_data)
                }
            )
            
            await self.log_interaction(context, result)
            return result
            
        except Exception as e:
            logger.error(f"직원 정보 처리 실패: {str(e)}")
            return RouterResult(
                response="죄송합니다. 직원 정보 검색 중 오류가 발생했습니다. 다시 시도해 주세요.",
                action=RouterAction.ERROR,
                confidence=0.0,
                metadata={"error": str(e)}
            ) 