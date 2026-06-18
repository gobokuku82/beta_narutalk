# 33. Preprocessing tools — 인벤토리

| 항목 | 내용 |
|---|---|
| 카테고리 | **preprocessing** |
| 의도 (32 §2.5) | 자연어 텍스트 전처리 (리뷰·블로그 한정) |
| 핵심 동사 | tokenize, strip, normalize_text |
| 출력 모양 | 정제된 텍스트/토큰 |
| 짝 문서 | [32 §2.5](../32_execution_agent_tools_v1.0.md) |
| tool 수 | **1** (2026-05-30) |

## 판정 기준 (자연어 한정)

- **자연어 텍스트** 처리 = preprocessing ✅
- 정형 데이터(DataFrame) 처리 = **cleaning** 또는 **normalization**
- 텍스트 기반 *추론*(감성·키워드 추출) = **analysis**

## tool 목록

| name | input | output | status | 의도 |
|---|---|---|---|---|
| text_preprocessor | normalized_reviews (review_normalizer 출력) | cleaned_texts (list[dict]) | complete | 리뷰 텍스트 통합 클렌징 (sponsored 필터·이모지·HTML·중복 dedup) |

## 향후 진입 후보

| 후보 tool | 의도 |
|---|---|
| `tokenizer_ko` | KoNLPy/Mecab 기반 형태소 분석 |
| `stopword_remover` | 불용어 제거 (감성·키워드 추출 전처리) |
| `blog_html_stripper` | 블로그 HTML → 텍스트 (스크래핑 후) |

→ MVP+ 8 단계 분리 (emoji_handler / repeat_char_normalizer 등) 시 신설.

## anti-pattern

- **정형 데이터 처리** — DataFrame 컬럼 정제는 cleaning 으로.
- **추론 섞음** — 토큰화 + 감성 분석 동시. → preprocessing 은 *전처리만*, 감성은 analysis.

## 변경 이력

- 2026-05-30: preprocessing/text_cleaning/ sub-folder 폐기 — text_preprocessor 가 preprocessing/ 직속으로 승격.
