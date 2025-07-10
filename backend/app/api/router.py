"""
메인 API 라우터

새로운 모듈화된 라우터 시스템의 메인 라우터입니다.
서비스 초기화 오류를 방지하기 위해 지연 로딩을 사용합니다.
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

# API 라우터 생성
api_router = APIRouter()

# 서브 라우터 지연 로딩
try:
    from .routes.router import router as routes_router
    # 서브 라우터 포함 (prefix 제거 - main.py에서 이미 설정됨)
    api_router.include_router(routes_router)
    logger.info("라우터 서브 모듈 로드 완료")
except Exception as e:
    logger.warning(f"라우터 서브 모듈 로드 실패: {str(e)}")
    
    # 기본 라우터 생성
    @api_router.get("/test")
    async def test_fallback():
        """기본 테스트 엔드포인트"""
        return {
            "success": True,
            "message": "기본 API가 정상적으로 작동하고 있습니다.",
            "warning": "일부 서비스가 제한 모드로 실행 중입니다."
        }
    
    @api_router.get("/health")
    async def health_fallback():
        """기본 헬스 체크"""
        return {
            "status": "limited",
            "message": "기본 기능만 사용 가능합니다.",
            "services": {
                "embedding": False,
                "database": False,
                "openai": False
            }
        } 