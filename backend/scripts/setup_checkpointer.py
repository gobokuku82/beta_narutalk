"""
Checkpoint Database Setup Script

PostgreSQL 데이터베이스 생성 및 LangGraph AsyncPostgresSaver 테이블 셋업.

사용법:
    cd backend
    uv run python -m scripts.setup_checkpointer

참고:
    - langgraph-checkpoint-postgres 3.0+ 기준
    - https://pypi.org/project/langgraph-checkpoint-postgres/
"""

import asyncio
import sys
import platform
from pathlib import Path

# Windows 호환성: SelectorEventLoop 사용 (psycopg async 요구사항)
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import psycopg
from psycopg import sql
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ========================================
# 설정: .env의 CHECKPOINT_DB_URI에서 동적 추출
# ========================================
from urllib.parse import urlparse

try:
    from app.core.config import settings
    CHECKPOINT_DB_URI = settings.CHECKPOINT_DB_URI
except ImportError:
    CHECKPOINT_DB_URI = None

# 기본값 (settings 로드 실패 시 폴백)
_DEFAULT_URI = "postgresql://postgres:postgres@localhost:5432/dreamagent_system"
if not CHECKPOINT_DB_URI:
    CHECKPOINT_DB_URI = _DEFAULT_URI

# URI 파싱 (postgresql+psycopg:// 도 지원)
_uri_for_parse = CHECKPOINT_DB_URI.replace("postgresql+psycopg", "postgresql")
_parsed = urlparse(_uri_for_parse)

POSTGRES_HOST = _parsed.hostname or "localhost"
POSTGRES_PORT = _parsed.port or 5432
POSTGRES_USER = _parsed.username or "postgres"
POSTGRES_PASSWORD = _parsed.password or ""
DATABASE_NAME = (_parsed.path or "/dreamagent_system").lstrip("/") or "dreamagent_system"

# Admin 접속 (postgres 시스템 DB) — DB 생성용
ADMIN_CONN_STRING = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/postgres"
)


def create_database():
    """
    dreamagent_system 데이터베이스 생성 (동기 작업).

    PostgreSQL에서 CREATE DATABASE는 트랜잭션 내에서 실행할 수 없으므로
    autocommit 모드로 실행해야 합니다.
    """
    print(f"[1/4] PostgreSQL에 연결 중... ({POSTGRES_HOST}:{POSTGRES_PORT})")

    try:
        # autocommit=True 필수 (CREATE DATABASE는 트랜잭션 내에서 실행 불가)
        with psycopg.connect(ADMIN_CONN_STRING, autocommit=True) as conn:
            with conn.cursor() as cur:
                # 데이터베이스 존재 여부 확인
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (DATABASE_NAME,)
                )
                exists = cur.fetchone()

                if exists:
                    print(f"      데이터베이스 '{DATABASE_NAME}'가 이미 존재합니다.")
                else:
                    # 데이터베이스 생성
                    cur.execute(
                        sql.SQL("CREATE DATABASE {}").format(
                            sql.Identifier(DATABASE_NAME)
                        )
                    )
                    print(f"      데이터베이스 '{DATABASE_NAME}' 생성 완료!")

    except psycopg.OperationalError as e:
        print(f"      오류: PostgreSQL 연결 실패 - {e}")
        print("      PostgreSQL 서버가 실행 중인지 확인하세요.")
        sys.exit(1)


async def setup_checkpoint_tables():
    """
    AsyncPostgresSaver에 필요한 체크포인트 테이블 생성.

    LangGraph checkpoint-postgres 3.0+에서는 .setup() 메서드를 호출하여
    필요한 테이블을 자동 생성합니다.

    Note: from_conn_string()을 사용하면 autocommit이 올바르게 설정되어
    CREATE INDEX CONCURRENTLY 문제를 피할 수 있습니다.
    """
    print(f"\n[2/4] 체크포인트 테이블 생성 중...")
    print(f"      연결 URI: {CHECKPOINT_DB_URI[:50]}...")

    try:
        # from_conn_string을 사용하여 autocommit 설정이 올바르게 적용되도록 함
        async with AsyncPostgresSaver.from_conn_string(CHECKPOINT_DB_URI) as checkpointer:
            # 테이블 생성 (.setup() 호출)
            await checkpointer.setup()

            print("      체크포인트 테이블 생성 완료!")
            print("      - checkpoint_migrations")
            print("      - checkpoints")
            print("      - checkpoint_blobs")
            print("      - checkpoint_writes")

    except Exception as e:
        print(f"      오류: 테이블 생성 실패 - {e}")
        raise


def setup_memory_table():
    """memory_entries 테이블 생성 (dreamagent_system) — MemoryManager cross-thread knowledge.

    진실 소스: docs/agent_specs/35_DB_SCHEMA_v1.0.md §3.3.
    JSONB content + schema_version(in content) + append-only + scope cascade
    (global|org|user|session). 확장/변경 용이 구조(§0.1 5원칙).
    LangGraph checkpoint 테이블과 동일 system DB 에 둔다 (ADR-015 §A.7: 분리 테이블, 같은 DB).
    """
    print(f"\n[3/4] memory_entries 테이블 생성 중...")
    ddl = """
    CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()

    CREATE TABLE IF NOT EXISTS memory_entries (
        id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
        type        VARCHAR(32)  NOT NULL,   -- preference|conversation|conversation_meta|plan|pattern|knowledge|session|tool_cache
        scope_type  VARCHAR(16)  NOT NULL,   -- global|org|user|session
        scope_id    VARCHAR(255) NOT NULL,   -- scope_type 별 식별자 (global = '' 또는 'default')
        key         VARCHAR(255) NOT NULL,   -- scope 내 unique key (upsert 단위)
        content     JSONB        NOT NULL,   -- flexible content (content.schema_version 로 진화)
        source      VARCHAR(16)  NOT NULL DEFAULT 'explicit',  -- explicit|implicit|extracted
        confidence  FLOAT        NOT NULL DEFAULT 1.0,         -- 0.0~1.0
        created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
        updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
        expires_at  TIMESTAMPTZ,                               -- TTL (NULL = 무한)
        CONSTRAINT memory_type_chk   CHECK (type IN ('preference','conversation','conversation_meta','plan','pattern','knowledge','session','tool_cache')),
        CONSTRAINT memory_scope_chk  CHECK (scope_type IN ('global','org','user','session')),
        CONSTRAINT memory_source_chk CHECK (source IN ('explicit','implicit','extracted')),
        CONSTRAINT memory_conf_chk   CHECK (confidence >= 0.0 AND confidence <= 1.0),
        CONSTRAINT memory_unique_key UNIQUE (scope_type, scope_id, type, key)
    );

    CREATE INDEX IF NOT EXISTS idx_memory_scope   ON memory_entries (scope_type, scope_id, type);
    CREATE INDEX IF NOT EXISTS idx_memory_content ON memory_entries USING GIN (content);
    CREATE INDEX IF NOT EXISTS idx_memory_expires ON memory_entries (expires_at) WHERE expires_at IS NOT NULL;

    -- updated_at 자동 갱신 trigger
    CREATE OR REPLACE FUNCTION memory_entries_set_updated_at() RETURNS TRIGGER AS $$
    BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS memory_entries_updated_at_trigger ON memory_entries;
    CREATE TRIGGER memory_entries_updated_at_trigger
        BEFORE UPDATE ON memory_entries
        FOR EACH ROW EXECUTE FUNCTION memory_entries_set_updated_at();
    """
    try:
        with psycopg.connect(CHECKPOINT_DB_URI, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
        print("      memory_entries 테이블 + 인덱스 3 + trigger 생성 완료! (spec 35 §3.3)")
    except Exception as e:
        print(f"      오류: memory_entries 생성 실패 - {e}")
        raise


def print_env_config():
    """
    .env 파일에 추가할 설정 출력.
    """
    print(f"\n[4/4] .env 파일에 다음 설정을 확인/추가하세요:")
    print("=" * 60)
    print(f"# Checkpoint Database (LangGraph AsyncPostgresSaver)")
    print(f"CHECKPOINT_DB_URI={CHECKPOINT_DB_URI}")
    print("=" * 60)


def verify_setup():
    """
    셋업 검증 - 테이블이 정상적으로 생성되었는지 확인 (동기 버전).
    """
    print(f"\n[검증] 테이블 확인 중...")

    with psycopg.connect(CHECKPOINT_DB_URI) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cur.fetchall()

            if tables:
                print("      생성된 테이블:")
                for (table_name,) in tables:
                    print(f"        - {table_name}")
            else:
                print("      경고: 테이블이 생성되지 않았습니다.")


async def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("DreamAgent - Checkpoint Database Setup")
    print("=" * 60)

    # 1. 데이터베이스 생성
    create_database()

    # 2. 체크포인트 테이블 생성
    await setup_checkpoint_tables()

    # 3. memory_entries 테이블 생성 (향후 MemoryManager)
    setup_memory_table()

    # 4. 검증
    verify_setup()

    # 5. 환경 설정 안내
    print_env_config()

    print("\n셋업 완료!")


if __name__ == "__main__":
    asyncio.run(main())
