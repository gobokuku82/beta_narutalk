# sentiment_analyzer — 감성 분석 (정규화 우선 + 규칙 폴백)

> **POC-07 (9 분석 모듈 중 감성 분석)** 매핑.
> POC = format_normalizer 정규화 라벨 + 규칙 기반 폴백. MVP = KoBERT 교체 검토 (D6).

## 메타

| 항목 | 값 |
|---|---|
| 소속 에이전트 | analysis_agent |
| 카테고리 (YAML) | `analysis` (폴더 `analysis/ml/`) |
| Status | ✅ implemented |
| 버전 | 0.1.0 |
| **Status 마커** (docstring) | ⚠️ **미명시** — 권장: `Status: partial — POC 규칙 기반. MVP KoBERT 도입 예정 (D6).` |
| **DC-10 정합** | docstring ⚠️ / YAML status 필드 없음 / team_catalog `status: implemented` |
| timeout_sec | 60 |
| max_retries | 1 |
| requires_approval | false |
| has_cost / estimated_cost | false / 0.0 (LLM 비호출) |

## 입출력 계약

### 입력 (params)
- 없음

### 입력 (context)
- `context.previous_results` 에서 `find_in_previous(..., "cleaned_texts")` 조회

### 출력 (produces)
- `sentiment_distribution` (dict) — positive/neutral/negative % + total_count
- `sentiment_items` (list[dict]) — text_id 별 라벨
- 보조: `total_count`

### 출력 dict 스키마

```json
{
  "sentiment_distribution": {
    "positive": 65.0,
    "neutral": 20.0,
    "negative": 15.0,
    "total_count": 87
  },
  "sentiment_items": [
    {"text_id": "rv_001", "text": "...", "sentiment": "positive", "confidence": null}
  ],
  "total_count": 87
}
```

## 데이터 source

- **입력**: `cleaned_texts` (text_preprocessor 출력)
- **로직 자원**:
  - `POS_KW` = ["좋", "만족", "추천", "최고", "훌륭", "촉촉", "가성비", "재구매", "효과"]
  - `NEG_KW` = ["별로", "실망", "안 좋", "후회", "불만", "최악", "별점", "자극", "트러블"]
  - format_normalizer 가 부여한 `sentiment` 필드 (mock CSV 의 `감성` 컬럼 정규화 결과) — **POC 에서는 이게 사실상 정답**

## 로직 단계

1. `cleaned_texts` 조회
2. 각 text 에 대해:
   - **정규화 라벨 우선 사용** — `t.get("sentiment")` 가 있으면 그대로 채택
   - 없으면 **`_classify()` 규칙 폴백** — POS_KW 출현 수 > NEG_KW = positive, 반대 = negative, 동률 = neutral
   - 알 수 없는 라벨 → neutral 강제
3. 카운트 집계 (pos/neu/neg)
4. 분포 % 계산 (`round(... * 100, 1)`)
5. `logger.info("sentiment_analyzer completed", **distribution)` + 반환

## 예외 처리

| 상황 | 동작 |
|---|---|
| `cleaned_texts` 부재 | 빈 리스트 → distribution `total=0`, 비율은 0/1 division 회피 (`total or 1`) |
| text 가 `sentiment` 없고 cleaned_text 도 없음 | `_classify("")` → neutral |
| 라벨이 enum 외 값 | neutral 강제 |

## 의존 Tool

- **이전**: `text_preprocessor` (cleaned_texts 생성)
- **다음**: `insight_extractor` (sentiment_distribution 소비)
- **병렬 형제**: `keyword_extractor` (같은 cleaned_texts 소비, 독립 실행)

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 | 어떤 변경 시 |
|---|---|---|
| Tool 코드 | [`tools/analysis/ml/sentiment_analyzer.py`](../../../../backend/app/dream_agent/tools/analysis/ml/sentiment_analyzer.py) | 로직 / 키워드 |
| Tool 메타카드 | [`catalog/analysis/ml/sentiment_analyzer.yaml`](../../../../backend/app/dream_agent/tools/catalog/analysis/ml/sentiment_analyzer.yaml) | params / produces |
| **team_catalog.yaml** | `analysis_agent.tools[sentiment_analyzer]` | params_required / produces |
| LLM Prompts (stage3) | `planning_stage3_todo.yaml` | Tool 이름 / 예시 |
| LLM Prompts (response) | `response.yaml` | 예시 |
| **MVP KoBERT 교체 시** | 신규 모델 weight 의존성 + requirements.txt + `_classify` 메서드 교체 | D6 |
| 데이터 source | `data/description/mock/SCHEMA.md` review_trends `감성` 컬럼 | 라벨 enum 변경 시 |
| `format_normalizer.helpers.normalize_sentiment` | `tools/shared/helpers.py` | 라벨 매핑 룰 |
| **Spec 32 §7.1** | `agent_specs/32_*.md` | analysis 행 |
| **TOBE_MVP/01** | `tool/TOBE_MVP/01_tool_data_matrix.md` | Tool ↔ Data 행 |
| 본 폴더 agent 카드 | [`agents/05_analysis.md`](../../agents/05_analysis.md) | Tool 목록 |
| Tests | `backend/tests/sprint*/test_*sentiment*.py` | unit |

### 변경 종류별 최소 갱신
- **POS/NEG_KW 추가**: 상수만 (가장 안전 변경)
- **KoBERT 교체 (D6)**: 모델 로드 + inference 로직 + confidence 필드 채움 + `has_cost` true 변경 + ADR 박제
- **새 라벨 (mixed/very_positive)**: enum 확장 + 모든 다음 Tool 영향 (report_writer 분석 결과 표기 등)

## 참조 코드

- 구현: [`tools/analysis/ml/sentiment_analyzer.py`](../../../../backend/app/dream_agent/tools/analysis/ml/sentiment_analyzer.py)
- 메타: [`catalog/analysis/ml/sentiment_analyzer.yaml`](../../../../backend/app/dream_agent/tools/catalog/analysis/ml/sentiment_analyzer.yaml)
- helper: [`shared/helpers.py:find_in_previous`](../../../../backend/app/dream_agent/tools/shared/helpers.py)

## 참조 spec

- [agent_specs/17 §3 analysis](../../../agent_specs/17_functions_to_io_v1.0.md)
- [agent_specs/32 §7.1 analysis](../../../agent_specs/32_execution_agent_tools_v1.0.md)
- [TOBE_MVP/01 §2 analysis](../../../_claude/tool/TOBE_MVP/01_tool_data_matrix.md)
- [TOBE_MVP/03 D6 Acknowledged](../../../_claude/tool/TOBE_MVP/03_drift_report.md) — sentiment 방법론 추후

## 참조 비전 (한국어 narrative)

- [agent_design/04_분석_에이전트.md](../../../_claude/referrence/agent_design/04_분석_에이전트.md) — POC-07 감성 분석 비전

## 📍 Mock vs 실API 분기

- 외부 API 의존 없음 (규칙 기반) — 분기 불필요
- MVP KoBERT 도입 시: 모델 weight 외부 의존 (huggingface) — 캐싱 / 사전 다운로드 전략 필요

## 테스트

- 단위 부재 — POC 9 분석 모듈 보강 시 권장
- E2E: Planner 가 sentiment_distribution produces 검증
- DC-10: docstring Status 마커 미명시 (D6 박제와 함께 보강 권장)

## Phase

| Phase | 본 Tool 의 작업 |
|---|---|
| **Phase 0 (현재)** | ✅ implemented — 정규화 라벨 + 규칙 폴백 |
| **Phase 2** | 분석 1차 4 Tool 추가 (trend_analyzer / competitor_comparator 등 신규 — 본 Tool 은 안정 운영) |
| **MVP** | KoBERT 교체 검토 (D6 — 방법론 정의 필요) |

## Drift / 결정

- **D6** 🟢 Acknowledged — sentiment 방법론 추후 (POC 규칙 / MVP ML)
- POC 정확도 의존: format_normalizer 가 이미 부여한 라벨이 main 경로 — `_classify` 폴백은 라벨 없는 경우만

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안 — POC 정규화 라벨 우선 전략 박제 + DC-10 갭 박제 |
