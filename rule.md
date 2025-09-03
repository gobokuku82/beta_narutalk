# 제약회사 영업사원 AI 어시스턴트 개발 규칙

## 1. 프로젝트 개요
제약회사 영업사원을 위한 AI 기반 업무 지원 시스템
- **목표**: 영업 효율성 향상 및 규정 준수 지원
- **아키텍처**: LangGraph Supervisor Pattern + Command Pattern
- **버전**: LangGraph 0.6.6 (2025년 8월 기준)

## 2. 기술 스택 및 버전

### 핵심 기술
- **Python**: 3.12
- **LangGraph**: 0.6.6 (최신 안정 버전)
- **LangChain**: 0.3.0
- **langgraph-supervisor**: 최신 버전 사용
- **FastAPI**: 0.115.0
- **React**: 18.3.1 + TypeScript

### ⚠️ 버전 주의사항
```
중요: Claude의 지식 기준은 2024년 LangGraph 0.2.x 버전입니다.
실제 프로젝트는 2025년 8월 LangGraph 0.6.6을 사용합니다.
문법과 패턴이 크게 변경되었으므로 아래 규칙을 반드시 따르세요.
```

## 3. LangGraph 0.6.6 구현 규칙

### 3.1 StateGraph 패턴 (필수)
```python
from typing_extensions import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# ✅ 올바른 State 정의 (0.6.6)
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_agent: str
    context: dict
    tools_output: list

# ✅ StateGraph 초기화 (0.6.6)
workflow = StateGraph(AgentState)

# ❌ 사용하지 마세요 (0.2.x 구문)
# workflow = MessageGraph()  # 더 이상 사용 안 함
```

### 3.2 노드 추가 패턴
```python
# ✅ 올바른 노드 추가 (0.6.6)
def agent_node(state: AgentState) -> AgentState:
    # 노드 로직
    return {"messages": state["messages"] + [response]}

workflow.add_node("agent_name", agent_node)

# ❌ 사용하지 마세요 (구버전)
# workflow.add_node("agent", agent, input=..., output=...)
```

### 3.3 엣지 추가 및 컴파일
```python
# ✅ 올바른 엣지 추가 (0.6.6)
workflow.add_edge(START, "supervisor")
workflow.add_conditional_edges(
    "supervisor",
    route_to_agent,
    {
        "info_retrieval": "info_retrieval_agent",
        "doc_generation": "doc_generation_agent",
        "compliance": "compliance_agent",
        "analytics": "analytics_agent",
        "FINISH": END
    }
)

# ✅ 컴파일 (0.6.6)
app = workflow.compile()

# ❌ config_schema 사용 금지 (deprecated in 0.6.0)
# app = workflow.compile(config_schema=...)  # 사용 안 함
# ✅ context_schema 사용
app = workflow.compile(context_schema=MyContextSchema)
```

## 4. Supervisor 패턴 구현

### 4.1 Supervisor Agent
```python
from langgraph_supervisor import create_supervisor

class SupervisorAgent:
    """중앙 오케스트레이터 - 모든 에이전트 조정"""
    
    def __init__(self):
        self.agents = {
            "info_retrieval": InfoRetrievalAgent(),
            "doc_generation": DocumentGenerationAgent(),
            "compliance": ComplianceCheckAgent(),
            "analytics": AnalyticsAgent()
        }
    
    async def route(self, state: AgentState) -> str:
        """Command Pattern 기반 동적 라우팅"""
        # 사용자 의도 분석
        intent = await self.analyze_intent(state["messages"][-1])
        
        # 적절한 에이전트 선택
        return self.command_router.route(intent)
```

### 4.2 Command Pattern Router
```python
class CommandRouter:
    """동적 라우팅을 위한 Command Pattern 구현"""
    
    commands = {
        "search_drug_info": "info_retrieval",
        "create_proposal": "doc_generation",
        "check_compliance": "compliance",
        "analyze_sales": "analytics"
    }
    
    def route(self, intent: str) -> str:
        return self.commands.get(intent, "supervisor")
```

## 5. 4개 전문 에이전트 상세 명세

### 5.1 Information Retrieval Agent (정보검색)
**역할**: 의약품 정보 및 학술자료 검색
```python
class InfoRetrievalAgent:
    tools = [
        "vector_search",      # ChromaDB/Pinecone 검색
        "drug_database",      # 의약품 DB 조회
        "literature_search",  # 학술 논문 검색
        "fda_kfda_search"    # 규제기관 정보
    ]
    
    capabilities = [
        "제품 효능/부작용 정보 검색",
        "경쟁 제품 비교 분석",
        "최신 임상시험 결과 조회",
        "처방 가이드라인 제공"
    ]
```

### 5.2 Document Generation Agent (문서자동생성)
**역할**: 영업 문서 및 보고서 자동 생성
```python
class DocumentGenerationAgent:
    tools = [
        "template_engine",    # 문서 템플릿 엔진
        "markdown_generator", # 마크다운 생성
        "pdf_creator",       # PDF 변환
        "email_composer"     # 이메일 작성
    ]
    
    capabilities = [
        "영업 제안서 작성",
        "병원별 맞춤 프레젠테이션",
        "주간/월간 영업 보고서",
        "학술대회 요약 자료"
    ]
```

### 5.3 Compliance Check Agent (규정위반검색)
**역할**: 약사법 및 규정 준수 검증
```python
class ComplianceCheckAgent:
    tools = [
        "regulation_db",      # 규정 데이터베이스
        "risk_analyzer",      # 리스크 분석
        "audit_logger",       # 감사 로그
        "alert_system"        # 경고 시스템
    ]
    
    capabilities = [
        "KGSP 규정 준수 체크",
        "리베이트 위험도 평가",
        "프로모션 자료 사전 검토",
        "공정거래 규정 확인"
    ]
```

### 5.4 Analytics Agent (실적 및 거래처분석)
**역할**: 판매 데이터 분석 및 인사이트 제공
```python
class AnalyticsAgent:
    tools = [
        "sales_analyzer",     # 판매 분석
        "customer_profiler",  # 거래처 프로파일링
        "trend_predictor",    # 트렌드 예측
        "dashboard_builder"   # 대시보드 생성
    ]
    
    capabilities = [
        "거래처별 판매 실적 분석",
        "처방 패턴 분석",
        "목표 달성률 모니터링",
        "경쟁사 시장 점유율 비교"
    ]
```

## 6. 도구(Tools) 구현 규칙

### 6.1 Tool Decorator 패턴
```python
from langchain.tools import tool

@tool
def search_drug_info(query: str) -> str:
    """의약품 정보 검색 도구"""
    # 구현 로직
    return result

# ✅ 0.6.6에서는 tool decorator 사용
# ❌ BaseTool 상속 패턴은 가급적 피하기
```

### 6.2 Tool 등록
```python
# ✅ 각 에이전트별 도구 세트 정의
agent_tools = {
    "info_retrieval": [search_drug_info, search_literature],
    "doc_generation": [create_document, generate_report],
    "compliance": [check_regulation, analyze_risk],
    "analytics": [analyze_sales, predict_trend]
}
```

## 7. State Management

### 7.1 State Reducer 패턴
```python
from typing import Annotated

def merge_lists(a: list, b: list) -> list:
    """리스트 병합 reducer"""
    return a + b

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # 메시지 누적
    tools_output: Annotated[list, merge_lists]  # 도구 출력 누적
    current_agent: str  # 현재 활성 에이전트
    context: dict  # 세션 컨텍스트
```

### 7.2 State 업데이트 규칙
```python
# ✅ 부분 업데이트 (권장)
return {"messages": [new_message], "current_agent": "analytics"}

# ❌ 전체 State 반환 (비효율적)
return state  # 전체 state 반환은 피하기
```

## 8. 비동기 처리

### 8.1 Async/Await 패턴
```python
# ✅ 비동기 노드 함수
async def async_agent_node(state: AgentState) -> AgentState:
    result = await external_api_call()
    return {"messages": [result]}

# 비동기 실행
result = await app.ainvoke({"messages": [user_input]})
```

## 9. 에러 처리 및 로깅

### 9.1 에러 처리 패턴
```python
from loguru import logger

async def safe_agent_node(state: AgentState) -> AgentState:
    try:
        # 에이전트 로직
        result = await process_request(state)
        return {"messages": [result]}
    except Exception as e:
        logger.error(f"Agent error: {e}")
        return {"messages": [f"오류가 발생했습니다: {str(e)}"]}
```

## 10. 프로젝트 구조

```
beta_v001/
├── backend/
│   ├── agents/
│   │   ├── supervisor.py         # Supervisor 에이전트
│   │   ├── info_retrieval.py     # 정보검색 에이전트
│   │   ├── doc_generation.py     # 문서생성 에이전트
│   │   ├── compliance.py         # 규정검사 에이전트
│   │   └── analytics.py          # 분석 에이전트
│   ├── tools/
│   │   ├── vector_db.py          # 벡터 DB 도구
│   │   ├── document.py           # 문서 도구
│   │   ├── regulation.py         # 규정 도구
│   │   └── analysis.py           # 분석 도구
│   ├── workflows/
│   │   └── main_workflow.py      # 메인 워크플로우
│   ├── core/
│   │   ├── state.py              # State 정의
│   │   ├── router.py             # Command Router
│   │   └── config.py             # 설정
│   └── main.py                   # FastAPI 앱
├── frontend/
│   ├── src/
│   │   ├── components/           # React 컴포넌트
│   │   ├── services/             # API 서비스
│   │   └── stores/               # 상태 관리
│   └── package.json
├── requirements.txt               # Python 의존성
├── rule.md                       # 이 파일
└── README.md                     # 프로젝트 문서
```

## 11. 개발 체크리스트

- [ ] Python 3.12 환경 설정
- [ ] LangGraph 0.6.6 설치 확인
- [ ] StateGraph 패턴 사용 (MessageGraph X)
- [ ] context_schema 사용 (config_schema X)
- [ ] 4개 에이전트 구현 완료
- [ ] Supervisor 패턴 적용
- [ ] Command Router 구현
- [ ] Tool decorator 패턴 사용
- [ ] 비동기 처리 구현
- [ ] 에러 처리 및 로깅

## 12. 주의사항

1. **버전 호환성**: 반드시 LangGraph 0.6.6 문법 사용
2. **State Management**: TypedDict와 reducer 패턴 활용
3. **Tool 구현**: @tool decorator 우선 사용
4. **비동기 처리**: async/await 적극 활용
5. **에러 처리**: 모든 에이전트에 try-catch 구현

---

**작성일**: 2025년 9월
**버전**: 1.0.0
**대상**: 제약회사 영업사원 AI 어시스턴트 개발팀