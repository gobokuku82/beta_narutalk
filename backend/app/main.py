"""
제약회사 영업사원 AI 어시스턴트 - FastAPI 메인 애플리케이션
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

from app.api.v1 import chat, session, database, upload
from app.core.config import settings
from app.langgraph.supervisor_multi_agent import create_multi_agent_supervisor_graph

# Supervisor 그래프 전역 변수
supervisor_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    global supervisor_app
    
    # 시작 시
    logger.info("🚀 제약회사 영업사원 AI 어시스턴트 시작")
    logger.info(f"LangGraph 버전: 0.6.6")
    logger.info(f"Python 버전: 3.12")
    
    # Multi-Agent Supervisor 그래프 초기화
    supervisor_app = create_multi_agent_supervisor_graph()
    logger.info("Supervisor graph initialized")
    
    yield
    
    # 종료 시
    logger.info("👋 애플리케이션 종료")

# FastAPI 앱 생성
app = FastAPI(
    title="제약회사 영업사원 AI 어시스턴트",
    description="LangGraph 0.6.6 기반 멀티 에이전트 시스템",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(session.router, prefix="/api/v1/session", tags=["Session"])
app.include_router(database.router, prefix="/api/v1/database", tags=["Database"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["Upload"])

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "langgraph_version": "0.6.6",
        "agents": [
            "supervisor",
            "info_retrieval",
            "doc_generation",
            "compliance",
            "analytics"
        ]
    }

# 루트 엔드포인트
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "제약회사 영업사원 AI 어시스턴트 API",
        "docs": "/docs",
        "health": "/health"
    }

# Supervisor 그래프 접근 함수
def get_supervisor_app():
    """Supervisor 앱 인스턴스 반환"""
    global supervisor_app
    if supervisor_app is None:
        raise RuntimeError("Supervisor가 아직 초기화되지 않았습니다")
    return supervisor_app

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )