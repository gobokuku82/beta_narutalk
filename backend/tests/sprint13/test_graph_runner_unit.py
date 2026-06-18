"""I10c — _graph_runner + _chunk_to_event Unit 테스트

명세서: sprint13_integration_i10c_graph_runner_spec.md

6 케이스 (mock agent).
"""

import pytest


class MockWebSocket:
    def __init__(self, name, raise_on_send=False):
        self.name = name
        self.raise_on_send = raise_on_send
        self.sent = []

    async def send_json(self, data):
        if self.raise_on_send:
            raise ConnectionError(f"{self.name} disconnected")
        self.sent.append(data)

    async def close(self, code=None, reason=None):
        pass


class MockAgent:
    """LangGraph agent mock — astream yield chunk."""

    def __init__(self, chunks):
        self.chunks = chunks
        self.received_state = None
        self.received_config = None

    async def astream(self, state, config=None):
        self.received_state = state
        self.received_config = config
        for chunk in self.chunks:
            yield chunk


@pytest.fixture
def mock_ws_u1(reset_conn_manager):
    ws = MockWebSocket("u1_ws")
    reset_conn_manager._connections.setdefault("u1", {}).setdefault("agent", []).append(ws)
    return ws


# ──────────────────────────────────────────────────────────────────
# GR-01 state 빌드
# ──────────────────────────────────────────────────────────────────

async def test_GR01_state_built_from_payload(mock_ws_u1):
    from api_v2.ws_agent import _graph_runner

    agent = MockAgent(chunks=[])
    await _graph_runner(
        "u1", "c1", "t1",
        {"user_input": "blooming 분석", "language": "en"},
        _agent=agent,
    )

    s = agent.received_state
    assert s["user_id"] == "u1"
    assert s["conversation_id"] == "c1"
    assert s["turn_id"] == "t1"
    assert s["session_id"] == "t1"
    assert s["user_input"] == "blooming 분석"
    assert s["language"] == "en"


# ──────────────────────────────────────────────────────────────────
# GR-02 🔴 thread_id + config
# ──────────────────────────────────────────────────────────────────

async def test_GR02_thread_id_config(mock_ws_u1):
    from api_v2.ws_agent import _graph_runner

    agent = MockAgent(chunks=[])
    await _graph_runner(
        "u1", "c1", "t1",
        {"user_input": "x"},
        _agent=agent,
    )

    assert agent.received_config is not None
    assert agent.received_config["configurable"]["thread_id"] == "c1_t1"


# ──────────────────────────────────────────────────────────────────
# GR-03 conversation_history pass
# ──────────────────────────────────────────────────────────────────

async def test_GR03_conversation_history_passed(mock_ws_u1):
    from api_v2.ws_agent import _graph_runner

    history = [{"turn_index": 1, "user_input": "a", "response_summary": "b"}]
    agent = MockAgent(chunks=[])
    await _graph_runner(
        "u1", "c1", "t1",
        {"user_input": "x", "conversation_history": history, "history_limit": 2},
        _agent=agent,
    )

    assert agent.received_state["conversation_history"] == history
    assert agent.received_state["history_limit"] == 2


# ──────────────────────────────────────────────────────────────────
# GR-04 🔴 chunk → broadcast
# ──────────────────────────────────────────────────────────────────

async def test_GR04_chunk_broadcast(mock_ws_u1):
    from api_v2.ws_agent import _graph_runner

    chunks = [
        {"cognitive_stage": {"structured_query": {"x": 1}}},
        {"planning_stage": {"plan": {"y": 2}}},
    ]
    agent = MockAgent(chunks=chunks)

    await _graph_runner("u1", "c1", "t1", {"user_input": "x"}, _agent=agent)

    assert len(mock_ws_u1.sent) == 2
    assert mock_ws_u1.sent[0]["type"] == "node_event"
    assert mock_ws_u1.sent[0]["node"] == "cognitive_stage"
    assert mock_ws_u1.sent[0]["conversation_id"] == "c1"
    assert mock_ws_u1.sent[0]["turn_id"] == "t1"
    assert mock_ws_u1.sent[1]["node"] == "planning_stage"


# ──────────────────────────────────────────────────────────────────
# GR-05 __interrupt__ chunk skip
# ──────────────────────────────────────────────────────────────────

async def test_GR05_interrupt_chunk_skipped(mock_ws_u1):
    from api_v2.ws_agent import _graph_runner

    chunks = [
        {"cognitive_stage": {"x": 1}},
        {"__interrupt__": [{"value": {"type": "plan_review"}}]},
    ]
    agent = MockAgent(chunks=chunks)

    await _graph_runner("u1", "c1", "t1", {"user_input": "x"}, _agent=agent)

    # cognitive_stage만 broadcast, __interrupt__는 skip
    assert len(mock_ws_u1.sent) == 1
    assert mock_ws_u1.sent[0]["node"] == "cognitive_stage"


# ──────────────────────────────────────────────────────────────────
# GR-06 _chunk_to_event 순수 함수
# ──────────────────────────────────────────────────────────────────

def test_GR06_chunk_to_event_unit():
    from api_v2.ws_agent import _chunk_to_event

    # 정상 노드
    evt = _chunk_to_event({"cognitive_stage": {"x": 1}}, "c1", "t1")
    assert evt["type"] == "node_event"
    assert evt["node"] == "cognitive_stage"
    assert evt["conversation_id"] == "c1"
    assert evt["turn_id"] == "t1"
    assert evt["data"] == {"x": 1}

    # __interrupt__
    assert _chunk_to_event({"__interrupt__": [{"value": {}}]}, "c1", "t1") is None

    # 빈 chunk
    assert _chunk_to_event({}, "c1", "t1") is None
