# text_preprocessor — 한글 리뷰 텍스트 통합 클렌징

> **D9 (preprocessing 2분리) 반영** — `text_preprocessing_agent` 소속 (언어 자원 측면).
> POC = 8 단계 통합 1 Tool. MVP+ = 단계 분리 도입 예정 (emoji_handler / repeat_char_normalizer 등).

## 메타

| 항목 | 값 |
|---|---|
| 소속 에이전트 | text_preprocessing_agent (D9 분리) |
| 카테고리 (YAML) | `data` (※ 폴더 위치 `preprocessing/text_cleaning/`) |
| Status | ✅ implemented |
| 버전 | 0.1.0 |
| **Status 마커** (docstring) | ⚠️ **미명시** — 권장: `Status: partial — POC 8단계 통합. MVP에서 단계 분리.` |
| **DC-10 정합** | docstring ⚠️ / YAML status 필드 없음 / team_catalog `status: implemented` |
| timeout_sec | 60 |
| max_retries | 1 |
| requires_approval | false |
| has_cost / estimated_cost | false / 0.0 |

## 입출력 계약

### 입력 (params)

| name | type | required | default | 설명 |
|---|---|---|---|---|
| min_length | integer | optional | `5` | 최소 길이 (미달 = 제외) |
| max_length | integer | optional | `500` | 최대 길이 (초과 = 절단) |

### 입력 (context)
- `context.previous_results` 에서 `find_in_previous(..., "normalized_reviews")` 자동 조회

### 출력 (produces)
- `cleaned_texts` (list[dict])
- 보조: `before_count`, `after_count`

### 출력 dict 스키마

```json
{
  "cleaned_texts": [
    {
      "text_id": "rv_001",
      "original_text": "보습력 짱!! https://...",
      "cleaned_text": "보습력 짱!",
      "is_sponsored": false,
      "is_valid": true,
      "language": "ko",
      "channel": "naver_blog",
      "sentiment": "positive"
    }
  ],
  "before_count": 100, "after_count": 87
}
```

## 데이터 source

- **입력**: `normalized_reviews` (format_normalizer 출력)
- **로직 자원**: 본 Tool 내부 상수 (`SPONSORED_KEYWORDS` / `_RE_HTML` / `_RE_URL` 등)

## 로직 단계 (POC = 8 단계 통합)

1. **min_len/max_len 병합** (`params` 기본값)
2. `normalized_reviews` 조회
3. 각 review 에 대해:
   - **HTML 제거** (`_RE_HTML`)
   - **URL 제거** (`_RE_URL`)
   - **반복 문자 축약** (`_RE_REPEAT` — 3회 이상 → 2회)
   - **공백 통일** (`_RE_WS`)
   - **strip()**
4. **길이 필터** — min_len 미달 skip / max_len 초과 truncate
5. **MD5 dedup** — 중복 cleaned_text 제거 (seen set)
6. **협찬 감지** — `SPONSORED_KEYWORDS` ("협찬", "제공받", "유료광고", "내돈내산 아님", "광고", "PR ") 매칭
7. dict 생성:
   - `text_id` = review_id 또는 hash 앞 8자리
   - `is_sponsored`, `is_valid=True`, `language="ko"`, `channel`, `sentiment` 보존
8. `logger.info(...)` + 반환

### MVP+ 분리 계획 (Phase 1B)

| 단계 | 분리 Tool 이름 |
|---|---|
| HTML 제거 | html_stripper |
| URL 제거 | url_stripper |
| 반복 문자 | repeat_char_normalizer |
| 이모지 처리 | emoji_handler |
| 길이 필터 | length_filter |
| MD5 dedup | dedup_filter |
| 협찬 감지 | sponsored_detector |
| 토큰화 | tokenizer (mecab/khaiii) |

## 예외 처리

| 상황 | 동작 |
|---|---|
| `normalized_reviews` 부재 | 빈 리스트 → cleaned_texts=[] |
| text None | `str(rv.get("text", "") or "")` → 빈 문자열 → 길이 필터로 자연 제외 |
| 모든 review 미달 | 빈 결과 (정상 — 후속 Tool 이 빈 입력 처리) |

## 의존 Tool

- **이전**: `format_normalizer` (normalized_reviews 생성)
- **다음**: `sentiment_analyzer` / `keyword_extractor` (cleaned_texts 소비)

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 | 어떤 변경 시 |
|---|---|---|
| Tool 코드 | [`tools/preprocessing/text_cleaning/text_preprocessor.py`](../../../../backend/app/dream_agent/tools/preprocessing/text_cleaning/text_preprocessor.py) | 로직 / 정제 단계 |
| Tool 메타카드 | [`catalog/preprocessing/text_cleaning/text_preprocessor.yaml`](../../../../backend/app/dream_agent/tools/catalog/preprocessing/text_cleaning/text_preprocessor.yaml) | params / produces |
| **team_catalog.yaml** | `text_preprocessing_agent.tools[text_preprocessor]` | params_required (`raw_reviews` 현재 — 실 코드는 `normalized_reviews` 사용 — **mismatch 박제**) |
| LLM Prompts (stage3) | `planning_stage3_todo.yaml` | Tool 이름 / 예시 |
| LLM Prompts (response) | `response.yaml` | 예시 |
| **Phase 1B 시 8 분리** | `tools/preprocessing/text_cleaning/` 하위 신규 8 .py + 8 .yaml | 본 Tool 은 deprecated 또는 orchestrator 로 |
| 데이터 source 변경 | `data/description/mock/SCHEMA.md` review_trends | text 컬럼 정의 변경 시 |
| **Spec 32 §7.1** | `agent_specs/32_*.md` | preprocessing 행 |
| **TOBE_MVP/01** | `tool/TOBE_MVP/01_tool_data_matrix.md` | Tool ↔ Data 행 |
| 본 폴더 agent 카드 | [`agents/03_text_preprocessing.md`](../../agents/03_text_preprocessing.md) | Tool 목록 |
| 본 폴더 00_overview | [`00_overview.md`](../../00_overview.md) | 표 |
| Tests | `backend/tests/sprint*/test_*preprocessor*.py` | unit |

### 변경 종류별 최소 갱신
- **새 SPONSORED_KEYWORDS 추가**: 상수만 — 다른 영역 0
- **새 정제 단계 추가**: `_clean()` 메서드 확장 + (필요 시) 상수 추가
- **MD5 → SimHash 교체**: dedup 로직 변경 (성능 영향 측정 필요)
- **Phase 1B 8 분리**: 본 Tool 폐기 + 8 신규 + Planner 가 8 Tool 직렬 호출 가능하도록 변경

## 참조 코드

- 구현: [`tools/preprocessing/text_cleaning/text_preprocessor.py`](../../../../backend/app/dream_agent/tools/preprocessing/text_cleaning/text_preprocessor.py)
- 메타: [`catalog/preprocessing/text_cleaning/text_preprocessor.yaml`](../../../../backend/app/dream_agent/tools/catalog/preprocessing/text_cleaning/text_preprocessor.yaml)
- helper: [`shared/helpers.py:find_in_previous`](../../../../backend/app/dream_agent/tools/shared/helpers.py)

## 참조 spec

- [agent_specs/17 §3 text_preprocessing](../../../agent_specs/17_functions_to_io_v1.0.md)
- [agent_specs/32 §7.1 preprocessing](../../../agent_specs/32_execution_agent_tools_v1.0.md)
- [TOBE_MVP/01 §2 preprocessing](../../../_claude/tool/TOBE_MVP/01_tool_data_matrix.md)
- [TOBE_MVP/03 D9](../../../_claude/tool/TOBE_MVP/03_drift_report.md) — preprocessing 2분리

## 참조 비전 (한국어 narrative)

- [agent_design/03_전처리_에이전트.md](../../../_claude/referrence/agent_design/03_전처리_에이전트.md) — 언어 자원 측 (text_preprocessing)

## 📍 Mock vs 실API 분기

- 외부 API 의존 없음 — 분기 불필요 (순수 텍스트 처리)

## 테스트

- 단위 부재 — Phase 1B 진입 시 정제 단계별 unit 권장
- E2E: Planner 가 cleaned_texts produces 검증
- DC-10: docstring Status 마커 미명시 (보강 권장)

## Phase

| Phase | 본 Tool 의 작업 |
|---|---|
| **Phase 0 (현재)** | ✅ implemented — 8 단계 통합 1 Tool |
| **Phase 1B** | 8 분리 + 본 Tool deprecated/orchestrator |

## Drift / 결정

- **D9** 🟢 Decided — preprocessing 2분리 (text_preprocessing + channel_normalizing)
- **team_catalog mismatch 박제** — `params_required: [raw_reviews]` vs 실 코드 `normalized_reviews` → 통합 정정 권장 (Phase 1B)

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안 — D9 분리 + team_catalog mismatch 박제 + DC-10 갭 박제 |
