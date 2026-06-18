# Sprint 15 — Phase E1 세부 작업계획서 (메모리 인프라 구현)

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-28 |
| Phase | E-1 — 메모리 인프라 (5 항목 정책 #1) |
| 마스터 | [`sprint15_implementation_plan.md`](./sprint15_implementation_plan.md) |
| 정식 spec | [`agent_specs/35_DB_SCHEMA_v1.0.md`](../agent_specs/35_DB_SCHEMA_v1.0.md) (ERD + schema source of truth) |
| 의존 | Phase D ✅ (ADR-015 본문 lock) |
| 다음 | [`sprint15_phase_e2_chat_memory.md`](./sprint15_phase_e2_chat_memory.md) (채팅 메모리 통합) |
| 예상 작업량 | ~6시간 (1.5세션) |
| Acceptance | DB 테이블 + Pydantic models + MemoryManager 7 메서드 + Dashboard CRUD UI + API endpoint + 단위 테스트 (group I) |

---

## 0. 본 문서의 역할

Phase E-1 의 **메모리 인프라 첫 구현 작업 카탈로그** — DB / 모델 / Manager / UI / API / 테스트.

본 문서는 **5 항목 정책 #1 (PostgreSQL 대화기록 / 로드 / 삭제)** 의 실현.

다루지 않는 것:
- 채팅 메모리 통합 (→ Phase E-2)
- Clarification (→ Phase E-3)
- NL 2차 (→ Phase E-4)

---

## 1. Phase E-1 의 의도

### 1.1 왜 인프라 부터?

5 항목 정책 #1 = 다른 모든 항목의 토대:
- #2 채팅창 로드 → 인프라 위에 UI 만 추가
- #3 LLM 히스토리 → 인프라의 search 활용
- #4 잘라내기 → 인프라 위 정책 logic
- #5 Clarification → 인프라의 store/find 활용

→ **인프라 없으면 #2~5 의미 0**.

### 1.2 작업 원칙

- **Q3 자료 §3, §7 그대로** — 사용자 권고 lock
- **Sprint 15 P0 범위만** — Org / Global / pattern 추출 등은 후속
- **Status 마커 명시** — `complete | partial | planned`

---

## 2. 작업 분해 — 5 sub-phase

```
E1-1  DB 마이그레이션 (memory_entries 테이블)
        ↓
E1-2  Pydantic models (MemoryEntry / MemoryContext / Pattern)
        ↓
E1-3  MemoryManager 7 P0 메서드 + DB 액세스 layer
        ↓
E1-4  API endpoint (memory CRUD)
        ↓
E1-5  Dashboard CRUD UI
```

### 시간 추정

| Sub-phase | 시간 | 누적 |
|-----------|------|------|
| E1-1 DB 마이그레이션 | 30min | 0.5h |
| E1-2 Pydantic models | 30min | 1h |
| E1-3 MemoryManager + DB layer | 2.5h | 3.5h |
| E1-4 API endpoint | 1h | 4.5h |
| E1-5 Dashboard UI | 1.5h | **6h** |

---

## 3. E1-1: DB 마이그레이션 (~30분)

### 3.1 작업

**경로**: `backend/migrations/versions/sprint15_001_memory_entries.py` (신규, alembic 형식)

**또는**: 직접 SQL 스크립트 — `backend/scripts/sprint15/001_create_memory_entries.sql`

**판단**: 프로젝트가 alembic 사용 시 alembic, 아니면 직접 SQL.

### 3.2 SQL 본문 (Q3 §2)

```sql
-- Sprint 15 P0 — Memory entries table
-- Status: complete — Sprint 15 P0
-- Reference: ADR-015, docs/reports/sprint14_a3_research_q3_memory.md §2

CREATE TABLE IF NOT EXISTS memory_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(32) NOT NULL,
    scope_type VARCHAR(16) NOT NULL,
    scope_id VARCHAR(255) NOT NULL,
    key VARCHAR(255) NOT NULL,
    content JSONB NOT NULL DEFAULT '{}'::jsonb,
    source VARCHAR(16) NOT NULL DEFAULT 'explicit',
    confidence FLOAT NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT memory_type_valid CHECK (type IN (
        'preference', 'conversation', 'conversation_meta', 'plan',
        'pattern', 'knowledge', 'session', 'tool_cache'
    )),
    CONSTRAINT memory_scope_type_valid CHECK (scope_type IN (
        'global', 'org', 'user', 'session'
    )),
    CONSTRAINT memory_source_valid CHECK (source IN (
        'explicit', 'implicit', 'extracted'
    )),
    CONSTRAINT memory_confidence_range CHECK (confidence >= 0.0 AND confidence <= 1.0)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_memory_scope ON memory_entries(scope_type, scope_id, type);
CREATE INDEX IF NOT EXISTS idx_memory_content ON memory_entries USING GIN (content);
CREATE INDEX IF NOT EXISTS idx_memory_expires ON memory_entries(expires_at)
    WHERE expires_at IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_memory_unique_key
    ON memory_entries(scope_type, scope_id, type, key);

-- Updated_at 자동 갱신 trigger
CREATE OR REPLACE FUNCTION update_memory_entries_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER memory_entries_updated_at_trigger
    BEFORE UPDATE ON memory_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_memory_entries_updated_at();
```

### 3.3 적용

```bash
# alembic 사용 시
uv run alembic upgrade head

# 또는 직접 SQL
psql $DATABASE_URL -f backend/scripts/sprint15/001_create_memory_entries.sql
```

### 3.4 검증

```sql
-- 테이블 확인
\d memory_entries

-- 인덱스 확인
\di memory_entries*

-- 샘플 INSERT (테스트)
INSERT INTO memory_entries (type, scope_type, scope_id, key, content)
VALUES ('preference', 'user', 'test_user', 'brand', '{"value": "블루밍글로우"}');

SELECT * FROM memory_entries WHERE scope_id = 'test_user';
```

### 3.5 Acceptance

- [ ] 테이블 생성 성공
- [ ] 5 인덱스 (scope / content GIN / expires / unique key + updated_at trigger)
- [ ] 3 CHECK constraint 작동
- [ ] 샘플 INSERT/SELECT 정상
- [ ] PostgreSQL Checkpointer 와 같은 DB 안에서 공존

---

## 4. E1-2: Pydantic models (~30분)

### 4.1 파일

**경로**: `backend/app/dream_agent/models/memory.py` (신규)

### 4.2 코드 (Q3 §9)

```python
"""Memory Domain Models — Sprint 15 P0.

Reference: ADR-015 §A.8 / docs/reports/sprint14_a3_research_q3_memory.md §9

Status: complete — Sprint 15 P0 (3 모델).
"""

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


MemoryType = Literal[
    "preference",         # 사용자 선호 (brand 등)
    "conversation",       # 개별 turn 데이터 (E2-1 persist_turn)
    "conversation_meta",  # 대화 메타 (E2-5 sidebar — title, last_turn_at 등)
    "plan",               # plan 이력
    "pattern",            # 추출된 패턴 (Sprint 17+)
    "knowledge",          # 도메인 지식
    "session",            # 세션 컨텍스트 (단기)
    "tool_cache",         # tool 결과 cache (Sprint 16+)
]

ScopeType = Literal["global", "org", "user", "session"]
SourceType = Literal["explicit", "implicit", "extracted"]


class MemoryEntry(BaseModel):
    """단일 메모리 entry — DB row 매핑."""

    model_config = ConfigDict(frozen=True)  # Immutable — 갱신은 새 entry

    id: UUID = Field(default_factory=uuid4)
    type: MemoryType
    scope_type: ScopeType
    scope_id: str
    key: str
    content: dict[str, Any] = Field(default_factory=dict)
    source: SourceType = "explicit"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class MemoryContext(BaseModel):
    """다층 cascade 결과 — Cognitive / Planning 입력.

    가까운 scope (session) → 먼 scope (global) 순으로 merge.
    """

    session_data: dict[str, Any] = Field(default_factory=dict)
    user_data: dict[str, Any] = Field(default_factory=dict)
    org_data: dict[str, Any] = Field(default_factory=dict)
    global_data: dict[str, Any] = Field(default_factory=dict)
    merged: dict[str, Any] = Field(default_factory=dict)


class Pattern(BaseModel):
    """추출된 패턴 — Sprint 17+.

    Status: planned — Sprint 17.
    """

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    pattern_type: str
    pattern_data: dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    sample_size: int
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.3 export 추가

**파일**: `backend/app/dream_agent/models/__init__.py`

```python
from app.dream_agent.models.memory import (
    MemoryEntry,
    MemoryContext,
    Pattern,
    MemoryType,
    ScopeType,
    SourceType,
)

__all__ = [
    # ... 기존
    "MemoryEntry",
    "MemoryContext",
    "Pattern",
    "MemoryType",
    "ScopeType",
    "SourceType",
]
```

### 4.4 Acceptance

- [ ] `models/memory.py` 생성
- [ ] 3 model + 3 type alias
- [ ] `__init__.py` export 추가
- [ ] `from app.dream_agent.models import MemoryEntry, ...` import 작동

---

## 5. E1-3: MemoryManager 구현 (~2.5시간)

### 5.1 파일 구조

```
backend/app/dream_agent/workflow_managers/memory_manager/
├── __init__.py        # public API export
├── manager.py         # MemoryManager class
├── db.py              # PostgreSQL access layer
└── tests/             # (또는 backend/tests/sprint15/)
```

### 5.2 `db.py` — DB Access Layer

**경로**: `backend/app/dream_agent/workflow_managers/memory_manager/db.py`

**LoC**: ~150

**책임**: SQL 실행, asyncpg / SQLAlchemy 사용. MemoryEntry ↔ DB row 변환.

**메서드**:
- `async def insert_or_update(entry: MemoryEntry) -> MemoryEntry` (upsert)
- `async def get_by_key(key, scope_type, scope_id) -> Optional[MemoryEntry]`
- `async def delete_by_key(key, scope_type, scope_id) -> bool`
- `async def search(type, scope_type, scope_id, content_filter=None) -> list[MemoryEntry]`
- `async def get_all_in_scope(scope_type, scope_id) -> list[MemoryEntry]` (cascade 용)

**골격**:
```python
"""Memory DB Access Layer — Sprint 15 P0."""

import asyncpg
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.dream_agent.models import MemoryEntry

logger = get_logger(__name__)


class MemoryDB:
    """memory_entries 테이블 액세스."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def insert_or_update(self, entry: MemoryEntry) -> MemoryEntry:
        """Upsert by (scope_type, scope_id, type, key)."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO memory_entries
                    (id, type, scope_type, scope_id, key, content,
                     source, confidence, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9)
                ON CONFLICT (scope_type, scope_id, type, key)
                DO UPDATE SET
                    content = EXCLUDED.content,
                    source = EXCLUDED.source,
                    confidence = EXCLUDED.confidence,
                    expires_at = EXCLUDED.expires_at,
                    updated_at = NOW()
                RETURNING *
                """,
                entry.id, entry.type, entry.scope_type, entry.scope_id,
                entry.key, entry.content, entry.source,
                entry.confidence, entry.expires_at,
            )
            return _row_to_entry(row)

    # ... 나머지 메서드
```

### 5.3 `manager.py` — MemoryManager

**경로**: `backend/app/dream_agent/workflow_managers/memory_manager/manager.py`

**LoC**: ~300

**P0 메서드 7 개** (Q3 §7):

```python
"""MemoryManager — Sprint 15 P0.

Status: complete — Sprint 15 P0 (7 메서드).

Reference:
- ADR-015 §A.6
- docs/reports/sprint14_a3_research_q3_memory.md §7
"""

from typing import Any, Optional

from app.core.logging import get_logger
from app.dream_agent.models import MemoryEntry, MemoryContext
from .db import MemoryDB

logger = get_logger(__name__)


class MemoryManager:
    """메모리 시스템 통합 manager.

    7 P0 메서드:
        - get / set / delete (CRUD)
        - get_context (cascade)
        - search
        - store_clarification / find_clarification_answer
    """

    def __init__(self, db: MemoryDB):
        self.db = db

    # ── CRUD ──

    async def get(
        self, key: str, scope_type: str, scope_id: str,
    ) -> Optional[MemoryEntry]:
        """단일 entry 조회."""
        return await self.db.get_by_key(key, scope_type, scope_id)

    async def set(
        self, key: str, content: dict[str, Any], *,
        scope_type: str, scope_id: str,
        type: str, source: str = "explicit",
        ttl: Optional[int] = None,
    ) -> MemoryEntry:
        """Upsert. ttl 초 단위 (None = 무한)."""
        from datetime import datetime, timedelta
        expires_at = datetime.utcnow() + timedelta(seconds=ttl) if ttl else None
        entry = MemoryEntry(
            type=type, scope_type=scope_type, scope_id=scope_id,
            key=key, content=content, source=source,
            expires_at=expires_at,
        )
        result = await self.db.insert_or_update(entry)
        logger.info(
            "memory set",
            type=type, scope_type=scope_type, scope_id=scope_id,
            key=key, source=source,
        )
        return result

    async def delete(
        self, key: str, scope_type: str, scope_id: str,
    ) -> bool:
        """단일 entry 삭제."""
        return await self.db.delete_by_key(key, scope_type, scope_id)

    # ── Cascade ──

    async def get_context(
        self, session_id: str, user_id: str, org_id: str = "default",
    ) -> MemoryContext:
        """Session → User → Org → Global cascade.

        가까운 scope 우선. merged dict = 통합 결과.
        """
        session_entries = await self.db.get_all_in_scope("session", session_id)
        user_entries = await self.db.get_all_in_scope("user", user_id)
        org_entries = await self.db.get_all_in_scope("org", org_id)
        global_entries = await self.db.get_all_in_scope("global", "")

        def to_dict(entries):
            return {f"{e.type}:{e.key}": e.content for e in entries}

        session_data = to_dict(session_entries)
        user_data = to_dict(user_entries)
        org_data = to_dict(org_entries)
        global_data = to_dict(global_entries)

        # cascade — 가까운 우선
        merged = {**global_data, **org_data, **user_data, **session_data}

        return MemoryContext(
            session_data=session_data,
            user_data=user_data,
            org_data=org_data,
            global_data=global_data,
            merged=merged,
        )

    # ── Search ──

    async def search(
        self, type: str, scope_type: str, scope_id: str,
        content_filter: Optional[dict] = None,
    ) -> list[MemoryEntry]:
        """type / scope / content 조건 조회."""
        return await self.db.search(type, scope_type, scope_id, content_filter)

    # ── Clarification 통합 ──

    async def store_clarification(
        self, session_id: str, user_id: str,
        field: str, value: Any,
    ) -> MemoryEntry:
        """Clarification 답변 저장.

        Strategy: user scope 에 'preference' type 으로 저장 (다음 turn 자동 활용).
        """
        return await self.set(
            key=field,
            content={"value": value, "from_clarification": True},
            scope_type="user", scope_id=user_id,
            type="preference", source="explicit",
        )

    async def find_clarification_answer(
        self, session_id: str, user_id: str, field: str,
    ) -> Optional[Any]:
        """Cognitive 가 clarification 직전 조회. 다층 cascade.

        Returns: value or None.
        """
        # Session 우선
        session_entry = await self.get(field, "session", session_id)
        if session_entry:
            return session_entry.content.get("value")

        # User 다음
        user_entry = await self.get(field, "user", user_id)
        if user_entry:
            return user_entry.content.get("value")

        # Org / Global = Sprint 16+
        return None
```

### 5.4 `__init__.py` 갱신

**경로**: `backend/app/dream_agent/workflow_managers/memory_manager/__init__.py`

```python
"""Memory Manager — Sprint 15 P0.

Public API:
    get_memory_manager() -> MemoryManager (singleton)
"""

from .manager import MemoryManager

_instance: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    """Singleton accessor."""
    global _instance
    if _instance is None:
        # DB pool 연결 — Sprint 15 P0 진입 시 lifecycle 관리
        raise RuntimeError("MemoryManager not initialized. Call init_memory_manager() first.")
    return _instance


def init_memory_manager(db_pool) -> MemoryManager:
    """앱 lifespan 진입 시 1회 호출."""
    global _instance
    from .db import MemoryDB
    _instance = MemoryManager(db=MemoryDB(db_pool))
    return _instance


__all__ = ["MemoryManager", "get_memory_manager", "init_memory_manager"]
```

### 5.5 lifespan 통합

**파일**: `backend/api_v2/main.py` (수정)

FastAPI lifespan 에서 MemoryManager 초기화:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 기존: PostgreSQL Checkpointer + Graph
    # 추가: MemoryManager
    from app.dream_agent.workflow_managers.memory_manager import init_memory_manager
    init_memory_manager(db_pool=postgres_pool)  # Checkpointer 와 같은 pool
    
    yield
    
    # cleanup (필요 시)
```

### 5.6 단위 테스트

**경로**: `backend/tests/sprint15/test_memory_manager_unit.py` (신규)

**Group I — Memory** (~10 TC):
- TC-MM-01: set + get (CRUD basic)
- TC-MM-02: delete
- TC-MM-03: upsert (같은 key 두 번 set → update)
- TC-MM-04: TTL (expires_at 적용)
- TC-MM-05: get_context cascade (Session → User → Global merge)
- TC-MM-06: search by type
- TC-MM-07: search by content_filter
- TC-MM-08: store_clarification + find_clarification_answer (가장 중요)
- TC-MM-09: scope 격리 (user_a 의 entry 가 user_b 에 안 보임)
- TC-MM-10: source 라벨 (explicit / implicit / extracted)

### 5.7 Acceptance — E1-3

- [ ] `db.py` 5 메서드
- [ ] `manager.py` 7 P0 메서드
- [ ] `__init__.py` get/init 함수
- [ ] `main.py` lifespan 통합
- [ ] Group I 10 TC 통과
- [ ] 자동 테스트 = 244 + 10 = **254+ passed**

---

## 6. E1-4: API endpoint (~1시간)

### 6.1 파일

**경로**: `backend/api_v2/memory.py` (신규)

### 6.2 Endpoints

```python
"""Memory API endpoints — Sprint 15 P0.

Status: complete — Sprint 15 P0.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.dream_agent.models import MemoryEntry
from app.dream_agent.workflow_managers.memory_manager import get_memory_manager

router = APIRouter(prefix="/api/v2/memory", tags=["memory"])


@router.get("/list")
async def list_memory(
    user_id: str = Query(...),
    type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    """사용자 메모리 조회 (UI 표시용)."""
    mm = get_memory_manager()
    entries = await mm.search(
        type=type or "preference",
        scope_type="user", scope_id=user_id,
    )
    # Paginate
    paginated = entries[offset:offset + limit]
    return [e.model_dump(mode="json") for e in paginated]


@router.delete("/{entry_id}")
async def delete_memory(entry_id: str) -> dict:
    """단일 entry 삭제 — UI."""
    # entry_id → 조회 → 삭제 (key + scope 알아야 함)
    # 또는 db.delete_by_id(entry_id) 추가 필요
    # ... 구현
    return {"deleted": True}


@router.delete("/user/{user_id}")
async def delete_user_memory(user_id: str) -> dict:
    """사용자 전체 메모리 삭제 (GDPR / right to forget)."""
    mm = get_memory_manager()
    # all_entries = await mm.search(...)
    # for e in all_entries: await mm.delete(...)
    # return count
    return {"deleted_count": 0}  # 구현
```

### 6.3 main.py router 등록

```python
# backend/api_v2/main.py
from api_v2.memory import router as memory_router
app.include_router(memory_router)
```

### 6.4 통합 테스트

**경로**: `backend/tests/sprint15/test_memory_api_integration.py`

- TC-MA-01: GET /list (빈 + 데이터 있음)
- TC-MA-02: DELETE /{entry_id}
- TC-MA-03: DELETE /user/{user_id} (전체 삭제)

### 6.5 Acceptance — E1-4

- [ ] 3 endpoint 구현
- [ ] router 등록
- [ ] 통합 테스트 3 TC

---

## 7. E1-5: Dashboard CRUD UI (~1.5시간)

### 7.1 변경

**파일**: `dashboard/index.html` (수정)

### 7.2 위치

설정 메뉴 또는 별도 "내 메모리" 패널.

### 7.3 기능

- **목록 표시**: `GET /api/v2/memory/list` 호출
- **개별 삭제**: 각 entry 옆 🗑 버튼 → `DELETE /{id}`
- **전체 삭제**: "내 메모리 모두 삭제" 버튼 (확인 dialog) → `DELETE /user/{id}`
- **표시 항목**: type, key, content (요약), source, created_at

### 7.4 UI 골격 (HTML)

```html
<!-- 메모리 패널 (설정 메뉴 안) -->
<div id="memory-panel" class="hidden">
    <h3>내 메모리</h3>
    <div id="memory-list"></div>
    <button id="memory-clear-all" class="danger">전체 삭제</button>
</div>

<script>
async function loadMemory() {
    const res = await fetch(`/api/v2/memory/list?user_id=${USER_ID}`);
    const entries = await res.json();
    const html = entries.map(e => `
        <div class="memory-item">
            <span class="type">${e.type}</span>
            <span class="key">${e.key}</span>
            <span class="content">${JSON.stringify(e.content)}</span>
            <button onclick="deleteMemory('${e.id}')">🗑</button>
        </div>
    `).join('');
    document.getElementById('memory-list').innerHTML = html;
}

async function deleteMemory(id) {
    if (!confirm('이 메모리를 삭제할까요?')) return;
    await fetch(`/api/v2/memory/${id}`, { method: 'DELETE' });
    loadMemory();
}

async function clearAllMemory() {
    if (!confirm('내 메모리를 모두 삭제할까요? 되돌릴 수 없습니다.')) return;
    await fetch(`/api/v2/memory/user/${USER_ID}`, { method: 'DELETE' });
    loadMemory();
}
</script>
```

### 7.5 Acceptance — E1-5

- [ ] 메모리 패널 UI 추가
- [ ] 목록 로드 정상
- [ ] 개별 삭제 정상
- [ ] 전체 삭제 정상 (확인 dialog 포함)
- [ ] 사용자 브라우저 검증

---

## 8. 검증 / 테스트 strategy

### 8.1 자동 테스트

```bash
# Group I (Memory) 단위
pytest backend/tests/sprint15/test_memory_manager_unit.py -v

# API 통합
pytest backend/tests/sprint15/test_memory_api_integration.py -v

# 전체 회귀
pytest backend/tests/ -v --tb=short
```

**기대**: 254+ passed.

### 8.2 사용자 브라우저 검증

- 메모리 패널 표시
- entry 추가 (다른 경로 = Phase E-2/E-3 후) 후 표시 확인
- 개별 / 전체 삭제 정상

### 8.3 DB 직접 검증

```sql
SELECT * FROM memory_entries ORDER BY created_at DESC LIMIT 10;
SELECT type, COUNT(*) FROM memory_entries GROUP BY type;
```

---

## 9. Risk + 완화

| Risk | 완화 |
|------|------|
| asyncpg pool 공유 (Checkpointer 와) | 같은 pool 사용 — main.py lifespan 단일 pool |
| JSONB content schema 진화 | Pydantic content 별도 schema (필요 시 version 필드) |
| TTL 만료 entry 누적 | Sprint 16+ 정기 cleanup job (POC = 미구현) |
| 인덱스 부족 시 search 느림 | scope + type 복합 인덱스 + content GIN 으로 cover |
| Singleton init 누락 (test 등) | `init_memory_manager()` lifespan 보장 + test fixture |
| 사용자 메모리 삭제 후 진행 중 cascade 영향 | 삭제 시 in-memory cache 도 invalidate (Phase E-2 통합 시 처리) |

---

## 10. 완료 체크리스트

### E1-1 DB 마이그레이션
- [ ] 테이블 생성
- [ ] 인덱스 + trigger
- [ ] 샘플 INSERT/SELECT

### E1-2 Pydantic models
- [ ] `models/memory.py` 신규
- [ ] export 추가

### E1-3 MemoryManager
- [ ] `db.py` 5 메서드
- [ ] `manager.py` 7 P0 메서드
- [ ] `__init__.py` singleton
- [ ] `main.py` lifespan 통합
- [ ] Group I 10 TC 통과

### E1-4 API endpoint
- [ ] `memory.py` router 신규
- [ ] 3 endpoint
- [ ] router 등록
- [ ] 통합 테스트 3 TC

### E1-5 Dashboard UI
- [ ] 메모리 패널
- [ ] 목록 / 삭제 / 전체 삭제
- [ ] 브라우저 검증

### Phase E-1 종합
- [ ] 자동 테스트 254+ passed
- [ ] 커밋 (`feat(sprint15): Phase E-1 메모리 인프라 — DB + Manager + API + UI`)
- [ ] 다음 [`sprint15_phase_e2_chat_memory.md`](./sprint15_phase_e2_chat_memory.md)

---

## 11. 다음 Phase 연결

Phase E-1 완료 후 → **Phase E-2**: 채팅 메모리 통합 (5 항목 #2/#3/#4)

[`sprint15_phase_e2_chat_memory.md`](./sprint15_phase_e2_chat_memory.md) 참조.

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-28 | 초안 — Phase E-1 5 sub-phase. DB / models / Manager / API / UI 모든 작업. ~6h 추정. Group I 10 TC |
| 2026-04-28 | **conversation_meta type 추가** — Phase E-2 E2-5 (Conversation list sidebar) 의존성. DB CHECK constraint + MemoryType Literal 갱신 (8 type 으로) |
