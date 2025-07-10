# 🚀 **LangGraph 전환 가이드**

## 📋 **현재 시스템 → LangGraph 전환 계획**

### **1. 의존성 추가 필요**

```bash
# requirements.txt에 추가
langgraph>=0.0.55
langchain-core>=0.1.45
```

### **2. 전환 단계**

#### **Phase 1: State 정의**
```python
# 현재: AgentContext 클래스
class AgentContext:
    def __init__(self, user_id, message, session_id, database_service, embedding_service, openai_client):
        ...

# 변경: TypedDict 기반 State
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    current_message: str
    current_agent: Optional[str]
    # ... 기타 필드들
```

#### **Phase 2: 노드 함수 전환**
```python
# 현재: BaseAgent.process() 메서드
class BaseAgent:
    async def process(self, context: AgentContext) -> AgentResult:
        ...

# 변경: 독립적인 노드 함수
def agent_node(state: AgentState) -> AgentState:
    try:
        # 처리 로직
        state["is_complete"] = True
        return state
    except Exception as e:
        state["error_message"] = str(e)
        return state
```

#### **Phase 3: 라우터 시스템 개선**
```python
# 현재: AgentRouterManager.route_message()
def route_message(self, message: str) -> str:
    confidences = {}
    for agent_name, agent in self.agents.items():
        confidences[agent_name] = agent.calculate_confidence(message)
    return max(confidences.keys(), key=lambda k: confidences[k])

# 변경: LangGraph 조건부 엣지
def route_after_router(state: AgentState) -> Literal["document_search", "document_draft", ...]:
    current_agent = state.get("current_agent")
    confidence = state.get("routing_confidence", 0.0)
    
    if confidence < 0.3:
        return "error"
    
    return current_agent
```

### **3. 마이그레이션 체크리스트**

#### **✅ 완료해야 할 작업**

1. **State 정의 완성**
   - [ ] AgentState TypedDict 정의
   - [ ] 메시지 어노테이션 추가
   - [ ] 상태 필드 매핑

2. **노드 함수 생성**
   - [ ] router_node() 구현
   - [ ] document_search_node() 구현
   - [ ] document_draft_node() 구현
   - [ ] performance_analysis_node() 구현
   - [ ] client_analysis_node() 구현
   - [ ] error_handler_node() 구현

3. **조건부 엣지 구현**
   - [ ] route_after_router() 함수
   - [ ] should_continue_or_end() 함수
   - [ ] 에러 핸들링 로직

4. **StateGraph 구성**
   - [ ] workflow = StateGraph(AgentState) 생성
   - [ ] 노드 추가: workflow.add_node()
   - [ ] 엣지 추가: workflow.add_edge()
   - [ ] 조건부 엣지: workflow.add_conditional_edges()
   - [ ] 워크플로우 컴파일: workflow.compile()

5. **API 엔드포인트 수정**
   - [ ] NaruTalkWorkflow 클래스 통합
   - [ ] async/await 패턴 적용
   - [ ] 응답 형식 변경

### **4. 파일별 수정 사항**

#### **`backend/app/services/langgraph_service.py` (신규)**
```python
from .langgraph_structure import NaruTalkWorkflow

class LangGraphService:
    def __init__(self):
        self.workflow = NaruTalkWorkflow()
    
    async def process_message(self, message: str, user_id: str, session_id: str):
        return await self.workflow.process_message(message, user_id, session_id)
```

#### **`backend/app/api/v1/chat.py` 수정**
```python
# 현재
router_manager = AgentRouterManager(...)
result = await router_manager.process_message(...)

# 변경
langgraph_service = LangGraphService()
result = await langgraph_service.process_message(...)
```

#### **`backend/app/agents/` 디렉토리 구조 변경**
```
agents/
├── __init__.py
├── langgraph_structure.py      # 새로 생성
├── nodes/                      # 새로 생성
│   ├── __init__.py
│   ├── router_node.py
│   ├── document_search_node.py
│   ├── document_draft_node.py
│   ├── performance_analysis_node.py
│   ├── client_analysis_node.py
│   └── error_handler_node.py
├── edges/                      # 새로 생성
│   ├── __init__.py
│   ├── routing_edges.py
│   └── completion_edges.py
└── legacy/                     # 기존 구조 보관
    ├── base_agent.py
    ├── document_search/
    ├── document_draft/
    ├── performance_analysis/
    └── client_analysis/
```

### **5. 장점 및 개선사항**

#### **🎯 LangGraph 전환 후 장점**

1. **시각적 워크플로우**
   - 노드와 엣지로 명확한 플로우 표현
   - 디버깅 및 모니터링 용이

2. **강력한 상태 관리**
   - TypedDict로 타입 안전성 확보
   - 모든 노드에서 상태 공유

3. **유연한 라우팅**
   - 조건부 엣지로 복잡한 라우팅 가능
   - 에이전트 간 협업 구현 용이

4. **확장성**
   - 새로운 노드/엣지 쉽게 추가
   - 워크플로우 동적 수정 가능

5. **표준화**
   - LangChain 생태계와 완전 호환
   - 커뮤니티 도구 활용 가능

### **6. 실행 계획**

#### **Week 1: 기반 구조 구축**
- [ ] LangGraph 의존성 설치
- [ ] AgentState 정의 완성
- [ ] 기본 노드 함수 스켈레톤 생성

#### **Week 2: 노드 구현**
- [ ] router_node 완전 구현
- [ ] 4개 에이전트 노드 구현
- [ ] error_handler_node 구현

#### **Week 3: 엣지 및 통합**
- [ ] 조건부 엣지 함수 구현
- [ ] StateGraph 구성 완료
- [ ] API 엔드포인트 연결

#### **Week 4: 테스트 및 최적화**
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 수행
- [ ] 성능 최적화

### **7. 위험 요소 및 대응**

#### **⚠️ 주의사항**

1. **상태 크기 관리**
   - 큰 문서는 참조로 저장
   - 불필요한 상태 정리

2. **비동기 처리**
   - 모든 노드 함수에 async/await 적용
   - 데이터베이스 연결 풀 관리

3. **오류 처리**
   - 각 노드에서 예외 처리 필수
   - error_handler_node로 안전한 종료

4. **성능 고려**
   - 상태 복사 최소화
   - 메모리 사용량 모니터링

### **8. 테스트 전략**

```python
# 테스트 예시
async def test_langgraph_workflow():
    workflow = NaruTalkWorkflow()
    
    test_cases = [
        ("문서 찾아줘", "document_search"),
        ("보고서 작성해줘", "document_draft"),
        ("매출 분석해줘", "performance_analysis"),
        ("고객 분석해줘", "client_analysis")
    ]
    
    for message, expected_agent in test_cases:
        result = await workflow.process_message(message)
        assert result["current_agent"] == expected_agent
        assert result["is_complete"] == True
```

### **9. 롤백 계획**

- 기존 `AgentRouterManager` 시스템 유지
- 설정을 통한 LangGraph/Legacy 전환 가능
- 점진적 마이그레이션 지원

```python
# config.py
USE_LANGGRAPH = True  # False로 설정시 레거시 시스템 사용
```

---

## 🎯 **결론**

현재 커스텀 라우터 시스템을 **완전한 LangGraph 구조**로 전환하면:

1. **표준화된 워크플로우** 구현
2. **강력한 상태 관리** 확보  
3. **시각적 디버깅** 가능
4. **확장성 및 유지보수성** 향상

단계적 전환을 통해 안전하게 마이그레이션할 수 있습니다. 