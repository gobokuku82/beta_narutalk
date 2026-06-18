# Session Compact 준비 (2026-05-30 v2) — 작업 ③ 완료 + 작업 ④(영향 점검) 진입

> v1 = 작업 ② contract A 완료 시점 ([session_compact_recovery_2026-05-30.md](./session_compact_recovery_2026-05-30.md)).
> v2 = **작업 ③ 카테고리·이름·구조 정리 완료 + 작업 ④ 영향 점검 진입**.

---

## ★ 이어가기 (compact 직후 진입)

### 1분 요약
- 작업 ③ 완료 (17 commit, e8d231f → cc9d0aa). 카테고리 7+1 박제 + 모든 tool 의도 정합.
- 사용자 다음 요구: **작업 ④ = tool 변경 영향 점검** (프론트/백엔드/데이터/문서 7 layer × 19 변경).
- 골든 baseline = **303 passed / 3 failed**(pyarrow 환경, baseline 그대로). S001=119,539,660.

### 작업 ④ 본질 (사용자 요구 원문)
> "tool의 변경 영향받는 부분의 프론트엔드/백엔드/데이터/문서 - 세부 기준으로 (pipeline, agent의 plan / execution layer, data layer 등) 하나씩 점검"

→ 7 layer × 19 변경 매트릭스로 점검. 각 셀에서 *갱신 필요 / 무관 / 이미 정합* 판정. 갱신 필요 셀만 작업.

### compact 후 첫 행동 (§4 권장)
1. 본 문서 §0~§3 정독 (현 상태·작업 ④ 기준·참조 확정).
2. §1.3 매트릭스에서 가장 영향 큰 영역 선택 (권장: pipeline yaml 먼저).
3. ONE 변경 단위 = 한 layer 의 영향 확인 → 갱신 필요 시 commit → 회귀.

---

## 0. 작업 ③ 완료 상태

### 0.1 17 commit (시간 역순)

| # | commit | 단계 | 핵심 |
|---|---|---|---|
| 17 | `cc9d0aa` | 정합 | 33 normalization/preprocessing 갱신 + 33_report.md 신설 + 32 §3 정합 |
| 16 | `fd1435d` | 이동 | preprocessing 잔존 3 tool 카테고리 재배치 |
| 15 | `906f4a3` | 이동 | SummaryGenerator: shared → report |
| 14 | `8e45bcb` | rename | ad_cost_total · member_guest_stats |
| 13 | `829d6e0` | 문서 | 32 §3 디렉토리 갱신 + §7 deprecated 노트 |
| 12 | `074523b` | 문서 | 33_metrics.md 35 tool 인벤토리 |
| 11 | `15b413b` | 문서 | clumi docstring 일반화 (6 파일) |
| 10 | `4fc3f4f` | 권한 | workspace client default 제거 (작업 ② 단계 5) |
| 9 | `74960ae` | 이동 | preprocessing/marketing 폐기 + 11 tool metrics 이동 |
| 8 | `0c22455` | 분리 | creatives_aggregate → K18/K19/K20 (3 tool) |
| 7 | `539d89c` | 분리 | campaigns_aggregate → K10/K11/K12/K13 (4 tool) |
| 6 | `f960753` | 문서 | 33/* skeleton 7 카테고리 인벤토리 + README |
| 5 | `e8d231f` | 박제 | **32 v1.1 — 카테고리 7 정의 + decision tree + 옵션 C 계약** |
| 4 | `832aa9a` | 폐기 | clumi_loader.py 폐기 |
| 3 | `6451c89` | ②-a | collection/_base — clumi_loader 의존 끊기 |
| 2 | `1f3afb2` | ②-a | FileDataSource.stream_jsonl + kst·ga4 정합 |
| 1 | `bdec57e` | ②-a | grade_system_unifier — ds.has + self.fetch |

(`4ff282b` missing_value_diagnostic + `bb5aa59` contract C + `88c98e7` contract B + `6e27f01` 死코드 + `47b9f04` contract A + `a01d57f` expand 는 v1 단계로 v2 commit 카운트 17개에는 포함, 작업 ② 마무리 commit 들)

### 0.2 최종 카테고리 분포 (87 tool + 6 helper)

| 카테고리 | tool 수 | 의도 (32 §2.5) |
|---|---:|---|
| collection | 27 | raw 가져오기 |
| normalization | 6 | 컬럼·형식·단위·시간대 표준화 |
| cleaning | 3 | 결측·이상치·필터·검증·보정 |
| preprocessing | 1 | 자연어 텍스트 전처리 (한정) |
| metrics | 35 | 순수 계산 |
| comparison | 7 | 두 metrics 조합·비교 |
| analysis | 6 | LLM·ML·통계 추론 |
| report (보조) | 2 | 보고서 텍스트 산출 |
| **합** | **87 tool** | + shared 6 helper |

### 0.3 박제 잣대 (수정 봉인됨, 변경 시 ADR)

- **카테고리 의도** → [32 v1.1 §2.5](../agent_specs/32_execution_agent_tools_v1.0.md)
- **분류 decision tree** → [32 v1.1 §2.6](../agent_specs/32_execution_agent_tools_v1.0.md)
- **input/output 계약 원칙 (옵션 C)** → [32 v1.1 §2.7](../agent_specs/32_execution_agent_tools_v1.0.md)
- **카테고리별 tool 인벤토리** → [33_tools_by_category/](../agent_specs/33_tools_by_category/) (8 문서)
- **shared = helper only** (tool 아님) — 박제 정합 완료.
- **sub-folder 도입 X** (현 시점 YAGNI, tool 50+ 시 재검토).

---

## 1. 작업 ④ 정의 — tool 변경 영향 점검

### 1.1 점검 영역 7 layer (기준 명확화)

| # | layer | 정의 | 핵심 코드 / 문서 위치 |
|---|---|---|---|
| L1 | **백엔드 - pipeline** | yaml flows 의 `tool:` 참조 | [backend/app/pipelines/flows/](../../backend/app/pipelines/flows/) (43 yaml) · [pipelines/runner.py](../../backend/app/pipelines/runner.py) |
| L2 | **백엔드 - agent plan** | LLM planner prompts + team_catalog | [planning/catalog/team_catalog.yaml](../../backend/app/dream_agent/planning/catalog/team_catalog.yaml) · [llm_manager/prompts/](../../backend/app/dream_agent/llm_manager/prompts/) (5 yaml: cognitive·stage1·stage2·stage3·response) |
| L3 | **백엔드 - agent execution** | executor·agent_pool·mock_tools | [execution/executor.py](../../backend/app/dream_agent/execution/executor.py) · [execution/agent_pool.py](../../backend/app/dream_agent/execution/agent_pool.py) · [execution/mock_tools.py](../../backend/app/dream_agent/execution/mock_tools.py) |
| L4 | **백엔드 - data layer** | data_sources + workspace + schemas | [app/data_sources/](../../backend/app/data_sources/) · [app/workspace/](../../backend/app/workspace/) · [app/schemas/](../../backend/app/schemas/) |
| L5 | **프론트엔드** | api/* 의 tool 결과 schema 참조 | [frontend/src/api/](../../frontend/src/api/) (clients·pipelines·schemas·queryKeys·rest·ws) · [frontend/src/features/](../../frontend/src/features/) |
| L6 | **데이터** | data/{client}/ 의 cache 키·디렉토리 구조 | data/clumi/raw/ · data/clumi/cleaned/ · data/clumi/computed/ |
| L7 | **문서** | agent_specs + _claude + reports | [docs/agent_specs/](../agent_specs/) · [docs/_claude/](../_claude/) · [docs/reports/](.) |

### 1.2 점검 대상 — 작업 ③ 의 19 변경

| # | 종류 | 변경 | 의미 |
|---|---|---|---|
| C1 | 폐기 | campaigns_aggregate → 4 분리 | generic 엔진 의미 단위 분리 |
| C2~C5 | 신규 | campaign_count · campaign_active_count · campaign_budget_total · campaign_target_roas_avg | K10·K11·K12·K13 |
| C6 | 폐기 | creatives_aggregate → 3 분리 | 동형 |
| C7~C9 | 신규 | creative_count · creative_ctr_avg · creative_roas_avg | K18·K19·K20 |
| C10~C20 | 이동 | preprocessing/marketing 11 tool → metrics/ (이름 동일) | 11 tool: ad_cost·budget(3)·channel·conversion·daily(2)·ga4·category·member_guest · category_multi |
| C21 | rename | ad_cost_aggregator → ad_cost_total | 이름·출력 정합 |
| C22 | rename | member_guest_splitter → member_guest_stats | 동형 |
| C23 | 이동 | summary_generator: shared → report | shared helper only 정합 |
| C24 | 이동 | format_normalizer: preprocessing/data_normalization → normalization | ADR-014 v2 정합 |
| C25 | 이동 | review_normalizer: preprocessing/data_normalization → normalization | 동형 |
| C26 | 이동 | text_preprocessor: preprocessing/text_cleaning → preprocessing/ 직속 | sub-folder 폐기 |

→ **총 26 변경 (4 폐기 + 7 신규 + 11 이동 + 2 rename + 2 추가 이동)**.
(0.1 의 "19 변경" 은 묶음 단위. 매트릭스에서 세분화 = 26.)

### 1.3 점검 매트릭스 (7 layer × 26 변경)

> 각 셀: **무관** / **이미 정합** / **갱신 필요** / **확인 필요**

#### L1. pipeline (yaml flows)

| 변경 | 영향 |
|---|---|
| C1~C5 campaigns_aggregate 분리 | **이미 정합** (`539d89c` 4 yaml tool: 갱신) |
| C6~C9 creatives_aggregate 분리 | **이미 정합** (`0c22455` 3 yaml tool: 갱신) |
| C10~C20 11 tool 이동 | **이미 정합** (registry 자동 path 추론, yaml 의 tool: 이름만 매칭) |
| C21 ad_cost_total rename | **이미 정합** (`8e45bcb` 2 yaml tool: 갱신) |
| C22 member_guest_stats rename | **이미 정합** (`8e45bcb` 1 yaml tool: 갱신) |
| C23~C26 분석 team tool 이동 | **확인 필요** (yaml flows 안 호출 여부 grep 필요) |

#### L2. agent plan (team_catalog + 5 prompts)

| 변경 | 영향 |
|---|---|
| C1~C9 campaigns·creatives 분리 | **무관** (dashboard1 영역, team_catalog 미등록) |
| C10~C22 metrics 이동·rename | **무관** (동일) |
| C23 summary_generator 이동 | **확인 필요** (team_catalog 의 report_text_agent 등록 — name 매칭만, path 무관 추정) |
| C24 format_normalizer 이동 | **확인 필요** (channel_normalizing_agent 등록) |
| C25 review_normalizer 이동 | **확인 필요** (동형) |
| C26 text_preprocessor 이동 | **확인 필요** (text_preprocessing_agent 등록) |

#### L3. agent execution (executor·agent_pool·mock_tools)

| 변경 | 영향 |
|---|---|
| C1~C22 dashboard1 영역 | **무관** (executor 는 분석 team 기준) |
| C23 summary_generator | **확인 필요** (`executor.py:103` tool_name 매칭 발견됨, path 무관 추정) |
| C24~C26 분석 team tool 이동 | **확인 필요** (agent_pool 이 path 기반 import 인지 name 기반인지) |

#### L4. data layer (data_sources·workspace·schemas)

| 변경 | 영향 |
|---|---|
| C1~C26 전체 | **이미 정합** (data layer 는 tool 무관 — `self.fetch`/`self.ds.get` 호출만, tool 이름·위치 알지 못함) |
| 단, 옵션 C schema 정의 시 | **신규 진입 시 적용** (작업 ③ 점진 적용 원칙) |

#### L5. 프론트엔드

| 변경 | 영향 |
|---|---|
| C1~C9 분리 (K10·K11·K12·K13·K18·K19·K20) | **확인 필요** (pipelines.ts·schemas.ts 에 KPI 이름 참조 여부) |
| C10~C20 metrics 이동 | **무관** (frontend 는 tool 이름 모름, pipeline 이름만 호출) |
| C21~C22 rename | **확인 필요** (호출이 tool 이름 직접인지 pipeline 이름인지) |
| C23~C26 분석 team | **무관** (dashboard1 frontend 와 별 시스템) |

#### L6. 데이터 (cache 키)

| 변경 | 영향 |
|---|---|
| C1~C9 분리 | **확인 필요** (key_template 변경됐는지) |
| C10~C20 이동 | **이미 정합** (이름 동일, 키 무변경) |
| C21 ad_cost_total | **확인 필요** (`ad_cost_total_{period}.json` 키 — rename 전후 동일) |
| C22 member_guest_stats | **확인 필요** (`orders_split_{period}.json` 키 — 동일) |
| C23~C26 분석 team | **무관** (dashboard1 cache 영역과 별 시스템) |

#### L7. 문서

| 변경 | 영향 |
|---|---|
| C1~C26 전체 | **이미 정합** (`cc9d0aa` 32 §3 + 33/* 모두 갱신) |
| 단, 32 §4~§9 outdated | **갱신 필요** (큰 작업, 작업 ④ 의 마지막) |
| _claude/* 참조 docs | **확인 필요** (recovery 문서·아키텍처 노트의 outdated 참조) |

### 1.4 점검 순서 (작업 ④ 권장)

```
1. L4 data layer 확인     ← 가장 영향 작음, baseline 확정
2. L1 pipeline 잔존 확인  ← L2 의 분석 team yaml 호출 여부 grep
3. L3 execution 확인      ← name vs path 매칭 방식 확정
4. L2 agent plan 갱신     ← 위 결과 토대로 team_catalog/prompts 갱신
5. L5 프론트 확인         ← pipelines.ts·schemas.ts grep
6. L6 데이터 cache 확인   ← key_template 일관성 확인
7. L7 문서 잔존 정리      ← 32 §4~§9 + _claude/* 정합
```

→ 각 step = **확인 결과** + **갱신 필요 시 commit**. 무관/정합 셀은 박제만.

---

## 2. 검증 기준

### 2.1 골든 회귀 (baseline 변하면 안 됨)

```bash
uv run pytest backend/tests/pipelines backend/tests/dashboard1 \
  backend/tests/data_sources backend/tests/workspace \
  backend/tests/permissions backend/tests/ml_models -q
```

→ **303 passed / 3 failed (baseline pyarrow 환경, 무관)**.
- 정답 앵커: S001 revenue_total(2026-04) = **119,539,660**.
- 3 fail = workspace 단위 parquet test, 환경 의존 (코드 무관).

### 2.2 실구동 스모크 (큰 변경 후)

- backend: `uv run python run_server_v2.py`
- frontend: `pnpm -C frontend dev`
- 브라우저: client 드롭다운 전환 + 대시보드 갱신 확인.
- 사용자 직접 확인 ✅ (작업 ② 후 검증됨).

### 2.3 분석 team 회귀 (작업 ④ 신규 추가)

작업 ④ 가 분석 team 영역(team_catalog·executor) 손대므로:
```bash
uv run pytest backend/tests/sprint13 backend/tests/sprint14 -q
```
- sprint13/14 = 분석 team(cognitive·planning·execution) 통합 테스트 위치.
- sprint15 = broken(recovery v1 명시), 포함 X.
- 통과 여부 확인. 실패 시 작업 ④ 의 갱신이 분석 team 깨뜨림 = 원복 후 별 접근.

### 2.4 검증 베이스라인 (작업 ④ 시작 전 박제됨, 2026-05-30)

```
backend/tests/sprint13 + sprint14:
  275 passed / 11 failed / 2 skipped

backend/tests/{pipelines,dashboard1,data_sources,workspace,permissions,ml_models}:
  303 passed / 3 failed (pyarrow 환경)
```

**11 fail (sprint14) = HITL timeout 통합 테스트** (test_hitl_timeout_integration HT08c~HT08g·HT10 · test_hitl_timeout_resume_query_unit HT11 등). 작업 ④ 가 *안 건드릴* 영역 baseline — 작업 ④ 후 동일 11 fail 유지 = 회귀 zero.

작업 ④ 종료 시점 검증:
```bash
# 1. dashboard1 영역 회귀 (분리·이동·rename 의 본 영역)
uv run pytest backend/tests/pipelines backend/tests/dashboard1 \
  backend/tests/data_sources backend/tests/workspace \
  backend/tests/permissions backend/tests/ml_models -q
# → 303 passed / 3 failed 그대로

# 2. 분석 team 회귀 (team_catalog·executor 손대므로)
uv run pytest backend/tests/sprint13 backend/tests/sprint14 -q
# → 275 passed / 11 failed 그대로
```

---

## 3. 참조 문서 (필수 — 모두 검증됨)

### 3.1 카테고리 잣대 (작업 ③ 박제)

| 참조 | path | 의도 | 검증 |
|---|---|---|---|
| 32 v1.1 | [docs/agent_specs/32_execution_agent_tools_v1.0.md](../agent_specs/32_execution_agent_tools_v1.0.md) | 카테고리 정의 + decision tree + 옵션 C | ✅ |
| 33 README | [docs/agent_specs/33_tools_by_category/README.md](../agent_specs/33_tools_by_category/README.md) | 8 카테고리 진입 | ✅ |
| 33_collection.md | [33_tools_by_category/33_collection.md](../agent_specs/33_tools_by_category/33_collection.md) | 27 tool | ✅ |
| 33_normalization.md | [33_normalization.md](../agent_specs/33_tools_by_category/33_normalization.md) | 6 tool (4+2 ADR-014 v2) | ✅ |
| 33_cleaning.md | [33_cleaning.md](../agent_specs/33_tools_by_category/33_cleaning.md) | 3 tool | ✅ |
| 33_preprocessing.md | [33_preprocessing.md](../agent_specs/33_tools_by_category/33_preprocessing.md) | 1 tool (text_preprocessor) | ✅ |
| 33_metrics.md | [33_metrics.md](../agent_specs/33_tools_by_category/33_metrics.md) | 35 tool 의미 단위 8 그룹 | ✅ |
| 33_comparison.md | [33_comparison.md](../agent_specs/33_tools_by_category/33_comparison.md) | 7 tool | ✅ |
| 33_analysis.md | [33_analysis.md](../agent_specs/33_tools_by_category/33_analysis.md) | 6 tool (일반/ML/LLM 3 sub) | ✅ |
| 33_report.md | [33_report.md](../agent_specs/33_tools_by_category/33_report.md) | 2 tool (보조 카테고리 활성화) | ✅ |

### 3.2 ADR (의사결정 박제, 작업 ④ 영향)

| ADR | path | 작업 ④ 와 관련 |
|---|---|---|
| ADR-014 v2 | [ADR-014_tool_param_auto_detection.md](../agent_specs/adr/ADR-014_tool_param_auto_detection.md) | format/review_normalizer 단일책임 분리 — 작업 ③ 정합 |
| ADR-019 | [ADR-019_summary_generator_responsibility.md](../agent_specs/adr/ADR-019_summary_generator_responsibility.md) | summary_generator 책임 — shared→report 이동 정합성 |
| ADR-022 | [ADR-022_data_source_workspace_layer_separation.md](../agent_specs/adr/ADR-022_data_source_workspace_layer_separation.md) | data layer 분리 — L4 점검 기준 |
| ADR-024 | [ADR-024_iterative_spec_refinement.md](../agent_specs/adr/ADR-024_iterative_spec_refinement.md) | spec 진화 — 작업 ④ 갱신 절차 |
| ADR-027 | [ADR-027_five_actor_permission_separation.md](../agent_specs/adr/ADR-027_five_actor_permission_separation.md) | 5 actor 권한 — pipeline·tool·data layer 경계 |
| ADR-029 | [ADR-029_folder_naming_principles.md](../agent_specs/adr/ADR-029_folder_naming_principles.md) | 폴더 명명 원칙 — 작업 ③ 카테고리 정의 정합 |

### 3.3 이전 recovery (시간순)

| 문서 | 시점 |
|---|---|
| [v1 (2026-05-30, 작업 ② contract A)](session_compact_recovery_2026-05-30.md) | 작업 ② 마무리 시점 |
| [v0 (2026-05-28)](session_compact_recovery_2026-05-28.md) | 데이터 정리 단계 |
| [v0 (2026-05-27)](session_compact_recovery_2026-05-27.md) | DataSource 분리 |
| [v0 (2026-05-26)](session_compact_recovery_2026-05-26.md) | tool/data/agent 분리 |

### 3.4 진입 지도

| 문서 | 역할 |
|---|---|
| [.claude/CLAUDE.md](../../.claude/CLAUDE.md) | 매 세션 자동 로드 — 진입 지도 |
| [docs/agent_specs/INDEX.md](../agent_specs/INDEX.md) | spec 진입점 |
| [docs/_claude/INDEX.md](../_claude/INDEX.md) | 자취·계획서·박제 |
| MEMORY.md (user) | 사용자 원칙 (auto-load) |

### 3.5 작업 ④ 점검 영역의 핵심 코드 위치 (필수)

| layer | path | 본 문서 §1.3 매트릭스 |
|---|---|---|
| L1 pipeline runner | [backend/app/pipelines/runner.py](../../backend/app/pipelines/runner.py) | tool name → registry 동적 import |
| L1 pipeline flows | [backend/app/pipelines/flows/](../../backend/app/pipelines/flows/) (43 yaml) | tool 참조 검증 |
| L2 team_catalog | [team_catalog.yaml](../../backend/app/dream_agent/planning/catalog/team_catalog.yaml) | name 매칭 등록 |
| L2 stage3 prompt | [planning_stage3_todo.yaml](../../backend/app/dream_agent/llm_manager/prompts/planning_stage3_todo.yaml) | LLM 이 tool 이름 박제 |
| L3 executor | [execution/executor.py](../../backend/app/dream_agent/execution/executor.py) | tool 라벨링 (line 103) |
| L3 agent_pool | [execution/agent_pool.py](../../backend/app/dream_agent/execution/agent_pool.py) | tool import 방식 |
| L3 mock_tools | [execution/mock_tools.py](../../backend/app/dream_agent/execution/mock_tools.py) | tool 폴백 |
| L4 data_sources | [app/data_sources/file.py](../../backend/app/data_sources/file.py) | 87 source_id 매핑 + stream_jsonl |
| L4 workspace | [app/workspace/file.py](../../backend/app/workspace/file.py) | client 필수 (default 제거됨) |
| L5 frontend api | [frontend/src/api/clients.ts](../../frontend/src/api/clients.ts) · [pipelines.ts](../../frontend/src/api/pipelines.ts) · [schemas.ts](../../frontend/src/api/schemas.ts) | tool 결과 schema 참조 |

---

## 4. compact 후 첫 행동 (권장 순서)

1. **★ 이어가기 정독** (본 문서 최상단).
2. **§0~§3 정합 확인** (현 상태·작업 ④ 기준·참조 검증됨).
3. **§1.4 권장 순서 따라 ONE 변경**:
   - 첫 ONE = L4 data layer 확인 (가장 안전, baseline 확정).
   - 둘째 ONE = L1 pipeline 잔존 확인 (분석 team yaml grep).
   - …
4. **각 layer 점검 결과 = "갱신 필요 셀만 commit"**. 무관/정합 셀은 박제만 (commit 없음, 본 문서에 기록).
5. **분석 team 회귀 (§2.3) 까지 통과** = 작업 ④ 마무리.

### 잔존·연기·재검토 항목 (작업 ④ 완료 후)

- **옵션 C schema 적용** (32 §2.7 박제) — 신규 tool 진입 시 자연 적용. 기존 점진.
- **sprint15 collectors 정리** (broken — recovery v1 명시) — agent team 연계 작업 필요.
- **32 §4~§9 outdated** — 큰 문서 작업, 작업 ④ 마지막.
- **sub-folder 재검토** — tool 50+ 시점.

---

## 5. 함정·교훈 (이전 세션 + 작업 ③ 누적)

1. **Regex alternation 순서**: 긴 것 먼저 (`(?:location|loc)`).
2. **Multi-line dict regex 위험** → per-tool Edit.
3. **BOM 주의**: 데이터 파일 plain utf-8.
4. **git mv 후 폴더 자동 정리 ≠ __init__ 자동 폐기**: 잔존 확인 필요 (작업 ③ 의 preprocessing 잔존 발견).
5. **tool 이동 시 yaml registry 자동 path 추론** (yaml 위치 = py 위치). 호출자(yaml flows) 의 `tool:` 이름만 매칭 — path 무관.
6. **default 제거 시 호출자 grep 필수** (작업 ② 단계 5 의 workspace default).
7. **사용자 진단 vs 실제 호출 패턴 차이** (작업 ③ 의 ad_cost·member_guest = 사용자가 "끼워맞춤" 진단했으나 호출 패턴 분석 결과 묶음 정당 → rename 만).

---

**작성 완료**: 2026-05-30. 모든 참조 link 검증됨 (§3 표 모든 path 존재 확인). compact 진입 가능.
