"""작업 ⑪.F — agent path helper-B E2E 검증 (sprint13)

명세서: docs/reports/계획_작업⑪_client_id_agent_흐름복구_2026-05-31.md §3.F·§7
대상 흐름: ws_agent payload → init_agent_state → AgentState →
          execution_stage → ExecutionContext → BaseTool.fetch helper-B

위치: sprint13 (ws_agent + state 통합 e2e 영역).
fixture: # clumi = POC 단일 client fixture, mock raw 의도 지정
         (project_poc_single_client_clumi 정합)

E2E 핵심:
  - positive: payload client_id="clumi" → ExecutionContext.client_id="clumi"
              → 실 helper-B (DataSource.get) 호출 시 clumi 인자 전달
  - negative: payload 누락 → ExecutionContext.client_id=None
              → BaseTool.fetch ValueError ("client 미지정")
"""

from unittest.mock import MagicMock

import pytest


# ──────────────────────────────────────────────────────────────────
# E2E-01 payload client_id 흐름 — init_agent_state → state → ExecutionContext
# ──────────────────────────────────────────────────────────────────

def test_E2E01_payload_to_execution_context_clumi():
    """clumi = POC 단일 client fixture, mock raw 의도 지정 (project_poc_single_client_clumi 정합)."""
    from app.dream_agent.states.agent_state import init_agent_state
    from app.dream_agent.models import ExecutionContext

    # 1단계: ws_agent payload → init_agent_state
    payload = {
        "user_input": "월 매출 보여줘",
        "language": "ko",
        "client_id": "clumi",
    }
    state = init_agent_state(
        user_input=payload.get("user_input", ""),
        conversation_id="conv_e2e_test",
        turn_id="turn_e2e_test",
        client_id=payload.get("client_id"),
        language=payload.get("language", "ko"),
    )

    assert state["client_id"] == "clumi"

    # 2단계: state.get → ExecutionContext (execution_stage:175 패턴)
    ctx = ExecutionContext(
        session_id=state["turn_id"],
        plan_id=state["turn_id"],
        client_id=state.get("client_id"),
    )

    assert ctx.client_id == "clumi"


# ──────────────────────────────────────────────────────────────────
# E2E-02 payload 누락 → ExecutionContext.client_id=None → helper-B fail-fast
# ──────────────────────────────────────────────────────────────────

def test_E2E02_no_client_id_payload_fails_fast():
    """negative — payload client_id 누락 시 BaseTool.fetch ValueError."""
    from app.dream_agent.states.agent_state import init_agent_state
    from app.dream_agent.models import ExecutionContext, ToolSpec
    from app.dream_agent.models.enums import ToolCategory
    from app.dream_agent.tools.base_tool import BaseTool

    # 1단계: payload 에 client_id 없음
    payload = {"user_input": "test", "language": "ko"}
    state = init_agent_state(
        user_input=payload.get("user_input", ""),
        conversation_id="c_no_client",
        turn_id="t_no_client",
        client_id=payload.get("client_id"),  # None
    )

    assert "client_id" not in state
    assert state.get("client_id") is None

    # 2단계: ExecutionContext.client_id = None
    ctx = ExecutionContext(
        session_id="t_no_client",
        plan_id="t_no_client",
        client_id=state.get("client_id"),
    )
    assert ctx.client_id is None

    # 3단계: BaseTool.fetch 호출 → ValueError fail-fast
    spec = ToolSpec(
        name="e2e_dummy",
        description="e2e",
        category=ToolCategory.METRICS,
        executor="tests.dummy.E2eDummyTool",
    )

    class E2eDummyTool(BaseTool):
        async def execute(self, params, context):
            return {}

    tool = E2eDummyTool(spec=spec)

    with pytest.raises(ValueError, match="client 미지정"):
        tool.fetch(source_id="revenue_total", context=ctx)


# ──────────────────────────────────────────────────────────────────
# E2E-03 helper-B DataSource.get 위임 검증 (mock DataSource)
# ──────────────────────────────────────────────────────────────────

def test_E2E03_helper_b_delegates_to_data_source():
    """positive — helper-B self.fetch 가 DataSource.get(client, source_id) 호출."""
    from app.dream_agent.models import ExecutionContext, ToolSpec
    from app.dream_agent.models.enums import ToolCategory
    from app.dream_agent.tools.base_tool import BaseTool

    # mock DataSource
    mock_ds = MagicMock()
    mock_ds.get.return_value = {"mocked": "data_for_revenue"}

    spec = ToolSpec(
        name="e2e_helper",
        description="e2e helper-B delegation",
        category=ToolCategory.METRICS,
        executor="tests.dummy.E2eHelperTool",
    )

    class E2eHelperTool(BaseTool):
        async def execute(self, params, context):
            return self.fetch(source_id="revenue_raw", context=context)

    tool = E2eHelperTool(spec=spec, data_source=mock_ds)

    ctx = ExecutionContext(session_id="s", plan_id="s", client_id="clumi")
    result = tool.fetch(source_id="revenue_raw", context=ctx)

    # DataSource.get 이 (clumi, revenue_raw) 인자로 호출됐는지
    mock_ds.get.assert_called_once_with("clumi", "revenue_raw")
    assert result == {"mocked": "data_for_revenue"}
