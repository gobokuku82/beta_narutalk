"""Application Configuration

pydantic-settings 기반 환경 설정
"""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 프로젝트 루트의 .env를 cwd 무관하게 로드
# config.py = backend/app/core/config.py → parents[3] = repo root
_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === App ===
    APP_NAME: str = "OctorAD"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production

    # === Server ===
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # === Database ===
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/octormate_system"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # === Checkpoint Database (LangGraph) ===
    CHECKPOINT_DB_URI: str = "postgresql://postgres:postgres@localhost:5432/octormate_system"

    # === Data DB (client 정형 데이터, schema-per-client) ===
    # client = schema. 새 client = data/{client}/computed/ 폴더만 추가 → setup_data_db 재실행으로 자동 schema.
    # 미설정(None) 시 CHECKPOINT_DB_URI 자격증명 재사용 + db명만 octormate_data로 교체 (data_db_uri 프로퍼티).
    DATA_DB_URI: Optional[str] = None

    # 데이터 영속화 백엔드: "file"(기본) | "postgres".
    # "postgres" 면 lifespan에서 Workspace(정제/계산 저장)를 PostgresWorkspace로 swap.
    # 안전 토글 — 문제 시 .env에서 이 값만 빼면(=file) 즉시 원복. (DataSource 전환=raw 항목은 후속)
    DATA_BACKEND: str = "file"

    # === Redis (Optional) ===
    REDIS_URL: Optional[str] = None

    # === LLM ===
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DEFAULT_LLM_PROVIDER: str = "openai"  # openai, anthropic
    DEFAULT_LLM_MODEL: str = "gpt-4o"

    # === Session ===
    # (2026-06-12) SESSION_TIMEOUT_SEC·SESSION_MAX_TURNS 제거 — 죽은 session_manager
    # (v1 잔재, 호출 0)와 동반 삭제. 세션 영속은 LangGraph checkpointer 가 전담.

    # === HITL ===
    # (2026-06-11) HITL_TIMEOUT_SEC·HITL_MAX_RETRIES 제거 — Sprint 12 event 트랙
    # (HITLRequest/wait_for_response) 폐기와 동반. 활성 timeout 은 HITL_RESUME_TIMEOUT_SEC.

    # Sprint 14 A1 — wait_for_resume 의 timeout 인자로 전달.
    # NFR-9: 기본 30분 (POC). NFR-10: .env HITL_RESUME_TIMEOUT_SEC 로 override.
    # G-3: ge=1 validator — 0/음수 오설정 방어 (즉시 timeout 유발 방지).
    # 권장: .env 에서 최소 300s 이상. 이하는 테스트 용도.
    HITL_RESUME_TIMEOUT_SEC: int = Field(default=1800, ge=1)

    # === Execution ===
    EXECUTION_TIMEOUT_SEC: int = 300
    EXECUTION_MAX_RETRIES: int = 3
    EXECUTION_MAX_PARALLEL: int = 5

    # === Logging ===
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json, text

    # === CORS ===
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000", "null", "*"]

    # === Sprint 13 — 멀티플렉싱 / 동시성 / 대화 컨텍스트 ===
    # 사용자 식별 (Sprint 16+ 실제 로그인 전까지 "demo" 고정)
    DEFAULT_USER_ID: str = "demo"

    # 유저당 동시 실행 쿼리 상한 (ConcurrencyManager)
    MAX_CONCURRENT_TURNS_PER_USER: int = 3

    # 유저당 WebSocket 연결 상한 (ConnectionManager, 탭 다중 지원)
    MAX_WS_CONNECTIONS_PER_USER: int = 5

    # Cognitive에 주입할 과거 대화 기본/상한
    DEFAULT_HISTORY_LIMIT: int = 3
    MAX_HISTORY_LIMIT: int = 10

    # 대화 제목 자동 생성 (Sprint 15 실사용)
    TITLE_SOURCE: str = "first_query"     # first_query | summary_llm
    TITLE_MAX_LENGTH: int = 15

    @property
    def data_db_uri(self) -> str:
        """Data DB URI — 명시값(DATA_DB_URI) 우선, 없으면 CHECKPOINT_DB_URI 자격증명 재사용(db명만 octormate_data로 교체)."""
        if self.DATA_DB_URI:
            return self.DATA_DB_URI
        head, _, _tail = self.CHECKPOINT_DB_URI.rpartition("/")
        return f"{head}/octormate_data"


# Singleton
settings = Settings()
