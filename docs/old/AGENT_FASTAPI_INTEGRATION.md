# 🔌 Agent-FastAPI Integration Guide

## 📋 개요
이 문서는 LangGraph Supervisor와 Worker Agents가 FastAPI 서버를 통해 데이터베이스와 통신하는 구조를 설명합니다.

## 🏗️ 시스템 아키텍처

```mermaid
graph TD
    A[Supervisor] --> B[Worker Agents]
    B --> C[FastAPI Server]
    C --> D[Database Manager]
    D --> E1[HR DB]
    D --> E2[Sales DB]
    D --> E3[Rules DB]
    D --> E4[HR Rules DB]
```

## 📁 프로젝트 구조

```
narutalk_upgrade/beta_v0033/
├── backend/
│   └── service/
│       ├── supervisor/
│       │   └── main_supervisor.py    # Supervisor 구현
│       └── worker_agents/
│           ├── sql_analysis_agent.py
│           ├── information_retrieval_agent.py
│           ├── document_generation_agent.py
│           └── compliance_validation_agent.py
├── database/
│   ├── main.py                      # FastAPI 메인 서버
│   ├── api_routes.py                # Worker Agent API 엔드포인트
│   ├── db_manager.py                # 다중 DB 관리
│   ├── hr_information/              # HR 데이터베이스
│   ├── sales_performance_db/        # 영업실적 데이터베이스
│   ├── rules_DB/                    # 규정 데이터베이스
│   └── hr_rules_db/                 # HR 규정 데이터베이스
└── docs/
    └── AGENT_FASTAPI_INTEGRATION.md # 이 문서
```

## 🚀 FastAPI 서버 시작

### 1. 환경 설정
```bash
# .env 파일 생성
cp .env.example .env

# 필수 환경 변수 설정
DATABASE_URL=sqlite+aiosqlite:///./pharma_chatbot.db
DATABASE_API_URL=http://localhost:8000/api/v1
```

### 2. 의존성 설치
```bash
pip install fastapi uvicorn aiosqlite sqlalchemy
pip install langgraph langgraph-supervisor
```

### 3. 서버 실행
```bash
# database 디렉토리에서 실행
cd database
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 또는 프로젝트 루트에서
python -m uvicorn database.main:app --reload
```

## 📡 API 엔드포인트

### 기본 엔드포인트 (기존)
- `GET /` - 루트 페이지
- `GET /health` - 헬스 체크
- `POST /conversations/` - 대화 생성
- `GET /conversations/{id}` - 대화 조회
- `POST /messages/` - 메시지 저장
- `GET /messages/{id}` - 메시지 조회

### Worker Agent 엔드포인트 (신규)

#### 1. SQL 실행
```http
POST /api/v1/execute_sql
Content-Type: application/json

{
    "query": "SELECT * FROM sales_performance WHERE month = '2024-01'",
    "database": "sales",
    "timeout": 30
}
```

#### 2. 스키마 조회
```http
GET /api/v1/schema/{table_name}?database=sales
```

#### 3. HR 정보 검색
```http
POST /api/v1/search/hr
Content-Type: application/json

{
    "query": "김철수",
    "filters": {
        "department": "영업1팀",
        "position": "과장"
    },
    "limit": 10
}
```

#### 4. 규정 검색
```http
POST /api/v1/search/regulations
Content-Type: application/json

{
    "query": "리베이트",
    "rule_type": "medical_law",
    "keywords": ["의료법", "금품", "제공"]
}
```

#### 5. 문서 생성
```http
POST /api/v1/documents/generate
Content-Type: application/json

{
    "document_type": "visit_report",
    "template_id": "VR001",
    "data": {
        "hospital": "서울대병원",
        "date": "2024-01-15",
        "purpose": "제품 설명"
    }
}
```

## 🔧 Worker Agents 설정

### SQLAnalysisAgent 사용 예시
```python
from backend.service.worker_agents.sql_analysis_agent import SQLAnalysisAgent

# FastAPI 서버와 연결
agent = SQLAnalysisAgent(api_base_url="http://localhost:8000/api/v1")

# 쿼리 실행
request = SQLQueryRequest(
    natural_language_query="지난달 실적 조회",
    target_tables=["sales_performance"],
    time_range={"start": "2024-01-01", "end": "2024-01-31"}
)

result = await agent.analyze_query(request)
```

### InformationRetrievalAgent 사용 예시
```python
from backend.service.worker_agents.information_retrieval_agent import InformationRetrievalAgent

agent = InformationRetrievalAgent(api_base_url="http://localhost:8000/api/v1")

# HR 정보 검색
result = await agent.search_hr_info("김철수 과장")

# 규정 검색
regulations = await agent.search_regulations("리베이트법")
```

## 🔄 Supervisor 통합

### Supervisor 도구 연결 방법
```python
# backend/service/supervisor/main_supervisor.py

def _create_sql_query_tool(self) -> Tool:
    from ..worker_agents.sql_analysis_agent import SQLAnalysisAgent

    async def execute_sql_wrapper(query: str) -> Dict[str, Any]:
        # Worker Agent 초기화 (API 서버 연결)
        agent = SQLAnalysisAgent(api_base_url="http://localhost:8000/api/v1")

        # 요청 생성
        request = SQLQueryRequest(
            natural_language_query=query,
            analysis_type="simple"
        )

        # 실행
        result = await agent.analyze_query(request)
        return result.dict()

    return Tool(
        name="sql_query",
        description="SQL 쿼리 실행",
        func=execute_sql_wrapper
    )
```

## 🗄️ 데이터베이스 구조

### 1. HR 데이터베이스 (`hr_data.db`)
- **인사자료**: 직원 정보 (사번, 성명, 부서, 직급, 급여 등)
- **지점연락처**: 지점별 연락처 정보

### 2. 영업실적 데이터베이스 (`sales_performance_db.db`)
- **sales_performance**: 월별 영업 실적
- **monthly_summary**: 월별 요약
- **employee_targets**: 직원별 목표

### 3. 규정 데이터베이스 (`rules.db`)
- **rules**: 일반 규정
- **medical_laws**: 의료법
- **rebate_laws**: 리베이트법
- **fair_trade_rules**: 공정거래규약

### 4. HR 규정 데이터베이스 (`hr_rules.db`)
- **hr_rules**: HR 관련 규정
- **policy_documents**: 정책 문서

## ⚙️ 환경 변수 설정

`.env` 파일 필수 설정:
```env
# Database API
DATABASE_API_URL=http://localhost:8000/api/v1
DATABASE_API_KEY=your-secure-api-key

# SQLite Databases
HR_DB_PATH=database/hr_information/hr_data.db
SALES_DB_PATH=database/sales_performance_db/sales_performance_db.db
RULES_DB_PATH=database/rules_DB/rules.db
HR_RULES_DB_PATH=database/hr_rules_db/hr_rules.db

# LLM Configuration
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
```

## 🧪 테스트

### 1. API 서버 테스트
```bash
# 헬스 체크
curl http://localhost:8000/api/v1/health

# 스키마 조회
curl http://localhost:8000/api/v1/schemas

# SQL 실행 테스트
curl -X POST http://localhost:8000/api/v1/execute_sql \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT COUNT(*) FROM sales_performance", "database": "sales"}'
```

### 2. Worker Agent 테스트
```python
# test_agents.py
import asyncio
from backend.service.worker_agents.sql_analysis_agent import SQLAnalysisAgent

async def test_sql_agent():
    agent = SQLAnalysisAgent("http://localhost:8000/api/v1")

    request = SQLQueryRequest(
        natural_language_query="직원 실적 조회",
        target_tables=["sales_performance"]
    )

    result = await agent.analyze_query(request)
    print(result)

asyncio.run(test_sql_agent())
```

## 🔒 보안 고려사항

1. **SQL Injection 방지**
   - 파라미터 바인딩 사용
   - 입력 검증 및 sanitization

2. **API 인증**
   - API 키 기반 인증 구현 필요
   - JWT 토큰 지원 고려

3. **Rate Limiting**
   - 과도한 요청 방지
   - IP 기반 제한 설정

4. **데이터 암호화**
   - 민감한 정보 암호화 저장
   - HTTPS 통신 사용

## 🐛 문제 해결

### 일반적인 문제

1. **"Database file not found" 오류**
   - 데이터베이스 파일 경로 확인
   - 상대 경로 대신 절대 경로 사용 고려

2. **"Connection refused" 오류**
   - FastAPI 서버가 실행 중인지 확인
   - 포트 번호 확인 (기본: 8000)

3. **"Timeout" 오류**
   - SQLite busy timeout 증가
   - 쿼리 최적화 필요

### 디버깅 팁

1. **로그 레벨 설정**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **FastAPI 디버그 모드**
```bash
uvicorn main:app --reload --log-level debug
```

3. **SQLite 쿼리 로깅**
```python
# database.py
engine = create_async_engine(DATABASE_URL, echo=True)
```

## 📚 참고 자료

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)
- [aiosqlite Documentation](https://aiosqlite.omnilib.dev/)

## 🔄 업데이트 내역

- **v1.1.0** (2024-01-17)
  - Worker Agent API 엔드포인트 추가
  - 다중 SQLite 데이터베이스 지원
  - 비동기 처리 구현

- **v1.0.0** (2024-01-16)
  - 초기 버전
  - 기본 대화 관리 API

---

*이 문서는 지속적으로 업데이트됩니다. 최신 버전은 프로젝트 저장소를 확인하세요.*