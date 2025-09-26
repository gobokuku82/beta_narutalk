# Sales Analytics Agent 테스트 결과 및 고도화 방안

## 📊 테스트 실행 요약

**테스트 일자**: 2025-01-26
**테스트 버전**: Beta v0.033
**테스트 환경**: Windows 11, Python 3.11, LangGraph 0.6.7

### 테스트 범위
1. Text2SQL 기능 (50개 테스트 케이스)
2. Data Collection Subgraph (10개 테스트 케이스)
3. Analysis Subgraph (20개 테스트 케이스)
4. 복합/단일 질의 처리 (20개 테스트 케이스)
5. E2E 사용자 시나리오

---

## 🔍 테스트 결과 분석

### 1. 작동 확인된 컴포넌트 ✅

#### 1.1 Agent 초기화
- SalesAnalyticsAgent 정상 초기화
- LLM (GPT-4o) 연동 성공
- Workflow graph 구성 완료

#### 1.2 LLM Planning
- 실행 계획 수립 기능 작동
- Subgraph 선택 로직 정상
- Tool 선택 기능 작동

#### 1.3 Basic Workflow
- State 관리 정상 작동
- Context API 정상 작동
- Checkpointing 기능 정상

### 2. 발견된 문제점 ❌

#### 2.1 SQL Generator 문제

**문제 1: 하드코딩된 컬럼명**
```python
# 현재 코드
SELECT *, `202411` as target_month FROM sales_performance
# 모든 쿼리가 202411로 고정됨
```

**원인**: `sql_generator.py`에서 날짜 처리 로직 오류
- 현재 날짜를 2025년으로 인식
- 데이터베이스는 2024년 11월까지만 존재
- Fallback이 항상 202411로 고정

**문제 2: 직원명 필터링 미작동**
```python
# 기대한 SQL
SELECT * FROM sales_performance WHERE 담당자 = '윤수아'

# 실제 생성된 SQL
SELECT * FROM sales_performance  # WHERE 절 누락
```

**원인**: parse_query 함수에서 person_name은 추출하지만 SQL 생성 시 사용하지 않음

#### 2.2 데이터 불일치

**문제**: 테스트 케이스의 직원명이 실제 DB와 불일치
```python
# 테스트 케이스
"김철수", "이영희", "박민수"  # 존재하지 않음

# 실제 DB의 직원명
"윤수아", "윤하은", "정예준", "조시현", "조하은", "최수아"
```

#### 2.3 Encoding 문제

**문제**: Windows 환경에서 한글 인코딩 오류
```
UnicodeEncodeError: 'cp949' codec can't encode character
```

**원인**:
- Rich 라이브러리의 특수문자 (✓, ✗) 출력 시 cp949 인코딩 오류
- sys.stdout 인코딩 설정 필요

#### 2.4 Subgraph 통합 문제

**문제**: Data Collection Subgraph가 실제로 데이터를 수집하지 않음
```python
# 로그 메시지
"No SQL query generated"
```

**원인**:
- SQL Generator와 Executor 간 연동 미완성
- Subgraph 내부에서 도구 호출 로직 미구현

---

## 🛠️ 수정 필요 사항

### Priority 1: SQL Generator 수정

#### 1.1 날짜 처리 로직 수정
```python
# backend/service/tools/sql_generator.py

def get_current_month_column(self):
    """현재 사용 가능한 최신 월 컬럼 반환"""
    current_date = datetime.now()

    # 데이터베이스의 실제 범위 확인
    if current_date.year == 2025:
        # 2024년 11월이 최신 데이터
        return "202411"

    # 실제 월 계산
    year_month = f"{current_date.year}{current_date.month:02d}"

    # 사용 가능한 컬럼 확인
    if year_month in self.available_columns:
        return year_month

    # Fallback: 가장 최근 사용 가능한 월
    available = [col for col in self.available_columns if col <= year_month]
    return available[-1] if available else "202411"
```

#### 1.2 WHERE 절 생성 수정
```python
def generate_sql(self, parsed_query: Dict) -> Tuple[str, str]:
    """SQL 생성 with proper WHERE clauses"""

    base_sql = "SELECT * FROM sales_performance"
    where_clauses = []

    # 직원명 필터
    if parsed_query.get('person_name') and parsed_query['person_name'] != '전체':
        where_clauses.append(f"담당자 = '{parsed_query['person_name']}'")

    # 월 필터
    if parsed_query.get('month'):
        year = parsed_query.get('year', 2024)
        column = f"{year}{parsed_query['month']:02d}"
        if column in self.available_columns:
            where_clauses.append(f"\"{column}\" IS NOT NULL")
            where_clauses.append(f"\"{column}\" > 0")

    # WHERE 절 조합
    if where_clauses:
        base_sql += " WHERE " + " AND ".join(where_clauses)

    return base_sql, "SQL generated with filters"
```

### Priority 2: Test Data 업데이트

#### 2.1 실제 직원명 사용
```python
# tests/test_sales_analytics_agent.py

ACTUAL_EMPLOYEES = [
    "윤수아", "윤하은", "정예준",
    "조시현", "조하은", "최수아"
]

def generate_text2sql_cases():
    cases = []

    # 실제 직원명으로 테스트 케이스 생성
    for emp in ACTUAL_EMPLOYEES[:3]:
        cases.extend([
            (f"{emp} 3월 실적", f"{emp}의 3월 실적 조회"),
            (f"{emp} 2024년 상반기 매출", f"{emp}의 상반기 매출"),
            (f"{emp} 작년 실적", f"{emp}의 2023년 실적"),
        ])

    return cases
```

#### 2.2 날짜 범위 수정
```python
# 사용 가능한 월 범위
AVAILABLE_MONTHS = [
    "202212", "202301", "202302", "202303", "202304", "202305",
    "202306", "202307", "202308", "202309", "202310", "202311",
    "202312", "202401", "202402", "202403", "202404", "202405",
    "202406", "202407", "202408", "202409", "202410", "202411"
]

# 테스트용 쿼리 생성
test_queries = [
    "윤수아 202403 실적",  # 특정 월
    "정예준 2024년 1분기 실적",  # 분기
    "조시현 작년 하반기 매출",  # 반기
]
```

### Priority 3: Encoding 문제 해결

#### 3.1 Console Output 수정
```python
# tests/test_sales_analytics_agent.py

import sys
import io

# Windows 환경 체크
if sys.platform == 'win32':
    # UTF-8 인코딩 설정
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace'
    )

# Rich 라이브러리 대체
class SimpleConsole:
    """Rich 라이브러리 대체용 Simple Console"""

    def print(self, text, **kwargs):
        # 특수문자를 일반 문자로 변환
        text = text.replace('✓', '[OK]')
        text = text.replace('✗', '[FAIL]')
        text = text.replace('⚠', '[WARN]')

        # ANSI 코드 제거
        import re
        text = re.sub(r'\[.*?\]', '', text)

        print(text)

# Rich 사용 가능 여부 체크
try:
    from rich.console import Console
    console = Console()
except ImportError:
    console = SimpleConsole()
```

### Priority 4: Subgraph 통합 개선

#### 4.1 Data Collection Subgraph 수정
```python
# backend/service/subgraphs/data_collection_subgraph.py

async def collect_performance_data(
    self,
    state: DataCollectionState,
    runtime: Runtime[SubgraphContext]
) -> Dict[str, Any]:
    """실제 데이터 수집 구현"""

    query_params = state.get("query_params", {})
    person_name = query_params.get("person_name")
    month = query_params.get("month")

    # SQL 생성
    sql_generator = SQLGenerator()
    parsed = {
        "person_name": person_name,
        "month": month,
        "year": 2024  # 고정값 사용
    }

    sql, explanation = sql_generator.generate_sql(parsed)

    # SQL 실행
    sql_executor = SQLExecutor()
    results, error = sql_executor.execute_query(
        sql=sql,
        db_name="sales_performance"
    )

    if error:
        return {
            "performance_data": [],
            "errors": [error]
        }

    return {
        "performance_data": results,
        "collection_status": "completed"
    }
```

---

## 📈 고도화 방안

### Phase 1: 기본 기능 안정화 (1주)

1. **SQL Generator 완전 재구현**
   - LLM 기반 SQL 생성 강화
   - Schema-aware SQL generation
   - 자동 컬럼 매핑

2. **테스트 데이터 정규화**
   - 실제 DB 스키마 기반 테스트 데이터 생성
   - Fixture 파일 생성
   - Mock 데이터 준비

3. **에러 처리 강화**
   - 명확한 에러 메시지
   - Fallback 메커니즘
   - 재시도 로직

### Phase 2: 기능 확장 (2주)

1. **복합 쿼리 지원**
   - JOIN 쿼리 자동 생성
   - 집계 함수 지원
   - 서브쿼리 처리

2. **분석 기능 강화**
   - 트렌드 분석
   - 예측 모델 통합
   - 비교 분석

3. **시각화 추가**
   - 차트 생성
   - 리포트 템플릿
   - Excel 내보내기

### Phase 3: 성능 최적화 (1주)

1. **쿼리 최적화**
   - 인덱스 활용
   - 쿼리 캐싱
   - 배치 처리

2. **병렬 처리**
   - 비동기 처리 강화
   - 동시 실행 제한
   - 리소스 관리

3. **모니터링**
   - 성능 메트릭
   - 로그 분석
   - 알림 시스템

---

## 🚀 즉시 적용 가능한 Quick Fixes

### 1. SQL Generator 날짜 수정
```python
# backend/service/tools/sql_generator.py - Line 24
# 변경 전
self.current_year = datetime.now().year  # 2025

# 변경 후
self.current_year = 2024  # 데이터베이스 최신 연도
```

### 2. 테스트 직원명 수정
```python
# tests/test_sales_analytics_agent.py
# 변경 전
basic_queries = [
    ("김철수 실적", "..."),
    ("이영희 3월 매출", "..."),

# 변경 후
basic_queries = [
    ("윤수아 실적", "..."),
    ("윤하은 3월 매출", "..."),
```

### 3. Encoding 설정 추가
```python
# 모든 테스트 파일 상단에 추가
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace'
    )
```

---

## 📋 체크리스트

### 즉시 수정 (Today)
- [ ] SQL Generator 날짜 하드코딩 수정
- [ ] 테스트 케이스 직원명 업데이트
- [ ] Windows 인코딩 문제 해결
- [ ] WHERE 절 생성 로직 수정

### 단기 개선 (This Week)
- [ ] Subgraph 통합 테스트 작성
- [ ] 에러 메시지 개선
- [ ] 로깅 강화
- [ ] 문서 업데이트

### 중장기 개선 (This Month)
- [ ] LLM 기반 SQL 생성 고도화
- [ ] 복합 쿼리 지원
- [ ] 성능 최적화
- [ ] 시각화 기능 추가

---

## 📊 성능 메트릭

### 현재 상태
- **Agent 초기화**: ~2초
- **단순 쿼리 처리**: ~3초
- **복합 쿼리 처리**: ~5초
- **성공률**: 약 60% (SQL 생성 오류로 인한 실패)

### 목표 상태
- **Agent 초기화**: <1초
- **단순 쿼리 처리**: <2초
- **복합 쿼리 처리**: <3초
- **성공률**: >95%

---

## 🔗 관련 파일

### 수정 필요 파일
1. `backend/service/tools/sql_generator.py`
2. `backend/service/subgraphs/data_collection_subgraph.py`
3. `backend/service/agents/sales_analytics_agent.py`
4. `tests/test_sales_analytics_agent.py`

### 참조 문서
1. `backend/README.md` - 시스템 아키텍처
2. `backend/MANUAL.md` - 개발자 매뉴얼
3. `database/schemas/table_descriptions.json` - 스키마 정의

---

## 📝 결론

Sales Analytics Agent는 기본적인 구조는 잘 구성되어 있으나, SQL 생성 로직과 데이터 통합 부분에서 개선이 필요합니다. 특히 날짜 처리와 직원명 필터링 같은 핵심 기능의 버그를 우선적으로 수정하고, 테스트 데이터를 실제 데이터베이스와 일치시켜야 합니다.

제안된 Quick Fixes를 즉시 적용하면 기본 기능은 정상 작동할 것으로 예상되며, 중장기 개선 사항을 단계적으로 적용하여 시스템을 고도화할 수 있습니다.

---

**작성일**: 2025-01-26
**작성자**: NaruTalk Development Team
**버전**: 1.0