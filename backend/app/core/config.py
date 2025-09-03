"""
환경 설정 관리
"""

from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 설정
    APP_NAME: str = "제약회사 영업사원 AI 어시스턴트"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API 키
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    HUGGINGFACE_TOKEN: str = os.getenv("HUGGINGFACE_TOKEN", "")
    
    # Database URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./database/main.db")
    
    # CORS 설정
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    # 데이터베이스 경로
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    ROOT_DIR: Path = BASE_DIR.parent  # 루트 폴더
    DATABASE_DIR: Path = ROOT_DIR / "database"  # 루트 폴더의 database
    VECTOR_DB_DIR: Path = DATABASE_DIR / "vectordb"
    DOCUMENTS_DIR: Path = DATABASE_DIR / "documents"
    RULE_DB_DIR: Path = DATABASE_DIR / "ruledb"
    RELATION_DB_DIR: Path = DATABASE_DIR / "relationdb"
    
    # 세션 설정
    SESSION_TIMEOUT: int = 3600  # 1시간
    MAX_SESSIONS_PER_USER: int = 5
    
    # LangGraph 설정
    LANGGRAPH_VERSION: str = "0.6.6"
    MAX_ITERATIONS: int = 10
    RECURSION_LIMIT: int = 25
    
    # 에이전트 설정
    AGENT_TIMEOUT: int = 30  # 초
    MAX_RETRIES: int = 3
    
    # 모델 설정 (GPT-4o 사용)
    OPENAI_MODEL: str = "gpt-4o"
    SQL_MODEL: str = "gpt-4o"
    
    # HuggingFace 모델 설정
    USE_HUGGINGFACE: bool = True
    EMBEDDING_MODEL: str = "nlpai-lab/KURE-v1"  # HuggingFace Kure-v1 임베딩
    RERANKER_MODEL: str = "dragonkue/bge-reranker-v2-m3-ko"  # 한국어 리랭커
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"  # OpenAI 임베딩 (대체용)
    
    # 벡터 DB 설정
    VECTOR_DB_TYPE: str = "chromadb"  # chromadb, pinecone
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # 문서 생성 설정
    MAX_DOCUMENT_LENGTH: int = 10000
    SUPPORTED_FORMATS: List[str] = ["pdf", "docx", "txt", "md"]
    
    # 규정 검사 설정
    COMPLIANCE_THRESHOLD: float = 0.8
    RISK_LEVELS: List[str] = ["low", "medium", "high", "critical"]
    
    # 분석 설정
    MAX_SQL_LENGTH: int = 500
    ANALYSIS_CACHE_TTL: int = 3600
    
    # Redis 설정 (옵션)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    USE_REDIS: bool = False
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    
    class Config:
        # 루트 폴더의 .env 파일 읽기
        env_file = Path(__file__).resolve().parent.parent.parent.parent / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# 싱글톤 설정 인스턴스
settings = Settings()

# 디렉토리 생성
def ensure_directories():
    """필요한 디렉토리 생성"""
    directories = [
        settings.DATABASE_DIR,
        settings.VECTOR_DB_DIR,
        settings.DOCUMENTS_DIR,
        settings.RULE_DB_DIR,
        settings.RELATION_DB_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# 앱 시작 시 디렉토리 생성
ensure_directories()