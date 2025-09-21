# Backend API 상세 분석 보고서
> FastAPI 기반 백엔드 서비스 구조 및 기능 분석

## 목차
1. [API 메인 애플리케이션](#api-메인-애플리케이션)
2. [Core 모듈 분석](#core-모듈-분석)
3. [Routes 엔드포인트](#routes-엔드포인트)
4. [Services 계층](#services-계층)
5. [미들웨어 구조](#미들웨어-구조)
6. [의존성 주입 패턴](#의존성-주입-패턴)

---

## API 메인 애플리케이션

### **backend/api/main.py**

#### 주요 기능
- FastAPI 애플리케이션 초기화 및 설정
- 라우터 등록 및 경로 관리
- Lifespan 이벤트 처리 (startup/shutdown)
- 전역 에러 핸들링

#### 핵심 구성요소

```python
# 애플리케이션 생성
app = FastAPI(
    title=settings.APP_NAME,           # "NaruTalk Chat API"
    version=settings.APP_VERSION,      # "2.0.0"
    lifespan=lifespan                  # 생명주기 관리
)

# 라우터 등록
- /api/v1/chat      : 대화 처리 엔드포인트
- /api/v1/sessions  : 세션 관리 엔드포인트
- /api/v1/health    : 헬스체크 엔드포인트
```

#### Lifespan 관리
| 이벤트 | 기능 | 상태 |
|--------|------|------|
| Startup | 설정 검증 | `validate_settings()` |
| Startup | Supervisor 초기화 | `get_supervisor_service()` |
| Shutdown | 리소스 정리 | `cleanup_dependencies()` |

---

## Core 모듈 분석

### **1. Configuration (config.py)**

#### Settings 클래스 구조
```python
class Settings(BaseSettings):
    # 애플리케이션 설정
    APP_NAME: str = "NaruTalk Chat API"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str

    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    WORKERS: int = 1

    # 데이터베이스
    DATABASE_API_URL: str = "http://localhost:8002"

    # 캐시 설정
    CACHE_TTL: int = 3600           # 1시간
    CACHE_MAX_SIZE: int = 1000

    # Supervisor 설정
    CHECKPOINT_PATH: str = "./checkpoints"
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4"
```

#### 주요 검증 함수
| 함수명 | 입력 | 출력 | 용도 |
|--------|------|------|------|
| `validate_settings()` | None | bool/Exception | 필수 설정 검증 |
| `get_database_url()` | None | str | DB URL 획득 |
| `get_cache_config()` | None | dict | 캐시 설정 반환 |

### **2. Middleware (middleware.py)**

#### 구현된 미들웨어

##### RequestLoggingMiddleware
- **목적**: 모든 요청 로깅 및 추적
- **기능**:
  - 고유 Request ID 생성 (UUID)
  - 응답 시간 측정
  - 요청/응답 로그 기록

##### RateLimitMiddleware
- **목적**: API 호출 빈도 제한
- **기능**:
  - IP별 호출 횟수 추적
  - 60초당 100회 제한
  - 초과 시 429 상태 코드 반환

##### ErrorHandlingMiddleware
- **목적**: 전역 에러 처리
- **기능**:
  - 예외 캐칭 및 로깅
  - 적절한 HTTP 상태 코드 매핑
  - 클라이언트 친화적 에러 메시지

#### 미들웨어 실행 순서
```
Request → CORS → ErrorHandling → RateLimit → RequestLogging → Application
```

### **3. Dependencies (dependencies.py)**

#### 싱글톤 서비스 관리

| 함수 | 반환 타입 | 용도 | 캐싱 |
|------|----------|------|-------|
| `get_supervisor_service()` | SupervisorService | Supervisor 인스턴스 | @lru_cache |
| `get_cache_manager()` | SQLiteMemoryCache | 캐시 매니저 | @lru_cache |
| `get_database_client()` | DatabaseAPIClient | DB 클라이언트 | @lru_cache |
| `verify_dependencies()` | Dict | 의존성 상태 확인 | None |
| `cleanup_dependencies()` | None | 리소스 정리 | None |

---

## Routes 엔드포인트

### **1. Chat Routes (chat.py)**

#### 주요 엔드포인트

##### POST /api/v1/chat
```python
async def chat(request: ChatRequest) -> ChatResponse
```
- **입력**:
  - `query`: str - 사용자 질문
  - `user_id`: Optional[str] - 사용자 식별자
  - `session_id`: Optional[str] - 세션 ID
  - `context`: Optional[Dict] - 추가 컨텍스트
  - `use_cache`: bool = True - 캐시 사용 여부

- **출력**:
  - `status`: str - "success" | "error"
  - `result`: Dict - 처리 결과
  - `session_id`: str - 세션 식별자
  - `metadata`: Dict - 메타데이터

##### GET /api/v1/chat/stream
```python
async def chat_stream(query: str, ...) -> StreamingResponse
```
- **입력**: Query parameters와 동일
- **출력**: Server-Sent Events (SSE) 스트림
- **이벤트 타입**:
  - `progress`: 진행 상황
  - `token`: 토큰 단위 응답
  - `result`: 최종 결과
  - `error`: 에러 발생

##### POST /api/v1/chat/feedback
```python
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse
```
- **입력**:
  - `session_id`: str
  - `message_id`: str
  - `rating`: int (1-5)
  - `comment`: Optional[str]
- **출력**: 성공 메시지

### **2. Sessions Routes (sessions.py)**

#### 세션 관리 엔드포인트

| 엔드포인트 | 메소드 | 기능 | 입력 | 출력 |
|-----------|--------|------|------|------|
| `/api/v1/sessions` | GET | 세션 목록 조회 | user_id (선택) | SessionListResponse |
| `/api/v1/sessions/{id}` | GET | 특정 세션 조회 | session_id | SessionInfo |
| `/api/v1/sessions/{id}/history` | GET | 대화 이력 조회 | session_id, limit | SessionHistory |
| `/api/v1/sessions/{id}` | DELETE | 세션 삭제 | session_id | 성공 메시지 |
| `/api/v1/sessions/stats` | GET | 통계 조회 | None | ServiceStatistics |

### **3. Health Routes (health.py)**

#### 시스템 상태 엔드포인트

##### GET /api/v1/health
- **기본 헬스체크**
- 출력: `{"status": "healthy", "timestamp": "..."}`

##### GET /api/v1/health/detailed
- **상세 시스템 상태**
- 출력:
  ```json
  {
    "status": "healthy",
    "components": {
      "api": "healthy",
      "supervisor": "healthy",
      "database": "healthy",
      "cache": "healthy"
    },
    "metrics": {...}
  }
  ```

##### GET /api/v1/health/ready
- **준비 상태 확인** (Kubernetes readiness probe)

##### GET /api/v1/health/live
- **활성 상태 확인** (Kubernetes liveness probe)

---

## Services 계층

### **1. Cache Manager (cache_manager.py)**

#### SQLiteMemoryCache 클래스

##### 주요 메소드
| 메소드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `get(key)` | str | Optional[Any] | 캐시 값 조회 |
| `set(key, value, ttl)` | str, Any, int | bool | 값 저장 |
| `delete(key)` | str | bool | 캐시 삭제 |
| `invalidate(pattern)` | str | int | 패턴 기반 삭제 |
| `cleanup()` | None | None | 만료된 항목 정리 |
| `get_stats()` | None | Dict | 통계 정보 |

##### 캐시 전략
- **TTL**: 기본 3600초 (1시간)
- **최대 크기**: 1000개 항목
- **제거 정책**: LRU (Least Recently Used)
- **자동 정리**: 5분마다 만료 항목 제거

### **2. Database Client (database_client.py)**

#### DatabaseAPIClient 클래스

##### 핵심 메소드

```python
async def execute_sql(query: str, database: str) -> Dict
```
- **용도**: SQL 쿼리 실행
- **재시도**: 3회, 지수 백오프
- **타임아웃**: 30초

```python
async def search_hr(query: str, filters: Dict, limit: int) -> List
```
- **용도**: HR 정보 검색
- **필터링**: 부서, 직급, 입사일 등

```python
async def search_regulations(query: str, rule_type: str, keywords: List) -> List
```
- **용도**: 규정 검색
- **분류**: HR, 안전, 품질 등

### **3. Supervisor Service (supervisor_service.py)**

#### SupervisorService 클래스

##### 주요 처리 흐름

```python
async def process_chat(query: str, user_context: Dict, use_cache: bool) -> Dict
```

1. **캐시 확인**
   - 캐시 키 생성 (query + context hash)
   - 캐시된 결과 확인 및 반환

2. **Supervisor 실행**
   - MedicalSupervisorV2 인스턴스 획득
   - execute_with_context() 호출
   - 결과 처리 및 포맷팅

3. **캐시 저장**
   - 성공 결과를 캐시에 저장
   - TTL 설정

4. **세션 관리**
   - 세션 정보 업데이트
   - 대화 이력 저장

##### 통계 추적
| 메트릭 | 설명 |
|--------|------|
| total_requests | 총 요청 수 |
| successful_requests | 성공 요청 수 |
| failed_requests | 실패 요청 수 |
| average_response_time | 평균 응답 시간 |
| cache_hit_rate | 캐시 적중률 |

### **4. Multi-level Cache (multi_level_cache.py)**

#### 3계층 캐시 구조

##### L1: Memory Cache (LRUCache)
- **크기**: 100개 항목
- **TTL**: 300초
- **특징**: 가장 빠른 접근, 휘발성

##### L2: SQLite Cache
- **크기**: 10,000개 항목
- **TTL**: 3600초
- **특징**: 영속성, 중간 속도

##### L3: Redis Cache (계획)
- **크기**: 무제한
- **TTL**: 86400초
- **특징**: 분산 캐시, 확장성

#### 캐시 동작 패턴

```python
async def get(key: str, fetch_func: Callable, ttl: int) -> Any
```

1. L1 캐시 확인 → 히트 시 즉시 반환
2. L2 캐시 확인 → 히트 시 L1 승격 후 반환
3. L3 캐시 확인 → 히트 시 L1, L2 승격 후 반환
4. 모든 미스 → fetch_func 실행 → 모든 레벨 저장

### **5. Enhanced Streaming (enhanced_streaming.py)**

#### 스트리밍 이벤트 타입

| 이벤트 | 설명 | 데이터 |
|--------|------|--------|
| STARTED | 처리 시작 | session_id, query |
| PROGRESS | 진행 상황 | step, percentage |
| AGENT_START | 에이전트 시작 | agent_name |
| AGENT_END | 에이전트 완료 | agent_name, result |
| TOKEN | 토큰 스트리밍 | token |
| RESULT | 최종 결과 | full_response |
| ERROR | 에러 발생 | error_message |
| COMPLETED | 처리 완료 | total_time |

#### SSE 포맷

```
event: progress
data: {"type": "progress", "step": 2, "total": 5, "percentage": 40}

event: token
data: {"type": "token", "content": "분석"}

event: heartbeat
data: {"type": "heartbeat", "timestamp": "..."}
```

---

## 미들웨어 구조

### 실행 순서 및 역할

```
클라이언트 요청
    ↓
CORS Middleware
- Origin 검증
- 허용된 메소드/헤더 확인
    ↓
ErrorHandling Middleware
- 예외 캐칭
- 에러 응답 포맷팅
    ↓
RateLimit Middleware
- IP별 호출 횟수 체크
- 제한 초과 시 429 반환
    ↓
RequestLogging Middleware
- Request ID 생성
- 요청/응답 로깅
    ↓
애플리케이션 처리
    ↓
응답 반환 (역순으로 미들웨어 통과)
```

---

## 의존성 주입 패턴

### FastAPI 의존성 시스템

#### 1. 서비스 의존성
```python
@lru_cache()
def get_supervisor_service() -> SupervisorService:
    """싱글톤 패턴으로 Supervisor 서비스 관리"""
    return SupervisorService()
```

#### 2. 라우트 의존성 주입
```python
@router.post("/chat")
async def chat(
    request: ChatRequest,
    supervisor: SupervisorService = Depends(get_supervisor_service),
    cache: SQLiteMemoryCache = Depends(get_cache_manager)
):
    # 의존성이 자동 주입됨
```

#### 3. 의존성 체인
```
get_supervisor_service()
    → get_cache_manager()
        → get_database_client()
            → settings (환경 설정)
```

### 장점
- **테스트 용이성**: Mock 객체 주입 가능
- **코드 재사용**: 공통 의존성 공유
- **생명주기 관리**: 자동 초기화/정리
- **타입 안정성**: 타입 힌트 지원

---

## API 보안 및 인증

### 구현된 보안 기능

| 기능 | 구현 | 설정 |
|------|------|------|
| API Key 인증 | 환경 변수 | `API_KEY` |
| Rate Limiting | 미들웨어 | 100 req/min |
| CORS | FastAPI 미들웨어 | 설정 가능 |
| Request ID | UUID 추적 | 자동 생성 |
| Error Masking | 에러 핸들러 | 상세 정보 숨김 |

---

## 성능 최적화

### 구현된 최적화

#### 1. 비동기 처리
- 모든 I/O 작업 비동기화
- AsyncIO 기반 동시성
- 논블로킹 데이터베이스 접근

#### 2. 캐싱 전략
- Multi-level 캐싱
- 캐시 키 최적화
- TTL 기반 자동 만료

#### 3. 연결 관리
- HTTP 연결 풀링 (httpx)
- 데이터베이스 연결 재사용
- 타임아웃 설정

#### 4. 리소스 관리
- 메모리 제한 설정
- 자동 가비지 컬렉션
- 리소스 정리 (shutdown)

---

## 모니터링 및 로깅

### 로깅 구조

```python
logging.basicConfig(
    level=settings.LOG_LEVEL,     # INFO/DEBUG/ERROR
    format=settings.LOG_FORMAT    # 타임스탬프, 레벨, 메시지
)
```

### 메트릭 수집

| 메트릭 | 수집 위치 | 용도 |
|--------|----------|------|
| Request Count | Middleware | 트래픽 분석 |
| Response Time | Middleware | 성능 모니터링 |
| Cache Hit Rate | CacheManager | 캐시 효율성 |
| Error Rate | ErrorHandler | 안정성 모니터링 |
| Agent Performance | Supervisor | 에이전트 최적화 |

---

## 결론

Backend API는 FastAPI를 기반으로 한 현대적이고 확장 가능한 아키텍처를 구현하고 있습니다. 비동기 처리, 다층 캐싱, 포괄적인 미들웨어, 그리고 체계적인 의존성 관리를 통해 높은 성능과 유지보수성을 제공합니다. 특히 의료/제약 도메인에 특화된 기능들과 실시간 스트리밍 지원으로 복잡한 대화형 AI 시스템의 요구사항을 효과적으로 충족시키고 있습니다.