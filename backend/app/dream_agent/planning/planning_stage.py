"""Planning Stage — StructuredQuery → Plan(Todo[] + DAG) 매핑

4-Layer 파이프라인의 두 번째 단계. StructuredQuery.tasks와 AgentPool
카탈로그를 매핑하여 누가(Team/Agent) 무엇을(Tool) 어떤 순서로(DAG) 할지
결정한다.

개념 서브 단계:
  ⑥ plan_drafter   (큰 계획 — Task 레벨)
  ⑦ team_selector  (Team + Agent 구성)
  ⑧ todo_builder   (Tool + params + DAG)
  ⑨ plan_validator (구조/DAG/논리 검증)

Reference: docs/agent_specs/system_architecture_spec_v1.5.md §2.3
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END
from langgraph.types import Command, interrupt

from app.core.logging import get_logger
from app.dream_agent.planning.planner import Planner
from app.dream_agent.schemas.structured_query import StructuredQuery
from app.dream_agent.states.agent_state import AgentState

logger = get_logger(__name__)


async def planning_stage(state: AgentState) -> Command[Any]:
    """StructuredQuery → Plan 매핑.

    Args:
        state: AgentState (structured_query 읽음)

    Returns:
        Command(update={plan}, goto="execution")       — 정상
        Command(update={plan: empty}, goto="response") — tasks 비어있음 (skip)
        Command(update={error}, goto=END)              — 실패
    """
    sq_dict = state.get("structured_query")
    if not sq_dict:
        return Command(update={"error": "no structured_query"}, goto=END)

    sq = StructuredQuery.model_validate(sq_dict)

    # tasks가 비어있으면 (ambiguous/factual) → planning skip → 바로 response
    if not sq.tasks:
        logger.info("planning skipped (empty tasks)", reason="ambiguity or factual_lookup")
        return Command(
            update={"plan": {"todos": [], "dag": {}, "teams_selected": [],
                             "plan_notes": "tasks 비어있음 — Planning skip"}},
            goto="response",
        )

    planner = Planner()
    plan, issues = await planner.plan(sq)
    if plan is None:
        return Command(update={"error": f"Planning failed: {issues}"}, goto=END)

    plan_dict = plan.model_dump(mode="json")

    logger.info(
        "planning done",
        teams=plan.teams_selected,
        todos=len(plan.todos),
        issues=len(issues),
    )

    # Plan 검토 토글 — False 면 interrupt 스킵, 바로 execution.
    # 누락 / True 가 default (POC 초기 = 검토 켜짐).
    require_review = state.get("require_review", True)
    if require_review is False:
        logger.info("planning auto-approved (require_review=False)", todos=len(plan.todos))
        return Command(
            update={"plan": plan_dict},
            goto="execution",
        )

    # HITL: Plan 승인 요청 — interrupt()로 Checkpoint 저장 + astream 중단
    user_decision = interrupt({
        "type": "plan_review",
        "plan": plan_dict,
        "message": f"{len(plan.todos)}개 Todo 실행 계획이 생성되었습니다. 승인하시겠습니까?",
    })

    # Command(resume=...) 후 여기서 이어서 실행
    action = user_decision.get("action", "approve") if isinstance(user_decision, dict) else "approve"

    if action == "reject":
        logger.info("planning rejected by user")
        return Command(
            update={"response": {"text": "실행 계획이 거부되었습니다.", "format": "text"}},
            goto=END,
        )

    if action == "modify" and isinstance(user_decision, dict):
        modified_plan = user_decision.get("value")
        if modified_plan:
            plan_dict = modified_plan
            logger.info("planning modified by user")

    return Command(
        update={"plan": plan_dict},
        goto="execution",
    )
