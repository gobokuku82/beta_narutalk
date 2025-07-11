"# NaruTalk - 좋은제약 AI 어시스턴트

🤖 **랭그래프 기반 AI 챗봇 시스템**

KURE-V1 임베딩 모델과 랭그래프를 활용한 지능형 라우터 시스템으로 구성된 AI 어시스턴트입니다.

## 🚀 주요 기능

### 🎯 4가지 라우터 시스템
- **질문답변 (QA)**: 문서 기반 질문 답변
- **문서검색 (Document Search)**: 임베딩 기반 문서 검색
- **직원정보 (Employee Info)**: 직원 데이터베이스 조회
- **일반대화 (General Chat)**: 일반적인 대화 처리

### 💡 핵심 기술
- **프론트엔드**: HTML5, CSS3, JavaScript (ES6+)
- **백엔드**: FastAPI, Python 3.8+
- **AI 모델**: KURE-V1 임베딩 모델, BGE-Reranker-v2-m3-ko
- **라우터**: LangGraph를 활용한 지능형 라우팅
- **데이터베이스**: ChromaDB (벡터 DB), SQLite (관계형 DB)
- **UI/UX**: 모던하고 반응형인 웹 인터페이스

## 📁 프로젝트 구조

```
beta_narutalk/
├── backend/                    # FastAPI 백엔드
│   ├── app/
│   │   ├── api/               # API 라우터
│   │   ├── core/              # 핵심 설정
│   │   ├── services/          # 비즈니스 로직
│   │   └── utils/             # 유틸리티
│   └── main.py                # 메인 애플리케이션
├── frontend/                   # 프론트엔드
│   ├── index.html             # 메인 페이지
│   ├── style.css              # 스타일시트
│   └── script.js              # 자바스크립트
├── database/                   # 데이터베이스
│   ├── chroma_db/             # 벡터 데이터베이스
│   ├── raw_data/              # 원본 문서
│   └── realationdb/           # 관계형 데이터베이스
├── models/                     # AI 모델
│   ├── KURE-V1/               # 임베딩 모델
│   └── bge-reranker-v2-m3-ko/ # 리랭커 모델
├── tests/                      # 테스트 파일
│   ├── test_api.py            # API 테스트
│   └── test_frontend.html     # 프론트엔드 테스트
├── requirements.txt            # 의존성 목록
├── run_server.py              # 서버 실행 스크립트
└── activate_env.bat           # 가상환경 활성화 스크립트
```

## 🛠️ 설치 및 실행

### 1. 가상환경 설정
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (Mac/Linux)
source venv/bin/activate
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 서버 실행
```bash
# 방법 1: 직접 실행
python run_server.py

# 방법 2: 백엔드 디렉토리에서 실행
cd backend
python main.py
```

### 4. 접속 정보
- **메인 페이지**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **테스트 페이지**: http://localhost:8000/tests/test_frontend.html

## 🎨 UI/UX 특징

### 메인 대시보드
- 현대적이고 직관적인 인터페이스
- 실시간 통계 및 일정 관리
- 반응형 디자인 (모바일/태블릿/데스크톱)

### 챗봇 인터페이스
- 오른쪽 하단 고정형 챗봇 버튼
- 실시간 메시지 송수신
- 라우터 타입 및 신뢰도 표시
- 키보드 단축키 지원 (Ctrl+/, ESC)

## 🔧 API 엔드포인트

### 채팅 API
```
POST /api/v1/chat
{
    "message": "안녕하세요",
    "user_id": "user123",
    "session_id": "session123"
}
```

### 문서 검색 API
```
POST /api/v1/embedding/search?query=검색어&limit=5
```

### 라우터 타입 조회
```
GET /api/v1/router/types
```

### 채팅 기록 조회
```
GET /api/v1/chat/history/{session_id}
```

## 🧪 테스트

### 백엔드 테스트
```bash
# API 테스트 실행
python -m pytest tests/test_api.py -v
```

### 프론트엔드 테스트
웹 브라우저에서 `http://localhost:8000/tests/test_frontend.html` 접속

## 🔍 랭그래프 라우터 시스템

### 라우팅 로직
1. **메시지 분석**: 입력된 메시지를 키워드 기반으로 분석
2. **라우터 결정**: 4가지 라우터 중 최적의 라우터 선택
3. **신뢰도 계산**: 라우팅 결정에 대한 신뢰도 점수 제공
4. **응답 생성**: 선택된 라우터에서 적절한 응답 생성

### 확장 가능성
- 새로운 라우터 타입 추가 가능
- 더 정교한 분류 모델 적용 가능
- 컨텍스트 기반 라우팅 개선 가능

## 🔒 보안 고려사항

- CORS 설정 (개발 환경에서만 모든 오리진 허용)
- 입력 데이터 검증
- 세션 관리
- 에러 핸들링

## 📊 성능 최적화

- 비동기 처리 (FastAPI + async/await)
- 임베딩 벡터 캐싱
- 데이터베이스 연결 풀링
- 프론트엔드 자원 최적화

## 🚀 향후 개선 계획

1. **AI 모델 고도화**
   - 더 정교한 라우터 분류 모델
   - 컨텍스트 인식 대화 시스템
   - 개인화된 응답 생성

2. **기능 확장**
   - 음성 인식 및 TTS 지원
   - 파일 업로드 및 분석
   - 실시간 알림 시스템

3. **UI/UX 개선**
   - 다크 모드 지원
   - 다국어 지원
   - 접근성 향상

4. **성능 최적화**
   - 더 빠른 응답 시간
   - 메모리 사용량 최적화
   - 스케일링 지원

## 🤝 기여 방법

1. 이슈 리포트
2. 기능 제안
3. 코드 개선
4. 문서화 개선

## 📄 라이선스

이 프로젝트는 MIT 라이선스하에 배포됩니다.

---

**개발자**: 좋은제약 AI 팀  
**버전**: 1.0.0  
**마지막 업데이트**: 2024년 7월" 
