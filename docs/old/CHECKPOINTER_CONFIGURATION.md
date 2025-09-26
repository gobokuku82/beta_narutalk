# AsyncSqliteSaver Checkpointer 설정 가이드

## 1. AsyncSqliteSaver 최신 버전 설정

### 1.1 필요 패키지
```bash
pip install langgraph>=0.2.0
pip install aiosqlite
```

### 1.2 폴더 구조
```
database/
├── checkpointer/          # 체크포인트 저장 위치
│   ├── supervisor.db      # Supervisor 체크포인트
│   ├── agents.db          # Agent별 체크포인트
│   └── conversations.db   # 대화 세션 체크포인트
├── raw_data/              # 기존 데이터베이스
│   ├── hr.db
│   ├── sales.db
│   └── rules.db
└── store/                 # Store 데이터 (향후 구현)
    └── memory.db
```

## 2. Supervisor에서 AsyncSqliteSaver 설정

### 2.1 기본 설정
```python
# backend/service/supervisor/main_supervisor.py

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import os
from pathlib import Path

class MedicalSupervisor:
    def __init__(
        self,
        llm_provider: str = "openai",
        model_name: Optional[str] = None,
        checkpoint_path: str = None  # 체크포인트 경로
    ):
        # 체크포인트 경로 설정
        if checkpoint_path is None:
            # 기본 경로: database/checkpointer/supervisor.db
            base_dir = Path(__file__).parent.parent.parent.parent  # 프로젝트 루트
            checkpoint_path = base_dir / "database" / "checkpointer" / "supervisor.db"

        # 디렉토리 생성
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        # AsyncSqliteSaver 초기화는 async 함수에서
        self.checkpoint_path = str(checkpoint_path)
        self.checkpointer = None  # await self._init_checkpointer()에서 설정

    async def _init_checkpointer(self):
        """비동기 체크포인터 초기화"""
        self.checkpointer = AsyncSqliteSaver.from_conn_string(
            str(self.checkpoint_path)
        )
        # 테이블 자동 생성
        await self.checkpointer.setup()
        return self.checkpointer
```

### 2.2 Graph Compile 시 Checkpointer 연결
```python
async def compile_graph(self):
    """그래프 컴파일 (비동기)"""

    # 체크포인터 초기화
    if self.checkpointer is None:
        await self._init_checkpointer()

    # StateGraph 생성
    workflow = StateGraph(MedicalSupervisorState)

    # 노드 추가
    workflow.add_node("supervisor", self.supervisor_node)
    workflow.add_node("sql_analysis", self.sql_analysis_node)
    workflow.add_node("information_retrieval", self.information_retrieval_node)
    # ... 다른 노드들

    # 엣지 추가
    workflow.set_entry_point("supervisor")
    # ... 엣지 설정

    # 컴파일 시 checkpointer 포함
    self.app = workflow.compile(
        checkpointer=self.checkpointer,
        interrupt_before=[],  # 필요시 중단 지점 설정
        interrupt_after=[]
    )

    return self.app
```

## 3. Agent별 체크포인터 설정

### 3.1 개별 Agent 체크포인터
```python
# backend/service/worker_agents/base_agent.py

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from pathlib import Path
import asyncio

class BaseAgent:
    """모든 Agent의 베이스 클래스"""

    def __init__(self, agent_name: str, checkpoint_enabled: bool = True):
        self.agent_name = agent_name
        self.checkpoint_enabled = checkpoint_enabled

        if checkpoint_enabled:
            # Agent별 체크포인트 경로
            base_dir = Path(__file__).parent.parent.parent.parent
            checkpoint_dir = base_dir / "database" / "checkpointer"
            checkpoint_dir.mkdir(parents=True, exist_ok=True)

            # agents.db 사용 (모든 agent 공유)
            self.checkpoint_path = checkpoint_dir / "agents.db"
            self.checkpointer = None

    async def init_checkpointer(self):
        """체크포인터 비동기 초기화"""
        if self.checkpoint_enabled:
            self.checkpointer = AsyncSqliteSaver.from_conn_string(
                str(self.checkpoint_path)
            )
            await self.checkpointer.setup()

    async def save_checkpoint(self, thread_id: str, state: dict):
        """체크포인트 저장"""
        if self.checkpointer:
            config = {"configurable": {"thread_id": thread_id}}
            await self.checkpointer.aput(
                config=config,
                checkpoint={
                    "agent": self.agent_name,
                    "state": state,
                    "timestamp": datetime.now().isoformat()
                },
                metadata={
                    "agent_name": self.agent_name,
                    "source": "agent_checkpoint"
                }
            )

    async def load_checkpoint(self, thread_id: str):
        """체크포인트 로드"""
        if self.checkpointer:
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint = await self.checkpointer.aget(config)
            return checkpoint.get("state") if checkpoint else None
```

### 3.2 SQL Analysis Agent 예제
```python
# backend/service/worker_agents/sql_analysis_agent.py

class SQLAnalysisAgent(BaseAgent):
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        super().__init__(agent_name="sql_analysis_agent")
        self.api_base_url = api_base_url
        # ... 기타 초기화

    async def analyze_query(self, request: SQLQueryRequest, thread_id: str = None):
        """쿼리 분석 (체크포인트 지원)"""

        # 체크포인터 초기화
        if self.checkpointer is None:
            await self.init_checkpointer()

        # 이전 상태 로드
        if thread_id:
            previous_state = await self.load_checkpoint(thread_id)
            if previous_state:
                logger.info(f"Loaded previous state for thread {thread_id}")

        # 분석 수행
        result = await self._perform_analysis(request)

        # 체크포인트 저장
        if thread_id:
            await self.save_checkpoint(
                thread_id=thread_id,
                state={
                    "request": request.dict(),
                    "result": result.dict(),
                    "timestamp": datetime.now().isoformat()
                }
            )

        return result
```

## 4. 대화 세션 관리

### 4.1 Conversation Checkpointer
```python
# backend/service/conversation_manager.py

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from pathlib import Path
import uuid

class ConversationManager:
    """대화 세션 관리"""

    def __init__(self):
        base_dir = Path(__file__).parent.parent.parent
        checkpoint_path = base_dir / "database" / "checkpointer" / "conversations.db"
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        self.checkpoint_path = str(checkpoint_path)
        self.checkpointer = None

    async def init(self):
        """비동기 초기화"""
        self.checkpointer = AsyncSqliteSaver.from_conn_string(
            self.checkpoint_path
        )
        await self.checkpointer.setup()

    async def create_session(self, user_id: str) -> str:
        """새 세션 생성"""
        session_id = str(uuid.uuid4())

        config = {"configurable": {"thread_id": session_id}}

        await self.checkpointer.aput(
            config=config,
            checkpoint={
                "session_id": session_id,
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "messages": [],
                "context": {}
            },
            metadata={
                "source": "conversation_manager",
                "user_id": user_id
            }
        )

        return session_id

    async def add_message(self, session_id: str, message: dict):
        """메시지 추가"""
        config = {"configurable": {"thread_id": session_id}}

        # 현재 체크포인트 로드
        checkpoint = await self.checkpointer.aget(config)

        if checkpoint:
            messages = checkpoint.get("messages", [])
            messages.append(message)

            checkpoint["messages"] = messages
            checkpoint["updated_at"] = datetime.now().isoformat()

            # 업데이트된 체크포인트 저장
            await self.checkpointer.aput(
                config=config,
                checkpoint=checkpoint,
                metadata={
                    "message_count": len(messages),
                    "last_message_at": datetime.now().isoformat()
                }
            )

    async def get_session_history(self, session_id: str):
        """세션 히스토리 조회"""
        config = {"configurable": {"thread_id": session_id}}
        checkpoint = await self.checkpointer.aget(config)

        if checkpoint:
            return checkpoint.get("messages", [])
        return []

    async def list_sessions(self, user_id: str = None):
        """세션 목록 조회"""
        # 모든 체크포인트 조회
        checkpoints = []

        async for config, checkpoint, metadata in self.checkpointer.alist():
            if user_id and metadata.get("user_id") != user_id:
                continue

            checkpoints.append({
                "session_id": checkpoint.get("session_id"),
                "user_id": checkpoint.get("user_id"),
                "created_at": checkpoint.get("created_at"),
                "message_count": len(checkpoint.get("messages", []))
            })

        return checkpoints
```

## 5. FastAPI 통합

### 5.1 API 엔드포인트
```python
# database/checkpoint_api.py

from fastapi import FastAPI, HTTPException
from typing import Dict, Any, List
from conversation_manager import ConversationManager

app = FastAPI()
conversation_manager = ConversationManager()

@app.on_event("startup")
async def startup():
    """서버 시작 시 초기화"""
    await conversation_manager.init()

@app.post("/api/v1/sessions")
async def create_session(user_id: str) -> Dict[str, str]:
    """새 세션 생성"""
    session_id = await conversation_manager.create_session(user_id)
    return {"session_id": session_id}

@app.post("/api/v1/sessions/{session_id}/messages")
async def add_message(session_id: str, message: Dict[str, Any]):
    """메시지 추가"""
    await conversation_manager.add_message(session_id, message)
    return {"status": "success"}

@app.get("/api/v1/sessions/{session_id}/history")
async def get_history(session_id: str) -> List[Dict]:
    """세션 히스토리 조회"""
    history = await conversation_manager.get_session_history(session_id)
    return history

@app.get("/api/v1/sessions")
async def list_sessions(user_id: str = None) -> List[Dict]:
    """세션 목록 조회"""
    sessions = await conversation_manager.list_sessions(user_id)
    return sessions
```

## 6. 마이그레이션 및 백업

### 6.1 기존 체크포인트 마이그레이션
```python
# scripts/migrate_checkpoints.py

import asyncio
import shutil
from pathlib import Path
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async def migrate_checkpoints():
    """기존 체크포인트를 새 위치로 마이그레이션"""

    # 이전 경로
    old_path = Path("data/checkpoints.db")

    # 새 경로
    new_dir = Path("database/checkpointer")
    new_dir.mkdir(parents=True, exist_ok=True)
    new_path = new_dir / "supervisor.db"

    if old_path.exists():
        # 파일 복사
        shutil.copy2(old_path, new_path)
        print(f"Migrated {old_path} to {new_path}")

        # 검증
        checkpointer = AsyncSqliteSaver.from_conn_string(str(new_path))
        await checkpointer.setup()

        # 체크포인트 개수 확인
        count = 0
        async for _ in checkpointer.alist():
            count += 1

        print(f"Verified: {count} checkpoints in new location")

if __name__ == "__main__":
    asyncio.run(migrate_checkpoints())
```

### 6.2 자동 백업 설정
```python
# scripts/backup_checkpoints.py

import asyncio
import shutil
from pathlib import Path
from datetime import datetime

async def backup_checkpoints():
    """체크포인트 백업"""

    checkpoint_dir = Path("database/checkpointer")
    backup_dir = Path("database/backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)

    for db_file in checkpoint_dir.glob("*.db"):
        backup_path = backup_dir / db_file.name
        shutil.copy2(db_file, backup_path)
        print(f"Backed up {db_file} to {backup_path}")

    # 오래된 백업 제거 (30일 이상)
    backup_root = Path("database/backups")
    cutoff_date = datetime.now().timestamp() - (30 * 24 * 60 * 60)

    for old_backup in backup_root.iterdir():
        if old_backup.stat().st_mtime < cutoff_date:
            shutil.rmtree(old_backup)
            print(f"Removed old backup: {old_backup}")

if __name__ == "__main__":
    asyncio.run(backup_checkpoints())
```

## 7. 환경 변수 설정

### 7.1 .env 파일
```bash
# .env
CHECKPOINT_DIR=database/checkpointer
CHECKPOINT_SUPERVISOR_DB=supervisor.db
CHECKPOINT_AGENTS_DB=agents.db
CHECKPOINT_CONVERSATIONS_DB=conversations.db

# 백업 설정
BACKUP_DIR=database/backups
BACKUP_RETENTION_DAYS=30
AUTO_BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"  # 매일 새벽 2시

# 성능 설정
SQLITE_JOURNAL_MODE=WAL
SQLITE_SYNCHRONOUS=NORMAL
SQLITE_CACHE_SIZE=10000
```

### 7.2 설정 로더
```python
# backend/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class CheckpointerConfig:
    """체크포인터 설정"""

    BASE_DIR = Path(__file__).parent.parent

    # 체크포인트 디렉토리
    CHECKPOINT_DIR = BASE_DIR / os.getenv(
        "CHECKPOINT_DIR",
        "database/checkpointer"
    )

    # 데이터베이스 파일
    SUPERVISOR_DB = CHECKPOINT_DIR / os.getenv(
        "CHECKPOINT_SUPERVISOR_DB",
        "supervisor.db"
    )

    AGENTS_DB = CHECKPOINT_DIR / os.getenv(
        "CHECKPOINT_AGENTS_DB",
        "agents.db"
    )

    CONVERSATIONS_DB = CHECKPOINT_DIR / os.getenv(
        "CHECKPOINT_CONVERSATIONS_DB",
        "conversations.db"
    )

    # SQLite 최적화 설정
    SQLITE_CONFIG = {
        "journal_mode": os.getenv("SQLITE_JOURNAL_MODE", "WAL"),
        "synchronous": os.getenv("SQLITE_SYNCHRONOUS", "NORMAL"),
        "cache_size": int(os.getenv("SQLITE_CACHE_SIZE", "10000"))
    }

    @classmethod
    def get_connection_string(cls, db_type: str) -> str:
        """연결 문자열 생성"""
        db_map = {
            "supervisor": cls.SUPERVISOR_DB,
            "agents": cls.AGENTS_DB,
            "conversations": cls.CONVERSATIONS_DB
        }

        db_path = db_map.get(db_type)
        if not db_path:
            raise ValueError(f"Unknown database type: {db_type}")

        # 디렉토리 생성
        db_path.parent.mkdir(parents=True, exist_ok=True)

        return str(db_path)
```

## 8. 테스트 코드

### 8.1 체크포인터 테스트
```python
# tests/test_checkpointer.py

import pytest
import asyncio
from pathlib import Path
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

@pytest.mark.asyncio
async def test_checkpointer_creation():
    """체크포인터 생성 테스트"""

    test_db = Path("database/checkpointer/test.db")
    test_db.parent.mkdir(parents=True, exist_ok=True)

    # 체크포인터 생성
    checkpointer = AsyncSqliteSaver.from_conn_string(str(test_db))
    await checkpointer.setup()

    # 체크포인트 저장
    config = {"configurable": {"thread_id": "test-thread"}}
    await checkpointer.aput(
        config=config,
        checkpoint={"test": "data"},
        metadata={"source": "test"}
    )

    # 체크포인트 로드
    loaded = await checkpointer.aget(config)
    assert loaded["test"] == "data"

    # 정리
    test_db.unlink()

@pytest.mark.asyncio
async def test_multiple_threads():
    """멀티 스레드 체크포인트 테스트"""

    test_db = Path("database/checkpointer/test_multi.db")
    test_db.parent.mkdir(parents=True, exist_ok=True)

    checkpointer = AsyncSqliteSaver.from_conn_string(str(test_db))
    await checkpointer.setup()

    # 여러 스레드에 저장
    for i in range(5):
        config = {"configurable": {"thread_id": f"thread-{i}"}}
        await checkpointer.aput(
            config=config,
            checkpoint={"thread_num": i},
            metadata={"source": "test"}
        )

    # 모든 스레드 확인
    threads = []
    async for config, checkpoint, metadata in checkpointer.alist():
        threads.append(checkpoint["thread_num"])

    assert len(threads) == 5
    assert sorted(threads) == [0, 1, 2, 3, 4]

    # 정리
    test_db.unlink()
```

## 9. 모니터링

### 9.1 체크포인트 상태 모니터링
```python
# scripts/monitor_checkpoints.py

import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime

async def monitor_checkpoints():
    """체크포인트 DB 상태 모니터링"""

    checkpoint_dir = Path("database/checkpointer")

    for db_file in checkpoint_dir.glob("*.db"):
        print(f"\n=== {db_file.name} ===")

        # 파일 크기
        size_mb = db_file.stat().st_size / (1024 * 1024)
        print(f"Size: {size_mb:.2f} MB")

        # 레코드 수
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # 체크포인트 테이블 확인
        cursor.execute("""
            SELECT COUNT(*) FROM checkpoints
        """)
        count = cursor.fetchone()[0]
        print(f"Checkpoints: {count}")

        # 최근 체크포인트
        cursor.execute("""
            SELECT thread_id, checkpoint_ns
            FROM checkpoints
            ORDER BY checkpoint_ns DESC
            LIMIT 5
        """)

        print("Recent checkpoints:")
        for thread_id, checkpoint_ns in cursor.fetchall():
            # nanoseconds to datetime
            dt = datetime.fromtimestamp(checkpoint_ns / 1e9)
            print(f"  - {thread_id}: {dt.isoformat()}")

        conn.close()

if __name__ == "__main__":
    asyncio.run(monitor_checkpoints())
```

## 10. 트러블슈팅

### 10.1 일반적인 문제와 해결

**문제: Database is locked 에러**
```python
# 해결: WAL 모드 활성화
async def setup_wal_mode(db_path: str):
    conn = await aiosqlite.connect(db_path)
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.commit()
    await conn.close()
```

**문제: 체크포인트 파일이 너무 큼**
```python
# 해결: VACUUM 실행
async def vacuum_checkpoint_db(db_path: str):
    conn = await aiosqlite.connect(db_path)
    await conn.execute("VACUUM")
    await conn.close()
```

**문제: 체크포인트 로드 속도가 느림**
```python
# 해결: 인덱스 추가
async def optimize_checkpoint_db(db_path: str):
    conn = await aiosqlite.connect(db_path)

    # thread_id 인덱스
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_thread_id
        ON checkpoints(thread_id)
    """)

    # checkpoint_ns 인덱스
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_checkpoint_ns
        ON checkpoints(checkpoint_ns)
    """)

    await conn.commit()
    await conn.close()
```