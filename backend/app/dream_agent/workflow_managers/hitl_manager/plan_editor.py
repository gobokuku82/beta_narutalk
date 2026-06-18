"""Plan Editor — 자연어 기반 Plan 수정.

Sprint 14 A3 D 통일 (2026-04-30):
  - planner.Plan / PlannedTodo 단일 사용 (models.Plan / TodoItem 의존 제거)
  - apply_edit 반환 단일화: tuple[Plan, PlanChange] → Plan
  - PlanChange 폐기 (NL edit 경로에서). approval.py 는 별도 flow 로 유지.

Phase 3 (D-13) 보존:
  - prompt injection 방어 (MAX_INSTRUCTION_LEN + sanitize)
  - reorder action 신구현

Reference:
  - docs/agent_specs/adr/ADR-010_plan_schema_unification.md
  - docs/reports/sprint14_a3_phase_c_unify_plan.md
"""

import re
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.llm_manager import get_llm_client
from app.dream_agent.planning.planner import Plan, PlannedTodo

logger = get_logger(__name__)


# Sprint 14 A3 Phase 3 (D-13): prompt injection 방어
MAX_INSTRUCTION_LEN = 500


def _sanitize(text: str) -> str:
    """LLM prompt 삽입 전 위험 패턴 중화.

    Status: complete — Sprint 14 A3 Phase 3 (D-13).

    방어 대상:
    - Backtick (code fence) / triple quote → 공백 치환
    - "ignore above" / "system:" 류 프롬프트 주입 문구 → 그대로 두되 길이 제한으로 완화
    - 개행 과다 → 단일 개행 정규화
    """
    text = text.replace("```", "   ").replace("'''", "   ").replace('"""', "   ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


class PlanEditor:
    """Plan 편집기 — 자연어 명령을 Plan 수정 작업으로 변환.

    Status: complete — Sprint 14 A3 D 통일 (2026-04-30).
    History: Sprint 12 add/remove/modify → A3 Phase 3 reorder + injection 방어
             → A3 Phase C-Unify (D 단일화 / PlanChange 폐기).
    """

    def __init__(self):
        self.client = get_llm_client("planning")

    async def parse_instruction(
        self,
        instruction: str,
        plan: Plan,
    ) -> dict[str, Any]:
        """자연어 명령 파싱.

        Args:
            instruction: 사용자 명령 ("2번 작업 삭제해줘", "구글 트렌드 추가해줘")
            plan: 현재 planner.Plan

        Returns:
            파싱된 명령 {action, target_todo_ids, params}
        """
        # D-13: 입력 길이 제한 + sanitize (prompt injection 방어)
        if not isinstance(instruction, str) or len(instruction) > MAX_INSTRUCTION_LEN:
            logger.warning(
                "instruction length exceeds limit",
                length=len(instruction) if isinstance(instruction, str) else 0,
                max_length=MAX_INSTRUCTION_LEN,
            )
            return {
                "action": "unknown",
                "target_todo_ids": [],
                "params": {},
                "reason": f"명령 길이 초과 (최대 {MAX_INSTRUCTION_LEN}자)",
            }
        instruction = _sanitize(instruction)

        logger.info("Parsing plan edit instruction", instruction=instruction)

        # 프롬프트 구성
        system_prompt = """
당신은 Plan 편집 명령을 파싱하는 AI입니다.

사용자의 자연어 명령을 다음 형식으로 변환하세요:

## 지원 액션
- add: Todo 추가
- remove: Todo 삭제
- modify: Todo 수정
- reorder: 순서 변경

## 응답 형식 (JSON)
{
    "action": "add|remove|modify|reorder",
    "target_todo_ids": ["todo_id1", ...],
    "params": {
        "task": "작업 설명 (add/modify) — rationale 로 매핑됨",
        "tool": "도구명 (add/modify)",
        "priority": 1-10 (modify),
        "new_position": 1-N (reorder)
    },
    "reason": "변경 이유"
}
"""

        # 현재 Todo 목록 문자열 (rationale/task_type 은 D-13 sanitize)
        todos_str = "\n".join([
            f"{i+1}. [{t.id[:8]}] {_sanitize(t.rationale or t.task_type)} "
            f"(tool: {t.tool or 'unknown'})"
            for i, t in enumerate(plan.todos)
        ])

        user_prompt = f"""
## 현재 Plan의 Todo 목록
{todos_str}

## 사용자 명령
{instruction}

JSON으로 응답하세요.
"""

        try:
            result = await self.client.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
            )
            return result
        except Exception as e:
            logger.error("Failed to parse instruction", error=str(e))
            return {
                "action": "unknown",
                "target_todo_ids": [],
                "params": {},
                "reason": f"파싱 실패: {str(e)}",
            }

    async def apply_edit(
        self,
        plan: Plan,
        parsed: dict[str, Any],
        user_instruction: str,
    ) -> Plan:
        """편집 적용.

        Args:
            plan: 현재 planner.Plan
            parsed: 파싱된 명령
            user_instruction: 원본 명령 (현재 미사용 — 향후 메모리 연동 시 활용)

        Returns:
            수정된 Plan (PlanChange 폐기 — Sprint 14 A3 D 통일)
        """
        action = parsed.get("action", "unknown")
        target_ids = parsed.get("target_todo_ids", [])
        params = parsed.get("params", {})

        logger.info(
            "Applying plan edit",
            action=action,
            target_ids=target_ids,
            user_instruction=user_instruction[:100] if user_instruction else "",
        )

        # 새 Todo 목록 생성
        new_todos = list(plan.todos)

        if action == "reorder":
            # Status: complete — Sprint 14 A3 Phase 3 신구현.
            # params["new_position"] 기반 target_ids 를 지정 위치로 이동.
            new_position = params.get("new_position")
            if new_position is None or not target_ids:
                logger.warning(
                    "reorder missing params",
                    target_ids=target_ids,
                    new_position=new_position,
                )
            else:
                target_items = [t for t in new_todos if t.id in target_ids]
                rest = [t for t in new_todos if t.id not in target_ids]
                insert_at = max(0, min(int(new_position), len(rest)))
                new_todos = rest[:insert_at] + target_items + rest[insert_at:]

        elif action == "remove":
            new_todos = [t for t in new_todos if t.id not in target_ids]

        elif action == "add":
            new_todo = PlannedTodo(
                id=params.get("id") or _generate_todo_id(plan),
                task_type=params.get("task_type", "user_added"),
                agent=params.get("agent"),
                tool=params.get("tool"),
                tool_params=params.get("tool_params") or {},
                depends_on=params.get("depends_on") or [],
                priority=params.get("priority", 5),
                rationale=params.get("task") or params.get("rationale", "사용자 추가"),
            )
            new_todos.append(new_todo)
            target_ids = [new_todo.id]

        elif action == "modify":
            for i, todo in enumerate(new_todos):
                if todo.id in target_ids:
                    update_dict = {}
                    if "task" in params:
                        # task → rationale (사용자 표시 우선)
                        update_dict["rationale"] = params["task"]
                    if "rationale" in params:
                        update_dict["rationale"] = params["rationale"]
                    if "tool" in params:
                        update_dict["tool"] = params["tool"]
                    if "priority" in params:
                        update_dict["priority"] = params["priority"]
                    if "agent" in params:
                        update_dict["agent"] = params["agent"]

                    new_todos[i] = todo.model_copy(update=update_dict)

        # Plan 업데이트 (model_copy — PlannedTodo 가 frozen=False 라도 불변 패턴)
        new_plan = plan.model_copy(update={"todos": new_todos})

        return new_plan

    async def validate_edit(
        self,
        plan: Plan,
        parsed: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """편집 유효성 검사.

        Args:
            plan: 현재 Plan
            parsed: 파싱된 명령

        Returns:
            (valid, errors)
        """
        errors = []
        action = parsed.get("action", "unknown")
        target_ids = parsed.get("target_todo_ids", [])

        if action == "unknown":
            errors.append("알 수 없는 명령입니다.")
            return False, errors

        if action in ("remove", "modify", "reorder") and not target_ids:
            errors.append("수정할 대상 Todo가 지정되지 않았습니다.")

        # 대상 Todo 존재 확인
        todo_ids = {t.id for t in plan.todos}
        for tid in target_ids:
            if tid not in todo_ids:
                errors.append(f"Todo를 찾을 수 없습니다: {tid}")

        # Sprint 14 A3 Phase 3 — reorder action 의 new_position 검증
        if action == "reorder":
            params = parsed.get("params", {})
            if "new_position" not in params:
                errors.append("reorder 에는 params.new_position 이 필요합니다.")

        return len(errors) == 0, errors


def _generate_todo_id(plan: Plan) -> str:
    """add 시 신규 todo id 생성 — 기존 id 와 충돌 X."""
    existing = {t.id for t in plan.todos}
    n = len(plan.todos) + 1
    while f"todo_{n:03d}" in existing:
        n += 1
    return f"todo_{n:03d}"
