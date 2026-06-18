# 32. Execution Agent Tools — 카테고리 정의 + 구현 현황 & 확장 가이드

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 데이터 (Execution Agent / Tools) |
| 진행상태 | Active |
| 버전 | **v1.2** |
| 최종 수정일 | 2026-05-31 |
| 독자 | Tool 을 추가·확장·교체하려는 개발자. 먼저 [14_system_agent_overview_v1.0.md](14_system_agent_overview_v1.0.md) 를 읽을 것 |
| 관련 명세 | `14_system_agent_overview_v1.0.md`, `31_execution_agent_function_list_v0.6.md`, `30_DATA_MODELS_v1.1.md`, **`33_tools_by_category/`** (카테고리별 tool 인벤토리) |

**목적**:
1. **카테고리 8개의 의도·경계·decision tree 박제** (§2.5, 7 본 + 1 보조 report) — tool 분류 단일 진실 소스.
2. **Tool input/output 계약 원칙 박제** (§2.7) — 옵션 C 진입점 typed.
3. 현재 `backend/app/dream_agent/tools/` 에 무엇이 **실제 구현** 되어 있고 무엇이 **Stub/Planned** 인지 단일 뷰로 제공.
4. 새로운 Tool 을 추가하는 **단계별 체크리스트** + 주의점 + anti-pattern 정리.

**v1.1 (2026-05-30) 추가 사항**:
- §2.5 카테고리 정의, §2.6 decision tree, §2.7 옵션 C 계약, §2.8 33/* 참조 (작업 ③ 박제).

**v1.2 (2026-05-31) 갱신 사항** (작업 ⑤·⑥·⑦):
- §2.5 카테고리 7 → 8 정합 (report 보조 행 #8 추가, line 14·20·70-83·87 + 33/README:3·22).
- §5 BaseTool ADR-022 정합 (helper-B `self.fetch` + client_id fail-fast + 90 tool).
- §6 YAML 메타카드 + _schema.yaml 8 카테고리 정합 + status 폐기.
- §7 구현 전수표 폐기 (33/* 가 진실 소스).
- §8 다이어그램 rewrite (2 경로: ads + review).
- §11.4 error handling raise 통일 박제 (90 tool 정합 확인).
- 후속 정합: ADR-022 amend (§4·§5), 30_DATA_MODELS:409, API_SPEC:834.

**v1.3 (2026-06-11) — 카테고리 2 신설 + 분석 사다리 tool** (라우팅·카테고리 상세는 [39 Query Categories & Routing](39_query_categories_and_routing_v1.0.md) 가 소유):
- **ToolCategory enum 9 → 11**: `qa`(질의응답) + `decision`(의사결정) 추가. (`models/enums.py`)
- **신규 tool**: `qa_responder`(qa, LLM) · `recommender`(decision, ml_model mock) · `diagnoser`·`forecaster`(analysis, LLM 분석 사다리 진단·예측) + `insight_extractor` 도메인무관化(추론). 전부 status=implemented, team_catalog `qa_agent`/`decision_agent`/analysis_agent 등재.
- **DEGRADE 해소**: diagnose/forecast/attribute 가 매핑 tool 없음(degrade)에서 실 분석 tool 로. → [37 v1.1](37_agent_language_pmal_v1.0.md)·[ADR-030](adr/ADR-030_query_category_routing_architecture.md).
- 결정: 카테고리 라우팅 + short-circuit(단일의도 한정)은 39·ADR-030. tool 분류 8 카테고리 표(§2.5)는 +qa·decision 으로 11(상세 39).

→ 32 v1.2 = 코드 (enum + base_tool + registry) + 33/* + ADR-022 + frontend ToolPalette + spec 와 *완전 정합*.

---

## 1. 실행 에이전트의 위치 (시스템 에이전트 내부에서)

```
Layer 3. Execution
 ├─ execution_stage.py         ── "오케스트레이터" (Phase loop)
 ├─ executor.py                ── "엔진" (build_phases, _run_single_todo, _inject_prev_outputs)
 ├─ agent_pool.py              ── "레지스트리" (Agent/Tool 메타 + Eager init)
 ├─ mock_tools.py              ── "Stub 응답기"
 └─ tools/  ←  실행 에이전트(Tool) 본체
     ├─ base_tool.py           ── 추상 기반 클래스
     ├─ registry.py            ── YAML 카탈로그 → 클래스 자동 import
     └─ <category>/<name>.py   ── 실제 구현
         + catalog/<category>/<name>.yaml
```

> **한 줄 요약**: **Tool = 하나의 책임을 수행하는 async 함수(class)** + **YAML 메타카드**. Planner 는 YAML 을 보고 선택하고, Executor 는 class 를 import 해서 실행한다.

---

## 2. 용어 정리

| 용어 | 의미 |
|------|------|
| **Team** | 팀 단위 묶음 (분석팀 / 크리에이티브팀). `planning/catalog/team_catalog.yaml` 의 최상위. |
| **Agent (실행 에이전트)** | Team 소속의 역할 단위 (collection_agent, preprocessing_agent, analysis_agent, report_agent, pdf_agent, image_creation_agent, video_creation_agent). Tool 들의 그룹. |
| **Tool** | 실제 실행 단위. `tools/<category>/<name>.py` 의 class. 하나의 Todo = 하나의 Tool 호출. |
| **ToolSpec** | Tool YAML 을 로드한 pydantic 모델. executor path, produces, parameters, 등. |
| **PlannedTodo** | Planner 가 생성한 Todo. tool_name + tool_params + depends_on. |
| **Phase** | DAG 에서 의존성이 같은 Todo 들의 묶음. Phase 내부는 asyncio.gather 병렬, Phase 간 순차. |

### Agent 와 Tool 의 관계

- Agent 는 **논리적 그룹핑**일 뿐 실제 코드 entity 가 아니다. Planner 가 "어느 Agent를 쓸까" 를 결정한 후, 그 Agent 에 속한 Tool 리스트에서 골라서 Todo 를 만든다.
- 따라서 **새 Tool 을 추가한다는 것**은:
  1. `tools/<category>/<name>.py` 구현
  2. `tools/catalog/<category>/<name>.yaml` 메타
  3. `planning/catalog/team_catalog.yaml` 해당 Agent 의 tools 배열에 추가
  - 이 3 가지를 **동시에** 해야 함.

---

## 2.5 카테고리 8 정의 (북극성)

> **잣대 단일 진실**. Tool 은 정확히 한 카테고리에 속한다. 모호하면 §2.6 decision tree.

| # | 카테고리 | 한 줄 의도 | 핵심 동사 | 출력 모양 |
|---|---|---|---|---|
| 1 | **collection** | raw 데이터를 외부 API / 내부 DB / 파일에서 *가져온다* | fetch, load, get | raw dict/list/DataFrame |
| 2 | **normalization** | raw 의 컬럼명·형식·단위·시간대를 *표준 schema 로 통일한다* (의미 변경 X) | unify, standardize, map | 표준 schema 의 DataFrame/dict |
| 3 | **cleaning** | 데이터 자체를 *정제한다* (결측·이상치·비즈니스 필터·검증·보정) | filter, validate, impute, correct | 정제된 DataFrame/dict |
| 4 | **preprocessing** | *자연어 텍스트* 의 불필요 요소를 제거 (리뷰·블로그 한정) | tokenize, strip, normalize_text | 정제된 텍스트/토큰 |
| 5 | **metrics** | *순수 계산* (어떤 출력이든 — scalar·list·dict·table 다 OK) | sum, count, avg, ratio, distribute | scalar 또는 구조화 dict |
| 6 | **comparison** | 두 metrics 를 *조합·비교* (MoM·delta·A/B·growth) | compare, delta, mom | 조합 결과 dict |
| 7 | **analysis** | LLM·ML·통계 기반 *추론* (감성·점수·키워드·예측) — 내부 3 sub: 일반/ML/LLM | infer, score, classify, recommend | 추론 결과 dict |
| 8 | **report** (보조) | 분석 결과를 사람이 읽는 *텍스트* 로 (요약·보고서) | summarize, narrate, format | 텍스트 (markdown) |

### 카테고리 외 (보조)

- **shared/** — helper. tool 이 아님. 여러 tool 공용 로직(예: `filter_active_orders`, `aggregate_ad_cost`, `safe_int`).
- **pdf·image_creation·video_creation** — planned/stub. 카테고리는 박제, 구현은 향후.
- **visualization** — **폐기** (2026-05-30 결정). 차트 그리기는 frontend 책임. backend tool 의 데이터 가공은 모두 **metrics**.

### 데이터 흐름 (선행 관계)

```
collection → normalization → cleaning → metrics → comparison
                                            ↘
                                              analysis (LLM/ML/통계)
preprocessing 는 자연어 라인 (collection → preprocessing → analysis)
```

---

## 2.6 Tool 분류 decision tree (모호할 때)

> tool 의 핵심 책임이 어디인지 위→아래 순서로 첫 yes 가 그 카테고리.

```
1. 자연어 텍스트 처리?       → preprocessing
2. raw 데이터 가져오기?       → collection
3. 컬럼·형식·단위·시간대 통일만? → normalization
4. 결측·이상치·필터·검증·보정?   → cleaning
5. 계산(scalar/list/table 무관)? → metrics
6. 두 metrics 조합·비교?       → comparison
7. LLM·ML·통계 추론?           → analysis
8. 차트 spec/그리기?            → frontend (backend tool 아님)
```

**상위 카테고리 우선** — 자연어면 *무조건* preprocessing, 다른 후보 무시.

### 끼워맞춤 anti-pattern (분리 신호)

다음은 한 tool 이 두 카테고리에 걸쳐 있다는 신호 — 의미 단위 분리 필요:

- **generic 엔진**: 한 tool 이 op+field 파라미터로 N 지표 동시 처리 (예: campaigns_aggregate K10~K13). → 의미 단위 N개로 분리 (1 tool = 1 지표).
- **helper wrapper**: tool 본체 = shared helper 1줄 호출만 (예: ad_cost_aggregator). → tool 폐기, helper 만 유지.
- **이름과 출력 불일치**: tool 이름 = X, 출력 = Y (예: member_guest_splitter — "분리"인데 카운트/비율 산출). → 의미대로 rename + 분리.
- **두 동사 묶음**: normalization + 합산 (ad_cost_aggregator) — 두 tool 로 분리.

---

## 2.7 Input/Output 계약 원칙 (옵션 C — 진입점 typed)

> **경계만 강제. 내부는 자유.** tool = 단일함수, pipeline = 복합함수. compose 가능성은 *경계 schema 의 호환* 으로 검증.

### 원칙

- **Input**: tool.execute 첫 줄에서 `Input.model_validate(params)`. 잘못된 키·타입 즉시 ValueError.
- **Output**: tool.execute 마지막 `Output(...).model_dump()`. 누락 필드 즉시 fail.
- **내부 자유**: 함수 본체는 dict·지역변수·list comprehension 그대로 OK.

### Schema 위치 — `app/schemas/`

이미 일부 적용 중 (`schemas/inputs/campaigns.py`, `schemas/outputs/dashboard_v1.py`).

```
app/schemas/
├── inputs/    ← tool input params 의 pydantic model (카테고리별)
└── outputs/   ← tool output 의 pydantic model (카테고리별)
```

- tool 코드는 `from app.schemas.inputs.X import XInput` 임포트.
- 같은 schema 를 여러 tool 이 공유 OK (예: `CampaignRow` = campaigns_count + campaigns_spend_total 둘 다).
- catalog yaml 의 `parameters`·`produces` 는 schema 이름만 reference (예: `input_schema: XInput`).

### 적용 사례 (3줄 추가)

```python
async def execute(self, params: dict, context):
    inp = RevenueTotalInput.model_validate(params)        # +1
    df = self.fetch("orders", context)
    df_active = filter_active_orders(df, period=inp.period)
    revenue = sum(safe_int(v) for v in df_active["payment_amount"])
    return RevenueTotalOutput(                             # +1
        revenue_total=revenue, period=inp.period,
    ).model_dump()                                         # +1
```

### 점진 적용

- 신규/분리/이동되는 tool 부터 옵션 C 적용 (자연 흐름).
- 기존 tool 은 옵션 A(dict) 그대로, 변경 시점에 마이그레이션.
- **한꺼번에 다 안 함** — 작업 부담 분산.

### anti-pattern

- 내부 변수까지 typed 강제 (옵션 D) — 빠른 prototyping 저해.
- agent/models 에 tool schema 정의 — tool 이 agent 의존성 가짐 (역방향).
- tool 코드 안 schema 정의 — 다른 tool 과 공유 불가, 중복.

---

## 2.8 카테고리별 tool 인벤토리 — `33_tools_by_category/`

각 카테고리의 *현 tool 목록·input/output schema·status·의도* 는 별 문서:

| 문서 | 내용 |
|---|---|
| `33_collection.md` | collection 카테고리 tool 인벤토리 |
| `33_normalization.md` | normalization 인벤토리 |
| `33_cleaning.md` | cleaning 인벤토리 |
| `33_preprocessing.md` | preprocessing 인벤토리 (현 0, placeholder) |
| `33_metrics.md` | metrics 인벤토리 (최대) |
| `33_comparison.md` | comparison 인벤토리 |
| `33_analysis.md` | analysis 인벤토리 (일반/ML/LLM 3 sub) |

**원칙**: 32 = 카테고리 정의·잣대 (변경 적음). 33/* = tool 인벤토리 (자주 변경). 분리.

---

## 3. 디렉터리 구조 (현재 상태, 2026-05-30)

```
backend/app/dream_agent/tools/
├── base_tool.py                    [implemented]
├── registry.py                     [implemented]  (catalog/ 트리 자동 import)
├── __init__.py
│
├── catalog/                        ← 모든 Tool 의 메타카드 (yaml 위치 = .py 위치 1:1)
│   ├── _schema.yaml                (Tool YAML 스키마 정의)
│   ├── collection/                 (27 yaml; external 13 + internal 8 + sprint15 6)
│   ├── cleaning/                   (3 yaml)
│   ├── normalization/              (4 yaml)
│   ├── metrics/                    (35 yaml)
│   ├── comparison/                 (7 yaml)
│   └── analysis/                   (6 yaml)
│
├── collection/                     [27 tool]  ← raw 가져오기 (32 §2.5)
│   ├── _base.py                    (RawCollectorBase, file_no→source_id 호환 매핑)
│   ├── external/                   (13 — meta/naver/kakao/google/instagram/...)
│   ├── internal/                   (8 — orders/customers/customer_rfm/grade_history/...)
│   └── {meta,kakao,naver_sa,naver_gfa,google_ads,review}_collector.py  (6 sprint15, broken)
│
├── cleaning/                       [3 tool]  ← 결측·이상치·필터·검증·보정
│   ├── active_orders_filter.py     (C40 취소 필터 + 기간)
│   ├── member_metrics_validator.py (customers↔orders 정합 보정)
│   └── missing_value_diagnostic.py (결측 분류 리포트)
│
├── normalization/                  [6 tool]  ← 컬럼·형식·단위·시간대 표준화
│   ├── utm_normalizer.py
│   ├── channel_attribution_normalizer.py
│   ├── grade_system_unifier.py
│   ├── kst_timezone_normalizer.py
│   ├── format_normalizer.py        (5매체 ads → daily_performance 통일, ADR-014 v2)
│   └── review_normalizer.py        (4 출처 리뷰 → review.v1)
│
├── metrics/                        [35 tool]  ← 순수 계산 (33/33_metrics.md 인벤토리)
│   ├── revenue/aov/cac/roas/grade/age/promotion/new_members/signup/repurchase/unknown  (12)
│   ├── campaign_*.py · campaigns_table.py             (5)
│   ├── creative_*.py · creative_cards.py              (4)
│   ├── budget_*.py                                    (3)
│   ├── daily_performance_*.py                         (2)
│   ├── ga4_session_aggregator · channel_aggregate · conversion_funnel  (3)
│   ├── keyword_metrics_avg · keyword_top_roas         (2)
│   └── ad_cost_aggregator · category_multi · member_guest · ab_test_table  (4 묶음 산출)
│
├── comparison/                     [7 tool]  ← 두 metrics 조합
│   ├── mom_revenue · aov_mom · repurchase_mom · new_members_mom
│   ├── grade_timeseries · channel_cac_compare
│   └── inapp_ad_ab_compare (partial)
│
├── analysis/                       [6 tool]  ← LLM·ML·통계 추론
│   ├── review_sentiment · review_keywords · review_recent
│   ├── creative_ai_axes · creative_fatigue
│   └── ai_recommendation
│
├── shared/                         [helper, tool 아님 — 6 helper]
│   ├── helpers.py (find_in_previous 등 공용)
│   ├── missing_helper.py (safe_int·safe_str·null_stats·classify_missing)
│   ├── order_helper.py (filter_active_orders)
│   ├── ad_cost_helper.py (aggregate_ad_cost 5매체)
│   ├── ga4_helper.py (get_event_param 등)
│   └── storage.py (workspace shim, deprecated)
│
├── preprocessing/                  [1 tool]  ← 자연어 텍스트 전처리 (한정)
│   └── text_preprocessor.py        (sponsored 필터·이모지·HTML·dedup)
│
├── report/                         [2 tool]  ← 보고서 텍스트 산출 (LLM)
│   ├── report_writer.py            (마크다운 상세 보고서, 스토리 3단계)
│   └── summary_generator.py        (한 문장 요약, 2026-05-30 shared 에서 이동)
│
└── image_creation/ · video_creation/ · pdf/   (폴더만, planned)
```

### 카테고리 진입 (요약)

| 카테고리 | tool 수 | 인벤토리 |
|---|---:|---|
| collection | 27 | [33_collection.md](33_tools_by_category/33_collection.md) |
| normalization | 6 | [33_normalization.md](33_tools_by_category/33_normalization.md) |
| cleaning | 3 | [33_cleaning.md](33_tools_by_category/33_cleaning.md) |
| preprocessing | 1 | [33_preprocessing.md](33_tools_by_category/33_preprocessing.md) (자연어 한정) |
| metrics | 35 | [33_metrics.md](33_tools_by_category/33_metrics.md) |
| comparison | 7 | [33_comparison.md](33_tools_by_category/33_comparison.md) |
| analysis | 6 | [33_analysis.md](33_tools_by_category/33_analysis.md) |
| report | 2 | [33_report.md](33_tools_by_category/33_report.md) (보조 카테고리 활성화) |

### 빈 폴더 (planned)

`image_creation/`, `video_creation/`, `pdf/` — 폴더 skeleton 만. Planner 가 해당 Tool 을 선택하면 **AgentPool → mock_tools.mock_result()** 로 fallback. 실행은 success 로 보이지만 **실제 데이터는 mock**.

### 2026-05-30 폐기·이동 이력

- `preprocessing/marketing/` 11 tool → `metrics/` 이동 (preprocessing 카테고리 = 자연어 한정 정합).
- `preprocessing/data_normalization/{format,review}_normalizer.py` → `normalization/` 이동 (ADR-014 v2 단일책임 정합).
- `preprocessing/text_cleaning/text_preprocessor.py` → `preprocessing/` 직속 (sub-folder 폐기).
- `preprocessing/brief_parser/` 빈 폴더 폐기.
- `metrics/campaigns_aggregate` → 4 tool 분리 (campaign_count·active·budget·target_roas).
- `metrics/creatives_aggregate` → 3 tool 분리 (creative_count·ctr_avg·roas_avg).
- `metrics/ad_cost_aggregator` → `ad_cost_total` rename (이름·출력 정합).
- `metrics/member_guest_splitter` → `member_guest_stats` rename.
- `shared/summary_generator.py` → `report/` 이동 (shared = helper only 정합).
- `shared/clumi_loader.py` 폐기 (FileDataSource 로 대체).

---

## 4. Tool 실행 파이프라인 상세

### 4.1 런타임 순서

```
1. execution_stage(state) 진입
   └ plan 읽기, hitl.create_progress or get_progress
2. build_phases(plan) = [[t1], [t2, t3], [t4]]  (DAG 위상정렬)
3. for phase in phases:
     3-1. should_continue() 검사 → pause 시 interrupt
     3-2. execute_phase(phase_todos, ctx, previous_results)
          └ asyncio.gather( _run_single_todo × N )
              ├ pool.is_tool_implemented(tool_name)?
              │    ├ True  → pool.get_real_tool(tool_name) = ToolClass 인스턴스
              │    │         _inject_prev_outputs(params, previous_results)
              │    │         await tool.execute(params, context) → data dict
              │    │         TodoResult(status=COMPLETED, data=..., is_mock=False)
              │    └ False → mock_result(tool_name, params)
              │              TodoResult(status=COMPLETED, data=..., is_mock=True)
              │
              └ Exception 시 → TodoResult(status=FAILED, error=str(e), is_mock=...)
     3-3. hitl.report_phase_complete(phase_idx, results)
     3-4. emit todo_start / todo_complete / progress events
     3-5. halt_on_first_failure 검사 (spec §2.4: failed is final, no retry)
4. _build_execution_result() → ExecutionResult.model_dump()
5. Command(update={execution_result, execution_progress}, goto="response")
```

### 4.2 `_inject_prev_outputs` 의 동작

[executor.py:_inject_prev_outputs](../../backend/app/dream_agent/execution/executor.py)

```python
def _inject_prev_outputs(params: dict, previous_results: dict[str, dict]) -> dict:
    """
    previous_results = {todo_id: {"data": {...}, "tool": ..., ...}}
    각 data dict 의 키 중 "_" 로 시작하지 않는 것을 params 에 setdefault 로 주입.
    """
```

**핵심 규칙**:
- **setdefault**: 이미 tool_params 에 명시된 값이 있으면 **절대 덮지 않음** → 사용자 override 우선.
- **`_` prefix 키 제외**: `_meta`, `_debug` 등은 propagate 안 됨.
- **결과 체인의 근간**: 그래서 produces 네이밍 통일이 중요. (e.g. `raw_reviews` → `normalized_reviews` → `cleaned_texts` → ...)

### 4.3 `find_in_previous` helper

[shared/helpers.py:find_in_previous](../../backend/app/dream_agent/tools/shared/helpers.py)

Tool 내부에서 명시적으로 이전 결과를 꺼낼 때 사용:

```python
from app.dream_agent.tools.shared.helpers import find_in_previous

normalized = find_in_previous(context.previous_results, "normalized_reviews")
if normalized is None:
    return {"error": "no normalized_reviews in previous_results"}
```

`previous_results[todo_id]["data"][key]` 또는 `previous_results[todo_id][key]` 양쪽 구조에서 찾음.

---

## 5. Tool 인터페이스 — BaseTool

[tools/base_tool.py](../../backend/app/dream_agent/tools/base_tool.py)

```python
class BaseTool(ABC):
    def __init__(self, spec: ToolSpec, data_source: DataSource | None = None):
        self.spec = spec
        self.ds: DataSource = data_source or get_default_data_source()

    @property
    def name(self) -> str: return self.spec.name

    @abstractmethod
    async def execute(self, params: dict, context: ExecutionContext) -> dict:
        """Tool 의 실제 수행. 반환 dict 는 TodoResult.data 에 그대로 들어간다."""

    def fetch(self, source_id: str, context: ExecutionContext) -> Any:
        """Tool용 데이터 요청 helper-B — client 는 context.client_id 에서만 (fail-fast).
        ADR-022: tool 은 *무엇*(source_id)만 알고 *어디/누구*는 data layer.
        """
        client = context.client_id
        if not client:
            raise ValueError(f"client 미지정: ExecutionContext.client_id 비어있음 (source_id={source_id!r})")
        return self.ds.get(client, source_id)

    def validate_params(self, params: dict) -> tuple[bool, list[str]]: ...
    def get_default_params(self) -> dict: ...
    def merge_params(self, params: dict) -> dict: ...
```

**`execute(params, context)` 계약**:
- **params**: Tool 에 주입된 값 (Planner tool_params + _inject_prev_outputs 결과)
- **context**: `ExecutionContext(session_id, plan_id, client_id, user_id, language, previous_results, session_memory, ...)`
- **반환 dict 필드**:
  - `produces` YAML 선언에 맞는 key 들 (e.g. `raw_reviews`, `count`)
  - `error: str` 가 있으면 Executor 가 FAILED 로 간주 (현재는 raise 와 반환 모두 지원, **raise 권장**)

### 5.1 DataSource DI 패턴 (Sprint 16+, ADR-022)

> 결정 박제: [ADR-022](adr/ADR-022_data_source_workspace_layer_separation.md) — Tool ↔ Data 사이 "관절"

**원칙**: Tool 은 "*무엇을*" 만 알고, "*어디서*" 는 `DataSource` 가 결정. tool 코드 안에 data 경로 박힘 금지 (P1).

**표준 패턴** — `__init__` DI + `execute` 내 `self.fetch(source_id, context)` helper-B 사용:

```python
from app.data_sources import DataSource

class ActiveOrdersFilter(BaseTool):
    def __init__(self, spec: ToolSpec, ds: DataSource | None = None):
        super().__init__(spec, ds)
        # self.ds 는 BaseTool 이 초기화 (data_source 또는 default 싱글톤)

    async def execute(self, params, context):
        merged = self.merge_params(params)
        df = self.fetch("orders", context)               # ← helper-B: client = context.client_id (fail-fast)
        # ... 순수 기능만
```

**Workspace 출력 (선택)**:

```python
from app.workspace import get_default_workspace

ws = get_default_workspace()
ws.save("cleaned", f"orders_active_{period}", {"rows": ..., "meta": {...}})
```

**테스트 시 DI**:

```python
mock_ds = MockDataSource({"clumi:orders": sample_df})
tool = ActiveOrdersFilter(spec, ds=mock_ds)
result = await tool.execute({"period": "2026-04"}, ctx)
```

→ monkeypatch 불필요. tool = 순수 기능 + DI = 자연 testable.

**❌ Anti-pattern (Sprint 15 이전 패턴, 금지)**:

```python
# ❌ data 경로 박힘
from app.dream_agent.tools.shared.clumi_loader import load_clumi_source
df = load_clumi_source(5)  # ORDERS_FILE_NO=5, clumi 전용

# ❌ 회사 변경 시 tool 코드 수정 필요
```

**`client` 결정** (ADR-022, 작업 ②-a 2026-05-30):

- `ExecutionContext.client_id` **한 곳**에서만 흐른다 (fail-fast).
- 진입점 (runner / API / agent) 이 ctx.client_id 를 채운다 — 없으면 `self.fetch()` 가 `ValueError` raise.
- Tool 의 `params` 에는 client 없음. Tool 은 client 모름.
- POC fallback `"clumi"` default = 폐기 (workspace 단계 5, commit `4fc3f4f`).

→ 현재 **90 tool** (collection 27 + normalization 6 + cleaning 3 + preprocessing 1 + metrics 35 + comparison 7 + analysis 9 + report 2) 모두 이 패턴 (작업 ④-L5/L7 commit `dd9dbd1`·`3738be6`).

---

## 6. Tool YAML 메타카드 스키마

`tools/catalog/_schema.yaml` 이 정식 스키마. 실제 예시:

**[tools/catalog/collection/review_collector.yaml](../../backend/app/dream_agent/tools/catalog/collection/review_collector.yaml)**:

```yaml
name: review_collector
category: collection            # collection | normalization | cleaning | preprocessing | metrics | comparison | analysis | report
description: "리뷰 수집 (naver_blog·shopping·cafe·oliveyoung, ADR-014 v2 통합)"
executor: null                  # null → 경로 규칙으로 자동 import
parameters:
  - name: brand
    type: string
    required: true
  - name: source
    type: string
    default: naver_blog
  - name: period
    type: string
    default: 3months
  - name: limit
    type: integer
    default: 100
produces:
  - raw_reviews
timeout_sec: 60
max_retries: 0                  # Sprint §2.4: retry 금지
requires_approval: false
has_cost: false
estimated_cost_usd: 0
```

**`executor` 필드 규칙**:
- `null` (권장) → `app.dream_agent.tools.<category>.<name>.<PascalCase>` (category = 8 카테고리 중 하나)
- 경로 명시 시 그대로 import

**상태 표기**: yaml 의 `status` 필드는 폐기 (작업 ③·④, 2026-05-30/31).
tool status 는 [33_tools_by_category/*.md](33_tools_by_category/) 의 tool 표 `status` 컬럼 박제
(complete / partial / planned / deprecated / split-pending). registry.py 는 `status` 필드를 읽지 않음 — yaml 에 작성해도 silent ignore.

---

## 7. 구현/Stub/Planned 전수표 — **폐기됨**

> ⚠ **POLAR / DEPRECATED (2026-05-31, 작업 ⑤).**
> 본 §7 의 표 (옛 §7.1·§7.2) = 2026-04-24 시점 ~10 tool 전제. 작업 ③·④ 후 90 tool 정합. 표 자체가 의미 상실 + 옛 카테고리 (preprocessing/pdf/image_creation/video_creation/shared) 박제 = 작업 ③ 8 카테고리와 모순.
>
> **진실 소스** = [33_tools_by_category/](33_tools_by_category/) (8 카테고리 인벤토리, 90 tool, status 컬럼 박제).
>
> 본 §7 의 표 = commit 폐기 (2026-05-31, 작업 ⑤). 헤더만 **다음 32 본 문서 갱신 시 (v1.2 또는 sprint 17+ 시점)** 완전 제거 예정 — 32 §2·§5·§8 추가 갱신 필요 시 묶음 처리.

### 7.1 stub 폐기 기록 + 재구현 로드맵 (2026-06-12, 오너 결정)

방향: **"구현 가능한 건 구현하면서 줄이자"** — mock("되는 척")보다 정직 degrade("안 된다고 말함")가 헌법 19 I1 정합. 카탈로그 메뉴에서 제거된 stub 은 planner 가 선택 불가 → 해당 요청은 정직 degrade.

| tool | ★오너 도메인 정의 (재구현 시 기준) | 처분 | 재구현 조건 |
|---|---|---|---|
| `trend_analyzer` | **트렌드 분석 — forecaster(예측)와 다른 개념** (과거 추세/패턴 분석 ≠ 미래 외삽). "forecaster 가 대체" 분류는 오답 | 폐기 후 재검토 (2026-06-12) | 헌법 §7 채용 3문항 + 계산 방법은 오너 제공 (정제·계산 임의 생성 금지) |
| `competitor_comparator` | **A/B 테스트 분석 tool** (일반 경쟁사 비교 아님) — 단일 tool 로는 구현 어려움 | 폐기 후 재검토 (2026-06-12) | 동일 + 분해 설계 선행 (단일 tool 부적합 판정됨) |
| `creative_team` 9종 (image_generator·image_resizer·thumbnail_creator·storyboard_creator·video_image_generator·slogan_writer·copy_generator·material_modifier·variation_generator) | 광고 크리에이티브 생성 — 외부 API(이미지/영상)·비용·제품 결정 필요한 **새 제품 영역** | **팀 전체 폐기** (2026-06-12, 2차) — agent 4 + tool 9. stage1 프롬프트에 "미지원 → 미선택" 규칙 동기 | 제품 결정 + 헌법 §7. TaskType 은 언어 레이어에 유지(인식→정직 미지원 응답) |
| `word_template_filler` / `excel_template_filler` | Word/Excel 양식 채우기 (렌더 확장) | 폐기 (2026-06-12, 2차) — 수요 미측정. output_format=excel 은 텍스트로 정직 응답 | 수요 측정(기준질문/사용 로그) + 헌법 §7 |
| `template_selector` | PDF 템플릿(브랜드 컬러·레이아웃) 선택 — produces `template_choice` | 폐기 (2026-06-12, 3차) — 소비자(word/excel filler)가 2차 폐기로 0, pdf_renderer 는 template 미수용 (헌법 R6) | pdf_renderer 가 템플릿을 수용하는 설계 + 헌법 §7 |
| `chart_to_slide` | 차트 이미지를 슬라이드로 배치 — produces `chart_slides` | 폐기 (2026-06-12, 4차) — 산출 소비자 0 (R6) + 책임을 **pptx_generator 의 chart_image_paths 선택 소비로 실구현·흡수** (별도 tool 불요 판정) | 불요 — 기능은 pptx_generator 에 살아있음 |
| `slide_designer` | PPT 시각 디자인 후처리 (레이아웃·색·폰트, 브랜드 컬러) | 폐기 (2026-06-12, 4차) — 브랜드 디자인 자산(D10) 확보 전 구현 불가. stub 잔류 = mock "디자인된 척" 경로라 메뉴에서 제거 | D10(브랜드 컬러·폰트 가이드) 확보 + 헌법 §7 |

부수 효과: trend/competitor stub 의 `params_required: [cleaned_texts, ...]` 가 subject-coherence 게이트의 리뷰-tool 오분류를 유발하던 함정(2026-06-11 분석 low 이슈) 해소.

**잔여 stub 0종 — stub 제도 폐지** (2026-06-12 오너 최종 처분): `chart_generator` 는 **실구현**(matplotlib·한국어 폰트·frontend Warm Neutral 차트 팔레트 미러 — 산출 형태 기반 결정론 차트 선택, 차트화 불가 시 data_insufficient 정직 SKIP). mock_tools.py("되는 척" 경로)와 executor stub 분기 삭제 — 비구현 tool 이 카탈로그에 등재되면 조용한 mock 대신 시끄러운 실패(I1). `test_d1_output_category_split.py::test_s2_4` 가 "전 tool implemented" 를 박제. 미구현 의도 표기는 코드 `Status: planned` 마커(DC-10)가 담당.

---

## 8. 실제 구현된 Tool 체인의 데이터 흐름

> 작업 ③·④ 후 90 tool 8 카테고리 정합. POC end-to-end **2 경로** (ads chain + review chain).
> 카테고리 표기 = 8 카테고리 enum 값 (sub-folder ml/llm 은 괄호 안 보조 명시).

### 경로 A — 광고 성과 분석 (ads chain)

```
┌─────────────────────────────────┐
│ external/meta_ads_performance / │  collection (helper-B 패턴, ADR-022)
│ external/meta_ads_by_age /      │  85 tool 중 collection 22 (external 13 + internal 8 + review 1)
│ external/meta_instagram_inapp / │  ⑫ (2026-06-01): broken 5 ads collector
│ external/naver_searchad /       │  (meta/kakao/naver_sa/naver_gfa/google_ads) 폐기
│ external/naver_advoost /        │  → external 신 패턴 분리 (ADR-014 v2)
│ external/kakao_bizmessage / ... │
└─────────────────┬───────────────┘
                  │ {meta_ads_raw, naver_ads_raw, ...} 신 produces key
                  ▼
┌─────────────────────┐
│ format_normalizer   │  normalization (ADR-014 v2 단일책임, ads 전용)
│  (normalization)    │  → normalized_ads (ads.v1 통일 스키마)
└──────────┬──────────┘
           │ normalized_ads
           ▼
┌─────────────────────┐
│ daily_performance_  │  metrics (순수 계산, 일별 시계열 합산)
│   aggregate         │  → daily_rows + metrics list
│  (metrics)          │
└──────────┬──────────┘
           │
           ├──────► ad_cost_total · campaign_count · creative_ctr_avg 등 (metrics 35 중 다수)
           ▼
┌─────────────────────┐
│ report_writer +     │  report (보조 카테고리, LLM 마크다운)
│ summary_generator   │
│   (report)          │
└─────────────────────┘
```

### 경로 B — 리뷰 감성·키워드·인사이트 (review chain)

```
┌─────────────────────┐
│ review_collector    │  collection (4 출처: naver_blog·shopping·cafe·oliveyoung)
│  (collection)       │  → raw_reviews
└──────────┬──────────┘
           │ raw_reviews
           ▼
┌─────────────────────┐
│ review_normalizer   │  normalization (ADR-014 v2 분리, review 전용)
│  (normalization)    │  → normalized_reviews (review.v1)
└──────────┬──────────┘
           │ normalized_reviews
           ▼
┌─────────────────────┐
│ text_preprocessor   │  preprocessing (자연어 텍스트만)
│  (preprocessing)    │  → cleaned_texts
└──────────┬──────────┘
           │ cleaned_texts
           ├──────────────────────────┐
           ▼                          ▼
┌─────────────────────┐    ┌─────────────────────┐
│ sentiment_analyzer  │    │ keyword_extractor   │  (Phase 내 병렬)
│  (analysis, ml/)    │    │  (analysis, ml/)    │
│ → sentiment_dist    │    │ → top_keywords      │
└──────────┬──────────┘    └──────────┬──────────┘
           │                          │
           └────────────┬─────────────┘
                        ▼
           ┌─────────────────────────────┐
           │ insight_extractor           │  analysis, llm/ sub-folder
           │  (analysis, llm/)           │  (sentiment + keywords 자동 주입)
           │ → insights                  │
           └──────────────┬──────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │ report_writer +     │  report (LLM 마크다운)
              │ summary_generator   │
              │   (report)          │
              └─────────────────────┘
```

→ POC 시나리오 = 위 2 경로. 나머지 90 tool (cleaning 3, comparison 7, analysis 직속 6, metrics 35 일부) = pipeline 또는 분석 team 호출 시 활성.
→ 카테고리별 인벤토리·계약·status = [33_tools_by_category/](33_tools_by_category/) 8 문서.

---

## 9. 새 Tool 추가 — Step-by-Step

### 9.1 Checklist

신규 Tool `X` 추가 시 **모두 동시에** 수행:

1. **YAML 메타** — `tools/catalog/<category>/<X>.yaml` 작성
   - name, category, status (처음엔 `implemented` 로 두되 테스트 전엔 `stub` 시작해도 됨)
   - parameters (required/optional, default)
   - **produces 명시** ← 다음 Tool 이 이 이름으로 받아감
   - requires_approval (외부 사이드이펙트/비용 있으면 true)

2. **구현 파일** — `tools/<category>/<X>.py`
   - `class X(BaseTool)` 정의
   - `async def execute(self, params, context) -> dict`
   - **docstring 에 `Status: complete` 추가** (MEMORY: *코드 Status 마커 컨벤션*)
   - 이전 결과가 필요하면 `find_in_previous(context.previous_results, "<produced_key>")`

3. **Planning 카탈로그 등록** — `planning/catalog/team_catalog.yaml`
   - 해당 Agent 의 `tools` 배열에 `{name: X, status: implemented, description: ..., produces: ...}` 추가
   - **중요**: Planner 는 이 카탈로그에만 의존. YAML 만 넣고 team_catalog 누락 시 **절대 계획되지 않음**.

4. **Prompt 업데이트** (선택) — Planner 의 Stage 3 프롬프트 `planning_stage3_todo.yaml` 에 해당 Tool 이 적합한 task_type 예시 추가 (LLM 선택률 높임).

5. **테스트**
   - unit: params 검증, execute 순수 동작
   - integration: planner 가 실제로 Todo 에 이 Tool 을 뽑는지 + Executor 가 load 해서 실행하는지
   - **Contract Test DC-10**: Status 마커 일관성 검사에 포함되는지 확인 (docstring/YAML/team_catalog 3 중 일치)
   - *(예정) Contract Test DC-11 (가칭)*: YAML `produces` 선언 ↔ 실제 execute() return key 일치 — **아직 미구현/미검증 제안**. §11.8 참조.

### 9.2 예시: `youtube_collector` 추가

```yaml
# tools/catalog/collection/youtube_collector.yaml
name: youtube_collector
category: collection
description: "YouTube 영상 리뷰/댓글 수집 (Data API v3)"
executor: null
parameters:
  - name: brand
    type: string
    required: true
  - name: query
    type: string
    description: "검색 쿼리, 미지정 시 brand 재사용"
  - name: period
    type: string
    default: 3months
  - name: limit
    type: integer
    default: 100
  - name: include_comments
    type: boolean
    default: true
produces:
  - raw_reviews            # ← format_normalizer 와 호환되게 기존 키 재사용
timeout_sec: 120
max_retries: 0
requires_approval: false
has_cost: true
estimated_cost_usd: 0.01
```

```python
# tools/collection/youtube_collector.py
"""
YouTube Data API v3 리뷰 수집.

Status: complete — 2026-04-XX Sprint 15 수집 확장
"""
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.helpers import _filter_by_period
from app.dream_agent.models.execution import ExecutionContext

class YoutubeCollector(BaseTool):
    async def execute(self, params: dict, context: ExecutionContext) -> dict:
        brand = params["brand"]
        query = params.get("query") or brand
        period = params.get("period", "3months")
        limit = params.get("limit", 100)

        # ... YouTube API 호출 ...
        raw = [...]  # [{id, text, rating, channel, date, ...}]

        return {
            "raw_reviews": raw,
            "count": len(raw),
            "brand": brand,
            "source": "youtube",
            "period": period,
        }
```

```yaml
# planning/catalog/team_catalog.yaml (부분)
analysis_team:
  agents:
    collection_agent:
      tools:
        - name: review_collector
          status: implemented
          produces: [raw_reviews]
        - name: youtube_collector        # ← 추가
          status: implemented
          produces: [raw_reviews]
```

### 9.3 가장 흔한 실수

| 증상 | 원인 |
|------|------|
| Planner 가 해당 Tool 을 영영 안 뽑음 | `team_catalog.yaml` 에 등록 안 함 |
| Executor 에서 `ImportError` | 클래스명이 경로 규칙과 불일치 (파일명 snake_case → 클래스 PascalCase) |
| `is_mock=True` 가 계속 나옴 | YAML `status: stub` 로 남아있거나 `team_catalog.yaml` 의 status 와 불일치 |
| 이전 결과가 빈 dict 로 들어옴 | produces 키 이름 불일치 (e.g. `raw_review` vs `raw_reviews`) |
| tool_params 의 default 가 덮임 | `_inject_prev_outputs` 의 key 와 parameter 이름이 같아서 충돌 — prefix 를 `_` 로 시작시켜 전파 차단 |
| Phase 가 계속 pending | `depends_on` 에 존재하지 않는 id 참조 → `validate_dag` 에서 누락 감지되는지 확인 |
| 서버 재시작 후 재개 실패 | Tool 이 execute 중 pickle 불가 객체를 state 에 넣음 (Checkpointer 직렬화 실패) |

---

## 10. 시스템 에이전트와 연결되는 **잊기 쉬운 접점**

Tool 을 만들 때 **Execution Layer 안의 일만** 생각하기 쉽지만, 다음 접점들이 시스템 전체 동작을 좌우한다:

### 10.1 Cancel/Pause 가능성

- 현재 pause 는 **Phase 경계** 에서만 발생. 즉 Phase 안의 Tool 은 **중단 불가**.
- 따라서 **분 단위 이상 걸리는 Tool** (외부 API, 영상 처리 등) 은 **단독 Phase** 로 배치되도록 DAG 를 설계할 필요 — Planner 프롬프트에서 유도하거나, Tool 자체에 "무거움 플래그" 를 넣어 이후 A2 에서 활용.

### 10.2 `requires_approval` 플래그

- Tool YAML 에 넣어두면 **Sprint 14 A4** 에서 pre-exec interrupt 자동 발동 예정. **지금** 넣어두면 A4 완료 시 자동 수혜.
- 후보: PDF 렌더러, 이미지/영상 생성기, 외부 광고 플랫폼 collector.

### 10.3 Response Layer 가 읽는 것

- Responder 는 `execution_result.todos[*].data` 를 **LLM 요약** 하므로, `data` 크기가 너무 크면 token cost 폭증. `_build_execution_summary` 가 size-limited 추출을 하지만, 가급적 `data` 에 raw 큰 배열을 100 개 이상 남기지 말 것.
- 긴 데이터는 **파일로 저장 + `attachments[].path` 로 참조** 패턴 권장.

### 10.4 `is_mock` 전파

- Responder 는 `is_mock=True` 가 섞인 결과는 summary 에 그대로 반영할 수 있음 ("mock 데이터 기반으로 작성됨" 같은 문구). 실제 배포 시 이 flag 를 어떻게 노출할지 UX 합의 필요.

### 10.5 Session 메모리

- `ExecutionContext.session_memory` 는 현재 **빈 dict 로 전달**만 됨. Sprint 15 MemoryManager 구현 시 실제 채워질 예정. Tool 이 이걸 읽는 코드를 미리 넣어두면 무난.

### 10.6 Trace 로깅

- `AgentState.trace` 는 append-only, max 200. Tool 내부에서 중요한 판단 기록을 남기려면 Executor 가 자동 축적해주는 todo_start/complete 외에 **별도 trace write 가 없음**. 필요하면 해당 Todo `data` 에 `_trace: [...]` 같은 의도적 prefix 키를 넣어 Responder 로 전파 안 하고 로그에만 쓰는 패턴.

---

## 11. 사용자가 놓치기 쉬운 부분 (Gap 정리)

### 11.1 **31 문서와 실제 구현의 Huge Gap**

[31_execution_agent_function_list_v0.6.md](31_execution_agent_function_list_v0.6.md) 는 **요구사항 문서**. 현재 실구현은 8 개 Tool 뿐이며, 나머지 40+ 개는 **명세만** 존재. 31 문서를 읽고 "이미 있다" 고 착각하지 말 것. → 이 문서(32)가 그 gap 의 단일 지도.

### 11.2 **mock_tools 커버리지가 31 문서보다 좁다**

[execution/mock_tools.py](../../backend/app/dream_agent/execution/mock_tools.py) 의 `mock_result()` switch 는 대표적인 tool_name 일부만 처리. 31 문서에 있는 Tool 중 **mock_tools 에도 없는** 이름은 `{"mock_result": "..."}` 기본 fallback 으로 떨어진다. POC 시나리오 테스트 시 이 차이가 플레인 실패처럼 보임.

**→ 필요 시 `mock_tools.mock_result()` 에 tool_name 별 분기 추가 권장.**

### 11.3 **Planner 가 "있는 Tool 만" 안다**

Planner 의 Stage 1/2/3 프롬프트는 `team_catalog.yaml` 을 읽어 LLM 에 전달. 즉 카탈로그에 없는 Tool 은 **절대 생성되지 않음**. `tools/catalog/*.yaml` 에 YAML 만 있고 `team_catalog.yaml` 미등록이면 **영영 호출 안 됨**.

### 11.4 **Tool 내부 예외 처리 = raise 통일 (2026-05-31 정합 박제)**

- 작업 ②-a (2026-05-30) + 작업 ④·⑤·⑥ 정합 후 = 90 tool 모두 `raise` 스타일 통일 (`return {"error":}` 패턴 0 hit 확인).
- Executor 가 `RuntimeError`/`ValueError` 를 FAILED 로 변환. Responder 가 `error_message` 일관 처리.
- **신규 tool 추가 시**: `raise RuntimeError(msg)` 또는 `raise ValueError(msg)` 권장. `return {"error":}` 금지.

### 11.5 **Retry 정책**

- spec §2.4 = **no retry**, failed is final
- 그러나 Tool YAML 에는 `max_retries: 0` 이 **관습적으로** 적힐 뿐, 실제 enforcing 은 executor 에서 하지 않는다 (Tool 쪽에서 직접 retry 하면 막을 방법 없음).
- **권고**: 외부 API Tool 이 transient error 를 잡기 위해 내부 retry 를 하더라도 **상한 (3 회 등) 을 명시** 하고, exponential backoff 를 넣어 Phase 전체 timeout (60s 기본) 과 충돌 안 하게.

### 11.6 **Checkpointer 직렬화**

- Tool.execute 의 return dict 는 eventually `AgentState` → Postgres Checkpointer 로 들어감.
- **pickle 불가능한 객체** (file handle, async gen, thread local 등) 를 dict 에 넣지 말 것. 재시작 후 `resume_query` 시 로드 실패.
- **파일 객체는 경로 (str) 로만 보관**, 실제 내용은 디스크에 저장.

### 11.7 **동시성 — Tool 은 thread-safe 필요 없지만 async-safe 는 필수**

- `asyncio.gather` 로 병렬 실행되므로 **동일 Tool 클래스의 여러 인스턴스가 동시 execute** 될 수 있음 (AgentPool 이 인스턴스 캐시).
- 클래스 인스턴스 변수 / 전역 dict 사용 시 **race** 주의. 가능하면 stateless.

### 11.8 **YAML `produces` 선언의 실효성**

- 현재 `produces` 는 **문서화 목적만**. Executor 는 실제 return dict 를 그대로 전파하므로, YAML 선언과 return 이 불일치해도 런타임 에러 없이 지나감 (다음 Tool 이 못 찾을 뿐).
- **→ 자동 검증 필요**: "YAML produces 에 선언된 키가 실제 return dict 에 있는지" Contract Test 에 추가 제안 → **DC-11 (가칭)**. 도입 타이밍은 Tool 확장 Sprint 킥오프 직전 권장 (지금은 implemented Tool 8 개 뿐이라 ROI 낮고, 40+ 개 확장 직전에 깔면 회귀 차단 효과 최대).
  > **⚠️ 제안 단계**: DC-11 은 아직 **설계/검증/테스트 안 된 아이디어**. 구현 스켈레톤·성공 기준·외부 API Tool 의 mock 전략 미정. 코드 반영 시 별도 검토 필요. 현 DC-1~DC-10 실장 위치: [backend/tests/docs/test_doc_code_contract.py](../../backend/tests/docs/test_doc_code_contract.py).

### 11.9 **`shared/summary_generator.py` 의 위치 모호성**

- 이 파일은 Tool (execute 가능) 이면서 동시에 `executor._generate_summary()` 가 가지는 **내부 헬퍼** 처럼 쓰임.
- → 둘 중 하나로 정리 필요: (a) 완전한 Tool 로 올려서 Planner 가 뽑게 하거나, (b) helpers.py 쪽으로 흡수.

### 11.10 **Brand Guideline RAG 의 부재**

- 31 문서에서 `brand_guideline_analyzer` 를 **크리에이티브 팀 공용 핵심 Tool** 로 표시.
- 현재 구현 0%. 그런데 크리에이티브 Tool 을 추가하려면 이게 먼저 필요 (브랜드 톤/금칙어/시각 가이드 제약).
- **→ 확장 전제 조건**: RAG 기반 `brand_guideline_analyzer` 를 가장 먼저 구현해야 후속 이미지/영상/슬로건 Tool 이 실제 값어치 있음.

### 11.11 **Tool 간 의존 그래프 시각화 부재**

- Planner 가 produces/consumes 를 LLM 추론으로 연결 → **사람이 전체 Tool chain 가능성을 한눈에 볼 수단 없음**.
- → 제안: `team_catalog.yaml` 을 읽어 produces/consumes 그래프를 mermaid 로 뽑는 스크립트 (`scripts/gen_tool_graph.py`) 추가.

### 11.12 **언어 / 다국어**

- 현재 POC: 한국어 전용 가정 (`text_preprocessor` 의 정규식 한글 범위, `keyword_extractor` 의 한국어 토큰).
- 31 문서 3차 목표: 다국어. → Tool 레벨에서 `params["language"]` / `context.language` 를 받되 분기 로직 준비 필요.

### 11.13 **비용 / 토큰 회계**

- Tool YAML 에 `has_cost`, `estimated_cost_usd` 필드 있으나 **누적 추적 없음**.
- LLM Tool (`insight_extractor`, `report_writer`, `response`) 호출 비용이 현재 관측 불가.
- → Sprint 15+ observability 항목. `ExecutionResult.meta.tokens_used` 를 채워 Responder 로 넘기면 대시보드 표시 가능.

### 11.14 **Execution 이 `state["plan"]` 을 수정 안 함**

- Todo 편집 (A3) 후 hitl_manager 가 `_progress.plan` 을 갱신하지만, **state["plan"] 은 첫 Planning 결과 그대로 유지**될 수 있음. Executor 는 `hitl.get_progress().plan` 을 읽으므로 문제 없지만, Response Layer 가 `state["plan"]` 을 쓰는 경우 편집 전 plan 을 보게 됨.
- **→ 확인 필요**: response_stage 가 최종적으로 편집된 plan 을 보는지. (편집 후 state 갱신 경로가 Command(update) 로 이어지는지 추적.)

---

## 12. 추가 구현 우선순위 제안

단기 (Sprint 15 직전) 가치가 큰 순으로:

| 우선순위 | 작업 | 근거 |
|----------|------|------|
| ★★★ | **brand_guideline_analyzer (RAG)** | 크리에이티브 전 계열 선결 조건 |
| ★★★ | **pdf_converter** + chart_generator | 31 문서 v0.5 NEW 추가 항목, 리포트 deliverable 완성 |
| ★★★ | **mock_tools 확장** — 31 문서 Tool 전부 mock 분기 | POC 데모 시나리오 커버리지 |
| ★★☆ | **kpi_calculator + kpi_anomaly_detector + kpi_trend_analyzer** | POC-01/06 실행 (광고 성과 분석) |
| ★★☆ | **youtube_collector + oliveyoung_collector** | 실데이터 확장 첫걸음 |
| ★★☆ | **ad_image_generator (DALL-E)** + ad_prompt_generator | 31 문서 이미지 에이전트 핵심 |
| ★★☆ | **sponsored_detector + language_detector** | 데이터 품질 8-step 중 가장 영향 큰 2 |
| ★☆☆ | **슬로건 체인 (generator + rag_search + evaluator + overlay)** | 네 Tool 을 한 묶음으로 추가 |
| ★☆☆ | **영상팀 전체** | 비용/복잡도 높음, 후순위 |
| 인프라 | **`produces` 자동 검증 Contract Test (DC-11 가칭)** — *미검증 제안* | 신뢰 기반 확장. §11.8 참조. 설계·성공 기준·외부 API mock 전략 미정 상태. |
| 인프라 | **Tool 그래프 시각화 스크립트** | 설계/디버깅 속도 |
| 인프라 | **비용 회계 (tokens_used / cost_usd 집계)** | observability 기반 |

---

## 13. 관련 문서

| 번호 | 제목 | 이 문서와의 관계 |
|------|------|------------------|
| [14_system_agent_overview_v1.0.md](14_system_agent_overview_v1.0.md) | System Agent Overview | **선행 문서** — 4 Layer 전체 지도 |
| [10_system_architecture_v1.9.md](10_system_architecture_v1.9.md) | System Architecture | Execution Layer interrupt 모델 |
| [11_main_graph_state_v1.5.md](11_main_graph_state_v1.5.md) | AgentState | `execution_result`, `execution_progress` 스키마 |
| [22_error_codes_v1.1.md](22_error_codes_v1.1.md) | Error Codes | EXECUTION_ALL_FAILED, PARTIAL_FAILED |
| [30_DATA_MODELS_v1.1.md](30_DATA_MODELS_v1.1.md) | Data Models | ExecutionResult / TodoResult / ToolSpec |
| [31_execution_agent_function_list_v0.6.md](31_execution_agent_function_list_v0.6.md) | Execution Agent Function List | **요구사항** (이 문서는 "구현 현황") |

---

## 변경 이력

| 버전 | 날짜 | 변경 |
|------|------|------|
| v1.0 | 2026-04-24 | 최초 작성 — 31 요구사항 vs 실제 구현 gap 정립, 확장 체크리스트/anti-pattern 제공. 동일 일자 micro-bump (§11.8 / §12 / §9.1 에 **DC-11 (가칭)** 라벨 추가. Tool `produces` 자동 검증 Contract Test 제안. 주의: 아직 설계·검증·테스트 전혀 안 된 아이디어 단계 — 도입 전 별도 검토 필요) |
| v1.0 (Sprint 16 보강) | 2026-05-27 | **§5.1 DataSource DI 패턴 신설** (ADR-022 박제). Tool ↔ Data 사이 "관절" — `__init__` DI + `client` 동적 결정 (3 fallback). 표준 코드 패턴 + Workspace 출력 + 테스트 DI + **❌ Anti-pattern** (Sprint 15 이전 `load_clumi_source(N)` 직접 호출 금지). Sprint 16 46 tool 일괄 전환 패턴. 30 spec §7.5/7.6 DataSource·Workspace ABC 참조. |
