# ADR-025: Pipeline Customization 3 Layer — 카테고리·툴·계산식 계층의 진화

## Status

**Accepted** (2026-05-28) — 사용자 통찰 *"세부설정이 카테고리 설정 - 툴 설정 - 툴내부의 미세한 계산식 수정 / 데이터 수정이 될 수 있다"* 의 framing 박제. POC v1 → MVP 진화 영역.

## Context

### 1. 사용자 통찰 (2026-05-28)

68 spec Batch 3 (Channel) V3 게이트 중 사용자 발언:

> "계산할때 placeholder나 혹은 data 주입방식으로 하는건가? 세부설정이 *카테고리 설정 - 툴 설정 - 툴내부의 미세한 계산식 수정 / 데이터 수정* 이 될 수 도 있을것 같아"

→ Pipeline / Tool 시스템에서 **어디부터 *코드 수정* 이 필요한가** = *configurability framing* 부재.

### 2. 기존 ADR 의 layer 정의

| ADR | layer 차원 | 한계 |
|---|---|---|
| ADR-022 (DataSource·Workspace) | 데이터 *경로* 분리 | 가변성 X |
| ADR-023 (5 주체·Trigger) | 작동 *주체* 분리 | 가변성 X |
| ADR-024 (Iterative Refinement) | *작업 방법론* | (메타) |

→ **사용자 가변성 (configurability) 차원** = 본 ADR 의 영역. 기존 ADR 의 빈 영역.

### 3. 현 시스템의 framing (68 Batch 1·2·3 검토)

```
YAML (Pipeline 정의)            Tool 코드 (Python)
─────────────────────           ────────────────────
- ${client} / ${period}    →    self.ds.get(client)
- metrics: ["노출수",...]  →    df[input.metrics]
- channel: ${channel}      →    df.filter(매체==channel)

                                # 계산식 = 코드 *hardcode*:
                                ctr = df["클릭수"] / df["노출수"]
                                roas = df["전환매출"] / df["광고비"]
```

→ **YAML = placeholder 주입** (static) / **계산식 = tool 코드 hardcode**. 외부 client (*다른 컬럼명·다른 산식*) 적응 = 코드 수정 필수 = MVP 진입의 *블로커*.

### 4. 산업 표준 매핑

| 패턴 | 본 ADR 의 대응 |
|---|---|
| dbt models + macros | L3(b) YAML 산식 |
| Apache Superset 의 Calculated columns | L3(b) formula |
| Looker LookML measures | L3(b)+(c) |
| Polars / DuckDB expression | L3(c) DSL |
| OpenAPI parameters | L2 placeholder |

## Decision

### 1. 3 Layer 정의

| Layer | 범위 | 변경 주체 | 변경 비용 | 위치 |
|---|---|---|---|---|
| **L1** 카테고리 | dashboard / 시각화 선택 | end user | 0 (클릭) | Frontend UI |
| **L2** 툴 설정 | placeholder 주입 (`${client}`/`${period}`/metrics) | end user · Canvas user | 낮음 (텍스트) | YAML `inputs` |
| **L3** 계산식·매핑 | CTR 정의·컬럼 매핑·산식 | 개발자 (현) → 사용자 (진화) | 높음 (코드) | Tool 코드 내부 |

→ **L3 만 *코드 수정 필요*** = 본 ADR 의 *진화 대상*.

### 2. L3 의 3 진화 단계

| 단계 | 표현 | 진입 시점 | 적합 use case |
|---|---|:---:|---|
| **(a)** 컬럼 매핑 layer | `column_mapping: {매출: "전환매출(원)"}` | POC v2 + / MVP-2 | 외부 client (다른 컬럼명) |
| **(b)** YAML 산식 | `formula: "클릭수 / 노출수"` | MVP | Canvas 사용자 산식 정의 |
| **(c)** DSL / safe-eval | `formula: pl.col("...")` (Polars) | MVP+ | 복잡 계산·조건·groupBy |

### 3. POC v1·v2·MVP 매트릭스 (사용자 § 형식)

| Layer | POC v1 (현) | POC v2 (Canvas) | MVP-1 (upload) | MVP-2 (외부 API) | MVP+ |
|---|:---:|:---:|:---:|:---:|:---:|
| **L1** 카테고리 | ✅ | ✅ | ✅ | ✅ | ✅ |
| **L2** placeholder | ✅ YAML | ✅ Canvas | ✅ + upload | ✅ + auth scope | ✅ |
| **L3 (a)** 컬럼 매핑 | ❌ | ⏸️ | ⏸️ | ✅ **필수** | ✅ |
| **L3 (b)** YAML 산식 | ❌ | ⏸️ | ❌ | ⏸️ | ✅ |
| **L3 (c)** DSL safe-eval | ❌ | ❌ | ❌ | ❌ | ⏸️ 별도 ADR |
| **Agent Maker** | ❌ | ❌ | ❌ | ❌ | ⏸️ Skills (ADR-023) |

→ **MVP-2 (외부 API) 진입 = L3(a) 필수**. 나머지 = 선택.

### 4. L3 (a) — 외부 client 적응의 *블로커*

#### 현 (POC v1) — 컬럼명 hardcode

```yaml
# 68 §6.1.1 K01
steps:
  - tool: revenue_total
# Tool 코드 내부 — clumi 컬럼 박힘
# df["payment_amount"].sum()    ← "payment_amount" hardcode
```

→ blooming 의 "전환매출(원)" 컬럼 = `revenue_total` 못 씀 (재사용 불가).

#### 진화 (a) — column_mapping

```yaml
steps:
  - tool: revenue_total
    column_mapping:
      payment_amount: "전환매출(원)"      # blooming 표준 매핑
      order_status: "주문상태"
```

→ 같은 tool 이 *다른 client* 의 *다른 컬럼명* 에 적응. **재사용성 ↑·코드 변경 0**.

### 5. L3 (b) — Canvas 친화 (산식 정의)

```yaml
# Canvas 사용자가 새 metric 정의
steps:
  - id: my_custom_metric
    tool: formula_evaluator                # ❌ 신규 (MVP+)
    formula: "전환매출 / 광고비 * 100"
    output_unit: "%"
    output_label: "마진율"
```

→ Canvas 가 *코드 없이* 새 metric 생성 → Canvas (62 spec) 의 *진정한 자유도* 확보.

### 6. L3 (c) — DSL safe-eval (복잡 계산)

```yaml
formula: |
  pl.col("전환매출")
    .filter(pl.col("매체") == "naver")
    .sum() / pl.col("광고비").sum() * 100
```

→ Polars expression / safe-eval. **조건·필터·groupBy 가능**. *Agent Maker (Skills)* 가 LLM 으로 생성하는 형태와 *자연 정합*.

### 7. 어휘 통일

| 단어 | 의미 | layer |
|---|---|:---:|
| **카테고리** | dashboard / 시각화 선택 | L1 |
| **placeholder** | YAML 의 `${var}` 치환 | L2 |
| **column mapping** | client 별 컬럼명 매핑 | L3(a) |
| **formula** | YAML 의 산식 (string 또는 DSL) | L3(b)(c) |
| **expression** | DSL (Polars / safe-eval) | L3(c) |

**금지어** (혼선 회피):
- ❌ "config" (L2·L3 포괄 모호)
- ❌ "param" (L2 placeholder·L3 column_mapping 혼선)
- ❌ "calculation" (L3(b)·(c) 혼선)

### 8. 본 ADR 의 *POC v1 범위 외* 명시

| 영역 | 본 ADR 의 결정 | POC v1 영향 |
|---|---|---|
| L1·L2 | 기존 framing 정합 | 0 |
| L3(a) | MVP-2 진입 시 도입 (별도 ADR-026 후보) | 0 |
| L3(b) | MVP+ (별도 ADR) | 0 |
| L3(c) | MVP++ (별도 ADR) | 0 |

→ **본 ADR = framing 박제만**. 실제 구현 = 각 MVP 단계 진입 시 별도 ADR.

## Consequences

### 긍정

| 영역 | 효과 |
|---|---|
| **외부 client 적응** | L3(a) 만 도입 시 *코드 수정 0* — `column_mapping` 만으로 새 client 추가 |
| **Canvas 자유도** | L3(b) 도입 시 사용자가 *새 metric 직접 정의* — Canvas (62) 의 핵심 가치 실현 |
| **Agent Maker (Skills)** | L3(c) DSL 위에서 LLM 생성 = ADR-023 Skills 박제와 자연 정합 |
| **framing 명시** | layer 별 변경 비용 명확 → 우선순위 결정 근거 |
| **다음 작업자** | "L3(a) 만 우선 도입" 같은 *단계별 의사결정* 가능 |

### 비용

| 영역 | 비용 |
|---|---|
| **L3(a) 도입** | `column_mapping` layer + Tool param 보강 + DataSource 정합 ~10h |
| **L3(b) 도입** | `formula_evaluator` tool + Canvas UI + YAML parser 확장 ~30h |
| **L3(c) 도입** | safe-eval / Polars expression layer + 보안 검토 ~40h |
| **MVP 진입 시** | L3(a) 만 *필수*. (b)(c) 는 *선택* |

### 완화

| 비용 | 완화 |
|---|---|
| L3(a) 시간 ↑ | ADR-022 의 DataSource adapter 패턴 안에 *흡수* 가능 (별 layer 신설 X) |
| L3(b)(c) 시간 ↑ | MVP+ 시점에 *별도 ADR* (ADR-026 / ADR-027 후보) |
| 보안 위험 (c) | RestrictedPython / Polars expression *limited subset* 검토 — 별도 ADR |

## Alternatives

### A. L3 영원히 코드 — *기각*
- 장: 단순
- 단: 외부 client 적응 불가 = MVP-2 진입 X

### B. L3 즉시 (c) DSL — *기각*
- 장: 최대 유연
- 단: POC 단계 over engineering, safe-eval 보안 위험, Canvas 미준비 상태에서 의미 X

### C. L3 = (a) 만 도입, (b)(c) 보류 — *부분 채택*
- 장: 외부 client 적응만 해결 (MVP-2 진입 가능)
- 단: Canvas 의 새 metric = 코드 수정 여전
- 결: **MVP-2 진입 시 (a) 우선**. (b)(c) = MVP+ 별도 결정

### D. Layer 박제 없이 코드만 진화 — *기각*
- 장: 빠름
- 단: framing 정합 X, 누락 영역 발견 어려움, 사용자 통찰 박제 0

### E. L3 = ADR-022/023 안에 흡수 — *기각*
- 장: ADR 수 ↓
- 단: ADR-022 = 데이터 경로, ADR-023 = 주체. **가변성은 *별 차원***. 분리가 framing 정확

## Related

| ADR / Spec | 관계 |
|---|---|
| [ADR-022](ADR-022_data_source_workspace_layer_separation.md) | DataSource ↔ L3(a) column_mapping 흡수 후보 |
| [ADR-023](ADR-023_pipeline_5_actors_and_trigger_abstraction.md) | Canvas (Maker 2) ↔ L3(b) formula / Agent (Maker 3 Skills) ↔ L3(c) DSL |
| [ADR-024](ADR-024_iterative_spec_refinement.md) | 본 ADR 작성 자체 = V1·V2·V3 사이클 적용 사례 |
| [65 spec §14.6](../65_dashboard_pages_v1.0.md) | tool chain = L3 hardcode 의 현 상태 |
| [68 spec §3.1](../68_pipeline_catalog_v1.0.md) | YAML schema = L2 placeholder 의 현 상태 |
| [68 spec §7.2.3](../68_pipeline_catalog_v1.0.md) | T05 9 컬럼 중 4개 파생 (CTR/CVR/CPA/ROAS) = L3 미래 대응 영역 |
| [62 spec](../62_workflow_canvas_design_v1.2.md) | Canvas = L3(b) formula 의 자연 UI |
| **ADR-026** (예정) | L3(a) column_mapping 구현 결정 (MVP-2 진입 시) |

## 변경 이력

| 일자 | 내용 |
|---|---|
| 2026-05-28 | 초안 — Accepted. 사용자 통찰 *"카테고리·툴·계산식 3 계층"* 흡수. L1·L2·L3 명시 + L3 의 3 진화 단계 (a) column_mapping / (b) YAML 산식 / (c) DSL safe-eval + POC v1·v2·MVP 매트릭스 박제. L3(a) = 외부 client 적응 *블로커* 박제 (MVP-2 진입 시 ADR-026 후보). L3(b) = Canvas (62) 의 핵심 자유도. L3(c) = Agent Maker (Skills, ADR-023) 와 자연 정합. **본 ADR = framing 박제만 (POC v1 영향 0)**. 어휘 통일 (placeholder / column mapping / formula / expression) + 금지어 (config / param / calculation). ADR-022 (DataSource) ·023 (5 주체) 위의 *사용자 가변성 framing* 4 번째 차원. |
| 2026-05-28 (정정) | **본문 변경 X (ADR-000 정합)**. 사용자 통찰 (R3·R6) — *L3(a) column_mapping = "MVP+ 진화" → **"POC v1 부터 권한 분담의 일부"**) 재정정*. [ADR-027](ADR-027_five_actor_permission_separation.md) 신설로 *DataSource 가 `normalizers/{client}.yaml` 적용* = L3(a) 의 *POC v1 구현체*. [ADR-028](ADR-028_hardcode_prohibition_and_raw_classification.md) 의 *Hardcode 금지 원칙* = L3 영역의 *원칙* 박제. 본 ADR의 §3 (L3 3 진화 단계) 표 의 (a) column_mapping = "POC v1 + " (즉시 적용) 으로 *해석 정정*. (b) YAML 산식 / (c) DSL = MVP+ 유지. |
