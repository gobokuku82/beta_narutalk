# 68. Pipeline Catalog v1.0

> **시각화별 Pipeline 정의 카탈로그** — 65 spec 의 *지도* 와 ADR-023 의 *5 주체* 위에서, *52 시각화 × 52 pipeline* 의 1:1 매핑 (Pipeline 경계 = A, 사용자 결정 2026-05-27).

---

## 0. 메타

| 항목 | 내용 |
|---|---|
| 작성일 | 2026-05-27 |
| 위치 | `docs/agent_specs/68_pipeline_catalog_v1.0.md` |
| 진실 소스 | **코드** (`backend/app/pipelines/flows/*.yaml` — 향후 신설) + 본 spec = 카탈로그 |
| 관련 spec | [65 dashboard pages](65_dashboard_pages_v1.0.md) (시각화 인벤토리 + tool chain), [63 backend contract](63_frontend_backend_contract_v1.0.md) (API 명세) |
| 관련 ADR | [ADR-023](adr/ADR-023_pipeline_5_actors_and_trigger_abstraction.md) (5 주체 + Trigger 추상화), [ADR-022](adr/ADR-022_data_source_workspace_layer_separation.md) (DataSource/Workspace) |
| 짝 spec | [63 §2.3.3 + §8.6](63_frontend_backend_contract_v1.0.md) — Pipeline API + Invocation 시퀀스 (Phase 0.5 A1, 2026-05-28 완성) |

---

## 🗂️ 문서 입구 인덱스

| § | 라벨 | 제목 | 상태 | 한 줄 |
|:---:|:---:|---|:---:|---|
| §1 | meta | 본 문서의 역할 | ✅ | 5 페이지 보완 작업의 Pipeline 정의 단일 진실 소스 |
| §2 | decisions | 사용자 결정 사항 | ✅ | Pipeline 경계 / DSL / Batch 전략 |
| §3 | dsl | Pipeline DSL 명세 (YAML schema) + cache framing + ADR 적용 | ✅ | 필수·옵션 필드 + 변수 + 예시 + §3.6 cache = Workspace 자산 + §3.7 ADR-026·027·028·029 통합 framing |
| §4 | conventions | 작성 컨벤션 | ✅ | 명명·폴더·step·trigger |
| §5 | mapping | 전체 매핑표 (52 시각화 × 52 pipeline) | ✅ | 카테고리별·batch별·상태 |
| §6 | batch-1 | Batch 1 — Dashboard1 21 pipeline YAML | ✅ | 실제 명세 (이미 backend tool 존재) |
| §7 | batches | Batch 2·3·4·5·6 ✅ | 🟢 | **6 batch × 52 pipeline 전체 완료** (Dashboard v1·Channel·Trend·Creative·Cost+O05 AI) |
| §8 | history | 변경 이력 | ✅ | — |

**범례**: ✅ 완료 / ⏳ 예정 (사용자 검토 후 batch 별 진입)

---

## 1. 본 문서의 역할

### 1.1 3 목적

| # | 목적 | 위치 |
|---|---|---|
| **P1** | Pipeline DSL (YAML) 의 *공통 schema* 정의 | §3 |
| **P2** | 52 시각화 ↔ 52 pipeline 1:1 *매핑* | §5 |
| **P3** | 각 pipeline 의 *실제 YAML 명세* (단계별 batch) | §6·§7 |

### 1.2 65 spec 과의 분리

| 영역 | 65 spec | 본 spec (68) |
|---|---|---|
| 시각화 인벤토리 | ✅ §2·§3·§10 | (참조) |
| Tool chain (low-level) | ✅ §14.6 composition | (참조) |
| 방법론 카탈로그 | ✅ §14 (M01~M21) | (참조) |
| **Pipeline 정의 (mid-level)** | (없음) | ✅ 본 spec |
| 5 주체 / Trigger | (참조 — §13.3) | (참조 — ADR-023) |
| Tool 카탈로그 (D1·D2·D3) | ✅ §15 | (참조) |

→ 65 = *지도*, 68 = *Pipeline 카탈로그* (별도 spec). 65 비대 회피.

### 1.3 5 페이지 보완 작업의 첫 referential

5 v1 페이지 작업자가:
1. 65 spec §14.6 에서 *tool chain* 확인
2. **본 68 spec §5 에서 *pipeline 매핑* 확인**
3. 본 68 spec §6·§7 에서 *YAML 명세* 복사·수정
4. `backend/app/pipelines/flows/{name}.yaml` 신설
5. Runner 실행 (Phase 1 신설 후)

---

## 2. 사용자 결정 사항 (2026-05-27)

| # | 결정 | 채택 |
|:---:|---|---|
| 1 | **Pipeline 경계** | **A** — 시각화 1개 = Pipeline 1개 (52 pipeline) |
| 2 | **DSL 포맷** | **YAML** (3 Maker 공통 산출물, Canvas/Agent 출력 가능) |
| 3 | **첫 진입 분량** | **모든 시각화 매핑** (단계별 batch — 작업 분할) |

### 2.1 옵션 A 선택 근거

| 옵션 | 평가 |
|---|---|
| **A** ✅ 시각화 1:1 (52 pipeline) | *세밀한 제어* + 부분 갱신 자연 + cache 중복 일부 (수용 가능) |
| B 대시보드 1:1 (6 pipeline) | 단순하나 부분 갱신 어려움 — 1 시각화 갱신 위해 21 step 모두 실행 |
| C 카테고리 그룹 (6~10) | 중간. 묶음 결정 모호 |
| D Hybrid | 가장 합리적이나 *복잡* — POC v1 단계 over engineering |

→ POC = 단순함 우선. **A 채택**. cache 중복 = 같은 cache key 사용으로 자연 해결.

### 2.2 단계별 batch 전략

| Batch | 범위 | tool 상태 | 추정 |
|:---:|---|---|---|
| **1** ✅ | Dashboard1 21 pipeline | ✅ 모든 tool 존재 (Sprint 16) | ~1h |
| 2 | Dashboard v1 6 pipeline | ❌ 신설 (Batch 5 + 14 collector + 5 metrics) | ~3h |
| 3 | Channel 3 pipeline | ❌ 신설 | ~2h |
| 4 | Trend 8 pipeline | ❌ 신설 | ~3h |
| 5 | Creative 6 pipeline | ❌ 신설 | ~3h |
| 6 | Cost 7 pipeline + O05 AI 추천 | ❌ 신설 (가장 복잡) | ~4h |
| **합계** | **52 pipeline** | | **~16h ≈ 2일** |

→ 본 commit = Batch 1 (Dashboard1 21) 만. 나머지 = 사용자 검토 후 단계별 진입.

---

## 3. Pipeline DSL 명세 (YAML schema)

### 3.1 필수 필드

```yaml
name: dashboard1_kpi_revenue          # snake_case, 고유 (cache_key 와 1:1)
visualization_id: K01                  # 65 spec §10 의 ID
category: dashboard1                   # dashboard1 | dashboard_v1 | channel | trend | creative | cost
client: ${client}                      # 변수 — Runner 가 주입
period: ${period}                      # 변수 (선택)

trigger:
  type: manual                         # manual | upload | cron | webhook | agent
  cron: null                           # cron 시 명시

steps:
  - id: orders_load
    tool: orders_collector
    inputs:
      client: ${client}
    outputs:
      raw_orders: data_source

  - id: revenue_compute
    tool: RevenueTotal
    inputs:
      client: ${client}
      period: ${period}
    outputs:
      result: ./computed/S001_revenue_total_${period}.json
    depends_on: [orders_load]

validator:
  schema: RevenueOutput
  expected:
    value_min: 0
    value_max: 1e10
  fail_policy: alert                   # alert | rollback | continue

cache:
  layer: computed                      # cleaned | computed | analyzed (MVP)
  key_template: "S001_revenue_total_${period}.json"
  ttl_seconds: null                    # null = 영구

owner: developer                       # developer | canvas | agent (3 Maker)
```

### 3.2 옵션 필드

```yaml
description: "Dashboard1 의 총 매출 KPI"   # 사람 친화 설명
methodology_id: M01                         # 65 §14 의 방법론 ID (단일 값 집계)
priority: P0                                # P0 | P1 | P2 | P3
estimated_seconds: 5                        # 실행 시간 예상
on_failure:
  retry: 0                                  # 재시도 횟수 (POC = 0)
  fallback: null                            # 실패 시 대체 cache 사용 여부
tags: [revenue, kpi, dashboard1]
```

### 3.3 변수 (Runner 가 주입)

| 변수 | 의미 | 예시 |
|---|---|---|
| `${client}` | TopBar 선택 클라이언트 | "clumi", "blooming" |
| `${period}` | 분석 기간 | "2026-04", "2026-Q1" |
| `${session_id}` | (MVP+ agent 한정) Session 격리 | UUID |
| `${run_id}` | Pipeline 실행 인스턴스 ID | UUID |

### 3.4 step 의존성 (DAG)

```yaml
steps:
  - id: A
    ...
  - id: B
    depends_on: [A]      # A 완료 후 B
  - id: C
    depends_on: [A]      # A 완료 후 C (B 와 병렬)
  - id: D
    depends_on: [B, C]   # B·C 모두 완료 후 D
```

POC v1 = 선형만 (depends_on = 1개) 우선. DAG 본격 = MVP+.

### 3.5 trigger.type 별 의미

| type | 의미 | POC | MVP |
|---|---|:---:|:---:|
| `manual` | 버튼 클릭 (사용자) | ✅ | ✅ |
| `upload` | 사용자 파일 업로드 | — | ✅ |
| `cron` | 주기 스케줄 | — | ✅ |
| `webhook` | 외부 push | — | ✅ |
| `agent` | LLM 동적 요청 (Skills) | — | ⏸️ (별도 ADR) |

### 3.6 본 spec 의 "cache" 의미 — 사용자 framing 박제 (2026-05-28) ⭐

> **사용자 통찰** (Batch 4 V3 게이트): *"raw data 가 있고 정제 결과 / 계산 결과... 이런식으로 raw 데이터의 *변환 결과를 서버 내부에 계속 저장* 하는 걸 cache 라고 한 건가?"*

#### 3.6.1 사실 정합 (4/4)

| 사용자 표현 | 본 spec 실체 |
|---|---|
| raw data | `data/{client}/raw/*.csv` (외부 주입) |
| 정제 결과 / 계산 결과 | `cleaned/` (cleaning 산출) / `computed/` (집계 산출) — ADR-022 Workspace layer |
| raw 의 *변환 결과* | tool 산출물 = raw 의 어떤 변환 |
| 서버 내부에 *계속* 저장 | 디스크 영속 (POC v1 `ttl_seconds: null`) |

→ **사용자 표현이 본 spec 의 "cache" 보다 *framing 정확***.

#### 3.6.2 일반 "cache" 와의 차이

| 측면 | 일반 cache (Redis·브라우저) | 본 spec 의 "cache" |
|---|---|---|
| 위치 | RAM | **디스크 파일** |
| 휘발성 | 휘발 (TTL) | **영속** (POC v1) |
| 본질 | 원본의 *임시 사본* (부수적) | **변환 결과 그 자체** (주요 자산) |
| 손실 가능성 | OK (재생성) | 손실 = 정답값 손실 (재계산 비싸거나 불가능 — 외부 raw 갱신 시) |

→ **본 spec 의 "cache" ≠ 통상 cache**. 본질 = ***Workspace 의 변환 산출물***.

#### 3.6.3 더 정확한 용어 (참고)

| 용어 | 의미 |
|---|---|
| **Workspace 자산** | ADR-022 의 *Workspace* 정합 |
| **변환 산출물** | 사용자 표현 직역 |
| **분석 자산** | 시스템 가치 측면 |
| ~~cache~~ | 통상 의미 = 임시 사본 (오해 유발) |

→ "cache" 단어 = *hit/miss 동작 측면만 강조*. 의미 framing 측면 = **"Workspace 자산"** 이 더 정확.

#### 3.6.4 단어 유지 결정 (2026-05-28 사용자 결정)

| 항목 | 결정 |
|---|---|
| 단어 "cache" 전면 정정 | ❌ 보류 (변경 비용 ↑ — 68/63/dashboard1.py 50+ 곳) |
| 본 §3.6 주석 박제 | ✅ **본 결정** — 변경 비용 0, framing 정합 ↑ |
| MVP+ 진입 시 어휘 정정 | ⏸️ 검토 (Workspace 자산 / 산출물) |

→ **본 spec 의 "cache" 단어를 만나면 → *§3.6 의 정의* 로 해석**. 향후 모든 spec 작업자에게 *framing 통일 가이드*.

#### 3.6.5 시스템 본질 정렬

```
raw 외부 주입
    ↓ (cleaning tool)
cleaned 자산  ← *값진 산출물 #1* (= "cleaned cache")
    ↓ (computed tool)
computed 자산 ← *값진 산출물 #2* (= "computed cache")
    ↓ (analyzed tool — MVP+)
analyzed 자산 ← *값진 산출물 #3*
    ↓ (decision tool — MVP+)
decisions     ← *값진 산출물 #4*
```

→ 각 layer 의 *변환 결과* = **시스템의 *주요 자산***. memory `project_core_value_data_transformation` 의 *"raw → 분석 변환 파이프라인 = 시스템 본질"* 와 정렬.

### 3.7 본 spec 에 적용된 ADR — 통합 framing (2026-05-28) ⭐

> 본 §3.6 의 cache 박제와 함께, Phase 0.5 R1~R7 사이클에서 박제된 **신규 ADR 4종** 의 본 spec 적용 명시.

#### 3.7.1 적용 ADR 매트릭스

| ADR | 영역 | 본 spec 적용 위치 |
|---|---|---|
| **ADR-026** Visualization-First Design Flow (10 step) | 작업 방법론 | 각 Batch §7.x 의 작성 순서 (시각화 → raw 역방향) |
| **ADR-027** 5 주체 권한 분리 (+ ml_model) | 코드 책임 분담 | YAML steps[] 의 tool 분리 + ml_model adapter (Batch 4·5·6 ml_mock) |
| **ADR-028** Hardcode 금지 + raw 4 분류 + LLM | 원칙·분류 판단 기준 | YAML inputs hardcode 영역 + B2b ml_mock 표시 + B4 외부 산출 |
| **ADR-029** 폴더 명명 원칙 | 메타 가이드 | Phase 1 신설 폴더 (`schemas/`·`normalizers/`·`ml_models/`·`data/ml_mock/`) |

#### 3.7.2 Batch 별 *ADR 적용 평가* (ADR-026 step 1~7 기준)

| Batch | step 1·2·3 | step 6 raw 검증 | ADR-027 권한 | ADR-028 hardcode | 평가 |
|---|---|---|---|---|---|
| **Batch 1** (Dashboard1 clumi) | ✅ 시각화 → tool | ✅ PASS (B1 진짜 raw, 정답 17) | ⚠️ Tool 컬럼명 hardcode (Phase 1 정정) | ⚠️ 동일 | 🟢 모범 (기존) |
| **Batch 2** (Dashboard v1) | ✅ | ⚠️ 한글 컬럼 hardcode (A 분류) | ⚠️ normalizers/blooming.yaml 신설 필요 | ⚠️ A 분류 정정 | 🟠 부분 위반 |
| **Batch 3** (Channel) | ✅ | ⚠️ 동일 | ⚠️ 동일 | ⚠️ 동일 | 🟠 부분 위반 |
| **Batch 4** (Trend) | ⚠️ (감성·키워드 mock 가정) | 🔴 B2b ml_mock (C08·C12·O03) | 🔴 ml_models/ 신설 필요 | 🔴 B2b 표시 + ml_mock_data 분리 | 🔴 명백 위반 — **R7 spec 정정** |
| **Batch 5** (Creative) | ⚠️ (AI 5축 mock 가정) | 🔴 B2b ml_mock (C11·K21) + axes hardcode | 🔴 ml_models/ + axes 추상화 | 🔴 동일 | 🔴 명백 위반 — **R7 spec 정정** |

→ **Batch 4·5 = 본 R7 commit 에 spec 정정 동반**. Batch 2·3 = R7 표시 + Phase 1 코드 정정. Batch 1 = 정합 확인.

#### 3.7.3 Phase 1 적용 영역 (ADR 코드 구현)

| ADR | Phase 1 신설·정정 |
|---|---|
| ADR-027 | `backend/app/schemas/inputs/` + `outputs/` + `backend/app/normalizers/{client}.yaml` + `backend/app/ml_models/{base,mock,llm}.py` |
| ADR-028 | `data/ml_mock/{sentiment,ai_axes,keywords,fatigue}/{client}.json` + Tool 의 client 컬럼 정정 |
| ADR-029 | 위 폴더 명명 적용 |
| DC-PERM-1~6 | Phase 1 도입 (CI 통합 MVP+) |

→ Phase 1 추가 시간 = ~7h (기존 15h + 5h schemas + 7h ml_models = ~27h ≈ 3.5일).

#### 3.7.4 F 사이클 (Batch 6 Cost+AI) — 본 ADR 첫 모범 사례

| 영역 | 이전 Batch | F 사이클 |
|---|---|---|
| 작성 순서 | raw → 시각화 (역방향) | **ADR-026 step 1~10 적용** |
| YAML inputs | 컬럼 hardcode | 논리 ID + normalizers/ |
| ml_mock | 표시 부재 | B2b 명시 |
| O05 추천 | (가설) | **LlmMlModel 호출** = LLM 분석 첫 활용 |

→ F 사이클 = **본 4 ADR 의 *통합 모범 사례***.

---

## 4. 작성 컨벤션

### 4.1 명명

```
backend/app/pipelines/flows/
  ├── dashboard1/
  │   ├── kpi_revenue.yaml              # K01
  │   ├── kpi_ad_cost.yaml              # K02
  │   ├── ...
  │   ├── mom_revenue.yaml              # M01
  │   ├── segment_grade.yaml            # T01
  │   ├── ...
  ├── dashboard_v1/
  │   ├── kpi_campaign_total.yaml       # K10
  │   ├── ...
  ├── channel/
  ├── trend/
  ├── creative/
  └── cost/
      ├── ...
      └── ai_recommendation.yaml        # O05 — 가장 복잡
```

### 4.2 파일명 패턴

```
{category}_{section}_{shortname}.yaml

예시:
  dashboard1_kpi_revenue.yaml    → name: dashboard1_kpi_revenue
  cost_ai_recommendation.yaml    → name: cost_ai_recommendation
```

→ **파일명 = name 필드** 와 일치. cache_key prefix 와 정합.

### 4.3 step ID 컨벤션

```
{영역}_{동작}

예시:
  - orders_load                # raw → 메모리
  - revenue_compute            # 단일 값 집계
  - channel_aggregate          # groupBy
  - validator_check            # 검산 (자동 추가)
```

→ snake_case + 동사형. 가독성 ↑.

### 4.4 outputs 경로 컨벤션

```
outputs:
  raw_xxx:    data_source                              # DataSource 거치는 raw (저장 X)
  cleaned_xxx: ./cleaned/{name}_${period}.json         # cleaned/ layer 저장
  result:     ./computed/{cache_key_template}.json     # computed/ layer 저장
  analyzed:   ./analyzed/{name}_${period}.json         # (MVP+) analyzed/ layer
```

### 4.5 validator 옵션

```yaml
validator:
  schema: PydanticOutputModelName              # Pydantic 모델 매핑
  expected:                                     # 산출 값 범위
    value_min: 0
    value_max: 1e10
    rows_min: 1                                 # rows 결과 시
  reference:                                    # 정답 비교 (선택)
    file: ./tests/fixtures/expected_K01.json
  fail_policy: alert | rollback | continue
```

POC = `alert` 만. `rollback` = MVP+.

---

## 5. 전체 매핑표 (52 시각화 × 52 pipeline)

### 5.1 Dashboard1 (Sprint 16 — 21 pipeline)

> 모든 tool 이미 존재 (Sprint 16 21 metrics + 17 cleaning/preprocessing). YAML 만 신설.

| 시각화 ID | Pipeline 이름 | category | Batch | 상태 | Methodology |
|:---:|---|:---:|:---:|:---:|:---:|
| K01 | `dashboard1_kpi_revenue` | dashboard1 | 1 | ✅ | M01 |
| K02 | `dashboard1_kpi_ad_cost` | dashboard1 | 1 | ✅ | M01 |
| K03 | `dashboard1_kpi_roas` | dashboard1 | 1 | ✅ | M01 |
| K04 | `dashboard1_kpi_cac` | dashboard1 | 1 | ✅ | M01 |
| K05 | `dashboard1_kpi_promotion_revenue` | dashboard1 | 1 | ✅ | M01 |
| K06 | `dashboard1_kpi_promotion_roas` | dashboard1 | 1 | ✅ | M01 |
| K07 | `dashboard1_kpi_new_members` | dashboard1 | 1 | ✅ | M01 |
| K08 | `dashboard1_kpi_aov` | dashboard1 | 1 | ✅ | M01 |
| K09 | `dashboard1_kpi_signup_conversion` | dashboard1 | 1 | ✅ | M01 |
| M01 | `dashboard1_mom_revenue` | dashboard1 | 1 | ✅ | M02 |
| M02 | `dashboard1_mom_aov` | dashboard1 | 1 | ✅ | M02 |
| M03 | `dashboard1_mom_repurchase` | dashboard1 | 1 | ✅ | M02 |
| M04 | `dashboard1_mom_new_members` | dashboard1 | 1 | ✅ | M02 |
| C01 | `dashboard1_segment_grade_timeseries` | dashboard1 | 1 | ✅ | M03 |
| C02 | `dashboard1_kpi_ad_cost_bar` ⚠️ K02 cache 재사용 | dashboard1 | 1 | ✅ | M04 |
| C03 | `dashboard1_segment_age` | dashboard1 | 1 | ✅ | M04 |
| T01 | `dashboard1_segment_grade` | dashboard1 | 1 | ✅ | M05 |
| T02 | `dashboard1_segment_channel` | dashboard1 | 1 | ✅ | M09 |
| T03 | `dashboard1_segment_category` | dashboard1 | 1 | ✅ | M09 |
| O01 | `dashboard1_segment_member_guest` | dashboard1 | 1 | ✅ | M09 |
| O02 | `dashboard1_segment_unknown_share` | dashboard1 | 1 | ✅ | M01 |

> **C02 ↔ K02 cache 재사용**: 같은 `ad_cost_total_{period}.json` cache. C02 pipeline 은 K02 cache 가 있으면 *load only*, 없으면 K02 와 같은 chain 실행. cache 중복 0.

### 5.2 Dashboard v1 (Batch 2 — 6 pipeline) ✅ 2026-05-28

| 시각화 ID | Pipeline 이름 | Batch | 상태 | Methodology |
|:---:|---|:---:|:---:|:---:|
| K10 | `dashboard_v1_kpi_campaign_total` | 2 | ✅ | M01 |
| K11 | `dashboard_v1_kpi_campaign_active` | 2 | ✅ | M01 |
| K12 | `dashboard_v1_kpi_budget_total` | 2 | ✅ | M01 |
| K13 | `dashboard_v1_kpi_target_roas_avg` | 2 | ✅ | M01 |
| C04 | `dashboard_v1_daily_performance_line` | 2 | ✅ | M03 |
| T04 | `dashboard_v1_table_campaigns` | 2 | ✅ | M09 |

> 신규 tool 7개 (2 collector + 4 metric + 1 active-count) Phase 1 동반. cache 공유 도식 §7.1.9.

### 5.3 Channel (Batch 3 — 3 pipeline) ✅ 2026-05-28

| 시각화 ID | Pipeline 이름 | Batch | 상태 | Methodology |
|:---:|---|:---:|:---:|:---:|
| C05 | `channel_bar_metrics` | 3 | ✅ | M04 |
| C06 | `channel_funnel` | 3 | ✅ | M07 |
| T05 | `channel_table_detailed` | 3 | ✅ | M04 |

> 신규 tool 6개 (2 collector + 1 cleaning + 3 metric). cleaning 공유 도식 §7.2.6.

### 5.4 Trend (Batch 4 — 8 pipeline) ✅ 2026-05-28

| 시각화 ID | Pipeline 이름 | Batch | 상태 | Methodology | 비고 |
|:---:|---|:---:|:---:|:---:|---|
| K14 | `trend_kpi_impressions` | 4 | ✅ | M01 | cache 공유 (K14~K17) |
| K15 | `trend_kpi_clicks` | 4 | ✅ | M01 | ↑ 같은 cache |
| K16 | `trend_kpi_conversions` | 4 | ✅ | M01 | ↑ 같은 cache |
| K17 | `trend_kpi_ad_cost` | 4 | ✅ | M01 | ↑ 같은 cache |
| C07 | `trend_area_3metric` | 4 | ✅ | M03 | daily_perf 공유 |
| C08 | `trend_pie_sentiment` | 4 | ✅ | M09 | 1-step (T04 패턴) |
| C12 | `trend_bar_keywords_top10` | 4 | ✅ | M12 | NLP-lite |
| O03 | `trend_cards_recent_reviews` | 4 | ✅ | M08 | period_filter 공유 (C12) |

> 신규 tool 6개 (`blooming_daily_performance_collector` Batch 2 재사용). cache 공유 도식 §7.3.9.

### 5.5 Creative (Batch 5 — 7 pipeline) ✅ 2026-05-28

> 헤더 *6 → 7* 정정 (compact recovery doc 2026-05-28 WARN 동반).

| 시각화 ID | Pipeline 이름 | Batch | 상태 | Methodology | 비고 |
|:---:|---|:---:|:---:|:---:|---|
| K18 | `creative_kpi_total` | 5 | ✅ | M01 | cache 공유 (K18·K21) |
| K19 | `creative_kpi_ctr_avg` | 5 | ✅ | M01 | cache 공유 (K19·K20) |
| K20 | `creative_kpi_roas_avg` | 5 | ✅ | M01 | ↑ 같은 cache |
| K21 | `creative_kpi_fatigue` | 5 | ✅ | M01 | ↑ K18 같은 cache |
| C11 | `creative_radar_ai_axis` | 5 | ✅ | M06 | raw 사전박힘 (AI_Sales·Short·Clear·Visual·Benefit) |
| O04 | `creative_cards_top9` | 5 | ✅ | M08 | sort ROAS desc |
| T06 | `creative_table_ab_tests` | 5 | ✅ | M09 | ab_tests 별 source |

> 신규 tool 7개 (2 collector + 5 metric). cache 공유 도식 §7.4.8.

### 5.6 Cost (Batch 6 — 7 pipeline) ✅ 2026-05-28

| 시각화 ID | Pipeline 이름 | Batch | 상태 | Methodology | 비고 |
|:---:|---|:---:|:---:|:---:|---|
| K22 | `cost_kpi_budget_total` | 6 | ✅ | M01 | budget 공유 (K22·K23·C09·C10) |
| K23 | `cost_kpi_exec_rate_avg` | 6 | ✅ | M01 | ↑ K22 cache 공유 |
| K24 | `cost_kpi_keyword_metrics` | 6 | ✅ | M01 | keyword 공유 (K24·T07) |
| C09 | `cost_pie_channel_share` | 6 | ✅ | M05 | budget 공유 / L3(a) hardcode |
| C10 | `cost_bar_budget_stacked` | 6 | ✅ | M10 | budget 공유 / L3(a) hardcode |
| T07 | `cost_table_keyword_top12` | 6 | ✅ | M08 | keyword 공유 + 경쟁 Badge |
| **O05** ⭐ | **`cost_ai_recommendation`** (베타 0.001 — LLM 단순 호출) | 6 | ✅ | M21 | LlmMlModel / K22·K23·K24 cache 재활용 / 로드맵 §7.5.10 |

> 신규 tool 9개 (2 collector + 1 cleaning + 5 metric + 1 recommendation). O05 = 지속 업그레이드 (§7.5.10). cache 공유 §7.5.9.

### 5.7 합계

| 카테고리 | Pipeline 수 | Batch | 상태 |
|---|---:|:---:|:---:|
| Dashboard1 | 21 | 1 | ✅ |
| Dashboard v1 | 6 | 2 | ✅ |
| Channel | 3 | 3 | ✅ |
| Trend | 8 | 4 | ✅ |
| Creative | 7 | 5 | ✅ |
| Cost (O05 AI 추천 포함) | 7 | 6 | ✅ |
| **합계** | **52** | — | ✅ **전 batch 완료** |

> **합계 정정 (2026-05-28, compact recovery doc WARN 동반)**: 52 시각화 = 52 pipeline (1:1, 사용자 결정 A). 이전 "53" 표기는 C02 (K02 cache 재사용) 를 *중복 계산* 한 오류 — C02 는 Dashboard1 21 안에 *이미 포함* (별 pipeline 이나 K02 와 cache 공유). Cost 의 "7 + 1" 표기도 O05 가 Cost 7 안에 *포함* (K22·K23·K24·C09·C10·T07·O05 = 7) → 정정. **6 batch × 52 pipeline 전체 완료**.

---

## 6. Batch 1 — Dashboard1 (21 pipeline YAML)

### 6.1 KPI 9 (K01~K09)

#### 6.1.1 K01 — 총 매출

```yaml
name: dashboard1_kpi_revenue
visualization_id: K01
category: dashboard1
description: "Dashboard1 의 총 매출 KPI (단일 값)"
methodology_id: M01
priority: P0
client: ${client}
period: ${period}

trigger:
  type: manual

steps:
  - id: orders_load
    tool: orders_collector
    inputs:
      client: ${client}

  - id: revenue_compute
    tool: RevenueTotal
    inputs:
      client: ${client}
      period: ${period}
    depends_on: [orders_load]

validator:
  schema: RevenueOutput
  expected:
    value_min: 0
  reference:
    file: ./tests/fixtures/expected_S001.json
  fail_policy: alert

cache:
  layer: computed
  key_template: "S001_revenue_total_${period}.json"
  ttl_seconds: null

owner: developer
tags: [revenue, kpi, dashboard1]
```

#### 6.1.2 K02 — 총 광고비 (5 collector 협력)

```yaml
name: dashboard1_kpi_ad_cost
visualization_id: K02
category: dashboard1
description: "Dashboard1 의 총 광고비 KPI (5 매체 합산)"
methodology_id: M01
priority: P0
client: ${client}
period: ${period}

trigger:
  type: manual

steps:
  - id: meta_ads_load
    tool: meta_ads_performance_collector
    inputs: {client: ${client}}
  - id: naver_sa_load
    tool: naver_searchad_collector
    inputs: {client: ${client}}
  - id: naver_advoost_load
    tool: naver_advoost_collector
    inputs: {client: ${client}}
  - id: kakao_biz_load
    tool: kakao_bizmessage_collector
    inputs: {client: ${client}}
  - id: naver_talktalk_load
    tool: naver_talktalk_collector
    inputs: {client: ${client}}

  - id: ad_cost_aggregate
    tool: AdCostAggregator
    inputs:
      client: ${client}
      period: ${period}
    depends_on: [meta_ads_load, naver_sa_load, naver_advoost_load, kakao_biz_load, naver_talktalk_load]

validator:
  schema: AdCostOutput
  expected:
    value_min: 0
  fail_policy: alert

cache:
  layer: cleaned
  key_template: "ad_cost_total_${period}.json"

owner: developer
tags: [ad_cost, kpi, dashboard1, aggregation]
```

#### 6.1.3 K03~K09 — 동일 패턴 요약

| name | tool | cache key | 의존 |
|---|---|---|---|
| `dashboard1_kpi_roas` | `RoasOverall` | `S004_roas_overall_${period}.json` | K01 + K02 cache load |
| `dashboard1_kpi_cac` | `CacOverall` | `S032_cac_overall_${period}.json` | K02 + K07 cache load |
| `dashboard1_kpi_promotion_revenue` | `PromotionRevenue` | `S002_promotion_revenue_${period}.json` | orders + promotions |
| `dashboard1_kpi_promotion_roas` | `PromotionRoas` | `S005_promotion_roas_${period}.json` | K05 + 프로모션 광고비 |
| `dashboard1_kpi_new_members` | `NewMembersMonthly` | `S069_new_members_${period}.json` | customers |
| `dashboard1_kpi_aov` | `AovMonthly` | `S048_aov_${period}.json` | orders |
| `dashboard1_kpi_signup_conversion` | `SignupConversion` | `S067_signup_conversion_${period}.json` | ga4_traffic + customers |

→ *YAML 명세 = K01 패턴 복사 + 필드만 변경*. Batch 1 진행 시 일괄 작성.

### 6.2 MoM 4 (M01~M04)

#### 6.2.1 M01 — MoM 매출

```yaml
name: dashboard1_mom_revenue
visualization_id: M01
category: dashboard1
description: "전월 대비 매출 비교"
methodology_id: M02
priority: P0
client: ${client}
period_a: ${period_a}      # 기준
period_b: ${period_b}      # 비교

trigger:
  type: manual

steps:
  - id: revenue_a
    tool: RevenueTotal
    inputs:
      client: ${client}
      period: ${period_a}
  - id: revenue_b
    tool: RevenueTotal
    inputs:
      client: ${client}
      period: ${period_b}
  - id: mom_compare
    tool: MomRevenue
    inputs:
      client: ${client}
      period_a: ${period_a}
      period_b: ${period_b}
    depends_on: [revenue_a, revenue_b]

validator:
  schema: MomRevenueOutput
  fail_policy: alert

cache:
  layer: computed
  key_template: "S001mom_revenue_${period_a}_to_${period_b}.json"

owner: developer
tags: [mom, revenue, dashboard1]
```

#### 6.2.2 M02·M03·M04 — 동일 패턴

| name | tool | cache key |
|---|---|---|
| `dashboard1_mom_aov` | `AovMom` | `S048mom_aov_${a}_to_${b}.json` |
| `dashboard1_mom_repurchase` | `RepurchaseMom` | `S028mom_repurchase_${a}_to_${b}.json` |
| `dashboard1_mom_new_members` | `NewMembersMom` | `S069mom_new_members_${a}_to_${b}.json` |

### 6.3 Segment 7 (C01·C03·T01·T02·T03·O01·O02)

| name | tool | M# | cache key |
|---|---|:---:|---|
| `dashboard1_segment_grade_timeseries` (C01) | `GradeTimeseries` | M03 | `S045_grade_timeseries.json` (period 없음) |
| `dashboard1_segment_age` (C03) | `AgeSegment` | M04 | `S037_age_segment.json` (period 없음) |
| `dashboard1_segment_grade` (T01) | `GradeRevenue` | M05 | `S046_grade_revenue_${period}.json` |
| `dashboard1_segment_channel` (T02) | `ChannelAttributionNormalizer` | M09 | `channel_normalized_${period}.json` |
| `dashboard1_segment_category` (T03) | `CategoryMultiDistributor` | M09 | `category_distributed_${period}.json` |
| `dashboard1_segment_member_guest` (O01) | `MemberGuestSplitter` | M09 | `orders_split_${period}.json` |
| `dashboard1_segment_unknown_share` (O02) | `UnknownRevenueShare` | M01 | `S054_unknown_share_${period}.json` |

### 6.4 광고비 Bar (C02 — K02 cache 재사용)

```yaml
name: dashboard1_kpi_ad_cost_bar
visualization_id: C02
category: dashboard1
description: "5 매체 광고비 BarChart — K02 cache 재사용 (단순 load)"
methodology_id: M04
priority: P0
client: ${client}
period: ${period}

trigger:
  type: manual

steps:
  - id: ad_cost_load_or_compute
    tool: AdCostAggregator                              # 같은 tool
    inputs:
      client: ${client}
      period: ${period}
    # cache hit 시 (K02 가 먼저 실행됨) → 즉시 load
    # cache miss 시 → K02 와 같은 chain 실행

validator:
  schema: AdCostOutput
  fail_policy: alert

cache:
  layer: cleaned
  key_template: "ad_cost_total_${period}.json"            # K02 와 동일 key

owner: developer
tags: [ad_cost, chart, dashboard1, cache_shared]
```

> **cache 재사용 패턴**: 같은 `cache.key_template` 사용 → cache hit 시 양쪽 pipeline 모두 load only. 데이터 중복 0.

### 6.5 Batch 1 — Validator 통과 기준

| 영역 | 기준 |
|---|---|
| schema 일치 | 모든 Pydantic Output (S001~S069·Ad·Channel·Category·Member·Unknown) |
| **정답값 17 보존** | Sprint 16 박제 ([clumi_백엔드_tool_구현_완료보고서_2026-05-25.md](../reports/clumi_백엔드_tool_구현_완료보고서_2026-05-25.md)) 와 일치 |
| 실행 시간 | 각 pipeline < 5초 (cache miss 시) |
| cache hit 시 | < 100ms |
| 동시 실행 | 같은 client+period 의 동시 호출 시 1개만 실행 (중복 방지) |

### 6.6 Batch 1 — Test 시나리오

```
1. data/clumi/raw/*.csv 비우기
2. POST /api/admin/pipelines/run/dashboard1_kpi_revenue?client=clumi&period=2026-04
3. 응답: run_id + status="completed"
4. Workspace 확인: data/clumi/computed/S001_revenue_total_2026-04.json 존재
5. Validator 통과 (정답값 17 의 매출 항목 비교)
6. Frontend Dashboard1 페이지 새로고침 → K01 KPI 카드 정답 표시
```

→ **Phase 1 진입 시** 본 시나리오로 *기본 작동 확인*.

---

## 7. Batch 2~6 (후속 commit, ⏳)

> 사용자 검토 후 batch 별 진입. 각 batch 완료 시 본 spec 의 §7.x 추가.

### 7.1 Batch 2 — Dashboard v1 (6 pipeline YAML) ✅ 2026-05-28

> **데이터 source**: `data/blooming/mock_data_{campaigns,daily_performance}.csv` (실제 컬럼명 한글 — 캠페인ID·월예산(원)·목표ROAS(%)·날짜·광고비(원)·전환매출(원) 등). 정답값 17 보존 대상 **X** (clumi 만) → validator.reference 없음.
> **의존 신규 tool 7개** (65 §15.2 D2 I-C03·I-C04·I-M01·I-M02·I-M03·I-M04·I-M05 + active 필터 I-N? 별도 검토). **Phase 1 동반 신설**.
> **K11 design 결정 (2026-05-28)**: 65 §14.6.3 의 *3 tool chain* (filter + count) 을 *단일 metric tool* `campaign_count_active` 로 흡수 (`상태=='진행중'` 내부 처리) — 별도 `active_campaigns_filter` 신설 회피. tool 수 7→7 (filter 1 절약, T04 projection 별도 X).

#### 7.1.1 K10 — 총 캠페인 수

```yaml
name: dashboard_v1_kpi_campaign_total
visualization_id: K10
category: dashboard_v1
description: "blooming 캠페인 총수 — campaigns.csv 행수 (period 무관)"
methodology_id: M01
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: campaigns_load
    tool: blooming_campaigns_collector              # ❌ 신설 — 65 §15.2 I-C03
    inputs:
      client: ${client}

  - id: campaign_count_compute
    tool: campaign_count_total                       # ❌ 신설 — 65 §15.2 I-M01
    inputs:
      client: ${client}
    depends_on: [campaigns_load]

validator:
  schema: CampaignCountOutput                        # ❌ Phase 1 신설 Pydantic
  expected:
    value_min: 0
  fail_policy: alert

cache:
  layer: computed
  key_template: "campaign_count_total.json"          # period 무관

owner: developer
tags: [campaign, kpi, dashboard_v1, blooming]
```

#### 7.1.2 K11 — 진행중 캠페인 수

```yaml
name: dashboard_v1_kpi_campaign_active
visualization_id: K11
category: dashboard_v1
description: "blooming 캠페인 중 상태=='진행중' 행수 (M01 + 내부 필터)"
methodology_id: M01
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: campaigns_load
    tool: blooming_campaigns_collector
    inputs:
      client: ${client}

  - id: campaign_active_count
    tool: campaign_count_active                      # ❌ 신설 — 65 §15.2 I-M02 (필터+카운트 통합)
    inputs:
      client: ${client}
    depends_on: [campaigns_load]

validator:
  schema: CampaignCountOutput
  expected:
    value_min: 0
  fail_policy: alert

cache:
  layer: computed
  key_template: "campaign_count_active.json"

owner: developer
tags: [campaign, kpi, dashboard_v1, blooming, filter]
```

#### 7.1.3 K12 — 총 월예산

```yaml
name: dashboard_v1_kpi_budget_total
visualization_id: K12
category: dashboard_v1
description: "blooming 캠페인 월예산(원) 합산"
methodology_id: M01
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: campaigns_load
    tool: blooming_campaigns_collector
    inputs:
      client: ${client}

  - id: budget_total_compute
    tool: campaign_budget_total                      # ❌ 신설 — 65 §15.2 I-M03
    inputs:
      client: ${client}
    depends_on: [campaigns_load]

validator:
  schema: BudgetTotalOutput                          # ❌ Phase 1 신설
  expected:
    value_min: 0
  fail_policy: alert

cache:
  layer: computed
  key_template: "campaign_budget_total.json"

owner: developer
tags: [campaign, kpi, budget, dashboard_v1, blooming]
```

#### 7.1.4 K13 — 평균 목표 ROAS

```yaml
name: dashboard_v1_kpi_target_roas_avg
visualization_id: K13
category: dashboard_v1
description: "blooming 캠페인 목표ROAS(%) 평균"
methodology_id: M01
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: campaigns_load
    tool: blooming_campaigns_collector
    inputs:
      client: ${client}

  - id: target_roas_avg_compute
    tool: campaign_target_roas_avg                   # ❌ 신설 — 65 §15.2 I-M04
    inputs:
      client: ${client}
    depends_on: [campaigns_load]

validator:
  schema: TargetRoasAvgOutput                        # ❌ Phase 1 신설
  expected:
    value_min: 0
  fail_policy: alert

cache:
  layer: computed
  key_template: "campaign_target_roas_avg.json"

owner: developer
tags: [campaign, kpi, roas, dashboard_v1, blooming]
```

#### 7.1.5 C04 — 일별 성과 LineChart (광고비 / 전환매출)

```yaml
name: dashboard_v1_daily_performance_line
visualization_id: C04
category: dashboard_v1
description: "daily_performance.csv 를 날짜별 광고비(원)·전환매출(원) 2 시리즈로 집계"
methodology_id: M03                                  # 시계열
priority: P0
client: ${client}
period: ${period}                                    # YYYY-MM (선택 — 없으면 전체)

trigger:
  type: manual

steps:
  - id: daily_perf_load
    tool: blooming_daily_performance_collector       # ❌ 신설 — 65 §15.2 I-C04
    inputs:
      client: ${client}

  - id: daily_perf_aggregate
    tool: daily_performance_aggregator               # ❌ 신설 — 65 §15.2 I-M05
    inputs:
      client: ${client}
      period: ${period}
      metrics: ["광고비", "전환매출"]                 # 2 시리즈
    depends_on: [daily_perf_load]

validator:
  schema: DailyPerformanceLineOutput                 # ❌ Phase 1 신설
  expected:
    rows_min: 1                                       # 최소 1 일자
  fail_policy: alert

cache:
  layer: cleaned                                      # 시계열 = cleaned
  key_template: "daily_performance_line_${period}.json"

owner: developer
tags: [daily, line, dashboard_v1, blooming, timeseries]
```

#### 7.1.6 T04 — 캠페인 테이블 (7 컬럼 projection)

```yaml
name: dashboard_v1_table_campaigns
visualization_id: T04
category: dashboard_v1
description: "캠페인 목록 7 컬럼 (ID·이름·유형·상태·예산·ROAS·담당자) — 별도 metric tool X"
methodology_id: M09                                  # 분포·테이블
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: campaigns_load
    tool: blooming_campaigns_collector
    inputs:
      client: ${client}
    # collector 산출물 = campaigns.csv 전 컬럼.
    # frontend 가 7 컬럼만 select (collector 변경 X, projection 별 tool 없음).

validator:
  schema: CampaignsTableOutput                       # ❌ Phase 1 신설 — 7 필드 보장
  expected:
    rows_min: 1
  fail_policy: alert

cache:
  layer: cleaned                                      # raw 정합 = cleaned 동급
  key_template: "campaigns_table.json"

owner: developer
tags: [campaign, table, dashboard_v1, blooming, projection]
```

> **T04 = collector 결과 직접 사용** (별도 metric step 없음). Pipeline 단계 *최단* = 1 step. *cache hit 시* `campaigns.csv` 부재해도 즉시 응답.

#### 7.1.7 Batch 2 — Validator 통과 기준

| 영역 | 기준 |
|---|---|
| schema 일치 | 6 신규 Pydantic Output (`CampaignCountOutput` ×2 / `BudgetTotalOutput` / `TargetRoasAvgOutput` / `DailyPerformanceLineOutput` / `CampaignsTableOutput`) |
| 정답값 비교 | **없음** (blooming = mock data, clumi 정답 17 와 무관). `expected.value_min` / `rows_min` 만 |
| 실행 시간 | 각 pipeline < 3초 (cache miss 시) — campaigns ≈ 수십 행 / daily_perf ≈ 수백~수천 행 |
| cache hit | < 100ms |
| 동시 실행 | K10·K11·K12·K13·T04 는 같은 `campaigns_load` step → cache 자연 공유 (5 pipeline 1 collector 실행) |

#### 7.1.8 Batch 2 — Test 시나리오

```
1. data/blooming/mock_data_{campaigns,daily_performance}.csv 존재 확인
2. POST /api/admin/pipelines/run/dashboard_v1_kpi_campaign_total?client=blooming
3. 응답: run_id + status="completed" (수초 내)
4. Workspace 확인: data/blooming/computed/campaign_count_total.json 존재
5. 응답 schema = CampaignCountOutput {value: N, ...}
6. Frontend Dashboard v1 페이지 새로고침 → K10 KPI 카드 값 표시
7. 6 pipeline 모두 위 동일 패턴으로 검증
8. cache 공유 검증: K10 실행 후 K11 실행 시 campaigns_load step skip (또는 즉시 load)
```

#### 7.1.9 Batch 2 cache 공유 관계 도식

```
              ┌─────────────────────────────────────────┐
              │  blooming_campaigns_collector            │
              │  (campaigns.csv → 메모리)                │
              └────┬────────────────────────────────────┘
                   │ 공유 입력
       ┌───────────┼───────────┬──────────┬──────────────┐
       ▼           ▼           ▼          ▼              ▼
     K10         K11          K12        K13            T04
   total      active        budget      roas         table
                                                  (no metric)

              ┌─────────────────────────────────────────┐
              │  blooming_daily_performance_collector    │
              │  (daily_performance.csv → 메모리)        │
              └────┬────────────────────────────────────┘
                   │
                   ▼
                  C04
              (line chart)
```

→ **2 collector + 5 metric + T04 projection = 6 pipeline**. Runner 의 step-level cache (Phase 1) 가 `campaigns_load` 결과를 공유 → 5 pipeline 의 collector 호출 1회로 수렴.

### 7.2 Batch 3 — Channel (3 pipeline YAML) ✅ 2026-05-28

> **데이터 source**: `data/blooming/mock_data_{channel_performance,conversion_funnel}.csv` (실제 컬럼명 한글 — 매체·노출수·클릭수·CTR(%)·전환수·CVR(%)·광고비(원)·ROAS(%)·CPA(원)·전환매출(원) + 퍼널단계·매체·유입수·이전단계대비(%)·전체대비(%)).
> **의존 신규 tool 6개** (Phase 1 동반): 2 collector + 1 cleaning + 3 metric.
> **cleaning layer 공유 (핵심)**: C05·T05 모두 `channel_aggregate_dedup` (`'합계'`/`'전체'` 행 제외) 의 산출 (`cleaned/channel_perf_clean.json`) 위에서 작동. Runner step-level cache 로 *cleaning 1회 → 2 metric 분기*.

#### 7.2.1 C05 — 매체별 막대 (노출/클릭/전환 3 시리즈)

```yaml
name: channel_bar_metrics
visualization_id: C05
category: channel
description: "매체별 노출수·클릭수·전환수 3 시리즈 BarChart (합계·전체 행 제외)"
methodology_id: M04
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: channel_perf_load
    tool: blooming_channel_performance_collector   # ❌ 신설 — 65 §15.2 I-C05
    inputs:
      client: ${client}

  - id: channel_dedup
    tool: channel_aggregate_dedup                   # ❌ 신설 — 65 §15.2 I-CL02 (cleaning)
    inputs:
      client: ${client}
    depends_on: [channel_perf_load]

  - id: channel_metrics_compute
    tool: channel_metrics_aggregator                # ❌ 신설 — 65 §15.2 I-M06
    inputs:
      client: ${client}
      metrics: ["노출수", "클릭수", "전환수"]
    depends_on: [channel_dedup]

validator:
  schema: ChannelMetricsBarOutput                   # ❌ Phase 1 신설
  expected:
    rows_min: 1                                      # 최소 1 매체
  fail_policy: alert

cache:
  layer: computed
  key_template: "channel_metrics_bar.json"

owner: developer
tags: [channel, bar, blooming, dedup_shared]
```

#### 7.2.2 C06 — 전환 퍼널 (수평 bar)

```yaml
name: channel_funnel
visualization_id: C06
category: channel
description: "퍼널단계별 유입수 + max 대비 비율 정규화 (수평 bar)"
methodology_id: M07
priority: P0
client: ${client}
channel: ${channel}                                  # 선택 — 매체 필터

trigger:
  type: manual

steps:
  - id: funnel_load
    tool: blooming_conversion_funnel_collector       # ❌ 신설 — 65 §15.2 I-C06
    inputs:
      client: ${client}

  - id: funnel_normalize
    tool: conversion_funnel_normalizer               # ❌ 신설 — 65 §15.2 I-M07
    inputs:
      client: ${client}
      channel: ${channel}                            # null = 전 매체 합산
    # ${channel} 변수 주입 = 63 §2.3.3.4 의 PipelineRunRequest.variables
    # (POST body 의 {"variables": {"channel": "naver"}} → ${channel} 치환)
    # cache_key 의 ${channel} 도 동일 치환. null → "all" 문자열로 정규화 (Phase 1 결정)
    depends_on: [funnel_load]

validator:
  schema: ConversionFunnelOutput                     # ❌ Phase 1 신설
  expected:
    rows_min: 1                                      # 최소 1 단계
  fail_policy: alert

cache:
  layer: computed
  key_template: "V07_funnel_${channel}.json"

owner: developer
tags: [channel, funnel, blooming, normalize]
```

#### 7.2.3 T05 — 매체 상세 테이블 (9 컬럼)

```yaml
name: channel_table_detailed
visualization_id: T05
category: channel
description: "매체별 9 컬럼 (매체·노출·클릭·CTR·전환·CVR·CPA·광고비·ROAS) — C05 의 dedup 공유"
methodology_id: M04
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: channel_perf_load
    tool: blooming_channel_performance_collector     # ← C05 와 step 공유 (cache hit)
    inputs:
      client: ${client}

  - id: channel_dedup
    tool: channel_aggregate_dedup                    # ← C05 와 step 공유 (cache hit)
    inputs:
      client: ${client}
    depends_on: [channel_perf_load]

  - id: channel_detailed_compute
    tool: channel_detailed_metrics                   # ❌ 신설 — 65 §15.2 I-M08
    inputs:
      client: ${client}
    # 9 컬럼 중 4개 (CTR/CVR/CPA/ROAS) = *파생 계산*:
    #   CTR = 클릭수/노출수, CVR = 전환수/클릭수,
    #   CPA = 광고비/전환수, ROAS = 전환매출/광고비
    # 나머지 5개 (매체·노출·클릭·전환·광고비) = CSV 직접 로드
    # 상세 = 65 §15.2 I-M08
    depends_on: [channel_dedup]

validator:
  schema: ChannelDetailedTableOutput                 # ❌ Phase 1 신설 — 9 필드 보장
  expected:
    rows_min: 1
  fail_policy: alert

cache:
  layer: computed
  key_template: "channel_detailed_table.json"

owner: developer
tags: [channel, table, blooming, dedup_shared]
```

> **C05 + T05 cache 공유**: 같은 `channel_perf_load` + `channel_dedup` step 사용. Runner step-level cache (Phase 1) 시 *collector + dedup 1회 → 2 metric 분기* 로 자연 수렴.

#### 7.2.4 Batch 3 — Validator 통과 기준

| 영역 | 기준 |
|---|---|
| schema 일치 | 3 신규 Pydantic Output (`ChannelMetricsBarOutput` / `ConversionFunnelOutput` / `ChannelDetailedTableOutput`) |
| 정답값 비교 | **없음** (blooming = mock). `expected.rows_min` 만 |
| 실행 시간 | 각 pipeline < 2초 (cache miss 시) — channel_perf 6 행 / funnel 21 행 (소규모) |
| cache hit | < 100ms |
| dedup 결과 | C05·T05 모두 `cleaned/channel_perf_clean.json` 공유 (`매체 not in ['합계','전체']`) |

#### 7.2.5 Batch 3 — Test 시나리오

```
1. data/blooming/mock_data_{channel_performance,conversion_funnel}.csv 존재 확인
2. POST /api/admin/pipelines/run/channel_bar_metrics?client=blooming
3. 응답: run_id + status="completed"
4. Workspace 확인: data/blooming/cleaned/channel_perf_clean.json + computed/channel_metrics_bar.json
5. T05 호출 시 cleaned/channel_perf_clean.json cache hit → collector + dedup skip
6. POST /api/admin/pipelines/run/channel_funnel?client=blooming&channel=naver
7. computed/V07_funnel_naver.json 산출
8. Frontend Channel 페이지 새로고침 → C05·C06·T05 모두 표시
```

#### 7.2.6 Batch 3 cache 공유 도식

```
       ┌──────────────────────────────────────┐
       │ blooming_channel_performance_collector│
       └──────────────┬───────────────────────┘
                      │
                      ▼
       ┌──────────────────────────────────────┐
       │ channel_aggregate_dedup               │
       │ → cleaned/channel_perf_clean.json     │
       └────────┬─────────────────────────────┘
                │ 공유 입력
        ┌───────┴───────┐
        ▼               ▼
   channel_metrics  channel_detailed
   _aggregator      _metrics
        │               │
        ▼               ▼
       C05             T05
   (bar)           (table 9 컬럼)


       ┌──────────────────────────────────────┐
       │ blooming_conversion_funnel_collector  │
       └──────────────┬───────────────────────┘
                      │
                      ▼
       ┌──────────────────────────────────────┐
       │ conversion_funnel_normalizer          │
       └──────────────┬───────────────────────┘
                      ▼
                     C06
                  (funnel)
```

→ **3 pipeline / 6 신규 tool / cleaning 1회 → 2 metric 분기**. Batch 2 의 cache 공유 패턴 + cleaning layer 1단 추가.

### 7.3 Batch 4 — Trend (8 pipeline YAML) ✅ 2026-05-28

> **데이터 source**: `data/blooming/mock_data_{daily_performance,review_trends}.csv` (daily = Batch 2 collector 재사용 / review_trends 실제 컬럼: 리뷰ID·텍스트·별점·작성일·상품명·브랜드·출처·카테고리·**감성**·**주요키워드**·video_title·view_count·channel_name·감성점수·좋아요수).
> **신규 tool 6개** (`blooming_daily_performance_collector` Batch 2 재사용) — 1 collector + 1 cleaning + 4 metric (1 NLP-lite).
> **K14~K17 cache 공유 (핵심)**: 4 pipeline = 같은 `daily_performance_totals` cache_key. Batch 1 C02 ↔ K02 와 동일 패턴 (Runner step-level cache + cache_key 공유).
> **C12 컬럼 결정 (2026-05-28)**: keyword_split_count_top_n input = **"주요키워드"** 컬럼 (raw 사전박힘 활용) ≠ 65 §15.2 I-M12 의 "review_text" 표기. 65 spec §15.2 정정 항목 (V3 후 동반 갱신).
> **C08 1-step 결정**: 감성 분포 = collector 직접 반환 (T04·Batch 2 패턴 일관). frontend 가 groupBy 감성. 별 sentiment_count tool 신설 회피.

#### 7.3.1 K14 — 총 노출수 (template)

```yaml
name: trend_kpi_impressions
visualization_id: K14
category: trend
description: "daily_performance 의 총 노출수 (4 KPI 공유 cache: daily_performance_totals)"
methodology_id: M01
priority: P0
client: ${client}
period: ${period}

trigger:
  type: manual

steps:
  - id: daily_perf_load
    tool: blooming_daily_performance_collector       # ← Batch 2 재사용 (I-C04)
    inputs:
      client: ${client}

  - id: daily_perf_totals
    tool: daily_performance_totals                    # ❌ 신설 — 65 §15.2 I-M09
    inputs:
      client: ${client}
      period: ${period}
    # 4 필드 (총노출/총클릭/총전환/총광고비) 동시 산출
    depends_on: [daily_perf_load]

validator:
  schema: DailyPerformanceTotalsOutput                # ❌ Phase 1 신설 — 4 필드
  expected:
    value_min: 0
  fail_policy: alert

cache:
  layer: computed
  key_template: "daily_performance_totals_${period}.json"   # ← K14·K15·K16·K17 *공유*

owner: developer
tags: [trend, kpi, blooming, daily_perf, cache_shared]
```

#### 7.3.2 K15·K16·K17 — 동일 cache 공유 패턴

| name | visualization_id | 같은 cache_key | frontend 표시 필드 |
|---|:---:|:---:|---|
| `trend_kpi_clicks` | K15 | `daily_performance_totals_${period}.json` | `total_clicks` |
| `trend_kpi_conversions` | K16 | `daily_performance_totals_${period}.json` | `total_conversions` |
| `trend_kpi_ad_cost` | K17 | `daily_performance_totals_${period}.json` | `total_ad_cost` |

> **K14·K15·K16·K17 = 1 tool 호출 → 4 frontend 카드**. cache hit 시 모두 `< 100ms`. Runner 의 동시 실행 4건 중 1건만 backend 작업, 나머지 3건은 cache load only.

YAML 명세 = §7.3.1 K14 패턴 복사 + `name` + `visualization_id` 만 변경. `tags` 에 cache_shared 유지.

#### 7.3.3 C07 — 일별 성과 AreaChart (3 series)

```yaml
name: trend_area_3metric
visualization_id: C07
category: trend
description: "daily_performance 시계열 area — 노출/클릭/전환 3 시리즈"
methodology_id: M03
priority: P0
client: ${client}
period: ${period}

trigger:
  type: manual

steps:
  - id: daily_perf_load
    tool: blooming_daily_performance_collector       # ← K14~K17 와 step 공유
    inputs:
      client: ${client}

  - id: daily_perf_timeseries
    tool: daily_timeseries_3metric                    # ❌ 신설 — 65 §15.2 I-M10
    inputs:
      client: ${client}
      period: ${period}
      metrics: ["노출수", "클릭수", "전환수"]
    depends_on: [daily_perf_load]

validator:
  schema: DailyTimeseries3MetricOutput                # ❌ Phase 1 신설
  expected:
    rows_min: 1                                        # 최소 1 일자
  fail_policy: alert

cache:
  layer: cleaned                                       # 시계열 = cleaned
  key_template: "daily_timeseries_3metric_${period}.json"

owner: developer
tags: [trend, area, blooming, daily_perf, timeseries]
```

#### 7.3.4 C08 — 리뷰 감성 도넛 (1-step, T04 패턴)

```yaml
name: trend_pie_sentiment
visualization_id: C08
category: trend
description: "review_trends 의 감성 컬럼 (raw 사전박힘) — frontend 가 groupBy 감성"
methodology_id: M09                                    # 분포
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: review_trends_load
    tool: blooming_review_trends_collector             # ❌ 신설 — 65 §15.2 I-C07
    inputs:
      client: ${client}
    # collector 결과 = review_trends 전 컬럼.
    # 감성 분포 = frontend groupBy 감성 (별 sentiment_count tool 신설 X)

validator:
  schema: ReviewTrendsOutput                          # ❌ Phase 1 신설 — collector 직접 반환
  expected:
    rows_min: 1
  fail_policy: alert

cache:
  layer: cleaned                                       # raw 정합 = cleaned 동급
  key_template: "review_trends.json"

owner: developer
tags: [trend, pie, sentiment, blooming, raw_passthrough]
```

> **C08 1-step 결정 (T04 패턴)**: 감성 (`긍정`/`부정`/`중립`) 은 raw 사전박힘 (`감성` 컬럼). backend 가 raw 만 제공, frontend 가 `Map<감성, count()>`. MVP+ 시 *진짜 sentiment_analyzer* (M11, 65 §15.4 A-R01) 로 *진화 가능*.

#### 7.3.5 C12 — 키워드 랭킹 Top 10 (NLP-lite)

```yaml
name: trend_bar_keywords_top10
visualization_id: C12
category: trend
description: "review_trends 의 '주요키워드' 컬럼 split + count + top-N (NLP-lite)"
methodology_id: M12                                    # NLP-lite
priority: P0
client: ${client}
period: ${period}
n: 10

trigger:
  type: manual

steps:
  - id: review_trends_load
    tool: blooming_review_trends_collector             # ← C08·O03 와 step 공유
    inputs:
      client: ${client}

  - id: review_period_filter
    tool: review_period_filter                         # ❌ 신설 — 65 §15.2 I-CL04 (cleaning)
    inputs:
      client: ${client}
      period: ${period}
    depends_on: [review_trends_load]

  - id: keyword_top_n
    tool: keyword_split_count_top_n                    # ❌ 신설 — 65 §15.2 I-M12 (NLP-lite)
    inputs:
      client: ${client}
      period: ${period}
      source_column: "주요키워드"                       # ← 65 §15.2 의 "review_text" 정정 (V3 후 spec 갱신)
      n: ${n}
    depends_on: [review_period_filter]

validator:
  schema: KeywordTopNOutput                            # ❌ Phase 1 신설 — n keyword
  expected:
    rows_min: 1                                        # 최소 1 keyword
  fail_policy: alert

cache:
  layer: computed
  key_template: "V12_keywords_top${n}_${period}.json"

owner: developer
tags: [trend, keyword, blooming, nlp_lite, period_filter_shared]
```

#### 7.3.6 O03 — 최근 리뷰 카드 6

```yaml
name: trend_cards_recent_reviews
visualization_id: O03
category: trend
description: "review_trends 작성일 desc sort + slice(0, 6) — 카드 grid"
methodology_id: M08                                    # 정렬·top-N
priority: P0
client: ${client}
period: ${period}
n: 6

trigger:
  type: manual

steps:
  - id: review_trends_load
    tool: blooming_review_trends_collector             # ← C08·C12 와 step 공유
    inputs:
      client: ${client}

  - id: review_period_filter
    tool: review_period_filter                         # ← C12 와 step 공유
    inputs:
      client: ${client}
      period: ${period}
    depends_on: [review_trends_load]

  - id: review_sort_recent
    tool: review_sort_recent                           # ❌ 신설 — 65 §15.2 I-M11
    inputs:
      client: ${client}
      period: ${period}
      n: ${n}
    depends_on: [review_period_filter]

validator:
  schema: ReviewSortRecentOutput                       # ❌ Phase 1 신설 — n card
  expected:
    rows_min: 1
  fail_policy: alert

cache:
  layer: computed
  key_template: "review_sort_recent_top${n}_${period}.json"

owner: developer
tags: [trend, card, recent, blooming, period_filter_shared]
```

#### 7.3.7 Batch 4 — Validator 통과 기준

| 영역 | 기준 |
|---|---|
| schema 일치 | 5 신규 Pydantic Output (`DailyPerformanceTotalsOutput` (K14~K17 공유) / `DailyTimeseries3MetricOutput` (C07) / `ReviewTrendsOutput` (C08) / `KeywordTopNOutput` (C12) / `ReviewSortRecentOutput` (O03)) |
| 정답값 비교 | **없음** (blooming = mock) |
| 실행 시간 | daily_perf < 3초 (5,329 행), review_trends < 1초 (36 행), keyword_split < 1초 |
| cache hit | < 100ms (K14~K17 = 4 호출 중 1건만 실행) |
| dedup 결과 | C12·O03 = `cleaned/reviews_${period}.json` 공유 (period_filter 1회) |

#### 7.3.8 Batch 4 — Test 시나리오

```
1. data/blooming/mock_data_{daily_performance,review_trends}.csv 존재 확인
2. POST /api/admin/pipelines/run/trend_kpi_impressions?client=blooming&period=2026-04
3. 응답: run_id + status="completed", cache 저장
4. POST /api/admin/pipelines/run/trend_kpi_clicks?client=blooming&period=2026-04
   → daily_performance_totals_2026-04.json cache hit → load only (< 100ms)
5. 같은 패턴으로 K16·K17 검증
6. POST /api/admin/pipelines/run/trend_area_3metric?client=blooming&period=2026-04
   → daily_perf_load step cache hit (K14~K17 와 공유)
7. POST /api/admin/pipelines/run/trend_bar_keywords_top10?client=blooming&period=2026-04&n=10
   → keyword_split 후 V12_keywords_top10_2026-04.json
8. POST /api/admin/pipelines/run/trend_cards_recent_reviews?client=blooming&period=2026-04&n=6
   → review_period_filter cache hit (C12 와 공유)
9. Frontend Trend 페이지 새로고침 → 8 시각화 모두 표시
```

#### 7.3.9 Batch 4 cache 공유 도식

```
              ┌─────────────────────────────────────────────────┐
              │ blooming_daily_performance_collector (Batch 2)   │
              └────┬────────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
   daily_performance_totals  daily_timeseries_3metric
   (4 필드 동시 산출)         (시계열 area)
        │                     │
   ┌────┼────┬────┬────┐      │
   ▼    ▼    ▼    ▼           ▼
  K14  K15  K16  K17          C07
  (총노출)(총클릭)(총전환)(총광고비)  (area)


              ┌─────────────────────────────────────────┐
              │ blooming_review_trends_collector         │
              └────┬───────────────────────────────────┬┘
                   │                                   │
        ┌──────────┴──────────┐                       │
        ▼                     ▼                       ▼
   review_period_filter      C08 (sentiment)
   (cleaning)                (1-step, frontend groupBy)
        │
   ┌────┴────┐
   ▼         ▼
keyword_  review_
split     sort_recent
   │         │
   ▼         ▼
  C12       O03
 (Top10)  (cards 6)
```

→ **8 pipeline / 6 신규 tool / 2 collector 1회 + 1 cleaning 1회 → 다중 metric 분기**. Batch 1·2·3 의 cache 공유 패턴 + NLP-lite layer 1단 추가.

### 7.4 Batch 5 — Creative (7 pipeline YAML) ✅ 2026-05-28

> **데이터 source**: `data/blooming/mock_data_{creatives,ab_tests}.csv`. creatives 컬럼 = 소재ID·캠페인ID·소재명·매체·규격·CTR(%)·CVR(%)·CPC(원)·ROAS(%)·CPA(원)·Frequency·집행일수·상태·**피로도**·카피_헤드라인·카피_본문·이미지URL·**AI_Sales·AI_Short·AI_Clear·AI_Visual·AI_Benefit**·소재유형·랜딩URL·시작일·fatigue_score·**is_fatigue**.
> **신규 tool 7개** (Phase 1 동반) — 2 collector + 5 metric.
> **cache 공유 (이중 공유)**:
> - **K18·K21 = 같은 cache** (`creative_counts` = 총·피로·비율 동시) — Batch 4 K14~K17 패턴
> - **K19·K20 = 같은 cache** (`creative_metric_avg` = CTR·ROAS 동시) — 동일 패턴
> - **K18·K19·K20·K21·C11·O04 = 같은 collector step 공유** (Runner step-level cache)
> **C11 = raw 사전박힘 활용**: `AI_Sales·AI_Short·AI_Clear·AI_Visual·AI_Benefit` 5 컬럼 avg. MVP+ 시 `ai_axis_scorer` (M13, 65 §15.4 A-R03) *진짜 CV/LLM* 으로 진화.

#### 7.4.1 K18 — 총 소재 수 + K21 cache 공유 template

```yaml
name: creative_kpi_total
visualization_id: K18
category: creative
description: "creatives 의 총 소재 수 (cache 공유: creative_counts — K18·K21)"
methodology_id: M01
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: creatives_load
    tool: blooming_creatives_collector               # ❌ 신설 — 65 §15.2 I-C08
    inputs:
      client: ${client}

  - id: creative_counts_compute
    tool: creative_counts                             # ❌ 신설 — 65 §15.2 I-M13
    inputs:
      client: ${client}
    # 3 필드 동시 산출 (total / fatigue / fatigue_ratio)
    depends_on: [creatives_load]

validator:
  schema: CreativeCountsOutput                        # ❌ Phase 1 신설 — 3 필드
  expected:
    value_min: 0
  fail_policy: alert

cache:
  layer: computed
  key_template: "creative_counts.json"                # ← K18·K21 *공유*

owner: developer
tags: [creative, kpi, blooming, cache_shared]
```

#### 7.4.2 K21 — 피로 소재 수 + 비율 (K18 cache 공유)

```yaml
name: creative_kpi_fatigue
visualization_id: K21
category: creative
description: "creatives 의 is_fatigue==1 행수 + 비율 (K18 cache 공유)"
methodology_id: M01
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: creatives_load
    tool: blooming_creatives_collector               # ← K18 와 step 공유
    inputs:
      client: ${client}

  - id: creative_counts_compute
    tool: creative_counts                             # ← K18 와 같은 tool
    inputs:
      client: ${client}
    depends_on: [creatives_load]

validator:
  schema: CreativeCountsOutput                        # K18 와 공유
  expected:
    value_min: 0
  fail_policy: alert

cache:
  layer: computed
  key_template: "creative_counts.json"                # ← K18 와 *같은 key*

owner: developer
tags: [creative, kpi, fatigue, blooming, cache_shared]
```

> K21 frontend 표시 = `{fatigue}건 ({fatigue}/{total})` 의 부속 라인. cache hit 시 < 100ms.

#### 7.4.3 K19·K20 — 평균 CTR / ROAS (cache 공유)

```yaml
name: creative_kpi_ctr_avg
visualization_id: K19
category: creative
description: "creatives 의 CTR avg (cache 공유: creative_metric_avg — K19·K20)"
methodology_id: M01
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: creatives_load
    tool: blooming_creatives_collector               # ← K18·K21 와 step 공유
    inputs:
      client: ${client}

  - id: creative_metric_avg_compute
    tool: creative_metric_avg                         # ❌ 신설 — 65 §15.2 I-M14
    inputs:
      client: ${client}
      metrics: ["CTR", "ROAS"]                        # ← 2 필드 동시 산출
    depends_on: [creatives_load]

validator:
  schema: CreativeMetricAvgOutput                    # ❌ Phase 1 신설 — 2 필드
  expected:
    value_min: 0
  fail_policy: alert

cache:
  layer: computed
  key_template: "creative_metric_avg.json"            # ← K19·K20 *공유*

owner: developer
tags: [creative, kpi, blooming, cache_shared]
```

| K20 변경 | 값 |
|---|---|
| `name` | `creative_kpi_roas_avg` |
| `visualization_id` | `K20` |
| frontend 표시 필드 | `ROAS_avg` (K19 는 `CTR_avg`) |
| 나머지 (steps / cache_key / validator) | **K19 와 동일** |

#### 7.4.4 C11 — AI 5축 RadarChart

```yaml
name: creative_radar_ai_axis
visualization_id: C11
category: creative
description: "creatives 의 AI 5축 (AI_Sales/Short/Clear/Visual/Benefit) avg — raw 사전박힘"
methodology_id: M06
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: creatives_load
    tool: blooming_creatives_collector               # ← K18~K21 와 step 공유
    inputs:
      client: ${client}

  - id: ai_axis_avg_compute
    tool: creative_ai_axis_avg                        # ❌ 신설 — 65 §15.2 I-M15
    inputs:
      client: ${client}
      axes:                                            # ← 5 컬럼명 hardcode (ADR-025 L3)
        - AI_Sales
        - AI_Short
        - AI_Clear
        - AI_Visual
        - AI_Benefit
    depends_on: [creatives_load]

validator:
  schema: CreativeAiAxisAvgOutput                    # ❌ Phase 1 신설 — 5 축
  expected:
    rows_min: 5                                       # 5 축
  fail_policy: alert

cache:
  layer: computed
  key_template: "creative_ai_axes.json"

owner: developer
tags: [creative, radar, blooming, ai_axes, raw_pretrained]
```

> **C11 = raw 사전박힘 (POC v1)**. MVP+ 시 `ai_axis_scorer` (65 §15.4 A-R03 — *진짜 CV/LLM*) 로 step 교체. tool 명만 바뀜 → 본 pipeline 구조 변경 0.

#### 7.4.5 O04 — 소재 Top 9 카드

```yaml
name: creative_cards_top9
visualization_id: O04
category: creative
description: "creatives sort ROAS desc + slice(0, 9) — 카드 grid (3×3)"
methodology_id: M08
priority: P0
client: ${client}
n: 9

trigger:
  type: manual

steps:
  - id: creatives_load
    tool: blooming_creatives_collector               # ← K18~K21·C11 와 step 공유
    inputs:
      client: ${client}

  - id: top_n_by_roas
    tool: creative_top_n_by_roas                      # ❌ 신설 — 65 §15.2 I-M16
    inputs:
      client: ${client}
      n: ${n}
    depends_on: [creatives_load]

validator:
  schema: CreativeTopNOutput                          # ❌ Phase 1 신설 — n card
  expected:
    rows_min: 1
  fail_policy: alert

cache:
  layer: computed
  key_template: "creative_top${n}_by_roas.json"

owner: developer
tags: [creative, card, top_n, blooming]
```

#### 7.4.6 T06 — AB 테스트 테이블 7 컬럼 (독립 source)

```yaml
name: creative_table_ab_tests
visualization_id: T06
category: creative
description: "ab_tests 7 컬럼 (테스트ID·매체·A안·B안·승자·신뢰도·판정일) — collector 직접"
methodology_id: M09
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: ab_tests_load
    tool: blooming_ab_tests_collector                 # ❌ 신설 — 65 §15.2 I-C09 (ab_tests)
    inputs:
      client: ${client}

  - id: ab_test_results_compute
    tool: ab_test_results                             # ❌ 신설 — 65 §15.2 I-M17
    inputs:
      client: ${client}
    depends_on: [ab_tests_load]

validator:
  schema: AbTestResultsOutput                         # ❌ Phase 1 신설 — 7 필드
  expected:
    rows_min: 1
  fail_policy: alert

cache:
  layer: computed
  key_template: "ab_test_results.json"

owner: developer
tags: [creative, table, ab_test, blooming]
```

#### 7.4.7 Batch 5 — Validator 통과 기준

| 영역 | 기준 |
|---|---|
| schema 일치 | 5 신규 Pydantic Output (`CreativeCountsOutput` (K18·K21) / `CreativeMetricAvgOutput` (K19·K20) / `CreativeAiAxisAvgOutput` (C11) / `CreativeTopNOutput` (O04) / `AbTestResultsOutput` (T06)) |
| 정답값 비교 | **없음** (blooming = mock) |
| 실행 시간 | creatives 47 행 / ab_tests 9 행 (소규모) — 각 pipeline < 1초 |
| cache hit | < 100ms (K18·K21 동시 호출 시 1건만 실행 / K19·K20 동시 호출 시 1건만 실행) |

#### 7.4.8 Batch 5 cache 공유 도식

```
              ┌─────────────────────────────────────────┐
              │ blooming_creatives_collector             │
              └──────────────┬──────────────────────────┘
                             │ 공유 입력 (6 pipeline)
        ┌─────────────┬──────┼──────────────┬─────────────┐
        ▼             ▼      ▼              ▼             ▼
   creative_counts  creative_metric_avg  creative_ai  creative_top_n
   (3 필드)         (2 필드)              _axis_avg   _by_roas
   = K18·K21        = K19·K20             = C11        = O04
   *같은 cache*     *같은 cache*           (5 축)       (Top 9)
        │             │                     │             │
   ┌────┴────┐   ┌────┴────┐                ▼             ▼
   ▼         ▼   ▼         ▼               C11           O04
  K18       K21 K19       K20            (radar)       (cards)
  (total)(fatigue)(ctr)(roas)


              ┌─────────────────────────────────────────┐
              │ blooming_ab_tests_collector              │
              └──────────────┬──────────────────────────┘
                             ▼
                       ab_test_results
                             ▼
                            T06
                         (table 7)
```

→ **7 pipeline / 7 신규 tool / collector 1회 + 4 metric tool → 6 pipeline 분기 (K18·K19·K20·K21·C11·O04)** + T06 독립. *이중 cache 공유* (K18·K21 / K19·K20) = Batch 4 K14~K17 패턴 + Batch 3 cleaning 공유 패턴 결합.

### 7.5 Batch 6 — Cost 7 + O05 AI 추천 (베타 0.001) ✅ 2026-05-28

> **데이터 source**: `data/blooming/mock_data_{budget_allocation,keyword_performance}.csv`. budget 컬럼 = `구분·캠페인유형·네이버 예산·카카오 예산·메타 예산·구글 예산·총 예산·집행률(%)`. keyword 컬럼 = `키워드·매체·노출수·...·ROAS(%)·경쟁강도·품질지수·키워드그룹` 등.
> **사용자 결정 (베타 0.001)**: O05 AI 추천 = **계속 업그레이드 영역**. 본 batch = *최소 작동 박제*. 단순 LLM 호출 (1 step). 업그레이드 로드맵 §7.5.10 박제.
> **신규 tool 9개**: 2 collector + 1 cleaning + 5 metric + **1 recommendation (LlmMlModel 호출)**. ADR-027 의 ml_model adapter 첫 적용.
> **cache 공유**: K22·K23·C09·C10 = budget collector + dedup 공유 / K24·T07 = keyword collector 공유 / O05 = 위 6 결과를 *입력* 으로 받음.

#### 7.5.1 K22 — 총 예산 (budget 공유 template)

```yaml
name: cost_kpi_budget_total
visualization_id: K22
category: cost
description: "budget_allocation 의 총예산 합산 (K22·K23 cache 공유: budget_totals)"
methodology_id: M01
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: budget_load
    tool: blooming_budget_allocation_collector       # ❌ 신설 — 65 §15.2 I-C10
    inputs:
      client: ${client}

  - id: budget_dedup
    tool: budget_aggregate_dedup                      # ❌ 신설 — 65 §15.2 I-CL03 (cleaning, '합계' 제외)
    inputs:
      client: ${client}
    depends_on: [budget_load]

  - id: budget_totals_compute
    tool: budget_totals                               # ❌ 신설 — 65 §15.2 I-M18
    inputs:
      client: ${client}
    # 2 필드 동시 산출 (total / avg_exec_rate)
    depends_on: [budget_dedup]

validator:
  schema: BudgetTotalsOutput                          # ❌ Phase 1 신설 — 2 필드
  expected:
    value_min: 0
  fail_policy: alert

cache:
  layer: computed
  key_template: "budget_totals.json"                  # ← K22·K23 *공유*

owner: developer
tags: [cost, kpi, budget, blooming, cache_shared]
```

#### 7.5.2 K23 — 평균 집행률 (K22 cache 공유)

| 변경 | 값 |
|---|---|
| `name` | `cost_kpi_exec_rate_avg` |
| `visualization_id` | `K23` |
| frontend 표시 필드 | `avg_exec_rate` (K22 는 `total`) |
| 나머지 | **K22 와 동일** (cache_key 공유) |

#### 7.5.3 K24 — 키워드 평균 ROAS + 운영 수

```yaml
name: cost_kpi_keyword_metrics
visualization_id: K24
category: cost
description: "keyword_performance 의 avg(ROAS) + count (K24)"
methodology_id: M01
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: keyword_load
    tool: blooming_keyword_performance_collector     # ❌ 신설 — 65 §15.2 I-C11
    inputs:
      client: ${client}

  - id: keyword_metrics_avg
    tool: keyword_metrics_avg                         # ❌ 신설 — 65 §15.2 I-M19
    inputs:
      client: ${client}
    depends_on: [keyword_load]

validator:
  schema: KeywordMetricsAvgOutput                    # ❌ Phase 1 신설
  expected:
    value_min: 0
  fail_policy: alert

cache:
  layer: computed
  key_template: "keyword_metrics_avg.json"

owner: developer
tags: [cost, kpi, keyword, blooming]
```

#### 7.5.4 C09 — 채널 비중 도넛

```yaml
name: cost_pie_channel_share
visualization_id: C09
category: cost
description: "4 채널 (네/카/메/구) 예산 합산 → 비중 도넛"
methodology_id: M05                                   # 분포
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: budget_load
    tool: blooming_budget_allocation_collector       # ← K22·K23 와 step 공유
    inputs:
      client: ${client}

  - id: budget_dedup
    tool: budget_aggregate_dedup                      # ← K22·K23 와 step 공유
    inputs:
      client: ${client}
    depends_on: [budget_load]

  - id: budget_by_channel
    tool: budget_by_channel                           # ❌ 신설 — 65 §15.2 I-M20
    inputs:
      client: ${client}
      channels: ["naver", "kakao", "meta", "google"]   # ⚠️ ADR-027 L3(a) 영역 — Phase 1 시 normalizers/blooming.yaml 로 추상화
    depends_on: [budget_dedup]

validator:
  schema: BudgetByChannelOutput                       # ❌ Phase 1 신설 — 4 채널
  expected:
    rows_min: 1
  fail_policy: alert

cache:
  layer: computed
  key_template: "budget_by_channel.json"

owner: developer
tags: [cost, pie, channel, blooming, cache_shared, hardcode_l3a]
```

> **ADR-028 정합**: `channels:` = client 종속 hardcode (A 분류). Phase 1 시 `normalizers/blooming.yaml` 의 `channel_map: [naver, kakao, meta, google]` 으로 추상화.

#### 7.5.5 C10 — 누적 막대 (구분 × 채널)

```yaml
name: cost_bar_budget_stacked
visualization_id: C10
category: cost
description: "구분(캠페인유형) × 4 채널 예산 누적 stacked bar"
methodology_id: M10                                   # 누적
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: budget_load
    tool: blooming_budget_allocation_collector       # ← K22·K23·C09 와 step 공유
    inputs:
      client: ${client}

  - id: budget_dedup
    tool: budget_aggregate_dedup                      # ← step 공유
    inputs:
      client: ${client}
    depends_on: [budget_load]

  - id: budget_stacked
    tool: budget_stacked_by_segment                   # ❌ 신설 — 65 §15.2 I-M21
    inputs:
      client: ${client}
      segment_key: "구분"
      channel_keys: ["네이버 예산", "카카오 예산", "메타 예산", "구글 예산"]   # ⚠️ ADR-028 L3(a) 영역
    depends_on: [budget_dedup]

validator:
  schema: BudgetStackedBySegmentOutput               # ❌ Phase 1 신설
  expected:
    rows_min: 1
  fail_policy: alert

cache:
  layer: computed
  key_template: "budget_stacked_by_segment.json"

owner: developer
tags: [cost, bar, stacked, blooming, cache_shared, hardcode_l3a]
```

#### 7.5.6 T07 — 키워드 ROI Top 12 + 경쟁 Badge

```yaml
name: cost_table_keyword_top12
visualization_id: T07
category: cost
description: "keyword_performance sort ROAS desc slice(12) + 경쟁강도 Badge"
methodology_id: M08                                   # 정렬·top-N
priority: P0
client: ${client}
n: 12

trigger:
  type: manual

steps:
  - id: keyword_load
    tool: blooming_keyword_performance_collector     # ← K24 와 step 공유
    inputs:
      client: ${client}

  - id: keyword_top_n
    tool: keyword_top_n_by_roas                       # ❌ 신설 — 65 §15.2 I-M22 (≠ Batch 4 C12 의 NLP)
    inputs:
      client: ${client}
      n: ${n}
    depends_on: [keyword_load]

  - id: competition_classify
    tool: keyword_competition_classifier              # ❌ 신설 — 65 §15.2 I-M23 (M17 Badge)
    inputs:
      client: ${client}
    depends_on: [keyword_top_n]

validator:
  schema: KeywordCompetitionTableOutput              # ❌ Phase 1 신설 — 8 필드 + Badge
  expected:
    rows_min: 1
  fail_policy: alert

cache:
  layer: computed
  key_template: "keyword_top${n}_with_badge.json"

owner: developer
tags: [cost, table, keyword, blooming, cache_shared]
```

#### 7.5.7 O05 — AI 추천 3 카드 (베타 0.001 — 단순 LLM 호출) ⭐

```yaml
name: cost_ai_recommendation
visualization_id: O05
category: cost
description: "광고 비용·키워드·성과 종합 LLM 추천 (베타 0.001 — 단순 1-shot prompt)"
methodology_id: M21                                   # LLM 분석
priority: P0
client: ${client}

trigger:
  type: manual

steps:
  - id: budget_summary_load
    tool: budget_totals                               # ← K22·K23 cache hit
    inputs: {client: ${client}}

  - id: keyword_summary_load
    tool: keyword_metrics_avg                         # ← K24 cache hit
    inputs: {client: ${client}}

  - id: ai_recommend
    tool: ai_recommendation_tool                      # ❌ 신설 — LlmMlModel 호출 ⭐
    inputs:
      client: ${client}
      budget_summary: ${budget_summary_load.result}
      keyword_summary: ${keyword_summary_load.result}
      card_count: 3                                   # 3 카드 산출
      methodology: "광고 최적화 추천 (베타 0.001 — 단순 prompt)"
    depends_on: [budget_summary_load, keyword_summary_load]

validator:
  schema: RecommendationOutput                        # ❌ Phase 1 신설 — N 카드 {priority, title, body, impact}
  expected:
    rows_min: 1
    rows_max: 5                                       # 3 ± 2 (LLM 변동 허용)
  fail_policy: alert

cache:
  layer: computed
  key_template: "ai_recommendation_3card.json"
  ttl_seconds: 86400                                  # 1일 — LLM 비용 절감

owner: developer
tags: [cost, ai, recommendation, blooming, llm, beta_0_001]
```

> **베타 0.001 framing**:
> - LLM 호출 = `ai_recommendation_tool` 내부 `self.ml.generate_recommendation(...)` (ADR-027 ml_model adapter)
> - 구현체 = `LlmMlModel` (현 LLM 인프라 활용) 또는 `MockMlModel` (POC 단계 mock 추천 fixture)
> - DI 결정 = Phase 1 `build_ml_model(env)` (ADR-027 §3.2)
> - cache TTL = 1일 (LLM 비용 절감 — 매 호출 X)

#### 7.5.8 Batch 6 — Validator 통과 기준

| 영역 | 기준 |
|---|---|
| schema 일치 | 7 신규 Pydantic Output (`BudgetTotalsOutput`·`KeywordMetricsAvgOutput`·`BudgetByChannelOutput`·`BudgetStackedBySegmentOutput`·`KeywordCompetitionTableOutput`·`RecommendationOutput` + Batch 4 `KeywordTopNOutput` 재사용 X — 별 영역) |
| 정답값 비교 | **없음** (blooming = mock) |
| LLM 호출 검증 | O05 = response schema 검증만 (LLM 응답 변동 허용) |
| 실행 시간 | budget 9 행 / keyword 21 행 (소규모) — 각 K/C pipeline < 1초. O05 = LLM 응답 ~2~5초 |
| cache hit | K22·K23·C09·C10 = budget collector + dedup 공유 / O05 = K22·K23·K24 cache 재사용 → 빠름 |

#### 7.5.9 Batch 6 cache 공유 도식

```
       ┌──────────────────────────────────────┐
       │ blooming_budget_allocation_collector │
       └──────────────┬───────────────────────┘
                      │
                      ▼
       ┌──────────────────────────────────────┐
       │ budget_aggregate_dedup ('합계' 제외)  │
       └──────────────┬───────────────────────┘
                      │ 공유 입력 (4 pipeline)
       ┌──────┬───────┴───────┬──────┐
       ▼      ▼               ▼      ▼
   budget_  budget_         budget_ budget_
   totals   totals          by_     stacked_
   (K22)    (K23)           channel by_segment
   = same cache             (C09)   (C10)


       ┌──────────────────────────────────────┐
       │ blooming_keyword_performance_collector│
       └──────────────┬───────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                            ▼
   keyword_metrics              keyword_top_n
   _avg (K24)                   _by_roas (T07)
                                     │
                                     ▼
                                competition
                                _classifier (T07 Badge)


       ┌─────────────────────────────────────────────────┐
       │ O05 AI 추천 (LlmMlModel 호출 — 베타 0.001) ⭐   │
       │   ↑ budget_totals (K22·K23 cache hit)            │
       │   ↑ keyword_metrics_avg (K24 cache hit)          │
       │   = ai_recommendation_tool → LLM 호출 → 3 카드  │
       └─────────────────────────────────────────────────┘
```

→ **7 pipeline / 9 신규 tool / 2 collector + 1 cleaning 공유 + 1 LLM tool**. O05 = *K22·K23·K24 의 산출 결과 재활용* = 매우 효율적.

#### 7.5.10 O05 업그레이드 로드맵 ⭐ (사용자 결정 — 지속 진화 영역)

> 사용자 명시 (2026-05-28): *"이건 계속 업그레이드해야 되는 파트야. 지금은 베타 0.001 정도고 추후 계속 업그레이드 해야 되는 거야."*
>
> 본 §7.5 = 베타 0.001. 다음 단계는 *별 사이클* 별 박제.

| 베타 버전 | O05 구현 | 추가 작업 | 시간 |
|:---:|---|---|---|
| **0.001** (현 — Phase 1) | 단순 prompt → LLM 호출 → 3 카드 | `ai_recommendation_tool` + `LlmMlModel` 또는 `MockMlModel` | ~1h |
| 0.002 | + `cost_anomaly_diagnostic` (이상 패턴 진단 step 추가) | tool 1 + prompt 보강 | ~3h |
| 0.003 | + multi-shot prompt + 카드 우선순위 정교화 | prompt engineering | ~2h |
| 0.004 | + `budget_efficiency_diagnostic` (효율 진단) + 추천 근거 표시 | tool 1 + UI 카드 보강 | ~4h |
| 0.01 | + RAG (historical recommendation 참조) | vector store + retrieve step | ~1d |
| 0.05 | + `creative_fatigue_diagnostic` + multi-domain 통합 추천 | 65 §15.4 A-D04 진화 | ~2d |
| **MVP+** | + fine-tuned model + 추천 outcome tracking | 학습 인프라 | ~1 sprint |
| Prod | + RLHF + 실시간 학습 + multi-tenant 추천 모델 | (별 ADR) | ongoing |

→ **각 버전 = 별 사이클 (ADR-024 적용)**. 본 batch = **베타 0.001 박제만**.

#### 7.5.11 Batch 6 — Test 시나리오

```
1. data/blooming/mock_data_{budget_allocation,keyword_performance}.csv 존재 확인
2. POST /api/admin/pipelines/run/cost_kpi_budget_total?client=blooming
3. → data/blooming/computed/budget_totals.json 산출
4. K23·C09·C10 = budget cache hit
5. POST /api/admin/pipelines/run/cost_kpi_keyword_metrics?client=blooming
6. → keyword_metrics_avg.json 산출
7. T07 = keyword cache hit
8. POST /api/admin/pipelines/run/cost_ai_recommendation?client=blooming
9. → budget·keyword cache hit + LLM 호출 (~2~5초) → 3 카드 응답
10. Frontend Cost 페이지 새로고침 → 7 시각화 모두 표시
```



---

## 8. 변경 이력

| 일자 | 내용 |
|---|---|
| 2026-05-27 | 초안 신규 — Pipeline DSL (YAML) + 작성 컨벤션 + 52 시각화 매핑표 + **Batch 1 (Dashboard1 21 pipeline) 완성**. Batch 2~6 (32 pipeline) = 후속 commit. 사용자 결정 (Pipeline 경계 A / YAML / 단계별) 반영. ADR-023 정합. POC v1 Phase 1 진입의 첫 referential. |
| 2026-05-28 | **Batch 2 — Dashboard v1 6 pipeline YAML 완성** (§7.1.1~§7.1.9). K10·K11·K12·K13·C04·T04 = 6 pipeline / 신규 tool 7개 (`blooming_campaigns_collector`·`blooming_daily_performance_collector` 2 collector + `campaign_count_total`·`campaign_count_active`·`campaign_budget_total`·`campaign_target_roas_avg`·`daily_performance_aggregator` 5 metric — Phase 1 동반). **K11 design 결정**: 65 §14.6.3 의 3-step chain (load+filter+count) → 2-step (load + count_active 통합) 으로 단순화 (`active_campaigns_filter` 신설 회피). **T04 = 1-step pipeline** (projection 별 tool X, frontend 가 select). **cache 공유**: K10·K11·K12·K13·T04 = 같은 `campaigns_load` step → Runner 의 step-level cache (Phase 1) 로 collector 5→1 호출. **validator.reference 없음** (blooming = mock, clumi 정답 17 무관). §5.2 매핑 상태 ⏳→✅, §0 §7 상태 ⏳→🟡. 63 §2.3.3 + §8.6 (commit f6aa1ad) 정합. **ADR-024 V1·V2·V3 사이클 적용** (Phase 0.5 B). |
| 2026-05-28 | **Batch 5 — Creative 7 pipeline YAML 완성** (§7.4.1~§7.4.8). K18·K19·K20·K21·C11·O04·T06 = 7 pipeline / 신규 tool 7개 (2 collector `blooming_creatives_collector`·`blooming_ab_tests_collector` + 5 metric `creative_counts`·`creative_metric_avg`·`creative_ai_axis_avg`·`creative_top_n_by_roas`·`ab_test_results` — Phase 1 동반). **이중 cache 공유**: K18·K21 = `creative_counts` (3 필드 동시) / K19·K20 = `creative_metric_avg` (2 필드 동시). **6 pipeline collector 공유**: K18~K21·C11·O04 모두 같은 `blooming_creatives_collector` step → Runner step-level cache 로 collector 1회 → 4 metric tool 분기. **C11 = raw 사전박힘**: `AI_Sales·AI_Short·AI_Clear·AI_Visual·AI_Benefit` 5 컬럼 avg. axes hardcode (ADR-025 L3 영역). MVP+ 시 `ai_axis_scorer` (65 §15.4 A-R03) 진화 가능 — tool 명만 교체. **T06 독립 source** (ab_tests). 신규 Pydantic Output 5개. §5.5 매핑 헤더 *6 → 7 정정* (compact recovery doc WARN 동반). §0 §7 상태 🟡 누적. **ADR-024 V1·V2·V3·V5 사이클 적용** (Phase 0.5 E). |
| 2026-05-28 | **Batch 6 — Cost 7 pipeline YAML 완성 (베타 0.001)** (§7.5.1~§7.5.11). K22·K23·K24·C09·C10·T07·O05 = 7 pipeline / 신규 tool 9개 (2 collector `blooming_budget_allocation_collector`·`blooming_keyword_performance_collector` + 1 cleaning `budget_aggregate_dedup` + 5 metric `budget_totals`·`keyword_metrics_avg`·`budget_by_channel`·`budget_stacked_by_segment`·`keyword_top_n_by_roas`·`keyword_competition_classifier` + 1 recommendation `ai_recommendation_tool`). **O05 = 베타 0.001 LLM 단순 호출** (사용자 결정 "지속 업그레이드 영역"). ai_recommendation_tool = LlmMlModel 호출 (ADR-027 ml_model adapter 첫 적용). **§7.5.10 업그레이드 로드맵** (베타 0.001 → 0.002 → 0.01 → MVP+ → Prod). cache 공유: K22·K23·C09·C10 = budget / K24·T07 = keyword / O05 = K22·K23·K24 cache 재활용. C09·C10 = channel hardcode (ADR-028 L3(a) — Phase 1 normalizers/ 추상화). **§5.6 매핑 ⏳→✅, §5.7 합계 53→52 정정** (compact recovery doc WARN — C02·O05 중복 계산 오류 해소). §0 §7 상태 🟡→🟢 (**6 batch × 52 pipeline 전체 완료**). **Phase 0.5 완성**. ADR-024 V1·V2·V3·V5 + ADR-026 step 1~10 정방향 첫 적용 (Phase 0.5 F). |
| 2026-05-28 | **§3.7 신설 — ADR-026·027·028·029 통합 framing 박제** (R7 commit). 4 신규 ADR 의 본 spec 적용 매트릭스 + Batch 별 ADR 적용 평가 (Batch 1 🟢 / 2·3 🟠 / 4·5 🔴) + Phase 1 적용 영역 (`schemas/`·`normalizers/`·`ml_models/`·`data/ml_mock/`) + F 사이클 = 첫 모범 사례. **Batch 4·5 spec 정정 = R7 commit 동반** (B2b ml_mock 표시 + axes hardcode 정정 + ml_model adapter 참조). **Phase 1 추가 시간 ~7h** (총 ~27h ≈ 3.5일). 사용자 7 라운드 토의 (시각화 역방향 / 권한 명확 / ml_mock + LLM / tool 영구·ml_model swap / 폴더 명명) 흡수. |
| 2026-05-28 | **§3.6 신설 — "cache" framing 박제** (사용자 통찰). 본 spec 의 "cache" = ***Workspace 변환 산출물 (영속)*** ≠ 통상 cache (임시 사본). 사용자 표현 *"raw 의 변환 결과를 서버 내부에 계속 저장"* = framing 정확. 일반 cache 와의 4 차이 (RAM↔디스크 / 휘발↔영속 / 임시사본↔주요자산 / 손실OK↔손실=정답값손실) + 더 정확한 용어 후보 ("Workspace 자산" / "변환 산출물") + 단어 유지 결정 (변경 비용 회피, MVP+ 정정 검토 ⏸️) + 시스템 본질 정렬 (memory `project_core_value_data_transformation`). §0 §3 입구 갱신. **모든 spec 작업자에게 framing 통일 가이드**. |
| 2026-05-28 | **Batch 4 — Trend 8 pipeline YAML 완성** (§7.3.1~§7.3.9). K14·K15·K16·K17·C07·C08·C12·O03 = 8 pipeline / 신규 tool 6개 (`blooming_review_trends_collector` + `review_period_filter` + `daily_performance_totals` + `daily_timeseries_3metric` + `keyword_split_count_top_n` (NLP-lite) + `review_sort_recent` — `blooming_daily_performance_collector` Batch 2 재사용). **K14~K17 cache 공유**: 4 pipeline = 같은 `daily_performance_totals_${period}.json` cache_key — Batch 1 C02 ↔ K02 패턴. 1 backend 호출 = 4 frontend 카드. **C08 1-step 결정**: 감성 분포 = collector 직접 반환 (T04 패턴 일관). frontend groupBy 감성. 별 sentiment_count tool 신설 회피. MVP+ 시 `sentiment_analyzer` (65 §15.4 A-R01) 진화 가능. **C12·O03 cleaning 공유**: 같은 `review_period_filter` step → `cleaned/reviews_${period}.json` 공유. **C12 컬럼 결정**: `keyword_split_count_top_n` input = "주요키워드" 컬럼 (raw 사전박힘 활용). 65 §15.2 I-M12 의 "review_text" 표기는 V3 후 65 정정 항목. 신규 Pydantic Output 5개 (`DailyPerformanceTotalsOutput`·`DailyTimeseries3MetricOutput`·`ReviewTrendsOutput`·`KeywordTopNOutput`·`ReviewSortRecentOutput`). §5.4 매핑 상태 ⏳→✅, §0 §7 상태 🟡 누적. ADR-025 framing 정합 — 본 batch = L2 (placeholder) 만 활용, L3(a) column_mapping 부재 명시. **ADR-024 V1·V2·V3·V5 사이클 적용** (Phase 0.5 D). |
| 2026-05-28 | **Batch 3 — Channel 3 pipeline YAML 완성** (§7.2.1~§7.2.6). C05·C06·T05 = 3 pipeline / 신규 tool 6개 (2 collector `blooming_channel_performance_collector`·`blooming_conversion_funnel_collector` + 1 cleaning `channel_aggregate_dedup` (`'합계'`/`'전체'` 행 제외) + 3 metric `channel_metrics_aggregator`·`conversion_funnel_normalizer`·`channel_detailed_metrics` — Phase 1 동반). **C05 + T05 cleaning 공유**: 같은 `channel_perf_load` + `channel_dedup` step → Runner step-level cache 로 *cleaning 1회 → 2 metric 분기*. cache layer = `cleaned/channel_perf_clean.json` 단일 진실 소스. **C06 채널 필터**: `channel=naver` 등 ${channel} 변수로 매체별 분기. cache_key 에 ${channel} 포함. 신규 Pydantic Output 3개 (`ChannelMetricsBarOutput`·`ConversionFunnelOutput`·`ChannelDetailedTableOutput`). §5.3 매핑 상태 ⏳→✅, §0 §7 상태 🟡 누적. **ADR-024 V1·V2·V3·V5 사이클 적용** (Phase 0.5 C). **V1·V2·V5 검증 결과**: 4/4 + 6/7 + 3/3 = 13/14 PASS + WARN 2건 정정 완료 — §7.2.2 ${channel} 변수 주입 = 63 §2.3.3.4 PipelineRunRequest.variables 매핑 + null→"all" 정규화 명시 / §7.2.3 T05 9 컬럼 중 4개 (CTR/CVR/CPA/ROAS) 파생 계산 공식 박제. V3 사용자 검토 게이트 대기. |
