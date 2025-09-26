# Frontend API Interface Documentation

## 개요
이 문서는 NaruTalk 챗봇 시스템의 프론트엔드에서 백엔드 API와 통신하기 위한 인터페이스 정보를 정리합니다.

## 1. API 서버 정보

### Chat API Server
- **Base URL**: `http://localhost:8001/api/v1`
- **Port**: 8001
- **Description**: 메인 챗봇 대화 처리 서버
- **CORS**: 모든 origin 허용 (개발 환경)

### Database API Server
- **Base URL**: `http://localhost:8002/api/v1`
- **Port**: 8002
- **Description**: 데이터베이스 관리 및 Worker Agent API
- **CORS**: 모든 origin 허용 (개발 환경)

## 2. 주요 엔드포인트

### 2.1 Chat Endpoints (Port: 8001)

#### POST `/api/v1/chat`
일반 대화 요청 처리

**Request Body:**
```json
{
  "query": "김철수 직원의 2024년 실적을 분석해주세요",
  "user_id": "emp_001",
  "session_id": "session_123",  // optional
  "context": {
    "role": "영업관리자",
    "department": "영업1팀"
  },
  "use_cache": true
}
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "final_answer": "김철수 직원의 2024년 실적은...",
    "domain": "sales_analysis",
    "data_sources": ["sales_performance", "hr_data"],
    "agents_used": ["sql_analysis_agent", "information_retrieval_agent"]
  },
  "session_id": "session_123",
  "cached": false,
  "response_time": 1.234,
  "timestamp": "2024-01-20T10:30:00"
}
```

#### GET `/api/v1/chat/stream`
스트리밍 대화 응답 (Server-Sent Events)

**Query Parameters:**
- `query`: 사용자 질의 (required)
- `user_id`: 사용자 ID (required)
- `session_id`: 세션 ID (optional)

**Response (SSE format):**
```
event: message
data: {"type": "content", "data": "분석을 시작합니다...", "timestamp": "2024-01-20T10:30:00"}

event: message
data: {"type": "agent", "data": "sql_analysis_agent 실행 중...", "timestamp": "2024-01-20T10:30:01"}

event: message
data: {"type": "content", "data": "김철수 직원의 실적은...", "timestamp": "2024-01-20T10:30:02"}

event: message
data: {"type": "done", "data": {"agents_used": ["sql_analysis_agent"]}, "timestamp": "2024-01-20T10:30:03"}
```

#### POST `/api/v1/chat/feedback`
사용자 피드백 제출

**Request Body:**
```json
{
  "session_id": "session_123",
  "message_id": "msg_456",
  "rating": 4,
  "feedback": "정확한 분석이었습니다",
  "category": "accuracy"
}
```

### 2.2 Session Endpoints (Port: 8001)

#### GET `/api/v1/sessions/{session_id}`
세션 정보 조회

#### GET `/api/v1/sessions/{session_id}/messages`
세션의 모든 메시지 조회

### 2.3 Health Check (Port: 8001)

#### GET `/api/v1/health`
서비스 상태 확인

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-20T10:30:00"
}
```

## 3. WebSocket 연결 (향후 구현 예정)

### WebSocket URL
- **URL**: `ws://localhost:8001/ws/{user_id}`
- **Protocol**: WebSocket
- **Purpose**: 실시간 양방향 통신

## 4. 에러 처리

### 에러 응답 형식
```json
{
  "status": "error",
  "error": "에러 메시지",
  "detail": "상세 에러 정보",
  "timestamp": "2024-01-20T10:30:00"
}
```

### HTTP 상태 코드
- `200 OK`: 성공
- `400 Bad Request`: 잘못된 요청
- `401 Unauthorized`: 인증 실패
- `404 Not Found`: 리소스 없음
- `500 Internal Server Error`: 서버 에러
- `503 Service Unavailable`: 서비스 이용 불가

## 5. 인증 및 보안

### API Key (선택적)
환경변수 `API_KEY`가 설정된 경우:
```javascript
headers: {
  'X-API-Key': 'your-api-key'
}
```

## 6. 시스템 응답 상태

### Agent 실행 상태
1. **thinking**: 사용자 의도 분석 중
2. **planning**: 실행 계획 수립 중
3. **executing**: 에이전트 실행 중
4. **complete**: 처리 완료

### 사용 가능한 Agent 목록
- `sql_analysis_agent`: SQL 데이터 분석
- `information_retrieval_agent`: 정보 검색
- `document_generation_agent`: 문서 생성
- `compliance_validation_agent`: 규정 검증

## 7. 프론트엔드 구현 가이드

### 기본 요구사항
1. **입력 인터페이스**
   - 텍스트 입력창
   - 전송 버튼
   - 엔터키 전송 지원

2. **출력 인터페이스**
   - 사용자 메시지 표시
   - AI 응답 표시
   - 타임스탬프 표시

3. **시스템 상태 표시**
   - 현재 실행 중인 에이전트
   - 처리 상태 (thinking/planning/executing/complete)
   - 응답 시간

4. **스트리밍 지원**
   - SSE (Server-Sent Events) 처리
   - 실시간 메시지 업데이트
   - 연결 상태 표시

### JavaScript 예제 코드

#### 일반 대화 요청
```javascript
async function sendMessage(message) {
  const response = await fetch('http://localhost:8001/api/v1/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query: message,
      user_id: 'test_user',
      use_cache: true
    })
  });

  const data = await response.json();
  return data;
}
```

#### 스트리밍 응답 처리
```javascript
function streamChat(message) {
  const eventSource = new EventSource(
    `http://localhost:8001/api/v1/chat/stream?query=${encodeURIComponent(message)}&user_id=test_user`
  );

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch(data.type) {
      case 'content':
        // 컨텐츠 업데이트
        appendMessage(data.data);
        break;
      case 'agent':
        // 에이전트 상태 업데이트
        updateAgentStatus(data.data);
        break;
      case 'done':
        // 완료 처리
        eventSource.close();
        break;
      case 'error':
        // 에러 처리
        showError(data.error);
        eventSource.close();
        break;
    }
  };

  eventSource.onerror = (error) => {
    console.error('SSE Error:', error);
    eventSource.close();
  };
}
```

## 8. 테스트 시나리오

### 기본 테스트
1. 서버 연결 확인 (Health Check)
2. 간단한 질의 전송
3. 응답 수신 및 표시

### 스트리밍 테스트
1. 스트리밍 연결 생성
2. 실시간 메시지 수신
3. 연결 종료 처리

### 에러 처리 테스트
1. 잘못된 요청 전송
2. 서버 다운 상황 처리
3. 네트워크 오류 처리

## 9. 개발 도구

### 추천 라이브러리
- **UI Framework**: Bootstrap 5 (CDN)
- **Icons**: Font Awesome (CDN)
- **HTTP Client**: Fetch API (내장)
- **SSE**: EventSource API (내장)

### 디버깅 도구
- Chrome DevTools Network 탭
- Postman/Insomnia (API 테스트)
- Browser Console (JavaScript 디버깅)

## 10. 배포 시 고려사항

### CORS 설정
프로덕션 환경에서는 특정 도메인만 허용하도록 설정:
```python
CORS_ORIGINS = ["https://your-domain.com"]
```

### HTTPS 적용
프로덕션 환경에서는 HTTPS 사용 필수

### 환경변수
- `API_HOST`: API 서버 호스트
- `API_PORT`: API 서버 포트
- `API_KEY`: API 인증 키 (선택적)

## 참고사항
- 모든 API는 JSON 형식으로 통신
- 타임스탬프는 ISO 8601 형식 사용
- UTF-8 인코딩 사용 (한글 지원)
- 세션 타임아웃: 3600초 (1시간)