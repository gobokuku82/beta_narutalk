"""
라우터 매니저

모든 라우터를 관리하고 적절한 라우터를 선택하여 메시지를 처리하는 중앙 관리자입니다.
확장 가능한 아키텍처를 제공하며, 라우터 간 전환을 지원합니다.
"""

from typing import Dict, List, Optional, Any
import logging
from openai import AsyncOpenAI
from ..core.config import settings
from .routers.base_router import BaseRouter, RouterContext, RouterResult, RouterAction
from .routers.qa_router import QARouter
from .routers.document_search_router import DocumentSearchRouter
from .routers.employee_info_router import EmployeeInfoRouter
from .routers.general_chat_router import GeneralChatRouter
from .routers.analysis_router import AnalysisRouter
from .routers.report_generator_router import ReportGeneratorRouter

logger = logging.getLogger(__name__)

class RouterManager:
    """라우터 매니저 클래스"""
    
    def __init__(self, embedding_service=None, database_service=None):
        self.embedding_service = embedding_service
        self.database_service = database_service
        self.routers: Dict[str, BaseRouter] = {}
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        self.openai_client = None
        
        # OpenAI 클라이언트 초기화
        self._init_openai_client()
        
        # 라우터 초기화
        self._init_routers()
        
        logger.info("라우터 매니저 초기화 완료")
    
    def _init_openai_client(self):
        """OpenAI 클라이언트 초기화"""
        try:
            if settings.openai_api_key:
                self.openai_client = AsyncOpenAI(
                    api_key=settings.openai_api_key,
                    timeout=settings.openai_timeout
                )
                logger.info("OpenAI 클라이언트 초기화 완료")
            else:
                logger.warning("OpenAI API 키가 설정되지 않았습니다.")
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {str(e)}")
    
    def _init_routers(self):
        """모든 라우터 초기화"""
        router_classes = [
            QARouter,
            DocumentSearchRouter,
            EmployeeInfoRouter,
            GeneralChatRouter,
            AnalysisRouter,
            ReportGeneratorRouter
        ]
        
        for router_class in router_classes:
            try:
                router = router_class()
                router.set_services(
                    openai_client=self.openai_client,
                    embedding_service=self.embedding_service,
                    database_service=self.database_service
                )
                self.routers[router.router_name] = router
                logger.info(f"라우터 등록: {router.router_name}")
            except Exception as e:
                logger.error(f"라우터 초기화 실패 ({router_class.__name__}): {str(e)}")
    
    def add_router(self, router: BaseRouter):
        """새로운 라우터 추가"""
        try:
            router.set_services(
                openai_client=self.openai_client,
                embedding_service=self.embedding_service,
                database_service=self.database_service
            )
            self.routers[router.router_name] = router
            logger.info(f"라우터 동적 추가: {router.router_name}")
        except Exception as e:
            logger.error(f"라우터 추가 실패: {str(e)}")
    
    def remove_router(self, router_name: str):
        """라우터 제거"""
        if router_name in self.routers:
            del self.routers[router_name]
            logger.info(f"라우터 제거: {router_name}")
    
    def get_available_routers(self) -> List[Dict[str, Any]]:
        """사용 가능한 라우터 목록 반환"""
        return [
            {
                "name": router.router_name,
                "description": router.description,
                "keywords": router.keywords,
                "priority": router.priority
            }
            for router in self.routers.values()
        ]
    
    async def select_router(self, context: RouterContext) -> Optional[BaseRouter]:
        """최적의 라우터 선택"""
        best_router = None
        best_confidence = 0.0
        
        # 모든 라우터의 신뢰도 계산
        router_scores = []
        for router in self.routers.values():
            try:
                confidence = await router.can_handle(context)
                router_scores.append({
                    "router": router,
                    "confidence": confidence,
                    "priority": router.priority
                })
            except Exception as e:
                logger.error(f"라우터 신뢰도 계산 실패 ({router.router_name}): {str(e)}")
        
        # 신뢰도와 우선순위를 고려하여 최적 라우터 선택
        if router_scores:
            # 신뢰도 임계값 이상인 라우터들 필터링
            valid_routers = [
                score for score in router_scores 
                if score["confidence"] >= settings.router_confidence_threshold
            ]
            
            if valid_routers:
                # 신뢰도와 우선순위를 고려한 가중치 계산
                for score in valid_routers:
                    score["weighted_score"] = (
                        score["confidence"] * 0.7 + 
                        (score["priority"] / 10) * 0.3
                    )
                
                # 가중치가 가장 높은 라우터 선택
                best_score = max(valid_routers, key=lambda x: x["weighted_score"])
                best_router = best_score["router"]
                best_confidence = best_score["confidence"]
                
                logger.info(f"라우터 선택: {best_router.router_name} (신뢰도: {best_confidence:.2f})")
            else:
                # 신뢰도가 낮은 경우 일반 대화 라우터 선택
                if "general_chat_router" in self.routers:
                    best_router = self.routers["general_chat_router"]
                    best_confidence = 0.5
                    logger.info("기본 라우터 선택: general_chat_router")
        
        return best_router
    
    async def process_message(self, message: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """메시지 처리 메인 함수"""
        try:
            # 대화 기록 관리
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []
            
            # 사용자 환경설정 로드
            user_prefs = self.user_preferences.get(user_id, {})
            
            # 라우터 컨텍스트 생성
            context = RouterContext(
                current_message=message,
                user_id=user_id,
                session_id=session_id,
                conversation_history=self.conversation_history[session_id],
                current_router="",
                router_switches=0,
                user_preferences=user_prefs
            )
            
            # 라우터 선택 및 처리
            result = await self._process_with_router_switching(context)
            
            # 대화 기록 업데이트
            self.conversation_history[session_id].append({
                "user": message,
                "assistant": result["response"],
                "router": result.get("router_type", "unknown"),
                "timestamp": str(context.current_router)
            })
            
            # 기록 크기 제한 (최근 50개만 유지)
            if len(self.conversation_history[session_id]) > 50:
                self.conversation_history[session_id] = self.conversation_history[session_id][-50:]
            
            return result
            
        except Exception as e:
            logger.error(f"메시지 처리 실패: {str(e)}")
            return {
                "response": "죄송합니다. 메시지 처리 중 오류가 발생했습니다.",
                "router_type": "error",
                "confidence": 0.0,
                "sources": [],
                "metadata": {"error": str(e)}
            }
    
    async def _process_with_router_switching(self, context: RouterContext) -> Dict[str, Any]:
        """라우터 전환을 지원하는 메시지 처리"""
        current_router = None
        switch_count = 0
        max_switches = settings.max_router_switches
        
        while switch_count < max_switches:
            # 라우터 선택
            if current_router is None:
                current_router = await self.select_router(context)
                if current_router is None:
                    return {
                        "response": "적절한 라우터를 찾을 수 없습니다.",
                        "router_type": "error",
                        "confidence": 0.0,
                        "sources": [],
                        "metadata": {"error": "no_router_found"}
                    }
            
            # 컨텍스트 업데이트
            context.current_router = current_router.router_name
            context.router_switches = switch_count
            
            # 라우터 처리
            result = await current_router.process(context)
            
            # 결과에 따른 후속 처리
            if result.action == RouterAction.COMPLETE:
                # 처리 완료
                return {
                    "response": result.response,
                    "router_type": current_router.router_name,
                    "confidence": result.confidence,
                    "sources": result.sources,
                    "metadata": result.metadata
                }
            elif result.action == RouterAction.SWITCH:
                # 라우터 전환
                if result.next_router and result.next_router in self.routers:
                    current_router = self.routers[result.next_router]
                    switch_count += 1
                    logger.info(f"라우터 전환: {result.next_router} (전환 횟수: {switch_count})")
                else:
                    return {
                        "response": result.response,
                        "router_type": current_router.router_name,
                        "confidence": result.confidence,
                        "sources": result.sources,
                        "metadata": result.metadata
                    }
            elif result.action == RouterAction.ERROR:
                # 오류 발생
                return {
                    "response": result.response,
                    "router_type": current_router.router_name,
                    "confidence": result.confidence,
                    "sources": result.sources,
                    "metadata": result.metadata
                }
            else:
                # CONTINUE 또는 기타 액션
                return {
                    "response": result.response,
                    "router_type": current_router.router_name,
                    "confidence": result.confidence,
                    "sources": result.sources,
                    "metadata": result.metadata
                }
        
        # 최대 전환 횟수 초과
        return {
            "response": "라우터 전환이 너무 많이 발생했습니다. 다시 시도해 주세요.",
            "router_type": "error",
            "confidence": 0.0,
            "sources": [],
            "metadata": {"error": "max_switches_exceeded"}
        }
    
    def get_router_statistics(self) -> Dict[str, Any]:
        """라우터 통계 정보 반환"""
        return {
            "total_routers": len(self.routers),
            "available_routers": list(self.routers.keys()),
            "active_sessions": len(self.conversation_history),
            "total_users": len(self.user_preferences)
        } 