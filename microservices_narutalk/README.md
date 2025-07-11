# 🏗️ NaruTalk 마이크로서비스 아키텍처

## 📋 개요

NaruTalk 마이크로서비스는 Django 관리 시스템과 5개의 독립적인 FastAPI 에이전트로 구성된 AI 대화 시스템입니다.

## 🗂️ 시스템 구성

### Django 관리 시스템 (포트: 8000)
- **역할**: 전체 마이크로서비스 오케스트레이션 및 관리
- **주요 기능**: API 게이트웨이, 서비스 라우팅, 모니터링

### FastAPI 에이전트 서비스
1. **라우터 에이전트** (포트: 8001) - 사용자 의도 분석 및 라우팅
2. **문서 검색 에이전트** (포트: 8002) - 문서 검색 및 임베딩
3. **직원 분석 에이전트** (포트: 8003) - 직원 데이터 분석
4. **고객 정보 에이전트** (포트: 8004) - 고객 데이터 관리
5. **일반 대화 에이전트** (포트: 8005) - 일반적인 대화 처리

## 🚀 빠른 시작

### 1. 의존성 설치
```bash
# 가상환경 생성 (이미 있는 경우 생략)
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 서비스 실행
```bash
# 모든 서비스 한번에 시작
python run_all_services.py

# 또는 특정 명령어로 실행
python run_all_services.py start
```

### 3. 서비스 상태 확인
```bash
# 헬스 체크
python run_all_services.py health

# 서비스 상태 조회
python run_all_services.py status
```

### 4. 서비스 중지
```bash
# 모든 서비스 중지
python run_all_services.py stop

# 또는 Ctrl+C로 모든 서비스 중지
```

## 🌐 API 엔드포인트

### Django 관리 시스템 (http://localhost:8000)
- `GET /` - 홈 페이지
- `POST /api/chat` - 통합 채팅 API
- `GET /api/health` - 전체 서비스 헬스 체크
- `GET /api/service/status` - 서비스 상태 조회
- `POST /api/service/call` - 직접 서비스 호출
- `GET /monitoring/` - 모니터링 대시보드

### 라우터 에이전트 (http://localhost:8001)
- `POST /analyze` - 메시지 의도 분석
- `GET /health` - 헬스 체크

### 문서 검색 에이전트 (http://localhost:8002)
- `POST /search` - 문서 검색
- `GET /documents` - 문서 목록 조회
- `GET /health` - 헬스 체크

### 직원 분석 에이전트 (http://localhost:8003)
- `POST /analyze` - 직원 분석
- `GET /employees` - 직원 목록 조회
- `GET /stats` - 직원 통계
- `GET /health` - 헬스 체크

### 고객 정보 에이전트 (http://localhost:8004)
- `POST /info` - 고객 정보 조회
- `GET /clients` - 고객 목록 조회
- `GET /transactions` - 거래 내역 조회
- `GET /contracts` - 계약 목록 조회
- `GET /health` - 헬스 체크

### 일반 대화 에이전트 (http://localhost:8005)
- `POST /chat` - 일반 대화 처리
- `GET /conversation/{id}` - 대화 기록 조회
- `GET /categories` - 대화 카테고리 조회
- `GET /health` - 헬스 체크

## 🔧 사용 예시

### 1. 통합 채팅 API 사용
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "좋은제약 윤리강령에 대해 알려주세요"}'
```

### 2. 직접 서비스 호출
```bash
# 문서 검색
curl -X POST http://localhost:8002/search \
  -H "Content-Type: application/json" \
  -d '{"query": "윤리강령", "top_k": 3}'

# 직원 분석
curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d '{"analysis_type": "performance"}'

# 고객 정보 조회
curl -X POST http://localhost:8004/info \
  -H "Content-Type: application/json" \
  -d '{"info_type": "basic"}'
```

### 3. 헬스 체크
```bash
# 전체 서비스 헬스 체크
curl http://localhost:8000/api/health

# 개별 서비스 헬스 체크
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health
```

## 📊 모니터링

### 로그 확인
- Django 관리 시스템: `django_manager/logs/django_manager.log`
- 각 에이전트: 콘솔 출력 및 시스템 로그

### 서비스 상태 모니터링
```bash
# 실시간 상태 모니터링
python run_all_services.py start

# 10초마다 서비스 상태 체크
# Ctrl+C로 모든 서비스 중지
```

## 🏗️ 아키텍처 특징

### 장점
1. **확장성**: 각 서비스 독립적 스케일링 가능
2. **안정성**: 서비스 장애 격리
3. **유지보수성**: 서비스별 독립적 개발 및 배포
4. **기술 다양성**: Django + FastAPI 혼합 사용

### 통신 흐름
```
사용자 요청 → Django 관리자 → 라우터 에이전트 (의도 분석)
                    ↓
            적절한 전문 에이전트 호출
                    ↓
             결과 통합 후 응답
```

## 🔧 개발 환경 설정

### 필수 요구사항
- Python 3.8+
- Django 4.2+
- FastAPI 0.100+
- 가상환경 (venv)

### 개발 모드 실행
```bash
# Django 개발 서버 (디버그 모드)
cd django_manager
python manage.py runserver --settings=narutalk_manager.settings

# FastAPI 개발 서버 (리로드 모드)
cd agents/router_agent
uvicorn main:app --reload --port 8001
```

## 🚨 문제 해결

### 포트 충돌 해결
```bash
# 포트 사용 중인 프로세스 확인
netstat -ano | findstr :8000

# 프로세스 종료
taskkill /PID <PID> /F
```

### 서비스 시작 실패
1. 가상환경 활성화 확인
2. 의존성 설치 확인
3. 포트 충돌 확인
4. 로그 확인

### 데이터베이스 초기화
```bash
cd django_manager
python manage.py migrate
python manage.py collectstatic
```

## 📝 추가 개발 사항

### 향후 확장 가능 요소
1. **인증 시스템**: JWT 토큰 기반 인증
2. **데이터베이스 연동**: 실제 데이터베이스 연결
3. **캐싱**: Redis 캐싱 시스템
4. **로드 밸런싱**: nginx 리버스 프록시
5. **컨테이너화**: Docker 컨테이너 지원

### 개발 가이드라인
- 각 서비스는 독립적으로 개발 및 테스트
- API 스펙은 OpenAPI 3.0 표준 준수
- 로깅은 구조화된 로그 형식 사용
- 에러 처리는 일관된 형식으로 응답

## 🤝 기여하기

1. 이슈 등록
2. 기능 브랜치 생성
3. 코드 작성 및 테스트
4. 풀 리퀘스트 제출

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

---

**📞 문의사항이 있으시면 언제든 연락해주세요!** 