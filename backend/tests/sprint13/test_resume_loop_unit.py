"""I10d + I11-a — _graph_runner_with_resume Unit 테스트.

기존 IR-01~04 (I10d) + 신규 IR-05~10 (I11-a 이벤트 보강).

명세서:
  - I10d: sprint13_integration_i10d_resume_loop_spec.md
  - I11-a: docs/_claude/checkpointer/sprint13_i11_i12_plan.md §2

I11-a 변경으로 IR-01~04 기대값 업데이트:
  - 정상 종료 시 complete 이벤트 1회 추가 emit
  - cancel 시 silent drain astream 1회 + cancelled complete 이벤트
"""

from __future__ import annotations

import pytest


class MockWebSocket:
    def __init__(self, name):
        self.name = name
        self.sent: list[dict] = []

    async def send_json(self, data):
        self.sent.append(data)

    async def close(self, code=None, reason=None):
        pass


class _MockInterrupt:
    def __init__(self, value):
        self.value = value


class _MockTask:
    def __init__(self, interrupts):
        self.interrupts = interrupts


class _MockGraphState:
    """pending=True일 때 tasks[].interrupts[0].value 제공."""
    def __init__(self, pending, intr_value=None):
        self.next = ("some_node",) if pending else ()
        if pending and intr_value is not None:
            self.tasks = [_MockTask([_MockInterrupt(intr_value)])]
        else:
            self.tasks = []


class MockAgentWithInterrupt:
    """astream 연속 호출 가능 mock.

    streams: list[list[chunk]]
    pending_sequence: list[bool]
    intr_values: list[dict] — 각 aget_state에서 pending=True 시 반환할 intr_value
    """

    def __init__(self, streams, pending_sequence, intr_values=None):
        self.streams = streams
        self.pending_sequence = pending_sequence
        self.intr_values = intr_values or []
        self.stream_index = 0
        self.aget_index = 0
        self.resume_values = []
        self.received_state = None

    async def astream(self, state_or_cmd, config=None):
        from langgraph.types import Command as LGCommand
        if isinstance(state_or_cmd, LGCommand):
            self.resume_values.append(state_or_cmd.resume)
        else:
            self.received_state = state_or_cmd
        idx = self.stream_index
        self.stream_index += 1
        if idx >= len(self.streams):
            return   # 추가 astream 호출 (cancel/reject silent drain) — empty
        for chunk in self.streams[idx]:
            yield chunk

    async def aget_state(self, config):
        idx = self.aget_index
        self.aget_index += 1
        pending = (
            self.pending_sequence[idx]
            if idx < len(self.pending_sequence) else False
        )
        iv = self.intr_values[idx] if idx < len(self.intr_values) else None
        return _MockGraphState(pending=pending, intr_value=iv)


@pytest.fixture
def mock_ws_u1(reset_conn_manager):
    ws = MockWebSocket("u1_ws")
    reset_conn_manager._connections.setdefault("u1", {}).setdefault("agent", []).append(ws)
    return ws


def _nodes(sent_list):
    return [s.get("node") for s in sent_list if s.get("type") == "node_event"]


def _types(sent_list):
    return [s.get("type") for s in sent_list]


# ──────────────────────────────────────────────────────────────────
# IR-01 interrupt 없음 → 1차 astream + complete(success)
# ──────────────────────────────────────────────────────────────────

async def test_IR01_no_interrupt_skips_loop(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    agent = MockAgentWithInterrupt(
        streams=[[{"unknown_node_x": {"x": 1}}]],
        pending_sequence=[False],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1", {"user_input": "x"}, _agent=agent,
    )

    assert agent.stream_index == 1
    assert agent.resume_values == []
    assert _nodes(mock_ws_u1.sent) == ["unknown_node_x"]
    # I11-a: complete 이벤트 추가
    assert _types(mock_ws_u1.sent)[-1] == "complete"
    assert mock_ws_u1.sent[-1]["data"]["status"] == "success"


# ──────────────────────────────────────────────────────────────────
# IR-02 🔴 interrupt 1회 → approve 재실행 → complete
# ──────────────────────────────────────────────────────────────────

async def test_IR02_single_interrupt_resume(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    fresh_hitl.signal_resume("t1", {"action": "approve"})

    agent = MockAgentWithInterrupt(
        streams=[
            [{"unknown1": {}}],
            [{"unknown2": {}}, {"unknown3": {}}],
        ],
        pending_sequence=[True, False],
        intr_values=[{"type": "plan_review", "plan": {"todos": [{"id": "t1"}]}}],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1", {"user_input": "x"}, _agent=agent,
    )

    assert agent.stream_index == 2
    assert agent.resume_values == [{"action": "approve"}]
    # I11-a: hitl_request + resumed + complete 이벤트 추가
    types = _types(mock_ws_u1.sent)
    assert "hitl_request" in types
    assert "resumed" in types
    assert types[-1] == "complete"


# ──────────────────────────────────────────────────────────────────
# IR-03 🔴 interrupt 2회 연속 → FIFO
# ──────────────────────────────────────────────────────────────────

async def test_IR03_consecutive_interrupts_fifo(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    fresh_hitl.signal_resume("t1", {"action": "approve"})
    fresh_hitl.signal_resume("t1", {"action": "continue"})

    agent = MockAgentWithInterrupt(
        streams=[
            [{"unk1": {}}],
            [{"unk2": {}}],
            [{"unk3": {}}],
        ],
        pending_sequence=[True, True, False],
        intr_values=[
            {"type": "plan_review", "plan": {"todos": [{"id": "t1"}]}},
            {"type": "execution_pause", "progress": {}},
        ],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1", {"user_input": "x"}, _agent=agent,
    )

    assert agent.stream_index == 3
    assert agent.resume_values == [
        {"action": "approve"},
        {"action": "continue"},
    ]


# ──────────────────────────────────────────────────────────────────
# IR-04 cancel → silent drain + complete(cancelled)
# ──────────────────────────────────────────────────────────────────

async def test_IR04_cancel_breaks_loop(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    fresh_hitl.signal_resume("t1", {"action": "cancel"})

    agent = MockAgentWithInterrupt(
        streams=[[{"unk1": {}}]],   # silent drain 용 두번째 스트림은 없어도 빈 generator
        pending_sequence=[True],
        intr_values=[{"type": "execution_pause", "progress": {}}],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1", {"user_input": "x"}, _agent=agent,
    )

    # I11-a: cancel도 agent.astream 한 번 더 호출 (silent drain)
    assert agent.stream_index == 2
    assert agent.resume_values == [{"action": "cancel"}]
    types = _types(mock_ws_u1.sent)
    assert types[-1] == "complete"
    assert mock_ws_u1.sent[-1]["data"]["status"] == "cancelled"


# ──────────────────────────────────────────────────────────────────
# IR-05 🔴 plan_review interrupt → hitl_request broadcast
# ──────────────────────────────────────────────────────────────────

async def test_IR05_hitl_request_on_plan_review(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    fresh_hitl.signal_resume("t1", {"action": "approve"})

    agent = MockAgentWithInterrupt(
        streams=[
            [{"unk1": {}}],
            [{"unk2": {}}],
        ],
        pending_sequence=[True, False],
        intr_values=[{
            "type": "plan_review",
            "plan": {"todos": [{"id": "t1"}, {"id": "t2"}]},
            "message": "2개 Todo 승인?",
        }],
    )
    await _graph_runner_with_resume("u1", "c1", "t1", {"user_input": "x"}, _agent=agent)

    hr = [s for s in mock_ws_u1.sent if s.get("type") == "hitl_request"][0]
    assert hr["conversation_id"] == "c1"
    assert hr["turn_id"] == "t1"
    assert hr["data"]["plan"]["todos"] == [{"id": "t1"}, {"id": "t2"}]
    assert hr["data"]["message"] == "2개 Todo 승인?"
    assert hr["data"]["options"] == ["approve", "reject", "modify"]
    assert "request_id" in hr["data"]


# ──────────────────────────────────────────────────────────────────
# IR-06 🔴 execution_pause → paused broadcast
# ──────────────────────────────────────────────────────────────────

async def test_IR06_paused_on_execution_pause(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    fresh_hitl.signal_resume("t1", {"action": "continue"})

    agent = MockAgentWithInterrupt(
        streams=[
            [{"unk1": {}}],
            [{"unk2": {}}],
        ],
        pending_sequence=[True, False],
        intr_values=[{
            "type": "execution_pause",
            "progress": {
                "plan": {"todos": [{"id": "t1"}, {"id": "t2"}, {"id": "t3"}]},
                "completed_todos": {"t1": {}},
                "current_phase": 1,
            },
        }],
    )
    await _graph_runner_with_resume("u1", "c1", "t1", {"user_input": "x"}, _agent=agent)

    pa = [s for s in mock_ws_u1.sent if s.get("type") == "paused"][0]
    assert pa["turn_id"] == "t1"
    assert pa["data"]["total"] == 3
    assert pa["data"]["current_phase"] == 1
    assert pa["data"]["completed"] == ["t1"]


# ──────────────────────────────────────────────────────────────────
# IR-07 🔴 resumed broadcast (action 필드 확인)
# ──────────────────────────────────────────────────────────────────

async def test_IR07_resumed_broadcast(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    fresh_hitl.signal_resume("t1", {"action": "approve", "value": None})

    agent = MockAgentWithInterrupt(
        streams=[[{"unk1": {}}], [{"unk2": {}}]],
        pending_sequence=[True, False],
        intr_values=[{"type": "plan_review", "plan": {"todos": [{"id": "t1"}]}}],
    )
    await _graph_runner_with_resume("u1", "c1", "t1", {"user_input": "x"}, _agent=agent)

    re = [s for s in mock_ws_u1.sent if s.get("type") == "resumed"]
    assert len(re) == 1
    assert re[0]["data"]["action"] == "approve"


# ──────────────────────────────────────────────────────────────────
# IR-08 🔴 complete on success (guard_warnings 빈 리스트)
# ──────────────────────────────────────────────────────────────────

async def test_IR08_complete_on_success(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    agent = MockAgentWithInterrupt(
        streams=[[{"unk1": {}}]],
        pending_sequence=[False],
    )
    await _graph_runner_with_resume("u1", "c1", "t1", {"user_input": "x"}, _agent=agent)

    cm = [s for s in mock_ws_u1.sent if s.get("type") == "complete"]
    assert len(cm) == 1
    assert cm[0]["data"]["status"] == "success"
    assert cm[0]["data"]["guard_warnings"] == []


# ──────────────────────────────────────────────────────────────────
# IR-09 🔴 complete on cancel (status=cancelled)
# ──────────────────────────────────────────────────────────────────

async def test_IR09_complete_on_cancel(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    fresh_hitl.signal_resume("t1", {"action": "cancel"})

    agent = MockAgentWithInterrupt(
        streams=[[{"unk1": {}}]],
        pending_sequence=[True],
        intr_values=[{"type": "execution_pause", "progress": {}}],
    )
    await _graph_runner_with_resume("u1", "c1", "t1", {"user_input": "x"}, _agent=agent)

    cm = [s for s in mock_ws_u1.sent if s.get("type") == "complete"][-1]
    assert cm["data"]["status"] == "cancelled"


# ──────────────────────────────────────────────────────────────────
# IR-10 🔴 auto-approve — hitl._paused pre-set → plan_review 자동 승인
# ──────────────────────────────────────────────────────────────────

async def test_IR10_auto_approve_when_paused(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    # 사용자가 미리 pause 요청 (e.g., planning 중 pause 버튼)
    fresh_hitl._paused.add("t1")
    # 이후 plan_review interrupt 도달 → 자동 approve
    # 자동 approve 후 execution_pause interrupt 기대 → 사용자 resume
    fresh_hitl.signal_resume("t1", {"action": "continue"})

    agent = MockAgentWithInterrupt(
        streams=[
            [{"planning": {"plan": {"todos": [{"id": "t1"}]}}}],   # 1차 → plan_review
            [{"execution": {"execution_result": {"todos": []}}}],  # 자동 approve 후 execution → pause
            [{"response": {"response": {"text": "done"}}}],        # continue 후 response
        ],
        pending_sequence=[True, True, False],
        intr_values=[
            {"type": "plan_review", "plan": {"todos": [{"id": "t1"}]}},
            {"type": "execution_pause", "progress": {}},
        ],
    )
    await _graph_runner_with_resume("u1", "c1", "t1", {"user_input": "x"}, _agent=agent)

    # auto-approve는 hitl_request broadcast 하지 않음
    hr_events = [s for s in mock_ws_u1.sent if s.get("type") == "hitl_request"]
    assert hr_events == []

    # 대신 paused 이벤트가 1회 (execution_pause)
    paused = [s for s in mock_ws_u1.sent if s.get("type") == "paused"]
    assert len(paused) == 1

    # resume action은 approve(auto) + continue(user) 순서
    assert agent.resume_values == [
        {"action": "approve"},     # auto
        {"action": "continue"},    # user
    ]
