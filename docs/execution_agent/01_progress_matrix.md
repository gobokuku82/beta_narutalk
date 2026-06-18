# 01. Progress Matrix — 버전별 실행 에이전트/Tool 진행 매트릭스

> **본 문서의 역할**: 시간축으로 "지금 몇 에이전트 / 몇 Tool 완성?" 의 단일 진실 소스.
> 사용자 표현: "v1 = 10 에이전트 8 Tool → v2 = 10 에이전트 22 Tool → 피벗 4 에이전트 33 Tool 변경 ..." 같은 매트릭스.
>
> **갱신 트리거**: 매 commit (Tool 추가/rename/폐기) 시 + Phase 진입 시.

---

## 1. 현재 — v0.2 (2026-05-18 박제, 4 commit) ⭐

| 항목 | 값 |
|---|---|
| **에이전트 (team_catalog 안)** | **11** (analysis_team 7 + creative_team 4) — chat_hub 별개 |
| **에이전트 (비전 카운트)** | **10** (chat_hub + analysis 7 + creative 2: image/storyboard) |
| **Tool implemented** | **8** ✅ |
| **Tool stub** | ~34 (mock_tools fallback 가능) |
| **Tool planned** | ~30 (요구사항만, mock 도 없음) |
| **회귀** | Planner test 45 pass (sprint13~14) |

### 1.1 v0.2 의 implemented 8 Tool

| Tool | Agent | 코드 | 카드 |
|---|---|---|---|
| review_collector | collection | [tools/collection/review_collector.py](../../backend/app/dream_agent/tools/collection/review_collector.py) | [→](tools/implemented/review_collector.md) |
| format_normalizer | channel_normalizing | [tools/preprocessing/data_normalization/format_normalizer.py](../../backend/app/dream_agent/tools/preprocessing/data_normalization/format_normalizer.py) | [→](tools/implemented/format_normalizer.md) |
| text_preprocessor | text_preprocessing | [tools/preprocessing/text_cleaning/text_preprocessor.py](../../backend/app/dream_agent/tools/preprocessing/text_cleaning/text_preprocessor.py) | [→](tools/implemented/text_preprocessor.md) |
| sentiment_analyzer | analysis | [tools/analysis/ml/sentiment_analyzer.py](../../backend/app/dream_agent/tools/analysis/ml/sentiment_analyzer.py) | [→](tools/implemented/sentiment_analyzer.md) |
| keyword_extractor | analysis | [tools/analysis/ml/keyword_extractor.py](../../backend/app/dream_agent/tools/analysis/ml/keyword_extractor.py) | [→](tools/implemented/keyword_extractor.md) |
| insight_extractor | analysis | [tools/analysis/llm/insight_extractor.py](../../backend/app/dream_agent/tools/analysis/llm/insight_extractor.py) | [→](tools/implemented/insight_extractor.md) |
| report_writer | report_text | [tools/report/report_writer.py](../../backend/app/dream_agent/tools/report/report_writer.py) | [→](tools/implemented/report_writer.md) |
| summary_generator | report_text | [tools/shared/summary_generator.py](../../backend/app/dream_agent/tools/shared/summary_generator.py) | [→](tools/implemented/summary_generator.md) |

---

## 2. 버전 진행 매트릭스 — v0.x → MVP

> 누적 카운트. 각 버전 끝의 **Demo 1 시나리오** 가 mock 으로 동작해야 다음 버전 진입.

| 버전 | 시점 | 에이전트 | Tool impl 누적 | 신규 Tool (해당 버전) | Demo 시나리오 | 비고 |
|---|---|---|---|---|---|---|
| **v0.1** | 2026-04-13 | 9 (옛 7) | **8** | 초기 8 | 네이버 리뷰 감성 분석 | `tool_plan_poc_260413.md` |
| **v0.2** ⭐ 현재 | 2026-05-18 | **10** (D9+D13 Y) | **8** | 0 (구조 변경 + rename) | 동일 + 10 에이전트 라우팅 | commit 8ce2f3d/0c89933/5537c08/2138798 |
| **v0.3** (Phase 1A) | M2 데이터 도착 후 | 10 | **14** | +6 수집 (youtube/coupang/oliveyoung/naver_sa/meta/external) | "어제 데이터 수집해줘" — 매체별 통합 | 7 raw 매체 + external_variables |
| **v0.4** (Phase 1B) | v0.3 후속 | 10 | **18** | +4 전처리 (kpi_calculator/anomaly_flagger/creative_history/external_joiner) | daily_performance 통합 16 컬럼 동작 | 4 채널 매핑 룰 흡수 |
| **v0.5** (Phase 2) | v0.4 후속 | 10 | **22** | +4 분석 1차 (POC-01/03/04/06) — kpi_anomaly_detector/roas_cause/fatigue/zero_conv_keyword | "어제 ROAS 왜 떨어졌어?" → 원인 TOP3 | 대시보드 + 비용최적화 + 소재 4 시나리오 |
| **v0.6** (Phase 3) | v0.5 후속 | 10 | **27** | +5 분석 2차 (POC-02/05/07/08/09) — kpi_forecaster/ab_test_runner/sentiment 강화/trend_spike/insight_synthesizer | "이번 달 리포트 만들어줘" → markdown 출력 | 9 분석 모듈 fully wired |
| **v0.7** (Phase 4A) | v0.6 후속 | 10 | **33** | +6 이미지 (RAG 선결: brand_guideline_analyzer + ad_image_generator + image_resizer + thumbnail_creator + background_editor + creative_quality_scorer) | "CICA 봄 소재 만들어줘" → 3 시안 + 5축 채점 | DALL-E 3 + Vision API |
| **v0.8** (Phase 4B) | v0.7 후속 | 10 | **36** | +3 스토리보드 (storyboard_planner / frame_image_generator / storyboard_composer) | "수분크림 15초 광고 스토리보드" | 4 씬 Hook-Value-Result-CTA |
| **v0.9** (Phase 4C) | v0.8 후속 | 10 | **44** | +8 출력물 (pdf 5: pdf_renderer/chart_generator/template_selector/word_filler/excel_filler + ppt 3: pptx_generator/slide_designer/chart_to_slide) | "리포트 + 소재 + 스토리보드 PPT" | PDF/Word/Excel/PPT 다출력 |
| **v1.0 — MVP 1차** (Phase 5) | v0.9 후속 | 10 | **44+** | Tool 신규 없음 — chat_hub + 11 매트릭스 + HITL 4 카테고리 wired | 대시보드 "상세 분석 보기" 클릭 → 채팅 자동 진입 → 답변 | spec 16/64 신규 |
| **v1.1+ MVP 가동** (Phase 6+) | 권한 확보 후 매체별 | 10 | 44+ | mock → 실API 전환 (매체별 sprint) | 실 메타 API 데이터 분석 | API 표면 동결 |

→ 누적 Tool 카운트: 8 → 14 → 18 → 22 → 27 → 33 → 36 → 44 → MVP.

---

## 3. 피벗 시 매트릭스 (사용자 표현 시나리오)

> 사용자 예시: "10 에이전트 22 Tool → 피벗 4 에이전트 33 Tool 변경"
>
> 피벗 = 비전 변경 / 카테고리 재정렬 / 큰 재구성. [agent_specs/41 §6 예시](../agent_specs/41_agent_tool_change_hub_v1.0.md).

### 3.1 피벗 종류

| 피벗 | 예시 | 영향 |
|---|---|---|
| **에이전트 카운트 변경** | 10 → 8 (creative_team 의 copy/material → image 흡수) | team_catalog + LLM Prompts + 카드 일괄 |
| **카테고리 재정렬** | 7 카테고리 → 12 카테고리 | team_catalog 전면 재작성 |
| **Tool 폐기 + 신규** | 옛 Tool 5 폐기 + 신규 Tool 8 도입 | rename + git history 보존 |
| **에이전트 분리/합병** | D9 (preprocessing 2 분리) / D13 (레포팅 2 갈래) | task_agent_hints 갱신 |
| **v1 → v2 메이저** | 컨벤션 자체 변경 | `tools/v2/` 폴더 신설 + 공존 |

### 3.2 피벗 시 변경 카운트 표 (예시)

| 피벗 | Before | After | 작업량 (sprint) | 절차 |
|---|---|---|---|---|
| D9 + D13 Y (2026-05-18 완료) | 7 에이전트 / 8 Tool | 10 에이전트 / 8 Tool | 1 sprint (4 commit) | ✅ [41 §3.C+E](../agent_specs/41_agent_tool_change_hub_v1.0.md) |
| creative_team 정리 (Q4 추후) | 10 / 8 | 8 / 8 (copy/material → image 흡수) | 0.5 sprint | [40 §3.C](../agent_specs/40_agent_tool_lifecycle_v1.0.md) |
| (가상) 카테고리 7→12 재정렬 | 7 카테고리 50 Tool | 12 카테고리 33 Tool | 1~2 sprint | [41 §6 예시](../agent_specs/41_agent_tool_change_hub_v1.0.md) |
| (가상) v1 → v2 메이저 | 10 / N | 신규 / M | 2~3 sprint | [40 §3.E + §4](../agent_specs/40_agent_tool_lifecycle_v1.0.md) |

---

## 4. 각 버전의 commit / ADR / 변경 자취

| 버전 | 주요 commit / ADR / 자취 |
|---|---|
| v0.1 (2026-04-13) | [`tool_plan_poc_260413.md`](../_claude/tool/tool_plan_poc_260413.md), [`tool_plan_full_260413.md`](../_claude/tool/tool_plan_full_260413.md), `tool_catalog_master.csv` |
| **v0.2** (2026-05-18) ⭐ | commit 8ce2f3d (team_catalog 10 에이전트 + LLM Prompts) / 0c89933 (spec 17/40/41/42) / 5537c08 (dead code) / 2138798 (naver→review rename) / [TOBE_MVP/04 v1.3 migration plan](../_claude/tool/TOBE_MVP/04_migration_plan_2026-05-18.md) / [03 D9 + D13 Drift](../_claude/tool/TOBE_MVP/03_drift_report.md) |
| v0.3 (Phase 1A) | (예정) commit M2 신규 데이터 + 6 collector 신규 + ADR (실API 전환 결정) |
| v0.4 (Phase 1B) | (예정) commit 채널 정규화 4 Tool + format_normalizer 확장 |
| v0.5 (Phase 2) | (예정) commit 분석 1차 4 Tool + POC-01/03/04/06 |
| v0.6 (Phase 3) | (예정) commit 분석 2차 5 Tool + KoBERT 도입 결정 ADR |
| v0.7 (Phase 4A) | (예정) commit 이미지 6 Tool + RAG 인프라 sprint + D8 ADR |
| v0.8 (Phase 4B) | (예정) commit 스토리보드 3 + Q4 video→storyboard rename |
| v0.9 (Phase 4C) | (예정) commit PDF 5 + PPT 3 + ADR (python-pptx 도입) |
| v1.0 MVP 1차 (Phase 5) | (예정) commit 채팅 허브 + 11 매트릭스 + HITL 4 카테고리 + spec 16/64 |
| v1.1+ MVP 가동 (Phase 6+) | (예정) commit 매체별 실API + ROADMAP Phase 2 박제 |

---

## 5. 검증 명령 (각 버전 박제 시)

```bash
# 회귀 (모든 버전 공통)
.\.venv\Scripts\python.exe -m pytest backend/tests/sprint13 backend/tests/sprint14 backend/tests/sprint15 -q

# Planner-related 빠른 회귀 (Phase A+B 같은 큰 변경 후)
.\.venv\Scripts\python.exe -m pytest backend/tests/sprint13 backend/tests/sprint14/ -q -k "planner or planning or todo"

# Tool implemented 카운트 verification (수동)
ls backend/app/dream_agent/tools/catalog/*/  # YAML 8개
ls backend/app/dream_agent/tools/*/*.py      # .py 8개
```

→ 회귀 통과 + Tool 카운트 일치 = 버전 박제 완료.

---

## 6. 갱신 정책

| 트리거 | 본 매트릭스 갱신 |
|---|---|
| Tool 신규 implemented | §1 표 + §2 매트릭스 (해당 버전 행 갱신) |
| Tool rename | §1 표 (이름) + §2 매트릭스 (비고 행) |
| Tool 폐기 | §1 표 (제거) + §2 매트릭스 (신규 버전 행 + 폐기 표기) |
| 에이전트 추가/분리/합병 | §1 에이전트 카운트 + §2 매트릭스 + §3 피벗 표 |
| 피벗 발생 | §3 피벗 표 신규 행 |
| 다음 Phase 진입 | §2 의 해당 버전 (v0.3, v0.4 ...) 행을 "현재" 로 갱신 |

---

## 7. 추적 — "지금 X 에이전트 Y Tool" 자동 확인

```bash
# 에이전트 카운트 (team_catalog)
grep -c "^      [a-z_]*_agent:" backend/app/dream_agent/planning/catalog/team_catalog.yaml

# Tool implemented (yaml status: implemented)
grep -l "status: implemented" backend/app/dream_agent/tools/catalog/**/*.yaml | wc -l

# .py vs YAML 정합 (DC-10 검증의 일부)
ls backend/app/dream_agent/tools/*/*.py | wc -l   # .py 카운트
find backend/app/dream_agent/tools/catalog -name "*.yaml" ! -name "_*" | wc -l   # YAML 카운트
```

→ 결과를 본 매트릭스의 §1 과 비교해 drift 검출.

---

## 8. 관련 자료

- [03_gap_and_roadmap](../_claude/tool/03_gap_and_roadmap.md) — POC → MVP 6 Phase 로드맵
- [TOBE_MVP/04_migration_plan_2026-05-18](../_claude/tool/TOBE_MVP/04_migration_plan_2026-05-18.md) — v0.1 → v0.2 변경 계획서 (Phase A+B+C+E+F)
- [agent_specs/41 Change Hub](../agent_specs/41_agent_tool_change_hub_v1.0.md) — 피벗 절차
- [agent_specs/40 Lifecycle](../agent_specs/40_agent_tool_lifecycle_v1.0.md) — 변경 시나리오 5종

---

## 9. 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-19 | 초안 — v0.1 / v0.2 박제 + v0.3~v1.1+ 예측 매트릭스 + 피벗 시나리오 3종 + 검증 명령 |
