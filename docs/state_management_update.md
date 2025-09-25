● 🏗️ 현재 구조 상세 분석 250925_state management-sale_agent중심으로

  1. Config (config.py) - 정적 시스템 설정

  📌 목적

  - 애플리케이션 시작 시 한 번 로드되는 불변 설정값 관리
  - 환경에 따라 바뀌지 않는 시스템 레벨 설정

  🔧 주요 구성요소

  class Config:
      # 1. 시스템 경로 (사용중 ✅)
      BASE_DIR          # 프로젝트 루트
      DB_DIR            # 데이터베이스 디렉토리
      CHECKPOINT_DIR    # 체크포인트 저장 경로
      MODEL_DIR         # 모델 파일 경로 (미사용 ⚠️ - 삭제 고려)
      LOG_DIR           # 로그 디렉토리

      # 2. 데이터베이스 경로 (사용중 ✅)
      DATABASES = {
          "hr_info": ...,           # HR 정보 DB
          "hr_rules": ...,          # HR 규칙 DB
          "sales_performance": ..., # 판매 실적 DB
          "sales_targets": ...,     # 판매 목표 DB
          "clients": ...,           # 고객 DB
          "compliance": ...         # 컴플라이언스 DB (미사용 ⚠️)
      }

      # 3. 모델 설정 (사용중 ✅)
      DEFAULT_MODELS = {
          "intent": "gpt-4o-mini",     # 의도 분석용
          "planning": "gpt-4o",         # 계획 수립용
          "execution": "gpt-4o-mini",   # 실행용 (미사용 ⚠️)
          "response": "gpt-4o-mini",    # 응답 생성용 (미사용 ⚠️)
          "analysis": "gpt-4o"          # 분석용 (미사용 ⚠️)
      }

      # 4. 시스템 제한 (사용중 ✅)
      TIMEOUTS = {
          "agent": 30,      # 에이전트 타임아웃
          "subgraph": 15,   # 서브그래프 타임아웃 (미사용 ⚠️)
          "tool": 10,       # 도구 타임아웃 (미사용 ⚠️)
          "llm": 20,        # LLM 호출 타임아웃
          "database": 5,    # DB 쿼리 타임아웃 (미사용 ⚠️)
          "total": 60       # 전체 타임아웃 (미사용 ⚠️)
      }

      # 5. 실행 설정 (부분 사용 ⚠️)
      EXECUTION = {
          "enable_parallel": True,      # 병렬 실행 (미사용)
          "enable_caching": True,       # 캐싱 활성화 (미사용)
          "enable_checkpointing": True, # 체크포인트 (사용중 ✅)
          "checkpoint_interval": 5,     # 체크포인트 간격 (미사용)
          "cache_ttl": 300,            # 캐시 TTL (미사용)
          "stream_mode": "updates"      # 스트림 모드 (미사용)
      }

      # 6. 기능 플래그 (사용중 ✅)
      FEATURES = {
          "enable_llm_planning": True,  # LLM 계획 사용 (사용중 ✅)
          "enable_semantic_search": True, # 의미 검색 (미사용 ⚠️)
          "enable_reranking": False,     # 재순위 (미사용 ⚠️)
          "enable_memory_store": True,   # 메모리 저장 (미사용 ⚠️)
          "enable_tool_validation": True, # 도구 검증 (미사용 ⚠️)
          "enable_error_recovery": True  # 오류 복구 (미사용 ⚠️)
      }

  🗑️ 삭제 고려 항목

  - MODEL_DIR - 사용하지 않음
  - DATABASES["compliance"] - 컴플라이언스 에이전트 미구현
  - DEFAULT_MODELS의 execution, response, analysis - 현재 planning만 사용
  - EXECUTION의 대부분 - checkpointing 외 미사용
  - FEATURES의 대부분 - enable_llm_planning 외 미사용

  ---
  2. Context (context.py) - 런타임 메타데이터

  📌 목적

  - 요청별로 전달되는 읽기 전용 메타데이터 관리
  - 사용자별, 세션별 정보 포함

  🔧 주요 구성요소

  # 1. AgentContext (에이전트용)
  class AgentContext(TypedDict):
      # 필수 필드 (사용중 ✅)
      user_id: str          # 사용자 ID
      session_id: str       # 세션 ID

      # 선택 필드
      request_id: Optional[str]     # 요청 ID (사용중 ✅)
      timestamp: Optional[str]       # 타임스탬프 (사용중 ✅)
      original_query: Optional[str]  # 원본 쿼리 (사용중 ✅)

      # 인증 (부분 사용 ⚠️)
      api_keys: Optional[Dict]       # API 키 (사용중 ✅)
      auth_token: Optional[str]      # 인증 토큰 (미사용 ⚠️)
      permissions: Optional[List]    # 권한 (미사용 ⚠️)

      # 사용자 설정 (사용중 ✅)
      language: Optional[str]        # 언어 설정 (사용중 ✅)
      timezone: Optional[str]        # 시간대 (미사용 ⚠️)
      preferences: Optional[Dict]    # 사용자 선호 (미사용 ⚠️)

      # 런타임 설정 (부분 사용 ⚠️)
      model_overrides: Optional[Dict]   # 모델 오버라이드 (미사용)
      timeout_overrides: Optional[Dict] # 타임아웃 오버라이드 (사용중 ✅)
      feature_flags: Optional[Dict]     # 기능 플래그 (미사용)

      # 오케스트레이션 (미사용 ⚠️)
      intent_result: Optional[Dict]     # 의도 분석 결과
      supervisor_hints: Optional[Dict]  # 수퍼바이저 힌트
      parent_context: Optional[Dict]    # 부모 컨텍스트

  # 2. SubgraphContext (서브그래프용) - 미사용 ⚠️
  class SubgraphContext(TypedDict):
      # 현재 구현된 서브그래프 없음
      ...

  # 3. SupervisorContext (오케스트레이터용) - 미사용 ⚠️
  class SupervisorContext(TypedDict):
      # 오케스트레이터 미구현
      ...

  🗑️ 삭제 고려 항목

  - SubgraphContext - 서브그래프 미구현
  - SupervisorContext - 오케스트레이터 미구현
  - auth_token, permissions - 인증 시스템 미구현
  - timezone, preferences - 사용자 설정 미사용
  - model_overrides, feature_flags - 오버라이드 미사용

  ---
  3. State (states.py) - 워크플로우 데이터

  📌 목적

  - 워크플로우 실행 중 변경되는 데이터 관리
  - 리듀서 패턴으로 자동 상태 병합

  🔧 주요 구성요소

  # 1. 리듀서 함수들 (사용중 ✅)
  def merge_dicts()       # 딕셔너리 병합 (사용중 ✅)
  def append_unique()     # 중복 제거 추가 (사용중 ✅)
  def append_with_timestamp() # 타임스탬프 추가 (미사용 ⚠️)
  def keep_max()          # 최대값 유지 (미사용 ⚠️)
  def keep_min()          # 최소값 유지 (미사용 ⚠️)
  def increment_counter() # 카운터 증가 (미사용 ⚠️)

  # 2. SalesState (사용중 ✅)
  class SalesState(BaseState):
      # 입력 필드 (사용중 ✅)
      query: str
      employee_name: Optional[str]
      period: Optional[str]
      metrics_type: Optional[str]

      # 계획 필드 (사용중 ✅)
      execution_plan: Optional[Dict]

      # 쿼리 처리 (사용중 ✅)
      parsed_query: Dict
      generated_sql: Optional[str]

      # 데이터 수집 (부분 사용 ⚠️)
      sql_result: Annotated[List, add]      # SQL 결과 (사용중 ✅)
      raw_data: Annotated[List, add]        # 원시 데이터 (미사용)

      # 집계 (사용중 ✅)
      collected_data: Annotated[Dict, merge_dicts]
      execution_results: Annotated[Dict, merge_dicts]
      aggregated_data: Annotated[Dict, merge_dicts]
      statistics: Annotated[Dict, merge_dicts]

      # 분석 (사용중 ✅)
      insights: Annotated[List, append_unique]
      recommendations: Annotated[List, append_unique] # 미사용 ⚠️

      # 출력 (사용중 ✅)
      formatted_result: Optional[str]
      final_report: Optional[Dict]

      # 메트릭 (미사용 ⚠️)
      max_value: Annotated[Optional[float], keep_max]
      min_value: Annotated[Optional[float], keep_min]
      total_processed: Annotated[int, increment_counter]

  # 3. 기타 State 클래스들 (미사용 ⚠️)
  class SearchState       # 검색 에이전트 미구현
  class OrchestratorState # 오케스트레이터 미구현
  class DataCollectionState # 데이터 수집 서브그래프 미구현
  class AnalysisState    # 분석 서브그래프 미구현

  🗑️ 삭제 고려 항목

  - 미사용 리듀서 함수들 (append_with_timestamp, keep_max, keep_min, increment_counter)
  - 미사용 State 클래스들 (SearchState, OrchestratorState, DataCollectionState, AnalysisState)
  - SalesState의 미사용 필드들 (raw_data, recommendations, max_value, min_value, total_processed)

  ---
  4. SalesAnalyticsAgent 구조 분석

  📌 클래스 구조

  class SalesAnalyticsAgent:
      # 초기화
      __init__(config)
          ├── _init_llm()          # LLM 초기화 (사용중 ✅)
          └── _build_graph()        # 워크플로우 그래프 구축 (사용중 ✅)

      # 노드 함수들 (Runtime[AgentContext] 패턴)
      ├── plan_execution()         # LLM 계획 수립 (사용중 ✅)
      ├── execute_plan()          # 계획 실행 (사용중 ✅)
      ├── analyze_query()         # 쿼리 분석 (규칙 기반) (사용중 ✅)
      ├── collect_data()          # 데이터 수집 (사용중 ✅)
      ├── process_data()          # 데이터 처리 (사용중 ✅)
      └── format_results()        # 결과 포맷팅 (사용중 ✅)

      # 헬퍼 메서드
      ├── _build_planning_prompt() # 프롬프트 생성 (사용중 ✅)
      ├── _parse_llm_response()    # LLM 응답 파싱 (사용중 ✅)
      ├── _format_korean()         # 한국어 포맷팅 (사용중 ✅)
      ├── _format_english()        # 영어 포맷팅 (사용중 ✅)
      ├── _execute_sql()           # SQL 실행 (Mock) (부분 사용 ⚠️)
      └── _invoke_subgraph()       # 서브그래프 호출 (Mock) (미사용 ⚠️)

      # 공개 인터페이스
      └── run()                    # 에이전트 실행 (사용중 ✅)

  🔄 워크플로우 패턴

  LLM 모드:
  START → plan → execute → format → END

  규칙 기반 모드:
  START → analyze → collect → process → format → END

  ---
  🎯 개선 제안

  1. 즉시 삭제 가능

  - SubgraphContext, SupervisorContext
  - SearchState, OrchestratorState, DataCollectionState, AnalysisState
  - 미사용 리듀서 함수들
  - 미사용 Config 항목들

  2. 단순화 가능

  - Context의 미사용 필드들 제거
  - State의 미사용 필드들 제거
  - Config의 EXECUTION, FEATURES 단순화

  3. Mock 구현 개선

  - _execute_sql() 실제 DB 연결 구현
  - _invoke_subgraph() 제거 또는 실제 구현

  이렇게 정리하면 코드가 훨씬 깔끔해지고 실제 사용하는 기능만 남게 됩니다.
