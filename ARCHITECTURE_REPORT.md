# 🏗️ NaruTalk AI 챗봇 시스템 구조 분석 보고서

## 📋 프로젝트 개요
NaruTalk는 FastAPI 백엔드와 HTML/CSS/JavaScript 프론트엔드로 구성된 AI 챗봇 시스템입니다. LangGraph 0.5+를 활용한 라우터 시스템과 KURE-V1 임베딩 모델을 사용하여 4가지 기능을 제공합니다.

## 🗂️ 디렉토리 구조

```
beta_narutalk/
├── 📁 backend/                     # FastAPI 백엔드 애플리케이션
│   ├── 📁 app/
│   │   ├── 📁 api/                 # API 엔드포인트
│   │   │   ├── router.py           # 메인 API 라우터 (79 lines)
│   │   │   └── __init__.py
│   │   ├── 📁 core/                # 핵심 설정
│   │   │   ├── config.py           # 설정 파일 (31 lines)
│   │   │   └── __init__.py
│   │   ├── 📁 services/            # 비즈니스 로직
│   │   │   ├── langgraph_service.py # LangGraph 라우터 서비스 (272 lines)
│   │   │   ├── embedding_service.py # 임베딩 서비스 (115 lines)
│   │   │   ├── database_service.py  # 데이터베이스 서비스 (122 lines)
│   │   │   └── __init__.py
│   │   ├── 📁 utils/               # 유틸리티 함수
│   │   └── __init__.py
│   └── main.py                     # FastAPI 애플리케이션 진입점 (46 lines)
├── 📁 frontend/                    # 웹 프론트엔드
│   ├── index.html                  # 메인 HTML 페이지 (228 lines)
│   ├── style.css                   # 스타일시트 (578 lines)
│   └── script.js                   # JavaScript 로직 (315 lines)
├── 📁 tests/                       # 테스트 파일
│   ├── test_api.py                 # API 테스트 (187 lines)
│   ├── test_frontend.html          # 프론트엔드 테스트 (378 lines)
│   ├── 📁 unit/                    # 단위 테스트
│   └── 📁 integration/             # 통합 테스트
├── 📁 database/                    # 데이터베이스 파일
│   ├── 📁 chroma_db/               # ChromaDB 벡터 데이터베이스
│   ├── 📁 raw_data/                # 원본 문서 데이터
│   └── 📁 realationdb/             # SQLite 관계형 데이터베이스
├── 📁 models/                      # AI 모델 파일
│   ├── 📁 KURE-V1/                 # 한국어 임베딩 모델
│   └── 📁 bge-reranker-v2-m3-ko/   # 재랭킹 모델
├── 📁 venv/                        # 가상환경
├── requirements.txt                # 패키지 의존성 (33 lines)
├── run_server.py                   # 서버 실행 스크립트 (159 lines)
├── activate_env.bat                # 가상환경 활성화 스크립트
└── README.md                       # 프로젝트 문서 (203 lines)
```

## 🔧 백엔드 아키텍처

### 1. 애플리케이션 구조
- **main.py**: FastAPI 애플리케이션 진입점, CORS 설정, 정적 파일 서비스
- **core/config.py**: 환경 설정, 모델 경로, 데이터베이스 설정 관리
- **api/router.py**: RESTful API 엔드포인트 정의

### 2. 핵심 서비스 모듈

#### 📊 LangGraph 라우터 서비스 (langgraph_service.py)
- **목적**: 4가지 기능으로 사용자 요청을 라우팅
- **구조**: StateGraph 기반 워크플로우
- **기능**:
  - QA 핸들러: 질문 답변 처리
  - 문서 검색: 벡터 기반 문서 검색
  - 직원 정보: 관계형 DB 조회
  - 일반 대화: 기본 대화 처리

#### 🔍 임베딩 서비스 (embedding_service.py)
- **모델**: KURE-V1 한국어 임베딩 모델
- **데이터베이스**: ChromaDB 벡터 저장소
- **기능**: 문서 임베딩, 유사도 검색, 문서 인덱싱

#### 💾 데이터베이스 서비스 (database_service.py)
- **관계형 DB**: SQLite 기반 직원 정보 저장
- **벡터 DB**: ChromaDB 기반 문서 검색
- **기능**: 직원 정보 관리, 검색 기능

### 3. API 엔드포인트
- `POST /api/chat`: 메시지 처리
- `GET /api/chat/history`: 대화 기록 조회
- `GET /api/chat/search`: 문서 검색
- `GET /api/chat/router-types`: 라우터 유형 조회
- `GET /health`: 헬스체크

## 🎨 프론트엔드 아키텍처

### 1. 사용자 인터페이스 (index.html)
- **대시보드**: 메인 대시보드 화면
- **통계 카드**: 시스템 상태 표시
- **챗봇 위젯**: 우측 하단 고정 챗봇 UI
- **네비게이션**: 사이드바 메뉴

### 2. 스타일링 (style.css)
- **반응형 디자인**: 모바일/태블릿/데스크톱 지원
- **현대적 UI**: 그라데이션, 애니메이션 효과
- **챗봇 테마**: 고정 위젯 스타일
- **다크 모드**: 지원 준비

### 3. 인터랙션 로직 (script.js)
- **API 통신**: 백엔드 RESTful API 호출
- **실시간 메시징**: 챗봇 대화 처리
- **키보드 단축키**: Ctrl+/, ESC 지원
- **세션 관리**: 사용자 ID, 세션 ID 관리

## 🧪 테스트 구조

### 1. API 테스트 (test_api.py)
- **pytest 프레임워크**: 비동기 테스트 지원
- **엔드포인트 테스트**: 모든 API 엔드포인트 검증
- **통합 테스트**: 서비스 간 연동 테스트

### 2. 프론트엔드 테스트 (test_frontend.html)
- **인터랙티브 테스트**: 브라우저 기반 테스트
- **API 연동 테스트**: 실제 API 호출 검증
- **UI 테스트**: 사용자 인터페이스 검증

## 🗄️ 데이터 관리

### 1. 벡터 데이터베이스 (ChromaDB)
- **경로**: `database/chroma_db/`
- **용도**: 문서 임베딩 저장 및 검색
- **특징**: 벡터 유사도 검색 최적화

### 2. 관계형 데이터베이스 (SQLite)
- **경로**: `database/realationdb/`
- **파일**: `employees.db`, `client_data.db`, `personal_data.db`
- **용도**: 구조화된 데이터 저장

### 3. 원본 데이터 (raw_data)
- **경로**: `database/raw_data/`
- **파일**: 좋은제약 관련 문서 (*.docx)
- **용도**: 문서 처리 및 임베딩 소스

## 🤖 AI 모델 관리

### 1. KURE-V1 임베딩 모델
- **경로**: `models/KURE-V1/`
- **용도**: 한국어 텍스트 임베딩 생성
- **특징**: 한국어 특화 문맥 이해

### 2. BGE 재랭킹 모델
- **경로**: `models/bge-reranker-v2-m3-ko/`
- **용도**: 검색 결과 재순위 매기기
- **특징**: 한국어 검색 성능 향상

## 📦 의존성 관리

### 1. 핵심 프레임워크
- **FastAPI**: 0.115.9 (웹 프레임워크)
- **LangGraph**: 0.5.2 (워크플로우 관리)
- **LangChain**: 0.3.26 (AI 애플리케이션 프레임워크)

### 2. AI/ML 라이브러리
- **Transformers**: 4.36.2 (모델 로딩)
- **Sentence-Transformers**: 2.2.2 (임베딩)
- **ChromaDB**: 1.0.10 (벡터 데이터베이스)

### 3. 테스트 도구
- **pytest**: 8.4.1 (테스트 프레임워크)
- **pytest-asyncio**: 1.0.0 (비동기 테스트)

## 🎯 주요 기능

### 1. 4-Way 라우터 시스템
- **질문 답변**: 문서 기반 답변 생성
- **문서 검색**: 벡터 유사도 검색
- **직원 정보**: 데이터베이스 조회
- **일반 대화**: 기본 대화 처리

### 2. 실시간 챗봇 UI
- **고정 위젯**: 우측 하단 고정 위치
- **반응형 디자인**: 모든 화면 크기 지원
- **키보드 단축키**: 빠른 접근 지원

### 3. 멀티모달 지원
- **텍스트 처리**: 한국어 최적화
- **문서 검색**: 벡터 기반 검색
- **구조화 데이터**: 관계형 DB 조회

## 📈 성능 최적화

### 1. 백엔드 최적화
- **비동기 처리**: FastAPI 기반 비동기 API
- **벡터 인덱싱**: ChromaDB 최적화
- **캐싱**: 모델 로딩 최적화

### 2. 프론트엔드 최적화
- **경량화**: 최소한의 의존성
- **반응성**: 빠른 UI 반응
- **모바일 최적화**: 터치 친화적 UI

## 🔒 보안 고려사항

### 1. 데이터 보안
- **로컬 저장**: 민감 데이터 로컬 보관
- **API 검증**: 입력 데이터 검증
- **CORS 설정**: 안전한 API 접근

### 2. 사용자 관리
- **세션 관리**: 사용자 세션 추적
- **개인정보 보호**: 최소 데이터 수집

## 🚀 배포 및 실행

### 1. 환경 설정
```bash
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python run_server.py
```

### 2. 접근 URL
- **메인 애플리케이션**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **헬스체크**: http://localhost:8000/health

## 🔧 개발 도구

### 1. 코드 품질
- **Python 타입 힌트**: 타입 안정성 확보
- **FastAPI 자동 문서화**: Swagger UI 지원
- **pytest 테스트**: 포괄적 테스트 커버리지

### 2. 디버깅
- **로깅 시스템**: 상세한 로그 기록
- **에러 처리**: 적절한 예외 처리
- **개발자 도구**: 브라우저 개발자 도구 활용

## 📝 개선 사항

### 1. 단기 개선
- **의존성 정리**: requirements.txt 최적화
- **에러 처리**: 더 강력한 에러 핸들링
- **성능 모니터링**: 응답 시간 측정

### 2. 장기 개선
- **확장성**: 마이크로서비스 아키텍처
- **AI 모델**: 더 강력한 한국어 모델 도입
- **보안**: 인증/인가 시스템 추가

## 🎉 결론

NaruTalk AI 챗봇 시스템은 현대적이고 확장 가능한 아키텍처를 가지고 있습니다. LangGraph 0.5+를 활용한 라우터 시스템과 KURE-V1 한국어 임베딩 모델을 통해 효과적인 AI 챗봇 서비스를 제공합니다. 잘 구조화된 코드베이스와 포괄적인 테스트 시스템으로 안정적인 운영이 가능합니다.

---
*생성일: 2024년 12월 25일*
*버전: 1.0*
*작성자: AI Assistant* 