# Dream Agent 제품 기획서

> **상태**: Phase 0.5 완료 반영
> **최종 수정**: 2026-02-05

---

## 1. 문제 정의

### 1.1 해결하려는 문제

- **AI 도입 장벽**: 비개발자가 AI를 활용하려면 기술적 허들이 높음
- **반복적 분석 작업**: K-Beauty 트렌드 분석, 리뷰 수집, 감성 분석 등 반복 업무에 시간 소모
- **암묵지 손실**: 기업의 분석 노하우가 개인에게 귀속되어 조직 자산으로 축적 안됨

### 1.2 문제의 중요성

자연어로 "K-Beauty 트렌드 분석해줘"라고 요청하면 데이터 수집 → 분석 → 리포트 생성까지 자동화. 비개발자도 데이터 기반 의사결정이 가능하며, 분석 과정이 학습 데이터로 축적됨.

---

## 2. 목표 사용자

### 2.1 주요 사용자 페르소나

| 페르소나 | 역할 | 기술 수준 | 주요 니즈 |
|----------|------|-----------|-----------|
| 마케터 | 마케팅 담당 | 비개발자 | 리뷰 수집, 트렌드 분석, 콘텐츠 생성 |
| 데이터 분석가 | 분석 담당 | 중급 | 감성 분석, 키워드 추출, 시각화 |
| 경영진 | 의사결정자 | 비개발자 | 시장 인사이트, 경쟁사 분석, 요약 리포트 |

### 2.2 사용 환경

- 접속 방식: 웹 대시보드 (WebSocket 실시간 업데이트)
- 동시 사용자 수: Beta 기준 1-5명
- 사용 빈도: 일 1-10회 분석 요청

---

## 3. 핵심 기능 (Features)

### 3.1 기능 목록

| ID | 기능명 | 설명 | 우선순위 | 상태 |
|----|--------|------|----------|------|
| F001 | 의도 분석 | 6 도메인 × 19 카테고리 × 57 서브카테고리 계층적 분류 | P0 | 구현됨 |
| F002 | 작업 계획 | 의도 기반 Plan + Todo 생성, 리소스 할당, 실행 그래프 빌드 | P0 | 구현됨 |
| F003 | 데이터 수집 | 웹 크롤링, Google Trends, 리뷰 수집 | P0 | 구현됨 |
| F004 | ML 분석 | 감성 분석, 키워드 추출, 해시태그 분석, 트렌드 인사이트 | P1 | 구현됨 |
| F005 | 콘텐츠 생성 | 리포트, 광고 크리에이티브, 스토리보드 | P1 | 구현됨 |
| F006 | 실시간 진행 | WebSocket으로 Todo 상태 실시간 전송 | P0 | 구현됨 |
| F007 | HITL 개입 | pause, modify, delete, verify 기능 | P0 | 기본 구현 |
| F008 | 세션 영속화 | JSON 파일 기반 세션/비즈니스 데이터 저장 | P1 | 구현됨 |

### 3.2 기능별 상세

#### F001: 의도 분석 (Cognitive Layer)

- **입력**: 사용자 자연어 텍스트
- **출력**: HierarchicalIntent (domain/category/subcategory + 신뢰도)
- **분류 체계**: IntentDomain(6) → IntentCategory(19) → IntentSubcategory(57)
- **방식**: LLM 기반 분류 + 룰 기반 fallback
- **파일**: `cognitive/intent_classifier.py`, `models/intent.py`

#### F002: 작업 계획 (Planning Layer)

- **입력**: Intent + 대화 컨텍스트
- **출력**: Plan 객체 + TodoItem 리스트 + ExecutionGraph
- **특징**: Phase 2 고도화 완료 (PlanManager, ResourcePlanner, ExecutionGraphBuilder)
- **파일**: `planning/planning_node.py`, `workflow_manager/planning_manager/`

#### F003: 데이터 수집 (Execution Layer - Data)

- **도구**: web_scraper, crawler, preprocessor, google_trends
- **출력**: 수집 데이터 (CSV/JSON)
- **파일**: `execution/domain/`

#### F004: ML 분석 (Execution Layer - Insight)

- **도구**: sentiment_analyzer, keyword_extractor, hashtag_analyzer, trend_insight, competitor_analyzer
- **출력**: 분석 결과 (JSON + 시각화)
- **파일**: `execution/domain/`

---

## 4. 기술 스택

| 분류 | 기술 | 버전 |
|------|------|------|
| Orchestration | LangGraph | 0.3+ |
| Backend | FastAPI | 0.100+ |
| Realtime | WebSocket | FastAPI 내장 |
| State Persistence | AsyncPostgresSaver | langgraph-checkpoint-postgres |
| Business Data | JSON 파일 (Repository 패턴) | - |
| LLM | OpenAI GPT-4 | 설정 가능 |

---

## 5. 제약 조건

### 5.1 기술적 제약

- Python 3.10+
- PostgreSQL (checkpointer용)
- OpenAI API 키 필요

### 5.2 비용 제약

- LLM API 호출: 세션당 약 $0.05-0.15 (intent + planning + response)
- ML 분석 포함 시: 세션당 약 $0.15-0.50

### 5.3 성능 제약

- 단순 질의 (hello): ~8초 (LLM 3회 호출)
- ML 분석 요청: ~30-120초 (도구 실행 시간 포함)

---

## 6. 현재 구현 상태 (2026-02-05)

### 6.1 완료된 Phase

| Phase | 내용 | 상태 |
|-------|------|------|
| Phase 0 | 4-Layer 기본 파이프라인 | 완료 |
| Phase 0.5 | models/schemas 분리, Pydantic v2 마이그레이션 | 완료 |
| Phase 1 | Hand-off 아키텍처 전환 (Command 패턴) | 완료 |
| Phase 2 | Planning 고도화 (PlanManager, ResourcePlanner, ExecutionGraphBuilder) | 완료 |

### 6.2 인프라 상태

| 항목 | 상태 |
|------|------|
| AsyncPostgresSaver (checkpointer) | 연결 완료 |
| Hand-off (Command 패턴) | 전환 완료 |
| Intent Enum 통일 (SSOT) | 완료 |
| JSON SessionStore | 구현 완료 |
| JSON BusinessStore | 구현 완료 |

### 6.3 알려진 이슈

- `execution_result`가 AgentState에 미등록 → astream 이벤트에서 누락
- Windows ProactorEventLoop + psycopg 비호환 (--reload 시 정상)
- EntityExtractor LLM 호출 간헐적 실패 (JSON 파싱 오류)

---

## 7. 로드맵

### Next: 안정화

- [ ] AgentState에 execution_result 필드 추가
- [ ] 미사용 저장소 정리 (file_storage.py, todo_store.py)
- [ ] 대시보드 연동 강화
- [ ] 테스트 커버리지 확보

### Future: 확장

- [ ] Redis 캐시 레이어
- [ ] PostgreSQL 비즈니스 테이블 (ORM)
- [ ] 학습 데이터 수집 파이프라인
- [ ] 멀티 사용자 지원

---

## 참고 문서

- [VISION.md](VISION.md) — 비전 및 설계 원칙
- [LAYER_CONTRACTS.md](LAYER_CONTRACTS.md) — Layer 간 계약 (최신)
- [USE_CASES.md](USE_CASES.md) — 유스케이스

---

*이 문서는 코드 기반으로 2026-02-05에 업데이트되었습니다.*
