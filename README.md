# ADALLPIN

ML Automation + Insight + Marketing Agent with LangGraph

## 프로젝트 개요

머신러닝 자동화를 통한 인사이트 도출 및 광고 제작, 영업 활동을 지원하는 멀티레이어 에이전트 시스템

## 프로젝트 구조

```
hyper_agent/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── api/               # FastAPI, WebSocket
│   │   ├── core/              # Core Logic
│   │   ├── db/                # Database
│   │   ├── models/            # 데이터 모델
│   │   ├── schemas/           # 스키마 모델(pydantic)
│   │   ├── services/          # ML/임베딩 모델 등 외부 서비스
│   │   └── dream_agent/       # 에이전트 (아래 상세 구조)
│   ├── scripts/
│   └── tests/
├── frontend/                  # Frontend (React, Next.js 16+)
├── data/                      # 실제 데이터 폴더
└── docs/                      # 문서 폴더
```

### dream_agent 구조

```
dream_agent/
├── orchestrator/              # 그래프 빌더 및 라우터
│   ├── builder.py            # 메인 그래프 빌더 (Entry Point)
│   └── router.py             # 라우팅 로직
│
├── cognitive/                 # Layer 1: 의도 파악
├── planning/                  # Layer 2: 계획 수립 (Todo 생성)
├── ml_execution/              # Layer 3: ML 실행
│   ├── ml_supervisor.py      # ML 레이어 조율자
│   ├── collector.py          # 데이터 수집
│   ├── preprocessor.py       # 전처리
│   ├── analyzer.py           # 분석
│   └── insight.py            # 인사이트 도출
│
├── biz_execution/             # Layer 4: 비즈니스 실행
│   ├── report/               # 보고서 에이전트
│   ├── ad_creative/          # 광고 크리에이티브 에이전트
│   ├── sales/                # 영업 에이전트
│   └── inventory/            # 재고 관리 에이전트
│
├── response/                  # Layer 5: 응답 생성
├── llm_manager/               # LLM 클라이언트 및 프롬프트
├── workflow_manager/          # Todo, HITL, 세션 관리
└── states/                    # 상태 정의 (AgentState, TodoItem)
```

## 4-Layer 아키텍처

> ML Execution과 Biz Execution은 통합된 **Execution Layer**로 운영됩니다.
> 상세 스펙 → `docs/specs/DATA_MODELS.md §2.3 Layer Enum`

```
[User Input]
     │
     ▼
┌──────────────┐  CognitiveOutput   ┌──────────────┐
│   Layer 1    │ ─────────────────► │   Layer 2    │
│  Cognitive   │  Intent + Entities │   Planning   │
│  (의도 파악)  │                    │ (계획 + Todo) │
└──────────────┘                    └──────────────┘
                                           │
                                           │ PlanningOutput
                                           │ Plan + TodoItems
                                           ▼
┌──────────────┐  ExecutionOutput   ┌──────────────┐
│   Layer 4    │ ◄───────────────── │   Layer 3    │
│   Response   │  ExecutionResults  │  Execution   │
│  (응답 생성)  │                    │ (Todo 실행)   │
└──────────────┘                    └──────────────┘
```

## 기술 스택

- **Backend**: FastAPI + WebSocket
- **Agent**: LangGraph 1.0.5 + Command API
- **Checkpointer**: AsyncPostgresSaver (PostgreSQL)
- **ML**: scikit-learn, Prophet, transformers
- **Frontend**: React + Next.js 16+

## 설치

```bash
uv sync
```

## 테스트 실행

```bash
cd test
uv run python run_all_tests.py
```

## 환경 변수

`.env.example`을 `.env`로 복사하고 필요한 값을 설정하세요.
# adallpin
