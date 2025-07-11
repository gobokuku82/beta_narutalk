# 🔀 라우터 시스템 비교

## 현재 두 가지 라우터 옵션

### 1️⃣ 복잡한 LangGraph 라우터 (`/api/v1/langgraph/chat`)

**특징:**
- 25개 필드의 복잡한 State 구조 
- 노드/엣지 기반 워크플로우
- 상세한 메타데이터 추적
- LangChain 생태계 완전 호환

**장점:**
- 시각적 워크플로우 표현 가능
- 복잡한 조건부 라우팅
- 확장성 높음
- 강력한 상태 관리

**단점:**
- 구조가 복잡함 (520줄)
- 학습 곡선 높음
- 메모리 사용량 많음
- 관리가 어려움

**코드 복잡도:**
```python
# 25개 필드의 State 
class RouterState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    current_message: str
    current_agent: Optional[str]
    agent_switches: int
    routing_confidence: float
    confidence_scores: Dict[str, float]
    # ... 20개 더
```

---

### 2️⃣ 간단한 라우터 (`/api/v1/api/simple/chat`)

**특징:**
- 우선순위 기반 간단한 분류
- 최소한의 데이터 구조
- 빠른 처리 속도
- 직관적인 로직

**장점:**
- 코드가 간단함 (100줄)
- 이해하기 쉬움
- 빠른 응답 속도
- 관리가 편함

**단점:**
- 제한적인 라우팅 로직
- 확장성 낮음
- 메타데이터 제한적
- LangGraph 기능 미사용

**코드 간단함:**
```python
def _classify_intent(self, message: str) -> tuple[str, float]:
    """의도 분류 - 단순하고 명확한 규칙"""
    message_lower = message.lower()
    
    # 우선순위 기반 분류
    if any(word in message_lower for word in ["실적", "성과", "매출"]):
        return "performance", 0.9
    # ...
```

---

## 🎯 4개 에이전트 분리 기준

### 현재 분류 기준
```python
classification_rules = {
    "performance": ["실적", "성과", "매출", "수익", "kpi", "분석"],
    "client": ["거래처", "고객", "클라이언트", "파트너", "업체"], 
    "draft": ["작성", "만들어", "생성", "초안", "보고서", "제안서"],
    "search": ["기본값 - 문서 검색"]
}
```

### 분리 기준의 문제점
1. **키워드 중복**: "문서"가 검색/작성 둘 다 포함
2. **단순 매칭**: 복잡한 의도 파악 어려움
3. **우선순위 없음**: 여러 키워드 포함 시 충돌

### 개선된 분리 기준 (간단한 라우터)
1. **우선순위 기반**: 구체적인 것부터 매칭
2. **중복 제거**: 명확한 키워드 분리
3. **기본값 설정**: 애매한 경우 문서 검색

---

## 📊 성능 비교

| 항목 | LangGraph 라우터 | 간단한 라우터 |
|------|-----------------|---------------|
| **코드 줄 수** | 520줄 | 100줄 |
| **State 필드** | 25개 | 5개 |
| **메모리 사용** | 높음 | 낮음 |
| **응답 속도** | 보통 | 빠름 |
| **확장성** | 매우 높음 | 제한적 |
| **학습 곡선** | 가파름 | 완만함 |
| **관리 용이성** | 어려움 | 쉬움 |

---

## 🚀 권장 사항

### 간단한 라우터 추천 시나리오
- **프로토타입/MVP**: 빠른 개발이 필요한 경우
- **단순한 챗봇**: 기본적인 라우팅만 필요한 경우  
- **소규모 팀**: 관리 리소스가 제한적인 경우
- **빠른 응답**: 성능이 최우선인 경우

### LangGraph 라우터 추천 시나리오
- **복잡한 워크플로우**: 다단계 처리가 필요한 경우
- **확장성 중요**: 미래에 기능 확장 계획이 있는 경우
- **상세한 추적**: 워크플로우 분석이 필요한 경우
- **LangChain 활용**: 생태계 도구들을 사용하는 경우

---

## 🔧 사용 방법

### 간단한 라우터 사용
```javascript
// 프론트엔드에서
const response = await fetch('/api/v1/api/simple/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: "매출 분석해줘",
        user_id: "user123",
        session_id: "session456"
    })
});
```

### LangGraph 라우터 사용
```javascript
// 프론트엔드에서 (현재 기본값)
const response = await fetch('/api/v1/langgraph/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: "매출 분석해줘",
        user_id: "user123", 
        session_id: "session456"
    })
});
```

---

## 💡 결론

**현재 상황**: LangGraph 라우터가 과도하게 복잡함
**추천**: 간단한 라우터로 시작하여 필요에 따라 점진적 확장

**이유:**
1. 현재 4개 에이전트 분류는 간단한 키워드 매칭으로 충분
2. 복잡한 State 관리가 현재 요구사항에 과도함
3. 관리 부담을 줄이고 개발 속도 향상 가능

**다음 단계:**
1. 간단한 라우터로 전환
2. 실제 사용량과 요구사항 파악
3. 필요시 점진적으로 LangGraph 기능 추가 