# 🔄 FastAPI 아키텍처 리팩토링 계획서

## 📊 프로젝트 개요

### 목적
현재 `database/` 디렉토리에 혼재되어 있는 FastAPI 엔드포인트들을 `backend/api/`로 재구성하여 관심사 분리(Separation of Concerns)를 달성하고 확장 가능한 아키텍처를 구축

### 범위
- Chat API 이동
- Supervisor Service 이동
- Database API는 현 위치 유지 (데이터 접근 계층)
- 통합 테스트 업데이트

---

## 🏗️ 아키텍처 비교

### 현재 구조 (AS-IS)
```
database/
├── main.py                 # 모든 API 통합 서버
├── api_routes.py          # Database API
├── chat_api.py            # Chat API (이동 대상)
├── supervisor_service.py  # Supervisor 서비스 (이동 대상)
├── cache_manager.py       # 캐시 관리 (이동 대상)
├── db_manager.py          # DB 관리 (유지)
└── database.py            # SQLAlchemy (유지)

backend/
├── api/                   # 비어있음
└── service/
    └── supervisor/        # LangGraph Supervisor
```

### 목표 구조 (TO-BE)
```
backend/
├── api/
│   ├── main.py           # Chat/Supervisor API 서버
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py     # API 설정
│   │   ├── dependencies.py # 의존성 주입
│   │   └── middleware.py  # 미들웨어
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py       # Chat 엔드포인트
│   │   ├── sessions.py   # 세션 관리
│   │   └── health.py     # 헬스체크
│   ├── services/
│   │   ├── __init__.py
│   │   ├── supervisor_service.py  # Supervisor 서비스
│   │   ├── cache_manager.py       # 캐시 관리
│   │   └── database_client.py     # DB API 클라이언트
│   └── models/
│       ├── __init__.py
│       ├── chat.py       # Chat 모델
│       └── session.py    # 세션 모델
│
database/
├── main.py               # Database API 서버 (유지)
├── api_routes.py        # DB 엔드포인트 (유지)
├── db_manager.py        # DB 관리 (유지)
└── database.py          # SQLAlchemy (유지)
```

---

## 📝 리팩토링 단계별 계획

### Phase 1: 준비 작업 (Day 1)
#### 1.1 백업 및 브랜치 생성
```bash
git checkout -b feature/api-refactoring
git add .
git commit -m "Backup before API refactoring"
```

#### 1.2 디렉토리 구조 생성
```bash
backend/api/
├── core/
├── routes/
├── services/
└── models/
```

#### 1.3 의존성 분석
- 현재 import 관계 파악
- 순환 참조 확인
- 공통 유틸리티 식별

### Phase 2: Core 모듈 구현 (Day 2)
#### 2.1 Config 설정
```python
# backend/api/core/config.py
class Settings:
    APP_NAME = "Pharma Chat API"
    VERSION = "2.0.0"
    API_PREFIX = "/api/v1"

    # 서버 설정
    HOST = "0.0.0.0"
    PORT = 8001  # Chat API 포트

    # Database API
    DATABASE_API_URL = "http://localhost:8002/api/v1"

    # Cache 설정
    CACHE_TTL = 300
    CACHE_MAX_SIZE = 10000

    # Supervisor 설정
    CHECKPOINT_PATH = "database/checkpointer/checkpoint.db"
    LLM_PROVIDER = "openai"
```

#### 2.2 Dependencies 설정
```python
# backend/api/core/dependencies.py
async def get_supervisor_service():
    # Supervisor 서비스 싱글톤
    pass

async def get_cache_manager():
    # 캐시 매니저 싱글톤
    pass

async def get_db_client():
    # Database API 클라이언트
    pass
```

### Phase 3: Models 이동 (Day 2)
#### 3.1 Pydantic 모델 분리
```python
# backend/api/models/chat.py
class ChatRequest(BaseModel):
    query: str
    user_id: str
    session_id: Optional[str]
    context: Dict[str, Any]

class ChatResponse(BaseModel):
    status: str
    result: Optional[Dict]
    session_id: str
```

### Phase 4: Services 이동 (Day 3)
#### 4.1 Supervisor Service 이동
- `database/supervisor_service.py` → `backend/api/services/supervisor_service.py`
- Import 경로 수정
- Database API 클라이언트로 변경

#### 4.2 Cache Manager 이동
- `database/cache_manager.py` → `backend/api/services/cache_manager.py`
- 독립적인 모듈로 유지

#### 4.3 Database Client 생성
```python
# backend/api/services/database_client.py
class DatabaseAPIClient:
    """Database API와 통신하는 클라이언트"""
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def execute_sql(self, query: str, database: str):
        # HTTP 요청으로 Database API 호출
        pass
```

### Phase 5: Routes 이동 (Day 4)
#### 5.1 Chat Routes 이동
- `database/chat_api.py` → `backend/api/routes/chat.py`
- Router prefix 조정
- Dependency injection 적용

#### 5.2 Session Routes 분리
```python
# backend/api/routes/sessions.py
@router.get("/sessions")
async def list_sessions():
    pass

@router.get("/sessions/{session_id}")
async def get_session():
    pass
```

### Phase 6: Main Application 구성 (Day 4)
#### 6.1 새로운 FastAPI 앱 생성
```python
# backend/api/main.py
from fastapi import FastAPI
from backend.api.core.config import settings
from backend.api.routes import chat, sessions, health

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION
)

# 라우터 등록
app.include_router(chat.router, prefix=f"{settings.API_PREFIX}/chat")
app.include_router(sessions.router, prefix=f"{settings.API_PREFIX}/sessions")
app.include_router(health.router, prefix=f"{settings.API_PREFIX}/health")
```

### Phase 7: Database API 정리 (Day 5)
#### 7.1 Chat 관련 코드 제거
- `database/main.py`에서 chat_api import 제거
- `database/supervisor_service.py` 파일 제거
- `database/chat_api.py` 파일 제거

#### 7.2 Database API 독립 실행
```python
# database/main.py
app = FastAPI(
    title="Database API",
    description="Database management API",
    version="1.2.0"
)
# Chat 관련 라우터 제거
```

### Phase 8: 통합 및 테스트 (Day 5-6)
#### 8.1 두 서버 동시 실행 스크립트
```python
# run_servers.py
import subprocess
import sys

def run_servers():
    # Database API (Port 8002)
    db_server = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "database.main:app",
        "--port", "8002"
    ])

    # Chat API (Port 8001)
    chat_server = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "backend.api.main:app",
        "--port", "8001"
    ])
```

#### 8.2 통합 테스트 업데이트
```python
# test_integration_v2.py
CHAT_API_URL = "http://localhost:8001"
DATABASE_API_URL = "http://localhost:8002"
```

### Phase 9: Migration 및 배포 (Day 6)
#### 9.1 데이터 마이그레이션
- 체크포인트 DB 경로 확인
- 캐시 초기화
- 세션 데이터 백업

#### 9.2 배포 준비
- Docker Compose 구성
- 환경 변수 설정
- 로드 밸런서 설정

---

## ⚠️ 위험 요소 및 대응 방안

### 위험 요소
1. **Import 경로 깨짐**
   - 대응: 체계적인 경로 매핑 문서화

2. **순환 참조**
   - 대응: 의존성 주입 패턴 사용

3. **서버 간 통신 오류**
   - 대응: Retry 로직 및 Circuit Breaker

4. **성능 저하**
   - 대응: 연결 풀링, 캐싱 강화

5. **테스트 실패**
   - 대응: 단계별 테스트, 롤백 계획

---

## 🔄 롤백 계획

### 즉시 롤백 조건
- 핵심 기능 동작 불가
- 데이터 손실 발생
- 성능 50% 이상 저하

### 롤백 절차
1. Git revert to backup commit
2. Database 체크포인트 복원
3. 캐시 초기화
4. 서버 재시작

---

## 📊 성공 지표

### 기술적 지표
- ✅ 모든 테스트 통과
- ✅ API 응답 시간 < 100ms
- ✅ 캐시 히트율 > 70%
- ✅ 에러율 < 1%

### 아키텍처 지표
- ✅ 관심사 분리 달성
- ✅ 독립적 배포 가능
- ✅ 수평 확장 가능
- ✅ 모듈 간 낮은 결합도

---

## 🚀 실행 체크리스트

### Pre-Migration
- [ ] 전체 백업 완료
- [ ] 테스트 환경 준비
- [ ] 의존성 문서화
- [ ] 팀 공지

### Migration
- [ ] Phase 1: 준비 작업
- [ ] Phase 2: Core 모듈
- [ ] Phase 3: Models 이동
- [ ] Phase 4: Services 이동
- [ ] Phase 5: Routes 이동
- [ ] Phase 6: Main App
- [ ] Phase 7: DB API 정리
- [ ] Phase 8: 통합 테스트
- [ ] Phase 9: 배포

### Post-Migration
- [ ] 성능 모니터링
- [ ] 에러 로그 확인
- [ ] 사용자 피드백
- [ ] 문서 업데이트

---

## 📅 일정

| Phase | 작업 내용 | 예상 시간 | 담당자 |
|-------|----------|-----------|---------|
| 1 | 준비 작업 | 4시간 | - |
| 2 | Core 모듈 | 4시간 | - |
| 3 | Models 이동 | 2시간 | - |
| 4 | Services 이동 | 6시간 | - |
| 5 | Routes 이동 | 4시간 | - |
| 6 | Main App 구성 | 2시간 | - |
| 7 | DB API 정리 | 2시간 | - |
| 8 | 통합 테스트 | 8시간 | - |
| 9 | 배포 준비 | 4시간 | - |

**총 예상 시간: 36시간 (4-6일)**

---

## 📚 참고 문서

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Microservices Pattern](https://microservices.io/patterns/microservices.html)
- [Python Project Structure](https://realpython.com/python-application-layouts/)

---

## 🔍 부록: 주요 코드 변경 사항

### A. Import 경로 변경 매핑

| 기존 경로 | 새 경로 |
|----------|---------|
| `from cache_manager import get_cache` | `from backend.api.services.cache_manager import get_cache` |
| `from supervisor_service import SupervisorService` | `from backend.api.services.supervisor_service import SupervisorService` |
| `from chat_api import router` | `from backend.api.routes.chat import router` |

### B. 환경 변수 변경

```bash
# 기존
DATABASE_API_URL=http://localhost:8000/api/v1

# 새로운
CHAT_API_URL=http://localhost:8001/api/v1
DATABASE_API_URL=http://localhost:8002/api/v1
```

### C. API 엔드포인트 변경

| 기능 | 기존 URL | 새 URL |
|------|----------|--------|
| Chat | http://localhost:8000/api/v1/chat | http://localhost:8001/api/v1/chat |
| Sessions | http://localhost:8000/api/v1/sessions | http://localhost:8001/api/v1/sessions |
| Database | http://localhost:8000/api/v1/execute_sql | http://localhost:8002/api/v1/execute_sql |

---

*이 문서는 리팩토링 진행 상황에 따라 지속적으로 업데이트됩니다.*

**작성일**: 2024-12-XX
**버전**: 1.0.0
**작성자**: Claude & Development Team