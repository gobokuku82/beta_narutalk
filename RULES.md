# Medical Multi-Agent System Development Rules
## 의료/제약 도메인 멀티에이전트 시스템 개발 규칙

### 🎯 **프로젝트 개요**
의료/제약 영업 지원을 위한 AI 멀티에이전트 시스템
- **Framework**: LangGraph 0.6.7 + langgraph-supervisor 0.0.29
- **LLM**: OpenAI GPT-4o
- **Backend**: FastAPI + SQLAlchemy Core(2.x)
- **Frontend**: React (Create React App)
- **Database**: SQLite / chroma db ( ./database/)

---

## 📋 **Core Development Rules**

### 1. **Architecture Rules**

#### 1.1 Supervisor Pattern (필수)
```python
# ✅ GOOD: langgraph-supervisor 라이브러리 사용
from langgraph_supervisor import create_supervisor, create_handoff_tool

# ❌ BAD: 커스텀 supervisor 구현
class CustomSupervisor:  # 지양
    pass
```

#### 1.2 Context Engineering (핵심)
```python
# ✅ GOOD: 에이전트별 컨텍스트 최적화
context = context_manager.get_agent_specific_context(agent_name, full_context)

# ❌ BAD: 전체 컨텍스트 전달
agent.execute(full_context)  # 비효율적
```

#### 1.3 State Management
```python
# ✅ GOOD: Custom Reducer 사용
messages: Annotated[List[Any], add_messages]
data_sources: Annotated[List[str], merge_data_sources]

# ❌ BAD: 수동 상태 관리
state["messages"] = state["messages"] + new_messages  # 지양
```

---
## 🔧 **Technical Rules**

### 3. **Code Standards**

#### 3.1 Async First
```python
# ✅ GOOD: 모든 I/O 작업은 async
async def fetch_data():
    result = await db.query()
    return result

# ❌ BAD: 동기 I/O
def fetch_data():
    result = db.query()  # 블로킹
    return result
```

#### 3.2 Error Handling
```python
# ✅ GOOD: 구체적 에러 처리
try:
    result = await agent.execute(task)
except TimeoutError:
    result = await fallback_agent.execute(simplified_task)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    return error_response(e)

# ❌ BAD: 포괄적 예외 처리
try:
    result = await agent.execute(task)
except:  # 너무 포괄적
    pass
```

#### 3.3 Type Hints (필수)
```python
# ✅ GOOD: 명시적 타입 힌트
async def analyze_intent(
    query: str,
    context: Dict[str, Any]
) -> IntentAnalysisState:
    pass

# ❌ BAD: 타입 힌트 없음
async def analyze_intent(query, context):  # 타입 불명확
    pass
```

---

## 🚀 **Agent Development Rules**

### 4. **Agent Implementation Standards**

#### 4.1 Agent Structure
```python
class BaseAgent:
    """모든 에이전트는 이 구조를 따라야 함"""
    
    def __init__(self, llm_provider: str = "openai"):
        self.llm = self._init_llm(llm_provider)
        self.tools = self._init_tools()
        self.context_manager = ContextManager()
    
    async def execute(
        self, 
        task: Dict[str, Any],
        context: MedicalContext
    ) -> AgentResult:
        # 1. Context 최적화
        optimized_context = self._optimize_context(context)
        
        # 2. Tool 실행
        result = await self._run_tools(task, optimized_context)
        
        # 3. 결과 검증
        validated_result = await self._validate(result)
        
        return validated_result
```

#### 4.2 Tool Creation Rules
```python
# ✅ GOOD: 명확한 도구 정의
def create_sql_query_tool() -> Tool:
    return Tool(
        name="sql_query",
        description="정형 DB에서 SQL 쿼리 실행",  # 한국어 OK
        func=execute_sql_query,
        args_schema=SQLQuerySchema  # Pydantic 스키마
    )

# ❌ BAD: 모호한 도구
def create_tool():
    return Tool(name="tool", func=lambda x: x)  # 불명확
```

#### 4.3 Agent Communication
```python
# ✅ GOOD: Handoff tool 사용
handoff_tool = create_handoff_tool(
    agent_name="data_analysis_expert",
    description="데이터 분석 전문가에게 위임"
)

# ❌ BAD: 직접 호출
data_agent.execute()  # 지양, supervisor 통해야 함
```

---

## 💾 **Database Rules**

### 5. **Data Management**

#### 5.1 정형/비정형 데이터 구분
```python
# 정형 데이터 → PostgreSQL
STRUCTURED_DATA = [
    "직원정보",
    "거래처정보", 
    "매출데이터",
    "방문기록"
]

# 비정형 데이터 → MongoDB
UNSTRUCTURED_DATA = [
    "보고서본문",
    "상담내용",
    "메모",
    "첨부파일"
]
```

#### 5.2 복잡한 칼럼 처리
```python
# 복잡한 칼럼은 메타데이터 관리
COMPLEX_COLUMNS = {
    "product_mix": {
        "type": "json",
        "structure": {
            "product_id": "string",
            "quantity": "integer",
            "unit_price": "decimal"
        },
        "aggregation": ["sum", "avg"],
        "description": "제품 구성 정보"
    }
}
```

#### 5.3 트랜잭션 관리
```python
# ✅ GOOD: 트랜잭션 보장
async with db.transaction():
    await db.save_report(report)
    await db.update_status(status)
    await db.log_activity(activity)

# ❌ BAD: 개별 저장
await db.save_report(report)  # 실패 시 불일치 가능
await db.update_status(status)
```

---

## 📡 **API Integration Rules**

### 6. **External API Management**

#### 6.1 API Key 관리
```python
# .env 파일 사용 (절대 하드코딩 금지)
NAVER_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
HIRA_API_KEY=your_key_here

# ❌ NEVER: 코드에 직접 입력
api_key = "sk-xxxxx"  # 절대 금지
```

#### 6.2 Rate Limiting
```python
# API 호출 제한 관리
RATE_LIMITS = {
    "naver_api": {"calls": 1000, "period": "day"},
    "google_api": {"calls": 100, "period": "minute"},
    "hira_api": {"calls": 50, "period": "hour"}
}

# Rate limiter 적용
@rate_limit(max_calls=100, period=60)
async def call_external_api():
    pass
```

#### 6.3 Retry Strategy
```python
# 재시도 전략
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def api_call_with_retry():
    pass
```

---

## 🔍 **Debugging Rules**

### 7. **Logging & Monitoring**

#### 7.1 Structured Logging
```python
import structlog

logger = structlog.get_logger()

# ✅ GOOD: 구조화된 로깅
logger.info(
    "agent_execution",
    agent="data_analysis",
    task_id="task_123",
    duration=1.5,
    status="success"
)

# ❌ BAD: 비구조화 로깅
print(f"Agent executed: {result}")  # 지양
```

#### 7.2 Performance Tracking
```python
# 실행 시간 추적
from time import perf_counter

async def track_performance(func):
    start = perf_counter()
    result = await func()
    duration = perf_counter() - start
    
    metrics.record(
        name=func.__name__,
        duration=duration,
        timestamp=datetime.now()
    )
    return result
```

#### 7.3 Debug Mode
```python
# VS Code Claude Desktop 디버깅용
if os.getenv("DEBUG_MODE") == "true":
    logger.setLevel("DEBUG")
    
    # 상세 컨텍스트 출력
    logger.debug("context", context=context.dict())
    
    # 중간 결과 저장
    with open("debug_output.json", "w") as f:
        json.dump(state, f, indent=2)
```

---

## 🎨 **VS Code Claude Desktop Settings**

### 9. **Development Environment**

#### 9.1 Recommended Extensions
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "tamasfe.even-better-toml",
    "redhat.vscode-yaml"
  ]
}
```

---

## 🚨 **Critical Rules (절대 규칙)**

### 10. **Must Follow**

3. **API Key 하드코딩 금지**
4. **동기 I/O 사용 금지**
5. **타입 힌트 필수**
6. **에러 처리 필수**
7. **트랜잭션 보장**
8. **Context Engineering 적용**
9. **langgraph-supervisor 패턴 사용**

---

## 📝 **Commit Convention**

```bash
# Feature
feat: DataAnalysisAgent SQL 쿼리 기능 추가

# Fix
fix: 규정 검토 에이전트 타임아웃 문제 해결

# Refactor
refactor: Context Manager 최적화

# Docs
docs: API 문서 업데이트

# Test
test: Compliance validation 테스트 추가
```

---

## 🔄 **Development Workflow**

1. **기능 구현 전 RULES.md 확인**
2. **Context Engineering 설계**
3. **에이전트 구현**
4. **단위 테스트 작성**
5. **통합 테스트**
6. **규정 준수 검증**
7. **문서화**
8. **코드 리뷰**
9. **배포**

---

## 📞 **Support & Resources**

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **langgraph-supervisor**: https://github.com/langchain-ai/langgraph-supervisor-py
- **Medical Regulations**: 내부 규정 문서 참조
- **API Docs**: /docs/api/README.md

---

**Last Updated**: 2025-09-16
**Version**: 1.0.0
**Author**: Medical AI Team
