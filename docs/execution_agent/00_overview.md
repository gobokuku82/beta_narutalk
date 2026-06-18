# 00. Execution Agent — 전체 한눈

> **10 에이전트 + ~46 Tool 의 한 페이지 지도**. 본 폴더의 진입점.
> ⭐ **버전별 진행 매트릭스 → [01_progress_matrix.md](01_progress_matrix.md)** (v0.x → MVP + 피벗 시나리오)

| 시점 | 2026-05-19 |
| 현재 버전 | **v0.2** (2026-05-18 박제, 4 commit) — 10 에이전트 + 8 Tool implemented |
| 변경 commit | 8ce2f3d / 0c89933 / 5537c08 / 2138798 (10 에이전트 구조 + review_collector rename + dead code 삭제 박제) |

---

## 1. 10 에이전트 구조

```
[chat_hub] (Cognitive Stage 내부 — Tool 카탈로그 외부)
   │
   ▼
═══ analysis_team (7 agent) ═══════════════════════════════
collection
  │ raw_reviews / raw_performance
  ▼
  ├── text_preprocessing (자연어 8 단계 정제)
  │     │ cleaned_texts
  │     ▼
  └── channel_normalizing (4 채널 광고성과 통합)
        │ normalized_data + KPI
        ▼
analysis (9 분석 모듈 — sentiment/keyword/insight/POC-01~09)
   │ analysis_results
   ▼
report_text (markdown + LLM 스토리)
   │ report_markdown
   │
   ├──► pdf (PDF / Word / Excel 텍스트 기반 출력)
   │      → pdf_file_path / word_file_path / excel_file_path
   │
   └──► ppt ⭐ (PPT 슬라이드 + 시각 디자인)
          → pptx_file_path / designed_pptx_path

═══ creative_team (4 agent — Q4 추후 정리) ═══════════════
image / video / copy / material
```

---

## 2. 에이전트 한 줄 카드 (10 개)

| # | 에이전트 | 한 줄 역할 | Tool (impl/total) | 카드 |
|---|---|---|---|---|
| 1 | chat_hub | NL 라우팅 + 11 화면 컨텍스트 + HITL | (Cognitive 내부) | [→](agents/01_chat_hub.md) |
| 2 | collection | 채널별 데이터 수집 (광고 5 + 콘텐츠 4) | 6/9 (67%) | [→](agents/02_collection.md) |
| 3 | text_preprocessing | 자연어 8 단계 정제 | 1/1 (통합) | [→](agents/03_text_preprocessing.md) |
| 4 | channel_normalizing | 데이터 채널 포맷 통일 (광고 + 리뷰) | 2/6 (33%) | [→](agents/04_channel_normalizing.md) |
| 5 | analysis | 9 분석 모듈 | 3/5 implemented + 6 POC 모듈 | [→](agents/05_analysis.md) |
| 6 | image | 광고 이미지 + 5축 채점 | 0/6 | [→](agents/06_image.md) |
| 7 | storyboard | 영상 4 씬 스토리보드 | 0/3 | [→](agents/07_storyboard.md) |
| 8 | report_text | markdown 텍스트 + LLM 스토리 | 2/2 (100%) ✅ | [→](agents/08_report_text.md) |
| 9 | pdf | PDF / Word / Excel 텍스트 기반 출력 | 0/5 | [→](agents/09_pdf.md) |
| 10 | **ppt** ⭐ | PPT 슬라이드 + 시각 디자인 | 0/3 (신규) | [→](agents/10_ppt.md) |

→ 합계: **8 implemented / 약 34 stub / ~42 Tool 명세 (creative_team 4 agent 제외)**. 구현률 ~19%.

---

## 3. implemented 8 Tool — POC 동작 체인

```
review_collector            (collection)
   │ raw_reviews
   ▼
format_normalizer           (channel_normalizing)
   │ normalized_reviews
   ▼
text_preprocessor           (text_preprocessing)
   │ cleaned_texts
   ├──► sentiment_analyzer     (analysis)
   │      │ sentiment_distribution
   └──► keyword_extractor      (analysis)
          │ top_keywords
          ▼
   insight_extractor        (analysis)
      │ insights
      ▼
   report_writer            (report_text)
      │ report_markdown
      ▼
   summary_generator        (report_text)
      │ summary_text
```

| Tool | Agent | Status | 카드 |
|---|---|---|---|
| review_collector | collection | ✅ implemented (v0.2.0) | [→](tools/implemented/review_collector.md) |
| format_normalizer | channel_normalizing | ✅ implemented | [→](tools/implemented/format_normalizer.md) |
| text_preprocessor | text_preprocessing | ✅ implemented | [→](tools/implemented/text_preprocessor.md) |
| sentiment_analyzer | analysis (POC-07) | ✅ implemented (POC: 규칙) | [→](tools/implemented/sentiment_analyzer.md) |
| keyword_extractor | analysis | ✅ implemented | [→](tools/implemented/keyword_extractor.md) |
| insight_extractor | analysis (LLM) | ✅ implemented | [→](tools/implemented/insight_extractor.md) |
| report_writer | report_text | ✅ implemented (LLM) | [→](tools/implemented/report_writer.md) |
| summary_generator | report_text | ✅ implemented | [→](tools/implemented/summary_generator.md) |

> 위 8 Tool 이 현재 POC 시연 가능한 **유일한 시나리오** (사용자 "블루밍글로우 네이버 리뷰 감성 분석해줘" 같은 query).

---

## 4. stub Tool 목록 (~34 개) — Phase 별 우선순위

### Phase 1A — 수집 6 추가 (M2 데이터 도착 후)
| Tool | Agent | 데이터 source |
|---|---|---|
| youtube_collector | collection | (mock 신규 필요) |
| coupang_collector | collection | (mock 신규 필요) |
| oliveyoung_collector | collection | (mock 신규 필요) |
| naver_searchad_collector ✅ | collection | data/clumi/raw/naver_searchad.json (external 활성) |
| meta_ads_performance_collector ✅ | collection | data/clumi/raw/meta_ads_performance.json (external 활성) |
| external_variables_collector | collection | (mock 신규 — 사용자 작업 중) |

> ⑫ (2026-06-01): broken `meta_collector`·`naver_sa_collector` 폐기 → external 신 패턴 (`meta_ads_performance_collector`·`naver_searchad_collector`) 정정. `oliveyoung_collector` mock source 폐기 (data/mock/ 부재).

### Phase 1B — 채널 정규화 4 추가
| Tool | Agent |
|---|---|
| kpi_calculator | channel_normalizing |
| anomaly_flagger | channel_normalizing |
| creative_history_updater | channel_normalizing |
| external_variables_joiner | channel_normalizing |

### Phase 2~3 — 분석 6 추가 (POC-01~06/08)
| Tool | Agent |
|---|---|
| kpi_anomaly_detector | analysis (POC-01) |
| kpi_forecaster | analysis (POC-02) |
| roas_cause_analyzer | analysis (POC-03) |
| fatigue_detector | analysis (POC-04) |
| ab_test_runner | analysis (POC-05) |
| zero_conv_keyword_detector | analysis (POC-06) |
| trend_spike_detector | analysis (POC-08) |

### Phase 4 — 콘텐츠 14 추가
| 에이전트 | Tool 수 |
|---|---|
| image | 6 (brand_guideline_analyzer RAG + ad_image_generator + image_resizer + thumbnail_creator + background_editor + creative_quality_scorer) |
| storyboard | 3 (storyboard_planner + frame_image_generator + storyboard_composer) |
| pdf | 5 (pdf_renderer + chart_generator + template_selector + word_template_filler + excel_template_filler) |
| **ppt** | 3 (pptx_generator + slide_designer + chart_to_slide) |

상세 = [TOBE_MVP/01 매트릭스 §2](../_claude/tool/TOBE_MVP/01_tool_data_matrix.md).

---

## 5. 데이터 source 의존 (POC mock CSV 12)

| Tool | 사용 CSV | 영향도 |
|---|---|---|
| review_collector | `mock_data_review_trends.csv` ⭐ 유일 사용 | High (현재) |
| kpi_anomaly_detector / kpi_forecaster / roas_cause_analyzer / fatigue_detector | `mock_data_daily_performance.csv` ⭐⭐ (가장 큰 영향) | High |
| zero_conv_keyword_detector | `mock_data_keyword_performance.csv` | Mid |
| ab_test_runner | `mock_data_ab_tests.csv` | Mid |
| sentiment_analyzer / keyword_extractor | (이전 Tool 출력) | — |
| brand_guideline_analyzer | `mock_data_company_info.csv` + (mock_data_brand_style.csv — 사용자 작업 중) | High (RAG) |

상세 = [TOBE_MVP/01 §5 역방향](../_claude/tool/TOBE_MVP/01_tool_data_matrix.md) + [data/description/mock/SCHEMA](../../data/description/mock/SCHEMA.md).

---

## 6. 핵심 메커니즘 한 줄 (참조 link 위주)

| 영역 | 핵심 | 깊이 |
|---|---|---|
| Tool 자동 import | catalog YAML 경로 → tools/.py 자동 매핑 (registry.py rglob) | [tools/registry.py](../../backend/app/dream_agent/tools/registry.py) |
| Tool 입력 자동 주입 | `_inject_prev_outputs` setdefault (이전 produces → params) | [17 §5.2](../agent_specs/17_functions_to_io_v1.0.md) |
| Tool 출력 체이닝 | produces 키 = 다음 Tool 의 input | [17 §5.4](../agent_specs/17_functions_to_io_v1.0.md) |
| 실패 처리 | raise 권장 (return error 도 지원, 비추) | [17 §5.5](../agent_specs/17_functions_to_io_v1.0.md) |
| 직렬화 | pickle 불가 객체 금지 (파일 핸들/async gen 등) | [17 §5.6](../agent_specs/17_functions_to_io_v1.0.md) |
| mock fallback | implemented 아니면 `mock_tools.mock_result()` 자동 | [executor.py:_run_single_todo](../../backend/app/dream_agent/execution/executor.py) |

---

## 7. ⚠️ 수정 시 영향 매트릭스 — 한 페이지 요약

실행 에이전트 / Tool 수정 시 **함께 갱신해야 할 영역**. 카드별 깊이는 각 카드의 §"수정 시 함께 변경 영역" 참조.

### 7.1 변경 종류 × 영향 영역

| 변경 ↓ \ 영향 → | Tool 코드 (.py) | Tool YAML | team_catalog | LLM Prompts (stage2/3/response) | Spec 31/32 | TOBE_MVP/01-02 | mock_tools.py | Frontend (PropertyPanel) | Dashboard | ADR | Tests | 의존 Tool |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Tool 추가 (신규 implemented)** | ✅ 신규 | ✅ 신규 | ✅ 행 추가 | △ stage3 예시 | ✅ 행 추가 | ✅ 행 추가 | — | — | — | △ (큰 결정 시) | ✅ unit | — |
| **Tool rename** | ✅ rename | ✅ rename | ✅ name 갱신 | ✅ Tool 이름 전체 | ✅ rename | ✅ rename | △ (stub 이면) | △ placeholder | △ 분기 텍스트 | — | ✅ import / 클래스명 | △ (참조 시) |
| **Tool params 추가/변경** | ✅ execute | ✅ parameters | △ params_required/optional 변경 시 | △ 예시 갱신 | △ | △ | — | — | — | — | △ | — |
| **Tool produces 키 변경** | ✅ return dict | ✅ produces | ✅ produces | ✅ stage3 (예시 chain) | △ | ✅ 매트릭스 | — | — | — | — | △ | **⭐ 의존 Tool 들 input 일치 갱신 필수** |
| **Tool 폐기** | ❌ 삭제 | ❌ 삭제 | ❌ 행 제거 | ❌ 참조 제거 | ✅ status: deprecated | ✅ 행 제거 | △ | △ | △ | ✅ (영향 큼) | ✅ 의존 test 정리 | ⚠️ 의존 Tool 영향 분석 |
| **에이전트 추가/분리/합병** | — | — | ✅ **다수** (agents block) | ✅ **다수** (stage2/3) | △ | ✅ 카드 신규/갱신 | — | — | — | ✅ (구조 변경) | △ Planner test | — |
| **에이전트 rename** | — | — | ✅ key rename | ✅ stage2/3 전체 | △ | ✅ 카드 rename | — | — | — | △ | △ | — |
| **카테고리 재정렬** (예: 7→12) | △ 폴더 이동 가능 | △ 카탈로그 이동 | ✅ **전면 재작성** | ✅ **전면 재작성** | ✅ 재작성 | ✅ 재작성 | — | — | — | ✅ **필수** | ✅ | — |
| **데이터 source 변경 (mock→실API)** | ✅ 분기 (`USE_MOCK_DATA`) | △ description | — | — | — | △ | — | — | — | ✅ (Phase 6+) | ✅ fixture | — |
| **로직 변경 (시그니처/produces 불변)** | ✅ | — | — | — | — | — | — | — | — | — | △ | — |

### 7.2 가장 흔한 함정 (자주 빠뜨림)

1. **`task_agent_hints`** (`team_catalog.yaml` L232-248) — 5 매핑 — 에이전트 변경 시 누락 흔함
2. **`implicit_prerequisites`** (`team_catalog.yaml` L254-265) — 선행 task → 변경 시 검토
3. **`response.yaml` 예시** — Tool rename 시 깜빡 (4 line)
4. **의존 Tool 의 produces 키 일치** — produces 키 rename 시 다음 Tool 의 params 가 맞아야 데이터 체인 안 끊김
5. **Spec 32 §7.1 카운트** — Tool implemented 카운트 갱신 (8 → N)
6. **본 폴더 카드 cross-link** — 새 카드 추가 시 INDEX / 00_overview / agent 카드 동시 갱신
7. **Frontend `PropertyPanel.tsx` placeholder** — Tool rename 시 L150 (간단하지만 깜빡 자주)
8. **Dashboard `index.html` Tool 분기** — rename 시 4 line 정도
9. **ADR (Architecture Decision Record)** — 큰 결정 (카테고리 재정렬 / 에이전트 추가/폐기) 시 ADR 작성 — 미작성 시 결정 이유 휘발
10. **DC-10 Status 3중 정합** — docstring `Status: complete` + YAML `status: implemented` + team_catalog `status: implemented` 한쪽만 갱신 흔함

→ 상세 절차 = [agent_specs/41 Change Hub §4](../agent_specs/41_agent_tool_change_hub_v1.0.md).

### 7.3 변경 절차 한 줄

```
① 41 §3 에서 변경 종류 분류
   ↓
② 위 §7.1 표에서 영향 영역 확인 (✅ 표시 영역 모두 갱신)
   ↓
③ Phase 1~5 (영향 측정 → 계획서 → 검증 → 작업 → 회귀+commit)
```

→ [agent_specs/41 §5 5 Phase 표준 절차](../agent_specs/41_agent_tool_change_hub_v1.0.md).

---

## 8. Phase 0~6 진입 매트릭스 ⚠️ 본 폴더 카드별 진입 시점

각 에이전트 / Tool 이 어느 Phase 에서 작업되는지. [03_gap_and_roadmap](../_claude/tool/03_gap_and_roadmap.md) 의 6 Phase 매핑.

### 8.1 Phase × 에이전트 매트릭스

| Phase | 작업 영역 | 본 폴더 카드 변경 |
|---|---|---|
| **Phase 0** (현재) | **매핑 작업** — 카드 작성 / 갱신 / Drift 박제 | 본 폴더 **00_overview + agents/ + tools/** 전체 |
| **Phase 1A** | 수집 6 추가 (M2 데이터 도착 후) | `agents/02_collection.md` + `tools/stub/<col>.md` × 6 |
| **Phase 1B** | 채널 정규화 4 신규 | `agents/04_channel_normalizing.md` + `tools/stub/<norm>.md` × 4 |
| **Phase 2** | 분석 1차 (POC-01/03/04/06) | `agents/05_analysis.md` + `tools/stub/<analysis>.md` × 4 |
| **Phase 3** | 분석 2차 (POC-02/05/07/08/09) | `agents/05_analysis.md` + `tools/stub/<analysis>.md` × 5 |
| **Phase 4A** | 이미지 (RAG 선결) | `agents/06_image.md` + `tools/stub/<image>.md` × 6 |
| **Phase 4B** | 스토리보드 | `agents/07_storyboard.md` + `tools/stub/<story>.md` × 3 |
| **Phase 4C** | PDF + PPT 출력 | `agents/09_pdf.md` + `agents/10_ppt.md` + `tools/stub/<output>.md` × 8 |
| **Phase 5** | 채팅 허브 + 11 매트릭스 + HITL 4 카테고리 | `agents/01_chat_hub.md` 강화 |
| **Phase 6+** | mock → 실API 전환 (매체별) | 해당 collector 카드 `mock vs real` 분기 |

### 8.2 각 카드의 "Phase" 절 작성 규칙

카드 본문의 `## Phase` 절에 다음 명시:
- 본 카드의 **현재 Phase** (예: Phase 0 — 매핑 완료)
- **다음 Phase** (예: Phase 1A — Tool 추가)
- **MVP 진입 시 변화** (예: mock → 실API)

상세 = [03_gap_and_roadmap](../_claude/tool/03_gap_and_roadmap.md).

---

## 9. POC 시연 가능 시나리오 1 개

> 사용자: **"블루밍글로우 네이버 리뷰 감성 분석해줘"**

```
[Cognitive] NL → StructuredQuery
[Planning Stage 1] team: analysis_team
[Planning Stage 2] agents: [collection, text_preprocessing, analysis]
[Planning Stage 3] todos:
   todo_001  review_collector       → raw_reviews
   todo_002  text_preprocessor       → cleaned_texts
   todo_003  sentiment_analyzer      → sentiment_distribution
   todo_004  keyword_extractor       → top_keywords  (병렬)
   todo_005  insight_extractor       → insights
   todo_006  report_writer           → report_markdown
   todo_007  summary_generator       → summary_text
[Execution] DAG 실행 (asyncio.gather)
[Response] markdown + 요약 1줄
```

→ 위 7 todo 가 현재 시연 가능. 나머지 변형 (PDF/PPT/이미지 생성/A/B 테스트) 은 stub fallback.

---

## 10. 변경 이력

| 날짜 | commit | 변경 |
|---|---|---|
| 2026-05-19 | 2138798 | naver_collector → review_collector rename + 출처 일반화 (Phase C) |
| 2026-05-19 | 5537c08 | dead code 삭제 — planning.yaml + planning_legacy.yaml (Phase F) |
| 2026-05-19 | 0c89933 | spec 17/40/41/42 신규 (Phase E) |
| 2026-05-18 | 8ce2f3d | team_catalog 10 에이전트 + LLM Prompts 동기 (Phase A+B) |
