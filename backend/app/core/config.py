from pydantic_settings import BaseSettings
from typing import Optional, ClassVar, List
import os
from pathlib import Path

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 설정
    app_name: str = "NaruTalk AI 챗봇"
    debug: bool = True
    
    # 프로젝트 루트 경로
    project_root: ClassVar[Path] = Path(__file__).parent.parent.parent.parent
    
    # OpenAI 설정
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 1000
    openai_timeout: int = 30
    
    # 모델 경로 (절대 경로)
    embedding_model_path: str = str(project_root / "models" / "KURE-V1")
    reranker_model_path: str = str(project_root / "models" / "bge-reranker-v2-m3-ko")
    
    # 데이터베이스 설정 (절대 경로)
    chroma_db_path: str = str(project_root / "database" / "chroma_db")
    sqlite_db_path: str = str(project_root / "database" / "realationdb")
    
    # 랭그래프 설정
    langgraph_debug: bool = True
    
    # 라우터 시스템 설정
    available_routers: List[str] = [
        "qa_router",
        "document_search_router", 
        "employee_info_router",
        "general_chat_router",
        "analysis_router",
        "report_generator_router"
    ]
    
    router_confidence_threshold: float = 0.5
    max_router_switches: int = 5
    
    # API 설정
    api_v1_prefix: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 설정 인스턴스 생성
settings = Settings() 