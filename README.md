# 제약회사 영업사원 AI 어시스턴트 (NaruTalk Upgrade)

LangGraph 기반 멀티 에이전트 시스템으로 구현된 제약회사 영업사원을 위한 AI 어시스턴트입니다.

## 프로젝트 개요

제약회사 영업사원들이 의약품 정보 조회, 문서 생성, 규정 확인, 데이터 분석 등의 업무를 효율적으로 수행할 수 있도록 돕는 AI 기반 챗봇 시스템입니다.

## 기술 스택

### Backend
- **Framework**: FastAPI (v0.115.0)
- **AI/ML**: 
  - LangGraph (v0.6.6) - 멀티 에이전트 오케스트레이션
  - LangChain (v0.3.0+) - LLM 통합
  - OpenAI/Anthropic API - LLM 모델
  - HuggingFace Transformers - 한국어 임베딩 모델
- **Database**: ChromaDB (v0.5.0) - 벡터 데이터베이스
- **Python**: 3.12

### Frontend  
- **Framework**: React (v19.1.1)
- **Build Tool**: Vite (v7.1.2)
- **HTTP Client**: Axios (v1.11.0)
- **Charts**: Recharts (v3.1.2)
- **Language**: JavaScript/JSX

## 프로젝트 구조

```
beta_v001/
├── backend/
│   └── app/
│       ├── main.py                 # FastAPI 메인 애플리케이션
│       ├── api/
│       │   └── v1/
│       │       ├── chat.py         # 채팅 엔드포인트
│       │       ├── session.py      # 세션 관리
│       │       ├── database.py     # DB 연동
│       │       └── upload.py       # 파일 업로드
│       ├── core/
│       │   └── config.py           # 설정 관리
│       └── langgraph/
│           ├── supervisor.py       # 중앙 관리 에이전트
│           ├── state.py            # 상태 관리
│           └── agents/
│               ├── info_retrieval.py    # 정보 검색 에이전트
│               ├── info_retrieval_hf.py # HuggingFace 버전
│               ├── doc_generation.py    # 문서 생성 에이전트
│               ├── compliance.py        # 규정 확인 에이전트
│               └── analytics.py         # 데이터 분석 에이전트
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # 메인 앱 컴포넌트
│   │   ├── main.jsx                # 엔트리 포인트
│   │   ├── components/
│   │   │   ├── ChatBot.jsx         # 챗봇 UI
│   │   │   ├── Message.jsx         # 메시지 컴포넌트
│   │   │   ├── Spinner.jsx         # 로딩 스피너
│   │   │   └── Visualization.jsx   # 데이터 시각화
│   │   ├── services/               # API 서비스
│   │   └── styles/                 # 스타일시트
│   ├── package.json
│   └── vite.config.js
├── database/                        # (미완성) 데이터베이스 설정
├── tests/                           # 테스트 코드
├── .env                            # 환경 변수
├── requirements_clean.txt          # Python 의존성
└── rule.md                         # 프로젝트 규칙 문서
```

## 주요 기능

### 멀티 에이전트 시스템
LangGraph 기반의 Supervisor 패턴으로 구현된 멀티 에이전트 시스템:

1. **Supervisor Agent**: 사용자 요청을 분석하고 적절한 전문 에이전트로 라우팅
2. **Info Retrieval Agent**: 의약품 정보, 학술자료, 제품 정보 검색
3. **Document Generation Agent**: 제안서, 보고서 등 문서 자동 생성
4. **Compliance Agent**: 규정 확인, 리스크 체크, 컴플라이언스 검토
5. **Analytics Agent**: 영업 데이터 분석, 통계 생성, 리포트 작성

### API 엔드포인트

- `GET /health` - 헬스체크
- `POST /api/v1/chat` - 챗봇 대화
- `GET /api/v1/session` - 세션 관리
- `POST /api/v1/upload` - 파일 업로드
- `GET /api/v1/database` - 데이터베이스 조회

## 설치 및 실행

### Prerequisites
- Python 3.12+
- Node.js 18+
- npm 또는 yarn

### Backend 설정

1. Python 가상환경 생성 및 활성화:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

2. 의존성 설치:
```bash
pip install -r requirements_clean.txt
```

3. 환경 변수 설정:
`.env` 파일에 다음 키 설정:
```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key  # Optional
USE_HUGGINGFACE=true  # HuggingFace 모델 사용 여부
```

4. 서버 실행:
```bash
cd backend
python -m app.main
```
서버는 `http://localhost:8000`에서 실행됩니다.

### Frontend 설정

1. 의존성 설치:
```bash
cd frontend
npm install
```

2. 개발 서버 실행:
```bash
npm run dev
```
프론트엔드는 `http://localhost:5173`에서 실행됩니다.

3. 프로덕션 빌드:
```bash
npm run build
```

## 개발 현황

### 완료된 기능
- ✅ FastAPI 백엔드 구조 설정
- ✅ LangGraph 멀티 에이전트 시스템 구현
- ✅ React 프론트엔드 기본 UI
- ✅ 채팅 인터페이스
- ✅ 세션 관리
- ✅ ChromaDB 벡터 검색 통합

### 진행 중
- 🔄 데이터베이스 스키마 설계 및 구현
- 🔄 사용자 인증/권한 시스템
- 🔄 파일 업로드 및 처리
- 🔄 실시간 알림 시스템

### 예정된 기능
- 📋 Redis 기반 메모리 관리
- 📋 WebSocket 실시간 통신
- 📋 고급 데이터 분석 기능
- 📋 배치 처리 시스템

## API 문서

FastAPI 자동 생성 문서:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 테스트

```bash
# Backend 테스트
cd backend
pytest

# Frontend 테스트
cd frontend
npm run test
```

## 기여 가이드

1. 이슈를 먼저 생성해주세요
2. Feature 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/AmazingFeature`)
5. Pull Request를 생성합니다

## 라이선스

이 프로젝트는 비공개 프로젝트입니다.

## 연락처

프로젝트 관련 문의사항은 이슈 트래커를 이용해주세요.