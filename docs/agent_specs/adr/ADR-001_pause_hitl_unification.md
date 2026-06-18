# ADR-001: hitl/pause 개념 통합 (Plan review 편집 경로 일원화)

## Status

Accepted (2026-04-27)

## Context

Sprint 14 A3 Phase 1~4 구현 완료 후 브라우저 검증 (R-5) 에서 **Plan review 단계의 Todo 편집이 항상 실패** 함을 발견. 원인은 두 경로의 분리된 상태 저장소:

| 경로 | 사용 저장소 | 편집 가드 조건 |
|------|------------|---------------|
| Sprint 12 legacy `_run_agent` | `_pending_requests[turn_id]` | `pending_request != None` |
| Sprint 13 query `_graph_runner_with_resume` | `_progress[turn_id]` | `progress.status == "paused"` |

문제: Sprint 13 query 경로는 `_pending_requests` 를 채우지 않고, `_progress` 는 execution_stage 진입 후에만 생성됨. 따라서 plan_review interrupt 시점에는 두 저장소 모두 비어있어 ws_hitl 의 `_handle_todo_*` 모든 분기가 실패.

사용자가 2026-04-23 에 5항목 요구사항 제시:

> 1. ws_agent / ws_hitl 두 통로. pause / hitl 모두 여기 사용. **pause = hitl = interrupt 같은 선상**
> 2. hitl_manager 가 hitl/pause 모두 관리
> 3. todo_manager 가 todo 관리. hitl/pause 상태에서 어떻게 todo 관리할지 명확히
> 4. **hitl/pause 는 같은 개념** — 사용자가 개입해 작업계획을 승인/수정/재개. 자연어 가능. 단순 작업 (순서 변경, 삭제) 간단히. UI 체계는 완벽
> 5. 기존 구조와 사용자 의도의 gap 작음. 타이밍·구조·연결만 맞추면 됨

이 요구사항은 단순한 버그 수정이 아니라 **두 interrupt 타입 (plan_review, execution_pause) 을 사용자 경험·내부 구현 모두에서 동일 개념으로 다루겠다** 는 방향성 결정.

## Decision

**Plan review 와 Execution pause 를 단일 편집 경로로 통합** 한다.

### 핵심 변경 (ADR 결정 = "옵션 1 — 임시 progress 생성")

1. **타이밍 변경**: ws_agent 의 plan_review interrupt 분기에서 **임시 `_progress` 생성** + `status="paused"` 직접 세팅. 기존엔 execution_stage 진입 후에만 생성됨.
2. **구조 변경**: ws_hitl 의 `_handle_todo_modify/delete` 에서 plan_review 분기 (pending_request 기반) 제거 → pause 분기 단일 경로.
3. **연결 변경**: `_handle_hitl_response` 의 approve 처리 시 `progress` 가 존재하면 (= plan_review 임시 progress 가 있다는 뜻) `{action:"modify", value:progress.plan}` 으로 변환해 signal_resume. 그러면 `planning_stage.py:88-92` 의 modify 분기가 edited plan 으로 교체.
4. **수명주기 변경**: `cleanup_turn` 에 `_progress.pop(turn_id, None)` 추가 (임시 progress leak 방지).

### 클라이언트 계약 (불변)

- 클라는 여전히 `{type:"hitl_response", data:{action:"approve"}}` 전송. 서버 내부에서 modify 변환은 transparent.
- UI 도 변경 없음 (사용자 §4 P3 "UI 체계 완벽" 준수).

### 코드 변경량

- 백엔드 +50줄 / -120줄 (net -70)
- UI 0줄
- 테스트 +200줄 (Group H 8건 신규)

## Consequences

### 좋은 점

- **사용자 의도 §4 직접 반영**: hitl/pause 가 코드 레벨에서도 같은 개념. 분기 없음
- **dead code 제거**: pending_request 기반 plan_review 분기 (~40줄 × 2 핸들러) 삭제
- **NL 편집 plan_review 도 가능**: `_handle_todo_edit_nl` 도 동일 pause 분기를 통과 → plan_review 단계에서도 자연어 편집 동작
- **테스트 단순화**: 한 경로만 테스트하면 됨

### 나쁜 점 / 비용

- **임시 progress 라는 추가 개념**: "execution 진입 전인데 progress 가 있다" 는 정신 모델 변화. walkthrough/문서로 보완
- **status 강제 세팅**: `create_progress()` 가 `_paused` 체크로 status 결정하는데 plan_review 시점엔 _paused 가 없어 default "running" 으로 만들어짐 → 명시 override (`temp.status = "paused"`) 필요. 우회 코드 1줄
- **cleanup 에 의존**: `_progress.pop` 누락 시 leak. cleanup_turn 에 추가 (Phase 5)

### 위험

- **execution_stage 가 임시 progress 재사용 시 phases 정합성**: handle_todo_edit/delete/add 가 phases 재구성하므로 일치. reorder 등 미래 추가 시 점검 필요
- **Sprint 12 legacy 경로 영향**: legacy `_run_agent` 는 변경 #1 가 적용되지 않음 (다른 코드 경로). 현재 legacy 는 dead 라 무관 (ADR-005 별도)

## Alternatives Considered

### Alt-1. 클라이언트 누적 + 승인 시 일괄 전달 (옵션 2)

클라이언트가 편집을 로컬에 누적하다 승인 시 전체 plan 을 modify+value 로 전송.

- 장점: 백엔드 변경 거의 없음
- 단점:
  - NL 편집은 LLM 호출이 필요해 결국 서버 왕복 — 구조화/NL 경로 분리됨 (사용자 §4 일관성 깨짐)
  - 드래그 중 preview 와 최종 결과 분리
  - 사용자 의도 §4 "같은 경로" 위배
- **불채택**

### Alt-2. Plan review 편집 기능 제거 (옵션 3)

Plan review 모달에서 편집 버튼 hidden. Execution pause 시점에만 편집 가능.

- 장점: 변경량 최소
- 단점: 사용자 의도 §4 미충족. UX 후퇴
- **불채택**

### Alt-3. `_pending_requests` 를 query 경로에서도 채우기

Sprint 12 의 dual-track 을 유지하되 query 경로에서도 create_request 호출.

- 장점: 옛 분기 살아남
- 단점: 두 저장소 동기화 부담. 사용자 §5 "구조 단순화" 와 반대 방향
- **불채택**

## Related

- **사용자 요구사항**: 2026-04-23 5항목 (대화 기록)
- **상세 흐름 문서**: [`docs/_claude/sprint14_a3_edit_flow.md`](../../_claude/sprint14_a3_edit_flow.md) v1.1
- **구현 계획**: [`docs/_claude/sprint14_a3_implementation_plan.md`](../../_claude/sprint14_a3_implementation_plan.md) v1.0
- **Walkthrough**: [`docs/walkthroughs/sprint14_a3_walkthrough.md`](../../walkthroughs/sprint14_a3_walkthrough.md) §5~§7
- **요구사항 명세**: `01_requirements_v1.6.md` FR-12f
- **WebSocket 계약**: `21_WEBSOCKET_PROTOCOL_v1.5.md` §3.1 hitl_response 변환
- **Manager API**: `12_manager_layer_v1.4.md` §4.3
- **시퀀스 다이어그램**: `24_sequence_diagrams_v1.3.md` §8
- **구현 커밋**: `9ee24c2 feat(sprint14): A3 Phase 5 — Plan review 편집 통합`
- **테스트**: `backend/tests/sprint14/test_a3_plan_review_edit_integration.py` (TE-H01~H08)
- **관련 ADR**: ADR-003 (Manager 책임 분리), ADR-004 (WS 2채널) — 이 결정의 전제

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-27 | 초안 + Accepted. Sprint 14 A3 Phase 5 commit `9ee24c2` 로 구현 완료 |
