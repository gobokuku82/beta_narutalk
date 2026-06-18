# 03. text_preprocessing_agent — 자연어 텍스트 8 단계 정제

## 메타

| 항목 | 값 |
|---|---|
| 소속 팀 | analysis_team |
| handles_tasks | `data_preprocessing` |
| Tool 수 | 1 implemented (통합) / MVP 시 8 단계 분리 |
| 현재 구현률 | ✅ 통합 100% (text_preprocessor 1 Tool 안에 8 단계 흡수) |
| team_catalog 위치 | `text_preprocessing_agent` 블록 |
| 분리 이유 | **D9 결정** — 자연어 자원 (한국어 형태소/슬랭/협찬) ↔ 광고 성과 도메인 분리 |

## 입출력

- **입력**: `raw_reviews` (collection_agent 출력)
- **출력**: `cleaned_texts` (list[dict] — 정제된 텍스트)
- **다음 에이전트**: analysis (sentiment / keyword)

## Tool 목록

| Tool | Status | 카드 | 비고 |
|---|---|---|---|
| text_preprocessor | ✅ implemented (통합) | [→](../tools/implemented/text_preprocessor.md) | 8 단계 통합 — HTML/URL/MD5 dedup 등 |

### MVP 시 8 단계 분리 예정 (Phase 1B / 2)

| Tool | 단계 | 역할 |
|---|---|---|
| emoji_handler | 1 | 이모지 제거/변환 (`emoji.demojize`) |
| repeat_char_normalizer | 2 | "ㅋㅋㅋㅋ" → "ㅋㅋ" |
| html_url_stripper | 3 | HTML/URL 제거 |
| sponsored_detector | 4 | "협찬/제공받/PR" → `is_sponsored=True` |
| length_filter | 5 | <5자 제거 / >500자 절단 |
| deduplicator | 6 | MD5 해시 dedup |
| language_detector | 7 | langdetect — POC ko 만 통과 |
| spell_corrector | 8 | py-hanspell (느림 — 배치 전용) |

## 데이터 흐름

```
[raw_reviews from collection]
       │
       ▼
text_preprocessor (통합 8 단계)
   1. emoji 제거/변환
   2. 반복 문자 정규화
   3. HTML/URL 제거
   4. 협찬 감지
   5. 길이 필터
   6. MD5 dedup
   7. 언어 감지 (ko)
   8. 맞춤법 정규화 (배치만)
       │
       ▼
cleaned_texts
   │
   ├──► sentiment_analyzer
   └──► keyword_extractor
```

## HITL 카테고리 (D12)

| 카테고리 | 본 에이전트 해당 | 비고 |
|---|---|---|
| 조회·자동 | ✅ (배치 자동 실행) | 일 1회 (리뷰 수집 후) |
| 생성 후 | — | |
| 실행 전 | — | |
| 외부 발송 | — | |

→ 자동. 게이트 없음.

## Phase 진입

| Phase | 본 에이전트의 작업 |
|---|---|
| Phase 0 (현재) | ✅ text_preprocessor 통합 implemented |
| **Phase 1B / 2** | 8 단계 분리 도입 (정확도 검증 후) |
| **MVP+** | 다국어 (en/ja) 지원 + 신조어 사전 확장 |

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 | 변경 시 |
|---|---|---|
| Tool 코드 | `tools/preprocessing/text_cleaning/text_preprocessor.py` | 정제 로직 |
| Tool YAML | `tools/catalog/preprocessing/text_cleaning/text_preprocessor.yaml` | params/produces |
| **team_catalog.yaml** | `text_preprocessing_agent` 블록 | Tool 추가/분리 |
| **LLM Prompts stage3** | `planning_stage3_todo.yaml` | text_preprocessor 예시 todo |
| **task_agent_hints** | `team_catalog.yaml` L234 `data_preprocessing: [text_preprocessing_agent, channel_normalizing_agent]` | 두 갈래 매핑 — Planner LLM 선택 |
| **Spec 32 §7.1** | text_preprocessor 행 | |
| **TOBE_MVP/01** | 매트릭스 text_preprocessing 행 | |
| **데이터 source** | (이전 Tool 출력만 — CSV 직독 없음) | |
| **신조어 사전** | (MVP 시 신규 자원) | 단어 추가 시 |
| **ADR** | 8 단계 분리 결정 시 | |
| Tests | `backend/tests/sprint*/test_*text_preprocess*.py` | |

## 참조 코드

- Tool 코드: [`tools/preprocessing/text_cleaning/text_preprocessor.py`](../../../backend/app/dream_agent/tools/preprocessing/text_cleaning/text_preprocessor.py)
- Tool YAML: [`tools/catalog/preprocessing/text_cleaning/text_preprocessor.yaml`](../../../backend/app/dream_agent/tools/catalog/preprocessing/text_cleaning/text_preprocessor.yaml)
- team_catalog: `text_preprocessing_agent` 블록

## 참조 spec

- [17 §2 9~10 에이전트](../../agent_specs/17_functions_to_io_v1.0.md)
- [32 §7.1 preprocessing 카테고리](../../agent_specs/32_execution_agent_tools_v1.0.md)
- [TOBE_MVP/02 text_preprocessing 카드](../../_claude/tool/TOBE_MVP/02_agent_cards.md)
- [TOBE_MVP/03 D9](../../_claude/tool/TOBE_MVP/03_drift_report.md) — 분리 결정 박제

## 참조 비전 (한국어 narrative)

- [agent_design/03_전처리_에이전트.md](../../_claude/referrence/agent_design/03_전처리_에이전트.md) §2-2 텍스트 클렌징 8단계

## 📍 Mock vs 실API 분기

본 에이전트는 외부 API 의존 X (자체 라이브러리). 단:
- POC: 규칙 기반 (기본 정제)
- MVP+: 신조어 사전 / 맞춤법 사전 외부 의존성 (py-hanspell 등)

## Drift / 결정

- **D9** 🟢 Decided — preprocessing 2 분리 (text_preprocessing + channel_normalizing), 2026-05-18 (commit 8ce2f3d)

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안. D9 분리 박제. |
