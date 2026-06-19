# DreamAgent

도메인 무관 **4-Layer + Manager 에이전트 프레임워크** (LangGraph). 자연어 쿼리를
`cognitive → planning → execution → response` 파이프라인으로 처리하고, 워크플로우 캔버스와
대화이력을 제공한다. 도메인(도구·데이터·스키마)은 비어 있는 골격에 주입한다.

## 구조

```
backend/
├── api/                       # FastAPI + WebSocket 엔트리
│   ├── main.py               # create_app + lifespan(Checkpointer/Graph)
│   ├── ws_agent.py / ws_hitl.py
│   └── routes/               # health, conversations
├── app/
│   ├── core/                 # config, logging, error_codes
│   ├── data_layer/           # 데이터 레이어 골격
│   │   ├── data_sources/     # 입력(raw) 추상 + File/Postgres (SOURCE_REGISTRY 빈 골격)
│   │   ├── workspace/        # 출력(정제/계산 저장) 추상 + File/Postgres
│   │   └── schemas/          # 표준 입력/출력 스키마 골격
│   └── dream_agent/
│       ├── cognitive/        # Layer 1 — 의도 파악 → StructuredQuery
│       ├── planning/         # Layer 2 — Todo + DAG 계획 (team_catalog 빈 골격)
│       ├── execution/        # Layer 3 — Todo 실행 (data_gate/state_guard)
│       ├── response/         # Layer 4 — 응답 생성
│       ├── workflow_managers/# hitl, conversation, callback, recovery, todo, memory ...
│       ├── llm_manager/      # LLM 클라이언트 + 프롬프트(도메인 무관)
│       ├── tools/            # 도구 프레임 코어 (registry/base_tool/llm_tool — 구현은 도메인이 채움)
│       ├── models/ schemas/ states/   # 에이전트 데이터 레이어
│       └── system_graph/     # 4-Layer LangGraph 조립
└── scripts/                  # setup_checkpointer / setup_data_db

frontend/                     # React + Vite (워크플로우 캔버스 + 대화이력 + 에이전트 챗)
```

## 4-Layer 아키텍처

```
[User Input] → Cognitive(의도) → Planning(계획·Todo·DAG) → Execution(실행) → Response(응답)
```

각 레이어는 `system_graph/builder.py` 가 LangGraph StateGraph 로 조립한다.
Manager 계층(HITL·대화·콜백·복구·todo·memory)이 횡단 관심사를 담당한다.

## 기술 스택

- **Backend**: FastAPI + WebSocket
- **Agent**: LangGraph + Command API
- **Checkpointer**: AsyncPostgresSaver (PostgreSQL `dreamagent_system`)
- **Data DB**: `dreamagent_data` (schema-per-client)
- **Frontend**: React + Vite + TanStack Router

## 설치 / 실행

```bash
# 의존성
uv sync

# DB 셋업 (PostgreSQL 필요)
cd backend && uv run python -m scripts.setup_checkpointer   # dreamagent_system + memory_entries
cd backend && uv run python -m scripts.setup_data_db        # dreamagent_data (schema-per-client)

# 서버 (port 8001)
uv run python run_server.py

# 프론트엔드
cd frontend && pnpm install && pnpm dev
```

## 환경 변수

`.env.example` 을 `.env` 로 복사하고 `CHECKPOINT_DB_URI` 등을 설정한다.
체크포인터 연결은 **fail-fast** — PostgreSQL 미연결 시 서버가 기동하지 않는다.

## 프레임워크 스펙

`docs/agent_specs/` — 아키텍처/상태/매니저/라이프사이클/인터페이스/웹소켓/DB/프론트 스펙.
