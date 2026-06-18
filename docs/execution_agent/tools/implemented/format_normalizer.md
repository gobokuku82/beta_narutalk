# format_normalizer — 채널별 raw → 통일 스키마

> **D9 (preprocessing 2분리) 반영** — `channel_normalizing_agent` 소속.
> POC = 리뷰 도메인 1개. MVP+ = ads / trend 도메인 룰셋 추가.

## 메타

| 항목 | 값 |
|---|---|
| 소속 에이전트 | channel_normalizing_agent (D9 분리) |
| 카테고리 (YAML) | `data` (※ 폴더 위치 `preprocessing/data_normalization/`) |
| Status | ✅ implemented |
| 버전 | 0.1.0 |
| **Status 마커** (docstring) | ⚠️ **미명시** — Phase 1B 진입 시 `Status: partial — POC review 도메인만, MVP ads/trend 추가 예정` 추가 권장 |
| **DC-10 정합** | docstring ⚠️ / YAML status 필드 없음 / team_catalog `status: implemented` |
| timeout_sec | 30 |
| max_retries | 1 |
| requires_approval | false |
| has_cost / estimated_cost | false / 0.0 |

## 입출력 계약

### 입력 (params)

| name | type | required | default | 설명 |
|---|---|---|---|---|
| domain | string | optional | `"review"` | 매핑 룰셋 (`review` / `ads` / `trend`) — POC = review 만, 그 외 fallback |

### 입력 (context)
- `context.previous_results` 에서 `find_in_previous(..., "raw_reviews")` 자동 조회

### 출력 (produces)
- `normalized_reviews` (list[dict]) — 통일 스키마 (NormalizedReview)
- 보조: `count`, `schema_version` (`"review.v1"`), `domain`

### 출력 dict 스키마

```json
{
  "normalized_reviews": [
    {
      "review_id": "rv_001",
      "text": "...",
      "channel": "naver_blog",
      "rating": 5,
      "sentiment": "positive",
      "date": "2025-09-15",
      "keywords": ["보습력", "촉촉"]
    }
  ],
  "count": 100, "schema_version": "review.v1", "domain": "review"
}
```

### 매핑 룰셋 (REVIEW_FIELD_ALIASES)

| 통일 키 | alias 후보 |
|---|---|
| review_id | 리뷰ID / review_id / id |
| text | 텍스트 / 리뷰내용 / content / review_text / text |
| channel | 출처 / source / media / channel |
| rating | 별점 / rating / score |
| sentiment | 감성 / sentiment |
| date | 작성일 / date / created_at |
| keywords | 주요키워드 / 키워드 / keywords |

## 데이터 source

- **입력 source**: 이전 Tool produces (`raw_reviews`) — review_collector 출력
- **매핑 룰셋**: 본 Tool 내부 상수 `REVIEW_FIELD_ALIASES`
- 정규화 보조: [`helpers.normalize_channel()` / `normalize_sentiment()`](../../../../backend/app/dream_agent/tools/shared/helpers.py)

## 로직 단계

1. `params` 병합 — `domain` 기본 `"review"`
2. **도메인 별칭 정규화** — `DOMAIN_ALIASES` (한↔영 / 단수↔복수)
3. `raw_reviews` 조회 (`find_in_previous`) — 없으면 빈 리스트
4. 각 행에 대해 `_map_review()`:
   - `_pick()` 으로 alias 우선순위로 첫 non-null 값 선택 (pandas NaN 대응)
   - `channel` / `sentiment` → `normalize_channel()` / `normalize_sentiment()`
   - `rating` → int 변환 (실패 시 None)
   - `keywords` 문자열("a,b,c") → list (split + strip)
   - `date` → str (ISO 유지)
5. `logger.info(...)` + 반환

## 예외 처리

| 상황 | 동작 |
|---|---|
| `raw_reviews` 부재 | 빈 리스트 → `normalized_reviews=[]` 반환 (정상) |
| `domain` 미인식 값 | `DOMAIN_ALIASES` fallback `"review"` + warning log |
| alias 모두 부재 | `item[key] = None` |
| `rating` 비정상 값 | int 변환 실패 → None |
| `keywords` None | `[]` 반환 |

## 의존 Tool

- **이전**: `review_collector` (또는 미래의 youtube/coupang/oliveyoung_collector — 모두 `raw_reviews` produces)
- **다음**: `text_preprocessor` (normalized_reviews → cleaned_texts)

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 | 어떤 변경 시 |
|---|---|---|
| Tool 코드 | [`tools/preprocessing/data_normalization/format_normalizer.py`](../../../../backend/app/dream_agent/tools/preprocessing/data_normalization/format_normalizer.py) | 로직 / alias 추가 |
| Tool 메타카드 | [`catalog/preprocessing/data_normalization/format_normalizer.yaml`](../../../../backend/app/dream_agent/tools/catalog/preprocessing/data_normalization/format_normalizer.yaml) | params / produces |
| **YAML `dependencies` stale** ⚠️ | 위 YAML L18-19 | 현재 `[naver_collector]` — D2 rename 후 미갱신. `[review_collector]` 갱신 필요 |
| **team_catalog.yaml** | `channel_normalizing_agent.tools[format_normalizer]` | params_required / produces (현 `params_required: [source_data]` vs 실 코드 `domain` — 검토 필요) |
| LLM Prompts (stage3) | `planning_stage3_todo.yaml` | Tool 이름 / 예시 |
| LLM Prompts (response) | `response.yaml` | 예시 |
| helpers | `tools/shared/helpers.py` `normalize_channel/sentiment` | 4 채널 매핑 룰 확장 시 |
| Phase 1B 시 신규 4 Tool | `kpi_calculator / anomaly_flagger / creative_history_updater / external_variables_joiner` | channel_normalizing_agent 확장 |
| **Spec 32 §7.1** | `agent_specs/32_*.md` | 카운트 |
| **TOBE_MVP/01** | `tool/TOBE_MVP/01_tool_data_matrix.md` | Tool ↔ Data 행 |
| 본 폴더 agent 카드 | [`agents/04_channel_normalizing.md`](../../agents/04_channel_normalizing.md) | Tool 목록 |
| 본 폴더 00_overview | [`00_overview.md`](../../00_overview.md) | 표 |
| 데이터 source 변경 | `data/description/mock/SCHEMA.md` | 컬럼 추가 시 alias 갱신 |
| Tests | `backend/tests/sprint*/` | unit / integration |

### 변경 종류별 최소 갱신
- **새 alias 추가** (예 `리뷰_본문` → text): `REVIEW_FIELD_ALIASES` 만 — 다른 영역 0
- **새 도메인 추가** (ads): `DOMAIN_ALIASES` + 새 매핑 룰셋 dict + 로직 분기 + YAML description + team_catalog tools 추가 (별도 Tool 권장)
- **schema_version bump** (review.v1 → v2): produces 키 변경 — **모든 다음 Tool 영향**

## 참조 코드

- 구현: [`tools/preprocessing/data_normalization/format_normalizer.py`](../../../../backend/app/dream_agent/tools/preprocessing/data_normalization/format_normalizer.py)
- 메타: [`catalog/preprocessing/data_normalization/format_normalizer.yaml`](../../../../backend/app/dream_agent/tools/catalog/preprocessing/data_normalization/format_normalizer.yaml)
- helpers: [`tools/shared/helpers.py`](../../../../backend/app/dream_agent/tools/shared/helpers.py) — `find_in_previous` / `normalize_channel` / `normalize_sentiment`

## 참조 spec

- [agent_specs/17 §3 channel_normalizing](../../../agent_specs/17_functions_to_io_v1.0.md)
- [agent_specs/32 §7.1 preprocessing](../../../agent_specs/32_execution_agent_tools_v1.0.md)
- [TOBE_MVP/01 §2 normalize](../../../_claude/tool/TOBE_MVP/01_tool_data_matrix.md)
- [TOBE_MVP/03 D9](../../../_claude/tool/TOBE_MVP/03_drift_report.md) — preprocessing 2분리

## 참조 비전 (한국어 narrative)

- [agent_design/03_전처리_에이전트.md](../../../_claude/referrence/agent_design/03_전처리_에이전트.md) — 마케팅 도메인 측 (channel_normalizing)

## 📍 Mock vs 실API 분기 (Phase 6+) ⚠️

- 본 Tool 은 외부 API 의존 없음 (입력은 이전 Tool produces) — 분기 불필요
- 단, MVP+ 에서 새 채널 (광고 성과 4 채널) 추가 시 alias 룰셋 확장 필요

## 테스트

- 단위: 본 Tool 단독 테스트 부재 — Phase 1B 진입 시 alias 매핑 검증 권장
- E2E: Planner E2E 가 collection → normalize → preprocessing 체인 검증
- DC-10: docstring Status 마커 미명시 → 검증 시 경고 (보강 권장)

## Phase

| Phase | 본 Tool 의 작업 |
|---|---|
| **Phase 0 (현재)** | ✅ implemented — POC review 도메인만 |
| **Phase 1B** | ads / trend 도메인 룰셋 추가 + channel_normalizing_agent 4 Tool 신규 (kpi_calculator 등) |
| Phase 1B 권장 | docstring `Status: partial → complete` 갱신 |

## Drift / 결정

- **D9** 🟢 Decided — preprocessing 2분리 (text_preprocessing + channel_normalizing) → 본 Tool 은 channel_normalizing_agent 소속
- **stale dependency 박제** — YAML `dependencies: [naver_collector]` D2 rename 후 미갱신 (2026-05-19 발견)

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안 — D9 분리 + stale dependency 발견 박제 + DC-10 갭 박제 |
