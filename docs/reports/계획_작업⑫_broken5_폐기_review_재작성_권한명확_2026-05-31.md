# 계획 — 작업 ⑫ broken 5 폐기 + review_collector 신 패턴 재작성 + 권한 명확화

> **상태**: **v3** (2차 적대적 검증 반영 = minor_fix_then_proceed). **사용자 승인 대기**.
> v1 → v2 → v3: 1차 17 + 2차 10 = 27 변경 반영. 3차 round 우회 (ROI 한계).

---

## 0. 메타

| 항목 | 값 |
|---|---|
| 작업 번호 | ⑫ |
| 작업명 | broken 5 collector 폐기 + review_collector 신 패턴 재작성 + ADR-027 권한 명확화 |
| 작성일 | 2026-06-01 (v3) |
| 패턴 | 작업 ⑤·⑨·⑪ (계획서 → 1차 → v2 → 2차 → v3 → 사용자 승인 → 단계별 commit) |
| 분량 | 中 (백엔드 6 폐기 + 1 재작성 + 3 갱신 + 1 prompt + 7 test 폐기 + 2 test 신규 + 1 박제 = **약 21 파일**) |
| 후속 | 작업 ⑭ team_catalog 신 21 등재 + 작업 ⑮ external 8 ADR-027 audit + **작업 ⑯ doc-drift 정리 (broken 5 이름 잔존 13 docs)** |

---

## 1. 배경 (사용자 통찰 + 본질 진단 인용)

### 1.1 사용자 핵심 결정

> "review_collector 만 살리면 되겠다. 그런 방향으로. 그리고 **권한을 명확하게 하자**"

→ broken 5 (meta·kakao·naver_sa·naver_gfa·google_ads) = 폐기. review_collector = 신 패턴 재작성. **ADR-027 권한 매트릭스 정합**.

### 1.2 본질 진단 인용 (작업 ⑪ Q3 + 작업 ⑫ 측정 workflow)

- broken 6 = `data/mock/` 폐기 (2026-05-28) 로 `FileNotFoundError` 단일 원인
- broken 6 위반 ① data layer 침범 (`load_mock_csv` 직접 호출)
- broken 6 위반 ② collection + filtering 결합 = **ADR-027 권한 위반**
- 5 (ads) = 폐기 / 1 (review) = 신 패턴 재작성

### 1.3 ADR-027 5 주체 권한 매트릭스 (사용자 "권한 명확하게" 본질)

[ADR-027 §1 표 그대로](../agent_specs/adr/ADR-027_five_actor_permission_separation.md#L50-L58):

| 주체 | 입력 | 출력 | 인터페이스 (예) | 권한 | 금지 |
|---|---|---|---|---|---|
| **DataSource** | `client_id` + `source_id` | 표준 schema (Pydantic) | `ds.get(client, "reviews") → ReviewsSchema` | 외부 raw 접근, 컬럼명 매핑·정규화, schema 변환, 결측 처리, mock 폴백 | 계산·집계, Tool 호출, Pipeline 흐름 결정 |
| **Tool** | 표준 schema + 추상 params | 결과 (Pydantic Output) | `tool.execute(data, params, ctx) → Output` | *추상 계산* (sum/avg/groupBy/sort/NLP), **DataSource·ml_model 호출**, output schema 정의 | **client 컬럼명 hardcode, 파일 경로 접근**, DataSource·ml_model 우회 |
| **ml_model** ⭐ | 입력 (텍스트·이미지·수치) | ML 결과 | `ml.analyze_sentiment(texts) → SentimentResult` | ML 추론 *추상 인터페이스*. 구현체 swap | 데이터 fetch, 계산·집계 |
| **Pipeline** | YAML 정의 | step 조합 + cache_key | (YAML 파일) | Tool 조합, step 순서, depends_on, cache_key | 계산·데이터 fetch, 코드 실행 |
| **Maker** | (개발자·Canvas·Agent) | Pipeline 정의 (YAML) | IDE / Canvas / LLM | Pipeline 정의 *생성·수정* | 실행, 데이터 접근, Tool 코드 수정 |

→ 본 작업 ⑫ 범위 = **Tool 행** 중심 (broken 6 위반 해소). **ml_model·Maker** = 본 작업 범위 외.

---

## 2. 현황 spot-check (실 파일 박제, 2차 검증 정정)

### 2.1 신 패턴 인프라 = 이미 준비됨

| 항목 | 파일:라인 | 상태 |
|---|---|---|
| `SOURCE_REGISTRY` 에 reviews 등록 | [file.py:65](../../backend/app/data_sources/file.py#L65) `"reviews": SourceSpec("reviews.csv", "external", None)` | ✅ 즉시 사용 가능 |
| `BaseTool.fetch(source_id, context)` helper-B | [base_tool.py:29-42](../../backend/app/dream_agent/tools/base_tool.py#L29-L42) | ✅ ADR-022 정합 |
| `data/clumi/raw/reviews.csv` | 25 lines (1 header + 24 raw), 5 컬럼 영문 (review_id/date/product/rating/text) | ✅ |
| `review_normalizer.py` alias | [review_normalizer.py:32-40](../../backend/app/dream_agent/tools/normalization/review_normalizer.py#L32-L40) — 한글+영문 둘 다 처리 | ✅ 변경 0 |
| LLM Planner prompt 영향 | **planning_stage3_todo.yaml `tool_params:{brand}` = 4 곳** (line 79·109·135·160) | ⚠ 단계 E 동반 갱신 |
| response.yaml line 135 | execution_summary 예시 `{tool:"review_collector", brand:"블루밍글로우", count:15}` = **cosmetic** (tool_params 아님) | ✅ 변경 0 (2차 검증 정정) |

> **2차 검증 정정**: v2 "planning 6곳 + response 3곳 = 9건" 박제 부정확. 실 review_collector + tool_params{brand} = **planning 4 곳만**. response.yaml = result surface, 의미적 drop 아님.

### 2.2 broken 6 권한 위반 (폐기 대상)

| broken | Tool 권한 위반 (ADR-027) | data layer 침범 | 결정 |
|---|---|---|---|
| meta_collector | MOCK_FILE hardcode + date·campaign_id 필터 | `load_mock_csv()` | **폐기** (external 3 대체) |
| kakao_collector | 동일 | 동일 | **폐기** (POC 범위 외) |
| naver_sa_collector | 동일 | 동일 | **폐기** (external/naver_searchad 1:1) |
| naver_gfa_collector | 동일 | 동일 | **폐기** (external 3 대체) |
| google_ads_collector | 동일 | 동일 | **폐기** (clumi raw + external 둘 다 부재) |
| **review_collector** | `df["브랜드"]`·`df["출처"]`·`df["작성일"]` 한글 hardcode + brand·source·period·limit 필터 | `load_mock_csv("mock_data_review_trends.csv")` | **신 패턴 재작성** (이름 유지) |

### 2.3 sprint15 71 tests = 17 passed / 54 failed (2차 검증 fail vs total 정확화)

> **2차 검증 정정**: per-file 박제 = passed + failed 양쪽 명시 (v2 fail 카운트 정확, total 은 +1씩 — HITL date validation 통과).

| test 파일 | total | passed | failed | 결정 |
|---|---:|---:|---:|---|
| test_meta_collector_unit.py | 11 | 1 (MC09 HITL) | 10 | **동반 폐기** |
| test_google_ads_collector_unit.py | 12 | 1 (GA09) | 11 | **동반 폐기** |
| test_naver_sa_collector_unit.py | 11 | 1 (NS09) | 10 | **동반 폐기** |
| test_kakao_collector_unit.py | 11 | 1 (KC09) | 10 | **동반 폐기** |
| test_review_collector_unit.py | 8 | 0 | 8 | **동반 폐기** (한글 컬럼 강스키마 mismatch) |
| test_collectors_integration.py | 4 | 0 | 4 | **동반 폐기** (broken 6 통합 의존) |
| test_format_normalizer_ads_unit.py | 9 | 8 (FN01-08) | 1 (FN09) | **부분 폐기** (FN09 만, FN01-08 8 보존) |
| test_review_normalizer_unit.py | 5 | 5 (RN01-05) | 0 | **보존** |
| **합** | **71** | **17** | **54** | sprint15 baseline 정합 |

폐기 후 sprint15 baseline = **13 passed / 0 failed** (FN01-08 8 + RN01-05 5)

### 2.4 1차 검증 발견 — format_normalizer.yaml dependencies 5 stale (CRITICAL, v2 해소)

[format_normalizer.yaml line 12-17](../../backend/app/dream_agent/tools/catalog/normalization/format_normalizer.yaml#L12-L17) dependencies 5 broken collector 등재. v2 단계 C 에서 `dependencies: []` 정리.

### 2.5 1차 검증 발견 — team_catalog review entry params 모순 (HIGH, v2 해소)

[team_catalog.yaml line 51-56](../../backend/app/dream_agent/planning/catalog/team_catalog.yaml#L51-L56) `params_required:[brand]` vs 신 catalog `parameters:[]` 모순. v2 단계 D 에서 갱신.

### 2.6 1차 검증 발견 — LLM prompt brand semantic drop (HIGH, v2 해소, 2차 정정)

planning_stage3_todo.yaml **4 곳** (line 79·109·135·160) `tool_params: {brand: "블루밍글로우"}` → 신 collector parameters:[] silently dropped. v2 단계 E 에서 동반 갱신.

> 2차 정정: v2 "5 곳" → v3 "4 곳" (response.yaml line 135 = execution_summary 예시, tool_params 아님).

---

## 3. 변경 명세 (단계별, 7 commit + 1 doc commit, 권한 매트릭스 정합)

### 단계 0 — 사전 검증 (commit 아님, 진입 직전, 2차 검증 정정)

```bash
# 1. _old/ 격리 확인 (pyproject testpaths whitelist 방식, 2차 검증 정정)
grep "testpaths" pyproject.toml
# 기대: testpaths = ["backend/tests"] — _old/ 자연 격리

# 2. 신 catalog yaml clumi_methodology 메타 정합 (기존 51/90 패턴)
grep -l "clumi_methodology" backend/app/dream_agent/tools/catalog/collection/external/*.yaml | head -3
# 기대: 3+ 파일 매치

# 3. broken review_collector 의 실 produces 키 확인
grep "raw_reviews" backend/app/dream_agent/tools/collection/review_collector.py
# 기대: return {"raw_reviews": ...} 단일

# 4. DataSource get() 반환 타입 spot-check (2차 검증 신설, 단계 B 가정 검증)
cd backend && uv run python -c "
from app.data_sources import get_default_data_source
ds = get_default_data_source()
r = ds.get('clumi', 'reviews')
print('type:', type(r).__name__, '/ rows:', len(r) if hasattr(r, '__len__') else 'N/A')
"
# 기대: type: DataFrame / rows: 24
```

### 단계 A — broken 5 ads collector + catalog yaml 폐기 (10 파일)

폐기 대상:
- `backend/app/dream_agent/tools/collection/{meta,kakao,naver_sa,naver_gfa,google_ads}_collector.py`
- `backend/app/dream_agent/tools/catalog/collection/{meta,kakao,naver_sa,naver_gfa,google_ads}_collector.yaml`

### 단계 B — broken review_collector 폐기 + 신 패턴 재작성 (2 파일)

#### B.1 신 review_collector py (ADR-027 권한 정합)

**파일**: `backend/app/dream_agent/tools/collection/review_collector.py` (**전체 재작성**)

```python
"""Review Collector — clumi/raw/reviews.csv raw 수집 (helper-B 패턴).

작업 ⑫ (2026-06-01) 재작성 — ADR-027 §1 권한 매트릭스 정합:

  [Tool 권한] (할 일):
    * DataSource 호출 (self.fetch("reviews", context))
    * raw 통째 반환 (raw_reviews 키)

  [Tool 금지] (안 할 일):
    * 파일 경로·파일명 hardcode (load_mock_csv 폐기)
    * client 컬럼명 hardcode (한글 컬럼 hardcode 폐기 — review_normalizer 책임)
    * 도메인 필터링 (brand·source·period·limit — cleaning tool 책임, MVP+ 결정)
    * 다른 Tool 직접 호출 / ml_model 우회

Status: complete — broken (load_mock_csv) → helper-B 재작성

입력: params (예: brand) 받아도 무시 — POC clumi 단일 client 단일 brand raw.
       filtering = MVP+ 단계에 cleaning tool (cleaning/reviews_filter) 신규 결정.
출력: raw_reviews (list[dict]) — reviews.csv 24 raw 행 통째.
       컬럼 정규화 = review_normalizer 책임 (ADR-014 v2 단일 책임 분리).
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool

logger = get_logger(__name__)

SOURCE_ID = "reviews"           # file.py SOURCE_REGISTRY 등록 키
PRODUCES_KEY = "raw_reviews"    # 다음 tool (review_normalizer) 입력 키 (broken 과 동일)


class ReviewCollector(BaseTool):
    """리뷰 raw 수집 — DataSource 위임 + raw 통째 반환 (ADR-027 권한 정합)."""

    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        # helper-B (ADR-022) — client 흐름은 context, source_id 는 tool 책임
        data = self.fetch(SOURCE_ID, context)

        # pandas DataFrame → list[dict] (raw 형태 유지, normalize 위임)
        if hasattr(data, "to_dict"):
            records = data.to_dict(orient="records")
        else:
            records = data if isinstance(data, list) else [data]

        logger.info(
            "review_collector completed",
            source=SOURCE_ID,
            client=context.client_id,
            count=len(records),
        )

        return {
            PRODUCES_KEY: records,
            "count": len(records),
            "source_id": SOURCE_ID,
        }
```

#### B.2 catalog yaml 갱신

**파일**: `backend/app/dream_agent/tools/catalog/collection/review_collector.yaml` (갱신)

```yaml
name: review_collector
version: "0.3.0"
description: |
  clumi reviews.csv (24 raw) 수집 — raw 통째 반환 (review_normalizer 가 표준화).
  ADR-027 권한: DataSource 호출만, 도메인 필터링·컬럼 hardcode 금지.

category: collection
executor: app.dream_agent.tools.collection.review_collector.ReviewCollector

parameters: []

produces:
  - raw_reviews

dependencies: []

timeout_sec: 30
max_retries: 1

clumi_methodology: "data/clumi/raw/reviews.csv (5 컬럼: review_id, date, product, rating, text), 24 raw rows"
clumi_source_ids: ["reviews"]
```

### 단계 C — format_normalizer 정합 (2 파일, 2차 검증 정정)

> **2차 검증 정정**: v2 "line 1-15 docstring 만" → v3 "**line 1-15 + line 83-87 동반 갱신**" (broken 5 collector → produces 키 매핑 5 줄 docstring 도 stale).

#### C.1 format_normalizer.py docstring 갱신

**파일**: `backend/app/dream_agent/tools/normalization/format_normalizer.py`

- line 1-15 모듈 docstring: broken 5 collector 가정 → 작업 ⑫ 후 "fallback 5 키 유지 = 직접 주입 호환 보존" 명시
- **line 83-87** (broken 5 collector → produces 키 매핑 주석 5 줄, 2차 검증 신설): stale 정정 ("미래 신 ads collector 가 동일 produces key 사용 시 호환")

→ **fallback 키 list (line 91-98) 무변경**. FN01-08 8 건 보존.

#### C.2 format_normalizer.yaml dependencies 정리

```yaml
# 현재 line 12-17 (broken 5 등재)
# 변경 후
dependencies: []   # ⑫ 작업: broken 5 collector 폐기 후 ads chain 미완성 (MVP+ 시 갱신)
```

### 단계 D — team_catalog 정리 (1 파일)

#### D.1 broken 5 entry 삭제 (각 6 줄, 총 30 줄)

- line 79-84 `meta_collector` · line 85-90 `google_ads_collector` · line 91-96 `naver_sa_collector` · line 97-102 `naver_gfa_collector` · line 103-108 `kakao_collector`

#### D.2 review_collector entry 갱신 (line 51-56)

```yaml
# 변경 후
- name: review_collector
  status: implemented
  description: "clumi reviews.csv (24 raw) 수집 — raw 통째 반환. review_normalizer 가 표준화 (ADR-014 v2 분리). filtering = MVP+ cleaning tool 결정."
  params_required: []
  params_optional: []
  produces: [raw_reviews]
```

### 단계 E — LLM prompt 동반 갱신 (1 파일, 4 곳, 2차 정정)

> **2차 검증 정정**: v2 "5 곳 (planning 4 + response 1)" → v3 "**4 곳 (planning 만)**". response.yaml line 135 = execution_summary 예시 (cosmetic, 변경 0).

**파일**: `backend/app/dream_agent/llm_manager/prompts/planning_stage3_todo.yaml`

- line 78-79 example: `"tool_params": {"brand": "블루밍글로우"}` → `"tool_params": {}`
- line 109 example todo_001: `tool_params: {brand: "블루밍글로우"}` → `tool_params: {}`
- line 135 example todo_001: 동일
- line 160 example todo_001: 동일

각 변경 부근 주석 추가:
```yaml
# ⑫ (2026-06-01): review_collector parameters:[] (POC clumi 단일 client raw 통째 반환).
# brand·source 필터 = MVP+ cleaning tool 결정.
```

### 단계 F — sprint15 broken test 7 파일 폐기 (5 unit + 1 integration + 1 partial)

폐기 대상:
- `backend/tests/sprint15/test_{meta,google_ads,naver_sa,kakao,review}_collector_unit.py` (5 파일, total 53 = passed 4 + failed 49 모두 사라짐, 합 정정: 49+4=53 ❌ — 정확히 = passed 3 (MC09/GA09/NS09/KC09 4건? 검증: review 0 + 4 = 4 HITL)
  - 정확: meta 10+1 + google 11+1 + naver_sa 10+1 + kakao 10+1 + review 8+0 = failed 49 + passed 4 = 53
- `backend/tests/sprint15/test_collectors_integration.py` (4 tests, all failed)
- `backend/tests/sprint15/test_format_normalizer_ads_unit.py::FN09` (1 test, **FN01-08 8 보존**)

→ 합 폐기 = 53 + 4 + 1 = 58 (passed 4 + failed 54). 보존 = FN01-08 (8) + RN01-05 (5) = 13 passed.

### 단계 G — 신 review_collector 단위 + chain test 신규 (sprint13, 2 파일, 2차 정정)

> **2차 검증 정정**: v2 "1 파일 (RC-01~06)" → v3 "**2 파일 분리**" (unit vs integration 의미 정합).

**파일 1**: `backend/tests/sprint13/test_review_collector_helper_b_unit.py` (신규, **unit 5 cases**)

- RC-01: `self.fetch("reviews", context)` 호출 (mock DataSource)
- RC-02: raw_reviews list[dict] 형식 반환
- RC-03: client_id=None 시 BaseTool.fetch ValueError (helper-B fail-fast)
- RC-04: DataFrame → list[dict] 변환 정상
- RC-05: 파일 경로 hardcode 0 (ADR-027 권한 정합 자동 검증)

**파일 2**: `backend/tests/sprint13/test_review_chain_integration.py` (신규, **integration 1 case, 2차 신설**)

- **RCI-01**: review_collector → review_normalizer chain (real DataSource, clumi raw 24 행)
  ```python
  assert len(normalized) == 24
  assert normalized[0]['channel'] is None, \
      'POC reviews.csv 5컬럼 = channel alias 부재 박제 (MVP+ raw 확장 시 fail = 자연 trigger)'
  ```

### 단계 H — 박제 동기화 (1 파일, 2차 정정)

> **2차 검증 정정**: v2 "ADR-027 §3 + ADR-015 + 카드 (1-3 파일)" → v3 "**ADR-027 §3 만 (1 파일 고정)**" + 별 작업 ⑯ doc-drift 정리 박제.

**파일**: [ADR-027 §3 권한 위반 사례](../agent_specs/adr/ADR-027_five_actor_permission_separation.md#L28-L37)

§3 표 (line 28-37) 5번째 행 신규 추가:
```
| **Tool 코드 (broken review_collector)** | `load_mock_csv` 파일 경로 + `df["브랜드"]` 한글 hardcode + brand·source·period·limit 필터 (collection + filtering 결합) | clumi reviews.csv schema 변경 시 Tool 코드 수정 필요 |
```

§3 표 6번째 행 신규 추가:
```
| **Tool 코드 (broken 5 ads collector)** | 동일 패턴 (load_mock_csv + 도메인 hardcode) | data/mock/ 폐기로 즉시 fail (sprint15 broken baseline 54) |
```

§3 표 아래 박제 한 줄:
> ✅ **작업 ⑫ (2026-06-01) 해소** — broken 5 ads collector 폐기 + review_collector helper-B 패턴 재작성. external 8 collector + RawCollectorBase 21 entries ADR-027 audit = **작업 ⑮ 잔존**. broken 5 이름 잔존 13 docs (32/33/ADR-014/017/019/65/execution_agent 02_collection 등) doc-drift 정리 = **작업 ⑯ 잔존**.

---

## 4. 영향 범위 요약

### 4.1 변경 파일 (총 약 21, v2 25 → v3 -4 = 21)

| 영역 | 변경 |
|---|---|
| 백엔드 폐기 | 6 collector py + 6 catalog yaml = 12 파일 |
| 백엔드 재작성 | 1 (review_collector.py + yaml) = 2 파일 |
| 백엔드 갱신 | format_normalizer.py (docstring 2 곳) + format_normalizer.yaml (dependencies) + team_catalog.yaml = 3 파일 |
| LLM prompt | planning_stage3_todo.yaml = **1 파일** (v2 2 → v3 1, response.yaml 변경 0) |
| 테스트 폐기 | 5 unit + 1 integration + 1 partial = 7 파일 |
| 테스트 신규 | **2 파일** (sprint13 unit 5 cases + integration 1 case) |
| 박제 동기화 | **ADR-027 §3 = 1 파일 고정** (v2 1-3 → v3 1) |
| **합** | **약 21 파일** |

### 4.2 무영향 (사용자 안심 박제)

| 영역 | 사유 |
|---|---|
| `review_normalizer.py` | alias 가 영문 직접 매핑 가능 → 변경 0 |
| `response.yaml` (2차 정정) | line 135 = execution_summary 예시 (cosmetic) → 변경 0 |
| LLM Planner prompt `tool` 이름 부분 | `tool: review_collector` 이름 유지 → 학습 영향 0 |
| `data/clumi/raw/reviews.csv` | 5컬럼 영문 그대로 → 변경 0 |
| `format_normalizer.py` fallback 5 키 list (line 91-98) | **유지** (FN01-08 8건 호환) |
| 분석 team baseline (sprint13+14) | 287/11/2 — 변동 0 |
| dashboard1 영역 baseline | 303/3 (pyarrow) — 변동 0 |
| frontend type-check | exit 0 — 변동 0 |
| 박제 단일소스 사슬 9 곳 (compact v5 §0.1) | 무변경 |

---

## 5. 단계별 commit (7 commit, 회귀 baseline 유지)

| commit | 단계 | 회귀 명령 |
|---|---|---|
| 1 | A — broken 5 ads collector + catalog yaml 폐기 (10 파일) | sprint15: 54 → 5 fail 잔존 (review 8 + integration 4 + FN09 1 - meta/google/naver/kakao 41 폐기 = ... 정확 측정은 단계 4 후) + ToolRegistry 90 → 85 |
| 2 | B — review_collector 신 패턴 재작성 (py + yaml) | `uv run python -c "from app.dream_agent.tools.collection.review_collector import ReviewCollector; print(ReviewCollector)"` 정상 import + ToolRegistry 85 유지 (이름 같음) |
| 3 | C+D — format_normalizer (docstring 2 곳 + yaml dependencies) + team_catalog (5 entry 삭제 + 1 갱신) | sprint13+14 (287/11/2) + dashboard1 (303/3) + **FN01-08 8 보존 확인** |
| 4 | E — LLM prompt 4 곳 brand silently drop 해소 (planning 1 파일) | sprint13 (ws_agent + cognitive + planning) 회귀 + manual smoke (review chain) |
| 5 | F — sprint15 broken test 7 폐기 | sprint15 = **13 passed / 0 failed** (FN01-08 8 + RN01-05 5) |
| 6 | G — 신 review_collector unit (5) + chain integration (1) = 2 파일 | 신규 test 6 통과 (RC-01~05 + RCI-01) + 전체 회귀 |
| 7 | H — ADR-027 §3 박제 동기화 (1 파일, doc-only) | baseline 무관 |

→ 7 commit, 각 단위 git revert 가능. **단계 1·5 = atomic** (각 10·7 파일 1 commit).

---

## 6. 미해결 결정 (사용자 surface)

| # | 결정 | 권장 |
|---|---|---|
| 6.1 | 신 review_collector 이름 | **유지** (LLM prompt 학습 영향 0) |
| 6.2 | filtering 로직 (brand·source·period·limit) | **폐기** (POC, MVP+ cleaning tool) |
| 6.3 | google_ads POC 범위 축소 | **명시 확인 + 폐기** |
| 6.4 | team_catalog 신 21 등재 | **별 작업 ⑭ 분리** |
| 6.5 | _old/ 정리 | **별 정리 작업** |
| 6.6 | format_normalizer fallback 5 키 (1차 정정) | **유지** (FN01-08 8 보존) |
| 6.7 | ADR-027 §3 박제 동기화 (1차 격상, 2차 범위 축소) | **단계 H 인접 doc commit (ADR-027 §3 1 파일 고정)** |
| 6.8 | LLM prompt brand silently drop (1차 신설, 2차 정정) | **단계 E 동반 갱신 (planning 4 곳만, response 0)** |
| 6.9 | RawCollectorBase + external 13 ADR-027 audit (2차 정량 정정) | **별 작업 ⑮ 분리** (external 13 .py + _FILE_NO_TO_SOURCE_ID 21 entries) |
| 6.10 | LLM prompt blooming 잔존 (2차 정량 정정) | **별 정리 작업** (planning 10 + response 16 = 26건, 광범위) |
| 6.11 | load_mock_csv 死코드 timing | **별 turn** (작업 ⑫ 완료 후 인접 commit) |
| 6.12 | **broken 5 이름 잔존 13 docs doc-drift (2차 신설)** | **별 작업 ⑯ 분리** (32/33/ADR-014/017/019/65/execution_agent 02_collection 등) |
| 6.13 | RC-06 chain test 위치 (2차 정정) | **별 파일 `test_review_chain_integration.py` 분리** (unit vs integration 정합) |

---

## 7. 회귀 baseline 검증 명령

```bash
# 1. sprint13 (+ 신규 RC + RCI test 통과)
cd backend && uv run pytest tests/sprint13 -q
# 기대: 287 + 6 = 293 passed / 0 failed / 2 skipped

# 2. sprint14 분석 team (불변)
cd backend && uv run pytest tests/sprint14 -q
# 기대: 11 failed (HITL) — 변동 0

# 3. sprint15 broken (대폭 감소)
cd backend && uv run pytest tests/sprint15 -q
# 기대: 13 passed / 0 failed (FN01-08 8 + RN01-05 5)

# 4. dashboard1 영역 (불변)
cd backend && uv run pytest tests/{pipelines,dashboard1,data_sources,workspace,permissions,ml_models} -q
# 기대: 303 passed / 3 failed (pyarrow) — 변동 0

# 5. frontend type-check (변경 0)
cd frontend && pnpm exec tsc --noEmit
# 기대: exit 0

# 6. ToolRegistry 분포 변화 (90 → 85)
cd backend && uv run python -c "
from app.dream_agent.tools.registry import get_registry
from collections import Counter
reg = get_registry(); reg.load()
print(Counter(str(t.category.value) for t in reg.get_all()))
print('total:', len(reg.get_all()))
"
# 기대: collection 22 (27 - 5), 합 85

# 7. 신 review_collector ADR-027 권한 검증 (자동 회귀)
cd backend && uv run python -c "
from app.dream_agent.tools.collection.review_collector import ReviewCollector
import inspect
src = inspect.getsource(ReviewCollector)
assert 'load_mock_csv' not in src, 'Tool 금지: 파일 경로 접근 위반'
assert '브랜드' not in src and '출처' not in src and '작성일' not in src, 'Tool 금지: client 컬럼 hardcode 위반'
assert 'self.fetch' in src, 'Tool 권한: DataSource 호출 부재'
print('ADR-027 §1 Tool 권한 매트릭스 정합 ✓')
"

# 8. FN01-08 보존 확인 (1차 검증 정정 핵심)
cd backend && uv run pytest tests/sprint15/test_format_normalizer_ads_unit.py -q -k "not FN09"
# 기대: 8 passed (fallback 5 키 유지 효과)

# 9. format_normalizer dependencies 정합 (1차 검증 정정)
cd backend && uv run python -c "
import yaml
y = yaml.safe_load(open('backend/app/dream_agent/tools/catalog/normalization/format_normalizer.yaml'))
assert y.get('dependencies') == [], f'dependencies 미정리: {y.get(\"dependencies\")}'
print('format_normalizer.yaml dependencies = [] ✓')
"
```

---

## 8. rollback

단계 commit 단위 git revert 가능 (역순 7→1). POC 단순화 = `git reset` 통째 가능.

| 부분 revert 시점 | sprint15 예상 baseline |
|---|---|
| 단계 1 후 revert | 17/54 (원상) |
| 단계 1·2 적용 후 revert 단계 2 | 17/55 (broken 5 폐기 + review 신 작동 안 함) |
| 단계 1~5 적용 후 revert 단계 5 | 13/8 (broken 5 폐기 + review 신 + format/catalog 정합 + sprint15 test 미폐기) |

전체 revert 시 작업 ⑪+⑬ 종료 baseline 회귀.

---

## 9. 검증 체크리스트 (사용자 승인 전 final)

### 9.1 정확성 (1·2차 검증 정정)
- [x] reviews.csv 25 lines (1 header + 24 raw)
- [x] sprint15 per-file passed/failed 양쪽 명시 (2차 정정)
- [x] LLM prompt 영향 = planning 4 곳만 (2차 정정, response cosmetic 제외)
- [x] ADR-027 §1 5주체 매트릭스 (1차 정정)
- [x] format_normalizer.py docstring line 1-15 + 83-87 양쪽 (2차 정정)

### 9.2 완전성 (1·2차 critical/high 해소)
- [x] format_normalizer.yaml dependencies 5 stale 정리 (1차)
- [x] team_catalog review entry params·description 갱신 (1차)
- [x] LLM prompt brand silently drop 해소 (1차+2차)
- [x] 박제 동기화 ADR-027 §3 단계 H (1차+2차 범위 축소)
- [x] RCI-01 chain test 별 파일 분리 (2차)

### 9.3 실행 안전
- [x] **format_normalizer.py fallback 5 키 유지** (FN01-08 8 보존)
- [x] 단계 0 사전 검증 4 항목 (2차 신설 DataSource 타입 spot-check 포함)
- [x] 단계 commit 순서 안전 + atomic 단위 적정
- [x] 회귀 baseline 변동 0

### 9.4 사용자 원칙 정합 + ADR-027
- [x] 死코드 즉시 폐기 (broken 5)
- [x] v1/v2 섞임 금지 (recent ①.x batch 마무리 + LLM prompt 동반 갱신)
- [x] POC 단계 (filtering 폐기, MVP+ 결정)
- [x] tool / data / agent 분리
- [x] **ADR-027 §1 5주체 권한 매트릭스 정합** (사용자 핵심 결정)
- [x] 한 turn ONE 변경 (7 commit)
- [x] 전문가 단일 권장

### 9.5 의존성
- [x] 작업 ⑪ 완료 의존 (helper-B agent path 활성화)
- [x] 작업 ⑭·⑮·⑯ 후속 박제 (별 작업 분리)
- [x] sprint13 신 review_collector test 2 파일 신규 (unit + integration)

---

## 10. 참조

- **측정 workflow** (2026-05-31, 9 agent) — `partial_decommission_review_rewrite` verdict
- **본질 진단 workflow** (2026-05-31, 9 agent) — Q3 broken 6 발견
- **1차 적대적 검증** (2026-05-31, 5 agent) — major_revision, 17 항목 → v2
- **2차 적대적 검증** (2026-05-31, 5 agent) — minor_fix_then_proceed, 10 항목 → v3. ROI 한계 (3차 우회)
- [ADR-022](../agent_specs/adr/ADR-022_data_source_workspace_layer_separation.md) — DataSource DI helper-B
- [ADR-027](../agent_specs/adr/ADR-027_five_actor_permission_separation.md) — **5 주체 권한 분리 (사용자 핵심 본질)**
- [ADR-014 v2](../agent_specs/adr/ADR-014_tool_param_auto_detection.md) — Tool 단일 책임 분리
- 메모리 [project_poc_single_client_clumi] · [tool_data_agent_separation] · [feedback_convention_over_hardcoding] · [feedback_no_mixed_codebases] · [死코드 즉시 폐기] · [feedback_mock_raw_design_doc_first] · [검증 ROI 감소]
- 작업 ⑤·⑨·⑪ 계획서 패턴
- [compact v5](session_compact_recovery_2026-05-31_v5.md) — 작업 ⑪+⑬ 박제

### 10.1 compact v6 trigger 박제 (2차 검증 신설)

작업 ⑫ 완료 + 박제 동기화 (단계 H) commit 7 직후 = **compact v6 작성 trigger**. 본 작업 + 후속 작업 ⑭·⑮·⑯ 박제.

---

## 11. 변경 이력

| 버전 | 날짜 | 내용 |
|---|---|---|
| v1 | 2026-05-31 | 최초 작성 (broken 5 폐기 + review 재작성 + ADR-027) |
| v2 | 2026-05-31 | 1차 적대적 검증 (4 perspective) major_revision 반영. must 8 (critical 2 해소) + should 5 + optional 4 = 17 변경 |
| v3 | 2026-06-01 | 2차 적대적 검증 (4 perspective) minor_fix_then_proceed 반영. must 5 (LLM prompt 5→4 정정·grep 명령·박제 H 1 파일 고정·docstring line 83-87·per-file passed/failed) + should 4 (RCI 별 파일·DataSource 타입 spot-check·external 정량·박제 동기화) + optional 1 (compact v6 trigger) = 10 변경. **3차 round 우회 (ROI 한계)** |

---

## 12. 사용자 결정 surface (v3 최종)

| # | 결정 | 권장 |
|---|---|---|
| 1 | 신 review_collector 이름 | **유지** |
| 2 | filtering 로직 | **폐기** (POC, MVP+ cleaning tool) |
| 3 | google_ads POC 범위 축소 | **명시 확인 + 폐기** |
| 4 | team_catalog 신 21 등재 | **별 작업 ⑭ 분리** |
| 5 | _old/ 정리 | **별 정리 작업** |
| 6 | format_normalizer fallback 5 키 (1차) | **유지** (FN01-08 8 보존) |
| 7 | ADR-027 §3 박제 동기화 (1차+2차 범위 축소) | **단계 H 1 파일 고정** |
| 8 | LLM prompt brand silently drop (1차+2차 정정) | **단계 E planning 4 곳만** (response cosmetic 제외) |
| 9 | external 13 + RawCollectorBase 21 ADR-027 audit (2차 정량) | **별 작업 ⑮ 분리** |
| 10 | LLM prompt blooming 26건 (2차 정량) | **별 정리 작업** |
| 11 | load_mock_csv 死코드 timing | **별 turn** |
| 12 | **broken 5 이름 잔존 13 docs doc-drift (2차 신설)** | **별 작업 ⑯ 분리** |
| 13 | RCI-01 chain test 위치 (2차 정정) | **별 파일 `test_review_chain_integration.py`** |

**기본 = 모든 권장 적용 단계 0 진입**. 사용자 다른 결정 시 surface 후 v4 갱신 (3차 round 우회 권장).

---

**상태**: v3 작성 완료. **다음 단계**: 사용자 승인 → 단계 0 사전 검증 → commit 1 (단계 A) 진입.
