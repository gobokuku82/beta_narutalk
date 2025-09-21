# Database Layer 분석 보고서
> 데이터베이스 구조 및 관리 시스템 상세 분석

## 목차
1. [데이터베이스 아키텍처](#데이터베이스-아키텍처)
2. [Database API](#database-api)
3. [데이터 모델](#데이터-모델)
4. [CRUD 작업](#crud-작업)
5. [멀티 데이터베이스 관리](#멀티-데이터베이스-관리)
6. [스키마 및 검증](#스키마-및-검증)

---

## 데이터베이스 아키텍처

### 전체 구조
```
┌─────────────────────────────────────────────────────┐
│              Database API (Port 8002)               │
│  ┌────────────────────────────────────────────────┐ │
│  │  FastAPI Application (database/api/main.py)    │ │
│  └────────────────┬───────────────────────────────┘ │
│                   │                                  │
│  ┌────────────────▼───────────────────────────────┐ │
│  │     Routes (database/api/routes.py)            │ │
│  └────────────────┬───────────────────────────────┘ │
└───────────────────┼──────────────────────────────────┘
                    │
    ┌───────────────▼──────────────────┐
    │   Database Manager               │
    │  (database/system/db_manager.py) │
    └───────────────┬──────────────────┘
                    │
    ┌───────────────▼──────────────────────────────┐
    │           SQLite Databases                    │
    ├───────────────────────────────────────────────┤
    │ • Main DB (pharma_chatbot.db)                 │
    │ • HR DB (hr_data.db)                         │
    │ • Sales DB (sales_performance_db.db)         │
    │ • Rules DB (rules.db, hr_rules.db)           │
    └───────────────────────────────────────────────┘
```

### 데이터베이스 분류

| 데이터베이스 | 파일 경로 | 용도 | 주요 테이블 |
|------------|----------|------|------------|
| **Main DB** | `./pharma_chatbot.db` | 대화 및 세션 관리 | conversations, messages, agent_states |
| **HR DB** | `database/storage/hr_information/hr_data.db` | 인사 정보 | employees, departments, positions |
| **Sales DB** | `database/storage/sales_performance/sales_performance_db.db` | 매출 성과 | sales, targets, performance |
| **HR Rules DB** | `database/storage/hr_rules/hr_rules.db` | 인사 규정 | hr_policies, procedures |
| **Rules DB** | `database/storage/rules_compliance/rules.db` | 일반 규정 | regulations, compliance |

---

## Database API

### **database/api/main.py**

#### FastAPI 애플리케이션 구조
```python
app = FastAPI(
    title="Database API",
    description="Database service for NaruTalk system",
    version="1.0.0"
)
```

#### 주요 엔드포인트

##### 대화 관리
| 엔드포인트 | 메소드 | 기능 | 입력 | 출력 |
|-----------|--------|------|------|------|
| `/conversations` | POST | 대화 생성 | ConversationCreate | Conversation |
| `/conversations/{id}` | GET | 대화 조회 | conversation_id | Conversation |
| `/conversations` | GET | 대화 목록 | user_id, limit | List[Conversation] |

##### 메시지 관리
| 엔드포인트 | 메소드 | 기능 | 입력 | 출력 |
|-----------|--------|------|------|------|
| `/messages` | POST | 메시지 생성 | MessageCreate | Message |
| `/conversations/{id}/messages` | GET | 메시지 조회 | conversation_id, limit | List[Message] |

##### 상태 관리
| 엔드포인트 | 메소드 | 기능 | 입력 | 출력 |
|-----------|--------|------|------|------|
| `/agent-states` | POST | 에이전트 상태 저장 | AgentStateCreate | AgentState |
| `/agent-states/{id}` | GET | 상태 조회 | conversation_id | List[AgentState] |

##### 분석 결과
| 엔드포인트 | 메소드 | 기능 | 입력 | 출력 |
|-----------|--------|------|------|------|
| `/analysis-results` | POST | 분석 결과 저장 | AnalysisResultCreate | AnalysisResult |
| `/analysis-results` | GET | 결과 조회 | conversation_id | List[AnalysisResult] |

### **database/api/routes.py**

#### Worker Agent 전용 엔드포인트

##### SQL 실행
```python
@router.post("/execute-sql")
async def execute_sql(request: SQLExecuteRequest) -> SQLExecuteResponse
```
- **지원 데이터베이스**: hr, sales, rules, hr_rules
- **보안**: SQL Injection 방지 로직
- **타임아웃**: 30초 제한

##### 스키마 조회
```python
@router.get("/schema/{table_name}")
async def get_table_schema(
    table_name: str,
    database: str = Query(...)
) -> TableSchema
```
- **반환 정보**: 컬럼명, 타입, 제약조건
- **캐싱**: 스키마 정보 캐싱

##### 검색 기능
```python
@router.post("/search/hr")
async def search_hr(request: HRSearchRequest) -> List[HRRecord]

@router.post("/search/regulations")
async def search_regulations(request: RegulationSearchRequest) -> List[Regulation]
```

---

## 데이터 모델

### **database/system/models.py**

#### 핵심 모델 정의

##### Conversation 모델
```python
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, index=True)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    metadata = Column(JSON)

    # Relationships
    messages = relationship("Message", back_populates="conversation")
    agent_states = relationship("AgentState", back_populates="conversation")
    analysis_results = relationship("AnalysisResult", back_populates="conversation")
```

##### Message 모델
```python
class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(Enum(MessageRole))  # user, assistant, system
    content = Column(Text)
    sequence_number = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
```

##### AgentState 모델
```python
class AgentState(Base):
    __tablename__ = "agent_states"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    agent_type = Column(Enum(AgentType))
    state_data = Column(JSON)  # Serialized state
    execution_status = Column(Enum(ExecutionStatus))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    # Index for fast lookups
    __table_args__ = (
        Index("idx_agent_conversation", "conversation_id", "agent_type"),
    )
```

##### AnalysisResult 모델
```python
class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    query = Column(Text)
    result_type = Column(String)  # sql, search, document, compliance
    result_data = Column(JSON)
    confidence_score = Column(Float)
    processing_time = Column(Float)
    created_at = Column(DateTime)
```

#### 추가 모델

##### Document 모델
```python
class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    document_type = Column(String)
    file_path = Column(String)
    content = Column(Text)
    metadata = Column(JSON)
    created_at = Column(DateTime)
```

##### ComplianceCheck 모델
```python
class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.id"))
    rule_id = Column(String)
    is_compliant = Column(Boolean)
    violations = Column(JSON)
    suggestions = Column(JSON)
    checked_at = Column(DateTime)
```

##### AuditLog 모델
```python
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True)
    user_id = Column(String)
    action = Column(String)
    resource_type = Column(String)
    resource_id = Column(String)
    details = Column(JSON)
    ip_address = Column(String)
    timestamp = Column(DateTime)
```

---

## CRUD 작업

### **database/system/crud.py**

#### 대화 관리 CRUD

##### 대화 생성
```python
async def create_conversation(
    db: AsyncSession,
    conversation: ConversationCreate
) -> Conversation:
    """새 대화 생성"""
    db_conversation = Conversation(
        user_id=conversation.user_id,
        title=conversation.title or f"Conversation {datetime.now()}",
        metadata=conversation.metadata
    )
    db.add(db_conversation)
    await db.commit()
    await db.refresh(db_conversation)
    return db_conversation
```

##### 대화 목록 조회
```python
async def list_conversations(
    db: AsyncSession,
    user_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Conversation]:
    """페이지네이션을 포함한 대화 목록 조회"""
    query = select(Conversation)
    if user_id:
        query = query.filter(Conversation.user_id == user_id)
    query = query.order_by(desc(Conversation.updated_at))
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()
```

#### 메시지 관리 CRUD

##### 메시지 생성 with 시퀀스
```python
async def create_message(
    db: AsyncSession,
    message: MessageCreate
) -> Message:
    """시퀀스 번호 자동 할당하여 메시지 생성"""
    # 마지막 시퀀스 번호 조회
    last_seq = await db.execute(
        select(func.max(Message.sequence_number))
        .filter(Message.conversation_id == message.conversation_id)
    )
    next_seq = (last_seq.scalar() or 0) + 1

    db_message = Message(
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        sequence_number=next_seq,
        metadata=message.metadata
    )
    db.add(db_message)
    await db.commit()
    return db_message
```

#### 에이전트 상태 CRUD

##### Upsert 패턴
```python
async def create_or_update_agent_state(
    db: AsyncSession,
    state: AgentStateCreate
) -> AgentState:
    """에이전트 상태 생성 또는 업데이트"""
    existing = await db.execute(
        select(AgentState).filter(
            and_(
                AgentState.conversation_id == state.conversation_id,
                AgentState.agent_type == state.agent_type
            )
        )
    )

    if db_state := existing.scalar_one_or_none():
        # 업데이트
        db_state.state_data = state.state_data
        db_state.execution_status = state.execution_status
        db_state.updated_at = datetime.utcnow()
    else:
        # 생성
        db_state = AgentState(**state.dict())
        db.add(db_state)

    await db.commit()
    return db_state
```

#### 통계 및 분석

##### 데이터베이스 통계
```python
async def get_database_statistics(db: AsyncSession) -> Dict:
    """데이터베이스 사용 통계"""
    stats = {}

    # 대화 통계
    total_conversations = await db.scalar(
        select(func.count(Conversation.id))
    )

    # 메시지 통계
    total_messages = await db.scalar(
        select(func.count(Message.id))
    )

    # 평균 메시지 수
    avg_messages = await db.scalar(
        select(func.avg(
            select(func.count(Message.id))
            .filter(Message.conversation_id == Conversation.id)
            .scalar_subquery()
        ))
    )

    # 활성 사용자 수
    active_users = await db.scalar(
        select(func.count(func.distinct(Conversation.user_id)))
    )

    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "avg_messages_per_conversation": avg_messages,
        "active_users": active_users
    }
```

---

## 멀티 데이터베이스 관리

### **database/system/db_manager.py**

#### DatabaseManager 클래스

##### 초기화 및 설정
```python
class DatabaseManager:
    def __init__(self):
        self.databases = {
            "hr": "database/storage/hr_information/hr_data.db",
            "sales": "database/storage/sales_performance/sales_performance_db.db",
            "rules": "database/storage/rules_compliance/rules.db",
            "hr_rules": "database/storage/hr_rules/hr_rules.db"
        }
        self.connections = {}
        self.schema_cache = {}
        self._lock = asyncio.Lock()
```

##### 연결 관리
```python
@contextmanager
def get_connection(self, db_name: str):
    """컨텍스트 매니저를 통한 연결 관리"""
    if db_name not in self.databases:
        raise ValueError(f"Unknown database: {db_name}")

    db_path = self.databases[db_name]
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        yield conn
    finally:
        conn.close()
```

##### 쿼리 실행
```python
async def execute_query(
    self,
    db_name: str,
    query: str,
    timeout: int = 30
) -> List[Dict]:
    """비동기 쿼리 실행 with 타임아웃"""
    async with self._lock:
        try:
            # 비동기 실행을 위한 스레드 풀 사용
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    self._execute_sync,
                    db_name,
                    query
                ),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(f"Query exceeded {timeout}s timeout")
```

##### 스키마 관리
```python
def get_table_schema(self, db_name: str, table_name: str) -> Dict:
    """테이블 스키마 조회 및 캐싱"""
    cache_key = f"{db_name}:{table_name}"

    if cache_key in self.schema_cache:
        return self.schema_cache[cache_key]

    with self.get_connection(db_name) as conn:
        cursor = conn.cursor()

        # PRAGMA를 이용한 테이블 정보 조회
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        # 인덱스 정보
        cursor.execute(f"PRAGMA index_list({table_name})")
        indexes = cursor.fetchall()

        schema = {
            "table_name": table_name,
            "columns": [
                {
                    "name": col["name"],
                    "type": col["type"],
                    "nullable": not col["notnull"],
                    "primary_key": bool(col["pk"]),
                    "default": col["dflt_value"]
                }
                for col in columns
            ],
            "indexes": [
                {
                    "name": idx["name"],
                    "unique": bool(idx["unique"])
                }
                for idx in indexes
            ]
        }

        self.schema_cache[cache_key] = schema
        return schema
```

##### 크로스 데이터베이스 검색
```python
async def search_tables(
    self,
    search_term: str,
    databases: Optional[List[str]] = None
) -> Dict[str, List[Dict]]:
    """여러 데이터베이스에서 동시 검색"""
    if databases is None:
        databases = list(self.databases.keys())

    results = {}
    tasks = []

    for db_name in databases:
        if db_name in self.databases:
            task = self._search_in_database(db_name, search_term)
            tasks.append(task)

    # 병렬 검색 실행
    search_results = await asyncio.gather(*tasks)

    for db_name, result in zip(databases, search_results):
        results[db_name] = result

    return results
```

---

## 스키마 및 검증

### **database/system/schemas.py**

#### Pydantic 스키마 정의

##### 요청 스키마
```python
class ConversationCreate(BaseModel):
    user_id: str
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "title": "의약품 안전성 문의",
                "metadata": {"department": "QA"}
            }
        }

class MessageCreate(BaseModel):
    conversation_id: str
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None

    @validator("role")
    def validate_role(cls, v):
        if v not in MessageRole.__members__.values():
            raise ValueError(f"Invalid role: {v}")
        return v
```

##### 응답 스키마
```python
class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]
    message_count: Optional[int]

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    sequence_number: int
    created_at: datetime
    metadata: Optional[Dict[str, Any]]

    class Config:
        orm_mode = True
```

##### 복합 상태 스키마
```python
class GlobalSessionState(BaseModel):
    """LangGraph 워크플로우 전체 상태"""
    session_id: str
    current_step: str
    query: str
    user_context: Dict[str, Any]

    # 각 에이전트별 상태
    intent_analysis: Optional[IntentAnalysisState]
    planning: Optional[PlanningState]
    agent_selection: Optional[AgentSelectionState]
    execution: Optional[ExecutionManagerState]

    # 메타데이터
    timestamps: Dict[str, datetime]
    performance_metrics: Dict[str, float]
    error_log: List[Dict[str, Any]]

    @validator("timestamps", pre=True)
    def parse_timestamps(cls, v):
        if isinstance(v, dict):
            return {
                k: datetime.fromisoformat(v) if isinstance(v, str) else v
                for k, v in v.items()
            }
        return v
```

##### 검증 함수
```python
class DataValidator:
    @staticmethod
    def validate_sql_query(query: str) -> bool:
        """SQL 쿼리 안전성 검증"""
        forbidden_keywords = [
            "DROP", "DELETE", "TRUNCATE", "ALTER",
            "CREATE", "REPLACE", "INSERT", "UPDATE"
        ]

        query_upper = query.upper()
        for keyword in forbidden_keywords:
            if keyword in query_upper:
                return False
        return True

    @staticmethod
    def validate_json_structure(data: Any, schema: Dict) -> bool:
        """JSON 스키마 검증"""
        try:
            jsonschema.validate(instance=data, schema=schema)
            return True
        except jsonschema.ValidationError:
            return False
```

---

## 연결 관리

### **database/system/connection.py**

#### 비동기 SQLAlchemy 설정
```python
# 데이터베이스 URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./pharma_chatbot.db"
)

# 엔진 생성
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # SQL 로깅 비활성화
    pool_size=20,  # 연결 풀 크기
    max_overflow=10,  # 최대 오버플로우
    pool_timeout=30,  # 연결 타임아웃
    pool_recycle=3600  # 연결 재활용 시간
)

# 세션 팩토리
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)
```

#### 데이터베이스 초기화
```python
async def init_db():
    """데이터베이스 테이블 생성"""
    async with engine.begin() as conn:
        # 테이블 생성
        await conn.run_sync(Base.metadata.create_all)

        # 초기 인덱스 생성
        await create_indexes(conn)

        # 초기 데이터 로드
        await load_initial_data(conn)

async def create_indexes(conn):
    """성능 최적화를 위한 인덱스 생성"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id)",
        "CREATE INDEX IF NOT EXISTS idx_state_conv ON agent_states(conversation_id)",
        "CREATE INDEX IF NOT EXISTS idx_result_conv ON analysis_results(conversation_id)"
    ]

    for index in indexes:
        await conn.execute(text(index))
```

#### 의존성 주입
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 의존성 주입용 세션 제공"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

---

## 성능 최적화

### 인덱싱 전략
| 테이블 | 인덱스 | 용도 |
|--------|--------|------|
| conversations | user_id | 사용자별 조회 |
| messages | conversation_id | 대화별 메시지 |
| messages | (conversation_id, sequence_number) | 순서 정렬 |
| agent_states | (conversation_id, agent_type) | 상태 조회 |
| analysis_results | conversation_id | 결과 조회 |

### 쿼리 최적화
```python
# N+1 문제 방지 - Eager Loading
query = select(Conversation).options(
    selectinload(Conversation.messages),
    selectinload(Conversation.agent_states)
)

# 배치 처리
async def batch_insert(db: AsyncSession, items: List[Any]):
    db.add_all(items)
    await db.commit()
```

### 캐싱 전략
- **스키마 캐싱**: 테이블 구조 메모리 캐싱
- **결과 캐싱**: 자주 조회되는 데이터 캐싱
- **연결 풀링**: 데이터베이스 연결 재사용

---

## 백업 및 복구

### 백업 전략
```python
async def backup_database(db_name: str, backup_path: str):
    """데이터베이스 백업"""
    source_path = DatabaseManager.databases[db_name]

    # SQLite 백업 API 사용
    with sqlite3.connect(source_path) as source:
        with sqlite3.connect(backup_path) as backup:
            source.backup(backup)

    # 백업 검증
    if not verify_backup(backup_path):
        raise BackupError("Backup verification failed")
```

### 복구 프로세스
```python
async def restore_database(db_name: str, backup_path: str):
    """데이터베이스 복구"""
    # 기존 데이터베이스 백업
    await create_safety_backup(db_name)

    # 복구 실행
    target_path = DatabaseManager.databases[db_name]
    shutil.copy2(backup_path, target_path)

    # 무결성 검사
    await verify_database_integrity(db_name)
```

---

## 보안 고려사항

### SQL Injection 방지
```python
# 파라미터화된 쿼리 사용
query = text(
    "SELECT * FROM users WHERE id = :user_id"
).bindparams(user_id=user_id)

# 위험한 작업 차단
def is_safe_query(query: str) -> bool:
    dangerous_patterns = [
        r";\s*DROP\s+",
        r";\s*DELETE\s+",
        r"--",
        r"/\*.*\*/"
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return False
    return True
```

### 접근 제어
- **읽기 전용 연결**: SELECT만 허용
- **권한 분리**: 작업별 다른 권한
- **감사 로깅**: 모든 작업 기록

---

## 모니터링

### 성능 메트릭
```python
class DatabaseMonitor:
    async def get_metrics(self) -> Dict:
        return {
            "connection_pool_size": engine.pool.size(),
            "active_connections": engine.pool.checked_out(),
            "query_performance": await self.get_slow_queries(),
            "table_sizes": await self.get_table_sizes(),
            "cache_hit_rate": self.calculate_cache_hit_rate()
        }
```

### 헬스 체크
```python
async def health_check() -> Dict:
    """데이터베이스 상태 확인"""
    try:
        # 연결 테스트
        async with get_db() as db:
            await db.execute(text("SELECT 1"))

        # 모든 데이터베이스 확인
        manager = DatabaseManager()
        all_healthy = await manager.check_all_connections()

        return {
            "status": "healthy" if all_healthy else "degraded",
            "main_db": "connected",
            "specialized_dbs": manager.get_connection_status()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

---

## 결론

데이터베이스 계층은 메인 대화 관리 데이터베이스와 도메인별 특화 데이터베이스를 효과적으로 관리하는 통합 시스템을 제공합니다. 비동기 처리, 강력한 스키마 검증, 멀티 데이터베이스 지원, 그리고 포괄적인 CRUD 작업을 통해 안정적이고 확장 가능한 데이터 관리 기반을 구축하고 있습니다. 특히 성능 최적화, 보안, 그리고 모니터링 기능을 통해 엔터프라이즈 수준의 데이터베이스 서비스를 제공합니다.