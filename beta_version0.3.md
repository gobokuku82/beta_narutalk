# Beta Version 0.3 - 4-Stage LLM Agent System 구현 보고서

## 📋 개요

본 시스템은 LangGraph 기반의 4개 독립 에이전트와 이를 통합 관리하는 Orchestrator로 구성된 멀티 에이전트 시스템입니다. 각 에이전트는 독립적인 sub-graph로 동작하며, AsyncSqliteSaver를 통해 상태를 관리합니다.

## 🏗️ 시스템 아키텍처

### 폴더 구조
```
backend/service/
├── core/                       # 핵심 공통 모듈
│   ├── states.py              # State 정의
│   ├── base_agent.py          # BaseAgent 추상 클래스
│   ├── config.py              # 시스템 설정
│   └── checkpointer.py        # Checkpoint 관리
├── agents/                     # 4개 기능 에이전트
│   ├── search_agent.py        # 정보 검색
│   ├── sales_analytics_agent.py # 판매 분석
│   ├── compliance_check_agent.py # 규정 확인
│   └── document_generation_agent.py # 문서 생성
└── orchestrator/              # 메인 오케스트레이터 (구현 예정)
```

## 📦 Core 모듈 상세

### 1. states.py - State 정의

#### 주요 구성 요소:
- **BaseState**: 모든 State의 기본 클래스
  - `user_id`, `session_id`, `timestamp`
  - `status` (ProcessingStatus enum)
  - `error_logs`, `metadata`

- **AgentState**: 모든 에이전트의 기본 State
  - BaseState 상속
  - `input_data`, `output_data`
  - `execution_time`, `retry_count`

- **에이전트별 전용 State**:
  - `SearchState`: 검색 쿼리, 결과, 소스 관리
  - `SalesState`: 판매 데이터, 통계, 차트 관리
  - `ComplianceState`: 규정 확인, 위반사항, 권고사항 관리
  - `DocumentState`: 문서 타입, 템플릿, 포맷 관리

### 2. base_agent.py - BaseAgent 클래스

#### 핵심 기능:
```python
class BaseAgent(ABC):
    def __init__(self, agent_name: str, checkpoint_dir: Optional[str] = None)
    async def execute(self, input_data: Dict, config: Optional[Dict]) -> Dict
    async def get_state(self, thread_id: str) -> Optional[Dict]
    async def update_state(self, thread_id: str, state_update: Dict) -> bool
```

#### 주요 특징:
- **Checkpointer 자동 초기화**: AsyncSqliteSaver 사용
- **타임아웃 관리**: 기본 30초, 설정 가능
- **에러 처리**: 상세한 로깅 및 에러 반환
- **Thread 기반 상태 관리**: session_id를 thread_id로 사용

### 3. config.py - 시스템 설정

#### 주요 설정:
- **LLM 모델 설정**:
  - 의도분석: `gpt-4o-mini`
  - 계획수립: `gpt-4o`
  - 실행: `gpt-4o-mini`
  - 응답생성: `gpt-4o-mini`

- **데이터베이스 경로**:
  ```python
  DATABASES = {
      "hr_info": "database/storage/hr_information/hr_data.db",
      "hr_rules": "database/storage/hr_rules/chromadb",
      "sales": "database/storage/sales_performance",
      "compliance": "database/storage/rules_compliance"
  }
  ```

- **타임아웃 설정**:
  - 개별 에이전트: 10초
  - 전체 오케스트레이터: 30초

### 4. checkpointer.py - Checkpoint 관리

#### 주요 함수:
- `get_checkpointer()`: AsyncSqliteSaver 인스턴스 생성
- `cleanup_old_checkpoints()`: 오래된 checkpoint 정리

## 🤖 4개 기능 에이전트 상세

### 1. SearchAgent - 정보 검색 에이전트

#### 워크플로우 구조:
```
START → analyze_query → [조건분기] → search_hr_info/search_rules → merge_results → END
```

#### 노드별 기능:

1. **analyze_query**
   - 검색 쿼리 분석
   - 키워드 추출 (한국어 불용어 제거)
   - 검색 타입 결정 (hr_only, rules_only, both)

2. **search_hr_info**
   - SQLite DB 연결 (`database/storage/hr_information/hr_data.db`)
   - 테이블: `인사자료`
   - SQL 쿼리: 성명, 부서, 직급 필드 검색
   - 최대 20건 반환

3. **search_rules**
   - 현재: Mock 데이터 반환
   - 추후: ChromaDB 키워드 검색 구현 예정

4. **merge_results**
   - HR 정보와 규정 결과 병합
   - relevance_score 기준 정렬
   - 상위 10건 반환

#### 조건부 라우팅:
```python
determine_search_type():
    if search_type == "both": → search_hr_info → search_rules
    elif search_type == "rules_only": → search_rules
    else: → search_hr_info
```

### 2. SalesAnalyticsAgent - 판매 분석 에이전트

#### 워크플로우 구조:
```
START → validate_request → fetch_data → calculate_metrics → generate_insights → format_report → END
```

#### 노드별 기능:

1. **validate_request**
   - 필수 필드 확인: `employee_name`
   - 기본값 설정: period="monthly", metrics_type="performance"

2. **fetch_sales_data**
   - 현재: Mock 데이터 생성
   - 기간별 데이터: daily(30일), weekly(12주), monthly(6개월), yearly(1년)
   - 데이터 구조: date, employee, amount, product, customer

3. **calculate_metrics**
   - 통계 계산: 총매출, 평균, 최대/최소값
   - 기간별 집계 (월별 그룹화)
   - 차트 데이터 생성 (line chart)

4. **generate_insights**
   - 기본 인사이트: 총매출, 평균 거래액, 거래 건수
   - 추세 분석: 전월 대비 증감률
   - 한국어 인사이트 생성

5. **format_report**
   - 최종 보고서 포맷
   - 통계, 인사이트, 차트 데이터 포함
   - ISO 형식 타임스탬프

### 3. ComplianceCheckAgent - 규정 준수 확인 에이전트

#### 워크플로우 구조:
```
START → parse_request → load_rules → check_compliance → identify_violations
      → generate_recommendations → create_report → END
```

#### 노드별 기능:

1. **parse_request**
   - 필수 필드: `target_action`
   - 기본 check_type: "policy"
   - 초기화: violations[], recommendations[]

2. **load_compliance_rules**
   - Mock 규정 로딩
   - 규정 타입: HR (채용), FIN (지출), GEN (일반)
   - 심각도: critical, high, medium, low

3. **check_compliance**
   - 규칙별 준수 여부 평가
   - 준수 점수 계산 (백분율)
   - 준수 기준: 80% 이상

4. **identify_violations**
   - 미준수 규칙 식별
   - 위반 세부사항 생성
   - 심각도별 분류

5. **generate_recommendations**
   - 심각도별 권고사항:
     - critical: 즉시 조치
     - high: 조치 계획 수립
     - medium/low: 개선 고려
   - 한국어 권고사항 생성

6. **create_report**
   - 준수 보고서 생성
   - 포함 내용: 준수 점수, 위반사항, 권고사항

### 4. DocumentGenerationAgent - 문서 생성 에이전트

#### 워크플로우 구조:
```
START → prepare_content → select_template → generate_sections
      → apply_formatting → finalize_document → END
```

#### 노드별 기능:

1. **prepare_content**
   - 필수 필드: `document_type`, `input_content`
   - 기본 포맷: "markdown"
   - 컨텐츠 유효성 검증

2. **select_template**
   - 문서 타입별 템플릿:
     - report: standard_report
     - memo: internal_memo
     - email: email_template
     - presentation: presentation_outline
   - 포맷팅 규칙 로드

3. **generate_sections**
   - 문서 타입별 섹션 생성:
     - Report: title, summary, body, insights, recommendations
     - Memo: header, subject, body, action_items
     - Email: greeting, body, closing
     - Presentation: title_slide, agenda, slides

4. **apply_formatting**
   - 포맷별 변환:
     - Markdown: 헤더 레벨, 리스트 스타일
     - HTML: 기본 HTML 태그
     - Text: 플레인 텍스트
   - 한국어 지원

5. **finalize_document**
   - 메타데이터 추가
   - 최종 문서 구조화
   - 생성 타임스탬프

## 🔄 에이전트 실행 흐름

### 공통 실행 패턴:
```python
# 1. 에이전트 초기화
agent = SearchAgent()

# 2. 입력 데이터 준비
input_data = {
    "query": "최시우 실적",
    "user_id": "user123",
    "session_id": "session456"
}

# 3. 에이전트 실행
result = await agent.execute(input_data)

# 4. 결과 처리
if result["status"] == "success":
    data = result["data"]
else:
    error = result["error"]
```

## 💾 데이터베이스 연결

### 1. HR 정보 (SQLite)
- 경로: `database/storage/hr_information/hr_data.db`
- 테이블: `인사자료`
- 필드: 성명, 부서, 직급 등

### 2. HR 규정 (ChromaDB)
- 경로: `database/storage/hr_rules/chromadb`
- 현재: 비어있음 (Documents: 0)
- 추후: 키워드 검색 → 임베딩 검색 전환

### 3. 판매 데이터
- 경로: `database/storage/sales_performance`
- 현재: Mock 데이터 사용
- 추후: 실제 DB 연결

### 4. 규정 준수
- 경로: `database/storage/rules_compliance`
- 현재: Mock 규정 사용
- 추후: 실제 규정 DB 연결

## 🔑 핵심 개념 정리

### 1. State Management
- 모든 에이전트는 TypedDict 기반 State 사용
- State는 워크플로우 전체에서 공유
- 각 노드는 State를 입력받아 수정 후 반환

### 2. Checkpointing
- AsyncSqliteSaver로 상태 저장/복원
- thread_id 기반 세션 관리
- 중단된 워크플로우 재개 가능

### 3. Error Handling
- 각 노드별 try-catch 구현
- error_logs 배열에 에러 누적
- status 필드로 실행 상태 추적

### 4. Async/Await
- 모든 노드 함수는 async
- 병렬 실행 지원 (asyncio.gather)
- 타임아웃 관리 (asyncio.wait_for)

## 📝 다음 단계

### 1. Orchestrator 구현
- 의도 분석 (intent_analysis.py)
- 계획 수립 + 추론 (planning.py)
- 에이전트 실행 (agent_execution.py)
- 응답 생성 (response_generation.py)

### 2. 테스트
- 각 에이전트 개별 테스트
- 통합 테스트
- 성능 최적화

### 3. 데이터베이스 연결
- 실제 판매 데이터 연결
- 규정 데이터베이스 구축
- ChromaDB 임베딩 구현

## 🎯 주의사항

1. **인코딩**: 한국어 처리 시 UTF-8 인코딩 확인
2. **타임아웃**: 각 에이전트별 적절한 타임아웃 설정
3. **메모리**: ChromaDB 임베딩 모델 로딩 시 메모리 사용량 주의
4. **에러 처리**: 데이터베이스 연결 실패 시 폴백 처리

## 📊 성능 고려사항

1. **Lazy Loading**: 임베딩 모델은 필요시에만 로드
2. **Query Optimization**: SQL 쿼리 최적화 (인덱스 활용)
3. **Caching**: 자주 사용되는 데이터 캐싱
4. **Parallel Processing**: 독립적인 작업은 병렬 처리

---

**작성일**: 2024년
**버전**: Beta 0.3
**작성자**: System Architecture Team