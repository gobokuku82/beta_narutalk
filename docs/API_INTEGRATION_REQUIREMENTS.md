# Agent - FastAPI - Database 연동 필수 정보

## 1. 시스템 아키텍처
```
[Worker Agents] <--HTTP--> [FastAPI Server] <--SQL--> [SQLite Databases]
```

## 2. Agent가 알아야 할 정보

### 2.1 API 엔드포인트 정보
```python
# Base URL
API_BASE_URL = "http://localhost:8000/api/v1"

# 필수 엔드포인트
- POST /api/v1/execute_sql         # SQL 쿼리 실행
- GET  /api/v1/schema/{table}      # 테이블 스키마 조회
- POST /api/v1/search/hr           # HR 데이터 검색
- POST /api/v1/search/sales        # 영업 데이터 검색
- POST /api/v1/search/regulations  # 규정 검색
- GET  /api/v1/rules/{rule_type}   # 규칙 조회
```

### 2.2 요청/응답 포맷
```python
# SQL 실행 요청
{
    "query": "SELECT * FROM employees WHERE department = 'Sales'",
    "database": "hr"  # Optional: hr, sales, rules
}

# 검색 요청
{
    "query": "김철수 직원 정보",
    "filters": {
        "department": "영업부",
        "date_range": {"start": "2024-01-01", "end": "2024-12-31"}
    },
    "limit": 10
}

# 응답 포맷
{
    "status": "success",
    "data": [...],
    "metadata": {
        "total_count": 100,
        "execution_time": 0.5
    },
    "error": null
}
```

### 2.3 에러 처리
```python
# Agent에서 처리해야 할 HTTP 상태 코드
- 200: 성공
- 400: 잘못된 요청 (파라미터 오류)
- 404: 리소스 없음 (테이블/데이터 없음)
- 500: 서버 오류 (DB 연결 실패 등)

# 에러 응답 포맷
{
    "status": "error",
    "error": {
        "code": "INVALID_SQL",
        "message": "SQL syntax error near 'SELCT'",
        "details": {...}
    }
}
```

## 3. FastAPI가 알아야 할 정보

### 3.1 데이터베이스 연결 정보
```python
DATABASES = {
    "hr": {
        "path": "database/raw_data/hr.db",
        "tables": ["employees", "departments", "positions", "salaries"]
    },
    "sales": {
        "path": "database/raw_data/sales.db",
        "tables": ["sales_performance", "client_trends", "products", "targets"]
    },
    "rules": {
        "path": "database/raw_data/rules.db",
        "tables": ["compliance_rules", "validation_rules", "business_rules"]
    },
    "hr_rules": {
        "path": "database/raw_data/hr_rules.db",
        "tables": ["hr_policies", "attendance_rules", "payroll_rules"]
    }
}
```

### 3.2 Agent 별 권한 관리
```python
AGENT_PERMISSIONS = {
    "sql_analysis_agent": {
        "databases": ["hr", "sales"],
        "operations": ["SELECT", "ANALYZE"],
        "row_limit": 10000
    },
    "information_retrieval_agent": {
        "databases": ["hr", "rules", "hr_rules"],
        "operations": ["SELECT"],
        "row_limit": 1000
    },
    "compliance_validation_agent": {
        "databases": ["rules", "hr_rules"],
        "operations": ["SELECT"],
        "row_limit": 500
    },
    "document_generation_agent": {
        "databases": ["hr", "sales"],
        "operations": ["SELECT"],
        "row_limit": 100
    }
}
```

### 3.3 보안 설정
```python
# API Key 인증 (Optional)
API_KEY = "your-secure-api-key"

# Rate Limiting
RATE_LIMIT = {
    "requests_per_minute": 60,
    "requests_per_hour": 1000
}

# Query Timeout
QUERY_TIMEOUT = 30  # seconds

# 금지된 SQL 키워드
FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE"]
```

## 4. Database가 제공해야 할 정보

### 4.1 스키마 정보
```sql
-- 각 테이블의 스키마를 제공
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department_id INTEGER,
    position TEXT,
    hire_date DATE,
    salary DECIMAL(10,2),
    FOREIGN KEY (department_id) REFERENCES departments(id)
);
```

### 4.2 인덱스 정보
```sql
-- 성능 최적화를 위한 인덱스
CREATE INDEX idx_emp_dept ON employees(department_id);
CREATE INDEX idx_emp_hire_date ON employees(hire_date);
CREATE INDEX idx_sales_date ON sales_performance(sale_date);
```

### 4.3 데이터 통계
```python
TABLE_STATISTICS = {
    "employees": {
        "row_count": 1500,
        "avg_row_size": 256,
        "last_updated": "2024-12-01"
    },
    "sales_performance": {
        "row_count": 50000,
        "avg_row_size": 512,
        "last_updated": "2024-12-15"
    }
}
```

## 5. 연동 시 체크리스트

### 5.1 Agent 설정
- [ ] API Base URL 설정 확인
- [ ] API 엔드포인트 경로 확인 (/api/v1 prefix)
- [ ] Timeout 설정 (기본 30초)
- [ ] 에러 핸들링 로직 구현
- [ ] Retry 로직 구현 (최대 3회)

### 5.2 FastAPI 서버 설정
- [ ] CORS 설정 (Agent에서 호출 가능하도록)
- [ ] 로깅 설정 (요청/응답 로깅)
- [ ] 에러 핸들러 등록
- [ ] 미들웨어 설정 (인증, Rate Limiting)
- [ ] 데이터베이스 연결 풀 설정

### 5.3 Database 설정
- [ ] 연결 문자열 확인
- [ ] 권한 설정 확인
- [ ] 백업 정책 수립
- [ ] 트랜잭션 격리 수준 설정
- [ ] 쿼리 로깅 설정

## 6. 환경 변수 설정

### 6.1 Agent 환경 변수
```bash
# .env.agent
API_BASE_URL=http://localhost:8000
API_KEY=your-api-key
REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

### 6.2 FastAPI 환경 변수
```bash
# .env.fastapi
DATABASE_PATH=./database/raw_data
LOG_LEVEL=INFO
MAX_CONNECTIONS=100
QUERY_TIMEOUT=30
ENABLE_CORS=true
CORS_ORIGINS=["http://localhost:*"]
```

### 6.3 Database 환경 변수
```bash
# .env.database
SQLITE_TIMEOUT=30000
SQLITE_CACHE_SIZE=10000
SQLITE_PAGE_SIZE=4096
```

## 7. 테스트 시나리오

### 7.1 연결 테스트
```python
# 1. FastAPI 서버 상태 확인
GET http://localhost:8000/health

# 2. 데이터베이스 연결 확인
GET http://localhost:8000/api/v1/db/status

# 3. Agent에서 API 호출 테스트
agent = SQLAnalysisAgent(api_base_url="http://localhost:8000")
result = await agent.test_connection()
```

### 7.2 기능 테스트
```python
# 1. SQL 실행 테스트
POST http://localhost:8000/api/v1/execute_sql
{
    "query": "SELECT COUNT(*) FROM employees",
    "database": "hr"
}

# 2. 검색 테스트
POST http://localhost:8000/api/v1/search/hr
{
    "query": "영업부 직원",
    "limit": 10
}

# 3. 스키마 조회 테스트
GET http://localhost:8000/api/v1/schema/employees
```

### 7.3 부하 테스트
```python
# 동시 요청 처리 능력 테스트
import asyncio
import httpx

async def stress_test():
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(100):
            task = client.get("http://localhost:8000/api/v1/health")
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        success_count = sum(1 for r in results if r.status_code == 200)
        print(f"Success rate: {success_count}/100")
```

## 8. 모니터링 포인트

### 8.1 성능 메트릭
- API 응답 시간 (평균, P95, P99)
- 데이터베이스 쿼리 실행 시간
- 동시 연결 수
- 메모리 사용량
- CPU 사용률

### 8.2 에러 모니터링
- HTTP 에러율 (4xx, 5xx)
- 데이터베이스 연결 실패
- 타임아웃 발생 빈도
- 쿼리 에러 로그

### 8.3 비즈니스 메트릭
- Agent별 API 호출 횟수
- 가장 많이 사용되는 엔드포인트
- 평균 데이터 조회량
- 피크 시간대 분석

## 9. 문제 해결 가이드

### 9.1 연결 실패
```python
# 문제: Agent가 FastAPI 서버에 연결할 수 없음
# 해결:
1. FastAPI 서버가 실행 중인지 확인
   $ netstat -an | grep 8000

2. 방화벽 설정 확인
   $ sudo ufw status

3. CORS 설정 확인
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       allow_methods=["*"]
   )
```

### 9.2 쿼리 타임아웃
```python
# 문제: SQL 쿼리가 타임아웃됨
# 해결:
1. 쿼리 최적화 (인덱스 추가)
2. 타임아웃 값 증가
3. 쿼리 결과 캐싱 구현
```

### 9.3 데이터 불일치
```python
# 문제: Agent가 받는 데이터가 예상과 다름
# 해결:
1. 데이터베이스 스키마 확인
2. API 응답 포맷 확인
3. 데이터 인코딩 확인 (UTF-8)
```

## 10. 다음 단계

1. **FastAPI 서버 구현**
   - 모든 엔드포인트 구현
   - 미들웨어 설정
   - 에러 핸들링

2. **Agent 업데이트**
   - API 엔드포인트 경로 수정
   - 에러 핸들링 강화
   - Retry 로직 추가

3. **Supervisor 업데이트**
   - Lambda 함수를 실제 Agent 호출로 교체
   - Agent 응답 통합 로직 구현

4. **통합 테스트**
   - End-to-End 테스트
   - 성능 테스트
   - 보안 테스트

5. **배포 준비**
   - Docker 컨테이너화
   - 환경별 설정 분리
   - 모니터링 시스템 구축