# 33. Analysis tools — 인벤토리

| 항목 | 내용 |
|---|---|
| 카테고리 | **analysis** |
| 의도 (32 §2.5) | LLM·ML·통계 기반 추론 (감성·점수·키워드·예측) |
| 핵심 동사 | infer, score, classify, recommend |
| 출력 모양 | 추론 결과 dict |
| 짝 문서 | [32 §2.5](../32_execution_agent_tools_v1.0.md) |
| tool 수 | **9** (2026-05-31, ml/ 2 + llm/ 1 sub-folder 포함) |

## 판정 기준 (vs metrics·comparison)

- 산식이 명확 (SUM·AVG·MoM) = **metrics·comparison**
- 모델/규칙 기반 *추론* (감성=긍정/부정, 키워드 추출, 추천 등) = analysis ✅

## 3 sub-category (내부 분류, 추후 sub-folder 가능)

| sub | 의도 | 도구 종류 |
|---|---|---|
| **일반분석** | 통계·규칙 기반 추론 | scipy·heuristic |
| **ML 분석** | 학습 모델 기반 | scikit-learn·KoBERT 등 |
| **LLM 분석** | LLM 호출 기반 | Claude·GPT 등 |

> 현재 sub-folder 없음. tool 수 늘어나면 sub-folder 재구성.

## tool 목록

### 일반/LLM (직속 6)

| name | sub | input | output | status | 의도 |
|---|---|---|---|---|---|
| review_sentiment | LLM/ML | reviews | score+label | complete | 리뷰 감성 분석 |
| review_keywords | ML | reviews | keywords list | complete | 리뷰 키워드 추출 |
| review_recent | 일반 | reviews | recent list | complete | 최근 리뷰 |
| creative_ai_axes | LLM | creatives | scores by axis | complete | 소재 AI 축 점수 |
| creative_fatigue | 일반 | creatives | fatigue score | complete | 소재 피로도 |
| ai_recommendation | LLM | metrics+context | recommendation text | complete | AI 추천 |

### ml/ sub-folder (2)

| name | input | output | status | 의도 |
|---|---|---|---|---|
| sentiment_analyzer | normalized_reviews | sentiment_distribution | complete | (review_sentiment 와 별 ML 구현 — POC 라인) |
| keyword_extractor | cleaned_texts | keywords·top_keywords | complete | (review_keywords 와 별 ML 구현 — POC 라인) |

### llm/ sub-folder (1)

| name | input | output | status | 의도 |
|---|---|---|---|---|
| insight_extractor | analysis_results | insights list | complete | LLM 기반 인사이트 추출 (분석 결과 → 텍스트 인사이트) |

## anti-pattern

- **추론 X 인데 analysis** — 단순 평균은 metrics, MoM 은 comparison. analysis 는 *모델/규칙* 사용.
- **mock 만 있고 ML 모델 없음** — `ml_models` 가 mock 인지 실 모델인지 명시. status = partial 표기.
- **LLM 응답 그대로 노출** — 출력 schema (점수·라벨 등) 로 구조화 후 반환.

## 변경 이력

- 2026-05-31: ml/ 2 (sentiment_analyzer·keyword_extractor) + llm/ 1 (insight_extractor) sub-folder 추가 박제 — 작업 ④-L7 정합.
- 2026-05-30: 작업 ③ 의 직속 6 tool 초기 박제.
