# Architecture Decision Records (ADR) — INDEX

| 항목 | 내용 |
|------|------|
| 상위 | [`docs/agent_specs/INDEX.md`](../INDEX.md) |
| 도입 결정 | [ADR-000](./ADR-000_adr_process.md) — Sprint 14 A3 Phase 5 (2026-04-27) |
| 형식 | Michael Nygard 표준 (Status / Context / Decision / Consequences / Alternatives / Related) |

---

## 📋 ADR 목록

| # | 제목 | 상태 | 작성일 | 영향 범위 | 관련 |
|---|------|------|--------|----------|------|
| **000** | [ADR 도입 자체](./ADR-000_adr_process.md) | Accepted | 2026-04-27 | 메타 (프로세스) | — |
| **001** | [hitl/pause 개념 통합](./ADR-001_pause_hitl_unification.md) | Accepted | 2026-04-27 | hitl_manager + ws_agent + ws_hitl + planning_stage | 003, 004 (예정) |
| **002** | [NL 편집 점진 고도화 1·2·3차](./ADR-002_nl_edit_phased_roadmap.md) | Accepted | 2026-04-27 | plan_editor + ws_hitl | 001 |
| 003 | *(예정)* Manager 5 책임 분리 | — | — | — | 001 |
| 004 | *(예정)* WebSocket 2채널 (agent + hitl) | — | — | — | 001 |
| **005** | [Sprint 12 Legacy `_run_agent` 처리 정책](./ADR-005_legacy_run_agent_disposition.md) | Accepted | 2026-04-27 | ws_agent (legacy 경로) + `_old_v1/` 폴더 보존 정책 | 001, 007 |
| 006 | *(예정)* Walkthrough-First 패턴 | — | — | — | 000 |
| **007** | [session_id ↔ turn_id 네이밍 정책](./ADR-007_session_id_turn_id_naming.md) | Accepted | 2026-04-27 | AgentState + HITLManager + ws_hitl + dashboard | 005 |
| **010** | [Plan/Todo schema 통합 — `planner.Plan` 단일화](./ADR-010_plan_schema_unification.md) | Accepted | 2026-04-30 | plan_editor + ws_hitl + scripts + tests | 002, 015 |
| **011** | [ConnectionManager 채널 분리](./ADR-011_connection_channel_separation.md) | **Accepted** | 2026-05-16 | connection_manager + ws_agent + ws_hitl + spec 21 v1.5 + spec 12 v1.4 | 004 (예정) |
| **012** | [Workflow Canvas W2 — 확장형 구조 + paused 게이트](./ADR-012_workflow_canvas_w2_structure.md) | **Accepted** | 2026-05-16 | features/workflow/ 4 layer + spec 62 v1.1 + ws.ts 3 송신 | 010, 002 |
| **013** | [Workflow Canvas W2' — 엣지/드래그/batched + 시각 편집 gap 보강](./ADR-013_workflow_w2_prime_edge_drag_batched.md) | **Accepted** | 2026-05-17 | WorkflowCanvas onConnect/onEdgeClick/onNodeDragStop + cycleGuard + issues UX + editingStore.pendingOps + BatchedToolbar + spec 62 v1.2 | 012, 002 |
| **014** | [Tool 단일 책임 분리 패턴 (도메인별)](./ADR-014_tool_param_auto_detection.md) | **Accepted** (v2 2026-05-19) | 2026-05-19 | format_normalizer (ads 전용) + review_normalizer 신규 + team_catalog + 5 unit test + ADR-016 (D9) 패턴 일관 | 015, **016** |
| **015** | [Clarification 자동 판정 + Tool ValueError → HITL recovery](./ADR-015_clarification_hitl_recovery.md) | **Proposed** | 2026-05-19 | cognitive/prompts + executor + models/enums (HITL_WAITING) + frontend useWebSocket + 향후 모든 Tool fail-fast | 001, 002, 007, 014 (메모리 통합 부분은 별도 ADR 이연) |
| **016** | [10 에이전트 구조 — preprocessing 2분리 + 레포팅 2갈래 + PPT 별도](./ADR-016_ten_agent_structure.md) | **Accepted** | 2026-05-19 | team_catalog.yaml + task_agent_hints + execution_agent/agents 10 카드 + LLM Prompts stage2/3 (D9 + D13 Y 사후 박제) | 014, 010 |
| **017** | [Analysis Agent 도메인 분리 (광고/리뷰/검색)](./ADR-017_analysis_agent_domain_split.md) | **Proposed** | 2026-05-19 | analysis_agent → ads/review/search 3 분리 가능성. 9 Tool (POC-01~09) 도메인별 매핑. 카테고리 1 재설계 Phase 1 | 014, 016, 018, 019 |
| **018** | [channel_normalizing_agent 의미 — channel vs data](./ADR-018_channel_normalizing_agent_meaning.md) | **Proposed** | 2026-05-19 | agent rename (channel → data) 또는 review_normalizer 소속 이동. P1 시나리오 2 EXECUTION_ALL_FAILED 원인 | 014, 016, 017, 019 |
| **019** | [summary_generator 책임 영역 — review 전용 vs 다도메인](./ADR-019_summary_generator_responsibility.md) | **Proposed** | 2026-05-19 | cross-cutting Tool 의 도메인 처리 패턴. P1 시나리오 1 "분석 결과 비어있음" 원인. ADR-014 v2 패턴 vs cross-cutting 충돌 | 014, 016, 017, 018 |
| **020** | [Computed Metrics Layer — Tool 책임 영역 + 별도 계산 layer](./ADR-020_computed_metrics_layer.md) | **Proposed** | 2026-05-20 | 사용자 architectural insight 박제: 단순 계산은 Tool 영역 외. Frontend/backend metrics 모듈 + 07 plan 13→9 Tool 재정정. POC→MVP+ 진화 | **014**, 016, 017 |
| **022** | [DataSource / Workspace Layer 분리 — Tool ↔ Data 사이 "관절"](./ADR-022_data_source_workspace_layer_separation.md) | **Accepted** | 2026-05-27 | app/data_sources/ + app/workspace/ 신설 (dream_agent 형제) + 46 tool DataSource DI + ExecutionContext.client_id + /api/dashboard1 + multi-client (?client=) + spec 10/30/32/63 동반 갱신 | **014**, **020**, 017 |
| **023** | [Pipeline 5 주체 분리 + Trigger 추상화 + DataSource 진화](./ADR-023_pipeline_5_actors_and_trigger_abstraction.md) | **Accepted** | 2026-05-27 | 5 주체 (Agent / Direct API / **Maker / Runner / Validator**) + Trigger 추상화 (button/upload/cron/webhook/agent) + DataSource 진화 (POC FileDS+mock_source → MVP ApiDS+AuthManager) + Workspace 분리 (Shared / Session — agent 격리) + 3 Maker × 3 위치 매핑 (개발자/Canvas/Agent) + 어휘 통일 (Pipeline/Step/Tool/Maker/Runner/Validator/Trigger). Agent Maker = **Skills 박제** (구현 추후 토의). spec 62/65 동반 갱신 | **022**, 020 |
| **024** | [Iterative Spec Refinement — 작성-검증-수정 사이클의 작업 방법론](./ADR-024_iterative_spec_refinement.md) | **Accepted** | 2026-05-27 | 사용자 통찰 "작성-검증-수정 순환식" 박제. **5 검증** (V1 코드정합·V2 cross-ref·V3 사용자검토·V4 정답값·V5 영역침범X) + Stop 조건 + 사이클 횟수 권장 + V3 사용자 검토 게이트 *특수성* (자동화 불가). 기존 사례 (65 spec 4차·ADR-023 7 라운드·D1.6 검토 게이트) 박제. 검증 적용 결정 매트릭스 (작업 규모별 차등). POC v1 Phase 1 진입 *전* 본 사이클 적용 필수 | 모든 spec 작업 |
| **025** | [Pipeline Customization 3 Layer — 카테고리·툴·계산식 계층의 진화](./ADR-025_pipeline_customization_3_layer.md) | **Accepted** | 2026-05-28 | 사용자 통찰 "세부설정 = 카테고리 - 툴 - 툴 내부 계산식/데이터 수정" 박제. **3 Layer** (L1 카테고리 / L2 placeholder / L3 계산식·매핑) + **L3 의 3 진화** ((a) column_mapping / (b) YAML formula / (c) DSL safe-eval) + POC v1·v2·MVP 매트릭스. L3(a) = ADR-027 로 *POC v1 즉시 적용 정정* (변경 이력). L3(b) = Canvas 자유도. L3(c) = Agent Maker (Skills) 자연 정합 | **022**, **023**, **027**, **028**, 020, 62 |
| **026** | [Visualization-First Iterative Design Flow — 10 step 작업 방법론](./ADR-026_visualization_first_design_flow.md) | **Accepted** | 2026-05-28 | 사용자 통찰 "시각화 → 값 → 방법 → tool/pipeline → 필요 data → raw 검증 → 역방향 정합" 박제. **10 step** 정밀화 + step 6 (raw 검증) 의 3 분기 (PASS·WARN·FAIL) + ADR-024 V1~V5 매핑 + Loop 중단 (3회 회귀) + 적용 의무 매트릭스 + 기존 batch 평가 (1 모범 / 2·3 부분 위반 / 4·5 명백 위반). F 사이클 (Batch 6) = 첫 모범 사례. **mock raw = step 6 FAIL 시 *raw 자체 변경 가능* (POC 자유도)** | **024**, **027**, **028**, **029** |
| **027** | [Pipeline·Maker·DataSource·Tool·ml_model 5 주체 권한 분리](./ADR-027_five_actor_permission_separation.md) | **Accepted** | 2026-05-28 | 사용자 통찰 "권한 명확 + tool 다 만든다 + ml_model 파트만 mock" 박제. **5 주체** (Pipeline·Maker·DataSource·Tool·**ml_model**) 권한 매트릭스 + 호출 그래프 (단방향 + 6 금지 화살표) + **ml_model adapter** (ABC + DI + Mock·Llm·Production swap) + 표준 schema 위치 (`backend/app/schemas/`) + 추상 컬럼명 (Pydantic 필드명) + `normalizers/{client}.yaml` 클라이언트 매핑 + DC-PERM-1~6 test. **Tool 영구 production** / **ml_model 구현체만 swap** | **022** (책임 확장), **023** (직교), **025** (L3(a) 구체화), **028**, **029** |
| **028** | [Hardcode 금지 원칙 + raw data 4 분류 + LLM 분석 영역](./ADR-028_hardcode_prohibition_and_raw_classification.md) | **Accepted** | 2026-05-28 | 사용자 통찰 "hardcode 어디에서도 사용 X + raw 4 분류 + LLM 분석 활용" 박제. **Hardcode 3 분류** (A client 종속 금지 / B mock 표시 / C 상수 허용) + **raw 4 분류** (B1 진짜 / B2 mock {B2a 단순·**B2b ml_mock**} / B3 tool 산출 / B4 외부 산출 *명명 미정*) + **ml_mock 진화** (ADR-027 ml_model swap) + **LLM 분석 = LlmMlModel 구현체** (O05 추천 첫 모범) + 어휘 통일 | **022** (B3), **025** (L3(a)), **026** (step 6), **027** (ml_model), **029** |
| **029** | [폴더 명명 원칙 — 시스템 본질 + typical 정합 + 영역 명확](./ADR-029_folder_naming_principles.md) | **Accepted** | 2026-05-28 | 사용자 통찰 "db/models/schemas 와 본 시스템 관계?" 흡수. **3 명명 원칙** (P1 시스템 본질 + P2 typical 정합 + P3 영역 명확) + 본 시스템 폴더 결정 근거 표 + 신규 폴더 (`schemas/` + `normalizers/` + `ml_models/` + `data/ml_mock/`) + `dream_agent/models/` 예외 유지 (agent 전용) + 데이터 폴더 명명 + 신규 폴더 체크리스트. **메타 ADR — 다음 작업자 가이드** | **022**, **023**, **025**, **026**, **027**, **028** |
| **030** | [쿼리 카테고리 라우팅 아키텍처 — 분석 사다리 + Q&A·의사결정 신설](./ADR-030_query_category_routing_architecture.md) | **Accepted** | 2026-06-11 | 사용자 비전("결마다 다르게 처리") + stage-2 진단 흡수. **요청을 카테고리로 라우팅**(operation 선택자) + **분석 사다리**(탐색→진단→추론→예측, 깊은 3층 = LLMTool, 구 DEGRADE 해소) + **Q&A·의사결정 카테고리 신설**(ToolCategory += qa/decision, 결정론 short-circuit 단일의도 한정) + 단일 tool 부터(RAG·옵션·시뮬·승인 추후). 코드 커밋 fda4490·872cefe·b02f3eb·2f4c03a·71f0f6d·a2e17ee·9050096. spec 39(상세)·37 v1.1·18 동반 | **027**(ml_model), 37, 39, 18 |
| **032** | [normalized 피봇 영속화 결정 — 소스별 정형테이블·blended 레이어·활성주문 정의](./ADR-032_normalized_pivot_persistence_decisions.md) | **Accepted (잠정 — UX 재검토)** | 2026-06-17 | 피봇 기준점 점검(workflow wykcrn2iw) 후 결정 3건: **D1** 전용 relational writer(append/upsert·DROP 금지)+정형테이블 reserved 가드 / **D2** blended=Layer 4번째 / **D3** 활성주문=C계열 전체 제외(N00 입금전 포함 — 잠정). ⚠추후 UX 디자인 시 grain/컬럼/네이밍/order_status 대폭 수정 가능. translator 행 emitter 재작성이 후속 최대 작업 | **022**, **020**, **031**, scope memory |

---

## 🔍 검색 가이드

### 주제별

| 주제 | 관련 ADR |
|------|---------|
| **HITL / Pause / Interrupt** | 001, 015 (예정) |
| **자연어 편집** | 002, 015 (예정 — clarification) |
| **메모리 / 학습** | 015 (예정) |
| **Schema / Data Model** | 010 |
| **Legacy 코드 정리** | 005 |
| **네이밍 / 식별자** | 007 |
| **프로세스 / 메타** | 000, 006 (예정), **024** (Iterative Refinement) |
| **Manager Layer** | 003 (예정) |
| **WebSocket / 통신** | 004 (예정), **011** (채널 분리) |
| **워크플로우 캔버스** | **012** (W2 확장형 구조), **013** (W2' 엣지/드래그/batched) |
| **데이터 layer 분리 / 다중 client** | **022** (DataSource + Workspace 관절) |
| **Pipeline / Trigger / 5 주체** | **023** (5 주체 + Trigger 추상화 + Maker/Runner/Validator + SessionWorkspace) |
| **사용자 가변성 / Customization** | **025** (3 Layer L1·L2·L3 + L3 의 3 진화 단계) |
| **작업 방법론 / 작업 순서** | **024** (V1~V5 검증 사이클), **026** (Visualization-First 10 step) |
| **권한 분담 / 코드 책임** | **027** (5 주체 — Pipeline·Maker·DataSource·Tool·ml_model + ml_model adapter ABC) |
| **Hardcode 금지 / raw 분류 / ML·LLM 영역** | **028** (Hardcode 3 분류 + raw 4 분류 + ml_mock + LLM = LlmMlModel) |
| **폴더·파일 명명 원칙** | **029** (P1 시스템 본질 + P2 typical 정합 + P3 영역 명확) |
| **쿼리 카테고리 / 라우팅 / 분석 사다리 / Q&A·의사결정** | **030** (operation→카테고리 라우팅 + 사다리 + short-circuit) |

### 상태별

| 상태 | ADR 번호 | 의미 |
|------|---------|------|
| Accepted | 000, 001, 002, 005, 007, 010, **011**, **012**, **013**, **022**, **023**, **024**, **025**, **026**, **027**, **028**, **029**, **030** | 결정 완료, 적용됨 |
| Proposed | 015, 017, 018, 019, 020 | 015 = 본문 작성 대기 |
| Superseded | (현재 없음) | 다른 ADR 로 대체됨 |
| Deprecated | (현재 없음) | 폐기됨 |

### Sprint 별 발생

| Sprint | ADR |
|--------|-----|
| Sprint 14 A3 Phase 5 | 000, 001, 002, 005, 007 |
| Sprint 15 Phase C/D | 010 (Sprint 14 A3 어댑터 + Sprint 15 D 단일화), 015 (메모리 + Clarification + 자유 대화) |
| Sprint 16 (Data Layer Separation) | **022** (DataSource + Workspace 관절 + 다중 client), **023** (Pipeline 5 주체 + Trigger 추상화), **024** (Iterative Refinement 방법론), **025** (Customization 3 Layer), **026** (Visualization-First Design Flow), **027** (5 주체 권한 분리 + ml_model), **028** (Hardcode 금지 + raw 4 분류 + LLM), **029** (폴더 명명 원칙) |

---

## 📝 새 ADR 추가 가이드

### 언제 ADR 작성?

ADR-000 §"작성 트리거" 참조. 요약:
1. 두 가지 이상 옵션 중 한쪽 선택
2. API/메시지/스키마/저장소 구조 변경
3. 라이브러리/프레임워크/DB 큰 의존
4. 시스템 전반 정책 (eager vs lazy 등)
5. trade-off (A를 위해 B를 포기)

### 작성 절차

1. 다음 번호 확인 (이 INDEX 의 표 마지막)
2. 파일명: `ADR-NNN_snake_case_topic.md`
3. ADR-000 §"각 ADR 표준 형식" 따라 작성
4. **본 INDEX 의 표에 행 추가**
5. 필요 시 `docs/agent_specs/INDEX.md` 의 "사용/관리 규칙" 섹션 갱신

### 결정 변경 시

1. **본문은 절대 수정 안 함** (역사적 사실 기록)
2. 새 ADR 작성 (예: ADR-007)
3. 옛 ADR 의 Status 를 `Superseded by ADR-007` 으로 변경
4. 옛 ADR 의 Status 라인만 수정. 본문 변경 금지

---

## 📌 발견된 결정 누락 (ADR 작성 대기)

본 폴더 도입 시점 (2026-04-27) 기준 발견되었으나 아직 ADR 미작성인 결정 사항. 우선순위 순.

| 후보 | 상태 | 우선순위 |
|------|------|---------|
| ADR-003 Manager 5 책임 분리 (Connection / Concurrency / Callback / HITL / Todo) | 코드는 명확, 문서화 필요 | 중 — A3 마무리 후 |
| ADR-004 WebSocket 2 채널 분리 (agent + hitl) 이유 | 코드 명확, 문서화 필요 | 중 |
| ADR-006 Walkthrough-First 패턴 도입 | Sprint 14 회고 후 | 중 |
| ADR-008 Error 처리 통일 + ws_hitl error 코드 분리 + Layer guard logger | [`docs/_claude/sprint14_post_a3_cleanup_plan.md`](../../_claude/sprint14_post_a3_cleanup_plan.md) 작성됨 — 사용자 승인 후 ADR 격상 | 중 |
| ADR-009 LLM client timeout 설정 (현 무한 대기 가능) | 별도 결정 필요 — default 초/SDK 옵션 검토 | 높 |
| Plan review cascade UX 라벨 정책 (현 자동 숨김 vs data-mode 분기) | 브라우저 검증 결과 의존 | R-5 검증 후 |
| Pre-Sprint Discovery 단계 도입 여부 | 사용자 결정 대기 | Sprint 15 시작 전 |
| Doc Status 마커 (`Status: partial\|complete\|planned`) 적용 범위 | 미결정 (현재 일부 적용) | 중 |
| 구버전 archived 문서의 링크 정리 정책 (DC-4 잔여 10건) | (a) `POC_legacy/` 로 이동 (b) DC test 에서 archived 패턴 skip (c) 무시 | 낮 |
| Test skip 사유 추적성 (test_a3_race_unit.py F03/F05) | skip 이유에 추적 가능한 ticket/ADR 링크 도입 | 중 |
| Dashboard XSS audit (innerHTML 잔여 케이스 전수 점검) | innerHTML → textContent 전환 vs esc 보강 | 중 — Sprint 16+ |
| middleware/error_handler.py DEBUG mode stack trace 노출 | 환경 변수 분기 정책 | 낮 — POC OK, MVP 전 처리 |
| `cleanup_turn` race 의심 (timeout 중 wait_for_resume.get 진행 중 pop) | per-turn lock 도입 검토 | 낮 — 재현 어려움, 후속 |
| `cb_manager.unregister/register` 사이 race (R-9 resume_query 재진입) | 원자적 replace 메서드 도입 | 낮 |
| **ISSUE-001** ✅ Plan review 편집 후 메인 카드 stale (R-5 발견, R-7 임팩트 격상) | 2026-04-27 사용자 인사이트로 옵션 D 채택 — handleHitlAckTodo 에 renderTodoList 1줄 추가 (모달+메인 동시 갱신) | 해결 |
| **ISSUE-002** Cognitive LLM enum validation 실패 (robust prompting) | [known_issues.md](../../reports/sprint14_a3_known_issues.md) — A+B 조합 (prompt 보강 + fallback) 추천 | 높 |
| **ISSUE-004** Plan review 모달 헤더 메시지 stale (R-6 발견, 보류) | [known_issues.md](../../reports/sprint14_a3_known_issues.md) — 3줄 fix (handleHitlAckTodo 에 헤더 메시지 갱신 추가) | 낮 |
| **ISSUE-005** ✅ handle_todo_delete restart_from 누락 (R-6 발견) | 2026-04-27 1줄 fix 완료 + Group H TE-H02 검증 보강 | 해결 |
| **ISSUE-006** 도메인 의미적 검증 부재 (R-6 후속, 사용자 인사이트) | Level A Prevention 즉시 구현 (dashboard confirm 메시지 강화). Level B/C 는 ADR-002 NL 2·3차 진입 시 | Level A 해결, B/C 후속 |
| **ISSUE-007** ✅ handleHitlAckTodo 가 todo_add 후 모달 리스트 미갱신 (R-7 발견) | 2026-04-27 책임 분리 패턴 — handleHitlAckTodo 가 plan 갱신 + renderHitlTodoList. renderCascade 는 시각화만 | 해결 |
| **ISSUE-008** ✅ add_todo task_type 누락 → Plan validation fatal (R-7 재검증 발견) | 2026-04-27 1줄 fix — `setdefault("task_type", "custom")` + TE-A08b 신규 회귀 테스트 | 해결 |
| **ISSUE-009** tool 미지정 사용자 추가 todo execution 단계 SKIP (R-7 재재재검증 발견) | 현 상태 유지 — Sprint 15 Phase E-4 NL 2차 LLM Tool Routing 자연 해결 | 보류 → Phase E-4 |
| **🌟 종합 인사이트 — POC 1차 한계 측정** (R-5~R-7 누적) | ISSUE-006/008/009 모두 "사용자 도메인 지식 가정의 한계" 공유. ADR-002 NL 2차 진입 정당성 강화. memory `project_no_user_domain_assumption.md` 박제 | 박제 완료 |
| **ISSUE-010** plan_editor.modify 가 tool_params 미지원 (R-8 발견) | NL 2차 (Phase E-4 LLM Tool Routing) 진입 시 자연 해결 | 보류 → Phase E-4 |
| **ISSUE-011** pdf_renderer hallucination (catalog 부재, R-8 발견) | Phase E-4 catalog grounding 으로 자연 해결 | 보류 → Phase E-4 |
| **ISSUE-012** Cognitive 출력 parallelism 정보 없음 (R-8) | planning stage3 implicit grouping 으로 일부 보완. 정식 schema 강화는 Sprint 16+ | 보류 |
| **ISSUE-013** HITL request not found warning + ack accepted=false (동작 정상) | progress 일관성 — Phase E3/E4 ws_hitl 정리 시 묶음 | 보류 → Phase E |
| **ISSUE-014** Plan review UI list-only — DAG 시각화 0 (R-8 발견) | Sprint 16+ DAG 시각화 (별도 ADR) | 보류 → Sprint 16+ |
| **ISSUE-015** modify approve 시 planning 3-stage 재실행 (R-8/R-6 통합 로그) | Phase E3/E4 정리 시 묶음 | 보류 → Phase E |
| **ISSUE-016** ✅ NL path Pydantic Plan validation fatal (R-16 발견) | Phase C-1 B 어댑터로 즉시 해결. Sprint 15 D 단일화로 본질 해결 | Phase C-1 |
| **CAP-001** Clarification HITL trigger 부재 (사용자 요구 추가) | Phase E-3 + 메모리 통합 (ADR-015) — H0 자동 해결 | Phase E-3 |
| **TodoItem vs PlannedTodo** 두 모델 공존 → ADR-010 (작성 대기, Phase C-4 / D-2) | Sprint 14 A3 어댑터 임시 + Sprint 15 D planner.Plan 통일 결정 lock | ADR-010 ↑ 표 등재 |
| **메모리 + Clarification 통합** → ADR-015 (작성 대기, Phase D-1) | Q3 자료 9 영역 lock + Hybrid schema + Cognitive cascade + 5 항목 정책 | ADR-015 ↑ 표 등재 |

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-27 | 초안 — ADR-000/001/002/005 4건 등록 + 발견된 결정 누락 6건 트래킹 |
| 2026-04-29 | **Sprint 15 진입 갱신** — ADR-010 (Plan/Todo schema) + ADR-015 (메모리 + Clarification) 메인 표 등재 (Proposed). 결정 누락 표에 ISSUE-010~016 / CAP-001 추가 (Phase 매핑). 주제별 검색 + 상태별 + Sprint 별 모두 갱신 |
| 2026-05-15 | **ADR-011 등재 (Proposed, Stage 0)** — ConnectionManager 채널 분리. Phase 1 통합 직후 발견된 "답변 중복" 버그의 본질 해결. ws_contract 브랜치에서 5 Stage TDD 진행. spec 21 v1.4 → v1.5 동반. 5 Stage 통과 시 Accepted |
| 2026-05-16 | **ADR-011 Accepted** — 5 Stage 모두 통과 (RED 35건 → GREEN → 호출부 점진 + sprint13 172/172 회귀 → spec 21/12 정합 + INDEX sed → 사용자 E2E 검증). Stage 6 = 답변 순서 fix (assistant 메시지를 ChatTodoCard 위 → 아래로 재배치) 동반. ws_contract → main merge |
| 2026-05-16 | **ADR-012 등재 (Proposed, Stage 0)** — Workflow Canvas W2 시각적 편집. 폴더 4 layer 분리 (canvas/editing/library/palette) + paused 게이트 + 자연 동기화 (hitl_ack.plan 재활용). 백엔드 변경 0 (Sprint 14 A3 endpoint 활용). 8 Stage TDD main 직접 작업. Stage 7 통과 시 Accepted |
| 2026-05-16 | **ADR-012 Accepted** — 8 Stage 모두 통과 (폴더 리팩 → editingStore + Canvas 인터페이스 → ws 송신 3 + useWorkflowEditing → ContextMenu → PropertyPanel → EditToolbar + cascade + empty-state → spec 62 v1.1). 매 Stage 4종 회귀 (typecheck + build + vitest 22/22 + sprint13/15 191/191) 모두 통과. spec 62 v1.0 → legacy/ 백업, v1.1 = 현 권위 |
| 2026-05-17 | **ADR-013 등재 (Proposed, Stage 0)** — Workflow Canvas W2' 엣지 연결/끊기 + 노드 드래그 + batched 모드 + 시각 편집 gap 보강 (issues UX / tool_params 정책). 사용자 실사용 발견 + 3 고려사항 명시 대응. **Audit 정정**: 시각 편집은 plan_editor 가 아니라 TodoManager 가 처리 → 백엔드 변경 0. 8 Stage TDD main 직접. Stage 7 통과 시 Accepted |
| 2026-05-17 | **ADR-013 Accepted** — 8 Stage 모두 통과 (엣지 연결/끊기 → cycle DFS → 노드 드래그 debounce → issues UX → pendingOps + applyMode → BatchedToolbar + 시각화 + reset → spec 62 v1.2 + 본 문서). 매 Stage 4종 회귀 (typecheck + build + vitest 40→56 + sprint13/15 191/191) 통과. spec 62 v1.1 → legacy/ 백업, v1.2 = 현 권위. 신규 frontend 파일 2 (cycleGuard / BatchedToolbar). 4 active spec stale 링크 sed (60/61/63/66) + INDEX. 백엔드 변경 0. |
| 2026-05-27 | **ADR-022 등재 (Accepted)** — Sprint 16 데이터 layer 분리. `app/data_sources/` + `app/workspace/` 신설 (dream_agent 형제 — agent + 직접 API 공유). 46 tool DataSource DI 전환 + `ExecutionContext.client_id` + `/api/dashboard1/*` + multi-client (`?client=`). 13 commits (ba242c7 ~ f7de6c4) + G1 cleaning tag 정리 (c450330) 누적. spec 10/30/32/63 동반 갱신. **사용자 P1·P2·P3 원칙 박제** (memory `project_tool_data_agent_separation`). |
| 2026-05-27 | **ADR-023 등재 (Accepted)** — Pipeline 5 주체 + Trigger 추상화. 사용자 7 라운드 토의 누적 흡수 (Pipeline Runner / Maker / Fetch=DS / POC v1·v2 / Tool↔Data / Trigger / Agent sandbox + 위치). 5 주체 (Agent / Direct API / **Maker / Runner / Validator**), Trigger 추상화 (6 종 → 1 Pipeline), DataSource 진화 (FileDS+mock → ApiDS+Auth), Workspace 분리 (Shared / **Session — agent 격리**), 3 Maker × 3 위치 (개발자 ✅ POC v1 / Canvas ✅ POC v2 / **Agent ⏸️ Skills 박제 — 구현 추후 토의** 사용자 결정). 어휘 통일 + 금지 단어. ADR-022 정밀화. spec 62/65 동반 갱신. |
| 2026-05-28 | **ADR-024 등재 (Accepted, 2026-05-27 박제)** — Iterative Spec Refinement 방법론 (5 검증 V1~V5 + Stop 조건 + 사이클 횟수 권장 + V3 사용자 검토 게이트 자동화 불가 특수성). **ADR-025 등재 (Accepted)** — Pipeline Customization 3 Layer. 사용자 통찰 *"세부설정 = 카테고리·툴·툴내부 계산식 3 계층"* 흡수. L1 카테고리 / L2 placeholder (YAML inputs) / **L3 계산식·매핑** (현 코드 hardcode → 진화 (a) column_mapping → (b) YAML formula → (c) DSL safe-eval). L3(a) = MVP-2 외부 client 적응 블로커 (ADR-026 후보). L3(b) = Canvas 자유도 핵심. L3(c) = Agent Maker Skills 자연 정합. POC v1 영향 0 (framing 박제만). 어휘 통일 + 금지어 (config/param/calculation). 본 ADR = ADR-022·023 위 *사용자 가변성* 4 번째 차원. **ADR-024 V1·V2·V3 사이클 적용** (Phase 0.5 C 동반). |
| 2026-06-11 | **ADR-030 등재 (Accepted)** — 쿼리 카테고리 라우팅 아키텍처. 2026-06-10~11 세션(분석 사다리 완성 + Q&A·의사결정 카테고리 신설 + 복합쿼리 stage-2 진단·핀포인트) 결정 박제. 요청을 카테고리로 라우팅(operation 선택자) + 분석=인지 깊이 사다리(탐색→진단→추론→예측, 깊은 3층 LLMTool 로 구 DEGRADE 해소) + ToolCategory += qa/decision + 결정론 short-circuit(단일의도 한정, 복합은 Stage3). 단일 tool 부터(RAG·옵션·시뮬·승인 추후). spec 18(엔지니어링 축)·39(카테고리 상세)·37 v1.1 동반. 코드 커밋 7건(fda4490~9050096). |
| 2026-05-28 | **ADR-026·027·028·029 등재 (Accepted, 4 동시)** — 사용자 7 라운드 토의 누적 흡수 (시각화→역방향 정합 / Tool hardcode 위험 / 권한 명확 / db·models·schemas / ml_mock + LLM 분석 / tool은 production·ml_model만 swap). **ADR-026 Visualization-First Iterative Design Flow** — 10 step 작업 방법론 (step 6 raw 검증 = PASS·WARN·FAIL 3 분기 / Loop 중단 3회 회귀 / ADR-024 V1~V5 매핑). **ADR-027 5 주체 권한 분리** — Pipeline·Maker·DataSource·Tool·**ml_model** (DataSource 평행 layer) + ml_model adapter ABC + DI + 3 구현체 swap (Mock·Llm·Production) + `schemas/`·`normalizers/`·`ml_models/` 폴더 신설 + DC-PERM-1~6. **ADR-028 Hardcode 금지 + raw 4 분류 + LLM 영역** — Hardcode 3 분류 (A 금지·B 표시·C 허용) + raw 4 분류 (B1·B2{a/b ml_mock}·B3·B4 *명명 미정*) + ml_mock 진화 경로 + LLM = LlmMlModel. **ADR-029 폴더 명명 원칙** — P1 시스템 본질 + P2 typical 정합 + P3 영역 명확 + 결정 근거 표. **ADR-022·025 변경 이력 1줄 추가** (본문 변경 X, ADR-000 정합). Tool 영구 production / ml_model 만 swap 박제. POC v1 Phase 1 진입 *직전* framing 박제. |
| 2026-06-17 | **ADR-032 등재 (Accepted 잠정)** — normalized 피봇 영속화 결정. 기준점 점검(workflow wykcrn2iw, 5에이전트 적대감사)이 "테이블 사전생성=순서 틀림" 3 critical 적발 후, 오너 "권장대로+잘 기록(추후 UX 시 대폭 수정 가능)". D1 전용 relational writer(DROP 금지)+reserved 가드 / D2 blended=Layer 4번째 / D3 활성주문=C계열 전체 제외(N00 입금전 포함 잠정). translator 행 emitter 재작성=후속. ⚠ UX 디자인 재검토 시 Superseded. |
| 2026-06-12 | **ADR-031 등재 (Accepted)** — data 조회 pushdown 계약. 결정 5건: where 2연산자(텍스트 의미론) / 도메인 규칙=tool / 두 백엔드 같은답(교차 테스트 강제) / text2SQL 비채택 / **마커 생존=저장 계약(G28 — save→save_stream 라우팅)**. 관절 query·query_iter·aggregate 신설 + Postgres 행-테이블 SQL override(generic·typed 두 모양) + 시범 tool ga4_session_aggregator 전환 (PG 8.7s→2.8s 3.1×, File 피크 비역행). 마스터 [2] 완료 산출. |
