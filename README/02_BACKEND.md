# 02. 백엔드 (FastAPI + WebSocket)

## 서버 구성

```
backend/
├── api/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── middleware/
│   │   └── cors.py          # CORS 설정
│   ├── routes/
│   │   ├── agent.py         # /api/agent 라우트
│   │   ├── websocket.py     # WebSocket 핸들러
│   │   └── health.py        # 헬스체크
│   └── schemas/
│       ├── agent.py         # 에이전트 요청/응답 스키마
│       └── websocket.py     # WebSocket 메시지 스키마
│
└── app/
    ├── core/
    │   ├── config.py        # 환경 설정
    │   └── logging.py       # 로깅 설정
    └── dream_agent/         # 에이전트 핵심 로직
```

---

## FastAPI 앱 (main.py)

```python
# backend/api/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(
    title="Dream Agent API",
    version="1.0.0",
    description="K-Beauty 트렌드 분석 AI 에이전트"
)

# CORS 설정
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

# 라우트 등록
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(agent_router, prefix="/api/agent", tags=["agent"])
app.include_router(websocket_router, tags=["websocket"])

# 정적 파일 & 템플릿
app.mount("/static", StaticFiles(directory="dashboard/static"))
templates = Jinja2Templates(directory="dashboard/templates")

# 대시보드 렌더링
@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
```

---

## REST API 엔드포인트

### Agent Routes (`/api/agent`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/run` | 동기 실행 (짧은 작업용) |
| `POST` | `/run-async` | 비동기 실행 + WebSocket 업데이트 |
| `GET` | `/status/{session_id}` | 실행 상태 조회 |
| `POST` | `/stop/{session_id}` | 실행 중지 (HITL) |

### 요청 스키마

```python
# POST /api/agent/run, /api/agent/run-async

class AgentRequest(BaseModel):
    user_input: str           # 사용자 입력 텍스트
    language: str = "KOR"     # 언어 코드 (KOR, EN, JP)
    session_id: Optional[str] # 세션 ID (없으면 자동 생성)

# 예시
{
    "user_input": "라네즈 리뷰를 분석해서 인사이트 뽑아줘",
    "language": "KOR"
}
```

### 응답 스키마

```python
class AgentResponse(BaseModel):
    session_id: str           # 세션 ID
    status: str               # "running", "completed", "failed", "stopped"
    response: Optional[str]   # Agent 응답 텍스트
    todos: List[Any] = []     # Todo 리스트
    error: Optional[str]      # 에러 메시지
```

---

## WebSocket API

### 연결

```javascript
// 클라이언트
const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
```

### 메시지 타입

#### Server → Client

| 타입 | 설명 | 데이터 |
|------|------|--------|
| `todo_update` | Todo 진행 상황 | `{todo_id, status, progress, message}` |
| `complete` | 실행 완료 | `{response, todos, execution_time}` |
| `error` | 오류 발생 | `{error, details}` |
| `hitl_request` | 사용자 입력 필요 | `{prompt, options}` |

#### Client → Server

| 타입 | 설명 | 데이터 |
|------|------|--------|
| `ping` | Keep-alive | `{}` |
| `stop` | 실행 중지 | `{}` |
| `resume` | 재개 | `{}` |
| `input` | HITL 응답 | `{value}` |

### 메시지 형식

```python
# WebSocket 메시지 스키마
class WSMessage(BaseModel):
    type: str       # 메시지 타입
    data: dict      # 페이로드
    timestamp: str  # ISO 형식 타임스탬프
```

---

## 실행 흐름

```
┌─────────────┐     POST /run-async      ┌─────────────┐
│   Client    │ ─────────────────────────▶│   FastAPI   │
│  (Browser)  │                           │   Server    │
└─────────────┘                           └─────────────┘
      │                                          │
      │          WebSocket 연결                   │
      │◀─────────────────────────────────────────│
      │     ws://localhost:8000/ws/{session_id}  │
      │                                          │
      │                                          ▼
      │                                   ┌─────────────┐
      │                                   │ LangGraph   │
      │                                   │   Agent     │
      │                                   └─────────────┘
      │                                          │
      │          todo_update                     │
      │◀─────────────────────────────────────────│
      │     {"type": "todo_update", ...}         │
      │                                          │
      │          todo_update (반복)               │
      │◀─────────────────────────────────────────│
      │                                          │
      │          complete                        │
      │◀─────────────────────────────────────────│
      │     {"type": "complete", "data": {...}}  │
```

---

## 환경 설정

### .env 파일

```env
# LLM 설정
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
DEFAULT_LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7

# 서버 설정
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# 데이터베이스 (Phase 2)
DATABASE_URL=postgresql://user:pass@localhost:5432/octormate_system
CHECKPOINT_DB_URI=postgresql://postgres:root1234@localhost:5432/octormate_system

# Mock 모드
USE_MOCK_DATA=false
```

### Config 클래스

```python
# backend/app/core/config.py

class Settings(BaseSettings):
    # LLM
    openai_api_key: str
    anthropic_api_key: Optional[str]
    default_llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.7

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # Database
    database_url: Optional[str]
    checkpoint_db_uri: Optional[str]

    class Config:
        env_file = ".env"
```

---

## 서버 실행

### 개발 모드

```bash
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 프로덕션 모드

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker (추후)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 에러 처리

### HTTP 에러

```python
from fastapi import HTTPException

@router.post("/run")
async def run_agent(request: AgentRequest):
    if not request.message:
        raise HTTPException(status_code=400, detail="Message is required")

    try:
        result = await agent.run(request.message)
        return AgentResponse(status="completed", data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### WebSocket 에러

```python
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    try:
        await websocket.accept()
        # ... 처리 로직
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "data": {"error": str(e)}
        })
```

---

## 로깅

```python
# backend/app/core/logging.py

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)

# 사용 예
logger.info("[Agent] Starting execution...")
logger.error(f"[Agent] Execution failed: {error}")
```

---

## 테스트

```bash
# API 테스트
curl -X POST http://localhost:8000/api/agent/run-async \
  -H "Content-Type: application/json" \
  -d '{"user_input": "라네즈 리뷰 분석해줘", "language": "KOR"}'

# 헬스체크
curl http://localhost:8000/health
```
