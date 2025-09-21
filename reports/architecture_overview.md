# NaruTalk System Architecture Overview
> 종합 시스템 아키텍처 분석 보고서

## 목차
1. [시스템 개요](#시스템-개요)
2. [아키텍처 구조](#아키텍처-구조)
3. [주요 컴포넌트](#주요-컴포넌트)
4. [데이터 흐름](#데이터-흐름)
5. [기술 스택](#기술-스택)
6. [시스템 통합](#시스템-통합)

---

## 시스템 개요

NaruTalk는 의료/제약 도메인에 특화된 Multi-Agent 대화형 AI 시스템입니다. LangGraph 0.6.x 기반의 Supervisor-Worker 패턴을 구현하여 복잡한 쿼리를 효율적으로 처리합니다.

### 핵심 특징
- **Multi-Agent Architecture**: 전문화된 에이전트들의 협업 시스템
- **Real-time Streaming**: SSE 기반 실시간 응답 스트리밍
- **Multi-level Caching**: 3계층 캐싱 시스템 (Memory → SQLite → Redis)
- **Domain Specialization**: 의료/제약 도메인 최적화
- **Parallel Execution**: 병렬 처리를 통한 성능 최적화

---

## 아키텍처 구조

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Client Layer                              │
│                    (Web/Mobile/API Clients)                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API Gateway                                 │
│                    FastAPI (Port 8001)                             │
│  ┌──────────────┬──────────────┬──────────────┬────────────────┐  │
│  │   Chat API   │ Sessions API │  Health API  │   Metrics API   │  │
│  └──────────────┴──────────────┴──────────────┴────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Middleware Layer                               │
│  ┌────────────┬────────────┬────────────┬──────────────────────┐  │
│  │  Logging   │Rate Limit  │   CORS     │   Error Handler      │  │
│  └────────────┴────────────┴────────────┴──────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Service Layer                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  Supervisor Service                          │  │
│  │  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │  │
│  │  │ Intent   │ Planner  │  Agent   │Execution │ Context  │  │  │
│  │  │Analyzer  │          │ Selector │ Manager  │ Manager  │  │  │
│  │  └──────────┴──────────┴──────────┴──────────┴──────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Worker Agents                             │  │
│  │  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │  │
│  │  │   SQL    │   Info   │   Doc    │Compliance│  Others  │  │  │
│  │  │Analysis  │Retrieval │Generation│Validation│          │  │  │
│  │  └──────────┴──────────┴──────────┴──────────┴──────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Cache Layer                                  │
│  ┌──────────────┬──────────────┬──────────────────────────────┐  │
│  │  L1: Memory  │  L2: SQLite  │  L3: Redis (Planned)         │  │
│  │   (LRU)      │   (Persist)  │    (Distributed)             │  │
│  └──────────────┴──────────────┴──────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Database Layer                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │               Database API (Port 8002)                      │  │
│  └────────────────────────────┬─────────────────────────────────┘  │
│                               │                                      │
│  ┌──────────────┬──────────────┬──────────────┬────────────────┐  │
│  │ Main DB      │   HR DB      │  Sales DB    │  Rules DB      │  │
│  │ (SQLite)     │  (SQLite)    │  (SQLite)    │  (SQLite)      │  │
│  └──────────────┴──────────────┴──────────────┴────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 주요 컴포넌트

### 1. **Backend API Layer** (`backend/api/`)
- **Main Application** (`main.py`): FastAPI 애플리케이션 진입점
- **Routes** (`routes/`): API 엔드포인트 정의
  - Chat API: 대화 처리 엔드포인트
  - Sessions API: 세션 관리
  - Health API: 시스템 상태 모니터링
- **Core** (`core/`): 핵심 설정 및 미들웨어
  - Config: 환경 설정 관리
  - Dependencies: 의존성 주입
  - Middleware: 요청 처리 미들웨어
- **Services** (`services/`): 비즈니스 로직
  - SupervisorService: 워크플로우 조정
  - CacheManager: 캐시 관리
  - DatabaseClient: DB 통신

### 2. **Supervisor Service** (`backend/service/supervisor/`)
- **Main Supervisor**: LangGraph 워크플로우 구현
- **Intent Analyzer**: 사용자 의도 분석
- **Planner**: 실행 계획 수립
- **Agent Selector**: 에이전트 선택 로직
- **Execution Manager**: 병렬/순차 실행 관리
- **Context Manager**: 컨텍스트 최적화
- **State Management**: 상태 추적 및 관리
- **Performance Monitor**: 성능 모니터링

### 3. **Worker Agents** (`backend/service/worker_agents/`)
- **SQL Analysis Agent**: Text2SQL 및 데이터 분석
- **Information Retrieval Agent**: 멀티소스 정보 검색
- **Document Generation Agent**: 문서 생성 및 포맷팅
- **Compliance Validation Agent**: 규정 준수 검증
- **Database API Client**: 데이터베이스 추상화

### 4. **Database Layer** (`database/`)
- **Database API** (`api/`): RESTful 데이터베이스 API
- **System** (`system/`): 데이터베이스 시스템
  - Connection: 연결 관리
  - Models: ORM 모델
  - Schemas: Pydantic 스키마
  - CRUD: 데이터베이스 작업

---

## 데이터 흐름

### 1. **요청 처리 흐름**
```
사용자 요청 → API Gateway → Middleware 처리 → SupervisorService
    ↓
Intent Analysis → Planning → Agent Selection → Execution
    ↓
Worker Agents 실행 (병렬/순차)
    ↓
결과 집계 → Response Generation → 사용자 응답
```

### 2. **캐싱 흐름**
```
요청 → L1 Cache (Memory) 확인
    ↓ (미스)
L2 Cache (SQLite) 확인
    ↓ (미스)
실제 처리 수행 → 모든 레벨에 캐시 저장
```

### 3. **스트리밍 흐름**
```
스트리밍 요청 → SSE 연결 수립
    ↓
실시간 이벤트 생성 (Progress, Token, Result)
    ↓
클라이언트로 순차 전송 → 연결 종료
```

---

## 기술 스택

### **Backend Framework**
- **FastAPI**: 고성능 웹 프레임워크
- **Pydantic**: 데이터 검증 및 설정
- **SQLAlchemy**: ORM 및 데이터베이스 추상화
- **Uvicorn**: ASGI 서버

### **AI/ML Stack**
- **LangGraph 0.6.x**: Multi-agent 워크플로우
- **LangChain**: LLM 통합 프레임워크
- **OpenAI/Anthropic**: LLM 제공자

### **Database**
- **SQLite**: 메인 및 도메인별 데이터베이스
- **Aiosqlite**: 비동기 SQLite 드라이버

### **Caching & Performance**
- **In-Memory Cache**: LRU 캐시
- **SQLite Memory**: 영속성 있는 메모리 캐시
- **Asyncio**: 비동기 프로그래밍

### **Monitoring & Logging**
- **Python Logging**: 표준 로깅
- **Custom Metrics**: 성능 메트릭 수집

---

## 시스템 통합

### **API 통합 포인트**
| 엔드포인트 | 포트 | 용도 |
|-----------|------|------|
| Chat API | 8001 | 메인 대화 처리 API |
| Database API | 8002 | 데이터베이스 접근 API |
| Health Check | 8001/api/v1/health | 시스템 상태 확인 |
| Metrics | 8001/api/v1/stats | 성능 메트릭 |

### **외부 시스템 연동**
- **LLM Providers**: OpenAI, Anthropic API
- **Vector Database**: 임베딩 저장 (계획 중)
- **Document Storage**: 파일 시스템 기반
- **External APIs**: HIRA, 논문 검색 (Mock 구현)

### **보안 및 인증**
- **API Key 인증**: 환경 변수 기반
- **Rate Limiting**: 분당 요청 제한
- **CORS 설정**: 크로스 오리진 제어
- **Error Handling**: 보안 정보 노출 방지

### **확장성 고려사항**
- **수평 확장**: 무상태 설계로 스케일아웃 가능
- **캐시 분산**: Redis 통합 계획
- **비동기 처리**: 높은 동시성 지원
- **모듈화**: 독립적인 에이전트 추가 가능

---

## 주요 설계 패턴

### **적용된 패턴**
- **Singleton Pattern**: 서비스 인스턴스 관리
- **Factory Pattern**: 에이전트 생성
- **Strategy Pattern**: 에이전트 선택 전략
- **Observer Pattern**: 성능 모니터링
- **Command Pattern**: 작업 캡슐화
- **Builder Pattern**: 워크플로우 구성
- **Adapter Pattern**: 컨텍스트 적응

### **아키텍처 원칙**
- **Separation of Concerns**: 명확한 계층 분리
- **DRY (Don't Repeat Yourself)**: 코드 재사용
- **SOLID Principles**: 객체지향 설계 원칙
- **Async-First**: 비동기 우선 설계
- **Fail-Fast**: 빠른 실패 감지

---

## 성능 최적화

### **구현된 최적화**
- **Multi-level Caching**: 3계층 캐시 시스템
- **Connection Pooling**: 데이터베이스 연결 풀
- **Parallel Execution**: 병렬 작업 처리
- **Lazy Loading**: 지연 로딩
- **Request Batching**: 요청 일괄 처리

### **모니터링 메트릭**
- **Response Time**: 응답 시간 추적
- **Cache Hit Rate**: 캐시 적중률
- **Agent Performance**: 에이전트별 성능
- **Error Rate**: 오류율 모니터링
- **Throughput**: 처리량 측정

---

## 결론

NaruTalk 시스템은 의료/제약 도메인에 특화된 고도로 모듈화되고 확장 가능한 Multi-Agent AI 시스템입니다. LangGraph 기반의 정교한 워크플로우 관리, 다층 캐싱, 실시간 스트리밍 등 현대적인 아키텍처 패턴을 적용하여 높은 성능과 확장성을 제공합니다.