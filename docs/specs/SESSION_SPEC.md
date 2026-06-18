# Session Management Specification

**Version**: 2.0 | **Date**: 2026-02-06 | **Status**: Draft

---

## 1. Overview

Dream Agent V2의 세션 관리 시스템 명세입니다. 세션은 사용자 요청부터 응답 완료까지의 전체 라이프사이클을 추적합니다.

### 1.1 Design Goals

| Goal | Description |
|------|-------------|
| **Persistence** | 세션 상태를 영속적으로 저장하여 복구 가능 |
| **Resumability** | 중단된 세션을 재개 가능 |
| **Traceability** | 전체 실행 과정 추적 가능 |
| **Isolation** | 세션 간 데이터 격리 |
| **Scalability** | 다중 세션 동시 처리 |

### 1.2 Session Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Session Structure                               │
└─────────────────────────────────────────────────────────────────────────┘

Session
├── id: "sess_abc123"
├── status: "executing"
├── user_input: "라네즈 리뷰 분석..."
├── language: "ko"
│
├── LangGraph State (Checkpointer)
│   ├── cognitive_result
│   ├── planning_result
│   ├── execution_results
│   └── response_result
│
├── Plan
│   ├── id: "plan_xyz789"
│   ├── version: 2
│   ├── todos: [...]
│   └── versions: [...]
│
├── HITL State
│   ├── pending: null | HITLRequest
│   └── history: [...]
│
├── Metadata
│   ├── created_at
│   ├── updated_at
│   ├── started_at
│   └── completed_at
│
└── Statistics
    ├── tokens_used
    ├── cost_usd
    └── execution_time_ms
```

---

## 2. Session Lifecycle

### 2.1 State Diagram

```
                           ┌─────────────┐
                           │   CREATED   │
                           └──────┬──────┘
                                  │ start
                                  ▼
                           ┌─────────────┐
              ┌───────────►│   RUNNING   │◄───────────┐
              │            └──────┬──────┘            │
              │                   │                    │
              │ resume   ┌────────┼────────┐          │ resume
              │          │        │        │          │
              │          ▼        ▼        ▼          │
      ┌───────┴────┐  ┌──────┐  ┌──────┐  ┌─────┐    │
      │  PAUSED    │  │HITL  │  │ERROR │  │DONE │    │
      │            │  │WAIT  │  │      │  │     │    │
      └────────────┘  └──┬───┘  └──┬───┘  └──┬──┘    │
              │          │         │         │        │
              │ timeout  │ respond │ retry   │        │
              └──────────┴─────────┴─────────┘        │
                                  │                    │
                                  └────────────────────┘
                                  │
                     ┌────────────┼────────────┐
                     ▼            ▼            ▼
               ┌──────────┐ ┌──────────┐ ┌──────────┐
               │COMPLETED │ │ FAILED   │ │CANCELLED │
               └──────────┘ └──────────┘ └──────────┘
```

### 2.2 Status Definitions

| Status | Description | Transitions To |
|--------|-------------|----------------|
| `created` | 세션 생성됨, 아직 시작 안 함 | running |
| `running` | 에이전트 실행 중 | paused, hitl_waiting, completed, failed |
| `paused` | 사용자에 의해 일시정지 | running, cancelled |
| `hitl_waiting` | HITL 응답 대기 중 | running, cancelled |
| `completed` | 성공적으로 완료 | (terminal) |
| `failed` | 오류로 실패 | (terminal, but can retry) |
| `cancelled` | 사용자에 의해 취소 | (terminal) |
| `expired` | 타임아웃으로 만료 | (terminal) |

---

## 3. Storage Architecture

### 3.1 Storage Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Storage Architecture                              │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                           Application Layer                              │
│                                                                          │
│  SessionManager ──► PlanManager ──► TodoManager ──► HITLManager          │
│                                                                          │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────────────────────────┐
│                           Repository Layer                               │
│                                                                          │
│  SessionRepository   PlanRepository   ExecutionResultRepository          │
│                                                                          │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│    PostgreSQL     │   │      Redis        │   │   File Storage    │
│                   │   │                   │   │                   │
│ • sessions        │   │ • session_cache   │   │ • reports/        │
│ • plans           │   │ • hitl_pending    │   │ • exports/        │
│ • todos           │   │ • rate_limits     │   │ • uploads/        │
│ • checkpoints     │   │                   │   │                   │
│ • hitl_events     │   │                   │   │                   │
└───────────────────┘   └───────────────────┘   └───────────────────┘

     Persistence            Hot Cache             Binary Data
```

### 3.2 LangGraph Checkpointer

LangGraph의 `AsyncPostgresSaver`를 사용하여 그래프 상태를 저장합니다.

```python
# orchestrator/checkpointer.py

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import asyncpg

async def create_checkpointer(database_url: str) -> AsyncPostgresSaver:
    pool = await asyncpg.create_pool(database_url)
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()  # 테이블 생성
    return checkpointer
```

**Checkpoint 테이블:**
```sql
-- LangGraph가 자동 생성
CREATE TABLE checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint JSONB NOT NULL,  -- AgentState 직렬화
    metadata JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);
```

### 3.3 Session Table

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'created',
    language VARCHAR(10) DEFAULT 'ko',

    -- Input
    user_input TEXT NOT NULL,

    -- Plan Reference
    plan_id UUID REFERENCES plans(id),

    -- Results (denormalized for fast access)
    response JSONB,

    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Statistics
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(10, 6) DEFAULT 0,
    execution_time_ms INTEGER,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    CONSTRAINT valid_session_status CHECK (status IN (
        'created', 'running', 'paused', 'hitl_waiting',
        'completed', 'failed', 'cancelled', 'expired'
    ))
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);
```

### 3.4 Redis Cache Structure

```
# Active Session Cache
session:{session_id} = {
    "status": "running",
    "current_layer": "execution",
    "plan_id": "plan_xyz789",
    "last_activity": "2026-02-06T10:05:00Z"
}
TTL: 24 hours

# HITL Pending
session:{session_id}:hitl_pending = {
    "request_id": "hitl_001",
    "type": "plan_review",
    "data": {...},
    "timeout_at": "2026-02-06T10:10:00Z"
}
TTL: matches timeout_at

# WebSocket Connections
ws_connections:{session_id} = Set<client_id>

# Progress Cache
session:{session_id}:progress = {
    "total_todos": 5,
    "completed": 2,
    "current_todo": "todo_003"
}
TTL: matches session
```

---

## 4. Session Manager

### 4.1 Interface

```python
# workflow_managers/session_manager/manager.py

from typing import Optional, List
from datetime import datetime, timedelta
import uuid

class SessionManager:
    def __init__(
        self,
        session_repo: SessionRepository,
        cache: RedisClient,
        checkpointer: AsyncPostgresSaver
    ):
        self.repo = session_repo
        self.cache = cache
        self.checkpointer = checkpointer

    async def create_session(
        self,
        user_input: str,
        language: str = "ko",
        user_id: Optional[str] = None,
        options: Optional[dict] = None
    ) -> Session:
        """새 세션 생성"""
        session = Session(
            id=str(uuid.uuid4()),
            user_id=user_id,
            user_input=user_input,
            language=language,
            status="created",
            options=options or {},
            created_at=datetime.utcnow()
        )

        # DB 저장
        await self.repo.save(session)

        # 캐시에 저장
        await self.cache.hset(f"session:{session.id}", session.to_cache_dict())
        await self.cache.expire(f"session:{session.id}", 86400)  # 24h

        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """세션 조회 (캐시 우선)"""
        # 캐시 확인
        cached = await self.cache.hgetall(f"session:{session_id}")
        if cached:
            return Session.from_cache_dict(cached)

        # DB 조회
        session = await self.repo.get(session_id)
        if session:
            await self.cache.hset(f"session:{session.id}", session.to_cache_dict())

        return session

    async def update_status(self, session_id: str, status: str):
        """상태 업데이트"""
        now = datetime.utcnow()

        updates = {"status": status, "updated_at": now}

        if status == "running" and not await self._get_started_at(session_id):
            updates["started_at"] = now
        elif status in ("completed", "failed", "cancelled"):
            updates["completed_at"] = now

        await self.repo.update(session_id, updates)
        await self.cache.hset(f"session:{session_id}", updates)

    async def get_graph_state(self, session_id: str) -> Optional[dict]:
        """LangGraph 상태 조회"""
        config = {"configurable": {"thread_id": session_id}}
        state = await self.checkpointer.aget(config)
        return state.values if state else None

    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Session]:
        """세션 목록 조회"""
        return await self.repo.list(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset
        )

    async def delete_session(self, session_id: str):
        """세션 삭제"""
        # LangGraph 상태 삭제
        config = {"configurable": {"thread_id": session_id}}
        await self.checkpointer.adelete(config)

        # DB 삭제
        await self.repo.delete(session_id)

        # 캐시 삭제
        await self.cache.delete(f"session:{session_id}")

    async def cleanup_expired(self):
        """만료된 세션 정리"""
        expired_sessions = await self.repo.get_expired()
        for session in expired_sessions:
            await self.update_status(session.id, "expired")
            # Optional: 데이터 아카이브
```

### 4.2 Session Model

```python
# models/session.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class SessionStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    HITL_WAITING = "hitl_waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class Session(BaseModel):
    id: str
    user_id: Optional[str] = None
    status: SessionStatus = SessionStatus.CREATED
    language: str = "ko"

    # Input
    user_input: str

    # References
    plan_id: Optional[str] = None

    # Results
    response: Optional[Dict[str, Any]] = None

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Statistics
    tokens_used: int = 0
    cost_usd: float = 0.0
    execution_time_ms: Optional[int] = None

    # Options
    options: Dict[str, Any] = Field(default_factory=dict)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_cache_dict(self) -> Dict[str, str]:
        """Redis 캐시용 직렬화"""
        return {
            "status": self.status.value,
            "plan_id": self.plan_id or "",
            "last_activity": self.updated_at.isoformat()
        }

    @classmethod
    def from_cache_dict(cls, data: Dict[str, str]) -> "Session":
        """Redis 캐시에서 복원 (부분 데이터)"""
        # Note: 전체 데이터는 DB에서 조회 필요
        pass
```

---

## 5. Session Resume

### 5.1 Resume Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Session Resume Flow                              │
└─────────────────────────────────────────────────────────────────────────┘

1. POST /sessions/{session_id}/resume
   │
   ▼
2. 세션 상태 확인
   ├── status == "paused" or "hitl_waiting" → OK
   └── otherwise → Error (SESSION_NOT_RESUMABLE)
   │
   ▼
3. LangGraph 상태 로드
   │
   ▼
4. 수정사항 적용 (있는 경우)
   ├── skip_todos
   ├── retry_todos
   └── update_todos
   │
   ▼
5. 세션 상태 업데이트
   └── status = "running"
   │
   ▼
6. LangGraph 재개
   └── agent.arun(..., config={"thread_id": session_id})
   │
   ▼
7. WebSocket 연결 복구 (클라이언트)
```

### 5.2 Resume Implementation

```python
# api/routes/sessions.py

@router.post("/sessions/{session_id}/resume")
async def resume_session(
    session_id: str,
    body: ResumeRequest,
    session_manager: SessionManager = Depends(get_session_manager),
    agent: Agent = Depends(get_agent)
):
    # 1. 세션 조회
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    # 2. 상태 확인
    if session.status not in ("paused", "hitl_waiting", "failed"):
        raise HTTPException(400, "Session cannot be resumed")

    # 3. 수정사항 적용
    if body.modifications:
        graph_state = await session_manager.get_graph_state(session_id)
        updated_state = apply_modifications(graph_state, body.modifications)
        await save_modified_state(session_id, updated_state)

    # 4. 상태 업데이트
    await session_manager.update_status(session_id, "running")

    # 5. LangGraph 재개
    config = {"configurable": {"thread_id": session_id}}

    async def run_agent():
        async for event in agent.astream(None, config=config):
            await broadcast_to_websocket(session_id, event)

    asyncio.create_task(run_agent())

    return {
        "success": True,
        "data": {
            "session_id": session_id,
            "status": "running",
            "websocket_url": f"ws://localhost:8000/ws/{session_id}"
        }
    }
```

### 5.3 State Restoration

```python
# orchestrator/state_restore.py

async def restore_session_state(
    session_id: str,
    checkpointer: AsyncPostgresSaver
) -> Optional[AgentState]:
    """체크포인트에서 세션 상태 복원"""

    config = {"configurable": {"thread_id": session_id}}

    # 최신 체크포인트 조회
    checkpoint = await checkpointer.aget(config)

    if not checkpoint:
        return None

    # AgentState 복원
    state = checkpoint.values

    # 진행 중이던 Todo 상태 확인
    if "todos" in state:
        for todo in state["todos"]:
            if todo.get("status") == "in_progress":
                # 중단된 작업은 pending으로 리셋
                todo["status"] = "pending"
                todo["retry_count"] = todo.get("retry_count", 0) + 1

    return state
```

---

## 6. Session Expiry & Cleanup

### 6.1 Expiry Policy

```yaml
# config/session.yaml

session:
  expiry:
    active_session_ttl: 86400       # 24시간 (활성 세션)
    paused_session_ttl: 3600        # 1시간 (일시정지 세션)
    completed_session_ttl: 604800   # 7일 (완료된 세션)
    failed_session_ttl: 86400       # 24시간 (실패한 세션)

  cleanup:
    run_interval: 3600              # 1시간마다 정리 작업
    archive_completed: true         # 완료된 세션 아카이브
    delete_expired: true            # 만료된 세션 삭제
```

### 6.2 Cleanup Task

```python
# tasks/session_cleanup.py

from celery import shared_task
from datetime import datetime, timedelta

@shared_task
async def cleanup_expired_sessions():
    """만료된 세션 정리 (Celery task)"""

    session_manager = get_session_manager()
    config = get_session_config()

    # 각 상태별 만료 세션 조회
    expired = await session_manager.repo.find_expired(
        paused_before=datetime.utcnow() - timedelta(seconds=config["paused_session_ttl"]),
        active_before=datetime.utcnow() - timedelta(seconds=config["active_session_ttl"])
    )

    for session in expired:
        # 상태 업데이트
        await session_manager.update_status(session.id, "expired")

        # 아카이브 (선택적)
        if config["archive_completed"]:
            await archive_session(session)

        # LangGraph 체크포인트 정리
        await session_manager.checkpointer.adelete(
            {"configurable": {"thread_id": session.id}}
        )

        # 캐시 정리
        await session_manager.cache.delete(f"session:{session.id}")

    logger.info(f"Cleaned up {len(expired)} expired sessions")
```

---

## 7. Multi-Session Handling

### 7.1 Concurrent Session Limits

```python
# middleware/session_limit.py

class SessionLimitMiddleware:
    def __init__(self, max_concurrent_per_user: int = 5):
        self.max_concurrent = max_concurrent_per_user

    async def __call__(self, request: Request, call_next):
        user_id = request.state.user_id

        if request.url.path.startswith("/api/agent/run"):
            # 활성 세션 수 확인
            active_count = await self.count_active_sessions(user_id)

            if active_count >= self.max_concurrent:
                raise HTTPException(
                    429,
                    f"Maximum {self.max_concurrent} concurrent sessions allowed"
                )

        return await call_next(request)

    async def count_active_sessions(self, user_id: str) -> int:
        return await session_repo.count(
            user_id=user_id,
            status__in=["created", "running", "paused", "hitl_waiting"]
        )
```

### 7.2 Session Priority

```python
# workflow_managers/session_manager/priority.py

class SessionPriorityManager:
    """세션 우선순위 관리 (리소스 제한 시)"""

    PRIORITY_LEVELS = {
        "high": 3,      # 유료 사용자
        "normal": 2,    # 일반 사용자
        "low": 1        # 무료 사용자
    }

    async def get_priority(self, session: Session) -> int:
        user = await user_repo.get(session.user_id)
        return self.PRIORITY_LEVELS.get(user.tier, 2)

    async def should_queue(self, session: Session) -> bool:
        """리소스 부족 시 큐잉 여부 결정"""
        current_load = await self.get_system_load()
        priority = await self.get_priority(session)

        if current_load > 0.9 and priority < 3:
            return True
        return False
```

---

## 8. Session Events

### 8.1 Event Types

```python
# models/session_event.py

class SessionEventType(str, Enum):
    CREATED = "session.created"
    STARTED = "session.started"
    PAUSED = "session.paused"
    RESUMED = "session.resumed"
    COMPLETED = "session.completed"
    FAILED = "session.failed"
    CANCELLED = "session.cancelled"
    EXPIRED = "session.expired"

class SessionEvent(BaseModel):
    event_type: SessionEventType
    session_id: str
    timestamp: datetime
    data: Dict[str, Any] = {}
```

### 8.2 Event Publishing

```python
# workflow_managers/session_manager/events.py

class SessionEventPublisher:
    def __init__(self, redis: RedisClient):
        self.redis = redis
        self.channel = "session_events"

    async def publish(self, event: SessionEvent):
        """세션 이벤트 발행"""
        await self.redis.publish(
            self.channel,
            event.model_dump_json()
        )

        # 히스토리 저장
        await self.redis.lpush(
            f"session:{event.session_id}:events",
            event.model_dump_json()
        )

# 사용 예:
await event_publisher.publish(SessionEvent(
    event_type=SessionEventType.COMPLETED,
    session_id=session_id,
    timestamp=datetime.utcnow(),
    data={"execution_time_ms": 45000}
))
```

---

## 9. Session Analytics

### 9.1 Metrics Collection

```python
# analytics/session_metrics.py

class SessionMetrics:
    async def record_session_complete(self, session: Session):
        """세션 완료 시 메트릭 기록"""

        metrics = {
            "session_id": session.id,
            "user_id": session.user_id,
            "execution_time_ms": session.execution_time_ms,
            "tokens_used": session.tokens_used,
            "cost_usd": session.cost_usd,
            "todo_count": len(session.plan.todos) if session.plan else 0,
            "status": session.status,
            "timestamp": datetime.utcnow()
        }

        # PostgreSQL에 저장
        await self.metrics_repo.insert(metrics)

        # Prometheus/StatsD로 전송 (선택적)
        self.statsd.increment("sessions.completed")
        self.statsd.timing("sessions.execution_time", session.execution_time_ms)
```

### 9.2 Usage Statistics Query

```sql
-- 일별 세션 통계
SELECT
    DATE(created_at) as date,
    COUNT(*) as total_sessions,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    AVG(execution_time_ms) as avg_execution_time,
    SUM(tokens_used) as total_tokens,
    SUM(cost_usd) as total_cost
FROM sessions
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

---

## Related Documents

- [WEBSOCKET_PROTOCOL.md](WEBSOCKET_PROTOCOL.md) - WebSocket 프로토콜
- [API_SPEC.md](API_SPEC.md) - REST API 명세
- [HITL_SPEC.md](HITL_SPEC.md) - HITL 시스템
- [ERROR_CODES.md](ERROR_CODES.md) - 에러 코드

---

*Last Updated: 2026-02-06*
