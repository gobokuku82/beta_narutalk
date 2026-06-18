# Sprint 14 A3 — 수동 테스트 로그 (브라우저 regression)

| 항목 | 내용 |
|------|------|
| 시작일 | 2026-04-23 |
| 목적 | R-5~R-18 및 기존 regression 수동 검증 결과 누적 기록 |
| 형식 | 세션별 / 시나리오별 pass/fail + 발견 이슈 + 수정 커밋 SHA |
| 환경 | Windows 11, Chrome (버전 미기록), localhost:8001 |

---

## 세션 #1 — 2026-04-23 (도윤 + Claude)

### 환경
- 서버: `uv run python run_server_v2.py` (port 8001, PostgreSQL Checkpointer)
- 브라우저: Chrome
- 커밋 SHA 시작점: `48be097` (fallback 제거 refactor)

### 기존 regression (Sprint 13 + A1, 회귀 확인)

| ID | 시나리오 | 결과 | 비고 |
|----|---------|------|------|
| R-1 | 쿼리 → hitl → 승인 → 출력 | ✅ **PASS** | 정상 작동 |
| R-2 | 쿼리 → hitl → 거부 → 중단 | ✅ **PASS** | 정상 작동 |
| R-3 | 쿼리 → pause → 모달/메시지 → 중단/재개 | ✅ **PASS** | 정상 작동 |
| R-4 | 쿼리 → 승인 → 연속 pause/resume 반복 → 출력 | ✅ **PASS** | 여러번 토글 정상 |

### A3 신규 시나리오

| ID | 시나리오 | 결과 | 발견 이슈 |
|----|---------|------|----------|
| R-5 (v1) | Plan review → 🗑 삭제 | ❌ **FAIL** | "⚠️ 편집하려면 일시정지 상태가 필요합니다" — 편집 거부 |
| R-5 (v1) | Execution pause → 🗑 삭제 | ❌ **FAIL** | 동일 에러 |
| R-5 (v2 after 86e52a7) | Plan review → 🗑 | ❌ **FAIL** | 구조적 한계 (Sprint 13 query 경로는 `_pending_requests` 미사용) — 이슈 #8 |
| R-5 (v2 after 86e52a7) | **Execution pause → 🗑 → 성공** | ✅ **PASS** | Case 6 버그 수정 확인됨 — 이슈 #6/#7 해결 |
| R-6 (cascade 시각화 downstream 3+) | 미검증 | ⏳ | Case 5 결정 대기 후 진행 |

### 발견 & 수정 이력 (세션 #1)

| # | 이슈 | 커밋 | 상태 |
|---|------|------|------|
| 1 | 🗑 클릭 시 "session_id/todo_id 필수" 에러 (turn_id null 전송) | `602ce51` | ✅ 수정 |
| 2 | Pause 모달 재개 시 "⏱ 자동 종료됨" 오인 메시지 (ghost turn 필터 부재) | `602ce51` | ✅ 수정 |
| 3 | F5 경고 안 뜸 (브라우저 정책 제약) | `602ce51` | ⚠️ 제거 결정 (D4 B+ → B) |
| 4 | stale `_currentHitlTurnId` 오염 (fallback 체인 버그) | `0be1ff0` | ✅ 수정 |
| 5 | 서버·클라 turn_id 계약 일관화 (fallback 전수 제거) | `48be097` | ✅ 수정 |
| 6 | Execution pause 첫 클릭 시 편집 거부 (create_progress 초기 status 버그) | `86e52a7` | ✅ 수정 (v2 재검증 PASS) |
| 7 | (#6 과 동일 근본) | `86e52a7` | ✅ 해결 |
| **8** | **Plan review 단계 편집 구조적 한계** — Sprint 13 query 경로가 `_pending_requests` 미사용. Plan review 중 `_progress` 도 없음 → 편집 경로 단절 | **미결정** | 🟡 사용자 A/B/C 선택 대기 |

### 진단 중 이슈 #6/#7

**증상**: 두 케이스 모두 `TODO_EDIT_NOT_PAUSED` 반환 = "편집하려면 일시정지 상태가 필요합니다"

**가설 분석**:
- **Case 5 (Plan review)**: Sprint 13 query 경로 `_graph_runner_with_resume` 가 `hitl.create_request` 를 호출하지 않음 → `_pending_requests[turn_id]` 비어있음 → `get_pending_request` = None → 에러 분기
  - **구조적 한계 가능성**: Plan review 편집은 `Command(resume={"action":"modify", ...})` 경로로 해야 함 (pending_request 기반 아님)
- **Case 6 (Execution pause)**: `progress.status == "paused"` 조건 실패 가능성
  - `request_pause` → `progress.status = "paused"` 설정 확인됨
  - 혹은 session_id 매칭 실패

**다음 진단 단계 (사용자 협조 필요)**:
1. 브라우저 F12 **Console** 탭에서:
   - 🗑 클릭 후 `[hitl] ack:` 로그 공유
2. 브라우저 F12 **Network** 탭에서:
   - `/ws/hitl` WebSocket 메시지 확인 — `todo_delete` 전송 시 payload 의 `session_id` / `turn_id` 실제 값 공유
3. **서버 로그**: 편집 시도 시 `logger.warning` 이나 `logger.info` 출력 공유

---

## 템플릿 (세션 #2 이후 추가 시 사용)

```markdown
## 세션 #N — YYYY-MM-DD (작성자)

### 환경
- 커밋 SHA: ...
- 브라우저: ...

### 시나리오별 결과
| ID | 결과 | 비고 |
|----|------|------|
| R-X | ✅/❌ | ... |

### 발견 & 수정
| # | 이슈 | 커밋 | 상태 |
|---|------|------|------|
| X | ... | ... | ... |
```

---

## 세션 #2 — 2026-04-30 (도윤 + Claude) — Phase C-Unify (D 통일) 자동 테스트 검증

### 환경
- 커밋 SHA: `1e8f319` refactor(sprint14): A3 Phase C-Unify — planner.Plan 단일화 (ADR-010 Accepted)
- 직전: `e767845` (어댑터 B 옵션 시도 — 폐기) → D 직진
- 검증 범위: **자동 테스트만** (브라우저 R-16/17/18 은 다음 세션 사용자 협조)

### 자동 테스트 결과 — full suite

| 단계 | 결과 |
|------|------|
| TDD red (fixture 전환 후 plan_editor) | 6 fail (의도) |
| TDD green (plan_editor rewrite 후) | 10/10 PASS (D01~D10) |
| ws_hitl integration | 7/7 PASS (TE-E01~E07) |
| plan_review integration | 8/8 PASS (TE-H01~H08) |
| Sprint14 dir | **102 passed + 2 skipped** |
| Full suite | **239 passed + 2 skipped** (회귀 0, 어댑터 5 TC 삭제 보정) |

### 코드 레벨 R-16 fatal 해소 증명 (자동 테스트)

- TE-E07 `nl_remove_full_flow` PASS — `progress.plan` (planner.Plan dict) → `planner.Plan.model_validate` → `apply_edit` → `model_dump` 전 경로 무결
- TE-H04 `plan_review_todo_edit_nl_via_pause_branch` PASS — plan_review 단계 NL 편집 경로 통합 검증

### 브라우저 검증 (대기)

| ID | 시나리오 | 상태 |
|----|---------|------|
| R-16 | "4번 삭제" → ack accepted true + downstream tint | ⏳ 사용자 협조 대기 |
| R-17 | "3-4 순서 바꿔" → reorder | ⏳ |
| R-18 | "asdf xyz" → NL_INTENT_UNCLEAR | ⏳ |

### 발견 & 수정 이력 (세션 #2)

| # | 이슈 | 결과 |
|---|------|------|
| 9 | R-16 NL fatal — schema 불일치 (3 Plan / 2 Todo 클래스) | ✅ 해결 (D 통일) |
| 10 | 어댑터 B 옵션의 부채 위험 (v1/v2 섞임) | ✅ 해결 (D 직진으로 폐기) |
| 11 | PlanChange NL edit 경로에서 미사용 | ✅ 폐기 (approval.py 는 유지) |

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-23 | 세션 #1 — R-1~R-4 PASS, R-5 FAIL (이슈 #6/#7 진단 중) |
| v1.1 | 2026-04-30 | 세션 #2 — Phase C-Unify D 통일 자동 테스트 검증. 239 passed. R-16/17/18 브라우저 검증 대기 |
