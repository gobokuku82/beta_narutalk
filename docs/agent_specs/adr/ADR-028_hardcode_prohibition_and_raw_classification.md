# ADR-028: Hardcode 금지 원칙 + raw data 4 분류 + LLM 분석 영역

## Status

**Accepted** (2026-05-28) — 사용자 통찰 *"hardcode 는 이제 어디에서도 사용하지 않아야 한다"* + *"계산이 완료된 data 도 추후 raw 에 포함"* + *"LLM 분석은 쓸꺼야"* 박제. ADR-026 step 6 (raw 검증) 의 *판단 기준* + ADR-027 권한 위반 *판단 기준*.

## Context

### 1. 사용자 통찰 (2026-05-28)

> "1. data = 기존의 데이터에서 raw data가 아닌 결과값이 있는건, 실제 raw data로 간주한다 ( 업체 제공 / 클라이언트가 타 업체에서 받아서 입력 등등 ). 결과가 하드코딩인 경우 = 수정이 필요하다. ... data - tool / pipeline 설계는 면밀하게 검토해봐야 할것 같아. **하드코딩은 이제 어디에서도 사용하지 않아야 한다.**"
> "2. blooming data = tool 기능시연을 위한 하드코딩기반의 데이터 라는게 포인트"

추가 통찰 (R4):
> "raw data에서 1개 더 추가해줘. 계산이 완료된 data도 추후 raw data에 포함시킬꺼야."

추가 통찰 (R4 후속):
> "지금 ml은 없어서 이거 필요한 부분은 일단 표시해줘. 여기는 ml_mock을 사용해야 할것 같아. 그리고 **llm 분석은 쓸꺼야**."

→ 3 통찰 통합 박제:
1. Hardcode 전역 금지
2. raw data = 4 분류 (외부 그 자체 + mock + tool 산출 + 외부 산출)
3. LLM 분석 = 활용 (ml_model 의 한 구현체)

### 2. 기존 ADR 의 빈 영역

| ADR | 영역 | 본 ADR 관계 |
|---|---|---|
| ADR-022·023·025 | 시스템 *구조* | (구조) |
| ADR-024 | *검증 사이클* | (검증) |
| ADR-026 | *작업 순서* | (순서) |
| ADR-027 | *권한 분담* | (책임) |
| **ADR-028 (본)** | *원칙·분류* | ⭐ 판단 기준 |

→ ADR-027 = *누가* 한다 / 본 ADR = *무엇을 허용·금지* 한다.

### 3. 현 시스템의 *위반* 사례

| 위치 | 위반 | 분류 |
|---|---|---|
| 68 Batch 2·3 YAML | `월예산(원)`·`매체` 같은 한글 컬럼 hardcode | A. client 종속 |
| 68 Batch 4 review_trends | `감성`·`주요키워드` 컬럼 = mock 결과값 박힘 | B2b. ml_mock |
| 68 Batch 5 creatives | `AI_Sales` 등 5 컬럼 = mock 결과값 박힘 | B2b. ml_mock |
| 68 Batch 5 YAML | `axes: [AI_Sales, ...]` 컬럼명 직접 박힘 | A. client 종속 |
| 68 Batch 5 K21 | `is_fatigue` 컬럼 = mock 판정 박힘 | B2b. ml_mock |

→ 본 ADR 적용 후 *모두 정정*.

## Decision

### 1. Hardcode 3 분류

| 분류 | 정의 | 처리 |
|---|---|---|
| **A. client 종속 hardcode** | 특정 client 의 컬럼명·파일명·식별자 박힘 | ❌ **금지** — DataSource 가 정규화 (ADR-027) |
| **B. mock data hardcode** | mock data 에 *결과값 사전 박힘* | ⚠️ **표시 필요** (B2b ml_mock) — MVP+ 시 진짜 산출로 진화 |
| **C. 시스템 상수 hardcode** | 비-client 상수 (예: `PERIOD_REGEX`) | ✅ **허용** — 상수만 |

### 2. 금지 영역별 예시

| 영역 | 금지 (현 spec) | 권장 |
|---|---|---|
| **Tool 코드** | `df["전환매출(원)"].sum()` | `df.revenue.sum()` (Pydantic 필드명) |
| **YAML inputs** | `axes: [AI_Sales, AI_Short, ...]` | `metric_key: "ai_axes"` (논리 ID) |
| **YAML inputs** | `source_column: "주요키워드"` | `source_logical: "keywords"` |
| **YAML inputs** | `metrics: ["노출수", "클릭수"]` | `metrics: ["impressions", "clicks"]` (표준 명) |
| **YAML cache_key** | `"blooming_*.json"` | `"${client}/*.json"` (변수) |
| **DataSource 코드** | `if client == "blooming"` 분기 | `self.config.path_for(client)` (config 분리) |
| **Pipeline name** | `dashboard_v1_*` | ✅ **허용** (사용자 친화 — §5 예외) |

### 3. Hardcode 발견 시 *처리 절차*

```
1. 발견 (grep / code review / DC-PERM test)
   ↓
2. 분류 (A/B/C)
   ↓
3a. A 분류 → 즉시 정정 (DataSource normalizers/ 신설·갱신)
3b. B 분류 → 표시 박제 (B2b ml_mock 명시) + MVP+ 진화 계획
3c. C 분류 → 검토 (상수 의도 확인) → 허용 또는 const 모듈
   ↓
4. 사이클 (ADR-024 V1·V3 + ADR-026 step 7 재진입)
```

### 4. raw data 4 분류 ⭐

| 분류 | 정의 | 출처 | 예 | 처리 |
|---|---|---|---|---|
| **B1. 진짜 raw** | 외부가 *그 자체로* 준 raw | naver API / 업체 CSV | clumi orders·customers | DataSource 정규화 → Tool 재계산 |
| **B2. mock raw (POC 한정)** | 시연용 가상 — *2 세부* | ↓ | ↓ | ↓ |
| **B2a. 단순 mock** | 가짜 값 (가상 숫자·텍스트) | 개발자 mock 생성 | blooming campaigns 의 가상 캠페인명 | spec 박제 + MVP+ 실 데이터 |
| **B2b. ml_mock** ⭐ | *ML 결과 자리* 의 mock | mock data 생성기 | creatives 의 `AI_Sales` / review_trends 의 `감성`·`주요키워드` / `is_fatigue` | spec 박제 + ml_model 구현체 `MockMlModel` 가 반환 (ADR-027 §3) |
| **B3. tool 산출물** | 우리 시스템 tool 의 산출 — **raw 가 아님** | DataSource·Tool | `data/{client}/cleaned·computed/*.json` | Workspace 관리 (ADR-022) |
| **B4. 외부 산출 input** ⭐ | 외부가 *이미 계산한* 결과를 *입력* 으로 받음 | GA4 보고서 / 외부 BI export / 사용자 수작업 / 3자 분석 도구 | (가상) 외부 KPI 표 업로드 | DataSource 정규화 + **재계산 X** + *메타 정보 보존*. 명명 미정 (`precomputed input` 후보) |

→ B1·B4 = 외부 / B2 = mock / B3 = 우리 산출.

### 5. B2b ml_mock 의 *진짜 ML 진화* 경로 (ADR-027 정합)

```
[POC v1]
   Tool → ml_model.analyze() → MockMlModel → ml_mock_data 반환

[MVP+]
   Tool → ml_model.analyze() → ProductionMlModel → 실 추론
                              ↑ 이 줄만 swap (DI 1 줄)
```

| ML 영역 | POC v1 ml_mock_data 위치 | MVP+ 진짜 model |
|---|---|---|
| sentiment (감성) | `data/ml_mock/sentiment/{client}.json` | `sentiment_analyzer` (M11, 65 §15.4 A-R01) |
| keywords (NLP) | `data/ml_mock/keywords/{client}.json` | `keyword_extractor` (NLP tool, 65 §15.2 I-M12 진화) |
| ai_axes (CV/LLM) | `data/ml_mock/ai_axes/{client}.json` | `ai_axis_scorer` (M13, 65 §15.4 A-R03) |
| fatigue (anomaly) | `data/ml_mock/fatigue/{client}.json` | `creative_fatigue_diagnostic` (A-D04) |

### 6. LLM 분석 *별 영역* — ml_model 의 한 구현체

| 영역 | 의미 | POC v1 활용? |
|---|---|---|
| **LLM 인프라 (현)** | Agent (Cognitive/Planning/Response) 의 LLM | ✅ 활용 중 |
| **LLM 분석 (신규)** | *분석 작업* 에 LLM 사용 (O05 추천 등) — `LlmMlModel` 구현체 | ✅ **활용 결정** ⭐ |
| **ML 모델 (진화)** | CV/NLP/sentiment 의 학습된 모델 — `ProductionMlModel` | ❌ MVP+ |

#### 6.1 ml_model 3 구현체

```
ml_model ABC
   ├── MockMlModel       (POC v1 — ml_mock_data 반환)
   ├── LlmMlModel        (POC v1+ — 현 LLM 인프라 활용) ⭐ 실 사용
   └── ProductionMlModel (MVP+ — 진짜 학습 모델)
```

→ **3 구현체 모두 *같은 ABC***. Tool = *어떤 구현체* 인지 모름. DI 가 결정.

#### 6.2 O05 AI 추천 (Batch 6 Cost+AI) = LlmMlModel 첫 모범 사례

```yaml
# Batch 6 O05 pipeline (예고)
steps:
  - id: cost_data_load
    tool: blooming_cost_collectors  # 다중 source

  - id: cost_aggregate
    tool: cost_kpi_aggregator       # 수치 집계 (B3 산출)

  - id: recommendation_generate
    tool: ai_recommendation_tool    # ⭐ LlmMlModel 호출 step
    inputs:
      cost_summary: ${cost_aggregate.result}
      methodology: "광고 최적화 추천"
```

→ `ai_recommendation_tool` = `self.ml.generate_recommendation(...)`. ml_model = `LlmMlModel` (DI 주입). MVP+ 시 더 정교한 `ProductionRecommendationModel` 로 swap 가능.

### 7. 어휘 통일

| 단어 | 의미 |
|---|---|
| **raw** | 외부 입력 (B1·B2·B4) |
| **tool 산출** | 우리 시스템 산출 (B3) — raw 아님 |
| **ml_mock** | B2b — ml_model 구현체 MockMlModel 의 반환 자리 |
| **ml_mock_data** | `data/ml_mock/*` 의 사전 박힌 fixture |
| **LLM 분석** | LlmMlModel 구현체 활용 |
| **진짜 ML** | ProductionMlModel (MVP+) |

**금지어**:
- ❌ "AI 결과" (ML / LLM 혼선)
- ❌ "raw 박힘" (B2b 명시 X — *ml_mock* 사용)

### 8. 본 spec 의 *POC v1 적용*

| 영역 | POC v1 즉시 | MVP+ |
|---|:---:|:---:|
| Hardcode A 분류 금지 | ✅ 신규 코드 적용 + 기존 정정 | ✅ |
| B2b ml_mock 표시 | ✅ 박제 (Phase 1) | ✅ |
| B4 명명 결정 | ⏸️ 보류 | ✅ MVP-1 진입 시 |
| ml_models/ ABC + Mock + Llm | ✅ Phase 1 신설 | ✅ + Production |
| LLM 분석 (LlmMlModel) | ✅ O05 추천 (Batch 6) | ✅ |
| DC-PERM-1·2 (hardcode 검사) | ⚠️ Phase 1 도입 | ✅ CI 통합 |

### 9. 예외 영역 (hardcode 허용)

| 예외 | 이유 |
|---|---|
| **Pipeline name** (예: `dashboard1_kpi_revenue`) | 사용자 친화 + 검색 용이 |
| **methodology ID** (M01·M02 등) | 시스템 식별자 (client 무관) |
| **시스템 상수** (예: `PERIOD_REGEX`) | 비-client 상수 |
| **POC 단계 mock 폴백** (`mock_source_dir`) | 명시적 옵션. MVP 부재 |

## Consequences

### 긍정

| 영역 | 효과 |
|---|---|
| 외부 client 적응 | 코드 수정 0 (`normalizers/{client}.yaml` 만 추가) |
| ML 진화 | Tool 영구 + ml_model 구현체 swap (ADR-027) |
| LLM 활용 | 현 인프라 위에서 분석 작업 가능 (O05 추천) |
| 다음 작업자 가이드 | 4 분류 + 3 hardcode 분류 = 명확 판단 기준 |

### 비용

| 영역 | 비용 |
|---|---|
| 기존 batch 정정 | Batch 1~5 spec 정정 (R7) |
| Phase 1 신설 | `normalizers/`·`ml_models/`·`data/ml_mock/` (~7h) |
| ml_mock_data 생성 | 4 영역 fixture (~2h) |

### 완화

| 비용 | 완화 |
|---|---|
| 정정 ↑ | spec 표면만 (R7) + 코드 정정 = Phase 1 |
| Phase 1 ↑ | 기존 ~15h + 추가 ~7h = ~22h (1 sprint 안) |

## Alternatives

### A. raw 3 분류 (B4 없음) — *기각*
- 장: 단순
- 단: MVP+ 외부 BI 연동 시 *재정의* 필요

### B. Hardcode 부분 허용 — *기각*
- 장: 정정 비용 ↓
- 단: 사용자 명시 위배 ("어디에서도 사용 X")

### C. LLM = 별 layer (ml_model 외부) — *기각*
- 장: 명확
- 단: Tool 입장에서 *2 ABC* (ml_model + llm_analysis) → 복잡. ml_model 통합이 더 깔끔

### D. 본 ADR (4 분류 + 3 hardcode + LLM = ml_model 구현체) — *채택*

## Related

| ADR / Spec | 관계 |
|---|---|
| [ADR-022](ADR-022_data_source_workspace_layer_separation.md) | B3 tool 산출 = Workspace 관리 |
| [ADR-025](ADR-025_pipeline_customization_3_layer.md) | L3(a) column_mapping = A 분류 금지 구현 |
| [ADR-026](ADR-026_visualization_first_design_flow.md) | step 6 raw 검증 = 본 ADR 4 분류 *판단 기준* |
| [ADR-027](ADR-027_five_actor_permission_separation.md) | ml_model adapter = B2b ml_mock 구현체 |
| [ADR-029](ADR-029_folder_naming_principles.md) | `data/ml_mock/` 폴더 박제 |
| [65 spec §15.4](../65_dashboard_pages_v1.0.md) | 분석 layer (D3) = MVP+ 진짜 ML 진입 |

## 변경 이력

| 일자 | 내용 |
|---|---|
| 2026-05-28 | 초안 — Accepted. 사용자 통찰 *"hardcode 어디에서도 사용 X + raw 4 분류 + LLM 분석 활용"* 흡수. **Hardcode 3 분류** (A client 종속 금지 / B mock 표시 / C 상수 허용) + 금지 영역별 예시 + 처리 절차. **raw 4 분류** (B1 진짜 / B2 mock {B2a 단순·B2b ml_mock} / B3 tool 산출 / B4 외부 산출 *명명 미정*). **ml_mock 진화 경로** (ADR-027 ml_model adapter — Mock → Production swap). **LLM 분석 = LlmMlModel 구현체** (O05 추천 첫 모범). 어휘 통일 + 금지어 + POC v1 적용 깊이 + 예외 영역. ADR-022 (B3 Workspace) + ADR-025 (L3(a)) + ADR-026 (step 6 판단) + ADR-027 (ml_model adapter) 정합. |
