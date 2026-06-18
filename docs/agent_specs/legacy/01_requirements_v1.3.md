# Requirements Specification (POC / Sprint 13~14)

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 요구사항 정의 (Requirements) |
| 진행상태 | **Active** — POC / Sprint 13 완료 + Sprint 14 확장 |
| 버전 | **v1.3** |
| 최종 수정일 | 2026-04-22 |
| 관련 명세 | `10_system_architecture_v1.8.md`, `13_lifecycle_v1.2.md`, `24_sequence_diagrams_v1.2.md`, `docs/_claude/sprint14_a1_hitl_timeout_plan.md` |

> 이 문서는 "무엇을 만들고 있는가 / 왜 이 범위인가"의 단일 기준. 
> **기능 세부는 설계 문서(10~30번대) 참조.** 여긴 "요구사항" 수준만.

---

## 1. 비즈니스 목표

**ADALLPIN Dream Agent V2** — 퍼포먼스 마케팅 운영 업무 자동화 AI 에이전트.

- **핵심 가치**: 광고 운영자가 자연어로 쿼리하면, Agent가 의도 분석 → 계획 수립 → 승인 후 실행 → 결과 요약.
- **POC 목표 (~Sprint 17)**: LLM 기반 4-Layer 파이프라인 + HITL + Checkpoint 복원 검증. 특정 브랜드 운영(블루밍글로우)에 국한.
- **MVP 기준**: Sprint 17+ — 인증 / 멀티 브랜드 / 실시간 대시보드 / PII.

## 2. 이해관계자 / 페르소나

| 역할 | 설명 | 주 사용 기능 |
|------|------|--------------|
| **마케터(Operator)** | 광고 운영 실무자. 자연어로 쿼리 입력 | 쿼리 입력, Plan 승인/거부, 실행 중 pause |
| **PM(Project Manager)** | 플랜 검토 / 실행 감시 | Plan 승인, Todo 편집(Sprint 14), Pause/Resume |
| **개발팀** | 프롬프트 / 규칙 / Agent 튜닝 | `logs/layer_guard.jsonl`, Checkpoint 조회 |

POC 단계에서 위 3역할은 사실상 **동일 사용자** (개발자 본인).

## 3. 기능 요구사항 (FR)

| ID | 요구사항 | Sprint | 상태 |
|----|---------|--------|------|
| FR-1 | 사용자 자연어 쿼리 입력 가능 (WebSocket) | 13 | ✅ |
| FR-2 | 과거 대화 이력 참조한 의도 재해석 (Cognitive) | 13 | ✅ |
| FR-3 | 팀/Todo 구조의 실행 계획 자동 수립 (Planning) | 13 | ✅ |
| FR-4 | Plan 승인/거부/수정 HITL | 13 | ✅ (수정은 Sprint 14 확장) |
| FR-5 | Todo DAG 병렬 실행 (Execution) | 13 | ✅ |
| FR-6 | 실행 중 사용자 Pause/Resume | 13 | ✅ (phase 경계) |
| FR-7 | 마크다운 형식 응답 생성 (Response) | 13 | ✅ |
| FR-8 | Layer 품질 가드 (빈 쿼리/빈 플랜/전부 실패 등) | 13 | ✅ |
| FR-9 | 서버 재시작 시 중단 Turn 복원 (Checkpoint) | 13 | ✅ (R-9 live 검증 2026-04-21) |
| FR-10 | 사용자당 동시 Turn 개수 제한 (default 3) | 13 | ✅ |
| FR-11 | 같은 user 다중 탭 브로드캐스트 (fan-out) | 13 | ✅ |
| FR-12 | Todo 편집 (추가/삭제/수정) HITL | 14 | ⏳ |
| **FR-13** | **HITL 응답 타임아웃 (pause/plan_review 공유)** | **14** | **✅** (2026-04-22) |
| FR-13a | timeout 시 `complete(aborted, reason=hitl_timeout)` emit + slot 해제 | 14 | ✅ (2026-04-22, HTL-01/02 실 Checkpoint 종결 증명) |
| FR-13b | timeout 이후 동일 turn_id 의 pause/resume/cancel/hitl_response 4종은 `turn_not_active` 로 거부 | 14 | ✅ (2026-04-22, Round 17 hitl_response 포함) |
| FR-14 | 대화 세션 저장/불러오기 (Memory) | 15 | ⏳ |

## 3.5 UX 요구사항 (UX)

사용자 경험 측면에서 만족해야 하는 기준. 코드 레벨 기능(FR)과 달리 대시보드·알림·상태 표시 등 **프런트/상호작용** 관점.

| ID | 요구사항 | Sprint | 상태 |
|----|---------|--------|------|
| UX-1 | 실행 상태 버튼 전이: idle → waiting → pause_available → resume_available | 13 | ✅ |
| UX-2 | 서버 재시작 후 재접속 시 미완료 Turn 자동 resume_query (last_turn_id 기반) | 13 | ✅ |
| UX-3 | auto-approve (plan_review 자동 승인) 경로에서도 Todo 리스트 렌더 | 13 | ✅ (R-10) |
| UX-4 | HITL timeout 발생 시 대시보드에 시스템 메시지 표시 ("자동 종료됨") + plan_review 모달 자동 close | 14 | ✅ (2026-04-22, R-13 live) |
| UX-5 | timeout 이후 늦은 HITL 요청 시 토스트 + idle 복귀 (turn_not_active ack 처리) | 14 | ✅ (2026-04-22, R-14 live) |
| UX-6 | (Sprint 15) 대화 사이드바에서 종료/중단 Turn 이어하기 — Memory 범위 | 15 | ⏳ |

## 4. 비기능 요구사항 (NFR)

| ID | 항목 | 목표 | 현재 |
|----|------|------|------|
| NFR-1 | 동시성 | user당 최대 3 Turn | `MAX_CONCURRENT_TURNS_PER_USER=3` |
| NFR-2 | WS 연결 | user당 최대 5 탭 | `MAX_WS_CONNECTIONS_PER_USER=5` |
| NFR-3 | 의도 해석 지연 | P95 < 5s (LLM 단독) | 미측정 (Sprint 16) |
| NFR-4 | Plan 승인 응답 | interrupt 후 즉시 (Queue 기반) | ✅ (I7) |
| NFR-5 | Pause 응답 한계 | phase 경계에서만 (부분 제약) | 문서화됨 (`13_lifecycle`) |
| NFR-6 | 신뢰성 | 서버 재시작 후 Turn 복원 | AsyncPostgresSaver |
| NFR-7 | 관찰성 (POC) | layer guard JSONL | `logs/layer_guard.jsonl` |
| NFR-8 | 확장성 | Sprint 17+ K8s 배포 준비 | out of scope (POC) |
| **NFR-9** | **HITL 응답 대기 기본값** | **30분 (1800s)** | `settings.HITL_RESUME_TIMEOUT_SEC` ✅ (Sprint 14 A1 완료) |
| **NFR-10** | **HITL 타임아웃 설정 방식** | **`.env HITL_RESUME_TIMEOUT_SEC=<초>` override** | ✅ pydantic `Field(ge=1)` validator (Sprint 14 A1 완료) |

## 5. 제약 / 범위

### In Scope (Sprint 13)
- 단일 브랜드 (블루밍글로우) 고정
- 단일 사용자 (`demo`)
- 로컬 PostgreSQL Checkpointer
- Plan 승인/거부 + Execution Pause/Resume 만
- 대시보드 (개발자용 HTML)

### In Scope (Sprint 14 확장)
- ✅ **A1 HITL 타임아웃 완료** (FR-13/13a/13b, NFR-9/10, UX-4/5) — 2026-04-22
- ⏳ A2 phase 내 pause 세밀화 (`should_continue` Todo 단위)
- ⏳ A3 Todo 편집 HITL (FR-12, add/delete/modify + Cascade)
- ⏳ A4 `team_catalog.yaml` `requires_approval` 확장
- ⏳ agent_specs 문서 확장 (Glossary / Runbook / Event Catalog 등)
- 🔒 **AgentState Reducer — 보류** (Tool 확장 이후 재평가. Plan 수립 중 writer 전수 조사 결과 실 다중 writer race 부재. 자산: `docs/_claude/sprint14_reducer_plan.md`)

### Out of Scope (Sprint 13~14)
- 인증/인가, PII, 멀티 브랜드/테넌트
- Prometheus/Grafana observability
- Memory / 대화 이력 DB 저장 (Sprint 15)
- timeout 이후 재개 UI — **Sprint 15 Memory 범위** (UX-6)
- 운영 배포, CI/CD, 로그 로테이션

## 6. 성공 기준 (Acceptance)

Sprint 13 기준:
- ✅ 비-live 테스트 **137/137 pass × 3회 안정** (R-9 resume_only 대응 RO-01~13, WQ-09~11 추가)
- ✅ Live 테스트 6/6 개별 pass (WL-01~06)
- ✅ 브라우저 수동 regression 전 항목 pass:
  - R-1 plan 승인 / R-2 reject / R-3 pause / R-4 resume (Sprint 12 기존)
  - **R-9 서버 재시작 복원** (2026-04-21 성공 — resume_query + Checkpoint 복원)
  - **R-10 plan_review auto-bypass** (2026-04-22 성공 — cognitive/planning 중 pause → auto-approve → paused 이벤트에서 Todo 리스트 복원 렌더)
  - **R-11 연속 pause/resume 3회 토글** (2026-04-22 성공 — CallbackManager dedup 검증)
  - **R-12 progress 유지** (R-9 restore_progress 로그 확인)

Sprint 14 A1 달성 (✅ 2026-04-22):
- [x] HITL timeout 유닛/통합 34건 pass (그룹 A~F)
- [x] Live 4건 pass (그룹 G HTL-01~04) — 실 Checkpoint 종결 증명
- [x] Sprint 13 regression 137/137 유지
- [x] Contract Test 5/5 pass
- [x] 브라우저 regression 3건 전수 pass:
  - **R-13** timeout 발생 → `complete(aborted, reason=hitl_timeout)` 수신 + 한글 시스템 메시지 + 모달 자동 close (UX-4)
  - **R-14** timeout 후 뒤늦은 HITL 요청 (pause/resume/cancel/hitl_response 4종) → `turn_not_active` ack + 토스트 (UX-5)
  - **R-15** timeout'd turn 에 resume_query 재진입 → `INVALID_MESSAGE` emit (G-10)

Sprint 14 A2~A4 대기 (⏳):
- [ ] A2 phase 내 pause 세밀화
- [ ] A3 Todo 편집 regression R-5~R-8 live (FR-12)
- [ ] A4 `requires_approval` Tool 확장

## 7. 이해 필요 용어 (요약)

| 용어 | 의미 |
|------|------|
| `conversation_id` | 대화 세션 (여러 Turn 묶음) |
| `turn_id` | 쿼리 1회 = 1 Turn. `thread_id = f"{conv}_{turn}"` |
| **Turn** | 쿼리→응답 1사이클 (복수 phase 실행 + HITL 포함 가능) |
| **Phase** | Plan DAG의 topological 단계. pause는 phase 경계에서 감지 |
| `interrupt()` | LangGraph 원시 — state를 Checkpoint 저장 후 astream 중단 |
| `Command(resume=...)` | interrupt 값 주입하며 재개 |
| **fan-out** | 같은 user의 모든 WS 탭에 브로드캐스트 (`broadcast_to_user`) |
| **direct-WS** | 수신 WS 한 곳에만 전송 (`_safe_send`) |
| **turn_not_active** | HITL 핸들러 거부 사유 — timeout/완료 등으로 활성 리스트에서 제거된 turn_id (Sprint 14) |

(상세 Glossary = *(예정) 50_glossary_v1.0.md* — Sprint 14 범위)

## 8. 참조

- 시스템 구조 → `10_system_architecture_v1.8.md`
- 라이프사이클 / 상태머신 → `13_lifecycle_v1.2.md`
- 시퀀스 다이어그램 → `24_sequence_diagrams_v1.2.md`
- API 계약 → `20_INTERFACE_CONTRACT_v1.1.md`, `21_WEBSOCKET_PROTOCOL_v1.2.md`
- Error 카탈로그 → `22_error_codes_v1.0.md`
- Sprint 14 계획 → `docs/_claude/sprint14_master_plan.md`, `sprint14_a1_hitl_timeout_plan.md`, `sprint14_reducer_plan.md`

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-21 | 초안 — FR 14, NFR 8, Sprint 13 완료 기준 + Sprint 14~15 확장 |
| v1.1 | 2026-04-21 | R-9 서버 재시작 복원 live 검증 완료. 테스트 누적 121 → 137 (RO/WQ resume_query 경로 16개 추가). Acceptance 목록 갱신 |
| v1.2 | 2026-04-22 | Sprint 14 착수 — FR-13 을 13/13a/13b 로 확장 (HITL timeout 상세화), §3.5 UX 섹션 신설 (UX-1~6), NFR-9/10 추가 (timeout 기본값·설정 방식), §5 In Scope 에 Sprint 14 블록 신설, §6 Acceptance 에 Sprint 14 추가 기준·R-13/R-14 regression 추가, §7 용어 `turn_not_active` 추가 |
| v1.3 | 2026-04-22 | Sprint 14 A1 완료 반영 — FR-13/13a/13b / NFR-9/10 / UX-4/5 상태 ⏳ → ✅. FR-13b 가드 4종 확장 (pause/resume/cancel/**hitl_response** — Round 17). UX-4 에 모달 자동 close 추가. In Scope 를 A1 완료 / A2~A4 대기 / Reducer 🔒 보류 로 구분. Acceptance 체크박스 완료 마킹 + **R-15** (resume_query INVALID_MESSAGE) 추가. 관련 커밋 `d2d14a9 ~ 851683c` (8건) + 완료 보고서 `docs/reports/sprint14_a1_completion_report.md` |
