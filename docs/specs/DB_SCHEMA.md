# Dream Agent V2 - Database Schema

**Version**: 2.0 | **Date**: 2026-02-06 | **Status**: Draft

---

## 1. Overview

V2는 기존 PostgreSQL을 그대로 사용하며, LangGraph checkpoint 테이블과 세션 관리 테이블만 추가합니다.

### 1.1 테이블 구성

| 테이블 | 용도 | 관리 주체 |
|--------|------|----------|
| `checkpoints` | LangGraph 상태 저장 | AsyncPostgresSaver (자동) |
| `checkpoint_writes` | Checkpoint 쓰기 로그 | AsyncPostgresSaver (자동) |
| `checkpoint_blobs` | 대용량 상태 저장 | AsyncPostgresSaver (자동) |
| `sessions` | 세션 메타데이터 | 애플리케이션 |
| `session_messages` | 대화 히스토리 | 애플리케이션 |

---

## 2. LangGraph Checkpoint Tables

AsyncPostgresSaver가 자동으로 생성/관리하는 테이블입니다.

### 2.1 checkpoints

```sql
CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

CREATE INDEX idx_checkpoints_thread_id ON checkpoints(thread_id);
CREATE INDEX idx_checkpoints_created_at ON checkpoints(created_at);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `thread_id` | TEXT | 세션 ID (= session_id) |
| `checkpoint_ns` | TEXT | 네임스페이스 (기본 '') |
| `checkpoint_id` | TEXT | 체크포인트 UUID |
| `parent_checkpoint_id` | TEXT | 부모 체크포인트 (분기용) |
| `type` | TEXT | 체크포인트 타입 |
| `checkpoint` | JSONB | AgentState 직렬화 |
| `metadata` | JSONB | 추가 메타데이터 |
| `created_at` | TIMESTAMPTZ | 생성 시간 |

### 2.2 checkpoint_writes

```sql
CREATE TABLE IF NOT EXISTS checkpoint_writes (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    channel TEXT NOT NULL,
    type TEXT,
    blob BYTEA,

    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `task_id` | TEXT | 작업 ID |
| `idx` | INTEGER | 쓰기 순서 |
| `channel` | TEXT | 채널명 |
| `blob` | BYTEA | 직렬화된 데이터 |

### 2.3 checkpoint_blobs

```sql
CREATE TABLE IF NOT EXISTS checkpoint_blobs (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    channel TEXT NOT NULL,
    version TEXT NOT NULL,
    type TEXT NOT NULL,
    blob BYTEA,

    PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
);
```

---

## 3. Session Management Tables

애플리케이션에서 관리하는 세션 테이블입니다.

### 3.1 sessions

```sql
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,                                    -- 사용자 ID (nullable for anonymous)

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'created',  -- created, active, paused, completed, failed, expired
    current_layer VARCHAR(20),                       -- cognitive, planning, execution, response

    -- Config
    language VARCHAR(5) NOT NULL DEFAULT 'ko',
    config JSONB NOT NULL DEFAULT '{}',              -- 세션 설정

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,                          -- 세션 만료 시간
    completed_at TIMESTAMPTZ,

    -- Metrics
    total_turns INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    total_cost DECIMAL(10, 4) NOT NULL DEFAULT 0
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_created_at ON sessions(created_at);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at) WHERE expires_at IS NOT NULL;
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | UUID | 세션 ID (= LangGraph thread_id) |
| `user_id` | UUID | 사용자 ID |
| `status` | VARCHAR(20) | 세션 상태 |
| `current_layer` | VARCHAR(20) | 현재 처리 중인 레이어 |
| `language` | VARCHAR(5) | 언어 설정 |
| `config` | JSONB | 세션별 설정 |
| `total_turns` | INTEGER | 총 대화 턴 수 |
| `total_tokens` | INTEGER | 총 사용 토큰 |
| `total_cost` | DECIMAL | 총 비용 |

**Status Values**:

| Status | 설명 |
|--------|------|
| `created` | 세션 생성됨 |
| `active` | 실행 중 |
| `paused` | HITL 대기 또는 사용자 일시정지 |
| `completed` | 정상 완료 |
| `failed` | 에러로 실패 |
| `expired` | 타임아웃 만료 |

### 3.2 session_messages

```sql
CREATE TABLE IF NOT EXISTS session_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,

    -- Message
    role VARCHAR(20) NOT NULL,                       -- user, assistant, system
    content TEXT NOT NULL,

    -- Metadata
    layer VARCHAR(20),                               -- 메시지 생성 레이어
    metadata JSONB NOT NULL DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_session_messages_session_id ON session_messages(session_id);
CREATE INDEX idx_session_messages_created_at ON session_messages(created_at);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `session_id` | UUID | 세션 FK |
| `role` | VARCHAR(20) | user / assistant / system |
| `content` | TEXT | 메시지 내용 |
| `layer` | VARCHAR(20) | 메시지 생성 레이어 |
| `metadata` | JSONB | 첨부파일 URL 등 |

---

## 4. Checkpointer 설정

### 4.1 AsyncPostgresSaver 초기화

```python
# orchestrator/checkpointer.py
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.core.config import settings

async def get_checkpointer() -> AsyncPostgresSaver:
    """AsyncPostgresSaver 인스턴스 반환"""
    checkpointer = AsyncPostgresSaver.from_conn_string(
        settings.DATABASE_URL
    )
    # 테이블 자동 생성
    await checkpointer.setup()
    return checkpointer
```

### 4.2 Graph에 Checkpointer 연결

```python
# orchestrator/graph.py
from .checkpointer import get_checkpointer

async def create_agent():
    checkpointer = await get_checkpointer()
    graph = build_graph()

    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["planning"],
    )
```

### 4.3 세션 ID를 thread_id로 사용

```python
# api/routes/agent.py
from uuid import uuid4

async def run_agent(request: AgentRunRequest):
    session_id = str(uuid4())

    # LangGraph 실행 시 thread_id = session_id
    config = {"configurable": {"thread_id": session_id}}

    result = await agent.ainvoke(
        {"user_input": request.message, "session_id": session_id},
        config=config
    )

    return {"session_id": session_id, "response": result}
```

---

## 5. Redis 캐시 (선택)

빠른 세션 조회를 위한 Redis 캐시 (선택 사항)

### 5.1 캐시 키 구조

```
session:{session_id}              → 세션 메타데이터 (JSON)
session:{session_id}:status       → 상태 (string)
session:{session_id}:layer        → 현재 레이어 (string)
session:{session_id}:ws_clients   → 연결된 WebSocket 클라이언트 수 (int)
```

### 5.2 TTL 정책

| 키 | TTL | 설명 |
|-----|-----|------|
| `session:{id}` | 24시간 | 세션 메타 |
| `session:{id}:status` | 1시간 | 상태 (자주 갱신) |
| `session:{id}:ws_clients` | 5분 | WebSocket 연결 수 |

---

## 6. Related Documents

| Document | Description |
|----------|-------------|
| [SESSION_SPEC.md](SESSION_SPEC.md) | 세션 관리 시스템 상세 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 전체 시스템 아키텍처 |
| [DATA_MODELS.md](DATA_MODELS.md) | Pydantic 모델 정의 |

---

*Last Updated: 2026-02-06*
