# agent_specs/ INDEX

> OctorAD Dream Agent V2 개발 명세서 맵.
> 진실 소스는 **코드** (`backend/`). 이 문서들은 설계 계약/참조.

---

## 📘 번호 체계

| 범위 | 영역 | 설명 |
|------|------|------|
| **00~09** | 요구사항 (Requirements) | 비즈니스 목표 / FR·NFR / 범위 |
| **10~19** | 아키텍처 (Architecture) | 전체 구조 / AgentState / Lifecycle / Manager Layer |
| **20~29** | API 계약 (API Contracts) | REST / WebSocket / Error / Sequence |
| **30~39** | 데이터 (Data / Models) | Pydantic 모델 / Agent & Tool / Prompt |
| **40~49** | 운영 (Operations) | Runbook / Testing / Env / **Lifecycle** | *(40 신규 2026-05-18)* |
| **50~59** | 제품/UX (Product) | Glossary / User Journey | *(Sprint 14+ 예정)* |
| **60~69** | 프론트엔드 (Frontend) | Tech Stack / Architecture / Component / Workflow Canvas | *(Sprint 15 신규 — vision H4 맞춤화 UI)* |

버전은 suffix `_v<major>.<minor>.md` 로 일관 유지.

---

## 📚 현재 문서 목록

### 00대 — 요구사항

| 번호 | 문서 | 역할 |
|------|------|------|
| **00** | **[00_vision_and_intent.md](00_vision_and_intent.md)** | **🌟 north star — 사용자 ↔ 에이전트 파트너쉽 / 자유 대화 / 학습 / 맞춤형 비전. 모든 spec 의 source of truth. 가치 가설 H1~H4 + POC 1차 학습 + ADR 매핑 (2026-04-28 신규)** |
| 01 | [01_requirements_v1.6.md](01_requirements_v1.6.md) | 비즈니스 목표 / 페르소나 / FR(12 분해 8 sub + 13c + 총 ~20 entry) + UX(12) + NFR(14) / In·Out of Scope / Acceptance (**Sprint 14 A3 Phase 5 편집 경로 통합 완료**) |

### 10대 — 아키텍처

| 번호 | 문서 | 역할 |
|------|------|------|
| 10 | [10_system_architecture_v1.9.md](10_system_architecture_v1.9.md) | 전체 시스템 구조, 4-Layer, Manager 목록 개요, Sprint 13 + Sprint 14 A1 반영 |
| 11 | [11_main_graph_state_v1.5.md](11_main_graph_state_v1.5.md) | AgentState TypedDict + Reader/Writer 매트릭스 + `init_agent_state` + Settings + **Reducer 보류 (Sprint 14 A1)** |
| 12 | [12_manager_layer_v1.4.md](12_manager_layer_v1.4.md) | 5 매니저 개별 API + 수명주기 + HITLManager Sprint 14 A1/A3 확장 + **v1.4 (2026-05-16) ADR-011 ConnectionManager 채널 분리** — `(user_id, channel)` 기반, MAX (user, channel) 별 5, broadcast 채널 격리 |
| 13 | [13_lifecycle_v1.3.md](13_lifecycle_v1.3.md) | Turn 상태 머신 + interrupt/resume + Pause 타이밍 + Checkpoint 복원 + **Sprint 14 A1 HITL timeout 분기 + T-1/T-2/T-3 시나리오**. v1.3 (2026-04-27) 관련 명세 링크 갱신 |
| **14** | **[14_system_agent_overview_v1.0.md](14_system_agent_overview_v1.0.md)** | **시스템 에이전트(4-Layer OS Agent) 통합 지도 — Cognitive/Planning/Execution/Response 책임·입출력·구현 현황 + Manager Layer + 사용자가 놓치기 쉬운 포인트** |
| **15** | **[15_end_to_end_flow_v1.0.md](15_end_to_end_flow_v1.0.md)** | **🎯 신규 입사자 first read — 사용자 query → 응답까지 한 사이클 Mermaid sequence (full happy path + HITL + 5 PauseBox 액션) + 4-Layer 책임 한 줄 + 채널 2개 + 데이터 source + Reading Order 표** |
| **16** | **[16_layer_dependency_architecture_v1.0.md](16_layer_dependency_architecture_v1.0.md)** | **⭐ 물리 모듈 레이어 의존 구조 — `api_v2→agent→tool→data` 하향 그래프 + 검증된 4 불변식(grep 0건: data↛agent, tool↛orchestration, agent-data 순수, stage DAG) + 위반 5건(🔴 V1 core↔workflow_managers 순환 / 🟡 V2 ml_models→agent infra 누수 / 🟢 V3 tool 순수성 스멜·V4·V5) + tool 데이터 접근 규칙(BaseTool.fetch only + 예외 2). 디렉터리→레이어 귀속표(core/pipelines/ml_models/api_v2 포함). file:line 근거 + 독립 적대적 재검증. 의존-방향 단일 권위 (2026-06-05)** |
| **17** | **[17_functions_to_io_v1.0.md](17_functions_to_io_v1.0.md)** | **🔗 종단 매핑 — 마케터 기능 24 → 에이전트 9 → 툴 ~46 → 데이터 12 CSV → I/O 메커니즘 5 룰 한 흐름. 14(Layer 축) / 15(시간 축) 와 자매 = 17(계층 축). §5 가 신규 — `_inject_prev_outputs` setdefault·`_` prefix·COMPLETED·dict 룰 + raise vs error + pickle 금지 + mock fallback. 신규 Tool 종단 체크리스트 §7 (2026-05-18)** |
| **18** | **[18_engineering_disciplines_v1.0.md](18_engineering_disciplines_v1.0.md)** | **⚙ Engineering Disciplines — 시스템을 만든 4 축(하네스=8gate / 프롬프트 / 컨텍스트=4-Layer / tool 구현)의 책임·코드위치 + §2 게이트 두 종류(현실가드/가리개) + **§3 stage-2 근원귀속**(깨짐 5종→축 매트릭스: 프롬프트>하네스>>tool, 데이터 건강, 적대검증이 cycle/cognitive 오진 2건 기각) + §4 징후→진단 가이드. "복합쿼리가 깨지면 어느 축인가" 단일 진실 소스 (2026-06-11) ⚠️ "하네스=8gate" *용어*는 [19 헌법](19_architecture_constitution_v1.0.md) §2가 정정(plan repair로 재분류)** |
| **19** | **[19_architecture_constitution_v1.0.md](19_architecture_constitution_v1.0.md)** | **⭐⭐ 아키텍처 헌법 — 모든 변경의 자. 불변식 5(I1 정직~I5 감지=정책입력) + 5층 용어 확정(Contract/Guardrail/Plan repair/Policy/Harness — "하네스=게이트" 오용 금지) + 오너 비준 결정 3(D1 계약=코드 1곳 / D2 위반=거부 / D3 period없음=정직 degrade) + 경계 규약 R1~R6 + ★신호 라우팅 표(신호→지정 소비자, R6: 소비자 없는 신호 금지) + 정직 표면 H1~H5 + 신규 장치 채용 기준 3문항(상설) + 슬라이스 매핑 + 오너 기준질문 G1~G6. period silent-zero 사태 → Fable 검토+2차 재분석 종합의 산물 (2026-06-11)** |

### 20대 — API 계약

| 번호 | 문서 | 역할 |
|------|------|------|
| 20 | [20_INTERFACE_CONTRACT_v1.1.md](20_INTERFACE_CONTRACT_v1.1.md) | REST 엔드포인트 + Layer Contract + AgentState Contract + Session 식별 + Sprint 14 A1 Manager API 변경 요약 |
| 21 | [21_WEBSOCKET_PROTOCOL_v1.5.md](21_WEBSOCKET_PROTOCOL_v1.5.md) | `/ws/agent` + `/ws/hitl` 메시지 / 이벤트 / 시나리오 / interrupt payload / **complete.reason + hitl_ack.reason 카탈로그** / **A3 Phase 5 approve→modify 변환 + plan_review 임시 progress** / **v1.5 (2026-05-16) ADR-011 ConnectionManager 채널 분리 — fan-out 키 `(user_id, channel)`, §3.2 hitl 카탈로그 엄격 적용** |
| 22 | [22_error_codes_v1.1.md](22_error_codes_v1.1.md) | 모든 error code 단일 카탈로그 (진실 소스 = `backend/app/core/error_codes.py`) |
| 24 | [24_sequence_diagrams_v1.3.md](24_sequence_diagrams_v1.3.md) | 7+3+1 시나리오 시퀀스 — Happy/Reject/Pause/Restart/Concurrent/Guard/Multi-tab + Sprint 14 HITL timeout 3건 + **A3 Phase 5 Plan review 편집 통합 §8** |

### 30대 — 데이터

| 번호 | 문서 | 역할 |
|------|------|------|
| **30** | **[30_DATA_MODELS_v1.1.md](30_DATA_MODELS_v1.1.md)** | **★ Pydantic 모델 / Core Enum / HITL 모델 + 코드 참조 매핑 — v1.1 검증 정정판 (2026-05-15).** v1.0 원본 = [`legacy/30_DATA_MODELS_v1.0.md`](legacy/30_DATA_MODELS_v1.0.md) 보존 |
| 31 | [31_execution_agent_function_list_v0.6.md](31_execution_agent_function_list_v0.6.md) | 실행 Agent별 기능 + Tool 매핑 (POC 범위 — **요구사항**) |
| **32** | **[32_execution_agent_tools_v1.0.md](32_execution_agent_tools_v1.0.md)** | **실행 에이전트(Tool) 카테고리 정의 + 구현 현황 & 확장 가이드 (내부 v1.3, 2026-06-11) — 31과 짝. ★구현 ~90 tool (전수표는 [33_tools_by_category/](33_tools_by_category/README.md) 로 위임, §7 폐기), 8 카테고리 decision tree(§2.5), 옵션C 입출력 계약(§2.7), Tool 추가 체크리스트, anti-pattern** |
| **33** | **[33_tools_by_category/](33_tools_by_category/README.md)** | **카테고리별 tool 인벤토리 (32의 전수표 — 9파일: metrics 35·collection·comparison·normalization·cleaning·analysis·report + README). 각 tool → methodology S-코드·input·output·status 매핑. 32 §7이 진실 소스로 위임** |
| *34* | *(예정) 34_prompt_catalog_v1.0.md* | LLM 프롬프트 (`llm_manager/prompts/*.yaml`) 단계별 매핑 |
| **35** | **[35_DB_SCHEMA_v1.0.md](35_DB_SCHEMA_v1.0.md)** | **PostgreSQL DB Schema — ERD (LangGraph + memory_entries) + 의미적 hierarchy (User/Conversation/Turn) + 8 memory type + content JSONB schema + 자주 쓰는 query (E2-5 conversation list 등) + 향후 확장 (Sprint 14 A3 / Sprint 15 P0 baseline)** |
| **36** | **[36_clumi_mock_raw_data_design_v1.0.md](36_clumi_mock_raw_data_design_v1.0.md)** | **clumi Mock Raw Data 설계 (POC) — Phase 1 mock raw 단일 진실 소스. POC=clumi 단일 client, `data/clumi/raw/` 표준 영어 컬럼 (normalizer 불필요). §1 campaigns·§2 daily_performance (Batch 2·3 생성분) + §3~5 reviews·creatives·ab_tests (Batch 4·5 placeholder). 절차: 문서 정의→사용자 검토→CSV+schemas/inputs+DEFAULT_MAPPING→pipeline. 68(pipeline)·65(dashboard) 가 본 데이터를 소비. memory `feedback_mock_raw_design_doc_first`·`project_poc_single_client_clumi` (2026-05-28)** |
| **37** | **[37_agent_language_pmal_v1.0.md](37_agent_language_pmal_v1.0.md)** | **⭐ Agent Language (PMAL) — cognitive 출력 = planning 입력 inter-layer 계약 (에이전트 언어). 구조 (`intent: operation(authored)×domain(SET)×metric(open)×dimensions` + period/benchmark/filters/output, **source 축 금지**) + 레이어 헌장 (NL-free·도메인-complete·카탈로그-free) + v0→v1 마이그레이션 (operation→TaskType shim, diagnose/forecast/attribute 제외) + **진화 로드맵 (v0 닫힌enum → v1 PMAL 열린어휘 → v2 사용학습 → v3 skill참조)** + F2 차단 매핑. 설계 수렴(검증-재검증, 원문 `_claude/.../cognitive_planning_enhance` §8) / 구현 = Phase B. 2026-06-04** |
| **39** | **[39_query_categories_and_routing_v1.0.md](39_query_categories_and_routing_v1.0.md)** | **🧭 Query Categories & Routing — 시스템의 4 "결"(분석사다리 탐색→진단→추론→예측 / 질의응답 Q&A / 의사결정 추천 / 텍스트) + cognitive operation→intent_shim→TaskType→tool 배선 + QA/recommendation short-circuit(단일의도 한정) + 카테고리→agent/tool 표 + 복합쿼리 stage-2 현황(sub_intents 미배선=R2). 2026-06-10~11 세션(분석사다리·Q&A·의사결정 신설) 흡수. 37(PMAL operation 어휘)·32(tool 현황)·18(축) 짝 (2026-06-11)** |
| **38** | **[38_external_api_collection_architecture_v1.0.md](38_external_api_collection_architecture_v1.0.md)** | **외부 API 수집 → 회사 DB 저장 아키텍처 (as-built 박제 + MVP 방향) — 사용자 의도(external API→회사 DB raw 저장)가 코드 어디에 구현됐는지 통합 hub. 2 진입점: seed(`load_raw_to_data_db`: `data/{client}/raw`→PG `_workspace`) + 런타임(`ExternalRawCollector`: mock_api→raw), internal 은 raw 직접 읽기. DATA_BACKEND 토글. ★카운트 정정: 레지스트리 ext16+int14=30 vs collector 13+8=21, external 3 orphan(reviews·keyword_performance·daily_performance = mock_api·collector 부재 갭) 식별. 기존 분산 문서(ADR-022/027/028·수집설계노트·33·35·36) 통합. workflow `wf_c960b7b0` 검증 (2026-06-09)** |
| 🎨 | **[erd_database.md](erd_database.md)** | **ERD 시각화 모음 — Mermaid 7 view: Database ERD / 의미적 hierarchy / 데이터 흐름 (read·write·clarification) / Memory type 분류 / Sprint timeline / E2-5 sidebar / H0 자동 해결. 35 spec 의 시각화 보조** (에이전트 DB — 비즈니스 데이터 아님) |
| 🗃 | **[ERD/INDEX.md](ERD/INDEX.md)** (데이터 구조 재설계 폴더 — 과설계 점검·로드맵·방법론) | **★ raw→canonical 재설계 작업 폴더. ① [erd_octorad_raw_v1.0.md](ERD/erd_octorad_raw_v1.0.md)(+.dbml) — 실파일 직독 raw ERD 30파일/34테이블/11도메인·확정Ref17·추정7·drift·사전정합·stub·GA4노트. ② [normalize_synonym_classification_v0.1.md](ERD/normalize_synonym_classification_v0.1.md) — 채널 동의어 49 cluster + 충돌 레지스터(단위/ID공간/grain/의미함정) + 명명대기 + 실측해소(ccnt 등). ③ [normalize_implementation_research_v0.1.md](ERD/normalize_implementation_research_v0.1.md) — 외부 4각도(교과·트렌드·AX·아키텍처, 출처22) → 아키텍처 ⓐ~ⓔ 비교·권장(ⓔ 하이브리드: 채널별 declarative translator + canonical contract + LangGraph fan-out/in). ④ [octorad_raw_metadata_v0.1.md](ERD/octorad_raw_metadata_v0.1.md)(+.yaml) — 테이블 메타(벤더·API·doc·grain·PII) + 컬럼 description 712개(source/confidence: vendor_doc 266·dict 238·classification 44·inferred 164 / high 601). canonical contract 씨앗. 재생성 파이프라인=`docs/_claude/data/erd/`(local)** |
| 🗂 | **[data/description/mock/INDEX.md](../../data/description/mock/INDEX.md)** | **POC mock 데이터 해설 6 분할 진입점** (2026-05-18 신설) — INDEX / SCHEMA (12 시트 컬럼 175 + Status 마커) / RELATIONSHIPS (ERD + 함정 5) / API_MAPPING (`/api/mock/...` 12 endpoint + % 자동 변환) / UI_MAPPING / ROADMAP (POC→MVP→Prod). raw = `data/mock/*.csv`. 본 spec 들의 *데이터 차원 보조*. 3 사이클 검증 통과 (회귀 191+56). |

### 40대 — 운영 (신규)

| 번호 | 문서 | 역할 |
|------|------|------|
| **40** | **[40_agent_tool_lifecycle_v1.0.md](40_agent_tool_lifecycle_v1.0.md)** | **🔄 교체·재구성·버전 변경 운영 가이드 — OS 층 vs 콘텐츠 층 경계 명시 (§1) + 5 변경 시나리오 표준 절차 (Tool 추가/폐기/에이전트 재구성/데이터 source/v2 메이저) + 영향 분석 매트릭스 + 회귀 테스트 범위 + FAQ. "지금 만들어진 에이전트 다 지우고 새로" 같은 질문의 단일 진실 소스 (2026-05-18 신규)** |
| **41** | **[41_agent_tool_change_hub_v1.0.md](41_agent_tool_change_hub_v1.0.md)** | **🚪 Agent/Tool 변경 작업 — 단일 진입점 (Change Hub) — 40 의 빠른 시작 버전. §2 손대는 4 파일 매트릭스 + §3 5 시나리오 + §4 변경 종류별 영역 매트릭스 + §5 표준 5 Phase + §6 예시 ("7→12 카테고리 33 툴 재구성") + §8 핵심 참조 link 10. 변경 작업 시 첫 번째 봐야 할 문서 — 1 문서 + 참조 link 만으로 작업 진입 (2026-05-18 신규)** |
| **42** | **[42_quick_navigation_v1.0.md](42_quick_navigation_v1.0.md)** | **🧭 Quick Navigation — 자주 묻는 질문 진입점. §1 자주 보는 spec 11 link + §2 FAQ 5 카테고리 25 매핑 (구조/변경/데이터/결정/로드맵) + §3 INDEX 7 매트릭스 + §4 디렉토리 한 페이지 지도. CLAUDE.md (가벼움 유지) 짝 — 필요 시 사용자가 진입. "어디 봐야 할지 모를 때" 첫 진입점 (2026-05-18 신규)** |
| **44** | **[44_concepts_data_transfer_v1.0.md](44_concepts_data_transfer_v1.0.md)** | **📖 데이터 전달 시대 개념 사전 — 2026-06-12~13 재설계 대화의 신개념 ~20개 (엔지니어링 4분류·판별 질문 / 장부·신분 3분류·누적 계약·멀티스코프 천장 / 계획된 블랙보드·버그의버그·계약-게이트 관계·보존 5 / 동사 규약·역할 설계 3단계·문서 생존 장치). 모든 정의에 출처 — 오너 기준 수립용. 기준서·계획서의 표준 어휘 (2026-06-13 신설)** |
| **43** | **[43_gate_ledger_v1.0.md](43_gate_ledger_v1.0.md)** | **🛡 Gate Ledger — 런타임 검증·수선 게이트 전수 등기부 (G01~G28: 현역 27 + 예정 1[G28 마커 생존 가드], 전 행 코드 실측) + 데이터 평면 관절(pushdown 26배 실증 포함) + 오프라인 하네스(M0 측정기 4종 예정) + **§5 건설 현황 오버레이**(2트랙이 뼈대의 어디를 짓는지) + **§4-2 두 평면 뷰**(검사 대상 축 언어/접점/데이터/표면 — "왜 cognitive·planning에도 게이트가?" 박제). ★구조도 전략 = "표가 진실, 그림(Mermaid)은 `scripts/generate_gate_map` 생성물" — `test_gate_ledger_sync` 가 표↔그림 drift RED 강제. 헌법 19 §5(신호 라우팅)의 게이트 관점 짝 (2026-06-12)** |

### 60대 — 프론트엔드 (Sprint 15 신규)

| 번호 | 문서 | 역할 |
|------|------|------|
| **60** | **[60_frontend_overview_v1.0.md](60_frontend_overview_v1.0.md)** | **⭐ Frontend 진입점 — Vision H1~H4 매핑 + 5 UX 원칙 + Tech Stack 결정 (Vite + React 19 + TS + Tailwind v4 + shadcn/ui + Zustand + TanStack Query + @xyflow/react + dagre) + 7 Sprint roadmap (Sprint 0~6 + 7+) + W1~W4 Workflow Canvas Phase 매핑 + 학습 곡선 (~3주) + 보안/호환성/Risk. 60대 다른 문서들의 진입점** |
| **61** | **[61_frontend_architecture_v1.0.md](61_frontend_architecture_v1.0.md)** | **State (Zustand 7 store + TanStack Query) + Routing (15 라우트 + GlobalLayout + Workspace, 2026-06-01 갱신) + Component Inventory (shadcn/ui 15+ + features 폴더) + Design System (색상 토큰 라이트+다크+의미적 / Tailwind config / Pretendard / cn-cva 패턴) + v1→v2 마이그레이션 매트릭스** |
| **62** | **[62_workflow_canvas_design_v1.2.md](62_workflow_canvas_design_v1.2.md)** | **⭐ Workflow Canvas (React Flow) — vision H4 맞춤화 UI 핵심. 노드/엣지 schema + 자동 레이아웃 (dagre) + 인터랙션 (NL 편집 + 시각적 편집 공존) + Save/Load (memory_entries.type=workflow_template) + 4+1 Phase 로드맵 (W1~W4 + W2′) + **v1.2 (2026-05-17) ADR-013 W2′ 구현 완료** — §5.7 엣지/드래그 + §5.8 cycle 사전 차단 (DFS) + §5.9 issues UX (sonner toast) + §5.10 batched 모드 (applyMode + pendingOps + BatchedToolbar). 시각 편집 vs NL 편집 책임 분리 audit 정정 (TodoManager vs plan_editor)** |
| **63** | **[63_frontend_backend_contract_v1.0.md](63_frontend_backend_contract_v1.0.md)** | **Frontend ↔ Backend 계약 — REST API 매핑 (현재 4 + Sprint 15 예정 9 + **Mock 12 endpoint** v1.1) + WS 2 채널 메시지 카탈로그 + zod schema (Plan/Memory/WorkflowTemplate) + Error code 11 처리 + 시퀀스 5 + 구현 체크리스트 + DC-FE-1~5 Drift 방지** |
| **65** | **[65_dashboard_pages_v1.0.md](65_dashboard_pages_v1.0.md)** | **⭐ Dashboard Pages Specification — 5 v1 페이지 + Dashboard1 (Sprint 16) 의 *표시·분석·tool 단일 진실 소스*. 4 PART: I 현 상태 박제 (§1~§9 — 페이지 인벤토리 / 4 layer 분해 / 표시 패턴 / 데이터 source / 하드코딩 / 진화 경로 / 6×2 조합 매트릭스 N:M) + II 통합 매트릭스 (§10~§14 — 52 표시 정보 / 정보 생성 / 4 레이어 framework / Mermaid 시각화 / **21 분석 방법론 카탈로그**) + III Tool 신설 로드맵 (§15·§15.1 — D1 부족 tool 식별 ≈61 후보; D2·D3 예정) + IV 추후 구현 (§16·§17 — 학습 루프 / 외부 API / 비즈니스 적합성 / 멀티 테넌트). 사용자 5 Step 작업 흐름 박제 (시각화→데이터→raw·정제·분석→tool→구현). ADR-022 + memory `project_tool_data_agent_separation` 정합. 1,548 라인** |
| **66** | **[66_v1_to_v2_migration_map.md](66_v1_to_v2_migration_map.md)** | **v1 → v2 마이그레이션 가이드 — v1 11 페이지 → v2 14 라우트 (포트폴리오 4 + 클라이언트 8 + 신규 3) + 컴포넌트 / 15 Redux slice → Zustand store 매핑 + Sprint 별 우선순위 (Sprint 0~5+) + 변환 패턴 코드 예시 (chatPanel / navigation) + Drift 방지 체크리스트** |
| **68** | **[68_pipeline_catalog_v1.0.md](68_pipeline_catalog_v1.0.md)** | **⭐ Pipeline 카탈로그 — 52 시각화 × 52 pipeline 1:1 매핑 (사용자 결정 A). Pipeline DSL (YAML schema) + 작성 컨벤션 + 전체 매핑표 + **Batch 1 (Dashboard1 21 pipeline) 실제 YAML 완성**. Batch 2~6 (32 pipeline, Dashboard v1·Channel·Trend·Creative·Cost+AI 추천) = 후속 commit. POC v1 Phase 1 진입의 첫 referential. ADR-023 정합** |

> 참고: `docs/_claude/new_frontend/` (14 문서) 는 탐색/실험 자취 보존. agent_specs 60대 가 정식 진실 소스.

---

## 🗂 아카이브 / 보조

| 경로 | 설명 |
|------|------|
| [POC_legacy/](POC_legacy/README.md) | Sprint 13 이전 POC 초기 설계 (DATA_MODELS_poc / INTERFACE_CONTRACT_poc / WEBSOCKET_PROTOCOL_poc). 이력 보존용, Sprint 15+ 정리 예정 |
| [adr/](adr/INDEX.md) | **Architecture Decision Records** — 결정 1건 = 파일 1개. Michael Nygard 표준. ADR-000 (도입) / ADR-001 (hitl=pause 통합) / ADR-002 (NL 1·2·3차) / ADR-005 (legacy 처리) / **ADR-022 (DataSource + Workspace 관절, Sprint 16 Accepted)** / **ADR-023 (Pipeline 5 주체 + Trigger 추상화, Accepted)**. Sprint 14 A3 Phase 5 도입 (2026-04-27) |

---

## 🛠 사용/관리 규칙

### 참조 방향
- **코드 → 문서**: 코드 주석에 관련 문서 링크 (예: `# spec: docs/agent_specs/11_main_graph_state_v1.5.md`)
- **문서 → 코드**: 문서 "코드 참조" 섹션에 파일 경로 명기. 진실 소스는 항상 코드.

### 문서 추가 시 체크리스트
신규 매니저/모듈/이벤트 추가 시:
- [ ] 해당 영역 번호 내 다음 번호로 파일 작성 (12, 22, 32 등)
- [ ] 이 INDEX.md에 행 추가
- [ ] `10_system_architecture_v1.9.md` §10 관련 명세서 표 갱신
- [ ] 관련 ADR 있으면 [`adr/`](adr/INDEX.md) 에 작성 (도입됨 — 2026-04-27, ADR-000 참조)

### 버전 bump 정책
- **minor (v1.0 → v1.1)**: 내용 보강, 섹션 추가, 필드 설명 개선
- **major (v1.0 → v2.0)**: 구조/계약 breaking change (API 제거, 필드 rename)
- **파일명 동기화**: 내부 버전 bump 시 파일명도 함께 rename (`git mv`)

### Drift 방지
- Doc-Code Contract Test (Sprint 13 완료 직후 도입 예정) — 문서 내 코드 경로 자동 검증
- 각 문서 상단 "관련 명세" / "코드 위치" 섹션으로 단일 진실 소스 명시

---

## 📝 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-06-14 | **ERD/ 폴더 재설계 진행** — raw ERD(`erd_octorad_raw_v1.0`, clumi→octorad 리네임·실파일 직독 30파일/34테이블) + 채널 동의어 분류(`normalize_synonym_classification_v0.1`, 49 cluster·충돌 레지스터·ccnt 등 실측해소) + 구현 리서치(`normalize_implementation_research_v0.1`, 외부 4각도 출처22 → ⓔ 하이브리드 권장: 채널별 declarative translator + canonical contract + LangGraph fan-out/in). 단일함수(format_normalizer) 4각도 만장일치 기각. |
| 2026-06-13 | **32·33 INDEX 항목 정정 (코드 실측)** — 32 "구현 8/미구현 40+/v1.0" → 현행 "~90 tool, 전수표 33/* 위임, 내부 v1.3". 33 "(예정) team_catalog_schema" → 실재 `33_tools_by_category/` 9파일(metrics 35 등). INDEX↔코드 drift 해소. 짝 분석 = `docs/reports/시스템설계지도_OctorAD_2026-06-13.md §1-B`. |
| 2026-04-21 | 초안 — Category prefix 전환 + 현재 6개 문서 매핑 + 예정 문서 (12/22/32/33) 표시 |
| 2026-04-21 | R-9 서버 재시작 복원 구현/검증 완료 반영 — `01_requirements` / `13_lifecycle` / `21_WEBSOCKET_PROTOCOL` / `24_sequence_diagrams` 를 v1.1로 bump. `resume_query` 메시지 + `resume_only` 파라미터 + `first_iter` 분기 + CallbackManager unregister→register 중복 방지 + 대시보드 localStorage / `ws.onopen`·`ws.onclose` 복원 트리거 동작 반영. 12_manager_layer §3.4 dedup 패턴 보강. 테스트 누적 137/137 비-live pass × 3회 안정 |
| 2026-04-24 | 시스템 에이전트·실행 에이전트 통합 설명 문서 2건 신규 — [14_system_agent_overview_v1.0](14_system_agent_overview_v1.0.md) (4-Layer OS Agent 전체 지도 + 사용자가 놓치기 쉬운 포인트), [32_execution_agent_tools_v1.0](32_execution_agent_tools_v1.0.md) (Tool 구현/스텁/계획 gap 전수표 + 확장 checklist + anti-pattern + 우선순위 제안). 기존 31(요구사항)과 32(현황)의 짝 구성 명확화 |
| 2026-04-24 | **Sprint 14 A3 Phase 5 — Plan review 편집 경로 통합**. 사용자 5항목 요구사항 §4 "hitl=pause 같은 개념" 반영. 01 v1.5→v1.6 (FR-12f 단일 조건 단순화), 12 v1.2→v1.3 (`_progress` 수명주기 확장 + `cleanup_turn._progress.pop`), 21 v1.3→v1.4 (approve→modify 서버 내부 변환 + plan_review 임시 progress), 24 v1.2→v1.3 (§8 Plan review 편집 시퀀스 신규). 구현: ws_agent/ws_hitl/hitl_manager Change 4건 + Group H 8건 테스트 + regression 238 pass + 2 skip. 관련 자산: `docs/_claude/sprint14_a3_edit_flow.md` v1.1, `sprint14_a3_implementation_plan.md` v1.0, `sprint14_a3_missed_points.md` v1.1 |
| 2026-05-12 | **60대 영역 신설 — Frontend (Sprint 15)**. vision H4 맞춤화 UI 의 구체화. 신규: 62_workflow_canvas_design_v1.1.md (React Flow + 노드/엣지 schema + dagre 자동 레이아웃 + 3-panel + NL 편집과 시각적 편집 공존 + Save/Load via memory_entries.type=workflow_template + 4 Phase W1~W4 로드맵). 60/61/63 예정 표기. tech stack 결정 (Vite+React 19+TS+Tailwind v4+shadcn/ui+Zustand+TanStack Query+@xyflow/react+dagre). `docs/_claude/new_frontend/` 14 문서는 탐색 자취로 보존 |
| 2026-05-12 | **60 Frontend Overview v1.0 Accepted** (60대 진입점). Vision H1~H4 매핑 + 5 UX 원칙 + Tech Stack 결정 표 (옵션 A 트렌드 적극) + 7 Sprint roadmap (Sprint 0~6+ W1~W4 Workflow Canvas Phase 매핑) + 학습 곡선 (~3주, frontend 모름 고려) + 보안/호환성/Risk. `docs/_claude/new_frontend/` 14 문서 정제. 다음: 61 Architecture / 63 Backend Contract |
| 2026-05-13 | **61 Frontend Architecture v1.0 + 63 Frontend Backend Contract v1.0 Accepted**. 60대 완전 구성 (60/61/62/63). **61**: State (Zustand 7 store + TanStack Query) / Routing (7 라우트 + GlobalLayout + Workspace) / Component Inventory (shadcn/ui 15+ + features) / Design System (색상 토큰 라이트+다크+의미적, Tailwind, Pretendard, cn-cva). v1 (Redux) → v2 (Zustand) 매핑 매트릭스. **63**: REST API 매핑 (4 + Sprint 15 예정 9) / WS 2 채널 메시지 카탈로그 (in 8 + out 8) + zod schema (Plan/Memory/WorkflowTemplate per ADR-010/35/62) + Error code 11 처리 / 시퀀스 5 / Sprint 0~2 구현 체크리스트 / DC-FE-1~5 Drift 방지. **이후 사용자 검토 단계** (코드 작업 진입 전) |
| 2026-05-13 | **Phase A — v1.1 일괄 갱신** (사용자 통찰 "동료 화면 + 채팅 지시" 반영). 60 v1.1 (Layout 패턴 + 데이터 source 반영) / 61 v1.1 (§2 Routing 14 라우트 + GlobalLayout 패턴 + SideChatPanel v2 확장) / 62 v1.1 (3-Panel 제거, /workflow 라우트 Outlet) / 63 v1.1 (Mock API 12 endpoint 추가). **66 v1.0 신규** — v1 → v2 마이그레이션 가이드 (11 페이지 + 15 slice 매핑 + Sprint 우선순위 + Redux→Zustand 변환 패턴). data/mock/mock_data_description.md 280줄 보강 (KPI/Enum/FK/AI 5축/API 매핑) |
| 2026-05-15 | **15 End-to-End Flow v1.0 신규** — Phase 1 통합 직후 신규 입사자 first-read 문서. Mermaid sequence (query→Cognitive→Planning→hitl→Execution loop(callback)→Response→complete, + 5 PauseBox 액션 분기) + 채널 카탈로그 (REST/WS Agent/WS HITL) + 데이터 source (mock CSV 12종) + Reading Order 표 (질문→spec 매핑 12종). spec 14(Agent 내부 통합) 와 짝 — 14 는 agent deep, 15 는 frontend↔data end-to-end |
| 2026-05-16 | **Stage 4 — ADR-011 ConnectionManager 채널 분리 문서 정합** (ws_contract 브랜치). `21_WEBSOCKET_PROTOCOL` v1.4 → v1.5 (§1.2 fan-out 키 `(user_id, channel)`, §1.3 MAX 정책 (user, channel) 별, §3.2 hitl 카탈로그 엄격 적용). `12_manager_layer` v1.3 → v1.4 (ConnectionManager API signature). 두 spec 의 옛 버전 = `legacy/` 백업. 13 active spec stale 링크 sed 일괄 갱신 (19 파일). ADR-011 `Proposed` (Stage 5 통과 후 Accepted). |
| 2026-05-16 | **ADR-012 Workflow Canvas W2 완료** (main 8 Stage TDD). `62_workflow_canvas_design` v1.0 → v1.1 (§2.5 확장형 폴더 + §5.4 paused 게이트 + §5.5 W2 컴포넌트 카탈로그 + §5.6 자연 동기화 + §7 W2 ✅). v1.0 = `legacy/` 백업. `features/workflow/` 4 layer (canvas/editing/library/palette) — 신규 9 파일 (editingStore + useWorkflowEditing + ContextMenu + PropertyPanel + EditToolbar + nodeTypes + 4 README). 5 active spec stale 링크 sed (60/61/63/66 + INDEX). 매 Stage 4종 회귀 (typecheck/build/vitest 22/22/sprint13+15 191/191). |
| 2026-05-18 | **42 Quick Navigation v1.0 신규** — 사용자 요청 "흩어진 spec/문서 진입점 한 곳에". CLAUDE.md 가볍게 유지 + 별도 spec 으로 분리. 자주 보는 spec 11 link + FAQ 25 매핑 + INDEX 7 매트릭스 + 디렉토리 한 페이지 지도. "어디 봐야 할지 모를 때" 진입. |
| 2026-05-18 | **41 Agent / Tool Change Hub v1.0 신규** — 40 의 빠른 시작 버전. 사용자 시나리오 "1 문서 + 참조 link 만으로 변경 작업 진입". §2 손대는 4 파일 + §3 5 시나리오 + §4 변경 종류별 영역 매트릭스 + §5 5 Phase 표준 절차 + §6 예시 (7→12 카테고리 33 툴 재구성) + §7 FAQ 6 + §8 참조 link 10. |
| 2026-05-18 | **40 Agent / Tool Lifecycle v1.0 신규** — 40대 (운영) 영역 첫 entry. OS 층 (4-Layer + Manager + base_tool/registry/helpers — 절대 X) vs 콘텐츠 층 (tools/*.py + catalog/*.yaml + team_catalog.yaml — 자유 교체) 경계 명시. 5 변경 시나리오 표준 절차 + 영향 분석 매트릭스 + 회귀 테스트 범위 + FAQ. "에이전트 다 지우고 새로 만들기" 질문의 단일 진실 소스. |
| 2026-05-18 | **17 Functions → I/O 종단 매핑 v1.0 신규** — agent_design (비전 narrative) + 31/32 (Tool spec) + tool/TOBE_MVP (Tool↔Data 매핑) + 코드 4 source 흡수. 5단계 (기능→에이전트→툴→데이터→I/O) 한 흐름. §5 I/O 메커니즘 신규 가치 — `_inject_prev_outputs` setdefault·`_` prefix·COMPLETED only·dict only 4 룰 + raise 권장 + pickle 금지 + mock fallback. 14(Layer 축) / 15(시간 축) / 17(계층 축) 자매 완성. 신규 Tool 종단 체크리스트 §7. |
| 2026-05-17 | **ADR-013 Workflow Canvas W2′ 완료** (main 8 Stage TDD). `62_workflow_canvas_design` v1.1 → v1.2 — §5.5 BatchedToolbar 추가 / §5.7 엣지/드래그 (nodesConnectable/Draggable 해제) / §5.8 cycleGuard DFS (target→source) + sonner / §5.9 issues UX (hitl_ack.issues → toast.warning) / §5.10 batched applyMode + pendingOps + applyAllPendingOps + 노드별 ✏/회색 배지 + turn 종료 시 reset / §7.2 W2′ Acceptance. 시각 편집 vs NL 편집 책임 분리 audit 정정 (TodoManager 모든 필드 vs plan_editor 일부). v1.1 = `legacy/` 백업. 신규 frontend 파일 2 (cycleGuard / BatchedToolbar). 4 active spec stale 링크 sed (60/61/63/66) + INDEX. 매 Stage 4종 회귀 (typecheck/build/vitest 40→56/sprint13+15 191/191). 백엔드 변경 0. |
| 2026-05-22 | **64 Frontend Visualization Design v1.0 신규** — 사용자 피드백 "프론트엔드가 너무 AI스럽다" 의 데이터 시각화 craft 축 대응. 시각화 디자인 원칙 P1~P8(제약 형태) + 팔레트 3안(권장 A) + 컴포넌트 방향 6종 + 페이지 레이아웃 분화 5종 + Phase 0~5 로드맵. 짝 분석 문서 = `docs/_claude/frontend/프론트엔드_시각화_고도화_분석_2026-05-22.md` (AI스러움 진단 11종 + 트렌드 조사 교과서/최근). 선행 `docs/reports/frontend_ai_look_analysis_2026-05-21`(스캐폴딩 축) 위에 craft 축으로 보강. 상태 = 계획(사용자 검토 대기). |
| 2026-05-22 | **64 — 퍼포먼스 마케팅 도메인 정합** (사용자 지시 "이건 퍼포먼스 마케팅이라 관련 정보에 맞춰야"). §2 퍼포먼스 마케팅 도메인 모델 신설(지표=인과 사슬·목표 대비·예산 페이싱·채널 역할·캠페인 위계). 원칙 P1~P8 → **P1~P9** — P1(지표를 시스템으로)·P2(목표)·P3(페이싱) = 도메인 원칙 신설. 컴포넌트에 MetricChainStrip·PacingWidget·ChannelComparison·FunnelChart(단계 CVR) 추가. 페이지를 Executive/Channel/Ops 역할별 레이아웃으로. 로드맵 Phase 2~4 를 사슬·목표선·페이싱·채널 small multiples 중심으로 재구성. 짝 분석 문서 v2 동반 개정 — §1 에 도메인 부적합 진단 L(목표 데이터 미사용)·M(예산 페이싱 평균化) 추가, §2·§3 을 Google/Meta Ads·MER·어트리뷰션 기준으로 재작성. `campaigns.csv`·`budget_allocation.csv` 로 도메인 주장 검증. |
| 2026-05-22 | **64 폐기 → `docs/reports/프론트엔드_대시보드_고도화_통합계획서_2026-05-22.md` 로 통합 이전.** 사용자 결정 — 프론트 3계획(데이터기반 대시보드 고도화·스타일 개선·시각화 논의)을 단일 실행 계획으로 합치고 위치를 `docs/reports/` 로. 64 의 내용(도메인 모델·원칙 P1~P9·팔레트·컴포넌트)은 통합계획서가 전부 흡수 + 2-트랙/3-레이어 구조 + 데이터 의존성순 A/B구간 로드맵으로 재구성. 60대 = 60/61/62/63/66. |
| 2026-05-18 | **데이터 description 신설** (`data/description/mock/` 6 분할). `data/mock/mock_data_description.md` (부분 부정확) 폐기 → 6 파일 (INDEX/SCHEMA/RELATIONSHIPS/API_MAPPING/UI_MAPPING/ROADMAP). 정정 12+ (Enum 분포 / 퍼널 5단계 / 감성점수 의미 / 자사 vs 경쟁사 / 카러셀 / monitoring·replace 등). Status 마커 5종 도입 (active/defined_empty/planned/deprecated/experimental). 3 사이클 검증 통과 (1차 즉흥 / 2차 체계 8 영역 / 3차 전수 + 회귀 191+56). 60/63/66 spec stale link 갱신. backend mock_data.py docstring 4 + description_url 정정. 짝 자취 (gitignored) = `docs/_claude/data/{audit, verification, for_tool_planning, TOBE_MVP/*}`. commits: 19a2aee/1dea781/9422bea/6ced7cc/a5140e7. |
| 2026-05-27 | **ADR-022 Accepted + Sprint 16 데이터 layer 분리**. 사용자 P1·P2·P3 원칙 (tool 순수 / data 별도 / client 동적) 구현 박제. 신규: `backend/app/data_sources/` (DataSource Repository) + `backend/app/workspace/` (Workspace ABC) + `/api/dashboard1/*` (20 endpoint, ?client= param) + `/api/admin/{catalog, clients}` (tool 65 카탈로그 dump) + frontend `features/dashboard1/` (12 파일) + `useDashboard1Data` + `useAdminCatalog` + TopBar 클라이언트 드롭다운. 46 tool DataSource DI 전환. 13 commits (ba242c7 ~ f7de6c4) + G1 cleaning tag 정리 (c450330) + G2 옛 보고서 outdated 마커 (38528a5) 누적. **spec 10 §7.7 + v1.9.1 / 30 §4·§7.5·7.6·7.7 + §9 / 32 §5.1 / 63 §2.3.1·§2.3.2 동반 갱신 완료**. |
| 2026-05-27 | **65 Dashboard Pages Specification v1.0 신규** — 5 v1 페이지 (Dashboard/Channel/Trend/Creative/Cost) + Dashboard1 (Sprint 16) 의 *표시·분석·tool 단일 진실 소스*. 4 PART 구조 (현 상태 박제 / 통합 매트릭스 / Tool 신설 로드맵 / 추후 구현). 21 분석 방법론 카탈로그 (M01~M21) + 61 도메인 tool 후보 (D1) + 사용자 5 Step 작업 흐름 + 6×2 조합 매트릭스 (N:M) + 데이터 폴더 의미 (raw=외부주입 / 나머지=tool산출) + 학습 루프·외부 API 추후 구현. ADR-022 + memory `project_tool_data_agent_separation` 정합. 5 페이지 보완 작업의 첫 referential. |
| 2026-05-27 | **ADR-023 + 65 §13.3 (5 주체 + Trigger 추상화)** — 사용자 7 라운드 토의 누적 흡수. ADR-023 신설 (5 주체: Agent / Direct API / **Maker / Runner / Validator** + Trigger 추상화 6 종 + DataSource 진화 + Shared/Session Workspace + 3 Maker × 3 위치). **Agent Maker = Skills 박제** (구현 추후 토의 — 사용자 결정). 65 spec §13.3 신규 (Mermaid 도식 + 주체별 책임 + Trigger + 진화 단계) + 62 spec §0.1 (Canvas = Maker 2) cross-link. 어휘 통일 (Pipeline/Step/Tool/Maker/Runner/Validator/Trigger) + 금지 단어 (chain/compose/fetcher). POC v1 진입 framing 완성. |
| 2026-05-27 | **68 Pipeline Catalog v1.0 신규 (Batch 1 완성)** — 사용자 결정 (Pipeline 경계 A: 시각화 1개 = Pipeline 1개 / DSL YAML / 단계별 batch) 반영. Pipeline DSL schema + 작성 컨벤션 (명명·step·trigger·validator·cache·owner). 52 시각화 × 52 pipeline 매핑표 + **Batch 1 = Dashboard1 21 pipeline 실제 YAML** (K01~K09·M01~M04·C01~C03·T01~T03·O01~O02). C02 = K02 cache 재사용 패턴 박제. Batch 2~6 (32 pipeline) = 후속 commit. ADR-023 + 65 §14.6 정합. POC v1 Phase 1 의 첫 referential. |
| 2026-06-04 | **37 Agent Language (PMAL) v1.0 신규** — cognitive↔planning inter-layer 계약(에이전트 언어)을 `_claude` 작업 자취에서 committed spec 으로 승격. 구조(operation authored × domain SET × metric open × dimensions + period/benchmark/filters/output, source 축 금지) + 레이어 헌장(NL-free·도메인-complete·카탈로그-free) + 카탈로그 조직=planning 테이블((metric,dim)→tool + default-source + no-tool degrade) + v0→v1 마이그레이션(operation→TaskType shim) + **진화 로드맵 v0~v3** + F2 차단 매핑. 현 상태 = v0(StructuredQuery) 배포 / v1(PMAL) 설계 수렴·구현 Phase B. 이번 세션 F2 게이트(`9a2371a`·`495d98e`)·Phase A client 분리(`32d8241`)·Q1 provenance(`7151cb7`)·A4-lite(`646c56e`) 위에 작성. |
| 2026-06-05 | **16 Layer Dependency Architecture v1.0 신규** — 물리 모듈 레이어 의존 방향의 단일 권위 박제(audit이 짚은 "없던 문서"). 6-agent workflow(`wf_d37097fe`) 전수 import 분석 → 직접 grep 검증 → 독립 적대적 에이전트 재검증. `api_v2→agent→tool→data` 하향 그래프 + 검증된 4 불변식(I1 data↛agent·I2 tool↛orchestration·I3 agent-data 순수·I4 stage DAG, 전부 grep 0건) + 위반 5(🔴 V1 core↔workflow_managers 순환[decorators.py:44,104 lazy-avoided] / 🟡 V2 ml_models→llm_manager infra 누수 / 🟢 V3 tool 순수성 스멜·V4 wm→planning·V5 response→cognitive) + tool 데이터 접근 규칙(BaseTool.fetch only, 예외=registry·collection) + 디렉터리→레이어 귀속표 + 재현 grep §7. 재검증이 V3(tools→llm_manager) framing 정정(하드 위반 아닌 스멜). 후속: spec 10 §7.7.2 폐기 DI 예시 교체·카운트 정정, ADR-029 `normalizers/` 부재 박제. |
| 2026-06-11 | **18 Engineering Disciplines + 39 Query Categories & Routing v1.0 신규 + 37 PMAL v1.1 갱신** — 2026-06-10~11 세션(분석 사다리 완성 + Q&A·의사결정 카테고리 신설 + 복합쿼리 stage-2 진단) 흡수. **18**: 4 엔지니어링 축(하네스=8gate/프롬프트/컨텍스트=4-Layer/tool 구현) + 게이트 두 종류 + stage-2 근원귀속(워크플로우 6추적+적대검증 → 프롬프트>하네스>>tool, 데이터 건강, cycle/cognitive 오진 2건 기각). **39**: 4 카테고리 + operation→tool 배선(intent_shim + short-circuit 단일의도 한정) + 카테고리→agent 표 + 복합쿼리 현황. **37 v1.1**: diagnose/forecast/attribute 가 degrade→실 tool(diagnoser/forecaster/insight_extractor), recommend·factual_lookup 추가, sub_intents R2 미배선 박제. 짝 자취 = `_claude/4layer_system/{18_근원귀속·stage2_readiness·세션마무리}_260611` + `{분석레이어·질의응답·의사결정}_설계서_260610`. 코드 커밋 fda4490·872cefe·b02f3eb·2f4c03a·71f0f6d·a2e17ee·9050096. |
| 2026-06-09 | **38 외부 API 수집→회사 DB 저장 아키텍처 v1.0 신규** — 사용자 질문("external API→회사 DB 저장 의도가 코드에 덜 반영된 듯, 문서 있나?") 대응. 30대(데이터) 영역, 38(35 DB schema·36 mock raw·37 PMAL 옆). 3-agent workflow(`wf_c960b7b0`) = 기존 문서 인벤토리 + as-built 코드 매핑 + 적대적 검증. 결론: 아키텍처는 **이미 분산 문서(ADR-022/027/028·수집설계노트·33·35·36)에 부분 존재** → 38 = 통합 hub + as-built 정밀 박제 + MVP 방향. ★검증 정정: 레지스트리 ext16+int14=30 vs collector 13+8=21(차이 9 = collector 없는 소스), external 3 orphan(reviews·keyword_performance·daily_performance = external 분류인데 mock_api·collector 둘 다 부재) 식별. mock_api 는 런타임 external 수집기만 읽고 seed 에서 제외(`EXCLUDE`) 재확인. |
