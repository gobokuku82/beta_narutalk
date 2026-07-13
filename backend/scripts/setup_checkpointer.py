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
    (global|workspace|user|session). 확장/변경 용이 구조(§0.1 5원칙).
    LangGraph checkpoint 테이블과 동일 system DB 에 둔다 (ADR-015 §A.7: 분리 테이블, 같은 DB).
    """
    print(f"\n[3/4] memory_entries 테이블 생성 중...")
    ddl = """
    CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()

    CREATE TABLE IF NOT EXISTS memory_entries (
        id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
        type        VARCHAR(32)  NOT NULL,   -- preference|conversation|conversation_meta|plan|pattern|knowledge|session|tool_cache
        scope_type  VARCHAR(16)  NOT NULL,   -- global|workspace|user|session  (2026-07-05 org→workspace, ERD system_erd_v0 §2.7)
        scope_id    VARCHAR(255) NOT NULL,   -- scope_type 별 식별자 (workspace=workspaces.id, user=users.id, session=turn_id, global='')
        key         VARCHAR(255) NOT NULL,   -- scope 내 unique key (upsert 단위)
        content     JSONB        NOT NULL,   -- flexible content (content.schema_version 로 진화)
        source      VARCHAR(16)  NOT NULL DEFAULT 'explicit',  -- explicit|implicit|extracted
        confidence  FLOAT        NOT NULL DEFAULT 1.0,         -- 0.0~1.0
        created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
        updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
        expires_at  TIMESTAMPTZ,                               -- TTL (NULL = 무한)
        CONSTRAINT memory_type_chk   CHECK (type IN ('preference','conversation','conversation_meta','plan','pattern','knowledge','session','tool_cache')),
        CONSTRAINT memory_scope_chk  CHECK (scope_type IN ('global','workspace','user','session')),
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

    -- (2026-07-05) 기존 테이블 org→workspace 개명 (신규 생성분은 위 CHECK 로 이미 반영; 기존 DB 만 교체, 멱등)
    ALTER TABLE memory_entries DROP CONSTRAINT IF EXISTS memory_scope_chk;
    ALTER TABLE memory_entries ADD  CONSTRAINT memory_scope_chk CHECK (scope_type IN ('global','workspace','user','session'));
    """
    try:
        with psycopg.connect(CHECKPOINT_DB_URI, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
        print("      memory_entries 테이블 + 인덱스 3 + trigger 생성 완료! (spec 35 §3.3)")
    except Exception as e:
        print(f"      오류: memory_entries 생성 실패 - {e}")
        raise


def setup_auth_tables():
    """users + auth_sessions + 이메일인증/비번재설정 토큰 (dreamagent_system) — 회원가입형.

    설계 출처: system_erd_v0 §2.1·2.2·2.8 (ERD 문서 미이식 — 진실 소스는 코드 규약에 따라 본 DDL이 기준).
    인증 = 세션 테이블(opaque token): 토큰은 ≥256bit CSPRNG, DB엔 SHA-256 해시만.
    """
    print(f"\n[auth] users + auth_sessions + 토큰 테이블 생성 중...")
    ddl = """
    CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()

    CREATE TABLE IF NOT EXISTS users (
        id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email         TEXT NOT NULL,
        password_hash TEXT,                                -- NULL 허용 (OAuth 대비)
        display_name  VARCHAR(255),
        role          VARCHAR(16) NOT NULL DEFAULT 'user',
        status        VARCHAR(16) NOT NULL DEFAULT 'active',
        settings      JSONB NOT NULL DEFAULT '{}',
        email_verified_at TIMESTAMPTZ,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        last_login_at TIMESTAMPTZ,
        CONSTRAINT users_role_chk   CHECK (role IN ('user','admin')),
        CONSTRAINT users_status_chk CHECK (status IN ('active','suspended','deleted'))
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (lower(email));

    CREATE TABLE IF NOT EXISTS auth_sessions (
        id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token_hash   TEXT NOT NULL UNIQUE,                 -- SHA-256(≥256bit CSPRNG). 원문 저장 X
        created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        expires_at   TIMESTAMPTZ NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_sessions_user    ON auth_sessions (user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_expires ON auth_sessions (expires_at);

    CREATE TABLE IF NOT EXISTS email_verification_tokens (
        token_hash TEXT PRIMARY KEY,
        user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        expires_at TIMESTAMPTZ NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS password_reset_tokens (
        token_hash TEXT PRIMARY KEY,
        user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        expires_at TIMESTAMPTZ NOT NULL,
        used_at    TIMESTAMPTZ,                            -- 1회용 소진 표시
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """
    try:
        with psycopg.connect(CHECKPOINT_DB_URI, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
        print("      users + auth_sessions + 토큰 2종 생성 완료! (ERD §2.1·2.2·2.8)")
    except Exception as e:
        print(f"      오류: auth 테이블 생성 실패 - {e}")
        raise


def setup_workspace_tables():
    """workspaces + workspace_members (dreamagent_system) — 테넌트 레지스트리 (구 client 승계).

    설계 출처: system_erd_v0 §2.3·2.4 (ERD 문서 미이식 — 진실 소스는 코드 규약에 따라 본 DDL이 기준).
    name(표시명, 사용자 입력) ≠ schema_name(서버 발급 ws_<shortid>, PG 스키마명).
    agent_profile 은 nullable — NULL=미설정(cognitive fail-fast 보존, '{}' 금지).
    """
    print(f"\n[workspace] workspaces + workspace_members 생성 중...")
    ddl = """
    CREATE TABLE IF NOT EXISTS workspaces (
        id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name           VARCHAR(255) NOT NULL,
        schema_name    VARCHAR(63) NOT NULL UNIQUE,        -- 서버 발급 ws_<shortid>
        agent_profile  JSONB,                              -- NULL=미설정 (fail-fast 보존)
        dashboard_spec JSONB NOT NULL DEFAULT '{}',
        status         VARCHAR(16) NOT NULL DEFAULT 'active',
        created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at     TIMESTAMPTZ,
        CONSTRAINT ws_status_chk CHECK (status IN ('active','archived'))
    );

    CREATE TABLE IF NOT EXISTS workspace_members (
        workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        role         VARCHAR(16) NOT NULL DEFAULT 'owner',
        created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (workspace_id, user_id),
        CONSTRAINT wm_role_chk CHECK (role IN ('owner','editor','viewer'))
    );
    CREATE INDEX IF NOT EXISTS idx_wm_user ON workspace_members (user_id);
    """
    try:
        with psycopg.connect(CHECKPOINT_DB_URI, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
        print("      workspaces + workspace_members 생성 완료! (ERD §2.3·2.4)")
    except Exception as e:
        print(f"      오류: workspace 테이블 생성 실패 - {e}")
        raise


def setup_conversation_index():
    """conversations 대화 인덱스 (dreamagent_system) — 소유권·목록·N+1 해소 (계획서 P5-3).

    설계 출처: system_erd_v0 §2.5 (ERD 문서 미이식 — 진실 소스는 코드 규약에 따라 본 DDL이 기준).
    id = TEXT (현행 conversation_id 'conv_<8hex>' 형식 — UUID 아님, checkpoint 무변경).
    user_id = 소유권의 단일 진실 소스 (격리·목록 필터·소유권 가드 UPSERT).
    """
    print(f"\n[conversation] conversations 인덱스 생성 중...")
    ddl = """
    CREATE TABLE IF NOT EXISTS conversations (
        id           TEXT PRIMARY KEY,                     -- conversation_id (클라 발급 'conv_xxx')
        user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL,   -- generic = NULL
        title        VARCHAR(500),
        turn_count   INTEGER NOT NULL DEFAULT 0,
        last_turn_at TIMESTAMPTZ,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at   TIMESTAMPTZ
    );
    CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations (user_id, last_turn_at DESC);
    CREATE INDEX IF NOT EXISTS idx_conversations_ws   ON conversations (workspace_id);
    """
    try:
        with psycopg.connect(CHECKPOINT_DB_URI, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
        print("      conversations 인덱스 생성 완료! (ERD §2.5)")
    except Exception as e:
        print(f"      오류: conversations 생성 실패 - {e}")
        raise


def setup_memory_embeddings():
    """memory_embeddings 벡터 테이블 (dreamagent_system, pgvector) — 의미 검색.

    설계 출처: system_erd_v0 §2.6 (ERD 문서 미이식 — 진실 소스는 코드 규약에 따라 본 DDL이 기준).
    KURE-v1 (bge-m3 기반) 1024차원. memory_entries 와 1:1 ON DELETE CASCADE.

    ⚠️ pgvector 확장 필요 — 미설치 시 honest-degrade(경고 후 스킵). MemoryManager
    구현(계획서 P5-2) 전까지 소비자 0 이라 main() 에 미배선 — pgvector 설치 후 배선.
    """
    print(f"\n[memory_embeddings] pgvector 벡터 테이블 생성 시도...")
    try:
        with psycopg.connect(CHECKPOINT_DB_URI, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memory_embeddings (
                        memory_id  UUID PRIMARY KEY REFERENCES memory_entries(id) ON DELETE CASCADE,
                        embedding  vector(1024) NOT NULL,
                        model      TEXT NOT NULL DEFAULT 'KURE-v1',
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    """
                )
        print("      memory_embeddings 생성 완료! (ERD §2.6)")
    except Exception as e:
        print(f"      스킵: pgvector 미설치 또는 생성 실패 (memory 벡터검색 비활성) - {e}")


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

    # 3b. (2026-07-05) 회원가입형 시스템 테이블 — ERD system_erd_v0.md
    #     FK 순서: users(auth) → workspaces → conversations
    setup_auth_tables()
    setup_workspace_tables()
    setup_conversation_index()
    # setup_memory_embeddings()  # pgvector 설치 후 배선 (MemoryManager P5-2, 소비자 0)

    # 4. 검증
    verify_setup()

    # 5. 환경 설정 안내
    print_env_config()

    print("\n셋업 완료!")


if __name__ == "__main__":
    asyncio.run(main())
