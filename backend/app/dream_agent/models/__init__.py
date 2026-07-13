"""Domain Models — 활성 공개 API 큐레이션

**Tool I/O 공유 타입 + 프레임 enum** 만 노출.
레이어 경계 DTO (Schema) 는 `app.dream_agent.schemas/` 참조.
레이어 산출물 모델 (Plan/PlannedTodo) 은 `app.dream_agent.planning.planner` 참조.

| 영역 | 위치 |
|------|------|
| **레이어 산출물 DTO** (Schema) | `app.dream_agent.schemas/` — StructuredQuery / ExecutionResult / ResponsePayload |
| **Plan / PlannedTodo** | `app.dream_agent.planning.planner` (Planning 레이어가 소유) |
| **AgentState** (LangGraph 전역) | `app.dream_agent.states.agent_state` |
| **Tool 입력 컨텍스트** | `models/execution.py::ExecutionContext` (본 패키지) |
| **Tool 메타** | `models/tool.py` (`ToolSpec`/`ToolParameter`) |

프레임 추출(2026-06-19): 구 `app.data_layer.schemas.outputs.dashboard1` 마케팅 출력 재노출(소비처 0 — ADR-027
이전 후 미삭제 shim) 제거. 도메인 출력 DTO 는 도메인별로 `app.dream_agent.schemas` / data layer 에 둔다.
"""

from app.dream_agent.models.enums import (
    KNOWN_TOOL_CATEGORIES,
    ToolCategory,
    ToolParameterType,
)
from app.dream_agent.models.execution import ExecutionContext
from app.dream_agent.models.tool import DisplaySpec, StoragePolicy, ToolParameter, ToolSpec

__all__ = [
    # ── Enums / 관례 ──
    "ToolCategory",
    "KNOWN_TOOL_CATEGORIES",
    "ToolParameterType",
    # ── Execution (Tool 컨텍스트) ──
    "ExecutionContext",
    # ── Tool 메타 ──
    "ToolSpec",
    "ToolParameter",
    "StoragePolicy",
    "DisplaySpec",
]
