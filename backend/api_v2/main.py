"""DreamAgent API v2 — FastAPI 엔트리.

Checkpointer(AsyncPostgresSaver) + 4-Layer LangGraph 그래프를 lifespan에서 초기화.
PostgreSQL 연결 필수 — 실패 시 서버 시작 중단.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_v2.middleware import setup_error_handlers
from api_v2.routes import (
    conversations_router,
    health_router,
)
from api_v2.ws_agent import router as ws_agent_router
from api_v2.ws_hitl import router as ws_hitl_router
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작/종료 시 Checkpointer + Graph 초기화."""

    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from app.dream_agent.system_graph.builder import build_graph

    logger.info("Initializing Checkpointer (PostgreSQL)...")
    logger.info(f"  DB URI: {settings.CHECKPOINT_DB_URI[:50]}...")

    try:
        cm = AsyncPostgresSaver.from_conn_string(settings.CHECKPOINT_DB_URI)
        checkpointer = await cm.__aenter__()
        await checkpointer.setup()
        app.state.checkpointer = checkpointer
        app.state.graph = build_graph(checkpointer=checkpointer)
        logger.info("✅ Checkpointer connected + Graph compiled with PostgreSQL")
    except Exception as e:
        logger.error(f"❌ Checkpointer 연결 실패: {e}")
        logger.error("서버를 시작할 수 없습니다. 다음을 확인하세요:")
        logger.error("  1. PostgreSQL 서비스 실행 중인지")
        logger.error("  2. .env의 CHECKPOINT_DB_URI 설정")
        logger.error("  3. uv run python -m scripts.setup_checkpointer 실행")
        raise RuntimeError(f"Checkpointer 연결 실패: {e}")

    # 콘솔용 커넥션 풀 (체크포인터와 동일 DB, 앱 레벨 조회/수정). 비핵심 — 실패해도 서버는 가동.
    try:
        import asyncpg

        app.state.db_pool = await asyncpg.create_pool(
            settings.CHECKPOINT_DB_URI, min_size=1, max_size=5
        )
        logger.info("✅ DB console pool created")
    except Exception as e:
        app.state.db_pool = None
        logger.warning(f"DB console pool 생성 실패 (DB 콘솔 비활성): {e}")

    # Data DB 풀 (dreamagent_data, schema-per-client). 비핵심 — 실패해도 서버는 가동.
    try:
        import asyncpg

        app.state.data_db_pool = await asyncpg.create_pool(
            settings.data_db_uri, min_size=1, max_size=5
        )
        logger.info("✅ Data DB pool created")
    except Exception as e:
        app.state.data_db_pool = None
        logger.warning(f"Data DB pool 생성 실패 (Data 콘솔 비활성): {e}")

    # 데이터 영속화 백엔드 전환: DATA_BACKEND=postgres 면 입력(raw 읽기)·출력(정제/계산 저장)
    # 양쪽을 Postgres로. (도구·러너는 get_default_*() 사용 → set_* 한 번으로 전체 전환)
    #   - Workspace(출력): normalized/computed → dreamagent_data (항목②)
    #   - DataSource(입력): raw 읽기 → dreamagent_data {client}._workspace (항목①)
    if settings.DATA_BACKEND == "postgres":
        try:
            from app.workspace import set_workspace
            from app.workspace.postgres import PostgresWorkspace

            set_workspace(PostgresWorkspace())
            logger.info("✅ Workspace backend = PostgresWorkspace (normalized/computed → dreamagent_data)")
        except Exception as e:
            logger.warning(f"PostgresWorkspace 전환 실패 (file 백엔드 유지): {e}")
        try:
            from app.data_sources import set_data_source
            from app.data_sources.postgres import PostgresDataSource

            set_data_source(PostgresDataSource())
            logger.info("✅ DataSource backend = PostgresDataSource (raw 읽기 ← dreamagent_data)")
        except Exception as e:
            logger.warning(f"PostgresDataSource 전환 실패 (file 백엔드 유지): {e}")

    yield

    # 서버 종료 시 cleanup
    pool = getattr(app.state, "db_pool", None)
    if pool is not None:
        try:
            await pool.close()
        except Exception as e:
            logger.warning("DB pool cleanup failed", error=str(e))
    data_pool = getattr(app.state, "data_db_pool", None)
    if data_pool is not None:
        try:
            await data_pool.close()
        except Exception as e:
            logger.warning("Data DB pool cleanup failed", error=str(e))
    try:
        await cm.__aexit__(None, None, None)
        logger.info("Checkpointer connection closed")
    except Exception as e:
        logger.warning("Checkpointer cleanup failed", error=str(e), exc_info=True)


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{settings.APP_NAME} (v2)",
        version="2.0.0-alpha",
        description="DreamAgent API v2",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    setup_error_handlers(app)

    app.include_router(health_router)
    app.include_router(conversations_router)
    app.include_router(ws_agent_router)
    app.include_router(ws_hitl_router)

    # (2026-06-12 정리) 구 dashboard 정적 mount 폐기 — dashboard/ 디렉토리 삭제
    # (legacy 대시보드, 2026-05-28 mock 폐기 흐름)로 도달 불가 死경로였음.
    # 현행 UI = frontend/ (Vite React SPA, 별도 서빙).

    return app


app = create_app()
