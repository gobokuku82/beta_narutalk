# NaruTalk AI 챗봇 시스템 설치 가이드

## 시스템 요구사항
- Python 3.11.9 (또는 3.11.x)
- Windows 10/11 (PowerShell)
- 최소 4GB RAM
- 인터넷 연결 (모델 다운로드)

## 1. 가상환경 설정

### 1.1 기존 가상환경 제거 (필요시)
```powershell
Remove-Item -Recurse -Force venv
```

### 1.2 새 가상환경 생성
```powershell
py -m venv venv --clear
```

### 1.3 가상환경 활성화
```powershell
venv\Scripts\activate
```

## 2. 패키지 설치

### 2.1 pip 업그레이드
```powershell
.\venv\Scripts\python.exe -m pip install --upgrade pip
```

### 2.2 의존성 설치
```powershell
.\venv\Scripts\pip.exe install -r requirements.txt
```

## 3. 설치 확인

### 3.1 핵심 패키지 확인
```powershell
.\venv\Scripts\pip.exe list | findstr -i "fastapi langgraph chromadb sentence torch"
```

### 3.2 임포트 테스트
```powershell
.\venv\Scripts\python.exe -c "import fastapi; print('✅ FastAPI:', fastapi.__version__)"
.\venv\Scripts\python.exe -c "from langgraph.graph import StateGraph, END, START; print('✅ LangGraph 0.5+ 호환성 확인')"
```

## 4. 서버 실행

### 4.1 백엔드 서버 시작
```powershell
cd backend
..\venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4.2 실행 스크립트 사용
```powershell
.\venv\Scripts\python.exe run_server.py
```

## 5. 접속 확인

### 5.1 웹 브라우저
```
http://localhost:8000
```

### 5.2 API 문서
```
http://localhost:8000/docs
```

### 5.3 헬스체크
```
http://localhost:8000/health
```

## 6. 주요 패키지 버전
- **FastAPI**: 0.116.0
- **LangGraph**: 0.5.2 (0.5+ 호환)
- **LangChain**: 0.3.26
- **Sentence Transformers**: 5.0.0
- **ChromaDB**: 1.0.15
- **PyTorch**: 2.7.1
- **Uvicorn**: 0.35.0

## 7. 문제 해결

### 7.1 모듈을 찾을 수 없음
```powershell
# 가상환경 재생성
Remove-Item -Recurse -Force venv
py -m venv venv --clear
.\venv\Scripts\pip.exe install -r requirements.txt
```

### 7.2 포트 충돌
```powershell
# 다른 포트 사용
cd backend
..\venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 7.3 권한 문제
```powershell
# PowerShell을 관리자 권한으로 실행
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 8. 개발 환경 설정

### 8.1 VS Code 설정
1. Python 확장 프로그램 설치
2. Python 인터프리터 선택: `.\venv\Scripts\python.exe`
3. 터미널에서 가상환경 자동 활성화

### 8.2 테스트 실행
```powershell
.\venv\Scripts\python.exe -m pytest tests/ -v
```

## 9. 프로덕션 배포

### 9.1 환경 변수 설정
```powershell
# .env 파일 생성
cp .env.example .env
```

### 9.2 프로덕션 서버 실행
```powershell
.\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

**주의사항:**
- 반드시 가상환경을 활성화한 상태에서 실행하세요
- Python 3.11.9를 사용하세요
- 모든 의존성은 requirements.txt에 명시되어 있습니다
- LangGraph 0.5+ 호환성이 보장됩니다 