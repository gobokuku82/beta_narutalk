"""
간단한 AI 라우터 시스템
- 복잡한 LangGraph 구조를 단순화
- 핵심 라우팅 기능만 유지
- 관리하기 쉬운 구조
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..agents.base_agent import BaseAgent, AgentContext, AgentResult, AgentAction
from ..agents.document_search_agent import DocumentSearchAgent
from ..agents.document_draft_agent import DocumentDraftAgent
from ..agents.performance_analysis_agent import PerformanceAnalysisAgent
from ..agents.client_analysis_agent import ClientAnalysisAgent

logger = logging.getLogger(__name__)

@dataclass
class SimpleRouterResult:
    """라우터 처리 결과"""
    response: str
    agent_type: str
    confidence: float
    sources: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None


class SimpleRouter:
    """단순화된 AI 라우터"""
    
    def __init__(self):
        self.agents = {
            "search": DocumentSearchAgent(),
            "draft": DocumentDraftAgent(), 
            "performance": PerformanceAnalysisAgent(),
            "client": ClientAnalysisAgent()
        }
        logger.info("간단한 라우터 초기화 완료")
    
    def set_agent_services(self, **services):
        """모든 에이전트에 서비스 설정"""
        for agent in self.agents.values():
            agent.set_services(**services)
        logger.info("에이전트 서비스 설정 완료")
    
    def _classify_intent(self, message: str) -> tuple[str, float]:
        """의도 분류 - 단순하고 명확한 규칙"""
        message_lower = message.lower()
        
        # 우선순위 기반 분류 (명확한 것부터)
        
        # 1. 실적/성과 분석 (가장 구체적)
        if any(word in message_lower for word in ["실적", "성과", "매출", "수익", "kpi", "분석"]):
            return "performance", 0.9
            
        # 2. 거래처/고객 분석
        if any(word in message_lower for word in ["거래처", "고객", "클라이언트", "파트너", "업체"]):
            return "client", 0.9
            
        # 3. 문서 작성 (능동적 동작)
        if any(word in message_lower for word in ["작성", "만들어", "생성", "초안", "보고서", "제안서"]):
            return "draft", 0.8
            
        # 4. 문서 검색 (기본값)
        return "search", 0.7
    
    async def process_message(self, 
                            message: str,
                            user_id: str,
                            session_id: str,
                            conversation_history: List[Dict[str, str]] = None,
                            user_preferences: Dict[str, Any] = None) -> SimpleRouterResult:
        """메시지 처리"""
        try:
            # 의도 분류
            agent_type, confidence = self._classify_intent(message)
            
            # 컨텍스트 생성
            context = AgentContext(
                current_message=message,
                user_id=user_id,
                session_id=session_id,
                conversation_history=conversation_history or [],
                current_agent=agent_type,
                agent_switches=0,
                user_preferences=user_preferences or {}
            )
            
            # 에이전트 실행
            agent = self.agents[agent_type]
            result = await agent.process(context)
            
            # 결과 반환
            return SimpleRouterResult(
                response=result.response,
                agent_type=agent_type,
                confidence=confidence,
                sources=result.sources or [],
                metadata=result.metadata or {}
            )
            
        except Exception as e:
            logger.error(f"라우터 처리 실패: {str(e)}")
            return SimpleRouterResult(
                response=f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}",
                agent_type="error",
                confidence=0.0,
                sources=[],
                metadata={"error": str(e)}
            )
    
    def get_available_agents(self) -> List[str]:
        """사용 가능한 에이전트 목록"""
        return list(self.agents.keys())
    
    def get_router_info(self) -> Dict[str, Any]:
        """라우터 정보"""
        return {
            "total_agents": len(self.agents),
            "agent_types": list(self.agents.keys()),
            "classification_rules": {
                "performance": ["실적", "성과", "매출", "수익", "kpi", "분석"],
                "client": ["거래처", "고객", "클라이언트", "파트너", "업체"],
                "draft": ["작성", "만들어", "생성", "초안", "보고서", "제안서"],
                "search": ["기본값 - 문서 검색"]
            }
        }


# 전역 라우터 인스턴스
simple_router = SimpleRouter() 