# 06. 빠른 시작 가이드

## 사전 요구사항

- Python 3.10+
- Node.js 18+ (선택, 프론트엔드 빌드용)
- PostgreSQL (Phase 2, Checkpoint 저장용)
- OpenAI API Key

---

## 설치

### 1. 저장소 클론

```bash
git clone <repository-url>
cd mind_dream/beta_v001
```

### 2. 가상환경 생성

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 편집
notepad .env  # Windows
# 또는
nano .env     # macOS/Linux
```

**.env 내용:**

```env
# 필수
OPENAI_API_KEY=sk-your-openai-api-key

# 선택
ANTHROPIC_API_KEY=sk-your-anthropic-key
DEFAULT_LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7

# 서버
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Mock 모드 (API 키 없이 테스트)
USE_MOCK_DATA=true
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

### 실행 확인

```bash
# 헬스체크
curl http://localhost:8000/health

# 응답: {"status": "healthy"}
```

---

## 대시보드 접속

브라우저에서 열기:

```
http://localhost:8000
```

### 테스트 메시지

```
라네즈 리뷰 분석해줘
```

---

## Mock 모드로 테스트

API 키 없이 테스트하려면 Mock 모드를 활성화하세요.

### 환경변수 설정

```bash
# Windows (PowerShell)
$env:USE_MOCK_DATA="true"

# Windows (CMD)
set USE_MOCK_DATA=true

# macOS/Linux
export USE_MOCK_DATA=true
```

### Mock 데이터 확인

```bash
# data/mock 폴더 구조
data/mock/
├── reviews/naver_reviews.json
├── analysis/sentiment_result.json
├── insights/insight_result.json
├── trends/google_trends.json
├── internal/products.json
└── ads/ad_prompts.json
```

---

## API 테스트

### REST API

```bash
# 동기 실행 (짧은 작업)
curl -X POST http://localhost:8000/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "안녕하세요", "language": "KOR"}'

# 비동기 실행 (긴 작업)
curl -X POST http://localhost:8000/api/agent/run-async \
  -H "Content-Type: application/json" \
  -d '{"user_input": "라네즈 리뷰 분석해줘", "language": "KOR"}'

# 상태 조회
curl http://localhost:8000/api/agent/status/{session_id}

# 실행 중지
curl -X POST http://localhost:8000/api/agent/stop/{session_id}
```

### WebSocket 테스트 (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/test-session');

ws.onopen = () => {
    console.log('Connected');
};

ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    console.log('Received:', msg);
};
```

---

## 프로젝트 구조

```
mind_dream/beta_v001/
│
├── backend/                # FastAPI 백엔드
│   ├── api/               # REST API + WebSocket
│   └── app/               # 핵심 로직
│       ├── core/          # 설정, 로깅
│       └── dream_agent/   # 4-Layer 에이전트
│           ├── cognitive/     # Layer 1
│           ├── planning/      # Layer 2
│           ├── execution/     # Layer 3
│           ├── response/      # Layer 4
│           ├── states/        # 상태 관리
│           ├── orchestrator/  # LangGraph
│           └── tools/         # 도구 모음
│
├── dashboard/              # HTML 대시보드
│   ├── templates/         # HTML 파일
│   └── static/            # CSS, JS
│
├── data/                   # 데이터 폴더
│   ├── mock/              # Mock 테스트 데이터
│   ├── collected/         # 수집된 데이터
│   └── result_trend/      # 분석 결과
│
├── tests/                  # 테스트 코드
│
└── README/                 # 개발 문서
```

---

## 주요 명령어

```bash
# 서버 실행
uvicorn api.main:app --reload --port 8000

# 테스트 실행
pytest tests/

# 린트
ruff check .

# 포맷팅
ruff format .
```

---

## 문제 해결

### 1. OpenAI API 키 오류

```
Error: OPENAI_API_KEY not set
```

**해결**: `.env` 파일에 API 키 설정

```env
OPENAI_API_KEY=sk-your-key-here
```

### 2. 모듈 임포트 오류

```
ModuleNotFoundError: No module named 'backend'
```

**해결**: PYTHONPATH 설정

```bash
# Windows
set PYTHONPATH=%cd%

# macOS/Linux
export PYTHONPATH=$(pwd)
```

### 3. WebSocket 연결 실패

```
WebSocket connection failed
```

**해결**:
- 서버가 실행 중인지 확인
- CORS 설정 확인
- 포트 충돌 확인

### 4. Mock 데이터 로드 실패

```
[MockLoader] File not found: data/mock/...
```

**해결**: Mock 데이터 파일 생성 확인

```bash
# 파일 존재 확인
dir data\mock\reviews\  # Windows
ls data/mock/reviews/   # macOS/Linux
```

---

## 다음 단계

1. [01_ARCHITECTURE.md](./01_ARCHITECTURE.md) - 전체 아키텍처 이해
2. [02_BACKEND.md](./02_BACKEND.md) - FastAPI 백엔드 상세
3. [03_AGENT_LAYERS.md](./03_AGENT_LAYERS.md) - 4-Layer 에이전트 구조
4. [04_FRONTEND.md](./04_FRONTEND.md) - HTML 대시보드
5. [05_DATA_STRUCTURE.md](./05_DATA_STRUCTURE.md) - 데이터 구조 및 Mock
