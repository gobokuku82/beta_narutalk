"""I10a — _parse_query_message Unit 테스트

명세서: sprint13_integration_i10a_parse_query_spec.md
대상: backend/api_v2/ws_agent.py _parse_query_message

4 케이스.
"""


def test_PA01_valid_message():
    from api_v2.ws_agent import _parse_query_message

    msg = {
        "type": "query",
        "conversation_id": "conv_123",
        "turn_id": "turn_abc",
        "user_input": "블루밍글로우 분석",
        "language": "ko",
    }
    result = _parse_query_message(msg)

    assert "error" not in result
    assert result["conversation_id"] == "conv_123"
    assert result["turn_id"] == "turn_abc"
    assert result["payload"]["user_input"] == "블루밍글로우 분석"
    assert result["payload"]["language"] == "ko"


def test_PA02_missing_conversation_id():
    from api_v2.ws_agent import _parse_query_message

    msg = {"type": "query", "turn_id": "t1", "user_input": "x"}
    result = _parse_query_message(msg)

    assert result["error"]["type"] == "error"
    assert result["error"]["code"] == "INVALID_MESSAGE"
    assert "conversation_id" in result["error"]["message"]
    assert "conversation_id" not in result


def test_PA03_missing_turn_id():
    from api_v2.ws_agent import _parse_query_message

    msg = {"type": "query", "conversation_id": "c1", "user_input": "x"}
    result = _parse_query_message(msg)

    assert result["error"]["code"] == "INVALID_MESSAGE"
    assert "turn_id" in result["error"]["message"]


def test_PA04_missing_user_input():
    from api_v2.ws_agent import _parse_query_message

    msg = {"type": "query", "conversation_id": "c1", "turn_id": "t1"}
    result = _parse_query_message(msg)

    assert result["error"]["code"] == "INVALID_MESSAGE"
    assert "user_input" in result["error"]["message"]
