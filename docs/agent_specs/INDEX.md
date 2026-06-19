# agent_specs/ INDEX

> DreamAgent V2 개발 명세서 맵.
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
| **16** | **[16_layer_dependency_architecture_v1.0.md](16_layer_dependency_architecture_v1.0.md)** | **⭐ 물리 모듈 레이어 의존 구조 — `api→agent→tool→data` 하향 그래프 + 검증된 4 불변식(grep 0건: data↛agent, tool↛orchestration, agent-data 순수, stage DAG) + tool 데이터 접근 규칙(BaseTool.fetch only). 디렉터리→레이어 귀속표. file:line 근거 + 독립 적대적 재검증. 의존-방향 단일 권위 (2026-06-05)** |
| **17** | **[17_functions_to_io_v1.0.md](17_functions_to_io_v1.0.md)** | **🔗 종단 매핑 — 도메인 기능 → 에이전트 → 툴 → 데이터 → I/O 메커니즘 5 룰 한 흐름. 14(Layer 축) / 15(시간 축) 와 자매 = 17(계층 축). §5 가 신규 — `_inject_prev_outputs` setdefault·`_` prefix·COMPLETED·dict 룰 + raise vs error + pickle 금지 + mock fallback. 신규 Tool 종단 체크리스트 §7 (2026-05-18)** |
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
| **30** | **[30_DATA_MODELS_v1.1.md](30_DATA_MODELS_v1.1.md)** | **★ Pydantic 모델 / Core Enum / HITL 모델 + 코드 참조 매핑 — v1.1 검증 정정판 (2026-05-15).** |
| *34* | *(예정) 34_prompt_catalog_v1.0.md* | LLM 프롬프트 (`llm_manager/prompts/*.yaml`) 단계별 매핑 |
| **35** | **[35_DB_SCHEMA_v1.0.md](35_DB_SCHEMA_v1.0.md)** | **PostgreSQL DB Schema — ERD (LangGraph + memory_entries) + 의미적 hierarchy (User/Conversation/Turn) + 8 memory type + content JSONB schema + 자주 쓰는 query (E2-5 conversation list 등) + 향후 확장 (Sprint 14 A3 / Sprint 15 P0 baseline)** |
| **37** | **[37_agent_language_pmal_v1.0.md](37_agent_language_pmal_v1.0.md)** | **⭐ Agent Language (PMAL) — cognitive 출력 = planning 입력 inter-layer 계약 (에이전트 언어). 구조 (`intent: operation(authored)×domain(SET)×metric(open)×dimensions` + period/benchmark/filters/output, **source 축 금지**) + 레이어 헌장 (NL-free·도메인-complete·카탈로그-free) + v0→v1 마이그레이션 (operation→TaskType shim, diagnose/forecast/attribute 제외) + **진화 로드맵 (v0 닫힌enum → v1 PMAL 열린어휘 → v2 사용학습 → v3 skill참조)** + F2 차단 매핑. 2026-06-04** |
| 🎨 | **[erd_database.md](erd_database.md)** | **ERD 시각화 모음 — Mermaid 7 view: Database ERD / 의미적 hierarchy / 데이터 흐름 (read·write·clarification) / Memory type 분류 / Sprint timeline / E2-5 sidebar / H0 자동 해결. 35 spec 의 시각화 보조** (에이전트 DB — 도메인 데이터 아님) |

### 40대 — 운영 (신규)

| 번호 | 문서 | 역할 |
|------|------|------|
| **40** | **[40_agent_tool_lifecycle_v1.0.md](40_agent_tool_lifecycle_v1.0.md)** | **🔄 교체·재구성·버전 변경 운영 가이드 — OS 층 vs 콘텐츠 층 경계 명시 (§1) + 5 변경 시나리오 표준 절차 (Tool 추가/폐기/에이전트 재구성/데이터 source/v2 메이저) + 영향 분석 매트릭스 + 회귀 테스트 범위 + FAQ. "지금 만들어진 에이전트 다 지우고 새로" 같은 질문의 단일 진실 소스 (2026-05-18 신규)** |
| **41** | **[41_agent_tool_change_hub_v1.0.md](41_agent_tool_change_hub_v1.0.md)** | **🚪 Agent/Tool 변경 작업 — 단일 진입점 (Change Hub) — 40 의 빠른 시작 버전. §2 손대는 4 파일 매트릭스 + §3 5 시나리오 + §4 변경 종류별 영역 매트릭스 + §5 표준 5 Phase + §6 예시 ("7→12 카테고리 33 툴 재구성") + §8 핵심 참조 link 10. 변경 작업 시 첫 번째 봐야 할 문서 — 1 문서 + 참조 link 만으로 작업 진입 (2026-05-18 신규)** |
| **42** | **[42_quick_navigation_v1.0.md](42_quick_navigation_v1.0.md)** | **🧭 Quick Navigation — 자주 묻는 질문 진입점. §1 자주 보는 spec 11 link + §2 FAQ 5 카테고리 25 매핑 (구조/변경/데이터/결정/로드맵) + §3 INDEX 7 매트릭스 + §4 디렉토리 한 페이지 지도. CLAUDE.md (가벼움 유지) 짝 — 필요 시 사용자가 진입. "어디 봐야 할지 모를 때" 첫 진입점 (2026-05-18 신규)** |
| **44** | **[44_concepts_data_transfer_v1.0.md](44_concepts_data_transfer_v1.0.md)** | **📖 데이터 전달 시대 개념 사전 — 2026-06-12~13 재설계 대화의 신개념 ~20개 (엔지니어링 4분류·판별 질문 / 장부·신분 3분류·누적 계약·멀티스코프 천장 / 계획된 블랙보드·버그의버그·계약-게이트 관계·보존 5 / 동사 규약·역할 설계 3단계·문서 생존 장치). 모든 정의에 출처 — 오너 기준 수립용. 기준서·계획서의 표준 어휘 (2026-06-13 신설)** |

### 60대 — 프론트엔드 (Sprint 15 신규)

| 번호 | 문서 | 역할 |
|------|------|------|
| **60** | **[60_frontend_overview_v1.0.md](60_frontend_overview_v1.0.md)** | **⭐ Frontend 진입점 — Vision H1~H4 매핑 + 5 UX 원칙 + Tech Stack 결정 (Vite + React 19 + TS + Tailwind v3.4 + shadcn/ui + Zustand + TanStack Query + @xyflow/react + dagre) + 7 Sprint roadmap (Sprint 0~6 + 7+) + W1~W4 Workflow Canvas Phase 매핑 + 학습 곡선 (~3주) + 보안/호환성/Risk. 60대 다른 문서들의 진입점** |
| **61** | **[61_frontend_architecture_v1.0.md](61_frontend_architecture_v1.0.md)** | **State (Zustand 7 store + TanStack Query) + Routing (15 라우트 + GlobalLayout + Workspace, 2026-06-01 갱신) + Component Inventory (shadcn/ui 15+ + features 폴더) + Design System (색상 토큰 라이트+다크+의미적 / Tailwind config / Pretendard / cn-cva 패턴) + v1→v2 마이그레이션 매트릭스** |
| **62** | **[62_workflow_canvas_design_v1.2.md](62_workflow_canvas_design_v1.2.md)** | **⭐ Workflow Canvas (React Flow) — vision H4 맞춤화 UI 핵심. 노드/엣지 schema + 자동 레이아웃 (dagre) + 인터랙션 (NL 편집 + 시각적 편집 공존) + Save/Load (memory_entries.type=workflow_template) + 4+1 Phase 로드맵 (W1~W4 + W2′) + **v1.2 (2026-05-17) ADR-013 W2′ 구현 완료** — §5.7 엣지/드래그 + §5.8 cycle 사전 차단 (DFS) + §5.9 issues UX (sonner toast) + §5.10 batched 모드 (applyMode + pendingOps + BatchedToolbar). 시각 편집 vs NL 편집 책임 분리 audit 정정 (TodoManager vs plan_editor)** |
| **63** | **[63_frontend_backend_contract_v1.0.md](63_frontend_backend_contract_v1.0.md)** | **Frontend ↔ Backend 계약 — REST API 매핑 + WS 2 채널 메시지 카탈로그 + zod schema (Plan/Memory/WorkflowTemplate) + Error code 11 처리 + 시퀀스 5 + 구현 체크리스트 + DC-FE-1~5 Drift 방지** |
| **64** | **[64_design_system_v1.0.md](64_design_system_v1.0.md)** | **Design System — 8 카테고리 (Color/Typography/Spacing/Radius/Motion/Elevation/Layout/Enforcement) 결정·이유·자취·메타룰 (MR1~MR6). 토큰 값은 `frontend/src/styles/*.md`, 본 spec 은 "왜·언제·자취"** |

> 참고: agent_specs 60대 가 정식 진실 소스.

---

## 🛠 사용/관리 규칙

### 참조 방향
- **코드 → 문서**: 코드 주석에 관련 문서 링크 (예: `# spec: docs/agent_specs/11_main_graph_state_v1.5.md`)
- **문서 → 코드**: 문서 "코드 참조" 섹션에 파일 경로 명기. 진실 소스는 항상 코드.

### 문서 추가 시 체크리스트
신규 매니저/모듈/이벤트 추가 시:
- [ ] 해당 영역 번호 내 다음 번호로 파일 작성 (12, 22 등)
- [ ] 이 INDEX.md에 행 추가
- [ ] `10_system_architecture_v1.9.md` §10 관련 명세서 표 갱신

### 버전 bump 정책
- **minor (v1.0 → v1.1)**: 내용 보강, 섹션 추가, 필드 설명 개선
- **major (v1.0 → v2.0)**: 구조/계약 breaking change (API 제거, 필드 rename)
- **파일명 동기화**: 내부 버전 bump 시 파일명도 함께 rename (`git mv`)

### Drift 방지
- Doc-Code Contract Test (Sprint 13 완료 직후 도입 예정) — 문서 내 코드 경로 자동 검증
- 각 문서 상단 "관련 명세" / "코드 위치" 섹션으로 단일 진실 소스 명시

---

## 변경 이력

> 프레임워크 추출(2026-06-19) 이전(마케팅 도메인 시기)의 상세 변경 이력은 git 히스토리를 참조하세요.
