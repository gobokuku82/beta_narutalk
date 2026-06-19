# 17. Functions → Agents → Tools → Data → I/O — 종단 매핑

> **참고 (프레임워크화 정리)**: 본 문서의 §1~§4는 원래 특정 도메인(마케팅) 기능 카탈로그를 예시로 종단 매핑을 설명했다. 프레임워크가 도메인-비종속으로 전환되면서 구체적 기능/에이전트/도구/데이터 카탈로그는 모두 제거되었고(도구 카탈로그는 현재 비어 있음 — `tools/{registry,base_tool,llm_tool}` 프레임워크만 존재), §1~§4의 표는 **구조 설명용 일반 예시(placeholder)**로 남겨둔다. 본 문서의 영속 가치는 §5 **Tool I/O 관리 메커니즘**(코드 계약)이다.

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 아키텍처 (10대) |
| 진행상태 | Active |
| 버전 | **v1.0** |
| 최종 수정일 | 2026-05-18 |
| 독자 | "기능 1개가 어디서 시작해 어디서 끝나는가" 한 흐름으로 보고 싶은 사람 |
| 자매 문서 | [14 System Agent Overview](14_system_agent_overview_v1.0.md) (Layer 관점) · [15 End-to-End Flow](15_end_to_end_flow_v1.0.md) (시간 축) · **본 문서 (계층 종단 축)** |
| 독자 비고 | §1~§4는 일반 예시(placeholder), §5 I/O 메커니즘이 코드 계약 |

---

## 0. 본 문서의 역할

> **5단계 종단 매핑** — 기능 → 에이전트 → 툴 → 데이터 → I/O 메커니즘 한 페이지.

다른 spec 은 한 단계만 다룸:
- 14 = Layer 책임 (Cognitive/Planning/Execution/Response)
- 15 = 시간축 sequence (query → 응답)
- 30 = Pydantic 데이터 모델

→ **본 문서는 5단계가 한 흐름으로 흐른다**. 신규 Tool 작성자가 진입점으로 사용.

### 진실 소스 / 참조 흐름

| 단계 | 진실 소스 (참조) |
|---|---|
| ① 기능 | (도메인 기능 카탈로그 — 일반 예시) |
| ② 기능 → 에이전트 | (에이전트 매핑 — 일반 예시) |
| ③ 에이전트 → 툴 | 실행 에이전트 확장 가이드 (Tool 카탈로그는 현재 비어 있음) |
| ④ 툴 → 데이터 | (Tool↔Data 매트릭스 — 일반 예시) |
| ⑤ I/O 메커니즘 | 코드 — [base_tool.py](../../backend/app/dream_agent/tools/base_tool.py) + [executor.py](../../backend/app/dream_agent/execution/executor.py) + [shared/helpers.py](../../backend/app/dream_agent/tools/shared/helpers.py) |

---

## 1. ① 기능 카탈로그 (일반 예시)

> 이 단계는 도메인별 기능 카탈로그가 들어가는 자리다. 프레임워크는 도메인-비종속이므로 구체적 기능 목록은 제거되었다. 아래는 **구조 설명용 일반 예시**일 뿐 — 실제 기능은 도입 도메인에서 정의한다.

### 1.1 화면 트리거 (일반 예시)

| ID | 화면 | 버튼/트리거 | 한 줄 |
|---|---|---|---|
| F-D1 | 대시보드 | "상세 분석 보기 →" | 지표 이상 알림 → 원인 분석 진입 |
| F-D2 | 대시보드 | HITL 승인 클릭 | 정기 리포트 발송 승인 |
| F-CH1 | 채팅 직접 | "리포트 만들어줘" | 리포트 종합 |

### 1.2 자동 트리거 분석 (일반 예시)

| ID | 모듈 | 트리거 | 한 줄 |
|---|---|---|---|
| F-A01 | 이상 감지 | 매일 자동 | 임계 초과 탐지 |
| F-A02 | 달성률 예측 | 매일 자동 | 선형 외삽 |
| F-A03 | 원인 분석 | 인사이트 박스 / 요청 | 규칙 트리 |

### 1.3 산출물 생성 (일반 예시)

| ID | 기능 | 한 줄 |
|---|---|---|
| F-G3 | 리포트 출력물 | 문서 렌더링 |

> 위 표는 placeholder. 실제 기능 수·내용은 도입 도메인이 채운다. MVP 진입 = 정의된 기능이 mock 으로 동작.

---

## 2. ② 기능 → 에이전트 매핑 (일반 예시)

> 이 단계는 기능을 처리할 에이전트(Team/Agent)에 매핑한다. 아래는 **구조 설명용 일반 예시**다.

### 2.1 호출 매트릭스 (일반 예시)

| 기능 ID | 호출 에이전트 | HITL 카테고리 |
|---|---|---|
| F-D1 / F-A01~A03 | **analysis** | 조회·자동 |
| F-D2 | analysis | 실행 전 승인 |
| F-CH1 / F-G3 | analysis + **report_text** | 생성 후 / 외부 발송 |

> HITL 카테고리 예시 = 조회·자동 / 생성 후 / 실행 전 / 외부 발송.

### 2.2 에이전트 구성 (일반 예시)

```
① chat_hub_agent              ← 진입점 (NL + 화면 버튼)
② collection_agent             ← raw 데이터 적재
③ preprocessing_agent          ← 데이터 정제
④ analysis_agent               ← 분석 모듈
⑤ report_agent                 ← 보고서/출력물
```

> 에이전트 수·구성은 도입 도메인이 정의한다. (위는 placeholder.)

---

## 3. ③ 에이전트 → 툴 분해 (일반 예시)

> **현재 도구 카탈로그는 비어 있다** — 프레임워크는 `tools/{registry,base_tool,llm_tool}` 만 제공하고, 구체적 Tool 은 도입 도메인이 추가한다. 아래는 **구조 설명용 일반 예시**다.

### 3.1 에이전트별 툴 수 (일반 예시)

| 에이전트 | 툴 수 (예시) | 비고 |
|---|---:|---|
| ① chat_hub | (Cognitive Stage 로직, 별도 툴 아님) | 진입 분류 |
| ② collection | N | raw 데이터 수집 |
| ③ preprocessing | N | 데이터 정제 |
| ④ analysis | N | 분석 모듈 |
| ⑤ report | N | 보고서/출력물 |

> 툴 수·구성은 도입 도메인이 정의한다.

### 3.2 Tool 체인 (일반 예시)

```
<collector> → <normalizer> → <preprocessor>
                                  ├──► <analyzer-a>
                                  └──► <analyzer-b>
                                            │
                                       <insight-tool>
                                            │
                                       <report-writer> ──► <summary-tool>
```

→ Tool 의 return dict 키가 다음 Tool 의 입력으로 자동 전파되는 체인 패턴 (§5 참조).

---

## 4. ④ 툴 → 데이터 매핑 (일반 예시)

> 이 단계는 Tool 이 읽는 데이터 source 를 매핑한다. 아래는 **구조 설명용 일반 예시**다.

### 4.1 데이터 source 종류

| 종류 | 위치 | Phase |
|---|---|---|
| **파일 source** | `data_layer/data_sources/file.py` (`FileDataSource`) | 도메인 등록 시 |
| **DB source** | `data_layer/data_sources/postgres.py` (`PostgresDataSource`, `dreamagent_data`) | `DATA_BACKEND=postgres` |

데이터 source 추상(`DataSource` ABC) 뒤에서 입력 인터페이스 동결 — 구현 교체해도 tool/frontend 변경 0.

### 4.2 데이터셋 → 사용 Tool 역방향 매핑 (일반 예시)

| 데이터셋 | 사용 Tool | 영향도 |
|---|---|---|
| `<dataset-A>.csv` ⭐⭐ | `<tool-1>`, `<tool-2>`, ... | **최대** — 변경 시 다수 Tool 영향 |
| `<dataset-B>.csv` ⭐ | `<tool-3>`, `<tool-4>` | analysis |
| `<dataset-C>.csv` | `<collector>`, `<analyzer>` | collection + analysis |

> 데이터셋·Tool 매핑은 도입 도메인이 채운다.

---

## 5. ⑤ Tool I/O 관리 메커니즘 ⭐ 본 문서 핵심

> 코드 진실 소스: [base_tool.py](../../backend/app/dream_agent/tools/base_tool.py), [executor.py](../../backend/app/dream_agent/execution/executor.py), [shared/helpers.py](../../backend/app/dream_agent/tools/shared/helpers.py).

### 5.1 BaseTool 계약

모든 Tool 은 다음 추상 클래스 구현:

```python
class BaseTool(ABC):
    def __init__(self, spec: ToolSpec): ...

    @abstractmethod
    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        """Tool 실제 수행. 반환 dict = TodoResult.data 로 저장."""
```

| 인자 | 의미 |
|---|---|
| `params` | Planner 가 지정한 `tool_params` + `_inject_prev_outputs` 자동 주입 결과 |
| `context` | `ExecutionContext(session_id, plan_id, client_id, user_id, language, previous_results, session_memory)` |
| 반환 | `dict[str, Any]` — `produces` YAML 선언 키 + 부가 정보. Tool 체인의 다음 단계로 자동 전파됨 |

상세 = 실행 에이전트 확장 가이드.

### 5.2 입력 자동 주입 — `_inject_prev_outputs` 룰

[`executor.py:_inject_prev_outputs`](../../backend/app/dream_agent/execution/executor.py) (line 201):

```python
def _inject_prev_outputs(params: dict, previous_results: dict[str, TodoResult]) -> dict:
    merged = dict(params)
    for r in previous_results.values():
        if r.status != TodoStatus.COMPLETED:
            continue
        if not isinstance(r.data, dict):
            continue
        for k, v in r.data.items():
            if k.startswith("_"):
                continue
            merged.setdefault(k, v)   # ← 핵심: setdefault
    return merged
```

**핵심 4 룰**:

| # | 룰 | 결과 |
|---|---|---|
| 1 | **`setdefault`** | 이미 `tool_params` 에 명시된 값이 있으면 절대 덮지 않음 → 사용자/Planner override 우선 |
| 2 | **`_` prefix 키 제외** | `_meta`, `_trace`, `_debug` 등 내부용 키는 전파 안 됨 |
| 3 | **COMPLETED 만 주입** | 실패한 Tool 의 data 는 무시 |
| 4 | **dict 만 주입** | data 가 dict 가 아니면 무시 |

### 5.3 명시 조회 — `find_in_previous`

자동 주입이 안 되는 경우 (예: 깊은 nested 키), Tool 내부에서 명시 조회:

[`shared/helpers.py:find_in_previous`](../../backend/app/dream_agent/tools/shared/helpers.py) (line 60):

```python
from app.dream_agent.tools.shared.helpers import find_in_previous

class MyTool(BaseTool):
    async def execute(self, params, context):
        # context.previous_results 에서 명시 조회
        normalized = find_in_previous(
            context.previous_results,
            "normalized_records"
        )
        if normalized is None:
            raise RuntimeError("no normalized_records in previous_results")
        ...
```

지원하는 결과 dict 구조 2 종:
- `previous_results[todo_id]["data"][key]`
- `previous_results[todo_id][key]` (flat)

### 5.4 출력 — `produces` 키 체이닝 원칙

Tool 의 return dict 키는 **다음 Tool 의 입력** 으로 자동 전파됨. 따라서 키 네이밍 통일이 중요.

**권장 체인 패턴**:

```
<collector>       → return {"raw_records": [...], "count": N, ...}
                              │
                              ▼ (자동 주입 — setdefault)
<normalizer>      → return {"normalized_records": [...], "count": N, "schema_version": "v1"}
                              │
                              ▼
<preprocessor>    → return {"cleaned_items": [...], "before_count": N, "after_count": M}
                              │
                              ▼
<analyzer-a>      → return {"distribution": {...}, ...}
<analyzer-b>      → return {"top_items": [...], ...}
                              │
                              ▼ (양쪽 모두 주입)
<insight-tool>    → return {"insights": [...], ...}
                              │
                              ▼
<report-writer>   → return {"report_text": "...", "length": N}
```

**원칙 3 가지**:

| # | 원칙 | 이유 |
|---|---|---|
| 1 | **produces 키 = 다음 Tool 의 params 키와 일치** | setdefault 자동 매칭 |
| 2 | **내부용은 `_` prefix** | `_trace`, `_debug`, `_meta` 등 전파 차단 |
| 3 | **큰 raw 데이터 (>100 항목) 는 파일 경로로** | LLM 토큰 폭증 + Checkpointer 직렬화 부담 |

### 5.5 실패 처리 — raise vs return error

| 방식 | 동작 | 권장 |
|---|---|---|
| `raise RuntimeError("msg")` | Executor 가 FAILED 로 잡음. `error` 필드에 메시지 | ⭐ 권장 |
| `return {"error": "msg"}` | Executor 가 FAILED 로 간주 (현재 코드 양쪽 지원) | 비권장 (혼재) |

실패 시:
- TodoResult `status=FAILED` + `data={}` + `error=str(e)`
- 다음 Phase 의 의존 Todo = depends_on 만족 못 함 → **자동 skip** 또는 halt
- spec §2.4: **no retry** (failed is final)

### 5.6 직렬화 / 재시작 복원

Tool.execute 의 return dict 는 결국:
1. `TodoResult.data` 에 저장
2. `AgentState` 에 누적
3. Postgres Checkpointer 가 pickle 직렬화

**금지 사항**:

| 객체 | 이유 |
|---|---|
| 파일 핸들 (`open()` 반환) | pickle 불가 |
| async generator | pickle 불가 |
| thread local 객체 | pickle 불가 |
| DB 연결 객체 | pickle 불가 |

**대안**:
- 파일은 **경로 (str) 만 저장**, 실 내용은 디스크
- 큰 dict 는 **요약만 data 에**, 상세는 별도 path

### 5.7 mock fallback (POC 단계)

[`agent_pool.py:is_tool_implemented`](../../backend/app/dream_agent/execution/agent_pool.py):

```python
if pool.is_tool_implemented(agent_name, tool_name):
    # 실제 Tool 클래스 실행
    tool_inst = pool.get_real_tool(tool_name)
    params = _inject_prev_outputs(todo.tool_params, previous_results)
    data = await tool_inst.execute(params, ctx)
    is_mock = False
elif pool.is_tool_stub(agent_name, tool_name):
    # mock_tools.mock_result() fallback
    data = mock_result(tool_name, todo.tool_params)
    is_mock = True
else:
    raise RuntimeError(...)
```

→ team_catalog.yaml 의 `status: stub` 인 Tool 은 `mock_tools.py:mock_result()` 가 그럴듯한 dict 반환. POC 시연 시 체인 통과 보장.

상세 = 실행 에이전트 확장 가이드.

---

## 6. 종단 예시 한 시나리오 (일반 예시)

> 사용자: **"<엔티티> <범주> 데이터 분석해줘"**

```
[① 기능] F-CH1 "분석 요청"
   │
   ▼
[② 에이전트] chat_hub_agent
   - LLM 의도 추출 → 분류
   - HITL 카테고리 = 조회 (자동 실행)
   │
   ▼
[② → 라우팅] analysis_agent
   │
   ▼
[③ Planner] 5 todos 생성 (DAG):
   t1: <collector>     (collection)
   t2: <normalizer>    (preprocessing)    depends_on=[t1]
   t3: <preprocessor>  (preprocessing)    depends_on=[t2]
   t4: <analyzer>      (analysis)         depends_on=[t3]
   t5: <report-writer> (report)           depends_on=[t4]
   │
   ▼
[④ 데이터 + ⑤ I/O] Executor 가 Phase 별 실행:

Phase 1: t1
   params = {entity: "<엔티티>", source: "<source>"}
   t1 = <collector>.execute(params, ctx)
   load_data("<dataset>.csv")
     [필터 → N건]
   return {"raw_records": [...N건...], "count": N, "source": "<source>"}

Phase 2: t2 (raw_records 자동 주입)
   params = {schema: "<schema>"}  ← Planner
            + raw_records ← setdefault 자동 주입
   t2 = <normalizer>.execute(...)
   return {"normalized_records": [...], "schema_version": "v1"}

Phase 3: t3
   t3 = <preprocessor>.execute(...)
   정제 + dedup
   return {"cleaned_items": [...], "before_count": N, "after_count": M}

Phase 4: t4
   t4 = <analyzer>.execute(...)
   return {"distribution": {"a": 65, "b": 20, "c": 15}}

Phase 5: t5
   t5 = <report-writer>.execute(...)
   LLM 호출 → markdown 작성
   return {"report_text": "...", "length": 1024}

[Response Layer]
   사용자 응답: "<엔티티> 데이터 N건 분석 결과 — ..."
```

5단계가 한 흐름. 각 단계 멈춰서 위 §1~§5 참조.

---

## 7. 신규 Tool 추가 — 종단 체크리스트

`X` 라는 신규 Tool 을 만들 때 모든 단계 점검:

| ① 기능 | 이 Tool 이 어느 기능 (F-*) 의 일부? | §1 표에 신규 행? |
|---|---|---|
| ② 에이전트 | 어느 에이전트 소속? | team_catalog.yaml 의 해당 agent.tools 배열에 추가 |
| ③ 툴 메타 | YAML 작성 (`tools/catalog/<cat>/<X>.yaml`) | name, parameters, produces, requires_approval |
| ③ 툴 구현 | `tools/<cat>/<X>.py` 작성 | class X(BaseTool) + async execute |
| ④ 데이터 | 어느 데이터셋의 어느 컬럼 쓰나? | Tool↔Data 매트릭스 행 추가 |
| ⑤ I/O | 이전 produces 키 무엇 받아 무엇 만드나? | YAML produces 명시 + 다음 Tool 호환 키 |
| 코드 status 마커 | docstring `Status: complete \| partial \| planned — 설명` | 코드 status 마커 컨벤션 |
| 테스트 | unit + integration + DC-10 (Status 3중 정합) | 테스트 스위트 |

상세 = 실행 에이전트 확장 가이드 (Step-by-Step).

---

## 8. 관련 spec

| 번호 | 제목 | 본 문서와의 관계 |
|---|---|---|
| [14](14_system_agent_overview_v1.0.md) | System Agent Overview | **Layer 관점** (Cognitive/Planning/Execution/Response) |
| [15](15_end_to_end_flow_v1.0.md) | End-to-End Flow | **시간 축** (한 사이클 sequence) |
| **17** (본 문서) | **Functions → I/O 종단** | **계층 축** (기능 → 에이전트 → 툴 → 데이터 → I/O) |
| [30](30_DATA_MODELS_v1.1.md) | Data Models | Pydantic — TodoResult, ExecutionResult |

---

## 9. 변경 정책

| 트리거 | 본 문서 갱신 |
|---|---|
| 신규 기능 추가 (화면 버튼 등) | §1 표 + §2 매핑 |
| 신규 에이전트 도입 | §2.2 에이전트 표 |
| 신규 Tool 구현 | §3.1 카운트 + §3.2 (체인 변경 시) |
| 신규 데이터 source / 데이터셋 | §4.2 역방향 매핑 |
| I/O 룰 변경 (BaseTool 계약 변경 등) | §5 |
| Tool 실패 정책 변경 | §5.5 |

---

## 변경 이력

> 프레임워크 추출(2026-06-19) 이전(마케팅 도메인 시기)의 상세 변경 이력은 git 히스토리를 참조하세요.
