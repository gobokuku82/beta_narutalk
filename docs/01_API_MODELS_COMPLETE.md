# API Models 완전 상세 문서

## 파일: `backend/api/models/base.py`

### 파일 목적
LangGraph 0.6.x를 위한 표준화된 API 응답 모델 정의. 모든 API 엔드포인트에서 일관된 응답 형식을 보장하고, 타입 안정성과 메타데이터 포함을 제공합니다.

### Imports 및 Dependencies
```python
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
import uuid
```

### Type Variables
```python
T = TypeVar('T')  # 제네릭 타입 변수 - 응답 데이터의 타입 유연성 제공
```

---

## Enum 정의

### ResponseStatus(str, Enum)
```python
class ResponseStatus(str, Enum):
    SUCCESS = "success"      # 요청 성공
    ERROR = "error"          # 요청 실패
    PARTIAL = "partial"      # 부분 성공
    QUEUED = "queued"        # 큐에 대기 중
    PENDING = "pending"      # 현재 처리 중
```

**용도**: API 응답의 상태를 표준화하여 클라이언트가 응답을 일관되게 처리할 수 있도록 함

---

## 클래스 정의

### 1. StandardResponse(BaseModel, Generic[T])

**목적**: 모든 API 응답의 기본 형식을 정의하는 제네릭 클래스

**상속**:
- `BaseModel` - Pydantic 기본 모델
- `Generic[T]` - 제네릭 타입 지원

**속성 상세**:

| 속성 | 타입 | 설명 | 기본값 |
|------|------|------|--------|
| `status` | `ResponseStatus` | 응답 상태 | 필수 |
| `data` | `Optional[T]` | 응답 데이터 | `None` |
| `error` | `Optional[Dict[str, Any]]` | 에러 정보 | `None` |
| `metadata` | `Dict[str, Any]` | 추가 메타데이터 | `Field(default_factory=dict)` |
| `timestamp` | `str` | 응답 생성 시간 | `Field(default_factory=lambda: datetime.now().isoformat())` |
| `request_id` | `str` | 요청 고유 ID | `Field(default_factory=lambda: str(uuid.uuid4()))` |
| `execution_time` | `Optional[float]` | 실행 시간(초) | `None` |

**Config 클래스**:
```python
class Config:
    json_encoders = {
        datetime: lambda v: v.isoformat()  # datetime 객체를 ISO 형식 문자열로 변환
    }
    schema_extra = {
        "example": {
            "status": "success",
            "data": {"result": "example"},
            "metadata": {"version": "1.0"},
            "timestamp": "2024-01-01T00:00:00",
            "request_id": "123e4567-e89b-12d3-a456-426614174000",
            "execution_time": 1.23
        }
    }
```

---

### 2. PaginatedResponse(StandardResponse[List[T]], Generic[T])

**목적**: 대량 데이터를 페이지 단위로 전송하기 위한 응답 모델

**상속**:
- `StandardResponse[List[T]]` - 리스트 데이터를 가진 표준 응답
- `Generic[T]` - 제네릭 타입 지원

**추가 속성**:

| 속성 | 타입 | 설명 | 기본값 |
|------|------|------|--------|
| `page` | `int` | 현재 페이지 번호 | `1` |
| `page_size` | `int` | 페이지 크기 | `20` |
| `total_items` | `int` | 전체 아이템 수 | `0` |
| `total_pages` | `int` | 전체 페이지 수 | `0` |
| `has_next` | `bool` | 다음 페이지 존재 여부 | `False` |
| `has_prev` | `bool` | 이전 페이지 존재 여부 | `False` |

**메서드**:

#### `__init__(self, **data)`
```python
def __init__(self, **data):
    super().__init__(**data)
    # 자동으로 페이지 정보 계산
    if self.total_items > 0 and self.page_size > 0:
        self.total_pages = (self.total_items + self.page_size - 1) // self.page_size
        self.has_next = self.page < self.total_pages
        self.has_prev = self.page > 1
```
- **기능**: 페이지네이션 메타데이터 자동 계산
- **계산 내용**: total_pages, has_next, has_prev

---

### 3. StreamResponse(BaseModel)

**목적**: Server-Sent Events (SSE)를 위한 스트리밍 응답 모델

**속성 상세**:

| 속성 | 타입 | 설명 | 기본값 |
|------|------|------|--------|
| `event` | `str` | 이벤트 타입 | 필수 |
| `data` | `Any` | 이벤트 데이터 | 필수 |
| `id` | `Optional[str]` | 이벤트 ID | `None` |
| `retry` | `Optional[int]` | 재연결 시간(ms) | `None` |
| `progress` | `Optional[float]` | 진행률 (0-100) | `None` |
| `step` | `Optional[str]` | 현재 단계 설명 | `None` |

**메서드**:

#### `to_sse(self) -> str`
```python
def to_sse(self) -> str:
    """SSE 형식으로 변환"""
    lines = []
    if self.id:
        lines.append(f"id: {self.id}")
    if self.event:
        lines.append(f"event: {self.event}")
    if self.retry:
        lines.append(f"retry: {self.retry}")

    # data는 JSON으로 직렬화
    import json
    data_dict = {
        "data": self.data,
        "progress": self.progress,
        "step": self.step
    }
    lines.append(f"data: {json.dumps(data_dict)}")

    return "\n".join(lines) + "\n\n"
```
- **반환**: SSE 형식의 문자열
- **용도**: 실시간 스트리밍 응답 전송

---

### 4. AgentResponse(StandardResponse[Dict[str, Any]])

**목적**: LangGraph 워크플로우 에이전트 실행 결과 응답

**상속**: `StandardResponse[Dict[str, Any]]`

**추가 속성**:

| 속성 | 타입 | 설명 | 기본값 |
|------|------|------|--------|
| `agents_used` | `List[str]` | 사용된 에이전트 목록 | `Field(default_factory=list)` |
| `workflow_id` | `Optional[str]` | 워크플로우 ID | `None` |
| `thread_id` | `Optional[str]` | 스레드 ID | `None` |
| `checkpoint_id` | `Optional[str]` | 체크포인트 ID | `None` |
| `execution_phases` | `List[Dict[str, Any]]` | 실행 단계별 정보 | `Field(default_factory=list)` |
| `performance_metrics` | `Dict[str, float]` | 성능 메트릭 | `Field(default_factory=dict)` |

**execution_phases 구조**:
```python
{
    "phase": "intent_analysis",
    "start_time": "2024-01-01T00:00:00",
    "end_time": "2024-01-01T00:00:01",
    "status": "completed",
    "result": {...}
}
```

**performance_metrics 예시**:
```python
{
    "total_time": 5.23,
    "llm_time": 3.45,
    "db_time": 1.78,
    "tokens_used": 1500
}
```

---

### 5. DatabaseQueryResponse(StandardResponse[List[Dict[str, Any]]])

**목적**: 데이터베이스 쿼리 실행 결과 응답

**상속**: `StandardResponse[List[Dict[str, Any]]]`

**추가 속성**:

| 속성 | 타입 | 설명 | 기본값 |
|------|------|------|--------|
| `query` | `Optional[str]` | 실행된 SQL 쿼리 | `None` |
| `database` | `Optional[str]` | 대상 데이터베이스 | `None` |
| `rows_affected` | `int` | 영향받은 행 수 | `0` |
| `column_names` | `List[str]` | 컬럼명 목록 | `Field(default_factory=list)` |
| `statistics` | `Dict[str, Any]` | 쿼리 통계 | `Field(default_factory=dict)` |

**statistics 구조**:
```python
{
    "execution_time": 0.023,
    "rows_scanned": 1000,
    "index_used": True,
    "cache_hit": False
}
```

---

### 6. ValidationErrorResponse(StandardResponse[None])

**목적**: 입력 검증 실패 시 상세 에러 정보 제공

**상속**: `StandardResponse[None]`

**추가 속성**:

| 속성 | 타입 | 설명 | 기본값 |
|------|------|------|--------|
| `validation_errors` | `List[Dict[str, Any]]` | 검증 에러 목록 | `Field(default_factory=list)` |

**메서드**:

#### `add_field_error(self, field: str, message: str, value: Any = None, code: Optional[str] = None)`
```python
def add_field_error(self, field: str, message: str, value: Any = None, code: Optional[str] = None):
    """필드별 검증 에러 추가"""
    error = {
        "field": field,
        "message": message,
        "code": code or "validation_error"
    }

    # 값이 있으면 추가 (100자로 제한)
    if value is not None:
        error["value"] = str(value)[:100] if len(str(value)) > 100 else value

    self.validation_errors.append(error)

    # 자동으로 status를 ERROR로 설정
    self.status = ResponseStatus.ERROR
```

**validation_errors 구조**:
```python
{
    "field": "email",
    "message": "Invalid email format",
    "value": "not-an-email",
    "code": "invalid_format"
}
```

---

### 7. HealthCheckResponse(StandardResponse[Dict[str, Any]])

**목적**: 서비스 상태 및 의존성 체크 응답

**상속**: `StandardResponse[Dict[str, Any]]`

**추가 속성**:

| 속성 | 타입 | 설명 | 기본값 |
|------|------|------|--------|
| `healthy` | `bool` | 전체 상태 | 필수 |
| `version` | `str` | 서비스 버전 | 필수 |
| `uptime` | `float` | 가동 시간(초) | 필수 |
| `components` | `Dict[str, Dict[str, Any]]` | 컴포넌트별 상태 | `Field(default_factory=dict)` |

**메서드**:

#### `add_component_status(self, name: str, healthy: bool, latency: Optional[float] = None, details: Optional[Dict] = None)`
```python
def add_component_status(self, name: str, healthy: bool, latency: Optional[float] = None, details: Optional[Dict] = None):
    """컴포넌트 상태 추가"""
    component = {
        "healthy": healthy,
        "checked_at": datetime.now().isoformat()
    }

    if latency is not None:
        component["latency_ms"] = latency

    if details:
        component["details"] = details

    self.components[name] = component

    # 하나라도 unhealthy면 전체도 unhealthy
    if not healthy:
        self.healthy = False
```

**components 구조**:
```python
{
    "database": {
        "healthy": true,
        "checked_at": "2024-01-01T00:00:00",
        "latency_ms": 5.2,
        "details": {
            "connections": 10,
            "max_connections": 100
        }
    },
    "llm_service": {
        "healthy": true,
        "checked_at": "2024-01-01T00:00:00",
        "latency_ms": 250.5,
        "details": {
            "model": "gpt-4o",
            "rate_limit_remaining": 9500
        }
    }
}
```

---

## 유틸리티 클래스

### ResponseBuilder

**목적**: 일관된 응답 생성을 위한 헬퍼 클래스

**Static Methods**:

#### 1. `success(data: Any, metadata: Optional[Dict] = None, execution_time: Optional[float] = None) -> StandardResponse`
```python
@staticmethod
def success(data: Any, metadata: Optional[Dict] = None, execution_time: Optional[float] = None) -> StandardResponse:
    """성공 응답 생성"""
    return StandardResponse(
        status=ResponseStatus.SUCCESS,
        data=data,
        metadata=metadata or {},
        execution_time=execution_time
    )
```

#### 2. `error(error_code: str, message: str, detail: Optional[str] = None, status_code: int = 500) -> StandardResponse`
```python
@staticmethod
def error(error_code: str, message: str, detail: Optional[str] = None, status_code: int = 500) -> StandardResponse:
    """에러 응답 생성"""
    error_info = {
        "code": error_code,
        "message": message,
        "status_code": status_code
    }
    if detail:
        error_info["detail"] = detail

    return StandardResponse(
        status=ResponseStatus.ERROR,
        error=error_info
    )
```

#### 3. `partial(data: Any, completed: int, total: int, errors: Optional[List] = None) -> StandardResponse`
```python
@staticmethod
def partial(data: Any, completed: int, total: int, errors: Optional[List] = None) -> StandardResponse:
    """부분 성공 응답 생성"""
    metadata = {
        "completed": completed,
        "total": total,
        "success_rate": completed / total if total > 0 else 0
    }

    response = StandardResponse(
        status=ResponseStatus.PARTIAL,
        data=data,
        metadata=metadata
    )

    if errors:
        response.error = {"partial_errors": errors}

    return response
```

#### 4. `paginated(data: List[Any], page: int, page_size: int, total_items: int) -> PaginatedResponse`
```python
@staticmethod
def paginated(data: List[Any], page: int, page_size: int, total_items: int) -> PaginatedResponse:
    """페이지네이션 응답 생성"""
    return PaginatedResponse(
        status=ResponseStatus.SUCCESS,
        data=data,
        page=page,
        page_size=page_size,
        total_items=total_items
    )
```

#### 5. `stream(event: str, data: Any, progress: Optional[float] = None, step: Optional[str] = None) -> StreamResponse`
```python
@staticmethod
def stream(event: str, data: Any, progress: Optional[float] = None, step: Optional[str] = None) -> StreamResponse:
    """스트리밍 응답 생성"""
    return StreamResponse(
        event=event,
        data=data,
        progress=progress,
        step=step
    )
```

---

## 편의 함수 (Convenience Functions)

### 1. `create_success_response(data: Any, **kwargs) -> StandardResponse`
```python
def create_success_response(data: Any, **kwargs) -> StandardResponse:
    """성공 응답 빠른 생성"""
    return ResponseBuilder.success(data, **kwargs)
```

### 2. `create_error_response(error_code: str, message: str, **kwargs) -> StandardResponse`
```python
def create_error_response(error_code: str, message: str, **kwargs) -> StandardResponse:
    """에러 응답 빠른 생성"""
    return ResponseBuilder.error(error_code, message, **kwargs)
```

### 3. `create_paginated_response(data: List[Any], page: int, page_size: int, total_items: int) -> PaginatedResponse`
```python
def create_paginated_response(data: List[Any], page: int, page_size: int, total_items: int) -> PaginatedResponse:
    """페이지네이션 응답 빠른 생성"""
    return ResponseBuilder.paginated(data, page, page_size, total_items)
```

### 4. `create_stream_response(event: str, data: Any, **kwargs) -> StreamResponse`
```python
def create_stream_response(event: str, data: Any, **kwargs) -> StreamResponse:
    """스트리밍 응답 빠른 생성"""
    return ResponseBuilder.stream(event, data, **kwargs)
```

---

## 사용 예시

### 1. 기본 성공 응답
```python
response = create_success_response(
    data={"user_id": 123, "name": "홍길동"},
    metadata={"api_version": "1.0"},
    execution_time=0.025
)
```

### 2. 페이지네이션 응답
```python
users = [{"id": i, "name": f"User {i}"} for i in range(1, 11)]
response = create_paginated_response(
    data=users,
    page=1,
    page_size=10,
    total_items=100
)
```

### 3. 에러 응답
```python
response = create_error_response(
    error_code="INVALID_INPUT",
    message="Invalid email format",
    detail="Email must contain @ symbol",
    status_code=400
)
```

### 4. 스트리밍 응답
```python
response = create_stream_response(
    event="progress",
    data={"message": "Processing..."},
    progress=45.5,
    step="Analyzing data"
)
sse_string = response.to_sse()
```

### 5. 검증 에러 응답
```python
response = ValidationErrorResponse(
    status=ResponseStatus.ERROR
)
response.add_field_error(
    field="email",
    message="Invalid email format",
    value="not-an-email",
    code="INVALID_FORMAT"
)
response.add_field_error(
    field="age",
    message="Age must be positive",
    value=-5,
    code="INVALID_VALUE"
)
```

### 6. 헬스체크 응답
```python
response = HealthCheckResponse(
    status=ResponseStatus.SUCCESS,
    healthy=True,
    version="1.0.0",
    uptime=3600.0
)

response.add_component_status(
    name="database",
    healthy=True,
    latency=5.2,
    details={"connections": 10}
)

response.add_component_status(
    name="llm_service",
    healthy=True,
    latency=250.5,
    details={"model": "gpt-4o"}
)
```

### 7. 에이전트 응답
```python
response = AgentResponse(
    status=ResponseStatus.SUCCESS,
    data={"result": "Analysis complete"},
    agents_used=["sales_analytics", "compliance_check"],
    workflow_id="wf_123",
    thread_id="thread_456",
    execution_phases=[
        {
            "phase": "intent_analysis",
            "status": "completed",
            "duration": 0.5
        },
        {
            "phase": "agent_execution",
            "status": "completed",
            "duration": 2.3
        }
    ],
    performance_metrics={
        "total_time": 2.8,
        "tokens_used": 1500
    }
)
```

---

## 타입 안정성 및 검증

### Pydantic 자동 검증
- 모든 필드는 타입 힌트에 따라 자동 검증됨
- 잘못된 타입 입력 시 ValidationError 발생
- Optional 필드는 None 허용
- Field의 default_factory로 동적 기본값 생성

### JSON 직렬화
- 모든 모델은 `.dict()`, `.json()` 메서드 지원
- datetime 객체는 ISO 형식으로 자동 변환
- UUID는 문자열로 자동 변환

### 스키마 생성
- OpenAPI 스키마 자동 생성 지원
- FastAPI와 완벽 호환
- 스키마 예시 포함으로 문서화 개선

---

## 모범 사례 (Best Practices)

### 1. 일관된 응답 구조 유지
- 항상 StandardResponse 또는 그 하위 클래스 사용
- ResponseBuilder를 통한 응답 생성 권장

### 2. 에러 처리
- 모든 에러는 표준화된 형식으로 반환
- 에러 코드는 대문자와 언더스코어 사용 (예: `INVALID_INPUT`)
- 사용자 친화적 메시지와 기술적 세부사항 분리

### 3. 메타데이터 활용
- API 버전, 실행 환경 등 추가 정보 포함
- 디버깅과 모니터링에 유용한 정보 제공

### 4. 페이지네이션
- 대량 데이터는 항상 페이지네이션 적용
- 기본 페이지 크기는 20으로 설정
- 클라이언트가 page_size 조정 가능하도록 구현

### 5. 스트리밍
- 장시간 실행 작업은 StreamResponse 사용
- progress와 step으로 진행 상황 전달
- SSE 형식으로 실시간 업데이트 제공

---

## 확장 가능성

### 새로운 응답 타입 추가
```python
class CustomResponse(StandardResponse[Dict[str, Any]]):
    custom_field: str
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)

    def custom_method(self):
        # 커스텀 로직
        pass
```

### 커스텀 검증 추가
```python
class CustomResponse(StandardResponse):
    @validator('custom_field')
    def validate_custom_field(cls, v):
        if not v.startswith('CUSTOM_'):
            raise ValueError('custom_field must start with CUSTOM_')
        return v
```

---

이 문서는 `backend/api/models/base.py` 파일의 모든 내용을 완전히 문서화한 것입니다. 각 클래스, 메서드, 속성에 대한 상세한 설명과 실제 사용 예시를 포함하고 있습니다.