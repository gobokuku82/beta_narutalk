# ADR-014: Tool 단일 책임 분리 패턴 — 도메인별 정규화 Tool 분리

## Status

**Accepted** (2026-05-19) — P1.1~P1.4 sprint 완료. 회귀 362 pass.

**Amended** (2026-05-31, 작업 ⑩ 후속) — path 박제 갱신:
- 작업 ③ commit `fd1435d` 에서 `preprocessing/data_normalization/` 폐기 → `normalization/` 이동
- 실 위치: `tools/normalization/format_normalizer.py` + `tools/normalization/review_normalizer.py`
- 본 ADR 본문의 옛 path 박제 (line 39·190-193) = 결정 박제 시점 (2026-05-19) 이력으로 유지하되 amend 안내 추가

**Amended** (2026-06-01, 작업 ⑫ 후속) — broken 5 ads collector 폐기 박제:
- 본문 line 32·38 의 `meta_collector` 인용 = 결정 박제 시점 (2026-05-19) 시나리오 이력 보존
- 실 상태 (작업 ⑫.A·B 후): broken 5 (meta·google_ads·naver_sa·naver_gfa·kakao) 폐기됨. 신 ads chain = external/{meta_ads_performance, naver_searchad, kakao_bizmessage, ...} (ADR-022 helper-B + ADR-027 §1 Tool 권한 정합)

이전 이력:
- **Proposed v1** (2026-05-19) — 제목 "Tool 매개변수 자동 식별 패턴". 옵션 A (시그니처 dict 자동 식별) 채택 방향.
- **재검토** (2026-05-19 사용자 진단) — "format_normalizer 자체가 문제. 리뷰 정규화는 별도 Tool 로 분리해야 한다."
- **Proposed v2** (2026-05-19) — 제목 변경 + Decision 재작성. 자동 식별 (옵션 A~D) **기각**. Tool 단일 책임 분리 (옵션 E) 채택.
- **Accepted** (2026-05-19) — P1 sprint 완료:
  - commit 2ea7cec (P1.1): review_normalizer 신규
  - commit bed40a8 (P1.2): format_normalizer review 코드 제거 + ads 전용
  - commit 3f54136 (P1.3): test 분리 (review_normalizer 측 신규 5 unit)
  - commit dbc2e55 (P1.4): team_catalog 의 channel_normalizing_agent 에 review_normalizer 등록
  - 회귀 362 pass (pre-existing 2 fail 제외 — handoff 박제 영역)

## Context

### 발견 — 사용자 채팅 시나리오 1 (2026-05-19)

사용자가 채팅 UI 에 입력:
> "2024년 10월 메타 광고 성과 보여줘"

**Plan 결과** (Planner stage1~3 정상 동작):
```
todo_001  data_collection      meta_collector
todo_002  data_preprocessing   format_normalizer
todo_003  summary_generation   summary_generator
```

**실 동작**:
- meta_collector: ✅ 248 행 수집 (10월 × 8 캠페인)
- format_normalizer: ❌ **normalized_reviews 0건** (review 도메인 분기)
- summary_generator: ❌ 0건 데이터 → "248건 → 0건 비어 요약 불가" UX 메시지

### 원인 추적

`tools/preprocessing/data_normalization/format_normalizer.py:execute()`:

```python
raw_domain = merged.get("domain", "review")  # default = "review"
domain = DOMAIN_ALIASES.get(...)

if domain == "ads":
    return self._normalize_ads(...)   # ads raw 키 수집
elif domain == "review":
    return self._normalize_review(...) # raw_reviews 키만 수집
```

`tool_params = {}` (Planner LLM 이 `domain` 미명시) → default `"review"` → `find_in_previous("raw_reviews")` → 빈 결과 → `normalized_reviews = []`.

ads raw 키 (`meta_raw_daily / google_raw_daily / naver_raw_daily / naver_gfa_raw_daily / kakao_raw_daily`) 가 previous_results 에 **분명히 있음**에도 도메인 분기 misroute 로 무시.

### 책임 위치 모호

| 영역 | 현재 책임 | 결정 필요 |
|---|---|---|
| Planner stage3 LLM | `format_normalizer(domain="ads")` 명시 책임 — but `planning_stage3_todo.yaml` 에 ads 도메인 예시 미박제 | LLM 학습 부담 또는 명시 강제? |
| format_normalizer Tool | `params.domain` 명시 시 그대로 사용 — 미명시 fallback review | Tool 단의 자동 식별 의무? |
| `_schema.yaml` 의 parameters | `domain` = `required: false, default: "review"` | required 변경? default 변경? |

→ **호출자(LLM) 책임 vs 호출되는 측(Tool) 책임의 architectural 결정 필요**.

### 의도 vs 현실의 괴리

format_normalizer 설계 의도:
> "5 매체 raw → 통일 스키마. POC 부터 자연스러운 chain."

현실:
> Planner LLM 의 도메인 명시 학습 → 학습 안 됐을 때 silent failure (빈 결과 + 혼란스러운 UX).

### 영향 — 본 결정이 향후 Tool 매개변수 모델에 미치는 효과

format_normalizer 만의 결정이 아님. 향후 도입될 Tool 들 (kpi_target_joiner, trend_analyzer, image_generator 등) 모두 매개변수 책임 모델 따름.

예시 영향:
- `keyword_extractor(top_k=10, min_chars=2)` — 명시
- `pdf_renderer(template=?)` — 자동 식별? (브랜드 컬러 기반)
- `image_generator(style=?)` — 자동 식별? (이전 분석 결과 기반)

본 ADR = 향후 모든 Tool 의 매개변수 default + 자동 식별 패턴 기준선.

## Decision (v2 — 재작성)

**"Tool 단일 책임 분리 (도메인별)"** 패턴 채택.

### 핵심 원칙

> **각 Tool 은 단일 도메인만 담당한다. 다도메인 Tool 의 내부 분기 매개변수 (예: `domain`) 는 architectural smell — Tool 자체를 분리한다.**

### format_normalizer 의 구체 적용

**Before (다도메인 Tool — 오설계)**:
```
format_normalizer
   ├── _normalize_ads()      ← 광고 정규화 (5 매체)
   └── _normalize_review()   ← 리뷰 정규화 (4 출처)
```

**After (단일 책임 분리)**:
```
format_normalizer     ← 광고 채널 정규화 전용 (ads.v1)
review_normalizer ⭐  ← 리뷰 정규화 전용 (신규 Tool)
```

### 코드 시뮬레이션

**format_normalizer.py — After**:
```python
class FormatNormalizer(BaseTool):
    """광고 5 매체 raw → daily_performance 통일 (ads 전용)."""
    
    async def execute(self, params, context):
        # domain 매개변수 분기 X — 단일 책임
        raw = self._collect_ads_raw(context.previous_results)
        normalized = [self._map_ads(row) for row in raw]
        return {
            "normalized_ads": normalized,
            "schema_version": "ads.v1",
            "count": len(normalized),
            "channel_counts": ...,
        }
```

**review_normalizer.py — 신규**:
```python
class ReviewNormalizer(BaseTool):
    """4 출처 리뷰 raw → 통일 review 스키마 (review 전용)."""
    
    async def execute(self, params, context):
        raw = find_in_previous(context.previous_results, "raw_reviews") or []
        normalized = [self._map_review(row) for row in raw]
        return {
            "normalized_reviews": normalized,
            "schema_version": "review.v1",
            "count": len(normalized),
        }
```

### 일반화 원칙 (향후 Tool)

- 다도메인 Tool 발견 시 → **분리 후보 박제**. 단일 책임 위반.
- `domain` / `mode` / `type` 매개변수 + 분기 코드 = architectural smell signal
- 분기 매개변수 = "이 Tool 이 2개 책임 졌다" 의 증거
- 분기 발견 시 → ADR-014 패턴 적용 (분리 평가)

### ADR-016 (D9 preprocessing 2 분리) 와 정합

ADR-016 = agent 단의 단일 책임 분리 (text_preprocessing + channel_normalizing)
ADR-014 = Tool 단의 단일 책임 분리 (format_normalizer + review_normalizer)

→ **agent 와 Tool 모두 단일 책임 원칙 일관 적용**.

### Planner LLM 의 task → Tool 매핑

| task type | input | → Tool | produces |
|---|---|---|---|
| `data_preprocessing` | raw_reviews | review_normalizer | normalized_reviews |
| `data_preprocessing` | meta_raw_daily / google_raw_daily / ... | format_normalizer | normalized_ads |

→ Planner LLM 이 input 타입 따라 자연스럽게 매핑. 분기 학습 불필요.

## Consequences (v2)

### 긍정 (+)

- **단일 책임 원칙 (SRP)** — 각 Tool 이 자기 도메인만. 코드 + test + 카드 단순화
- **분기 매개변수 제거** — `domain` 매개변수 자체 폐기. silent failure 위험 0
- **Planner LLM 학습 부담 ↓** — task → Tool 1:1 매핑 (input 타입 보고 자연스러움)
- **ADR-016 와 일관성** — agent 단 (D9 preprocessing 2 분리) + Tool 단 (본 ADR) 같은 패턴
- **테스트 격리성 ↑** — review test 와 ads test 가 다른 Tool 의 unit
- **silent failure 회피 (근본 해결)** — 자동 식별 의 오판 위험 없음. 잘못된 Tool 호출 시 fail-fast
- **향후 정규화 Tool 추가 자연스러움** — 패턴: `<도메인>_normalizer.py`

### 부정 (−)

- **Tool 카운트 증가** — 1 (format_normalizer 다도메인) → 2 (format + review)
  - mitigation: ADR-016 의 agent 카운트 증가 (D9) 와 동일 trade-off — 책임 명확화가 우선
- **코드 분리 비용** — format_normalizer 의 review 코드 80 line 이식 + review_normalizer 신규 ~150 line
  - mitigation: 1 sprint 내 정리 (v1/v2 섞임 금지 원칙)
- **team_catalog + LLM Prompts 정합 필요** — channel_normalizing_agent 에 review_normalizer 추가
- **호환성 단절** — 기존 `params.domain="review"` 호출 패턴 폐기. 명시 호출 코드는 없음 (Planner LLM 만 호출자 — 호환 영향 없음)
- **review_normalizer 의 소속 agent 결정 필요** — channel_normalizing_agent 가 권장 (06 fix plan §2.9 C1)

### 영향 범위

| 영역 | 변경 |
|---|---|
| `tools/preprocessing/data_normalization/format_normalizer.py` | `_normalize_review` + `REVIEW_FIELD_ALIASES` + domain 분기 코드 **제거**. ads 전용 |
| `tools/catalog/preprocessing/data_normalization/format_normalizer.yaml` | description 광고 전용 명시. `domain` 매개변수 **제거** |
| **`tools/preprocessing/data_normalization/review_normalizer.py` 신규** | format_normalizer 의 review 코드 이식 |
| **`tools/catalog/preprocessing/data_normalization/review_normalizer.yaml` 신규** | catalog 신규 |
| `team_catalog.yaml` | channel_normalizing_agent 에 review_normalizer 추가 |
| `tests/test_format_normalizer*.py` | review test → review_normalizer 이전 |
| `tests/test_review_normalizer*.py` 신규 | unit + integration |
| LLM Prompts (stage3) | review chain 예시 보강 (review_collector → review_normalizer → text_preprocessor) |
| `tools/implemented/format_normalizer.md` | 광고 전용 갱신 |
| `tools/implemented/review_normalizer.md` 신규 | 카드 |
| `00_overview.md` + `agents/04_channel_normalizing.md` | Tool 표 갱신 (2 Tool) |
| `06_fix_plan §2` | 옵션 E 채택 반영 |
| 향후 Tool | "다도메인 Tool 발견 시 분리" 원칙 적용 |

## Alternatives Considered (v2)

### 대안 1 — 호출자 명시 강제

- 방법: Planner LLM 의 `planning_stage3_todo.yaml` 에 ads 도메인 예시 박제. Tool 단은 변경 X.
- 장점: Tool 코드 단순 유지. 의도 명확.
- 단점:
  - LLM 학습 부담 (도메인 enum 늘어날 때마다 prompt 보강)
  - LLM 환각으로 명시 누락 가능 (지금 발견된 문제)
  - silent failure 위험 (default review 로 fallback)
- **기각**: silent failure 회피 우선.

### 대안 A/B/C/D — 다도메인 Tool 유지 + 자동 식별 (v1 의 채택안)

- 방법: Tool 단에서 자동 식별 + 명시 override.
  - A: 시그니처 키 dict
  - B: 키 패턴 heuristic
  - C: `_detect_ads_channel` 재활용
  - D: Tool name 매핑
- 장점: 호출자 부담 0. 점진 도입.
- 단점:
  - **단일 책임 위반 유지** — Tool 안에 2 도메인 혼재
  - 자동 식별 오판 위험 (silent failure 가능성 남음)
  - 코드 복잡도 (자동 식별 로직 + 시그니처 관리)
  - **ADR-016 (D9 preprocessing 2 분리) 패턴과 모순**
  - Tool 책임 모호 = 향후 디버깅 부담
- **기각** (2026-05-19 사용자 진단): "format_normalizer 자체가 문제. 손 2 는 다른 Tool 로 구현해야 한다."
- 사유:
  - 자동 식별 = architectural smell 우회 (밴드에이드)
  - Tool 단 단일 책임 분리가 본질적 fix
  - ADR-016 (agent 단 분리) 와 일관성

### 대안 2 — `domain` 매개변수 required 강제 (default 제거)

- 방법: `format_normalizer.yaml` 의 `domain` → `required: true` 변경. Planner LLM 미명시 시 ValueError raise.
- 장점: silent failure 즉시 발견. 자동 식별 코드 불필요.
- 단점:
  - Tool 책임 모호 유지 (다도메인 Tool 자체는 그대로)
  - Planner LLM 학습 부담 그대로
  - 다도메인 Tool 의 의의 자체가 모호 (왜 한 Tool 안에 2 도메인?)
- **기각**: 책임 모호 해결 안 됨.

### 대안 E (채택) — Tool 단일 책임 분리

- 방법: format_normalizer 의 review 부분 제거 → review_normalizer 신규 Tool. 각 Tool 단일 책임.
- 장점:
  - **단일 책임 원칙** — Tool 의 역할 명확
  - ADR-016 패턴 일관 (agent 단 + Tool 단 모두 단일 책임)
  - silent failure 위험 0 (분기 자체 없음)
  - Planner LLM 의 매핑 1:1 (자연스러움)
  - 자동 식별 코드 불필요
  - 테스트 격리성 ↑
- 단점:
  - Tool 카운트 1 → 2 증가
  - 코드 분리 비용 (1 sprint)
- **채택**: 사용자 진단 + 본질적 fix + ADR-016 일관성

## Related

- **P1 fix plan**: [TOBE_MVP/06 §2](../../_claude/tool/TOBE_MVP/06_collection_normalize_fix_plan_2026-05-19.md) — 상세 원인분석 + UX 시나리오 + 검증 plan
- **D18 Drift**: [TOBE_MVP/03 §1 D18](../../_claude/tool/TOBE_MVP/03_drift_report.md) — 발견 자취 박제
- **ADR-015 (예정)**: 메모리 + Clarification + 자유 대화 통합 — P2/P3 가 이 ADR 의 일부로 흡수 예정
- **format_normalizer.py**: 본 ADR 변경 대상 코드
- **base_tool.py**: 향후 `_resolve_param()` 공통 헬퍼 가능성

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-19 | **Proposed v1** — 제목 "Tool 매개변수 자동 식별 패턴". 옵션 A (자동 식별) 채택 방향. P1 fix sprint 전 박제. |
| 2026-05-19 | **재검토** — 사용자 진단: "format_normalizer 자체가 문제. 리뷰는 별도 Tool 로 분리해야 한다." → 자동 식별 = 밴드에이드 인식. |
| 2026-05-19 | **Proposed v2** — 제목 변경 "Tool 단일 책임 분리 패턴". Decision / Consequences / Alternatives 재작성. 옵션 A~D 기각 + 옵션 E (Tool 분리) 채택. ADR-016 (D9) 패턴 일관 박제. |
| 2026-05-19 | **Accepted** — P1.1~P1.4 sprint 완료 (commit 2ea7cec / bed40a8 / 3f54136 / dbc2e55). review_normalizer 신규 + format_normalizer ads 전용 정합 + test 분리 + team_catalog 등록. 회귀 362 pass. |
