"""Sprint 14 A1 — 그룹 G: E2E Live (4건)

명세: docs/_claude/sprint14_a1_hitl_timeout_plan.md §R2 그룹 G

전제:
  - .env OPENAI_API_KEY
  - PostgreSQL 실행 중 + CHECKPOINT_DB_URI 유효
  - .env HITL_RESUME_TIMEOUT_SEC=10 (테스트용 임시값)

실행 — 각 테스트 **개별 실행** (TestClient 한계, Sprint 13 WL-01~06 동일):
  uv run pytest backend/tests/sprint14/test_hitl_timeout_e2e_live.py::test_HTL01_... -v -m live
  uv run pytest backend/tests/sprint14/test_hitl_timeout_e2e_live.py::test_HTL02_... -v -m live
  uv run pytest backend/tests/sprint14/test_hitl_timeout_e2e_live.py::test_HTL03_... -v -m live
  uv run pytest backend/tests/sprint14/test_hitl_timeout_e2e_live.py::test_HTL04_... -v -m live
"""

import concurrent.futures
import time
import uuid

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.live


def _recv_timeout(ws, timeout=30):
    """receive_json with thread-based timeout. timeout 시 None 반환."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        f = ex.submit(ws.receive_json)
        try:
            return f.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return None


@pytest.fixture
def live_client():
    """실제 lifespan 활성화 (sprint13 패턴 재사용)."""
    from api_v2.main import app
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def reset_singletons():
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
    if hasattr(h, "_active_turns"):
        h._active_turns.clear()
    time.sleep(1.0)
    yield
    concurrency._reset_for_test()
    conn_manager._connections.clear()
    time.sleep(1.0)


def _new_ids():
    return f"conv_{uuid.uuid4().hex[:8]}", f"turn_{uuid.uuid4().hex[:8]}"


def _drain_until(ws, predicate, timeout_each=30, max_events=40):
    """이벤트 수집. predicate True 시 break. 각 이벤트 최대 timeout_each 초 대기."""
    events = []
    for _ in range(max_events):
        evt = _recv_timeout(ws, timeout=timeout_each)
        if evt is None:
            break
        events.append(evt)
        if predicate(evt):
            break
    return events


def _get_timeout_sec():
    """현재 .env 의 HITL_RESUME_TIMEOUT_SEC. 테스트 대기 시간 계산용."""
    from app.core.config import settings
    return settings.HITL_RESUME_TIMEOUT_SEC


# ──────────────────────────────────────────────────────────────────
# HTL-01 ⭐ — plan_review timeout → 실 Checkpoint 종결 (G-1 진짜)
# ──────────────────────────────────────────────────────────────────

def test_HTL01_plan_review_timeout_real_checkpoint_terminal(live_client):
    """
    1. query 전송 → cognitive → planning interrupt(plan_review)
    2. hitl_response 전송 안 함 → HITL_RESUME_TIMEOUT_SEC 초과
    3. complete(aborted, hitl_timeout) 수신
    4. graph.aget_state(config) 로 Checkpoint 상태 확인:
       - gs.next == () AND 모든 tasks[].interrupts == []
    """
    timeout_sec = _get_timeout_sec()
    assert timeout_sec <= 15, f"HITL_RESUME_TIMEOUT_SEC={timeout_sec} 테스트용 낮은 값 권장 (.env 확인)"

    conv_id, turn_id = _new_ids()

    with live_client.websocket_connect("/ws/agent?user_id=u_live") as ws_agent:
        ws_agent.receive_json()  # connected

        ws_agent.send_json({
            "type": "query",
            "conversation_id": conv_id,
            "turn_id": turn_id,
            "user_input": "블루밍글로우 리뷰 분석",
        })

        # hitl_request 수신까지 기다림 (cognitive + planning 시간)
        events = _drain_until(
            ws_agent,
            lambda e: e.get("type") == "hitl_request",
            timeout_each=30, max_events=30,
        )
        assert any(e.get("type") == "hitl_request" for e in events), \
            f"hitl_request 미수신. events={[e.get('type') for e in events]}"

        # hitl_response 전송 **안 함** → timeout 대기
        # 타임아웃 + 버퍼 충분히 대기하며 complete 수신
        wait_budget = timeout_sec + 10
        events_after = _drain_until(
            ws_agent,
            lambda e: e.get("type") == "complete",
            timeout_each=wait_budget, max_events=5,
        )

        complete_events = [e for e in events_after if e.get("type") == "complete"]
        assert len(complete_events) == 1, f"complete 1회 기대. after={[e.get('type') for e in events_after]}"
        c = complete_events[0]
        assert c["data"]["status"] == "aborted", f"status={c['data']}"
        assert c["data"]["reason"] == "hitl_timeout"

    # 실 Checkpoint 상태 확인 (G-1 Critical)
    # TestClient 닫힌 후에도 Checkpointer DB 는 살아있음
    import asyncio
    from api_v2.main import app
    from api_v2.thread_id import make_thread_id

    async def _check_checkpoint():
        agent = app.state.graph  # lifespan 에서 set 된 compiled graph
        thread_id = make_thread_id(conv_id, turn_id)
        gs = await agent.aget_state({"configurable": {"thread_id": thread_id}})
        return gs

    gs = asyncio.run(_check_checkpoint())
    assert gs.next == (), f"Checkpoint 재진입 가능 상태: gs.next={gs.next}"
    # 모든 tasks 에 interrupts 없음 (pending_interrupts 소진)
    for task in getattr(gs, "tasks", []):
        assert not getattr(task, "interrupts", []), (
            f"잔존 interrupt: task={task}"
        )


# ──────────────────────────────────────────────────────────────────
# HTL-02 ⭐ — execution_pause timeout → 실 Checkpoint 종결
# ──────────────────────────────────────────────────────────────────

def test_HTL02_execution_pause_timeout_real_checkpoint_terminal(live_client):
    """
    1. pause 신호 **pre-signal** (query 전 _paused 플래그 세팅)
       주의: register_turn 이 run_turn 에서 호출되므로, pre-signal 시점에는 _active_turns 에 없음
             → ws_hitl 가드가 거부됨. 그래서 직접 hitl_manager 에 접근하는 경로 사용.
    2. query 전송 → cognitive → planning interrupt(plan_review)
    3. auto-approve 동작 (is_paused=True) → 즉시 approve 주입 → execution 시작
    4. execution phase 1 끝나면 should_continue → "pause" → interrupt(execution_pause)
    5. resume 전송 안 함 → timeout
    6. complete(aborted, hitl_timeout) 수신 + Checkpoint 종결 확인

    주의: execution 은 실제 tool 실행 (review_collector 등) — 시간 30~60s 소요 가능
    """
    timeout_sec = _get_timeout_sec()
    assert timeout_sec <= 15, f"HITL_RESUME_TIMEOUT_SEC={timeout_sec} 낮은 값 권장"

    conv_id, turn_id = _new_ids()

    # 사전 pause 설정 — ws_hitl 가드 우회 (register_turn 전이므로 hitl manager 직접 조작)
    from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager
    hitl = get_hitl_manager()

    with live_client.websocket_connect("/ws/agent?user_id=u_live2") as ws_agent:
        ws_agent.receive_json()

        # 직접 _paused 플래그 세팅 — run_turn 진입 후 auto-approve 트리거
        hitl._paused.add(turn_id)

        ws_agent.send_json({
            "type": "query",
            "conversation_id": conv_id,
            "turn_id": turn_id,
            "user_input": "블루밍글로우 리뷰 분석",
        })

        # paused 이벤트 수신까지 기다림 (cognitive + planning + auto-approve + execution phase 1)
        events = _drain_until(
            ws_agent,
            lambda e: e.get("type") == "paused",
            timeout_each=60, max_events=100,
        )
        assert any(e.get("type") == "paused" for e in events), \
            f"paused 이벤트 미수신. types={[e.get('type') for e in events]}"

        # resume 전송 안 함 → timeout
        wait_budget = timeout_sec + 15
        events_after = _drain_until(
            ws_agent,
            lambda e: e.get("type") == "complete",
            timeout_each=wait_budget, max_events=10,
        )
        complete_events = [e for e in events_after if e.get("type") == "complete"]
        assert len(complete_events) == 1
        c = complete_events[0]
        assert c["data"]["status"] == "aborted"
        assert c["data"]["reason"] == "hitl_timeout"

    # 실 Checkpoint 종결 확인
    import asyncio
    from api_v2.main import app
    from api_v2.thread_id import make_thread_id

    async def _check():
        agent = app.state.graph
        thread_id = make_thread_id(conv_id, turn_id)
        gs = await agent.aget_state({"configurable": {"thread_id": thread_id}})
        return gs

    gs = asyncio.run(_check())
    assert gs.next == ()
    for task in getattr(gs, "tasks", []):
        assert not getattr(task, "interrupts", [])


# ──────────────────────────────────────────────────────────────────
# HTL-03 — timeout 된 turn 에 resume_query → INVALID_MESSAGE
# ──────────────────────────────────────────────────────────────────

def test_HTL03_resume_query_on_real_timeouted_turn_invalid_message(live_client):
    """HTL-01 과 동일 flow 로 aborted turn 만들고, 같은 turn_id 로 resume_query 재전송."""
    timeout_sec = _get_timeout_sec()
    assert timeout_sec <= 15

    conv_id, turn_id = _new_ids()

    # Phase 1 — timeout aborted 상태 만들기
    with live_client.websocket_connect("/ws/agent?user_id=u_live3") as ws_agent:
        ws_agent.receive_json()
        ws_agent.send_json({
            "type": "query",
            "conversation_id": conv_id,
            "turn_id": turn_id,
            "user_input": "블루밍글로우 리뷰 분석",
        })
        _drain_until(ws_agent, lambda e: e.get("type") == "hitl_request",
                     timeout_each=30, max_events=30)
        events_after = _drain_until(
            ws_agent, lambda e: e.get("type") == "complete",
            timeout_each=timeout_sec + 10, max_events=5,
        )
        assert any(e.get("type") == "complete" for e in events_after)

    # Phase 2 — 새 WS 연결에서 같은 turn_id 로 resume_query
    time.sleep(1.0)
    with live_client.websocket_connect("/ws/agent?user_id=u_live3") as ws_agent:
        ws_agent.receive_json()
        ws_agent.send_json({
            "type": "resume_query",
            "conversation_id": conv_id,
            "turn_id": turn_id,
        })
        events = _drain_until(
            ws_agent,
            lambda e: e.get("type") == "error",
            timeout_each=15, max_events=10,
        )
        errors = [e for e in events if e.get("type") == "error"]
        assert len(errors) >= 1, f"INVALID_MESSAGE 미수신. events={events}"
        assert errors[0].get("code") == "INVALID_MESSAGE"


# ──────────────────────────────────────────────────────────────────
# HTL-04 — timeout 후 pause/resume/cancel 3종 → turn_not_active ack
# ──────────────────────────────────────────────────────────────────

def test_HTL04_pause_resume_cancel_guards_on_timeouted_turn(live_client):
    """HTL-01 후 3종 요청 각각 → accepted:False, reason:turn_not_active."""
    timeout_sec = _get_timeout_sec()
    assert timeout_sec <= 15

    conv_id, turn_id = _new_ids()

    # Phase 1 — timeout aborted 만들기
    with live_client.websocket_connect("/ws/agent?user_id=u_live4") as ws_agent:
        ws_agent.receive_json()
        ws_agent.send_json({
            "type": "query",
            "conversation_id": conv_id,
            "turn_id": turn_id,
            "user_input": "블루밍글로우 리뷰 분석",
        })
        _drain_until(ws_agent, lambda e: e.get("type") == "hitl_request",
                     timeout_each=30, max_events=30)
        _drain_until(ws_agent, lambda e: e.get("type") == "complete",
                     timeout_each=timeout_sec + 10, max_events=5)

    # Phase 2 — 3종 요청 각각 검증
    time.sleep(1.0)
    acks = []
    for action in ["pause", "resume", "cancel"]:
        with live_client.websocket_connect("/ws/hitl?user_id=u_live4") as ws_hitl:
            ws_hitl.receive_json()  # connected
            ws_hitl.send_json({
                "type": action,
                "data": {"turn_id": turn_id},
            })
            ack = _recv_timeout(ws_hitl, timeout=5)
            acks.append((action, ack))

    for action, ack in acks:
        assert ack is not None, f"{action} ack 미수신"
        assert ack.get("type") == "hitl_ack", f"{action}: type={ack.get('type')}"
        assert ack["data"]["accepted"] is False, f"{action}: {ack['data']}"
        assert ack["data"]["reason"] == "turn_not_active", f"{action}: {ack['data']}"
