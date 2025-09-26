# FastAPI Chat & Database API 개선 가이드

## 📌 Executive Summary
본 문서는 FastAPI 기반 Chat API (Port 8001)와 Database API (Port 8002) 아키텍처의 기능적 개선사항을 정리한 가이드입니다.

---

## 1. 🔴 즉시 수정 필요 사항

### 1.1 동기/비동기 실행 문제
**현재 문제점**
- `sql_analysis_agent.py`에서 `asyncio.run()`을 lambda 내부에서 호출
- 이벤트 루프 충돌 가능성

**수정 코드**
```python
# backend/service/worker_agents/sql_analysis_agent.py
# Line 약 50-60

# 기존 코드
return Tool(
    name="sql_query",
    func=lambda q: asyncio.run(execute_sql(q))
)

# 개선 코드
from langchain_core.tools import StructuredTool

return StructuredTool.from_function(
    func=execute_sql,
    coroutine=execute_sql,  # 비동기 함수 직접 지정
    name="sql_query",
    description="SQL 쿼리 실행"
)
```

### 1.2 데이터베이스 연결 관리
**현재 문제점**
- 매 요청마다 새로운 SQLite 연결 생성
- 연결 풀 없음

**수정 위치 및 코드**
```python
# backend/service/supervisor/main_supervisor_v2.py
# 새로운 클래스 추가

class CheckpointerPool:
    _instance = None
    _pool = []
    _max_connections = 5
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_connection(self, db_path: str):
        if self._pool:
            return self._pool.pop()
        return await AsyncSqliteSaver.from_conn_string(db_path)
    
    async def release_connection(self, conn):
        if len(self._pool) < self._max_connections:
            self._pool.append(conn)
        else:
            await conn.close()
```

### 1.3 한글 컬럼명 처리 통합
**수정 위치**
```python
# backend/api/services/database_client.py
# backend/service/worker_agents/database_api_client.py
# 중복 코드 제거 필요

# 공통 유틸리티로 분리
# backend/common/korean_sql_utils.py (새 파일)

class KoreanSQLProcessor:
    KOREAN_COLUMNS = {
        "사번", "성명", "본부", "직급", "부서", "지점", 
        "연락처", "월평균사용예산", "최근 평가", "기본급(₩)", 
        "성과급(₩)", "책임업무", "담당자", "거래처ID"
    }
    
    @classmethod
    def auto_quote_sql(cls, sql: str) -> str:
        import re
        processed = sql
        for column in cls.KOREAN_COLUMNS:
            if f'"{column}"' not in processed:
                pattern = rf'\b{re.escape(column)}\b'
                processed = re.sub(pattern, f'"{column}"', processed)
        return processed
```

---

## 2. 🟡 성능 최적화 개선사항

### 2.1 캐싱 전략 개선
**현재 상태**: SQLite 메모리 캐싱만 사용

**개선 방안**
```python
# backend/api/services/cache_manager.py 수정

class MultiLevelCache:
    """다단계 캐싱 구현"""
    
    def __init__(self):
        self.l1_cache = {}  # 메모리 (매우 빠름, 작은 용량)
        self.l2_cache = SQLiteMemoryCache()  # SQLite (빠름, 중간 용량)
        # L3는 추후 Redis 추가 가능
        
    async def get(self, key: str):
        # L1 체크
        if key in self.l1_cache:
            return self.l1_cache[key]
        
        # L2 체크
        value = await self.l2_cache.get(key)
        if value:
            # L1 캐시 업데이트 (LRU 적용)
            if len(self.l1_cache) > 100:
                self.l1_cache.pop(next(iter(self.l1_cache)))
            self.l1_cache[key] = value
            
        return value
```

### 2.2 스트리밍 응답 개선
**수정 위치**: `backend/api/services/supervisor_service.py`

```python
async def enhanced_stream_response(self, query: str, user_context: Dict):
    """향상된 스트리밍 응답 with 진행률"""
    
    session_id = user_context.get("session_id", "default")
    total_steps = 5  # 예상 단계
    current_step = 0
    
    try:
        supervisor = await self._get_or_create_supervisor()
        
        async for chunk in supervisor.stream_execution(query, user_context):
            # 진행률 계산
            if chunk["type"] == "stream":
                current_step += 1
                progress = (current_step / total_steps) * 100
                
                data = {
                    "type": "content",
                    "data": chunk["data"],
                    "progress": progress,
                    "step": f"{current_step}/{total_steps}",
                    "timestamp": chunk["timestamp"]
                }
                yield f"data: {json.dumps(data)}\n\n"
```

---

## 3. 🟢 아키텍처 개선사항

### 3.1 에러 핸들링 표준화
**새 파일**: `backend/common/exceptions.py`

```python
from enum import Enum

class ErrorCode(str, Enum):
    DATABASE_ERROR = "DB_001"
    AGENT_ERROR = "AG_001"
    VALIDATION_ERROR = "VAL_001"
    CACHE_ERROR = "CACHE_001"
    TIMEOUT_ERROR = "TIMEOUT_001"

class APIException(Exception):
    def __init__(self, 
                 status_code: int, 
                 error_code: ErrorCode,
                 detail: str,
                 context: Dict = None):
        self.status_code = status_code
        self.error_code = error_code
        self.detail = detail
        self.context = context or {}
```

### 3.2 API 응답 표준화
**새 파일**: `backend/api/models/base.py`

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional
from datetime import datetime

T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    """표준 API 응답 형식"""
    status: str  # success, error, partial
    data: Optional[T] = None
    error: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    request_id: Optional[str] = None
```

### 3.3 의존성 주입 개선
**수정 위치**: `backend/api/core/dependencies.py`

```python
from functools import lru_cache
from typing import Annotated
from fastapi import Depends

class ServiceContainer:
    """서비스 컨테이너 (의존성 관리)"""
    
    _instances = {}
    
    @classmethod
    def get_instance(cls, service_class, *args, **kwargs):
        key = service_class.__name__
        if key not in cls._instances:
            cls._instances[key] = service_class(*args, **kwargs)
        return cls._instances[key]

# FastAPI 의존성으로 사용
@lru_cache()
def get_supervisor_service() -> SupervisorService:
    return ServiceContainer.get_instance(
        SupervisorService,
        llm_provider=settings.LLM_PROVIDER,
        model_name=settings.LLM_MODEL
    )

# 타입 힌트 개선
SupervisorDep = Annotated[SupervisorService, Depends(get_supervisor_service)]
```

---

## 4. 🔵 기능 고도화 방안

### 4.1 동적 에이전트 로딩
**새 파일**: `backend/service/supervisor/agent_loader.py`

```python
import importlib
import inspect
from typing import Dict, Type

class DynamicAgentLoader:
    """필요시에만 에이전트를 동적으로 로드"""
    
    def __init__(self):
        self.agent_registry = {}
        self.agent_modules = {
            "sql": "backend.service.worker_agents.sql_analysis_agent",
            "doc": "backend.service.worker_agents.document_generation_agent",
            "info": "backend.service.worker_agents.information_retrieval_agent",
            "compliance": "backend.service.worker_agents.compliance_validation_agent"
        }
    
    async def get_agent(self, agent_type: str):
        if agent_type not in self.agent_registry:
            module_path = self.agent_modules.get(agent_type)
            if module_path:
                module = importlib.import_module(module_path)
                # 에이전트 클래스 찾기
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and "Agent" in name:
                        self.agent_registry[agent_type] = obj()
                        break
        
        return self.agent_registry.get(agent_type)
```

### 4.2 에이전트 성능 모니터링
**수정 위치**: `backend/service/supervisor/execution_manager.py`

```python
class AgentPerformanceMonitor:
    """에이전트 성능 추적 및 분석"""
    
    def __init__(self):
        self.metrics = defaultdict(lambda: {
            "total_executions": 0,
            "successful_executions": 0,
            "total_time": 0.0,
            "errors": []
        })
    
    async def record_execution(self, agent_name: str, execution_time: float, 
                              success: bool, error: str = None):
        metrics = self.metrics[agent_name]
        metrics["total_executions"] += 1
        metrics["total_time"] += execution_time
        
        if success:
            metrics["successful_executions"] += 1
        else:
            metrics["errors"].append({
                "timestamp": datetime.now().isoformat(),
                "error": error
            })
    
    def get_agent_stats(self, agent_name: str) -> Dict:
        metrics = self.metrics[agent_name]
        
        if metrics["total_executions"] == 0:
            return {"status": "no_data"}
        
        return {
            "success_rate": metrics["successful_executions"] / metrics["total_executions"],
            "average_time": metrics["total_time"] / metrics["total_executions"],
            "total_executions": metrics["total_executions"],
            "recent_errors": metrics["errors"][-5:]  # 최근 5개 에러
        }
```

### 4.3 컨텍스트 압축 및 최적화
**수정 위치**: `backend/service/supervisor/context_manager.py`

```python
class ContextCompressor:
    """컨텍스트 크기 최적화"""
    
    @staticmethod
    async def compress_context(context: Dict, max_tokens: int = 4000) -> Dict:
        """토큰 제한에 맞게 컨텍스트 압축"""
        
        # 1. 중복 제거
        context = ContextCompressor._remove_duplicates(context)
        
        # 2. 오래된 정보 제거
        if "history" in context:
            context["history"] = context["history"][-5:]  # 최근 5개만
        
        # 3. 긴 텍스트 요약
        for key, value in context.items():
            if isinstance(value, str) and len(value) > 500:
                context[key] = await ContextCompressor._summarize_text(value)
        
        return context
    
    @staticmethod
    def _remove_duplicates(context: Dict) -> Dict:
        """중복 정보 제거"""
        seen = set()
        cleaned = {}
        
        for key, value in context.items():
            value_str = str(value)
            if value_str not in seen:
                seen.add(value_str)
                cleaned[key] = value
        
        return cleaned
```

---

## 5. 📊 모니터링 및 관찰성

### 5.1 메트릭 수집
**새 파일**: `backend/api/monitoring/metrics.py`

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# 메트릭 정의
request_count = Counter('api_requests_total', 'Total API requests', 
                       ['method', 'endpoint', 'status'])
request_duration = Histogram('api_request_duration_seconds', 
                            'API request duration')
active_sessions = Gauge('active_sessions', 'Number of active sessions')
cache_hit_rate = Gauge('cache_hit_rate', 'Cache hit rate percentage')

class MetricsCollector:
    @staticmethod
    def record_request(method: str, endpoint: str, status: int, duration: float):
        request_count.labels(method=method, endpoint=endpoint, status=status).inc()
        request_duration.observe(duration)
    
    @staticmethod
    def update_sessions(count: int):
        active_sessions.set(count)
    
    @staticmethod
    def update_cache_stats(hits: int, misses: int):
        if hits + misses > 0:
            hit_rate = (hits / (hits + misses)) * 100
            cache_hit_rate.set(hit_rate)
```

### 5.2 로깅 개선
**수정 위치**: 모든 에이전트 파일

```python
import structlog

# 구조화된 로깅 설정
logger = structlog.get_logger()

# 사용 예시
logger.info("agent_execution_started",
           agent_name="sql_analysis",
           query_type="complex",
           session_id=session_id,
           user_id=user_id)
```

---

## 6. 🚀 배포 준비사항

### 6.1 환경 설정 분리
```yaml
# config/development.yaml
database:
  api_url: "http://localhost:8002"
  timeout: 30

cache:
  enabled: true
  ttl: 300

# config/production.yaml  
database:
  api_url: "https://api.production.com"
  timeout: 10
  
cache:
  enabled: true
  ttl: 3600
```

### 6.2 Health Check 개선
```python
# backend/api/routes/health.py 수정

@router.get("/deep-health")
async def deep_health_check():
    """심층 헬스 체크"""
    checks = {
        "database": await check_database_connection(),
        "cache": await check_cache_health(),
        "agents": await check_all_agents_health(),
        "memory": check_memory_usage(),
        "disk": check_disk_space()
    }
    
    overall_health = all(checks.values())
    
    return {
        "healthy": overall_health,
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }
```

---

## 7. 📝 구현 우선순위

### Phase 1 (즉시 적용 - 1주)
1. 동기/비동기 실행 문제 수정
2. 한글 컬럼명 처리 통합
3. 에러 핸들링 표준화
4. API 응답 표준화

### Phase 2 (성능 개선 - 2주)
1. 데이터베이스 연결 풀 구현
2. 다단계 캐싱 구현
3. 스트리밍 응답 개선
4. 컨텍스트 압축 구현

### Phase 3 (고도화 - 3주)
1. 동적 에이전트 로딩
2. 성능 모니터링 구현
3. 메트릭 수집 시스템
4. 구조화된 로깅

### Phase 4 (안정화 - 2주)
1. 통합 테스트 작성
2. 부하 테스트
3. 문서화
4. 배포 자동화

---

## 8. 🔍 테스트 전략

### 8.1 단위 테스트
```python
# tests/test_agents.py
import pytest
from backend.service.worker_agents.sql_analysis_agent import SQLAnalysisAgent

@pytest.mark.asyncio
async def test_sql_generation():
    agent = SQLAnalysisAgent()
    request = SQLQueryRequest(
        natural_language_query="지난달 매출 조회",
        target_tables=["sales_performance"]
    )
    
    result = await agent.analyze_query(request)
    
    assert result.execution_status == "success"
    assert result.generated_sql is not None
    assert "SELECT" in result.generated_sql.upper()
```

### 8.2 통합 테스트
```python
# tests/test_integration.py
@pytest.mark.asyncio
async def test_end_to_end_flow():
    """전체 플로우 테스트"""
    
    # 1. Chat API 호출
    response = await client.post("/api/v1/chat", json={
        "query": "김철수 사원의 실적 분석",
        "user_id": "test_user",
        "session_id": "test_session"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # 2. 결과 검증
    assert data["status"] == "success"
    assert "result" in data
    assert len(data["result"]["agents_used"]) > 0
```

---

## 9. 📚 추가 개선 아이디어

### 9.1 에이전트 자가 학습
- 각 에이전트의 성공/실패 패턴 학습
- 최적 실행 전략 자동 조정
- Fine-tuning 데이터 수집

### 9.2 워크플로우 버전 관리
- Blue-Green 배포 지원
- A/B 테스팅 프레임워크
- 점진적 롤아웃

### 9.3 보안 강화 (Phase 5)
- JWT 토큰 기반 인증
- Rate Limiting 세분화
- SQL Injection 방지 강화
- 입력 검증 레이어

---

## 10. 📞 문의 및 지원

이 문서에 대한 질문이나 추가 지원이 필요한 경우:
- 각 Phase별 상세 구현 가이드 제공 가능
- 코드 리뷰 및 페어 프로그래밍 지원
- 성능 벤치마크 및 최적화 컨설팅

---

*문서 버전: 1.0*  
*작성일: 2024*  
*대상 시스템: FastAPI Chat & Database API Architecture*