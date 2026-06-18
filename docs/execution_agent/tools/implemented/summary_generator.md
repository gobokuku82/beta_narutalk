# summary_generator — 한 문장 LLM 요약

> 분석 결과 전체를 한국어 한 문장(100자 이내)으로 압축.
> 공유 Tool (`shared` 카테고리) — 여러 에이전트에서 호출 가능.

## 메타

| 항목 | 값 |
|---|---|
| 소속 에이전트 | report_text_agent (D13 분리) |
| 카테고리 (YAML) | `content` (폴더 `shared/`) — **공유 Tool** |
| Status | ✅ implemented |
| 버전 | 0.1.0 |
| **Status 마커** (docstring) | ⚠️ **미명시** — 권장: `Status: complete — POC LLM 한 문장.` |
| **DC-10 정합** | docstring ⚠️ / YAML status 필드 없음 / team_catalog `status: implemented` |
| timeout_sec | 30 |
| max_retries | 2 |
| requires_approval | false |
| has_cost / estimated_cost | **true / 0.005** (LLM 호출, 짧음) |

## 입출력 계약

### 입력 (params)

| name | type | required | default | 설명 |
|---|---|---|---|---|
| max_length | integer | optional | `100` | 요약 최대 글자수 (그 이상 자름) |

### 입력 (context)
- `context.previous_results` 전체 자동 스캔 — `_collect_payload()` 가 4 키 (`sentiment_distribution`, `top_keywords`, `insights`, `report_text`) 중 발견되는 것 수집

### 출력 (produces)
- `summary` (string) — 한 문장, max_length 이내, 따옴표/줄바꿈 제거

### 출력 dict 스키마

```json
{ "summary": "블루밍글로우 9월 리뷰는 보습력·촉촉 키워드 중심으로 positive 65% 분포..." }
```

## 데이터 source

- **입력**: previous_results 의 4 키 자동 수집 (dependencies 명시 안 함 — implicit)
- **LLM 호출**: `get_llm_client("execution")`
- **프롬프트**: 본 Tool 내부
  - System: "당신은 마케팅 분석 결과를 한 문장으로 간결하게 요약하는 전문가입니다."
  - User: payload JSON 임베드 + 한 문장 요구 + 따옴표/줄바꿈 금지

## 로직 단계

1. params 병합 (`max_length=100`)
2. `_collect_payload(previous)` — 4 키 자동 수집 (먼저 발견된 값 사용)
3. payload JSON 직렬화 (`ensure_ascii=False, default=str, [:3000]` — token 보호)
4. `client.generate(prompt, system_prompt)` 호출
5. 정제: `strip()` + 양쪽 따옴표 제거 (`strip('"')`) + 첫 줄만 (`splitlines()[0]`) + max_length 절단
6. `logger.info(...)` + 반환

### _collect_payload 로직 (`tools/shared/summary_generator.py:49`)

```python
keep = ["sentiment_distribution", "top_keywords", "insights", "report_text"]
for result in previous.values():
    data = result.get("data") if isinstance(result, dict) else None
    src = data if isinstance(data, dict) else (result if isinstance(result, dict) else {})
    for k in keep:
        if k in src and k not in out:
            out[k] = src[k]
```

→ executor 의 `tool_result.data` 패턴 + 직접 dict 패턴 둘 다 수용 (방어적).

## 예외 처리

| 상황 | 동작 |
|---|---|
| previous_results 부재 / 4 키 모두 없음 | 빈 payload → LLM 일반론 또는 빈 응답 |
| LLM 응답이 여러 줄 | 첫 줄만 채택 |
| 응답 max_length 초과 | 절단 (`[:max_length]`) |
| LLM 호출 실패 | `max_retries=2` 재시도 → 실패 시 raise |

## 의존 Tool

- **이전**: implicit — analysis/insight/report 의 임의 조합 (4 키 중 하나라도 있으면 동작)
- **다음**: chat_hub (사용자 응답 — 짧은 요약 UI 표시)
- **YAML dependencies**: `[]` (의존 명시 안 함 — Planner 가 task_type `summary_generation` 으로 호출)

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 | 어떤 변경 시 |
|---|---|---|
| Tool 코드 | [`tools/shared/summary_generator.py`](../../../../backend/app/dream_agent/tools/shared/summary_generator.py) | 로직 / 프롬프트 / payload 키 |
| Tool 메타카드 | [`catalog/shared/summary_generator.yaml`](../../../../backend/app/dream_agent/tools/catalog/shared/summary_generator.yaml) | params / produces / cost |
| **team_catalog.yaml** | `report_text_agent.tools[summary_generator]` | params_required (현 `[analysis_results]` vs 실 코드 implicit — **단순화 박제**) / produces (`summary_text` vs 실 `summary` — **mismatch 박제**) |
| LLM Prompts (stage3) | `planning_stage3_todo.yaml` | task_type `summary_generation` 매핑 |
| LLM Prompts (response) | `response.yaml` | 예시 |
| **다른 에이전트에서도 사용** | task_type `summary_generation` 매핑 hint (team_catalog L297) | summary 도 chat_hub 가 호출 가능 |
| **`_collect_payload` 키 추가** | 새 ChatGPT/분석 키 (e.g., `competitor_summary`) | keep 리스트 확장 |
| **Spec 32 §7.1** | `agent_specs/32_*.md` | content/shared 행 |
| **TOBE_MVP/01** | `tool/TOBE_MVP/01_tool_data_matrix.md` | Tool ↔ Data 행 |
| 본 폴더 agent 카드 | [`agents/08_report_text.md`](../../agents/08_report_text.md) | Tool 목록 |
| Tests | `backend/tests/sprint*/test_*summary*.py` | unit (mock LLM) |

### 변경 종류별 최소 갱신
- **`max_length` 기본값 변경**: YAML default + 코드 default
- **새 payload 키 (예 `chart_caption`)**: `_collect_payload.keep` 리스트만
- **다국어 요약 (영문)**: SYSTEM 다국어 처리 + language param 추가
- **payload truncate 길이 (3000 → 5000)**: 코드 상수만 — token 비용 영향

## 참조 코드

- 구현: [`tools/shared/summary_generator.py`](../../../../backend/app/dream_agent/tools/shared/summary_generator.py)
- 메타: [`catalog/shared/summary_generator.yaml`](../../../../backend/app/dream_agent/tools/catalog/shared/summary_generator.yaml)
- LLM client: [`llm_manager/client.py:get_llm_client`](../../../../backend/app/dream_agent/llm_manager/client.py)

## 참조 spec

- [agent_specs/17 §3 report_text](../../../agent_specs/17_functions_to_io_v1.0.md)
- [agent_specs/32 §7.1 content/shared](../../../agent_specs/32_execution_agent_tools_v1.0.md)
- [TOBE_MVP/01 §2 report](../../../_claude/tool/TOBE_MVP/01_tool_data_matrix.md)
- [TOBE_MVP/03 D13](../../../_claude/tool/TOBE_MVP/03_drift_report.md)

## 참조 비전 (한국어 narrative)

- [agent_design/01_에이전트_채팅_허브.md](../../../_claude/referrence/agent_design/01_에이전트_채팅_허브.md) — 채팅 요약 표시 비전

## 📍 Mock vs 실API 분기

- **LLM API 의존** — 분기 없음 (POC 부터 실 API)
- 비용: 한 문장 ~0.005 USD (짧음)

## 테스트

- 단위 부재 (LLM mock 필요)
- E2E: Planner 가 summary produces 검증
- DC-10: docstring Status 마커 미명시

## Phase

| Phase | 본 Tool 의 작업 |
|---|---|
| **Phase 0 (현재)** | ✅ implemented — implicit payload 수집 |
| **Phase 5 (Chat Hub)** | chat_hub 가 summary 를 채팅 UI 에 표시 (HITL 4 카테고리 중 조회/자동) |
| **MVP** | 도메인별 톤 (formal/casual) |

## Drift / 결정

- **team_catalog mismatch 박제** (D13 분리 시 미정정):
  - params_required `[analysis_results]` (단일) vs 실 코드 implicit 자동 수집
  - produces `[summary_text]` vs 실 `[summary]` (키 mismatch)
  - 통일 권장 (다음 sprint)
- **`shared/` 카테고리 의도** — 여러 에이전트에서 재사용 (report_text_agent 외 chat_hub 등)

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안 — implicit payload 패턴 박제 + produces 키 mismatch 박제 + DC-10 갭 박제 |
