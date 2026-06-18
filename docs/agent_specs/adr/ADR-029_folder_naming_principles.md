# ADR-029: 폴더 명명 원칙 — 시스템 본질 + typical 정합 + 영역 명확

## Status

**Accepted** (2026-05-28) — 사용자 질문 *"db / models / schemas 와 본 시스템 폴더의 관계?"* 의 framing 박제. 다음 작업자에게 *왜 이 폴더명* 의 *결정 근거* 전달.

## Context

### 1. 사용자 통찰 (2026-05-28)

ADR-026·027·028 사이클 중 *폴더 구조 결정* 시 사용자 질문:
> "data_sources 내부 구조에서 schemas가 필요한가? models가 필요한가? data_sources라는게 db인가?"
> "폴더명에 대해서인데, 난 db / models / schemas 라고 만들어서 사용했었어. 구조와 기능별로 각 폴더가 어떤역할을 하는지와 현재 폴더명과의 연관성 및 폴더명을 지금처럼 선택한 이유는?"

→ 새 작업자가 *typical FastAPI 패턴 (db/models/schemas)* 을 기대하나 본 시스템은 다른 명명 사용. **결정 근거 박제 필요**.

### 2. typical FastAPI 패턴 (ORM 시대 유산)

| 폴더 | 역할 | 도구 |
|---|---|---|
| `db/` | DB 연결·세션·migration | SQLAlchemy / alembic |
| `models/` | DB 저장 모델 (ORM) | SQLAlchemy / Django ORM |
| `schemas/` | API 입출력 DTO | Pydantic (FastAPI) |

→ ORM 시대 = `models/` + `schemas/` *분리 필수* (ORM ≠ Pydantic).

### 3. 본 시스템과의 *근본 차이*

| 영역 | typical app | 본 시스템 |
|---|---|---|
| 데이터 저장 | DB 중심 (SQL) | **파일 중심** (CSV raw / JSON Workspace) |
| 데이터 source | 단일 DB | **다중** (CSV·API·DB·ML 어댑터) |
| 데이터 흐름 | CRUD | **Pipeline** (변환 산출물 누적) |
| ORM | 핵심 | **없음** (Pydantic 만) |
| 시스템 본질 | API 서버 | **분석 변환 파이프라인** ([memory](memory/project_core_value_data_transformation.md)) |

→ `db/` 부적합 / `models/` 모호 (ORM 없음) / `schemas/` 만 *자연 정합*.

## Decision

### 1. 3 명명 원칙

| 원칙 | 의미 | 적용 예 |
|---|---|---|
| **P1. 시스템 본질 반영** | Pipeline 중심 → 분석 변환 영역 명시 | `data_sources/`·`workspace/`·`pipelines/`·`normalizers/`·`ml_models/` |
| **P2. typical 패턴 정합** | 학습 곡선 ↓, 신규 작업자 친화 | `schemas/`·`core/` |
| **P3. 영역 명확 분리** | 의존성 위배 X (특히 agent 영역) | `dream_agent/` 안에 *agent 만* (Pydantic 등은 외부 `schemas/`) |

### 2. 본 시스템 폴더 결정 (현 + 신규)

```
backend/app/
├── data_sources/       # P1 — 외부 데이터 *어댑터* (DB 만 X — Repository Pattern, ADR-022)
├── ml_models/          # ⭐ P1 — ML 추론 *어댑터* (ABC + Mock + LLM + Production, ADR-027)
├── workspace/          # P1 — tool 산출물 영속 layer (ADR-022)
├── normalizers/        # ⭐ P1 — client 별 컬럼 매핑 YAML config (ADR-025 L3(a))
├── pipelines/          # P1 — (Phase 1) Pipeline Runner + Validator + flows/
├── schemas/            # ⭐ P2 — Pydantic 단일 진실 소스 (inputs/ + outputs/)
├── core/               # P2 — config, logging
└── dream_agent/        # P3 — Agent 영역만 (Cognitive/Planning/Execution/Response)
    ├── models/         # agent 전용 (ExecutionContext, AgentState, ToolSpec, HITLRequest 등 — 변경 없음)
    └── ...
```

### 3. *왜 이 명명* 표 — 결정 근거 매핑

| 폴더 | typical 후보 | 본 시스템 채택 | 사유 |
|---|---|---|---|
| **외부 데이터 추상** | `db/` | **`data_sources/`** | DB ≠ 유일 source. Repository 패턴 (Fowler 1996). ADR-022 의 "관절" |
| **산출물 영속** | (없음) | **`workspace/`** | tool 산출물의 *고유 개념* (DB 대체). ADR-022 |
| **ML 추론 추상** | `services/ml/` | **`ml_models/`** | DataSource 평행 layer. ABC + 구현체 swap (ADR-027) |
| **client 매핑 config** | (없음) | **`normalizers/`** | L3(a) column_mapping (ADR-025) 구현. YAML config = Python 코드 X |
| **Pipeline 영역** | (없음) | **`pipelines/`** | 시스템 본질. ADR-023 의 Runner/Validator |
| **Pydantic 통합** | `models/` + `schemas/` | **`schemas/` 만** | ORM 없음 → `models/` 별 의미 X. Pydantic = schema + model 통합 |
| **config·logging** | `core/` 또는 `config/` | **`core/`** | typical 정합 (P2) |
| **Agent 영역** | (없음) | **`dream_agent/`** | 시스템 고유. P3 (영역 명확) |

### 4. `dream_agent/models/` *예외 박제*

| 영역 | 위치 | 이유 |
|---|---|---|
| **`dream_agent/models/`** (현 위치 유지) | agent 안 | *agent 전용 모델* (ExecutionContext·AgentState·ToolSpec 등) — 시스템 외부 import 안 함 |
| **`schemas/inputs/` + `outputs/`** (신설) | 시스템 전역 | DataSource·Tool 공유 Pydantic. agent 의존성 X |

→ **`dream_agent/models/` 본문 *변경 X***. 신규 schema 만 `schemas/` 신설. *점진 진화* (MVP+ 시 통합 검토).

### 5. 데이터 폴더 (`data/`) 명명

```
data/
├── {client}/           # client 별 영역 (ADR-022 — client 무관 path)
│   ├── raw/            # 외부 입력 (ADR-028 B1·B2·B4)
│   ├── cleaned/        # tool 산출 (ADR-028 B3)
│   ├── computed/       # tool 산출 (ADR-028 B3)
│   └── ...
├── ml_mock/            # ⭐ ML mock data (ADR-028 B2b)
│   ├── sentiment/      # MockSentimentModel 의 반환 fixture
│   ├── ai_axes/        # MockAiAxisModel 의 반환 fixture
│   └── ...
└── (mock_source/)      # POC v1 mock 폴백 source (ADR-023 §4)
```

### 6. 명명 결정 *체크리스트* (신규 폴더 추가 시)

```
[ ] P1 시스템 본질 반영 — 시스템 고유 개념?
[ ] P2 typical 패턴 정합 — 신규 작업자가 이해 가능?
[ ] P3 영역 명확 분리 — 다른 영역 의존성 위배 X?
[ ] 본 ADR § 3 표에 추가 — 결정 근거 박제
```

→ 신규 폴더 = 본 체크리스트 통과 후 도입.

## Consequences

### 긍정

| 영역 | 효과 |
|---|---|
| 신규 작업자 학습 곡선 ↓ | `schemas/`·`core/` = typical 친화 |
| 시스템 본질 가시화 | `data_sources/`·`workspace/`·`pipelines/`·`ml_models/` = 분석 파이프라인 명시 |
| ADR 정합 | ADR-022 (DataSource·Workspace) + ADR-023 (Pipeline·5 주체) + ADR-025 (L3) + ADR-027 (5 주체) + ADR-028 (raw·hardcode) 모두 폴더 구조에 반영 |
| 결정 근거 박제 | 다음 작업자가 *왜 이 명명* 즉시 이해 |

### 비용

| 영역 | 비용 |
|---|---|
| typical 와 다름 | `db/` 기대한 작업자 = 학습 필요 (본 ADR 로 완화) |
| 신규 폴더 4종 | `schemas/`·`normalizers/`·`ml_models/`·`data/ml_mock/` 신설 (Phase 1 ~2h) |

### 완화

| 비용 | 완화 |
|---|---|
| 학습 비용 ↑ | 본 ADR 박제 + INDEX cross-link |
| 신규 폴더 ↑ | Phase 1 일정 안에 통합 (별 sprint 없음) |

## Alternatives

### A. typical 직역 (`db/` + `models/` + `schemas/` + ...) — *기각*
- 장: 익숙
- 단: `db/` = 부적합 (Postgres 작음). 시스템 본질 (Pipeline) 약화

### B. 현 명명 유지 + 신규 폴더 X — *부분 기각*
- 장: 변경 비용 0
- 단: ADR-027 (5 주체) / ADR-028 (raw·ml_mock) 구현 위치 부재

### C. 완전 재구성 (`dream_agent/models/` 도 이전) — *기각*
- 장: 일관성 최강
- 단: agent 전용 모델 이전 비용 ↑, agent 영역 의존성 위배 위험

### D. 본 ADR (혼합 — P1+P2+P3) — *채택*
- 장: 시스템 본질 + typical + 영역 명확 모두 만족
- 단: 일부 신규 폴더 (~2h)

## Related

| ADR / Spec | 관계 |
|---|---|
| [ADR-022](ADR-022_data_source_workspace_layer_separation.md) | `data_sources/` + `workspace/` 신설 박제 |
| [ADR-023](ADR-023_pipeline_5_actors_and_trigger_abstraction.md) | `pipelines/` 박제 |
| [ADR-025](ADR-025_pipeline_customization_3_layer.md) | `normalizers/` (L3(a) 구현) 박제 |
| [ADR-027](ADR-027_five_actor_permission_separation.md) | `ml_models/` 신설 (5 주체 = ml_model) |
| [ADR-028](ADR-028_hardcode_prohibition_and_raw_classification.md) | `data/ml_mock/` 신설 (B2b) |

## 변경 이력

| 일자 | 내용 |
|---|---|
| 2026-05-28 | 초안 — Accepted. 사용자 통찰 "db/models/schemas 와 본 시스템 관계?" 흡수. 3 명명 원칙 (P1 시스템 본질 + P2 typical 정합 + P3 영역 명확) + 본 시스템 폴더 결정 근거 표 + 신규 폴더 (schemas/ + normalizers/ + ml_models/ + data/ml_mock/) 박제 + `dream_agent/models/` 예외 유지 (agent 전용) + 데이터 폴더 명명 + 신규 폴더 체크리스트. 본 ADR = ADR-026·027·028 의 *메타 가이드*. |
