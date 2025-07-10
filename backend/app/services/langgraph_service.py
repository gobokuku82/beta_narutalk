"""
새로운 모듈화된 LangGraph 서비스

라우터 매니저를 사용하여 확장 가능한 라우터 아키텍처를 제공합니다.
"""

from typing import Dict, Any, List, Optional
import logging
from .router_manager import RouterManager
from .embedding_service import EmbeddingService
from .database_service import DatabaseService

logger = logging.getLogger(__name__)

class LangGraphService:
    """모듈화된 랭그래프 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        try:
            # 의존성 서비스 초기화
            self.embedding_service = None
            self.database_service = None
            
            # 임베딩 서비스 초기화 (선택적)
            try:
                self.embedding_service = EmbeddingService()
                logger.info("임베딩 서비스 초기화 완료")
            except Exception as e:
                logger.warning(f"임베딩 서비스 초기화 실패: {str(e)}")
            
            # 데이터베이스 서비스 초기화 (선택적)
            try:
                self.database_service = DatabaseService()
                logger.info("데이터베이스 서비스 초기화 완료")
            except Exception as e:
                logger.warning(f"데이터베이스 서비스 초기화 실패: {str(e)}")
            
            # 라우터 매니저 초기화
            self.router_manager = RouterManager(
                embedding_service=self.embedding_service,
                database_service=self.database_service
            )
            
            logger.info("새로운 LangGraph 서비스 초기화 완료")
            
        except Exception as e:
            logger.error(f"LangGraph 서비스 초기화 실패: {str(e)}")
            raise
    
    async def process_message(self, message: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        메시지 처리
        
        Args:
            message: 사용자 메시지
            user_id: 사용자 ID
            session_id: 세션 ID
            
        Returns:
            처리 결과 딕셔너리
        """
        try:
            result = await self.router_manager.process_message(message, user_id, session_id)
            
            # 호환성을 위한 응답 포맷 조정
            formatted_result = {
                "response": result.get("response", ""),
                "router_type": result.get("router_type", "unknown"),
                "confidence": result.get("confidence", 0.0),
                "sources": result.get("sources", []),
                "metadata": result.get("metadata", {})
            }
            
            logger.info(f"메시지 처리 완료: 라우터={formatted_result['router_type']}, 신뢰도={formatted_result['confidence']:.2f}")
            return formatted_result
            
        except Exception as e:
            logger.error(f"메시지 처리 실패: {str(e)}")
            return {
                "response": "죄송합니다. 메시지 처리 중 오류가 발생했습니다.",
                "router_type": "error",
                "confidence": 0.0,
                "sources": [],
                "metadata": {"error": str(e)}
            }
    
    async def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        채팅 기록 조회
        
        Args:
            session_id: 세션 ID
            
        Returns:
            채팅 기록 리스트
        """
        try:
            if session_id in self.router_manager.conversation_history:
                return self.router_manager.conversation_history[session_id]
            return []
        except Exception as e:
            logger.error(f"채팅 기록 조회 실패: {str(e)}")
            return []
    
    def get_router_types(self) -> List[Dict[str, Any]]:
        """
        사용 가능한 라우터 타입 목록 반환
        
        Returns:
            라우터 타입 리스트
        """
        try:
            return self.router_manager.get_available_routers()
        except Exception as e:
            logger.error(f"라우터 타입 조회 실패: {str(e)}")
            return []
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        서비스 상태 정보 반환
        
        Returns:
            서비스 상태 딕셔너리
        """
        try:
            router_stats = self.router_manager.get_router_statistics()
            
            return {
                "status": "active",
                "embedding_service": "available" if self.embedding_service else "unavailable",
                "database_service": "available" if self.database_service else "unavailable",
                "openai_client": "available" if self.router_manager.openai_client else "unavailable",
                "router_statistics": router_stats
            }
        except Exception as e:
            logger.error(f"서비스 상태 조회 실패: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def add_custom_router(self, router):
        """
        사용자 정의 라우터 추가
        
        Args:
            router: BaseRouter를 상속받은 라우터 인스턴스
        """
        try:
            self.router_manager.add_router(router)
            logger.info(f"사용자 정의 라우터 추가: {router.router_name}")
        except Exception as e:
            logger.error(f"사용자 정의 라우터 추가 실패: {str(e)}")
    
    def remove_router(self, router_name: str):
        """
        라우터 제거
        
        Args:
            router_name: 제거할 라우터 이름
        """
        try:
            self.router_manager.remove_router(router_name)
            logger.info(f"라우터 제거: {router_name}")
        except Exception as e:
            logger.error(f"라우터 제거 실패: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        헬스 체크
        
        Returns:
            헬스 체크 결과
        """
        try:
            # 간단한 테스트 메시지 처리
            test_result = await self.process_message("안녕하세요", "test_user", "test_session")
            
            return {
                "status": "healthy",
                "test_message_processed": bool(test_result.get("response")),
                "router_count": len(self.router_manager.routers),
                "services": {
                    "embedding": bool(self.embedding_service),
                    "database": bool(self.database_service),
                    "openai": bool(self.router_manager.openai_client)
                }
            }
        except Exception as e:
            logger.error(f"헬스 체크 실패: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            } 