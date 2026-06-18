"""F1 회귀 — executor 가 DataFrame 을 직렬화 가능 형태로 정화하는가.

버그 (2026-06-02 agent path 검증에서 발견):
    내부 collector (RawCollectorBase) 가 {PRODUCES_KEY: <pandas.DataFrame>} 반환
    → executor 가 그대로 TodoResult.data 에 담음
    → hitl.report_phase_complete / _build_execution_result 의 model_dump(mode="json")
       에서 PydanticSerializationError: DataFrame → agent turn 크래시.

검증 (LLM·planner 불필요 — 결정론):
    DataFrame 을 반환하는 fake tool 을 executor 로 실행 → 산출 TodoResult 가
    model_dump(mode="json") 가능해야 하고, DataFrame 값은 드롭(None)되어야 한다.
    (chaining 은 list/dict 키만 소비하므로 DataFrame 드롭은 안전 — 검증에서 확인됨.)

근거: runner.json_safe / ws_agent._json_safe 와 동일 convention (직렬화 경계에서 DataFrame 제거).
"""
from __future__ import annotations

import pandas as pd

from app.dream_agent.execution import executor as ex
from app.dream_agent.models import ExecutionContext
from app.dream_agent.planning.planner import PlannedTodo


class _FakeTool:
    """tool 출력에 raw DataFrame 을 섞어 반환 (내부 collector 재현)."""

    def validate_params(self, params):
        # BaseTool 계약 — executor param 경계(슬라이스 1-④)가 execute 전 호출
        return True, []

    async def execute(self, params, ctx):
        return {
            "orders_raw": pd.DataFrame({"order_id": [1, 2], "amount": [100, 200]}),
            "count": 2,
            "source_id": "orders",
        }


class _FakePool:
    """agent_pool 대체 — registry/team_catalog 의존 제거 (결정론)."""

    def is_tool_stub(self, agent, tool):
        return False

    def is_tool_implemented(self, agent, tool):
        return True

    def get_real_tool(self, tool):
        return _FakeTool()

    def get_tool_meta(self, agent, tool):
        # B2.1 데이터 게이트가 consumes 를 읽음 — fake tool 은 consumes 미선언({}).
        return {}


async def test_executor_output_is_json_serializable_with_dataframe(monkeypatch):
    """tool 이 DataFrame 을 반환해도 TodoResult 가 직렬화 가능해야 한다."""
    monkeypatch.setattr(ex, "get_agent_pool", lambda: _FakePool())

    todo = PlannedTodo(
        id="t1",
        task_type="data_collection",
        tool="orders_collector",
        agent="collection_agent",
    )
    ctx = ExecutionContext(session_id="verify", plan_id="verify", client_id="clumi")

    result = await ex._run_single_todo(todo, ctx, {})

    # 핵심 1 — model_dump(mode="json") 가 크래시하지 않아야 (F1 버그의 핵심)
    dumped = result.model_dump(mode="json")
    assert dumped["status"] == "completed"

    # 핵심 2 — DataFrame 은 드롭(None), 직렬 가능 값은 보존
    assert result.data["orders_raw"] is None
    assert result.data["count"] == 2
    assert result.data["source_id"] == "orders"


async def test_executor_preserves_serializable_dict(monkeypatch):
    """DataFrame 이 없는 정상 출력은 그대로 보존돼야 한다 (정화가 과하지 않음)."""

    class _PlainTool:
        def validate_params(self, params):
            return True, []

        async def execute(self, params, ctx):
            return {"roas": 6.53, "rows": [{"a": 1}, {"a": 2}], "nested": {"x": "y"}}

    class _PlainPool(_FakePool):
        def get_real_tool(self, tool):
            return _PlainTool()

    monkeypatch.setattr(ex, "get_agent_pool", lambda: _PlainPool())

    todo = PlannedTodo(id="t2", task_type="metric_calculation",
                       tool="roas_overall", agent="metrics_agent")
    ctx = ExecutionContext(session_id="verify", plan_id="verify", client_id="clumi")

    result = await ex._run_single_todo(todo, ctx, {})

    result.model_dump(mode="json")  # 직렬화 OK
    assert result.data["roas"] == 6.53
    assert result.data["rows"] == [{"a": 1}, {"a": 2}]
    assert result.data["nested"] == {"x": "y"}
