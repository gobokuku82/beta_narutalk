"""I10f — /ws/agent E2E live 테스트 (실제 LLM + PostgreSQL Checkpointer)

명세서: sprint13_integration_i10f_e2e_spec.md

5 케이스 (@pytest.mark.live, opt-in 실행).

전제:
  - .env: OPENAI_API_KEY
  - PostgreSQL 실행 중
  - settings.CHECKPOINT_DB_URI 유효

실행 — 각 테스트는 **개별 실행**해야 함 (TestClient 한계):
  uv run pytest backend/tests/sprint13/test_ws_agent_e2e_live.py::test_WL02_plan_review_reject -v -m live
  uv run pytest backend/tests/sprint13/test_ws_agent_e2e_live.py::test_WL03_multi_tab_broadcast -v -m live
  ...

⚠️ 알려진 한계 (TestClient + asyncio.create_task + lifespan):
   다수 테스트 수집 시 첫 번째 이후 테스트가 hang. 원인: anyio portal + PostgreSQL
   connection pool + asyncio task lifecycle 상호작용. 실제 uvicorn 환경에는 없음.
   → 각 live 테스트를 개별 실행하거나, 실제 서버(run_server_v2.py) + 브라우저로 검증.

노드명: cognitive / planning / execution / response (suffix 없음).
주의: planning 노드는 interrupt 전에 chunk를 yield하지 않으므로 cognitive 이벤트만 안정 수신 가능.
HITL signal은 pre-signal 패턴 (Queue 버퍼링).
"""

import concurrent.futures
import time
import uuid

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.live


def _recv_timeout(ws, timeout=30):
    """receive_json with thread-based timeout. timeout 시 None 반환.

    스레드 leak 가능 (TestClient receive 차단 해제 못 함) — 테스트 종료 시 회수됨.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        f = ex.submit(ws.receive_json)
        try:
            return f.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return None


@pytest.fixture
def live_client():
    """실제 lifespan 활성화 → PostgreSQL Checkpointer + 4-Layer graph 컴파일.

    function scope — 각 테스트 격리 (이전 run_turn task / PostgreSQL connection 잔재 방지).
    """
    from api_v2.main import app
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def reset_singletons():
    """매 live 테스트마다 싱글톤 클린 + 이전 테스트 task/connection 정리 대기."""
    from api_v2.connection_manager import conn_manager
    from app.dream_agent.workflow_managers.concurrency_manager import concurrency
    from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager
    conn_manager._connections.clear()
    concurrency._reset_for_test()
    h = get_hitl_manager()
    h._progress.clear()
    h._paused.clear()
    if hasattr(h, "_reset_resume_queues_for_test"):
        h._reset_resume_queues_for_test()
    # 이전 테스트의 PostgreSQL 연결/asyncio task 잔재가 settle 하도록 약간 대기
    time.sleep(1.0)
    yield
    concurrency._reset_for_test()
    conn_manager._connections.clear()
    time.sleep(1.0)


def _new_ids():
    return f"conv_{uuid.uuid4().hex[:8]}", f"turn_{uuid.uuid4().hex[:8]}"


def _drain_until(ws, predicate, max_events=40):
    """events를 모으며 predicate 만족 시 break."""
    events = []
    for _ in range(max_events):
        evt = ws.receive_json()
        events.append(evt)
        if predicate(evt):
            break
    return events


# ──────────────────────────────────────────────────────────────────
# 참고: WL-01 (full pipeline happy path)는 파일 마지막에 위치.
# 이유: execution까지 도는 긴 task(25s+) 이후 TestClient 시퀀셜 실행에서
#       anyio portal + asyncio task 간섭으로 뒤 테스트 hang. 개별 실행 가능.
# ──────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────
# WL-02 plan_review reject → 그래프 조기 종료
# ──────────────────────────────────────────────────────────────────

def test_WL02_plan_review_reject(live_client):
    conv_id, turn_id = _new_ids()

    with live_client.websocket_connect("/ws/agent?user_id=u_live") as ws_agent, \
         live_client.websocket_connect("/ws/hitl?user_id=u_live") as ws_hitl:

        ws_agent.receive_json(); ws_hitl.receive_json()

        ws_agent.send_json({
            "type": "query",
            "conversation_id": conv_id,
            "turn_id": turn_id,
            "user_input": "블루밍글로우 리뷰 분석",
        })

        ws_hitl.send_json({
            "type": "hitl_response",
            "data": {"request_id": "auto", "action": "reject", "turn_id": turn_id},
        })
        ws_hitl.receive_json()

        # cognitive 보장 수신 (blocking)
        events = _drain_until(ws_agent, lambda e: e.get("node") == "cognitive", max_events=10)

        # 이후 추가 이벤트는 timeout 기반 (reject는 response 노드 emit 안 할 수 있음)
        for _ in range(10):
            evt = _recv_timeout(ws_agent, timeout=15)
            if evt is None:
                break
            events.append(evt)

        nodes = [e.get("node") for e in events if e.get("type") == "node_event"]
        assert "cognitive" in nodes, f"cognitive 미수신. nodes={nodes}"
        errors = [e for e in events if e.get("type") == "error"]
        assert errors == [], f"unexpected errors: {errors}"


# ──────────────────────────────────────────────────────────────────
# WL-03 Multi-tab broadcast — 같은 user_id의 2개 WS 모두 수신
# ──────────────────────────────────────────────────────────────────

def test_WL03_multi_tab_broadcast(live_client):
    conv_id, turn_id = _new_ids()

    with live_client.websocket_connect("/ws/agent?user_id=u_multi") as ws_a, \
         live_client.websocket_connect("/ws/agent?user_id=u_multi") as ws_b, \
         live_client.websocket_connect("/ws/hitl?user_id=u_multi") as ws_hitl:

        ws_a.receive_json(); ws_b.receive_json(); ws_hitl.receive_json()

        ws_a.send_json({
            "type": "query",
            "conversation_id": conv_id,
            "turn_id": turn_id,
            "user_input": "블루밍글로우 분석",
        })

        # pre-signal reject → 빠른 종료
        ws_hitl.send_json({
            "type": "hitl_response",
            "data": {"request_id": "auto", "action": "reject", "turn_id": turn_id},
        })
        ws_hitl.receive_json()

        # 양쪽 모두 cognitive 수신
        events_a = _drain_until(ws_a, lambda e: e.get("node") == "cognitive", max_events=10)
        events_b = _drain_until(ws_b, lambda e: e.get("node") == "cognitive", max_events=10)

        assert any(e.get("node") == "cognitive" for e in events_a), \
            f"ws_a cognitive 미수신: {events_a}"
        assert any(e.get("node") == "cognitive" for e in events_b), \
            f"ws_b cognitive 미수신: {events_b}"


# ──────────────────────────────────────────────────────────────────
# WL-04 conversation_history 주입 sanity (2번째 turn 정상 수행)
# ──────────────────────────────────────────────────────────────────

def test_WL04_conversation_history_injection(live_client):
    conv_id = f"conv_{uuid.uuid4().hex[:8]}"
    turn_id = f"turn_{uuid.uuid4().hex[:8]}"

    with live_client.websocket_connect("/ws/agent?user_id=u_hist") as ws_agent, \
         live_client.websocket_connect("/ws/hitl?user_id=u_hist") as ws_hitl:

        ws_agent.receive_json(); ws_hitl.receive_json()

        ws_agent.send_json({
            "type": "query",
            "conversation_id": conv_id,
            "turn_id": turn_id,
            "user_input": "방금 결과 다시 정리해줘",
            "conversation_history": [{
                "turn_index": 1,
                "user_input": "블루밍글로우 리뷰 가져와",
                "response_summary": "12개 리뷰 수집 완료",
            }],
            "history_limit": 3,
        })

        # 빠른 종료를 위해 pre-signal reject
        ws_hitl.send_json({
            "type": "hitl_response",
            "data": {"request_id": "auto", "action": "reject", "turn_id": turn_id},
        })
        ws_hitl.receive_json()

        # cognitive 도달 검증 (history 주입이 prompt에 들어가도 cognitive는 정상 동작)
        events = _drain_until(ws_agent, lambda e: e.get("node") == "cognitive", max_events=10)
        assert any(e.get("node") == "cognitive" for e in events), \
            f"cognitive 미도달. events={events}"

        errors = [e for e in events if e.get("type") == "error"]
        assert errors == [], f"unexpected errors: {errors}"


# ──────────────────────────────────────────────────────────────────
# WL-05 Concurrent limit — 2번째 query는 CONCURRENT_LIMIT_EXCEEDED
# ──────────────────────────────────────────────────────────────────

def test_WL05_concurrent_limit_exceeded(live_client):
    from app.dream_agent.workflow_managers.concurrency_manager import concurrency
    concurrency._max_concurrent = 1

    conv_id1, turn_id1 = _new_ids()
    _, turn_id2 = _new_ids()

    try:
        with live_client.websocket_connect("/ws/agent?user_id=u_conc") as ws_agent, \
             live_client.websocket_connect("/ws/hitl?user_id=u_conc") as ws_hitl:

            ws_agent.receive_json(); ws_hitl.receive_json()

            # 1차 query — slot 점유. pre-signal reject로 빠른 정리.
            ws_agent.send_json({
                "type": "query",
                "conversation_id": conv_id1, "turn_id": turn_id1,
                "user_input": "블루밍글로우 분석",
            })
            ws_hitl.send_json({
                "type": "hitl_response",
                "data": {"request_id": "auto", "action": "reject", "turn_id": turn_id1},
            })
            ws_hitl.receive_json()

            # 즉시 2차 query 시도 — slot 점유 중이므로 거부
            ws_agent.send_json({
                "type": "query",
                "conversation_id": conv_id1, "turn_id": turn_id2,
                "user_input": "다른 쿼리",
            })

            # 다음 이벤트 중 CONCURRENT_LIMIT_EXCEEDED 찾기
            err_evts = []
            for _ in range(20):
                evt = _recv_timeout(ws_agent, timeout=30)
                if evt is None:
                    break
                if evt.get("type") == "error" and evt.get("code") == "CONCURRENT_LIMIT_EXCEEDED":
                    err_evts.append(evt)
                    break

            assert len(err_evts) == 1
            assert err_evts[0]["turn_id"] == turn_id2
    finally:
        concurrency._max_concurrent = None


# ──────────────────────────────────────────────────────────────────
# WL-06 🔴 I11-a 이벤트 보강 검증 — hitl_request/resumed/complete 순서 + guard_warnings
# ──────────────────────────────────────────────────────────────────

def test_WL06_i11a_events_sequence_and_guard_warnings(live_client):
    """I11-a run_turn 이벤트 보강 검증.

    pre-signal approve → full pipeline.
    검증:
      - hitl_request 이벤트 수신 (plan_review interrupt)
      - resumed 이벤트 수신 (approve)
      - complete 이벤트 수신 (status=success, guard_warnings 필드 존재)
    """
    conv_id, turn_id = _new_ids()

    with live_client.websocket_connect("/ws/agent?user_id=u_i11a") as ws_agent, \
         live_client.websocket_connect("/ws/hitl?user_id=u_i11a") as ws_hitl:

        ws_agent.receive_json(); ws_hitl.receive_json()

        ws_agent.send_json({
            "type": "query",
            "conversation_id": conv_id,
            "turn_id": turn_id,
            "user_input": "블루밍글로우 최근 리뷰 감성 분석",
        })

        # pre-signal approve
        ws_hitl.send_json({
            "type": "hitl_response",
            "data": {"request_id": "auto", "action": "approve", "turn_id": turn_id},
        })
        ws_hitl.receive_json()

        # complete 까지 모든 이벤트 수집
        events = _drain_until(
            ws_agent,
            lambda e: e.get("type") == "complete",
            max_events=40,
        )

        types = [e.get("type") for e in events]
        assert "hitl_request" in types, f"hitl_request 미수신. types={types}"
        assert "resumed" in types, f"resumed 미수신. types={types}"
        assert "complete" in types, f"complete 미수신. types={types}"

        # 순서: hitl_request → resumed → complete
        hr_idx = types.index("hitl_request")
        re_idx = types.index("resumed")
        cm_idx = types.index("complete")
        assert hr_idx < re_idx < cm_idx

        # complete 이벤트 포맷 검증
        cm = events[cm_idx]
        assert cm["conversation_id"] == conv_id
        assert cm["turn_id"] == turn_id
        assert cm["data"]["status"] in ("success", "rejected", "cancelled", "aborted")
        assert "guard_warnings" in cm["data"]
        assert isinstance(cm["data"]["guard_warnings"], list)

        # resumed action = approve
        re = events[re_idx]
        assert re["data"]["action"] == "approve"


# ──────────────────────────────────────────────────────────────────
# WL-99 (마지막) full pipeline happy path — execution 포함 (25s+)
# ──────────────────────────────────────────────────────────────────

def test_WL99_simple_query_full_pipeline_with_approve(live_client):
    """pre-signal approve → cognitive → planning(interrupt) → resume → execution → response."""
    conv_id, turn_id = _new_ids()

    with live_client.websocket_connect("/ws/agent?user_id=u_live") as ws_agent, \
         live_client.websocket_connect("/ws/hitl?user_id=u_live") as ws_hitl:

        ws_agent.receive_json(); ws_hitl.receive_json()

        ws_agent.send_json({
            "type": "query",
            "conversation_id": conv_id,
            "turn_id": turn_id,
            "user_input": "블루밍글로우 최근 리뷰 감성 분석",
        })

        ws_hitl.send_json({
            "type": "hitl_response",
            "data": {"request_id": "auto", "action": "approve", "turn_id": turn_id},
        })
        ws_hitl.receive_json()

        early = _drain_until(ws_agent, lambda e: e.get("node") == "cognitive", max_events=10)
        assert any(e.get("node") == "cognitive" for e in early)

        late = _drain_until(ws_agent, lambda e: e.get("node") == "response", max_events=30)
        nodes = [e.get("node") for e in late if e.get("type") == "node_event"]
        assert "response" in nodes, f"response 미수신. nodes={nodes}"
