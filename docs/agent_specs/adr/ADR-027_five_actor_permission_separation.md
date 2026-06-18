# ADR-027: Pipeline·Maker·DataSource·Tool·ml_model 5 주체 권한 분리

## Status

**Accepted** (2026-05-28) — 사용자 통찰 *"tool 내부 hardcode 위험, 권한이 명확해야 한다"* + *"tool 다 만든다. ml model 파트만 mock"* 박제. ADR-022 (DataSource·Workspace) + ADR-023 (5 외부 주체) 위의 *Pipeline 영역 내부 코드 책임* 분리.

## Context

### 1. 사용자 통찰 (2026-05-28)

68 spec Batch 5 V3 게이트 + 후속 라운드:

> "tool 내부의 하드코딩이 굉장히 위험하다. 특히 칼럼명 / 데이터 전달방법이 뒤섞일수 있다. 권한이 명확해야 한다. pipeline / maker / data_sources / tool 이 명확한 권한설정"

> "tool은 다 만들어야 한다. 다만 ml은 하루아침에 생기는게 아니니깐 tool이 요청 -> ml model 접속 -> 결과 반환 이렇게 되어야 하는게 tool - ml_model -> ml mock data 접속 -> ml mock data 반환 으로 되어야 한다. 'ml_model -> ml mock data 접속 -> ml mock data 반환' 이 부분만 ml model로 교체가능하게 바꿔야 한다"

→ **4 주체 (Pipeline·Maker·DataSource·Tool) + ml_model (5 번째)**. Tool 은 production / ml_model *구현체* 만 swap.

### 2. ADR-022·023 와의 관계

| ADR | 영역 | 본 ADR 관계 |
|---|---|---|
| **ADR-022** (DataSource·Workspace 존재) | 데이터 *경로* | 본 ADR = **DataSource 책임 명시 확장** (정규화·schema 매핑) |
| **ADR-023** (5 외부 주체 — Agent/Direct API/Maker/Runner/Validator) | 시스템 *외부 작동 주체* | 본 ADR = **Pipeline 영역 *내부* 코드 책임** (직교) |

→ ADR-022 + ADR-023 = *시스템 외부 구조*. 본 ADR = *코드 영역 내부 권한 분담*.

### 3. 현 시스템의 *권한 위반* 사례

| 위치 | 위반 | 영향 |
|---|---|---|
| **Tool 코드** (예: clumi_outputs) | `df["payment_amount"]` 같은 client 컬럼 hardcode | client 추가 시 Tool 코드 수정 필요 |
| **YAML inputs** (Batch 5 C11) | `axes: [AI_Sales, AI_Short, ...]` hardcode | Canvas 사용자가 산식 변경 불가 |
| **DataSource 코드** | `if client == "blooming"` 같은 분기 | client 추가 시 코드 수정 |
| **ML 추론** (현 부재) | (없음 — raw 사전박힘 가정) | 진짜 ML 진입 시 *전 코드 재작성* 위험 |
| ~~**Tool 코드 (broken review_collector)**~~ ✅ | ~~`load_mock_csv` 파일 경로 + `df["브랜드"]` 한글 hardcode + brand·source·period·limit 필터 (collection + filtering 결합)~~ | ~~clumi reviews.csv schema 변경 시 Tool 코드 수정 필요~~ |
| ~~**Tool 코드 (broken 5 ads collector)**~~ ✅ | ~~동일 패턴 (load_mock_csv + 도메인 hardcode)~~ | ~~data/mock/ 폐기로 즉시 fail (sprint15 broken baseline 54)~~ |

→ **권한 분리 + ml_model adapter** 로 해결.

> ✅ **작업 ⑫ (2026-06-01) 해소** — broken 5 ads collector (meta·google_ads·naver_sa·naver_gfa·kakao) 폐기 + review_collector helper-B 패턴 재작성 (`self.fetch("reviews", context)` + raw 통째 반환 + ADR-027 §1 Tool 권한 매트릭스 docstring 박제 + RC-05 자동 검증).
>
> ✅ **작업 ⑮ (2026-06-01) 해소** — broken 5 이름 잔존 9 docs doc-drift 정리 (32/33_collection/65/00_overview/02_collection active 5 + ADR-014/015/017/019 amend 4, commit 59bd6af).
>
> ✅ **작업 ⑭ (2026-06-01) 부분 해소** — team_catalog 신 21 collector 등재 (external 13 + internal 8, collection_agent atomic) + Source enum +8 (META/KAKAO/GA4/ORDERS/CUSTOMERS/PROMOTIONS/CATEGORY_SALES/CRM) + cognitive.yaml prompt 9→17 + Stage 3 prompt intent 분기 매핑 통합. **collection 카테고리 dual-source drift 100% 해소** (invisible 76 → 55, Planner LLM 시야 회복).
>
> ✅ **작업 ⑱ (2026-06-01) 부분 해소** — (A) stub 3 폐기 (youtube/coupang/oliveyoung 역드리프트 死코드, 5 파일 정리) + (B) cleaning_agent 신설 + cleaning 3 등재 (active_orders_filter/member_metrics_validator/missing_value_diagnostic). **collection·cleaning 카테고리 양방향 drift 0** (invisible 55 → 52, 잔존 = metrics 35 + comparison 7 + analysis 6 + normalization 4).
>
> ✅ **작업 ⑰ (2026-06-01) 부분 해소** — metrics 35 등재 (신 metrics_agent 신설, cleaning_agent 패턴 정합) + TaskType.METRIC_CALCULATION 추가 + cognitive.yaml 17→18 + Stage 1·2·3 prompt 분기 (text_preprocessing_agent exclusion). **GoalType.METRIC + TaskType.METRIC_CALCULATION 페어** (KPI 질의 정합). **metrics 카테고리 dual-source drift 100% 해소** (invisible 52 → 17, Q1 진단 77.6%). Manual smoke: source=meta + kpi=ROAS → metrics_agent.roas_overall 정확 매칭.
>
> ✅ **작업 ⑳ (2026-06-01) Q1 본질 진단 100% 해소** — 잔존 17 등재: comparison 7 + analysis 6 = analysis_agent (5→18), normalization 4 = channel_normalizing_agent (2→6). analysis 6 client default cleanup (POC convention, ⑰.A 패턴). **invisible 17 → 0** (Q1 진단 100% 해소). 신 agent 신설 0 (기존 통합, POC convention).
>
> **잔존 (별 작업, scope 변동 0)**:
> - **작업 ⑮**: external 13 collector + RawCollectorBase `_FILE_NO_TO_SOURCE_ID` 21 entries ADR-027 §1 권한 audit (FILE_NO hardcode 패턴 — 작업 ⑭과 별개).
> - **작업 ⑲**: ToolRegistry → team_catalog 자동 sync (sync_team_catalog.py, D3 옵션 B). drift 재발 방지.
> - **DAG audit**: collection → cleaning → metrics 3-hop dependencies.
> - **K-code/S-code taxonomy ADR**: metrics 35 = Pattern A (compact) 19 vs Pattern B (heavyweight) 16 분류 문서화.
> - **MVP+**: normalizers/{client}.yaml 분리 미구현 (현 review_normalizer = 코드 dict alias).

### 4. 산업 표준 매핑

| 패턴 | 본 ADR 대응 |
|---|---|
| Repository Pattern (Fowler 1996) | DataSource (외부 데이터) + ml_model (외부 추론) |
| Dependency Inversion Principle (SOLID D) | Tool ↔ ABC (구현체 swap) |
| Hexagonal Architecture (Ports & Adapters) | 5 주체 = 5 ports |
| Strategy Pattern | ml_model 의 Mock·Llm·Production |

## Decision

### 1. 5 주체 권한 매트릭스

| 주체 | 입력 | 출력 | 인터페이스 (예) | 권한 | 금지 |
|---|---|---|---|---|---|
| **DataSource** | `client_id` + `source_id` | 표준 schema (Pydantic) | `ds.get(client, "orders") → OrdersSchema` | 외부 raw 접근, 컬럼명 매핑·정규화, schema 변환, 결측 처리, mock 폴백 | 계산·집계, Tool 호출, Pipeline 흐름 결정 |
| **Tool** | 표준 schema + 추상 params | 결과 (Pydantic Output) | `tool.execute(data, params, ctx) → Output` | *추상 계산* (sum/avg/groupBy/sort/NLP), **DataSource·ml_model 호출**, output schema 정의 | client 컬럼명 hardcode, 파일 경로 접근, DataSource·ml_model 우회 |
| **ml_model** ⭐ | 입력 (텍스트·이미지·수치) | ML 결과 (감성·점수·분류) | `ml.analyze_sentiment(texts) → SentimentResult` | ML 추론 *추상 인터페이스*. 구현체 swap (Mock·Llm·Production) | 데이터 fetch, 계산·집계 |
| **Pipeline** | YAML 정의 | step 조합 + cache_key | (YAML 파일) | Tool 조합, step 순서, depends_on, cache_key, trigger | 계산·데이터 fetch, 코드 실행 |
| **Maker** | (개발자·Canvas·Agent) | Pipeline 정의 (YAML) | IDE / Canvas / LLM | Pipeline 정의 *생성·수정* | 실행, 데이터 접근, Tool 코드 수정 |

### 2. *호출 그래프* — 단방향 의존

```
[Maker] ──생성──→ [Pipeline YAML]
                       │
                       ▼ (Runner 가 해석)
                  [Pipeline Runner]
                       │
              ┌────────┴────────┐
              ▼                  ▼
         [Tool A]           [Tool B]
              │                  │
         ┌────┴────┐         ┌───┴────┐
         ▼         ▼         ▼        ▼
   [DataSource][ml_model][DataSource][ml_model]
         │         │
         ▼         ▼
   (raw)     (Mock·Llm·Production)
```

**금지 화살표**:
- ❌ Tool → Pipeline (Tool 이 다른 Pipeline 호출)
- ❌ Tool → 다른 Tool (직접 호출 — composer 패턴 금지)
- ❌ DataSource → Tool / ml_model (역방향)
- ❌ ml_model → DataSource / Tool (역방향)
- ❌ Pipeline → DataSource / ml_model (Tool 우회 — Pipeline 이 fetch)
- ❌ Maker → 실행 (Maker 는 정의만)

### 3. ml_model adapter 패턴 — ABC + DI + swap

#### 3.1 영구 영역 (POC v1 부터 production)

```python
# 1. ABC (영구)
class MlModel(ABC):
    @abstractmethod
    async def analyze_sentiment(self, texts: list[str]) -> SentimentResult: ...
    @abstractmethod
    async def score_ai_axes(self, creatives: list[dict]) -> AiAxesResult: ...
    # ... 다른 ML 영역

# 2. Tool (영구 — production 코드)
class SentimentDistributionTool(BaseTool):
    def __init__(self, ml: MlModel):     # ← ABC 타입
        self.ml = ml

    async def execute(self, params, ctx):
        reviews = self.ds.get(ctx.client_id, "reviews")
        result = await self.ml.analyze_sentiment(reviews.texts)
        return {"distribution": result.group_by_sentiment()}
```

#### 3.2 swap 영역 (구현체)

```python
# 3a. MockMlModel (POC v1)
class MockMlModel(MlModel):
    async def analyze_sentiment(self, texts):
        return load_mock("data/ml_mock/sentiment/blooming.json")

# 3b. LlmMlModel (POC v1+ — 현 LLM 인프라)
class LlmMlModel(MlModel):
    async def analyze_sentiment(self, texts):
        return await self.llm.complete(prompt_template(texts))

# 3c. ProductionMlModel (MVP+ 신설)
class ProductionMlModel(MlModel):
    async def analyze_sentiment(self, texts):
        return await self.real_model.predict(texts)        # 진짜 모델

# 4. DI / factory (env 분기)
def build_ml_model(env: str) -> MlModel:
    if env == "poc": return MockMlModel()
    if env == "poc_llm": return LlmMlModel()
    return ProductionMlModel()
```

→ **MVP+ 진입 시 변경 = `ProductionMlModel` 신설 1 파일 + DI 1 줄**. Tool / ABC / 호출 = *건드리지 않음*.

### 4. 표준 schema 위치 — `backend/app/schemas/` (단일 진실 소스)

```
backend/app/
├── schemas/
│   ├── inputs/                  # DataSource 가 반환하는 표준 형식
│   │   ├── orders.py           # OrdersSchema (clumi·blooming·... 공통)
│   │   ├── creatives.py
│   │   └── ...
│   └── outputs/                 # Tool 산출 형식
│       ├── revenue.py          # RevenueOutput
│       └── ...
├── data_sources/               # 어댑터 (schemas/inputs/ import)
├── ml_models/                  # 어댑터 (schemas/outputs/ 일부 import)
└── ...
```

→ Tool = `schemas/inputs/orders.py` 의 `OrdersSchema` import. DataSource = 같은 schema 반환. **단일 진실 소스**.

### 5. 추상 컬럼명 표기 — Pydantic 모델 필드명

```python
# schemas/inputs/orders.py
class OrderRow(BaseModel):
    revenue: int                          # 표준 필드명 (client 무관)
    period: str
    payment_status: Literal["active", "cancelled"]

class OrdersSchema(BaseModel):
    rows: list[OrderRow]

# Tool 코드
class RevenueTotal(BaseTool):
    async def execute(self, params, ctx):
        data: OrdersSchema = self.ds.get(ctx.client_id, "orders")
        return {"value": sum(r.revenue for r in data.rows if r.payment_status == "active")}
                                  ↑ 표준 필드명. client 모름.
```

→ DataSource 가 client 별 컬럼 매핑 (`normalizers/{client}.yaml` 적용).

### 6. client 매핑 — `backend/app/normalizers/{client}.yaml`

```yaml
# normalizers/blooming.yaml
orders:
  revenue: "전환매출(원)"
  period: "결제월"
  payment_status: "주문상태"
  status_map:
    "활성": "active"
    "취소": "cancelled"

creatives:
  ai_axes:
    - {std_name: "ai_sales",   src: "AI_Sales"}
    - {std_name: "ai_short",   src: "AI_Short"}
    - {std_name: "ai_clear",   src: "AI_Clear"}
    - {std_name: "ai_visual",  src: "AI_Visual"}
    - {std_name: "ai_benefit", src: "AI_Benefit"}
  fatigue: "is_fatigue"
```

→ DataSource = 본 config 로드 후 raw → 표준 schema 변환. *client 추가 = config 추가만*.

### 7. 권한 위반 감지 (DC-PERM-* test)

| Test | 영역 | 검증 |
|---|---|---|
| **DC-PERM-1** | Tool 코드 | client 종속 문자열 (한글 컬럼·`naver_*`·`AI_*`) grep → 0 건 |
| **DC-PERM-2** | YAML | `axes:` / `source_column:` 등 hardcode 컬럼 → 권장 패턴 (논리 ID) 만 |
| **DC-PERM-3** | DataSource | 계산 함수 (sum/mean/groupBy) → 0 |
| **DC-PERM-4** | Pipeline (Runner) | 파일 직접 fetch → 0 |
| **DC-PERM-5** | Maker (개발자 YAML) | 실행 함수 호출 → 0 |
| **DC-PERM-6** | Tool | ml_model 우회 (직접 모델 호출) → 0 |

→ Phase 1 진입 시 *CI 통합*. 위반 = build fail.

### 8. POC v1 적용 깊이

| 영역 | POC v1 즉시 | MVP+ |
|---|:---:|:---:|
| 5 주체 권한 *원칙* | ✅ 박제 + 코드 적용 | ✅ + 권한 검사 강화 |
| 표준 schema (Pydantic) | ✅ 신규 schema 만 | ✅ 전체 |
| normalizers/{client}.yaml | ✅ blooming + clumi | ✅ N client |
| ml_models/ (ABC + Mock + Llm) | ✅ Phase 1 신설 | ✅ + Production |
| DC-PERM test | ⚠️ Phase 1 도입 | ✅ CI 통합 |

## Consequences

### 긍정

| 영역 | 효과 |
|---|---|
| Tool 영구 production | MVP+ 진입 시 Tool 코드 변경 0 |
| ml_model swap | DI 1 줄 = MVP+ 진화 |
| client 추가 = config 만 | `normalizers/{client}.yaml` 추가 |
| 권한 위반 자동 감지 | DC-PERM CI |
| ADR-022·023 정합 | 본 ADR = 코드 영역 내부 권한 분담 (직교) |

### 비용

| 영역 | 비용 |
|---|---|
| 신규 layer 3 | `schemas/` + `normalizers/` + `ml_models/` (~7h Phase 1) |
| 기존 Tool 정정 | Batch 1·2·3·4·5 의 Tool 시그니처 변경 (Phase 1) |
| DC-PERM test 작성 | ~3h (Phase 1) |

### 완화

| 비용 | 완화 |
|---|---|
| 신규 layer 시간 ↑ | Phase 1 일정 안 통합 (~27h 총) |
| Tool 정정 ↑ | 본 ADR 적용 후 *영구 production* — 1 회 정정 후 무변경 |

## Alternatives

### A. 4 주체 (ml_model 없음) — *기각*
- 장: 단순
- 단: ML 진입 시 Tool 코드 수정 필요. *MVP+ 진화 비용 ↑*

### B. ml_model = Tool 의 *직접 의존* (ABC 없이) — *기각*
- 장: 더 단순
- 단: swap 불가능. mock ↔ production 교체 시 Tool 수정

### C. ml_model = DataSource 의 *내부 책임* — *기각*
- 장: layer 적음
- 단: DataSource = 데이터 / ML = 추론 — *책임 분리* 모호

### D. 본 ADR (5 주체 + ABC + DI) — *채택*
- 장: 영구 production + swap 가능 + 산업 표준

## Related

| ADR / Spec | 관계 |
|---|---|
| [ADR-022](ADR-022_data_source_workspace_layer_separation.md) | DataSource 책임 *명시 확장* (정규화·schema 매핑·결측 처리·mock 폴백) |
| [ADR-023](ADR-023_pipeline_5_actors_and_trigger_abstraction.md) | 5 *외부* 주체 (Agent·Direct API·Maker·Runner·Validator) 와 **직교**. 본 ADR 의 5 *내부* 주체는 Pipeline 영역 *내부 코드 책임* 분리 |
| [ADR-025](ADR-025_pipeline_customization_3_layer.md) | L3(a) column_mapping = `normalizers/` 구현 |
| [ADR-026](ADR-026_visualization_first_design_flow.md) | step 4·5·7 의 *책임 분담* |
| [ADR-028](ADR-028_hardcode_prohibition_and_raw_classification.md) | hardcode 금지 + B2b ml_mock = ml_model 구현체 반환 |
| [ADR-029](ADR-029_folder_naming_principles.md) | `schemas/`·`normalizers/`·`ml_models/` 폴더 박제 |

## 변경 이력

| 일자 | 내용 |
|---|---|
| 2026-05-28 | 초안 — Accepted. 사용자 통찰 "권한 명확 + tool 다 만든다 + ml_model 파트만 mock" 흡수. **5 주체** (Pipeline·Maker·DataSource·Tool·**ml_model**) 권한 매트릭스 + 호출 그래프 (단방향 + 6 금지 화살표) + ml_model adapter 패턴 (ABC + DI + Mock/Llm/Production swap) + 표준 schema 위치 (`backend/app/schemas/`) + 추상 컬럼명 표기 (Pydantic 필드명) + client 매핑 (`normalizers/{client}.yaml`) + DC-PERM-1~6 test + POC v1 적용 깊이. **Tool 영구 production** / **ml_model 구현체만 swap** 박제. ADR-022 책임 확장 + ADR-023 와 직교 + ADR-025 L3(a) 구체화. |
