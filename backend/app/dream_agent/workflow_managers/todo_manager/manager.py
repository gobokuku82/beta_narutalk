"""TodoManager — HITL 대기 중 Todo 수정/삭제/추가 + DAG 재검증

Plan dict (model_dump된 상태)를 직접 조작.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CascadeResult:
    """연쇄 무효화 계산 결과.

    Status: complete — Sprint 12 구현 완료.
      - `restart_from`: UX 라벨 전용 metadata (D1=E, 2026-04-23 확정). execution_stage 는 `completed_todos` 필터로 재실행 위치 결정 — `restart_from` 은 대시보드 cascade 시각화의 "Todo X 부터 재실행됩니다" 라벨용만.
      - `preserved_results`: dict[str, dict] (주의: 문서 10_system_architecture v1.8 은 preserved_todos: list[str] 로 기록됨 — A3 Phase 6 에서 v1.9 bump 시 정정 예정).
      - `new_plan`: 코드에만 존재 (문서 누락 — Phase 6 에서 v1.9 에 추가 예정).
    """
    invalidated_todos: list[str]     # 무효화된 Todo ID (Phase 순서)
    restart_from: Optional[str]      # UX 라벨 전용 — 재실행 시작점 안내
    preserved_results: dict[str, dict]  # 유지되는 결과
    new_plan: dict                   # 수정된 Plan (참조만)


class TodoManager:
    """Todo 수정/삭제/추가 + DAG 재검증."""

    def modify_todo(self, plan: dict, todo_id: str, changes: dict) -> dict:
        """Todo 파라미터 수정."""
        for todo in plan.get("todos", []):
            if todo.get("id") == todo_id:
                for key, value in changes.items():
                    if key == "tool_params" and isinstance(value, dict):
                        todo.setdefault("tool_params", {}).update(value)
                    else:
                        todo[key] = value
                logger.info("todo modified", todo_id=todo_id, keys=list(changes.keys()))
                break
        else:
            logger.warning("todo not found for modify", todo_id=todo_id)
        return self._rebuild_dag(plan)

    def delete_todo(self, plan: dict, todo_id: str) -> dict:
        """Todo 삭제 + 의존성 정리."""
        plan["todos"] = [t for t in plan.get("todos", []) if t.get("id") != todo_id]
        for todo in plan["todos"]:
            todo["depends_on"] = [d for d in todo.get("depends_on", []) if d != todo_id]
        logger.info("todo deleted", todo_id=todo_id, remaining=len(plan["todos"]))
        return self._rebuild_dag(plan)

    def add_todo(
        self,
        plan: dict,
        new_todo: dict,
        after_todo_id: Optional[str] = None,
    ) -> dict:
        """Todo 추가."""
        existing_ids = [t.get("id", "") for t in plan.get("todos", [])]
        nums = []
        for tid in existing_ids:
            parts = tid.split("_")
            if len(parts) >= 2 and parts[-1].isdigit():
                nums.append(int(parts[-1]))
        next_num = max(nums, default=0) + 1
        new_todo.setdefault("id", f"todo_{next_num:03d}")
        new_todo.setdefault("status", "pending")
        new_todo.setdefault("depends_on", [])
        new_todo.setdefault("tool_params", {})
        # ISSUE-008 (2026-04-27): PlannedTodo 의 필수 필드. 사용자 추가 todo 는
        # 분류 라벨 없이 들어오므로 "custom" 으로 기본값 — Plan.model_validate
        # 통과 + executor 에서도 분류 라벨로 사용 가능
        new_todo.setdefault("task_type", "custom")

        if after_todo_id and after_todo_id in existing_ids:
            new_todo["depends_on"] = [after_todo_id]

        plan.setdefault("todos", []).append(new_todo)
        logger.info("todo added", todo_id=new_todo["id"])
        return self._rebuild_dag(plan)

    def validate(self, plan: dict) -> list[str]:
        """DAG 검증 (순환, 유효 참조)."""
        issues: list[str] = []
        todo_ids = {t.get("id") for t in plan.get("todos", [])}

        for t in plan.get("todos", []):
            for dep in t.get("depends_on", []):
                if dep not in todo_ids:
                    issues.append(f"todo {t.get('id')} depends on unknown: {dep}")

        dag = plan.get("dag", plan.get("dependency_graph", {}))
        cycle = self._detect_cycle(dag)
        if cycle:
            issues.append(f"cycle detected: {cycle}")

        return issues

    def _rebuild_dag(self, plan: dict) -> dict:
        """todos의 depends_on으로 DAG 재구성."""
        dag = {}
        for t in plan.get("todos", []):
            dag[t.get("id", "")] = t.get("depends_on", [])
        plan["dag"] = dag
        plan["dependency_graph"] = dag
        return plan

    def _build_phases_from_plan(self, plan: dict) -> list[list[str]]:
        """dict Plan에서 Phase 계산. executor.build_phases(Pydantic)와 동일 로직.

        각 Phase는 sorted(ready)로 정렬 — 재현성 보장.
        stuck deps 발생 시 로그 + break (executor와 동일).
        """
        todos = plan.get("todos", [])
        dag = plan.get("dag", plan.get("dependency_graph", {}))

        if not todos:
            return []

        todo_by_id = {t["id"]: t for t in todos}
        remaining = set(todo_by_id.keys())
        completed: set[str] = set()
        phases: list[list[str]] = []

        while remaining:
            ready = [
                tid for tid in remaining
                if all(dep in completed for dep in dag.get(tid, []))
            ]
            if not ready:
                logger.error("DAG stuck — unresolvable deps", remaining=list(remaining))
                break
            phases.append(sorted(ready))
            for tid in ready:
                completed.add(tid)
                remaining.discard(tid)

        return phases

    def calculate_cascade(
        self,
        modified_todo_id: str,
        completed_todos: dict[str, dict],
        plan: dict,
    ) -> CascadeResult:
        """수정된 Todo로부터 downstream 의존성 추적 → 무효화 계산.

        read-only: plan을 변형하지 않음 (dag 읽기만).

        Args:
            modified_todo_id: 수정/삭제된 Todo ID
            completed_todos: 완료된 Todo 결과 {todo_id: result_dict}
            plan: 현재 Plan (dict)

        Returns:
            CascadeResult — 무효화 목록, 재시작 지점, 보존 결과
        """
        dag = plan.get("dag", plan.get("dependency_graph", {}))

        # downstream BFS
        invalidated_set: set[str] = set()
        queue = [modified_todo_id]
        while queue:
            current = queue.pop(0)
            if current in invalidated_set:
                continue
            invalidated_set.add(current)
            for todo_id, deps in dag.items():
                if current in deps and todo_id not in invalidated_set:
                    queue.append(todo_id)

        # 보존할 결과 (무효화 안 된 완료 Todo)
        preserved = {
            tid: result for tid, result in completed_todos.items()
            if tid not in invalidated_set
        }

        # Phase 순서 기반 정렬 (재현성)
        phases = self._build_phases_from_plan(plan)
        invalidated_ordered: list[str] = []
        for phase in phases:
            for tid in phase:
                if tid in invalidated_set:
                    invalidated_ordered.append(tid)

        # dag에 없는 id(삭제된 경우 등)도 포함
        for tid in invalidated_set:
            if tid not in invalidated_ordered:
                invalidated_ordered.append(tid)

        # restart_from — 무효화된 것 중 Phase 순서상 가장 빠른 것
        restart_from = invalidated_ordered[0] if invalidated_ordered else modified_todo_id

        return CascadeResult(
            invalidated_todos=invalidated_ordered,
            restart_from=restart_from,
            preserved_results=preserved,
            new_plan=plan,
        )

    def _detect_cycle(self, dag: dict[str, list[str]]) -> Optional[str]:
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {k: WHITE for k in dag}

        def dfs(u: str) -> bool:
            color[u] = GRAY
            for v in dag.get(u, []):
                if v not in color:
                    continue
                if color[v] == GRAY:
                    return True
                if color[v] == WHITE and dfs(v):
                    return True
            color[u] = BLACK
            return False

        for node in list(color.keys()):
            if color[node] == WHITE and dfs(node):
                return f"cycle at {node}"
        return None


_manager: Optional[TodoManager] = None


def get_todo_manager() -> TodoManager:
    global _manager
    if _manager is None:
        _manager = TodoManager()
    return _manager
