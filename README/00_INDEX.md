# Dream Agent - 개발 문서

> K-Beauty 글로벌 트렌드 분석 AI 에이전트

## 문서 목록

| 문서 | 설명 |
|------|------|
| [01_ARCHITECTURE.md](./01_ARCHITECTURE.md) | 전체 아키텍처 및 4-Layer 구조 |
| [02_BACKEND.md](./02_BACKEND.md) | FastAPI 백엔드 & WebSocket API |
| [03_AGENT_LAYERS.md](./03_AGENT_LAYERS.md) | Cognitive → Planning → Execution → Response |
| [04_FRONTEND.md](./04_FRONTEND.md) | HTML 대시보드 (테스트용) |
| [05_DATA_STRUCTURE.md](./05_DATA_STRUCTURE.md) | 데이터 구조 및 Mock 데이터 |
| [06_QUICKSTART.md](./06_QUICKSTART.md) | 빠른 시작 가이드 |

---

## 프로젝트 개요

```
mind_dream/beta_v001/
├── backend/          # FastAPI + WebSocket 백엔드
├── dashboard/        # HTML 테스트 대시보드
├── data/            # 데이터 저장소 (mock, collected, processed)
├── tests/           # 테스트 코드
└── README/          # 개발 문서 (현재 폴더)
```

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | FastAPI, WebSocket, LangGraph, Pydantic |
| LLM | OpenAI (gpt-4o-mini), Anthropic |
| Frontend | HTML, CSS, JavaScript (테스트용 대시보드) |
| Database | PostgreSQL (Checkpoint), Redis (Cache, Phase 2) |
| Orchestration | LangGraph (State Machine) |

## 핵심 아키텍처

```
┌─────────────────────────────────────────────────────┐
│  Layer 1: COGNITIVE (의도 파악)                     │
│  - IntentClassifier, EntityExtractor, DialogueManager│
├─────────────────────────────────────────────────────┤
│  Layer 2: PLANNING (작업 계획)                       │
│  - LLM 기반 계획 생성, Todo 생성, 의존성 관리          │
├─────────────────────────────────────────────────────┤
│  Layer 3: EXECUTION (실행)                          │
│  - DataExecutor, InsightExecutor, ContentExecutor    │
│  - OpsExecutor, ExecutionSupervisor                  │
├─────────────────────────────────────────────────────┤
│  Layer 4: RESPONSE (응답 생성)                       │
│  - 결과 요약, 마크다운 포맷팅, 보고서 저장             │
└─────────────────────────────────────────────────────┘
```

## 빠른 시작

```bash
# 1. 환경 변수 설정
cp .env.example .env
# OPENAI_API_KEY, DATABASE_URL 등 설정

# 2. 서버 실행
cd backend
uvicorn api.main:app --reload --port 8000

# 3. 대시보드 접속
# http://localhost:8000
```

## 연락처

- 프로젝트 관리자: kdy
- 최종 업데이트: 2026-01-31
