# Sprint 14 A3 — Phase C-Unify 작업계획서 (옵션 B: planner.Plan 단일화)

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-30 |
| 결정 | 옵션 A (어댑터) → **옵션 B (D 통일 직진)** 으로 변경 |
| 사유 | 사용자 통찰 ("v1/v2 섞임 금지", "확장/변경 용이성") + 통일 비용 ~3~5h = 1 day 미만 |
| 대체 대상 | 직전 commit `e767845` (어댑터) — revert 후 D 통일 |
| 마스터 | [`sprint15_compact_recovery.md`](./sprint15_compact_recovery.md) |
| 후속 | ADR-010 단일 결정 (B 임시 단계 history only), Phase D~E 그대로 |

---

## 0. 본 문서의 역할

옵션 B (planner.Plan 단일화) 의 **모든 작업 카탈로그**. TDD 흐름 / 영향 범위 / 회귀 검증 plan.

---

## 1. 영향 범위 — 활성 모듈 grep 결과

### 1.1 변경 대상 (활성)

| 모듈 | 현재 의존 | D 통일 후 |
|------|----------|----------|
| [`hitl_manager/plan_editor.py`](../../backend/app/dream_agent/workflow_managers/hitl_manager/plan_editor.py) | `models.Plan / TodoItem / PlanChange` | `planner.Plan / PlannedTodo` + 간단 dict 변경 이력 |
| [`api_v2/ws_hitl.py`](../../backend/api_v2/ws_hitl.py) | 어댑터 (`plan_adapter`) | 어댑터 호출 제거 → `planner.Plan` 직접 |
| [`hitl_manager/plan_adapter.py`](../../backend/app/dream_agent/workflow_managers/hitl_manager/plan_adapter.py) | 신규 (어댑터) | **삭제** |
| [`scripts/a3_nl_success_rate.py`](../../backend/scripts/a3_nl_success_rate.py) | `models.Plan / TodoItem` | `planner.Plan / PlannedTodo` |

### 1.2 테스트 변경 대상

| 테스트 | 현재 | D 통일 후 |
|--------|------|----------|
| `test_a3_plan_editor_nl_unit.py` | `models.Plan / TodoItem` 픽스처 | `planner.Plan / PlannedTodo` |
| `test_a3_plan_review_edit_integration.py` | `models.Plan` mock | `planner.Plan` mock |
| `test_a3_plan_adapter_unit.py` | 어댑터 5 TC (이번 세션 신규) | **삭제** |
| `test_a3_ws_hitl_nl_integration.py` | (변경 X — PlanEditor mock) | (변경 X) |
| `test_a3_todo_manager_unit.py` | 이미 `planner.PlannedTodo` 사용 | 변경 X |

### 1.3 영향 없음 (검증 필요)

- `approval.py` — `PlanChange` 사용 (HITL 승인 별개 flow). NL edit 과 분리. **그대로 유지**
- `executor.py / execution_stage.py` — 이미 `planner.Plan` 사용 → **변경 X** (오히려 통일됨)
- `manager.py` — `HITLRequest/Response` 만 사용 → **영향 X**
- `tools/*` — `ExecutionContext/ToolSpec` 만 사용 → **영향 X**
- `_old_v1/*` — 비활성 (격리됨), `models.Plan / TodoItem` 사용 → **그대로 유지** (deprecated 영역)

### 1.4 models.Plan / TodoItem 처리 결정

활성 의존이 사라지므로:
- **선택 A**: 파일 유지 + deprecated 마커 (`_old_v1/` 호환)
- **선택 B**: 파일 삭제 (활성에서 사용 X 확인 후)

→ **선택 A 권고** — `_old_v1/` 가 격리되어 있긴 하나 import 시 ImportError 위험. deprecated 마커로 안전하게.

---

## 2. PlanChange 처리 결정

### 현재
- `plan_editor.apply_edit()` → `tuple[Plan, PlanChange]` 반환
- ws_hitl 에서 `change` 변수 받지만 **사용 X** (ack 에 미포함, 로깅에 미포함)
- `approval.py` 가 별도로 PlanChange 생성/사용 (NL edit 과 무관)

### D 통일 후 옵션
| 옵션 | 설명 | 비용 | 결정 |
|------|------|------|------|
| **B-1** | `apply_edit` 가 `planner.Plan` 만 반환 (PlanChange 폐기) | 0 | ⭐ 권고 (POC 단순) |
| B-2 | PlanChange 를 `planner` 모듈로 이동 | ~30min | 향후 이력 추적 시 |
| B-3 | PlanChange 를 dict 로 반환 | ~10min | 중도 |

→ **B-1 채택** — ws_hitl 미사용 + 사용자 통찰 ("초기는 LLM 많이 써도 됨 / 단순 우선") 부합. approval.py 의 PlanChange 는 그대로 (`models.plan` 에서 import 유지).

---

## 3. 작업 분해 — 6 sub-phase

### 3.1 의존성 그래프

```
CU-0 사전 (어댑터 commit revert OR 그대로 두고 진행) ⭐ 결정 필요
  ↓
CU-1 plan_editor.py rewrite (planner.Plan 기반) — TDD red→green
  ↓
CU-2 ws_hitl.py 어댑터 호출 제거 — 직접 dict ↔ planner.Plan 사용
  ↓
CU-3 어댑터 파일 + 테스트 삭제 (plan_adapter.py / test_a3_plan_adapter_unit.py)
  ↓
CU-4 기존 테스트 수정 (plan_editor_nl_unit / plan_review_edit_integration)
  ↓
CU-5 scripts/a3_nl_success_rate.py 수정
  ↓
CU-6 models.plan / models.todo deprecated 마킹 + ADR-010 본문 + 문서 update
```

### 3.2 시간 추정

| Sub-phase | 시간 | 누적 |
|-----------|------|------|
| CU-0 사전 | 5min | 5min |
| CU-1 plan_editor rewrite | 1.5h | 1.6h |
| CU-2 ws_hitl 변경 | 30min | 2.1h |
| CU-3 어댑터 삭제 | 5min | 2.2h |
| CU-4 기존 테스트 수정 | 30min | 2.7h |
| CU-5 scripts 수정 | 15min | 2.9h |
| CU-6 ADR + deprecated + 문서 | 45min | **~3.7h** |

**예상 총 ~3.5~4h** (당초 추정 ~3~5h 범위).

---

## 4. CU-0: 사전 결정 — 어댑터 commit revert?

### 옵션
| 옵션 | 흐름 | git history |
|------|------|------------|
| **revert 후 진행** | `git revert e767845` → 새로 D 통일 commit | 깨끗 (어댑터 시도 자취 남김) |
| **그대로 두고 진행** | 어댑터 위에 D 통일 commit (어댑터 파일 삭제 포함) | 시도→폐기 자취 명확 |

→ **"그대로 두고 진행" 권고**. 이유:
- 어댑터 commit 도 학습 자취 (TDD / 분석 흐름) 가치 있음
- revert 시 force push 부담 (이미 push 됐으면)
- D 통일 commit 메시지에 "어댑터 e767845 폐기 + D 단일화" 명시로 충분히 추적 가능

**확인 필요**: `git push` 했는지? — 안 했다면 revert 도 안전. 했다면 그대로 두고 진행.

---

## 5. CU-1: plan_editor.py rewrite (~1.5h)

### 5.1 새 시그니처

```python
# Before
async def apply_edit(self, plan: Plan, parsed: dict, user_instruction: str) -> tuple[Plan, PlanChange]:

# After
async def apply_edit(self, plan: planner.Plan, parsed: dict, user_instruction: str) -> planner.Plan:
```

### 5.2 변경 핵심

| 영역 | Before | After |
|------|--------|-------|
| Import | `models.Plan, PlanChange, TodoItem` | `planning.planner.Plan, PlannedTodo` |
| `parse_instruction(plan)` 시그니처 | `Plan` (models) | `Plan` (planner) |
| `apply_edit` action="add" 의 새 todo 생성 | `TodoItem(...)` | `PlannedTodo(...)` |
| `apply_edit` action="modify" | `todo.model_copy(update=...)` | 동일 (PlannedTodo 도 BaseModel) |
| `apply_edit` action="reorder/remove" | todo 리스트 조작 | 동일 |
| 반환 | `(new_plan, change)` | `new_plan` (PlanChange 폐기 — B-1) |
| `validate_edit` | (변경 X) | (변경 X — dict 기반) |
| `parse_instruction` 의 prompt 안 todo 라벨 | `t.task / t.tool / t.status` | `t.rationale or t.task_type / t.tool / "active"` (planner 에 status 없음 → "active" hardcode) |

### 5.3 TDD red→green

#### red 단계
1. `test_a3_plan_editor_nl_unit.py` 의 sample_plan fixture 를 `planner.Plan / PlannedTodo` 로 전환
2. `apply_edit` return 도 `new_plan` 만 받도록 수정 (`tuple` 언패킹 제거)
3. 자동 테스트 실행 → 기존 plan_editor 가 models.Plan 기대하므로 **fail**

#### green 단계
4. plan_editor.py rewrite — planner.Plan / PlannedTodo 사용
5. 다시 테스트 → PASS

### 5.4 Acceptance
- [ ] plan_editor.py 의 `models` 임포트 제거
- [ ] `planner.Plan / PlannedTodo` 사용
- [ ] `apply_edit` 시그니처: `tuple[Plan, PlanChange]` → `Plan`
- [ ] `parse_instruction` 의 todos_str 생성 시 planner 형식 (rationale / task_type) 사용
- [ ] D-13 sanitize / MAX_INSTRUCTION_LEN 보존
- [ ] 단위 테스트 PASS (수정된 D01~D10 10 TC)

---

## 6. CU-2: ws_hitl.py 어댑터 호출 제거 (~30min)

### 6.1 변경

```python
# Before (어댑터 적용 후 — e767845)
plan_pydantic = planner_dict_to_models_plan(progress.plan, session_id)
...
new_plan_pydantic, change = await editor.apply_edit(plan_pydantic, parsed, instruction)
new_plan_dict = models_plan_to_planner_dict(new_plan_pydantic)

# After (D 통일)
plan_pydantic = planner.Plan.model_validate(progress.plan)
...
new_plan_pydantic = await editor.apply_edit(plan_pydantic, parsed, instruction)  # change 제거
new_plan_dict = new_plan_pydantic.model_dump(mode="json")
```

### 6.2 Import 변경

```python
# Before
from app.dream_agent.workflow_managers.hitl_manager.plan_adapter import (
    models_plan_to_planner_dict,
    planner_dict_to_models_plan,
)
# After
from app.dream_agent.planning.planner import Plan as PlannerPlan
```

### 6.3 Acceptance
- [ ] 어댑터 import 제거
- [ ] `planner.Plan` 직접 사용
- [ ] `change` 변수 제거 (단일 반환)
- [ ] `_handle_todo_edit_nl` 의 docstring update (Pydantic Plan → planner.Plan)
- [ ] ws_hitl integration 테스트 (TE-E01~07) PASS

---

## 7. CU-3: 어댑터 파일 + 테스트 삭제 (~5min)

### 7.1 삭제 대상
- [ ] `backend/app/dream_agent/workflow_managers/hitl_manager/plan_adapter.py`
- [ ] `backend/tests/sprint14/test_a3_plan_adapter_unit.py`

### 7.2 검증
- [ ] grep 확인 — `plan_adapter` 참조 0
- [ ] 자동 테스트 collect — ImportError 0

---

## 8. CU-4: 기존 테스트 수정 (~30min)

### 8.1 `test_a3_plan_editor_nl_unit.py`

- `sample_plan` fixture: `Plan / TodoItem` → `planner.Plan / PlannedTodo`
- `t.task` → `t.rationale or t.task_type`
- `apply_edit` 반환 언패킹: `new_plan, change = ...` → `new_plan = ...`
- `change.change_type == "nl_edit"` 같은 어설션 → 제거 (PlanChange 폐기)

### 8.2 `test_a3_plan_review_edit_integration.py`

- `_FakeEditor.apply_edit` mock: `(plan, change)` → `plan`
- `models.Plan` import → `planner.Plan`

### 8.3 Acceptance
- [ ] 두 테스트 모두 PASS
- [ ] PlanChange 어설션 제거 (NL edit 경로에서)

---

## 9. CU-5: scripts/a3_nl_success_rate.py (~15min)

NL 성공률 측정 스크립트 — 개발 도구. 같은 패턴으로 `models.Plan / TodoItem` → `planner.Plan / PlannedTodo`.

### Acceptance
- [ ] import 변경
- [ ] sample plan 생성 코드 변경
- [ ] 스크립트 실행 검증 (--dry-run 같은 옵션 있으면)

---

## 10. CU-6: models 정리 + ADR-010 + 문서 (~45min)

### 10.1 models.plan / models.todo deprecated 마킹

각 파일 상단:
```python
"""DEPRECATED: Sprint 14 A3 D 통일 완료 (2026-04-30). _old_v1/ 호환을 위해 유지.
신규 코드는 planner.Plan / PlannedTodo 사용.
"""
```

### 10.2 ADR-010 본문 작성

[`docs/agent_specs/adr/ADR-010_plan_schema_unification.md`](../agent_specs/adr/) 신규.

핵심 변경 (옵션 B 직진 반영):
- **Status**: Accepted (2026-04-30) — Sprint 14 A3 D 단일화 완료
- **Decision**: planner.Plan 단일화 (어댑터 시도는 history)
- **Alternatives**: A models 통일 / B 어댑터 (시도 후 폐기) / C 단계적 / **D planner 단일화 ⭐**
- **Consequences**: schema 1개 / lifecycle metadata 부재 (POC 무해) / Sprint 16+ 확장 시 PlannedTodo 필드 추가

### 10.3 문서 update

- `sprint14_a3_test_log.md` 세션 #2 (D 통일 결과)
- `sprint15_compact_recovery.md` — Phase C 종결 표기 + 어댑터 → D 단일화 반영
- `sprint15_phase_c_nl_fix.md` — D 단일화 완료 표기 (어댑터 부분 history)
- `sprint15_phase_d_adr.md` — ADR-010 v2 부분 단순화 (D 단일 결정으로 수렴)
- `sprint14_a3_known_issues.md` — ISSUE-016 해결

### 10.4 Acceptance
- [ ] models.plan / models.todo deprecated 마커
- [ ] ADR-010 본문 (D 단일 결정)
- [ ] 4 문서 update

---

## 11. 검증 / 테스트 strategy

### 11.1 자동 테스트 (단계별)

```bash
# CU-1 후 — plan_editor 단독
uv run pytest tests/sprint14/test_a3_plan_editor_nl_unit.py -v

# CU-2 후 — ws_hitl integration
uv run pytest tests/sprint14/test_a3_ws_hitl_nl_integration.py tests/sprint14/test_a3_plan_review_edit_integration.py -v

# CU-3 후 — adapter 삭제 확인
uv run pytest tests/ --collect-only 2>&1 | grep -i adapter

# CU-4~5 후 — 인접 회귀
uv run pytest tests/sprint14/ -v

# 전체 회귀 (마지막)
uv run pytest tests/ -v --tb=short
```

**기대**: 단계별 모두 PASS. 마지막 244 → **239 passed + 2 skipped** (어댑터 5 TC 삭제 보정).

### 11.2 DC 검증 (계약 / 문서 일관성)

```bash
uv run pytest tests/test_doc_contracts.py -v
```

### 11.3 브라우저 검증 (옵션 — Phase C-2 와 동일)

R-16/17/18 시나리오. 사용자 협조 시 진행.

---

## 12. Risk + 완화

| Risk | 완화 |
|------|------|
| `planner.Plan` model_validator 가 `models.Plan` 보다 약함 (cycle 검증 누락 가능) | `validate_dag()` 함수가 별도 존재 — plan_editor.validate_edit 에서 호출 가능 |
| `PlannedTodo` 가 `frozen=False` (mutable) — 의도치 않은 변경 위험 | `model_copy(update=...)` 패턴 유지 (불변성 관행) |
| `PlanChange` 폐기로 향후 이력 추적 불가 | Sprint 15 메모리 시스템 (memory_entries) 가 더 강력한 이력 제공 |
| `_old_v1/` 의 `models.Plan` 사용이 import 깨짐 | deprecated 마커만 (파일 유지) → import 무사 |
| LLM prompt 의 todo 라벨 형식 변경 (rationale vs task) | A/B 비교 측정 (`a3_nl_success_rate.py`) 권고 |
| reorder 시 depends_on 검증 약함 | `validate_edit` 의 cycle check + DAG validation 보강 |

---

## 13. 완료 체크리스트

### CU-0
- [ ] git push 상태 확인 + revert 여부 결정 (기본: 그대로 두고 진행)

### CU-1 plan_editor rewrite
- [ ] `models` import 제거
- [ ] `planner.Plan / PlannedTodo` 사용
- [ ] `apply_edit` 단일 반환
- [ ] D01~D10 PASS

### CU-2 ws_hitl
- [ ] 어댑터 import 제거
- [ ] 직접 `planner.Plan` 사용
- [ ] TE-E01~07 PASS

### CU-3 어댑터 삭제
- [ ] `plan_adapter.py` 삭제
- [ ] `test_a3_plan_adapter_unit.py` 삭제

### CU-4 테스트 수정
- [ ] `test_a3_plan_editor_nl_unit.py` D01~D10 PASS
- [ ] `test_a3_plan_review_edit_integration.py` H01~H08 PASS

### CU-5 scripts
- [ ] `a3_nl_success_rate.py` import / fixture 변경

### CU-6 문서
- [ ] models.plan / models.todo deprecated 마커
- [ ] ADR-010 본문
- [ ] 4 문서 update

### 종합
- [ ] Full suite 239 passed + 2 skipped
- [ ] DC 검증 PASS
- [ ] commit (단일 또는 sub-phase 별)
- [ ] Sprint 14 A3 종결 선언

---

## 14. 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-30 | 초안 — 옵션 B (D 통일) 직진 결정. 영향 범위 / 6 sub-phase / TDD / 회귀 plan |
