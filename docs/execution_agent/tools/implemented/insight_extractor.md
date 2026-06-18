# insight_extractor — LLM 인사이트 도출

> 감성 분포 + 키워드 → 마케팅 관점 핵심 인사이트 JSON 추출 (LLM).
> 분석 → 보고서 텍스트 체인의 **요약·해석 게이트** 역할.

## 메타

| 항목 | 값 |
|---|---|
| 소속 에이전트 | analysis_agent |
| 카테고리 (YAML) | `analysis` (폴더 `analysis/llm/`) |
| Status | ✅ implemented |
| 버전 | 0.1.0 |
| **Status 마커** (docstring) | ⚠️ **미명시** — 권장: `Status: complete — POC LLM-only, MVP에서 RAG (벡터DB) 결합 예정 (D8).` |
| **DC-10 정합** | docstring ⚠️ / YAML status 필드 없음 / team_catalog `status: implemented` |
| timeout_sec | 60 |
| max_retries | 2 |
| requires_approval | false |
| has_cost / estimated_cost | **true / 0.01** (LLM 호출) |

## 입출력 계약

### 입력 (params)

| name | type | required | default | 설명 |
|---|---|---|---|---|
| max_insights | integer | optional | `5` | 추출 인사이트 수 |

### 입력 (context)
- `context.previous_results` 에서:
  - `find_in_previous(..., "sentiment_distribution")` → 감성 분포
  - `find_in_previous(..., "top_keywords")` → 키워드

### 출력 (produces)
- `insights` (list[dict]) — title/description/importance/evidence
- 보조: `count`

### 출력 dict 스키마

```json
{
  "insights": [
    {
      "title": "보습력 만족도 65%",
      "description": "전체 감성 분포 중 positive 65%, 주요 키워드 '보습력/촉촉' 빈도 1·2위...",
      "importance": "high",
      "evidence": "sentiment.positive=65%, keywords[보습력]=42, keywords[촉촉]=38"
    }
  ],
  "count": 5
}
```

## 데이터 source

- **입력**: 이전 분석 Tool produces 2종 (sentiment_distribution + top_keywords)
- **LLM 호출**: `get_llm_client("execution")` — Claude/GPT (config 로 분기)
- **프롬프트**: 본 Tool 내부 `SYSTEM_PROMPT` + `USER_TEMPLATE`
  - System: "당신은 한국 화장품/뷰티 브랜드의 마케팅 분석 전문가입니다..."
  - User: sentiment + keywords JSON 임베드 → `max_insights` 개 JSON 형식 응답 요구

## 로직 단계

1. `max_insights` 병합 (default 5)
2. `sentiment_distribution` + `top_keywords` 조회
3. `USER_TEMPLATE.format(...)` — JSON 데이터 임베드
4. `get_llm_client("execution").generate_json(prompt, system_prompt)` 호출
5. result `{"insights": [...]}` → list 추출 (방어적 — dict 가 아닐 시 빈 리스트)
6. `logger.info(...)` + 반환

## 예외 처리

| 상황 | 동작 |
|---|---|
| sentiment_distribution / top_keywords 부재 | 빈 dict / 빈 list → 프롬프트에 빈 데이터 → LLM 이 그래도 일반론 응답 |
| LLM 응답이 dict 아님 | `result.get("insights", [])` 패턴 미적용 → 빈 리스트 |
| LLM 호출 실패 | `max_retries=2` 자동 재시도 → 그래도 실패 시 raise (executor 가 catch) |
| JSON 파싱 실패 | `generate_json()` 내부에서 retry 또는 raise |

## 의존 Tool

- **이전 (필수)**: `sentiment_analyzer` + `keyword_extractor` — 둘 다 cleaned_texts 소비, 본 Tool 은 둘 다 필요
- **다음**: `report_writer` (insights 소비)

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 | 어떤 변경 시 |
|---|---|---|
| Tool 코드 | [`tools/analysis/llm/insight_extractor.py`](../../../../backend/app/dream_agent/tools/analysis/llm/insight_extractor.py) | 로직 / 프롬프트 |
| Tool 메타카드 | [`catalog/analysis/llm/insight_extractor.yaml`](../../../../backend/app/dream_agent/tools/catalog/analysis/llm/insight_extractor.yaml) | params / produces / estimated_cost |
| **team_catalog.yaml** | `analysis_agent.tools[insight_extractor]` | params_required (현재 `[sentiment_distribution, top_keywords]` ✅) |
| LLM Prompts (stage3) | `planning_stage3_todo.yaml` | Tool 이름 |
| LLM Prompts (response) | `response.yaml` | 예시 |
| **LLM client config** | `llm_manager/client.py` + config | 모델/temperature/max_tokens 변경 시 |
| **프롬프트 내부 SYSTEM/USER** | 본 Tool .py 상수 | 도메인 전문 영역 변경 시 (현재 화장품/뷰티) |
| **MVP RAG 결합 (D8)** | 신규 vector_db 의존성 + 검색 단계 추가 | 인프라 sprint 필요 |
| **Spec 32 §7.1** | `agent_specs/32_*.md` | analysis 행 |
| **TOBE_MVP/01** | `tool/TOBE_MVP/01_tool_data_matrix.md` | Tool ↔ Data 행 |
| 본 폴더 agent 카드 | [`agents/05_analysis.md`](../../agents/05_analysis.md) | Tool 목록 |
| Tests | `backend/tests/sprint*/test_*insight*.py` | unit (mock LLM) |

### 변경 종류별 최소 갱신
- **`max_insights` 기본값 변경**: YAML default + 본 Tool 코드 default
- **시스템 프롬프트 도메인 변경** (예 식품): SYSTEM_PROMPT 수정 — 다른 영역 0
- **JSON 스키마 변경**: USER_TEMPLATE + produces 키 정의 + report_writer 입력 영향
- **RAG 결합 (D8)**: 새 의존성 + 인프라 + ADR

## 참조 코드

- 구현: [`tools/analysis/llm/insight_extractor.py`](../../../../backend/app/dream_agent/tools/analysis/llm/insight_extractor.py)
- 메타: [`catalog/analysis/llm/insight_extractor.yaml`](../../../../backend/app/dream_agent/tools/catalog/analysis/llm/insight_extractor.yaml)
- LLM client: [`llm_manager/client.py:get_llm_client`](../../../../backend/app/dream_agent/llm_manager/client.py)
- helper: [`shared/helpers.py:find_in_previous`](../../../../backend/app/dream_agent/tools/shared/helpers.py)

## 참조 spec

- [agent_specs/17 §3 analysis](../../../agent_specs/17_functions_to_io_v1.0.md)
- [agent_specs/32 §7.1 analysis](../../../agent_specs/32_execution_agent_tools_v1.0.md)
- [TOBE_MVP/01 §2 analysis](../../../_claude/tool/TOBE_MVP/01_tool_data_matrix.md)
- [TOBE_MVP/03 D8 Decided](../../../_claude/tool/TOBE_MVP/03_drift_report.md) — RAG 벡터DB 인프라

## 참조 비전 (한국어 narrative)

- [agent_design/04_분석_에이전트.md](../../../_claude/referrence/agent_design/04_분석_에이전트.md) — 인사이트 추출 비전

## 📍 Mock vs 실API 분기

- **LLM API 의존** — 분기 없음 (POC 부터 실 API)
- MVP RAG (D8): 벡터DB 신규 인프라 — Phase 4A 선결

## 테스트

- 단위 부재 (LLM mock 필요) — Phase 2 진입 시 권장
- E2E: Planner E2E 가 insights produces 검증
- DC-10: docstring Status 마커 미명시 (D8 박제와 함께 보강)

## Phase

| Phase | 본 Tool 의 작업 |
|---|---|
| **Phase 0 (현재)** | ✅ implemented — LLM-only |
| **Phase 4A** | RAG (벡터DB) 인프라 — 본 Tool 이 벡터 검색 결합 (D8) |
| **MVP** | 도메인별 시스템 프롬프트 다중 (화장품/식품/패션) |

## Drift / 결정

- **D8** 🟢 Decided — RAG (벡터DB) 인프라 sprint 필요 (Phase 4A 선결)
- **이유**: 인사이트 정확도 (사실 hallucination 방지) — 과거 사례 검색

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안 — D8 RAG 미래 박제 + DC-10 갭 박제 |
