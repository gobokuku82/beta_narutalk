# keyword_extractor — 빈도 기반 한글 키워드 추출

> POC = Counter + STOPWORDS. MVP = TF-IDF / KeyBERT / KR-WordRank 도입.

## 메타

| 항목 | 값 |
|---|---|
| 소속 에이전트 | analysis_agent |
| 카테고리 (YAML) | `analysis` (폴더 `analysis/ml/`) |
| Status | ✅ implemented |
| 버전 | 0.1.0 |
| **Status 마커** (docstring) | ⚠️ **미명시** — 권장: `Status: partial — POC Counter. MVP TF-IDF/KeyBERT 예정.` |
| **DC-10 정합** | docstring ⚠️ / YAML status 필드 없음 / team_catalog `status: implemented` |
| timeout_sec | 30 |
| max_retries | 1 |
| requires_approval | false |
| has_cost / estimated_cost | false / 0.0 |

## 입출력 계약

### 입력 (params)

| name | type | required | default | 설명 |
|---|---|---|---|---|
| top_k | integer | optional | `10` | 상위 K 키워드 |
| min_chars | integer | optional | `2` | 최소 글자수 (1 = 단음절 포함) |

### 입력 (context)
- `context.previous_results` 에서 `find_in_previous(..., "cleaned_texts")` 조회

### 출력 (produces)
- `top_keywords` (list[dict]) — keyword/count/rank
- 보조: `total_tokens`, `unique_tokens`

### 출력 dict 스키마

```json
{
  "top_keywords": [
    {"keyword": "보습력", "count": 42, "rank": 1},
    {"keyword": "촉촉", "count": 38, "rank": 2}
  ],
  "total_tokens": 1234, "unique_tokens": 287
}
```

## 데이터 source

- **입력**: `cleaned_texts` (text_preprocessor 출력)
- **로직 자원**:
  - 정규식 `[가-힣]{2,}` (한글 2자 이상) — `min_chars` 로 조정
  - `STOPWORDS` 집합 (21개) — "이거", "저거", "정말", "진짜", ...

## 로직 단계

1. params 병합 (`top_k=10`, `min_chars=2`)
2. `cleaned_texts` 조회
3. 정규식 컴파일: `rf"[가-힣]{{{min_chars},}}"`
4. 모든 cleaned_text 에서 토큰 추출 (`pattern.findall`)
5. STOPWORDS 제거
6. `Counter(words).most_common(top_k)` → rank 부여
7. `logger.info(...)` + 반환

## 예외 처리

| 상황 | 동작 |
|---|---|
| `cleaned_texts` 부재 | 빈 리스트 → top_keywords=[], total/unique=0 |
| 모든 단어가 STOPWORDS | top_keywords=[] (정상 — 매우 드문 케이스) |
| `min_chars=0` 또는 음수 | 정규식이 invalid → 예외 raise (BaseTool 에서 catch) — 미가드 |

## 의존 Tool

- **이전**: `text_preprocessor` (cleaned_texts 생성)
- **다음**: `insight_extractor` (top_keywords 소비)
- **병렬 형제**: `sentiment_analyzer` (같은 입력, 독립 실행)

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 | 어떤 변경 시 |
|---|---|---|
| Tool 코드 | [`tools/analysis/ml/keyword_extractor.py`](../../../../backend/app/dream_agent/tools/analysis/ml/keyword_extractor.py) | 로직 / STOPWORDS |
| Tool 메타카드 | [`catalog/analysis/ml/keyword_extractor.yaml`](../../../../backend/app/dream_agent/tools/catalog/analysis/ml/keyword_extractor.yaml) | params / produces |
| **team_catalog.yaml** | `analysis_agent.tools[keyword_extractor]` | params_required / params_optional / produces |
| LLM Prompts (stage3) | `planning_stage3_todo.yaml` | Tool 이름 |
| LLM Prompts (response) | `response.yaml` | 예시 |
| **MVP TF-IDF/KeyBERT 시** | requirements.txt (sklearn / sentence-transformers) + 로직 교체 + `has_cost` 변경 (모델 inference 비용) |
| 데이터 source | `data/description/mock/SCHEMA.md` review_trends | text 컬럼 |
| **Spec 32 §7.1** | `agent_specs/32_*.md` | analysis 행 |
| **TOBE_MVP/01** | `tool/TOBE_MVP/01_tool_data_matrix.md` | Tool ↔ Data 행 |
| 본 폴더 agent 카드 | [`agents/05_analysis.md`](../../agents/05_analysis.md) | Tool 목록 |
| Tests | `backend/tests/sprint*/test_*keyword*.py` | unit |

### 변경 종류별 최소 갱신
- **STOPWORDS 추가**: 상수만 — 다른 영역 0
- **min_chars 기본값 변경 (2→1)**: YAML default + 검증 (성능/노이즈 영향)
- **TF-IDF 교체**: 로직 + 의존성 + has_cost true (POC → 0 / MVP → +cost)
- **다국어 (영문 키워드 추가)**: 정규식 변경 `[a-zA-Z가-힣]{...}` + STOPWORDS 영문 추가

## 참조 코드

- 구현: [`tools/analysis/ml/keyword_extractor.py`](../../../../backend/app/dream_agent/tools/analysis/ml/keyword_extractor.py)
- 메타: [`catalog/analysis/ml/keyword_extractor.yaml`](../../../../backend/app/dream_agent/tools/catalog/analysis/ml/keyword_extractor.yaml)
- helper: [`shared/helpers.py:find_in_previous`](../../../../backend/app/dream_agent/tools/shared/helpers.py)

## 참조 spec

- [agent_specs/17 §3 analysis](../../../agent_specs/17_functions_to_io_v1.0.md)
- [agent_specs/32 §7.1 analysis](../../../agent_specs/32_execution_agent_tools_v1.0.md)
- [TOBE_MVP/01 §2 analysis](../../../_claude/tool/TOBE_MVP/01_tool_data_matrix.md)

## 참조 비전 (한국어 narrative)

- [agent_design/04_분석_에이전트.md](../../../_claude/referrence/agent_design/04_분석_에이전트.md) — 키워드 추출 비전

## 📍 Mock vs 실API 분기

- 외부 API 의존 없음 (정규식 + Counter) — 분기 불필요
- MVP TF-IDF: corpus 통계 의존 — 학습 데이터 source 필요 (POC 누적 데이터)

## 테스트

- 단위 부재 — Phase 2 진입 시 STOPWORDS 효과 검증 권장
- E2E: Planner 가 top_keywords produces 검증
- DC-10: docstring Status 마커 미명시

## Phase

| Phase | 본 Tool 의 작업 |
|---|---|
| **Phase 0 (현재)** | ✅ implemented — Counter |
| **Phase 2** | 분석 1차 4 Tool 추가 — 본 Tool 안정 운영 |
| **MVP** | TF-IDF / KeyBERT / KR-WordRank 검토 |

## Drift / 결정

- POC 의도된 단순 알고리즘 (Counter) — 데이터가 작아 충분
- MVP+ 정확도 필요 시 ML 교체 (D6 와 같은 결정 패턴)

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안 — DC-10 갭 박제 |
