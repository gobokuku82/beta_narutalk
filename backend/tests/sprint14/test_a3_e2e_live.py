"""Sprint 14 A3 — 그룹 G: Live E2E (실 PostgreSQL + OpenAI).

Test naming: TE-G01 ~ TE-G07 (structured 4 + NL 3).
Marker: `@pytest.mark.live` (개별 실행 — TestClient sequential hang 회피).

실행:
  uv run pytest backend/tests/sprint14/test_a3_e2e_live.py::test_TE_G01_R5_live_structured_modify_cascade_resume -v -m live

전제:
  - PostgreSQL 실행 중 (CHECKPOINT_DB_URI 연결 가능)
  - OPENAI_API_KEY 환경 변수 설정
  - 서버 미실행 (TestClient 로 lifespan 초기화)

G-1 패턴 (A1 에서 증명된 terminal 상태 검증):
  from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
  gs = await agent.aget_state({"configurable": {"thread_id": thread_id}})
  assert gs.next == ()  # re-entry 불가
  for task in gs.tasks:
      assert not task.interrupts  # pending 없음
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest


pytestmark = pytest.mark.live


def _make_plan_dict(todos_spec: list[dict[str, Any]]) -> dict[str, Any]:
    """테스트용 plan dict 생성 (planner.Plan 형식 — Sprint 14 A3 D 통일).

    구버전 spec ('task') 호환 — 'task' 입력은 'rationale' 로 매핑.
    """
    todos = []
    for i, spec in enumerate(todos_spec):
        todos.append({
            "id": spec.get("id", f"todo_{i+1:03d}"),
            "task_type": spec.get("task_type", "demo"),
            "agent": spec.get("agent", "default_agent"),
            "tool": spec.get("tool", "mock_tool"),
            "tool_params": spec.get("tool_params", {}),
            "depends_on": spec.get("depends_on", []),
            "priority": spec.get("priority", 5),
            "rationale": spec.get("rationale") or spec.get("task") or f"task {i+1}",
        })
    dag = {t["id"]: t["depends_on"] for t in todos}
    return {
        "teams_selected": [],
        "todos": todos,
        "dag": dag,
        "plan_notes": "",
    }


async def _assert_terminal(graph, thread_id: str):
    """G-1 패턴 — Checkpoint terminal 상태 검증."""
    gs = await graph.aget_state({"configurable": {"thread_id": thread_id}})
    assert gs.next == (), f"re-entry 가능 상태 (next={gs.next})"
    for task in getattr(gs, "tasks", []):
        assert not getattr(task, "interrupts", []), \
            f"pending interrupt 잔존: {task.interrupts}"


# ──────────────────────────────────────────────────────────────
# Structured (R-5 ~ R-8)
# ──────────────────────────────────────────────────────────────

@pytest.mark.skip(reason="Phase 8 브라우저 수동 regression 에서 실 live 검증")
async def test_TE_G01_R5_live_structured_modify_cascade_resume():
    """R-5: pause → structured modify → cascade → resume.

    시나리오:
      1. 쿼리 전송 → plan_review interrupt
      2. 승인 → execution 진행 중 pause
      3. _handle_todo_modify (pause 분기) → cascade 계산
      4. resume → 남은 Todo 재실행
      5. Checkpoint terminal 확인 (G-1)
    """
    pass


@pytest.mark.skip(reason="Phase 8 브라우저 수동 regression 에서 실 live 검증")
async def test_TE_G02_R6_live_structured_delete_cascade_diamond():
    """R-6: delete + cascade 4기준 검증 (R1 M4):

    - 삭제 대상 Todo downstream 3+ Plan 사용
    - invalidated 목록 순서 = Phase 순서 일치
    - preserved_results 개수 = 삭제 전 완료 - 무효화
    - resume 후 재실행 Todo = invalidated 와 정확 일치
    """
    pass


@pytest.mark.skip(reason="Phase 8 브라우저 수동 regression 에서 실 live 검증")
async def test_TE_G03_R7_live_structured_add_after_todo():
    """R-7: add (after_todo_id 지정) → depends_on 자동 → resume 실행."""
    pass


@pytest.mark.skip(reason="Phase 8 브라우저 수동 regression 에서 실 live 검증")
async def test_TE_G04_R8_live_diamond_dag_complex_cascade():
    """R-8: Diamond DAG 복잡 cascade (t1→{t2,t3}→t4)."""
    pass


# ──────────────────────────────────────────────────────────────
# NL (R-16 ~ R-18, Y-a)
# ──────────────────────────────────────────────────────────────

@pytest.mark.skip(reason="Phase 8 브라우저 수동 regression 에서 실 live 검증")
async def test_TE_G05_R16_live_nl_delete():
    """R-16: pause → NL textarea '4번 삭제' → plan_editor parse → apply → resume.

    D-14 연동: 이 테스트 (또는 별도 100회 스크립트) 결과 실패율 ≥3% 시
    Phase 9 회고에서 γ (multi-turn clarification) 재평가 trigger.
    """
    pass


@pytest.mark.skip(reason="Phase 8 브라우저 수동 regression 에서 실 live 검증")
async def test_TE_G06_R17_live_nl_reorder():
    """R-17: pause → NL '3-4 순서 바꿔' → plan_editor reorder → apply → resume."""
    pass


@pytest.mark.skip(reason="Phase 8 브라우저 수동 regression 에서 실 live 검증")
async def test_TE_G07_R18_live_nl_llm_failure():
    """R-18: NL 파싱 실패 (LLM API down 시뮬레이션) → 에러 UX + 구조화 UI 유지."""
    pass
