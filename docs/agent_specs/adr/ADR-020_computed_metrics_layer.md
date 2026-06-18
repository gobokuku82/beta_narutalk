# ADR-020: Computed Metrics Layer — 에이전트 시스템 외부의 사전 계산 영역

## Status

**Proposed** (2026-05-20) — 사용자 architectural insight 박제 후 설계. 사용자 결정 후 Accepted 갱신.

후속 이력:
- (예정) Accepted — backend/metrics + frontend hook 1차 구현 후.

## Context

### 발견 — 사용자 architectural insight (2026-05-20)

> "CTR / CPC / CPM / CVR 는 그냥 단순 계산 수식만 있으면 되니깐, 데이터를 받으면 서버에 저장하고 그냥 로드만 하면 되는거 아닌가?"
>
> "단순계산식 및 사전에 미리 계산해야 되는건 대시보드에도 표시해야 하니깐, 그건 에이전트/툴 영역이 아니라, 에이전트 시스템과 별도로 데이터 계산 로직이 있어야하네."
>
> "일단 단순계산식은 프론트엔드/데이터베이스 구축부터 → 에이전트가 로드하는 형태면 좋을것 같아."
>
> "쓸데없이 LLM 호출할 필요는 없다."

→ **시스템 차원의 새 layer 정의**.

### 현 시스템의 한계

```
Frontend (대시보드) ─┐
                     │
Backend ─────────────┤
   ├── 에이전트 시스템 (4-Layer)
   │      └── 분석 Tool 13개 (07 plan)
   │           ├── 단순 산술 4 (CTR/CPC/CPM/CVR)
   │           └── 복잡 분석 9 (POC-01~09)
   └── mock_data API (CSV 그대로 노출)
                     │
Data ────────────────┘
   └── mock CSV 17 시트
```

**문제점**:
1. 단순 산술 (CTR/CPC/CPM/CVR) 도 Tool 로 만들면 → 에이전트 chain 길어짐 + LLM 거쳐서 응답 → 비효율
2. 대시보드에 사전 계산 값 표시 = frontend 가 직접 계산 → 분산
3. 데이터 source 가 늘어나면 (실 API 전환 시) 매번 다시 계산 = 캐시 X

### ADR-014 v2 와의 관계

ADR-014 v2 = "Tool 단일 책임 분리 (도메인별)". 분리는 OK 하지만 **Tool 자체의 책임 영역** 미정의.

→ 본 ADR-020 = Tool 책임 영역 명확화 + 별도 layer 정의.

### 사용자 직관 — Tool vs simple query 의 boundary

| 분류 | Tool 영역? |
|---|---|
| **단순 산술** (CTR = clicks/imp × 100) | ❌ Tool 영역 외 |
| **사전 계산 가능 + 자주 사용** (매체별 평균 ROAS) | ❌ Tool 영역 외 |
| **복잡 알고리즘** (kpi_anomaly_detector — 규칙 트리) | ✅ Tool |
| **외부 API / ML 모델** (sentiment KoBERT) | ✅ Tool |
| **LLM 호출 필수** (insight_extractor) | ✅ Tool |
| **statefuls 계산** (kpi_forecaster — 누적값 외삽) | ✅ Tool |

→ **Tool 책임 = "stateful 계산 / 외부 호출 / 복잡 알고리즘 / LLM"**.

## Decision

### 1. Tool 책임 영역 재정의

**Tool 영역**:
- 복잡 알고리즘 (규칙 트리 / 통계 검정 / ML / NLP)
- 외부 API / 라이브러리 호출 (DALL-E / statsmodels / KoBERT)
- LLM 호출 (insight / report / summary)
- stateful 계산 (예측 / 시계열)

**Tool 영역 외 (Computed Metrics Layer)**:
- 단순 산술 (CTR / CPC / CPM / CVR)
- 집계 (groupby + sum/mean/count)
- 매체별 ranking
- 퍼널 단계별 %
- 단순 CAC (광고비/전환수)

### 2. Computed Metrics Layer 의 위치

```
═══════════════════════════════════════════════════════════════
  Frontend (Dashboard + 채팅 UI)
═══════════════════════════════════════════════════════════════
       │                           │
       ▼                           ▼
═══════════════════════════════════════════════════════════════
  Computed Metrics Layer ⭐ 신규 (Backend)
  - 사전 계산 + 캐시 + API endpoint
  - LLM 호출 X (효율)
═══════════════════════════════════════════════════════════════
       │                           │
       ▼                           ▼
  데이터 source                에이전트 시스템 (4-Layer)
  (mock CSV / 실 API)           └── Tool = 복잡 분석만
═══════════════════════════════════════════════════════════════
```

→ Computed Metrics Layer = **에이전트 시스템과 같은 데이터 source 사용. 단 별도 layer**.

### 3. POC vs MVP+ 진화 패턴

| 단계 | 구현 | 이유 |
|---|---|---|
| **POC** (지금) | mock CSV 의 사전 계산 컬럼 (CTR/CPC/CPM/CVR 이미 박혀있음) + frontend 직접 평균 계산 | 빠른 ship + 단순 |
| **MVP-0** | backend/metrics/ 모듈 + API endpoint | 캐시 + 일관성 |
| **MVP+** | DB Materialized View / Redis 캐시 | 성능 + 실시간 |

### 4. 에이전트와 Computed Metrics 의 관계

**원칙**: 같은 데이터 source 사용 + Computed Metrics 가 사전 계산한 값을 에이전트도 로드 (별도 계산 X).

```
mock daily_performance.csv (CTR/CPC/CPM/CVR 컬럼 박혀있음)
        │
        ├──► frontend Dashboard (직접 평균 계산)
        │
        ├──► Computed Metrics API endpoint (캐시)
        │
        └──► 에이전트 Tool (필요 시 — 복잡 분석만)
```

**에이전트가 simple query 처리 시**:
- Cognitive Layer 가 "이건 simple query" 인식
- Computed Metrics API 호출 (Tool 우회)
- 응답 LLM 이 자연어 변환

### 5. 07 plan 의 13 Tool 재정정

| 기존 Tool 후보 | 재분류 | 처리 |
|---|---|---|
| ~~channel_performance_analyzer~~ | ❌ 제거 | Computed Metrics 영역 |
| ~~funnel_analyzer~~ | ❌ 제거 | conversion_funnel 컬럼 그대로 |
| ~~cac_analyzer~~ | ❌ 제거 | 단순 산술 |
| ~~retention_analyzer~~ | ❌ 제거 | retention 컬럼 그대로 |
| ~~ctr/cpc/cpm/cvr_analyzer~~ | ❌ 안 만듦 | 사용자 통찰 적용 |
| kpi_anomaly_detector (POC-01) | ✅ Tool | 규칙 트리 |
| creative_fatigue_detector (POC-04) | ✅ Tool | Freq + CTR 추이 + 규칙 |
| roas_root_cause_analyzer (POC-03) | ✅ Tool | 규칙 + external + LLM |
| kpi_forecaster (POC-02) | ✅ Tool | 선형 외삽 |
| ab_test_judge (POC-05) | ✅ Tool | statsmodels |
| search_surge_detector (POC-08) | ✅ Tool | 시계열 + LLM |
| sentiment_analyzer (POC-07) | ✅ Tool | NLP |
| keyword_extractor (POC-06+08) | ✅ Tool | 토큰화 + Counter |
| insight_extractor (POC-09) | ✅ Tool | LLM |

→ **13 → 9 Tool 재정정**.

## Consequences

### 긍정 (+)

- **Tool 책임 명확화** — Tool = 복잡 영역만. simple query 분리
- **효율성** — 단순 산술에 LLM 호출 X (사용자 메모리 `project_llm_heavy_initial` 의 보완 — "쓸데없이 호출 X")
- **대시보드 빠른 ship** — frontend 직접 표시 가능
- **MVP+ 자연스러운 진화** — backend/metrics/ 모듈 도입 시 architecture 일관
- **에이전트 chain 단순화** — Tool 4개 (CTR/CPC/CPM/CVR) 제거 = Plan todos 짧아짐
- **사용자 직관 정합** — "단순 계산 = 별도 layer" 의도 박제

### 부정 (−)

- **2 영역 일관성 부담** — Computed Metrics 와 에이전트가 같은 데이터 의미 유지 필요
- **신규 layer 추가** — POC 단계 새 모듈 (단, MVP+ 진입 시 필수)
- **Cognitive 분기 로직 필요** — "simple query vs complex analysis" 인식
- **테스트 영역 추가** — Computed Metrics 의 정합 검증

### 영향 범위

| 영역 | 변경 |
|---|---|
| `docs/_claude/tool/TOBE_MVP/07_analysis_tools_design` | 13 → 9 Tool 재정정 |
| `docs/_claude/tool/TOBE_MVP/09_computed_metrics_layer_*` | 신규 plan |
| Frontend `DashboardPage.tsx` | KPI 4 카드 추가 (CTR/CPC/CPM/CVR 직접 계산) |
| (MVP-0) Backend `backend/app/metrics/` | 신규 모듈 |
| (MVP-0) API endpoint `/api/metrics/*` | 신규 |
| Cognitive Layer (장기) | simple/complex 분기 룰 추가 |
| ADR-014 v2 | 보완 (Tool 책임 영역 명확화) |
| ADR-016 (10 에이전트 구조) | 영향 X (agent 단 그대로) |

## Alternatives Considered

### 대안 1 — 모든 분석 Tool 로 (현 07 plan 13 Tool)

- 장점: 일관성 (모든 분석 = Tool)
- 단점:
  - simple query 도 Tool chain 거침 = overhead
  - LLM 거쳐서 응답 = 불필요한 비용
  - 사용자 통찰 무시
- **기각**: 사용자 명시 + 효율 우선

### 대안 2 — Frontend 만 직접 계산 (옵션 5)

- 장점: 작업 최소
- 단점:
  - 채팅 NL 응답 시 다시 계산 = 분산
  - MVP+ 진입 시 정합 깨짐
- **기각**: 단기 ship 만 가능, 장기 분산

### 대안 3 — Computed Metrics Layer 신규 (채택) ⭐

- 장점: Tool 책임 명확 + 효율 + MVP+ 진화 자연
- 단점: 신규 layer + 일관성 부담
- **채택**: 사용자 직관 + 본질적 architectural decision

### 대안 4 — 모든 분석 = DB Materialized View

- 장점: 성능 최적
- 단점: POC 단계 과한 (PostgreSQL Materialized View 셋업)
- **이연**: MVP+ 진입 시

## Related

- **ADR-014 v2** (Tool 단일 책임 분리) — 본 ADR 이 보완 (Tool 책임 영역 명확화)
- **ADR-016** (10 에이전트 구조) — 영향 X
- **07 plan** — 13 → 9 Tool 재정정
- **09 plan (예정)** — Computed Metrics Layer 의 구체 설계
- 사용자 채팅 시나리오 1 ("10월 메타 광고 성과") — Tool chain 통과 후 "분석 결과 비어있음" UX. 본 ADR 적용 시 Computed Metrics API 직접 응답으로 해결.
- Frontend `DashboardPage.tsx` — KPI 4 카드 추가 영역

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-20 | Proposed — 사용자 architectural insight (단순 계산은 Tool 영역 외 + 별도 데이터 계산 로직) 박제. Computed Metrics Layer 정의 + POC/MVP 진화 패턴 + Tool 13→9 재정정. |
