# LangGraph Supervisor 0.0.29 매뉴얼 (for LangGraph 0.6.x)
> 파일명: `supervisor0029_manual.md`

본 문서는 **LangGraph 0.6.x**에서 사용하는 **`langgraph-supervisor` 0.0.29**의 개요, 설치, 빠른 시작, **API(함수·옵션·파라미터 전수)**, 모범 사례와 트러블슈팅을 정리합니다. (최신: `langgraph-supervisor 0.0.29`, 2025-07-28 릴리스 기준)

---

## 0) 개요
- **목적**: LangGraph로 **계층형(hierarchical)** 멀티에이전트 시스템을 쉽게 구축하기 위한 **슈퍼바이저 패턴** 제공.
- **핵심 역할**
  - 단일 **Supervisor(오케스트레이터)** 가 사용자 인터랙션을 담당하고
  - **Worker Agents** 간 **handoff(업무 이관)** 를 결정/실행
  - 메시지 이력(history) 구성 정책 제어(전부 포함 vs 마지막 메시지만 등)
  - (선택) 다계층 구조: **Supervisor of supervisors**

---

## 1) 버전 및 호환성
- **LangGraph**: 0.6.x (예: 0.6.7)
- **langgraph-supervisor**: **0.0.29** (2025-07-28)
- **Python**: **>= 3.10**

> 참고: LangGraph v1.0 알파 문서가 별도로 있으나, 본 매뉴얼은 **0.6.x 기반** 사용법을 다룹니다.

---

## 2) 설치
```bash
pip install langgraph langgraph-supervisor
# 필요에 따라 모델 커넥터 추가
pip install langchain-openai
```

---

## 3) 빠른 시작 (Quickstart)
```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

model = ChatOpenAI(model="gpt-4o")

# 예시 툴
def add(a: float, b: float) -> float: return a + b
def multiply(a: float, b: float) -> float: return a * b
def web_search(q: str) -> str: return f"search result for: {q}"

# 작업 에이전트 정의
math_agent = create_react_agent(model=model, tools=[add, multiply], name="math_expert",
                                prompt="You are a math expert. Always use one tool at a time.")
research_agent = create_react_agent(model=model, tools=[web_search], name="research_expert",
                                    prompt="You are a researcher with web search.")

# Supervisor 구성
workflow = create_supervisor(
    [research_agent, math_agent],
    model=model,
    prompt="You are a team supervisor managing research and math experts.",
    # 아래 '전체 API' 절에 모든 인자/옵션 정리
)

# 컴파일 및 실행
app = workflow.compile()
result = app.invoke({"messages": [{"role":"user","content":"2+2와 AI 뉴스 둘 다"}]})
```

---

## 4) 전체 API 레퍼런스 (함수·옵션 **전수**)

### 4.1 `create_supervisor(...) -> StateGraph`
**시그니처**
```python
create_supervisor(
    agents: list[Pregel],
    *,
    model: LanguageModelLike,
    tools: list[BaseTool | Callable] | ToolNode | None = None,
    prompt: Prompt | None = None,
    response_format: Optional[Union[StructuredResponseSchema, tuple[str, StructuredResponseSchema]]] = None,
    pre_model_hook: Optional[RunnableLike] = None,
    post_model_hook: Optional[RunnableLike] = None,
    parallel_tool_calls: bool = False,
    state_schema: StateSchemaType | None = None,
    config_schema: Type[Any] | None = None,
    output_mode: OutputMode = "last_message",
    add_handoff_messages: bool = True,
    handoff_tool_prefix: Optional[str] = None,
    add_handoff_back_messages: Optional[bool] = None,
    supervisor_name: str = "supervisor",
    include_agent_name: AgentNameMode | None = None,
) -> StateGraph
```

**파라미터 설명 (누락 없음)**  
- `agents`: 감독할 에이전트 리스트. **LangGraph `CompiledStateGraph`**, Functional API `workflow`, 기타 `Pregel` 객체 가능.  
- `model`: 슈퍼바이저에 사용할 LLM. (예: `ChatOpenAI(...)`)
- `tools`: 슈퍼바이저가 직접 호출할 **도구**. `BaseTool`/`Callable`/`ToolNode`/`None` 지원.
- `prompt`: 슈퍼바이저용 프롬프트. 문자열/SystemMessage/Callable/Runnable 가능. Callable/Runnable을 주면 **그래프 상태를 입력으로 받아 LLM 입력을 생성**.
- `response_format`: **최종 슈퍼바이저 출력의 스키마**. OpenAI function/JSON Schema/TypedDict/Pydantic, 또는 `(prompt, schema)` 튜플. 이 옵션 사용 시 **모델이 `with_structured_output`** 을 지원해야 하며, 상태 스키마에 `structured_response` 키가 있어야 함(예: `AgentStateWithStructuredResponse` 사용).
- `pre_model_hook`: **LLM 호출 전** 추가 노드. **메시지 트리밍/요약/정합화** 등. 반환 시 아래 형식 중 **최소 하나** 제공해야 함:
  - `{"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), ...]}` (상태의 `messages`를 **전체 교체**)
  - `{"llm_input_messages": [...]}` (LLM 입력만 교체, 상태 `messages`는 그대로)
  - 그 외 전달할 상태 키 포함 가능
- `post_model_hook`: **LLM 호출 후** 추가 노드. **HITL(인간검증), 검증/밸리데이션, 가드레일** 등에 활용. (`langgraph-prebuilt>=0.2.0` 필요)
- `parallel_tool_calls`: **도구 병렬 호출** 허용 여부(현재 **OpenAI/Anthropic** 지원). 여러 에이전트로 **동시 handoff** 가능.
- `state_schema`: 슈퍼바이저 그래프의 상태 스키마.
- `config_schema`: 구성 파라미터의 스키마(예: `supervisor.config_specs` 노출용).
- `output_mode`: 워커 출력의 **히스토리 반영 방식**.  
  - `"full_history"`: 워커의 전체 메시지 포함  
  - `"last_message"`: 워커의 마지막 메시지만 포함(기본)
- `add_handoff_messages`: **handoff 발생 시** (AIMessage, ToolMessage) 페어를 히스토리에 추가할지 여부(기본 `True`).
- `handoff_tool_prefix`: 자동 생성되는 handoff 도구 이름 접두사(예: `"delegate_to_"`, 결과적으로 `delegate_to_<agent_name>`).
- `add_handoff_back_messages`: 슈퍼바이저로 **복귀**할 때도 handoff 메시지 페어를 추가할지.
- `supervisor_name`: 슈퍼바이저 노드 이름(기본 `"supervisor"`).
- `include_agent_name`: 워커 **이름 노출 방식**.  
  - `None`: LLM 제공자의 AI message `name` 속성 지원에 의존(현재 OpenAI만)  
  - `"inline"`: **XML 스타일 태그**로 이름을 컨텐츠에 인라인 삽입

**반환**: `StateGraph` (→ `.compile(...)` 호출 필요)

---

### 4.2 `create_handoff_tool(...) -> BaseTool`
**시그니처**
```python
create_handoff_tool(
    *,
    agent_name: str,
    name: str | None = None,
    description: str | None = None,
    add_handoff_messages: bool = True,
) -> BaseTool
```
**설명**  
- 지정한 `agent_name`으로 **제어 이관**(handoff)하는 도구를 생성.  
- `name`/`description` 커스터마이즈 가능(미지정 시 기본 네이밍/설명).  
- `add_handoff_messages=False` 로 이관 메시지 기록 생략 가능.

---

### 4.3 `create_forward_message_tool(supervisor_name: str = "supervisor") -> BaseTool`
**설명**  
- 워커 에이전트의 **마지막 메시지**를 **그대로 최종 출력으로 전달**하는 포워딩 도구(`forward_message`) 생성.  
- 슈퍼바이저의 요약/재서술 없이 워커 출력을 직통으로 넘겨 **토큰 절약**/의미 왜곡 방지.

---

## 5) 컴파일 옵션: 체크포인터/스토어
```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

checkpointer = InMemorySaver()
store = InMemoryStore()

app = workflow.compile(
    checkpointer=checkpointer,  # 단기 메모리(상태 스냅샷)
    store=store,                # 장기 메모리(키-값/벡터 등)
)
```
- **checkpointer**: 세션 상태 스냅샷(단기 메모리). 재시작/타임트래블/내결함성.
- **store**: 장기 메모리(사용자 지식/선호/지속 컨텍스트).

> 운영환경에서는 SQLite 외 Postgres/Redis Saver, 외부 스토어 등으로 교체 권장.

---

## 6) 고급 구성 패턴
- **다계층(Hierarchical)**: 여러 하위 팀(supervisor + agents)을 만들어 **상위 supervisor**가 관리.
- **메시지 이력 정책**: `output_mode`, `add_handoff_messages`, `add_handoff_back_messages`로 기록 볼륨 제어.
- **프롬프트 전략**: supervisor 프롬프트에 각 에이전트 역할/능력을 명시(에이전트명은 **능력 드러내는 네이밍**).
- **커스텀 handoff 도구**: 인자(예: `task_description`)를 추가해 다음 에이전트 동작을 더 구체화.
- **전처리/후처리 훅**: `pre_model_hook`(히스토리 트리밍/요약), `post_model_hook`(밸리데이션/가드레일/HITL).

---

## 7) 베스트 프랙티스
1. **에이전트 역할을 좁고 명확하게**: tool 과다/역할 중복 지양.  
2. **이름 규약**: `snake_case` + 역할이 드러나게(`math_expert`, `retrieval_agent`).  
3. **Handoff 최소화**: 불필요한 이관 방지(토큰/비용/지연 감소).  
4. **히스토리 최적화**: 긴 히스토리는 `pre_model_hook`에서 요약/트리밍.  
5. **병렬 도구 호출**은 신중히: LLM/벤더별 지원 범위 확인 후 활성화.  
6. **메모리 전략 분리**: checkpointer(단기) vs store(장기) 목적 분리.  
7. **관찰가능성**: 각 노드 출력 로그, 선택 문서, 이관 경로를 추적/로깅.

---

## 8) 트러블슈팅
- **메시지 폭증**: `output_mode="last_message"`, handoff 메시지 비활성화, `pre_model_hook`로 트리밍.  
- **이관 오판**: supervisor 프롬프트에 각 에이전트 **역할/툴/경계조건**을 명시. handoff 도구 설명을 충실히 작성.  
- **병렬 호출 미동작**: `parallel_tool_calls=True` + 지원 모델(OpenAI/Anthropic) 확인.  
- **이름 충돌**: 에이전트 이름과 handoff 도구 이름 유일성 보장.  
- **구조화 응답 실패**: `response_format` 사용 시 모델이 `with_structured_output` 지원하는지, 상태 스키마에 `structured_response` 키가 있는지 확인.

---

## 9) 보안/거버넌스 체크리스트
- **툴 안전장치**: 외부 호출 도구는 입력 검증/타임아웃/레이트리밋.  
- **감사 로깅**: handoff 발생 지점, 선택된 에이전트, 최종 응답 근거 문서(출처) 기록.  
- **PII/규정 준수**: 저장소(store/checkpointer) 내 개인정보 취급 정책 명문화.

---

## 10) 최소 예제 (Functional API 혼합)
```python
from langgraph.func import entrypoint, task
from langgraph.graph import add_messages
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o")

@task
def generate_joke(messages):
    system = {"role":"system","content":"Write a short joke"}
    return model.invoke([system] + messages)

@entrypoint()
def joke_agent(state):
    msg = generate_joke(state["messages"]).result()
    return {"messages": add_messages(state["messages"], [msg])}

def web_search(q:str)->str: return "top news about AI ..."  # 예시

research_agent = create_react_agent(model=model, tools=[web_search], name="research_expert")

workflow = create_supervisor(
    [research_agent, joke_agent],
    model=model,
    prompt="Use research_expert for news; use joke_agent for humor."
)

app = workflow.compile()
out = app.invoke({"messages":[{"role":"user","content":"하나만의 농담과 AI 뉴스"}]})
```

---

## 11) 용어 요약
- **Supervisor**: 사용자 인터랙션과 에이전트 라우팅을 총괄하는 LLM 노드.
- **Handoff**: 한 에이전트에서 다른 에이전트로 제어를 넘김.
- **Forward Message**: 워커의 마지막 응답을 슈퍼바이저가 가공 없이 그대로 출력.
- **Checkpointer/Store**: 단기/장기 메모리 계층.

---

## 12) 체크리스트(도입 전)
- 목표/도메인 정의 → 에이전트 역할 설계 → 툴 목록/권한 → 프롬프트/훅 설계 → 로깅/모니터링 → 비용/성능 SLO.

---

(끝)
