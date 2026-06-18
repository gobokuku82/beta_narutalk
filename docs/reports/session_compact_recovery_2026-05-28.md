# Session Compact 준비 (2026-05-28) — Phase 1 완료 → 아키텍처 의도-정합 정리 진행 중

> compact 직후 이어서 작업 재개. **현 = (Phase 1 완료 후) 사용자 의도와 코드 정합 점검·정리 단계.**
> Phase 1 기록은 §0 이하 historical. **현 작업·규칙은 아래 ★ 블록이 최신.**

---

## ★ 이어가기 (2026-05-28 후반 — 아키텍처 의도-정합 정리) ⭐ 최신

**무엇**: 비전공자 사용자의 *의도한 구조*와 현 코드의 gap(E1~E10)을 **하나씩** 정리 중. 의도 = **convention(규칙) 주도, 하드코딩 최소**.

**⚠️ 작업 규칙 (이 세션의 핵심 교훈 — 필독):**
1. **convention 우선 — 하드코딩 자제.** 새 리스트/플래그/상수/분기 넣기 전 "기존 규칙으로 되나?" 먼저. (폴더 있으면 client / 이름으로 registry / client=변수로 흐름). → memory `feedback_convention_over_hardcoding`.
2. **한 턴 = ONE 변경 → golden 검증 → 커밋.** 대안 메뉴 나열·매 턴 재계획·큰 결합(예: Sprint15 제거) 착수 자제 (꼬임·반복 유발).
3. 자명하면 안 묻고 실행.

**이번 세션 정리 commits (시간순):**
`0c152c1` DC-PERM-1~6 · `258742b` 점검보고서(E1~E10)+설계노트 · `447409e` data_sources 레지스트리 kind/platform · `9d199c5` collection external(13)/internal(8) 분리 · `0bd0a05` _base→collection/ · `6594667` clumi_outputs→schemas/outputs/dashboard1 · `780d6da` TopBar client 드롭다운 동적화(/api/admin/clients).

**정리 우선순위 (점검보고서 §8) 진행:**
| 순위 | 항목 | 상태 |
|:--:|---|---|
| 0.5 | 수집 재구조화 (레지스트리·external/internal·_base) | ✅ 거의 완료 (Sprint15 잔재 제거만 추후) |
| 1 | 이름 (clumi_outputs→schemas ✅ / DEFAULT_CLIENT·workspace clumi 하드코딩 남음) | 🟡 일부 |
| — | (이름 1의 일환) frontend client 드롭다운 동적화 = data/{client}/raw 스캔 기반 | ✅ 780d6da |
| 2 | 레거시 25 tool 표준 schema 전환 | ⬜ |
| 3 | 카테고리 재배치 (집계·comparison·출력) | ⬜ |
| 4 | tool 순수화 (data 직접접근 제거, 의도 #6) | ⬜ |

→ **남은 정리는 전부 사용자 지시 대기. 하나씩.**

**🐛 다음 1순위 버그 (E11) — client 선택이 대시보드에 반영 안 됨:**
- 원인: **캐시가 client 무관.** `dashboard1.py::_cached_or_run`([L120](../../backend/api_v2/routes/dashboard1.py#L120)) 주석 명시 "cache_key 는 client 무관 (clumi 단일)". + Runner cache key_template 에 `${client}` 없음 + workspace 경로 `clumi/` 하드코딩(E9).
- 증상: clumi 계산→`data/clumi/computed/` 캐시 → 다른 client 선택해도 같은 cache_key → clumi 캐시 반환 → 화면 안 바뀜. **프론트는 정상**(selectedClientId→queryKey→refetch 동작).
- 빠른 fix: cache_key 를 client prefix — `_cached_or_run` + `runner.py` 2곳. (clumi 정상 / 데이터부족 client 는 빈·에러=의도)
- 정석 fix: workspace 를 `data/{client}/{layer}/` client-aware (E9 해소, 큼).

**golden 베이스라인 (회귀 기준)**: `291 passed / 14 failed` — **14 = pyarrow 미설치(환경), 작업 무관 → 무시.** 검증 명령:
`uv run pytest backend/tests/pipelines backend/tests/dashboard1 backend/tests/data_sources backend/tests/permissions backend/tests/ml_models -q` (291 유지 + 신규실패 0). frontend: `pnpm -C frontend build`.

**핵심 문서 (파악 완료 — 더 안 만듦):**
- `docs/reports/아키텍처_의도정합_점검보고서_2026-05-28.md` — E1~E10 오류목록 + 부록C tool 전수분류 + §8 정리 우선순위.
- `docs/reports/수집_datasource_설계노트_2026-05-28.md` — 수집 2-layer(external=data/mock_api / internal=data/{client}) + 옵션 C(플랫폼 커넥터+generic 리더).
- `docs/reports/수집_재구조화_검증로드맵_2026-05-28.md` — golden·정답값·Phase 게이트.

**핵심 memory**: `project_intended_layer_architecture`(의도 구조=북극성) · `feedback_convention_over_hardcoding`(규칙 우선·ONE 변경).

**클라이언트 흐름 (검증됨)**: TopBar 드롭다운 → store.selectedClientId → API `?client=` → Runner ctx.client_id + YAML `${client}` → tool `self.ds.get(client,…)` → `data/{client}/raw/`. 현재 client 4개(clumi 28·blooming 18·asyou 0·bluban 0 = raw 파일수); clumi만 정상, 나머지는 선택되나 데이터 부족으로 빈/에러(의도).

---

## 0. 메타

| 항목 | 내용 |
|---|---|
| 작성일 | 2026-05-28 |
| 위치 | `docs/reports/session_compact_recovery_2026-05-28.md` |
| Compact 시점 | **Phase 1 코드 구현 완료** (52 pipeline + frontend 5 v1 페이지 + mock 레거시 폐기) 후 |
| Branch | main (이번 세션 30 commit, origin 대비 다수 ahead — **push 안 함**) |
| 검증 | backend pipelines 74 + ml_models 11 + frontend 88 + build(2936 모듈) 전부 green |

---

## 1. 현 작업 한 줄

**Phase 1 코드 구현 완료 — 52 pipeline (6 batch) + Pipeline Runner(YAML·topo·캐시·검증) + `/api/admin/pipelines` API + ml_model adapter + frontend 5 v1 페이지 (Dashboard v1/Channel/Trend/Creative/Cost, recharts). 구 mock-API/blooming 레거시 전면 폐기 → 데이터 = pipeline(`data/clumi/raw/` + Runner)만. clumi 정답 17 보존. 남은 = M5(DC-PERM test) · git push · MVP+(포트폴리오 실구현·O05 0.002·M2 tool 리팩터·normalizer) = 전부 선택/연기.**

### Phase 1 진척 (2026-05-28)

| 마일스톤 | 내용 | 검증 | commit |
|---|---|---|---|
| **M1** | `backend/app/pipelines/` (models·loader·runner·validator) + K01 flow | 9/9 | b459d07 |
| **M1b** | `/api/admin/pipelines` 4 endpoint + in-memory run store + 비동기 실행 (63 §2.3.3) | 13/13 | 9763a19 |
| **M4** | Frontend 🔄 데이터 분석 버튼 + `api/pipelines.ts` zod·hooks (시각화-우선) | 83/83 | ee7119e |
| **M1b-2** | Batch 1 전체 21 pipeline YAML (K01~C02) | 35/35 | 7b85402 |
| **버튼 확장** | 🔄 = Dashboard1 21 pipeline 병렬 실행 (`useRunCategory`) | 88/88 | 43379e5 |
| **M3** | `ml_models/` adapter (MlModel ABC + Mock + Llm + factory) + ml_mock fixture | 11/11 | 3b96687 |
| **Batch 2** | Dashboard v1 6 pipeline (campaign·daily) + `schemas/inputs·outputs` | 8/8 | 483905f |
| **mock raw 설계** | `36_clumi_mock_raw_data_design` (60→30번대 정정) + 프로세스 memory | — | f7b2e2b·1872241 |
| **Batch 3** | Channel 3 pipeline (C05·C06·T05 — daily_performance channel 집계, 신규 데이터 0) | 4/4 | 441138d |
| **Batch 4** | Trend 8 pipeline (K14~17·C07·C08·C12·O03 — reviews + ml_model 감성·키워드 실증) | 8/8 | 58af603 |
| **Batch 5** | Creative 7 pipeline (K18~21·C11·O04·T06 — creatives·ab_tests + ml_model AI축·피로) | 8/8 | 392a18d |
| **Batch 6** | Cost+AI 7 pipeline (K22~24·C09·C10·T07·O05 — budget·keyword + O05 추천 ml_model) | 10/10 | 7667f40 |
| **frontend 5 v1** | category endpoint(33b35a4) + 5 페이지(Dashboard v1·Channel·Trend·Creative·Cost) + 차트 7종 + 라우팅 전환 | build+88 | 6617c7d·538d531 |

→ **🎉 전체 52 pipeline + 5 v1 페이지 완성** (21+6+3+8+7+7). Pipeline 전체 경로: 버튼/페이지 → `GET category/{cat}` 또는 `POST run/{name}` → Runner (YAML 해석·tool·캐시·검증) → 산출 → recharts 렌더. clumi 정답 S001=119,539,660 보존. 테스트 backend pipelines 74 + ml_models 11 + frontend 88. frontend build(2936 모듈) OK.

**v1 전환 + mock 레이어 폐기 (2026-05-28, commit 1d3d551·5fa0e87)**: 구 mock-API 페이지 → pipeline-backed 5 페이지로 라우팅 교체(/dashboard·/trend·/creatives·/cost + /channel 신설). 구 페이지 4 삭제(검증). **blooming 완전 폐기 → 구 mock-API 레이어 전면 제거**: `/api/mock`(routes/mock_data.py)·`useMockData.ts`·테스트 삭제 + main.py·routes/__init__ 등록 제거. 포트폴리오 3 페이지(Portfolio·Report·ChannelAnalysis) = **MVP+ placeholder stub**(다중 client = POC 범위 밖). 데이터 = 이제 **pipeline(data/clumi/raw/ + Runner)만**. `data/blooming`(로컬·gitignore)은 사용자 데이터 보존(참조 0).

### ⚠️ 방향 전환 (2026-05-28) — blooming 제외, clumi 단일 + mock raw

사용자 결정: *"blooming 때문에 자꾸 문제가 커진다. clumi 기준으로만 만들고 필요한 데이터는 mock raw 로 생성"* + *"하드코딩으로 수정영역이 폭증하면 안 돼"*.
- **POC = clumi 단일 client.** Batch 2~6 데이터 = `data/clumi/raw/` 표준 영어 컬럼 mock raw (별 blooming dataset·normalizer X). memory `project_poc_single_client_clumi`.
- **수정영역 최소 설계**: 컬럼명 = `schemas/inputs/` 1곳 집중 / metric tool = generic(op·field) → 새 KPI = pipeline YAML 1개 / 파일위치 = DataSource mapping 1줄.
- `normalizers/` + M2(기존 tool 리팩터) = **MVP+ 연기** (진짜 외부 2번째 client 시). ADR-027/028 박제 유지. memory `feedback_tool_coupling_is_data_fit`.

**남은 작업** (52 pipeline + 5 v1 페이지 + v1/mock 정리 완료 후): ① M5 (DC-PERM test, normalizer 리팩터와 함께 MVP+ 일부) · ② git push (local main 다수 ahead) · ③ O05 베타 0.002 업그레이드(68 §7.5.10) · ④ 포트폴리오 3 stub 의 실제 구현(MVP+ 다중 client). Batch 4~6 mock raw 는 `data/clumi/raw/` 로컬 (data/ gitignore).

---

## 2. 즉시 다음 액션 (compact 직후)

> **Phase 1 코드 구현은 완료됨.** 사용자 지시 대기 상태. 아래는 *남은 선택지* — 사용자 명시 후 진행.

1. **본 문서 §1 (Phase 1 진척표) 읽기** — 무엇이 완료됐는지 (52 pipeline + frontend 5 페이지 + mock 폐기).
2. **남은 선택 작업** (전부 사용자 결정):
   - **git push** — 이번 세션 30 commit 이 origin 대비 ahead (아직 push 안 함). 가장 먼저 추천.
   - **M5 DC-PERM test** — Tool client-종속 hardcode 검사 (단, normalizer 미도입이라 일부는 MVP+).
   - **MVP+**: 포트폴리오 3 stub 실구현(다중 client) · O05 베타 0.002 (68 §7.5.10) · M2 (기존 clumi tool 표준 schema 리팩터 + normalizer, 진짜 2번째 client 시).
3. **작업 패턴 (이미 확립)**: 새 시각화 = `backend/app/pipelines/flows/{name}.yaml` 1개 (Runner·API·페이지 무변경) + 필요 데이터는 `36_clumi_mock_raw_data_design` 문서에 컬럼 제안→검토→`data/clumi/raw/` 생성 (memory `feedback_mock_raw_design_doc_first`). ML 결과는 raw 아닌 MockMlModel.
4. **방법론**: ADR-024 (작성-검증-수정) + ADR-026 (Visualization-First). 삭제 전 참조 전수 검증 (이번 세션 mock 정리 패턴).

---

## 3. 2026-05-28 완성된 것 (9 commits 누적)

```
f6aa1ad  Phase 0.5 A  63 §2.3.3 Pipeline API + §8.6 Invocation 시퀀스 + §7.1.1 에러코드
c8d9c7f  Phase 0.5 B  68 Batch 2 Dashboard v1 6 pipeline
8ecd7de  Phase 0.5 C  68 Batch 3 Channel 3 pipeline
4e1472d  ADR-025      Pipeline Customization 3 Layer
0047155  Phase 0.5 D  68 Batch 4 Trend 8 pipeline + §3.6 cache framing
a8ad1e1  Phase 0.5 R7 4 신규 ADR (026·027·028·029) + 022·025 갱신 + INDEX + 68 §3.7 (1273 lines)
03033e8  Phase 0.5 F  68 Batch 6 Cost 7 + O05 AI 추천 = 52 pipeline 전체 완료
```

(+ Batch 5 Creative 7 = R7 commit a8ad1e1 에 동반)

---

## 4. 핵심 결정 (compact 에서 잃지 말 것)

### 4.1 신규 ADR 4종 (2026-05-28, 사용자 7 라운드 토의 R1~R7)

| ADR | 핵심 |
|---|---|
| **ADR-026** Visualization-First Iterative Design Flow | **10 step** 작업 방법론 (시각화 → 값 → 방법 → tool/pipeline → 필요 data → **raw 검증** → 역방향 정합). step 6 = PASS·WARN·FAIL 3 분기. **mock data = raw 자체 변경 가능 (POC 자유도)** |
| **ADR-027** 5 주체 권한 분리 | Pipeline·Maker·DataSource·Tool·**ml_model**. **ml_model adapter** (ABC + DI + Mock·Llm·Production swap). **Tool 영구 production / ml_model 구현체만 swap**. 표준 schema = `backend/app/schemas/`. client 매핑 = `normalizers/{client}.yaml` |
| **ADR-028** Hardcode 금지 + raw 4 분류 + LLM | Hardcode 3 분류 (A 금지·B 표시·C 허용). **raw 4 분류**: B1 진짜 / B2 mock {B2a 단순·**B2b ml_mock**} / B3 tool 산출 / B4 외부 산출 (명명 미정). **LLM 분석 = LlmMlModel 구현체** |
| **ADR-029** 폴더 명명 원칙 | 3 원칙 (P1 시스템 본질 + P2 typical 정합 + P3 영역 명확). `dream_agent/models/` = agent 전용 유지 |

### 4.2 ml_model adapter 핵심 (ADR-027 §3)

```
정상 작동 (영구):  Tool → ml_model.analyze() → 결과
POC v1:           Tool → ml_model.analyze() → [MockMlModel → ml_mock_data]
MVP+:             Tool → ml_model.analyze() → [ProductionMlModel → 실 추론]
                                              ↑ DI 1 줄만 swap
```

**3 영역 영구** (Tool 코드 / ml_model ABC / 호출 코드) / **1 영역 swap** (ml_model 구현체).

ml_model 3 구현체:
- `MockMlModel` (POC — `data/ml_mock/*` fixture 반환)
- `LlmMlModel` (POC+ — 현 LLM 인프라 `dream_agent/llm_manager/client.py`)
- `ProductionMlModel` (MVP+ — 진짜 학습 모델)

### 4.3 Phase 1 신설 폴더 (ADR-029)

```
backend/app/
├── schemas/            # ⭐ Pydantic 단일 진실 소스 (inputs/ + outputs/)
├── normalizers/        # ⭐ client 별 컬럼 매핑 YAML (clumi.yaml + blooming.yaml)
├── ml_models/          # ⭐ ML 추론 어댑터 (base.py + mock.py + llm.py)
├── pipelines/          # ⭐ Pipeline Runner + Validator + flows/
├── data_sources/       # 기존 (어댑터 — 책임 확장)
├── workspace/          # 기존
└── dream_agent/        # 기존 (models/ = agent 전용 유지)

data/
├── ml_mock/            # ⭐ ML mock fixture (sentiment/ ai_axes/ keywords/ fatigue/ recommendations/)
└── {client}/raw·cleaned·computed/
```

### 4.4 사용자 통찰 박제 (memory 후보)

| 통찰 | 의미 |
|---|---|
| **시각화 → 역방향 정합** | 기존 mock 에 맞추지 말고 시각화 출발 (ADR-026) |
| **Hardcode 어디서도 금지** | client 종속 = DataSource 정규화 (ADR-027·028) |
| **Tool 다 만든다, ml_model 만 mock** | Tool = production / ml_model 구현체 swap |
| **O05 = 베타 0.001, 지속 업그레이드** | AI 추천 = 단순 시작 + 로드맵 (68 §7.5.10) |
| **사용자 = 초보자, 권장 적극** | 사용자 표현 = 질문일 수 있음. 선호 X. 전문가 권장 (memory `project_no_user_domain_assumption` 인접) |
| **cache = Workspace 변환 산출물** | 통상 cache (임시 사본) ≠ 본 시스템 (영속 자산). 68 §3.6 |

### 4.5 기존 framing (Phase 0.5 이전)

| ADR | 핵심 |
|---|---|
| ADR-022 | DataSource·Workspace 관절 (P1·P2·P3) |
| ADR-023 | Pipeline 5 외부 주체 + Trigger 추상화 (button/upload/cron/webhook/agent) |
| ADR-024 | Iterative Refinement (V1~V5 검증 사이클) |
| ADR-025 | Customization 3 Layer (L1·L2·L3) |

---

## 5. 파일·문서 위치 맵

| 영역 | 위치 |
|---|---|
| **65 spec** (지도) | [docs/agent_specs/65_dashboard_pages_v1.0.md](../agent_specs/65_dashboard_pages_v1.0.md) |
| **68 spec** (52 pipeline) ⭐ | [docs/agent_specs/68_pipeline_catalog_v1.0.md](../agent_specs/68_pipeline_catalog_v1.0.md) |
| **63 spec** (Pipeline Invocation) | [docs/agent_specs/63_frontend_backend_contract_v1.0.md](../agent_specs/63_frontend_backend_contract_v1.0.md) §2.3.3 + §8.6 |
| **ADR-026~029** ⭐ | [docs/agent_specs/adr/](../agent_specs/adr/) |
| **ADR INDEX** | [docs/agent_specs/adr/INDEX.md](../agent_specs/adr/INDEX.md) |
| **LLM 인프라** | [backend/app/dream_agent/llm_manager/client.py](../../backend/app/dream_agent/llm_manager/client.py) |
| **DataSource** | [backend/app/data_sources/](../../backend/app/data_sources/) (base.py + file.py) |
| **Direct API** | [backend/api_v2/routes/dashboard1.py](../../backend/api_v2/routes/dashboard1.py) (`_cached_or_run`) |

---

## 6. 남은 작업 (Phase 1 + Phase 2)

### Phase 1 — POC v1 코드 구현

| 단계 | 작업 | 상태 |
|---|---|---|
| 5 | `backend/app/pipelines/{models,loader,runner,validator}.py` | ✅ M1 (b459d07) |
| 6 | `backend/app/pipelines/flows/*.yaml` (Batch 1 전체 21) | ✅ M1b-2 (7b85402) |
| 7 | `POST /api/admin/pipelines/run/{name}` + GET status + run store | ✅ M1b (9763a19) |
| 8 | Frontend "🔄 데이터 분석" 버튼 + useRunPipeline + usePipelineRun | ✅ M4 (ee7119e) — K01 단일, "전체 21" 확장 남음 |
| 1 | `backend/app/schemas/{inputs,outputs}/` 신설 (Pydantic 표준 schema) | ⬜ M2 ⚠️위험 |
| 2 | `backend/app/normalizers/{clumi,blooming}.yaml` (컬럼 매핑) | ⬜ M2 ⚠️위험 |
| (1·2 후) | 기존 Batch 1 tool 을 표준 schema·normalizer 로 리팩터 (정답 보존) | ⬜ M2 ⚠️위험 |
| 3 | `backend/app/ml_models/{base,mock,llm}.py` (ABC + Mock + Llm) | ⬜ M3 |
| 4 | `data/ml_mock/*` fixture (sentiment·ai_axes·keywords·fatigue·recommendations) | ⬜ M3 |
| 9 | DC-PERM-1~6 test (권한 검사) | ⬜ M5 |

**M2 위험 메모**: 단계 1·2 (schemas/+normalizers/) = 신규 파일 → 저위험. 그러나 *기존 tool 리팩터* (df["한글컬럼"] → Pydantic 필드) = 정답 17 생성 코드 수정 → ADR-024 V4 회귀 (정답값 비교) 필수. tool 1개씩 점진 + 매번 회귀.

### Phase 2 — 5 페이지 완성 (~57h ≈ 1 sprint)

- 65 §14.6.10 의 41 tool 신설 (ADR-027 권한 분리 준수)
- 5 v1 페이지 작동 완성
- O05 AI 추천 베타 0.001 (LlmMlModel)

### 진화 (별 사이클)

- O05 업그레이드 (베타 0.002 → MVP+) — 68 §7.5.10 로드맵
- B4 (외부 산출 input) 명명 결정 — MVP-1
- L3(b)(c) (YAML formula / DSL) — MVP+
- Agent Maker (Skills) — 별 ADR (ADR-023 미해결)

---

## 7. ADR-024 검증 사이클 결과 (Phase 0.5 전체)

| Batch / 작업 | V1 | V2 | V3 | V5 |
|---|:---:|:---:|:---:|:---:|
| A (63 §2.3.3) | 9/9 | 6/6 | A·A·A·A | — |
| B (Batch 2) | 5/5 | 6/6 | A·A·A·A·A | — |
| C (Batch 3) | 4/4 | 6/7 | A·A·A | 3/3 |
| ADR-025 | — | 8/8 | A·A·A | 3/3 |
| D (Batch 4) | 6/6 | 8/8 | B·A·A·A·A | — |
| R7 (4 ADR) | 3/3 | 7/7 | A·A·A | 2/2 |
| F (Batch 6) | 4/4 + LLM | 10/10 | A·A·A·A | 4/4 |

→ **전 사이클 V3 사용자 검토 게이트 통과**. ADR-026 step 1~10 = Batch 6 첫 정방향 적용.

---

## 8. 컨텍스트 빠른 복원 (compact 후 "이어서 진행" 만 하면)

1. 본 문서 **§1 (진척표) + §2 (다음 액션)** 읽기 — Phase 1 코드 완료, 남은 = 선택.
2. 코드 위치: `backend/app/pipelines/`(Runner·flows 52) + `backend/app/ml_models/`(adapter) + `backend/app/schemas/`(inputs·outputs) + `frontend/src/features/{dashboard_v1,channel,trend,creative,cost}/` + `frontend/src/components/charts/`.
3. **사용자 지시 대기** — git push / M5 / MVP+ 중 선택. 임의 진입 X.
4. 핵심 memory: `project_poc_single_client_clumi`(clumi 단일·mock 폐기) · `feedback_mock_raw_design_doc_first` · `feedback_tool_coupling_is_data_fit` · `project_core_value_data_transformation`.

---

## 9. 변경 이력

| 일자 | 내용 |
|---|---|
| 2026-05-28 (초안) | Phase 0.5 A1 진입 직전 (63 §3.x 작성 전) |
| 2026-05-28 (갱신) | **Phase 0.5 완성 — 68 52 pipeline + 8 ADR + 63 Pipeline Invocation.** 9 commits (f6aa1ad ~ 03033e8). 신규 ADR 4종 (026 Visualization-First / 027 5 주체 권한 / 028 Hardcode·raw 4 분류 / 029 폴더 명명). ml_model adapter (Tool 영구 / 구현체 swap). Phase 1 신설 폴더 (schemas·normalizers·ml_models·pipelines + data/ml_mock). O05 베타 0.001 + 로드맵. Phase 1 진입 직전 (~27h). ADR-024 전 사이클 V1~V5 통과 박제. |
| 2026-05-28 (Phase 1) | **Phase 1 기반 완성 — Pipeline Runner.** 4 commits (b459d07 M1 Runner / 9763a19 M1b API+store / ee7119e M4 프론트 버튼 / 7b85402 M1b-2 Batch 1 21 YAML). `backend/app/pipelines/` (models·loader·runner·validator·store·errors) + `flows/` 21 + `/api/admin/pipelines` 4 endpoint + `frontend/src/api/pipelines.ts` + RefreshButton. 정답 S001=119,539,660 compute-path 보존 검증. pipelines test 35/35 + 프론트 83/83. |
| 2026-05-28 (Phase 1 +5) | **버튼 전체실행 + M3 + 방향전환 + Batch 2.** 5 commits (43379e5 버튼 21 병렬 / 3b96687 M3 ml_models adapter / 483905f Batch 2 Dashboard v1 6 pipeline). **방향 전환: blooming 제외 → clumi 단일 + mock raw** (memory `project_poc_single_client_clumi`·`feedback_tool_coupling_is_data_fit`). `schemas/inputs·outputs` 신설(컬럼명 집중) + generic aggregate tool(수정영역 최소) + ml_model adapter(ABC+Mock+Llm). normalizer·M2 = MVP+ 연기. test pipelines 43 + ml_models 11 + 프론트 88. |
| 2026-05-28 (Batch 3~6) | **52 pipeline 전체 완성.** 441138d Batch 3 Channel(daily 재사용, 신규데이터 0) / 58af603 Batch 4 Trend(reviews + ml_model 감성·키워드 실증) / 392a18d Batch 5 Creative(creatives·ab_tests + ml_model AI축·피로) / 7667f40 Batch 6 Cost+AI(budget·keyword + O05 추천). mock raw 설계문서 `36`(69→30번대 정정) + `feedback_mock_raw_design_doc_first` memory. 데이터 검토 게이트 거침. |
| 2026-05-28 (frontend + 정리) | **frontend 5 v1 페이지 + mock 레거시 폐기.** 33b35a4 category endpoint / 6617c7d 5 페이지+차트 7종+useCategoryResults / 538d531 라우팅 전환 / 1d3d551 고아 페이지 4 삭제 / 5fa0e87 mock-API 레이어(/api/mock·useMockData·test) 전면 폐기 + 포트폴리오 3 stub. **blooming 완전 폐기 → 데이터 = pipeline only.** backend 89 + 프론트 typecheck·88·build(2936). **이번 세션 30 commit (b459d07~d6d0e9e). Phase 1 코드 완료 — 남은 = M5·push·MVP+ (선택, 사용자 대기).** |
