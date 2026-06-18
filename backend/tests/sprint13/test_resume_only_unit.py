"""R-9 resume_only 경로 Unit 테스트 (사전 검증).

목적: 서버 재시작 복원 흐름의 백엔드 경로를 수정 전에 검증 가능한지 확인.
  - _graph_runner_with_resume(payload={"resume_only": True}) 가 초기 astream skip
    + resume 루프 직행 → pending interrupt 감지 시 paused/hitl_request 재emit
  - pending 없으면 INVALID_MESSAGE fatal 반환 + 조기 return

테스트 케이스:
  RO-01  resume_only=True + pending 없음 → INVALID_MESSAGE + astream 미호출
  RO-02  resume_only=True + pending execution_pause → 초기 astream skip + paused emit
  RO-03  resume_only=True + pending plan_review → 초기 astream skip + hitl_request emit
  RO-04  resume_only=True + pause → resume(continue) → complete(success) 전체 플로우
  RO-05  resume_only=True + pause → cancel → complete(cancelled)
  RO-06  resume_only=True + plan_review → reject → complete(rejected)
  RO-07  resume_only=False (기본) → 초기 astream 정상 호출 (regression)
  RO-08  resume_only=True + execution_pause with progress → restore_progress 호출
  RO-09  resume_only=True + plan_review + hitl.is_paused → auto-approve 동작
"""

from __future__ import annotations

import pytest


# ───────── Mock infrastructure (IR 테스트와 같은 패턴) ─────────

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
    def __init__(self, pending, intr_value=None):
        self.next = ("some_node",) if pending else ()
        if pending and intr_value is not None:
            self.tasks = [_MockTask([_MockInterrupt(intr_value)])]
        else:
            self.tasks = []


class MockAgent:
    """astream 호출 추적 + pending_sequence 기반 aget_state.

    received_state: 1차 astream 호출 시 state 객체 저장 (resume_only 검증용)
    resume_values: Command(resume=...) 로 들어온 값들
    stream_index: astream 호출 횟수
    aget_index: aget_state 호출 횟수
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
            # dict state 1차 호출
            self.received_state = state_or_cmd
        idx = self.stream_index
        self.stream_index += 1
        if idx >= len(self.streams):
            return
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


def _types(sent_list):
    return [s.get("type") for s in sent_list]


# ══════════════════════════════════════════════════════════════════
# RO-01 resume_only=True + pending 없음 → INVALID_MESSAGE + no astream
# ══════════════════════════════════════════════════════════════════

async def test_RO01_resume_only_no_pending_emits_invalid(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    agent = MockAgent(
        streams=[],
        pending_sequence=[False],   # aget_state 1회, pending=False
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1",
        {"resume_only": True},
        _agent=agent,
    )

    # 초기 astream skip + resume 루프에서 pending 없음 감지 → error + return
    assert agent.stream_index == 0, "resume_only=True 에서 초기 astream 호출돼선 안됨"
    assert agent.received_state is None, "received_state 가 None 이어야 함"

    errs = [s for s in mock_ws_u1.sent if s.get("type") == "error"]
    assert len(errs) == 1, f"error 이벤트 1개 예상 (실제 {len(errs)})"
    assert errs[0]["code"] == "INVALID_MESSAGE"
    assert errs[0]["severity"] == "fatal"
    # complete 이벤트는 emit되지 않음 (조기 return)
    completes = [s for s in mock_ws_u1.sent if s.get("type") == "complete"]
    assert len(completes) == 0


# ══════════════════════════════════════════════════════════════════
# RO-02 resume_only=True + pending execution_pause → skip astream + paused emit
# ══════════════════════════════════════════════════════════════════

async def test_RO02_resume_only_pending_execution_pause_emits_paused(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    # 사용자가 이 테스트 내에서 resume 신호 보내기 위해 Queue 에 미리 넣어둠
    fresh_hitl.signal_resume("t1", {"action": "continue"})

    agent = MockAgent(
        streams=[[{"unk_after_resume": {}}]],   # resume 후 astream 1회
        pending_sequence=[True, False],
        intr_values=[{
            "type": "execution_pause",
            "progress": {
                "plan": {"todos": [{"id": "a"}, {"id": "b"}]},
                "completed_todos": {"a": {}},
                "current_phase": 1,
            },
        }],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1",
        {"resume_only": True},
        _agent=agent,
    )

    # 1차 astream skip 검증: received_state 는 None (초기 입력 안 들어감)
    assert agent.received_state is None
    # resume 루프의 astream (LGCommand) 는 1회 호출 (continue 처리)
    assert agent.stream_index == 1
    assert agent.resume_values == [{"action": "continue"}]

    # paused 이벤트 emit 확인
    paused = [s for s in mock_ws_u1.sent if s.get("type") == "paused"]
    assert len(paused) == 1
    assert paused[0]["turn_id"] == "t1"
    assert paused[0]["data"]["total"] == 2
    assert paused[0]["data"]["current_phase"] == 1

    # resumed + complete 도 나옴 (정상 재개)
    assert "resumed" in _types(mock_ws_u1.sent)
    assert _types(mock_ws_u1.sent)[-1] == "complete"


# ══════════════════════════════════════════════════════════════════
# RO-03 resume_only=True + pending plan_review → skip astream + hitl_request emit
# ══════════════════════════════════════════════════════════════════

async def test_RO03_resume_only_pending_plan_review_emits_hitl_request(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    fresh_hitl.signal_resume("t1", {"action": "approve"})

    agent = MockAgent(
        streams=[[{"unk_after_approve": {}}]],
        pending_sequence=[True, False],
        intr_values=[{
            "type": "plan_review",
            "plan": {"todos": [{"id": "t1"}], "teams_selected": ["x"]},
            "message": "approve?",
        }],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1",
        {"resume_only": True},
        _agent=agent,
    )

    assert agent.received_state is None, "plan_review 복원 시에도 초기 astream skip"
    req = [s for s in mock_ws_u1.sent if s.get("type") == "hitl_request"]
    assert len(req) == 1
    assert req[0]["turn_id"] == "t1"
    assert "plan" in req[0]["data"]


# ══════════════════════════════════════════════════════════════════
# RO-04 전체 플로우 — resume_only=True → paused → continue → complete
# ══════════════════════════════════════════════════════════════════

async def test_RO04_resume_only_full_flow_to_complete(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    fresh_hitl.signal_resume("t1", {"action": "continue"})

    agent = MockAgent(
        streams=[[{"response": {"text": "done"}}]],
        pending_sequence=[True, False],
        intr_values=[{
            "type": "execution_pause",
            "progress": {"plan": {"todos": []}, "completed_todos": {}, "current_phase": 0},
        }],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1",
        {"resume_only": True},
        _agent=agent,
    )

    tps = _types(mock_ws_u1.sent)
    # 시퀀스: paused → resumed → node_event(response) → complete
    assert tps[0] == "paused"
    assert "resumed" in tps
    assert tps[-1] == "complete"
    completes = [s for s in mock_ws_u1.sent if s.get("type") == "complete"]
    assert completes[0]["data"]["status"] == "success"


# ══════════════════════════════════════════════════════════════════
# RO-05 resume_only=True + pause → cancel → complete(cancelled)
# ══════════════════════════════════════════════════════════════════

async def test_RO05_resume_only_then_cancel(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    fresh_hitl.signal_resume("t1", {"action": "cancel"})

    agent = MockAgent(
        streams=[],   # cancel silent drain — 빈 astream
        pending_sequence=[True],
        intr_values=[{
            "type": "execution_pause",
            "progress": {"plan": {"todos": []}, "completed_todos": {}, "current_phase": 0},
        }],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1",
        {"resume_only": True},
        _agent=agent,
    )

    completes = [s for s in mock_ws_u1.sent if s.get("type") == "complete"]
    assert len(completes) == 1
    assert completes[0]["data"]["status"] == "cancelled"


# ══════════════════════════════════════════════════════════════════
# RO-06 resume_only=True + plan_review → reject → complete(rejected)
# ══════════════════════════════════════════════════════════════════

async def test_RO06_resume_only_plan_review_reject(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    fresh_hitl.signal_resume("t1", {"action": "reject"})

    agent = MockAgent(
        streams=[],
        pending_sequence=[True],
        intr_values=[{
            "type": "plan_review",
            "plan": {"todos": [], "teams_selected": []},
            "message": "approve?",
        }],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1",
        {"resume_only": True},
        _agent=agent,
    )

    completes = [s for s in mock_ws_u1.sent if s.get("type") == "complete"]
    assert len(completes) == 1
    assert completes[0]["data"]["status"] == "rejected"


# ══════════════════════════════════════════════════════════════════
# RO-07 regression: resume_only=False (기본) → 초기 astream 호출됨
# ══════════════════════════════════════════════════════════════════

async def test_RO07_resume_only_false_initial_astream_runs(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    agent = MockAgent(
        streams=[[{"unk": {}}]],
        pending_sequence=[False],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1",
        {"user_input": "hello"},   # resume_only 없음
        _agent=agent,
    )

    # 초기 astream 호출됨 + state 가 dict 로 들어감
    assert agent.stream_index == 1
    assert agent.received_state is not None
    assert agent.received_state["user_input"] == "hello"

    # 정상 complete
    assert _types(mock_ws_u1.sent)[-1] == "complete"


# ══════════════════════════════════════════════════════════════════
# RO-08 resume_only=True + execution_pause progress → restore_progress 호출
# ══════════════════════════════════════════════════════════════════

async def test_RO08_resume_only_restores_progress(mock_ws_u1, fresh_hitl):
    from api_v2.ws_agent import _graph_runner_with_resume

    fresh_hitl.signal_resume("t1", {"action": "continue"})

    # 프로덕션 get_progress_snapshot 포맷 준수 (completed_results 키)
    progress_snap = {
        "plan": {"todos": [{"id": "a"}, {"id": "b"}, {"id": "c"}]},
        "completed_todos": ["a"],
        "completed_results": {"a": {"tool": "x", "status": "completed"}},
        "current_phase": 1,
        "status": "paused",
    }
    agent = MockAgent(
        streams=[[{"unk": {}}]],
        pending_sequence=[True, False],
        intr_values=[{"type": "execution_pause", "progress": progress_snap}],
    )
    # fresh_hitl 는 progress 가 없는 상태 — 복원되어야 함
    assert fresh_hitl.get_progress("t1") is None

    await _graph_runner_with_resume(
        "u1", "c1", "t1",
        {"resume_only": True},
        _agent=agent,
    )

    # restore_progress 호출로 싱글톤에 progress 가 등록되어야 함
    p = fresh_hitl.get_progress("t1")
    assert p is not None
    assert list(p.completed_todos.keys()) == ["a"]


# ══════════════════════════════════════════════════════════════════
# RO-09 resume_only=True + plan_review + hitl.is_paused → auto-approve
# ══════════════════════════════════════════════════════════════════

async def test_RO09_resume_only_plan_review_auto_approve_when_paused(mock_ws_u1, fresh_hitl):
    """복원 시점 before-plan-review pause 예약 상태 → auto-approve 동작."""
    from api_v2.ws_agent import _graph_runner_with_resume

    # pause 예약 상태 세팅 — 그러나 resume signal 도 Queue 에 넣어놓아야 뒤에서 종료
    fresh_hitl.request_pause("t1")
    fresh_hitl.signal_resume("t1", {"action": "continue"})

    agent = MockAgent(
        streams=[
            # aget_state[0] pending=plan_review → auto-approve 분기
            [{"unk_after_auto_approve": {}}],
            # aget_state[1] pending=execution_pause → paused emit → continue
            [{"unk_after_continue": {}}],
        ],
        pending_sequence=[True, True, False],
        intr_values=[
            {"type": "plan_review", "plan": {"todos": []}, "message": "x"},
            {"type": "execution_pause",
             "progress": {"plan": {"todos": []}, "completed_todos": {}, "current_phase": 0}},
        ],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1",
        {"resume_only": True},
        _agent=agent,
    )

    # auto-approve 분기를 탔다면 resume_values[0] == {"action":"approve"}
    assert agent.resume_values[0] == {"action": "approve"}
    # plan_review 용 hitl_request 는 emit 되지 않아야 함 (auto-approve 는 이벤트 없음)
    reqs = [s for s in mock_ws_u1.sent if s.get("type") == "hitl_request"]
    assert len(reqs) == 0
    # 다음 interrupt 인 execution_pause 의 paused 는 emit
    assert "paused" in _types(mock_ws_u1.sent)


# ══════════════════════════════════════════════════════════════════
# RO-10 resume_only 첫 iter 에서만 pending 검사 (regression guard for B-0)
# ══════════════════════════════════════════════════════════════════

async def test_RO10_resume_only_only_first_iter_checks_pending(mock_ws_u1, fresh_hitl):
    """B-0 회귀 방지: first_iter 에서 interrupt 처리 후,
    둘째/셋째 iter 에서 pending=False 일 때 resume_only 분기로 잘못 들어가면 안됨.
    """
    from api_v2.ws_agent import _graph_runner_with_resume

    fresh_hitl.signal_resume("t1", {"action": "continue"})

    agent = MockAgent(
        streams=[[{"unk": {}}]],
        pending_sequence=[True, False],
        intr_values=[{
            "type": "execution_pause",
            "progress": {"plan": {"todos": []}, "completed_todos": {}, "current_phase": 0},
        }],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1",
        {"resume_only": True},
        _agent=agent,
    )

    # error 이벤트는 0개여야 함 (resume_only 분기가 재진입하지 않음)
    errs = [s for s in mock_ws_u1.sent if s.get("type") == "error"]
    assert len(errs) == 0, f"resume_only가 둘째 iter에 잘못 진입 — error {errs}"
    # 정상 complete
    assert _types(mock_ws_u1.sent)[-1] == "complete"


# ══════════════════════════════════════════════════════════════════
# RO-11 resume_only 연속 2회 호출 — CallbackManager 중복 등록 위험 검증
# ══════════════════════════════════════════════════════════════════

async def test_RO11_resume_only_double_call_callback_register(fresh_hitl):
    """CallbackManager.register 가 append 기반 — 같은 turn_id 로 2회 호출 시
    callback 2개 쌓여서 event 중복 fan-out 될 수 있음.

    이 테스트는 현재 동작을 '문서화' (dedup 없음) — 중복 있으면 FAIL 아님, 경고로 파악.
    브라우저 재연결 2회 시 UI 이벤트 중복 위험 표면화.
    """
    from api_v2.ws_agent import _graph_runner_with_resume
    from app.dream_agent.workflow_managers.callback_manager import get_callback_manager
    cbm = get_callback_manager()
    cbm._listeners.clear()

    fresh_hitl.signal_resume("t1", {"action": "continue"})
    fresh_hitl.signal_resume("t1", {"action": "continue"})   # 2회 호출 대비

    async def run_once():
        agent = MockAgent(
            streams=[[{"unk": {}}]],
            pending_sequence=[True, False],
            intr_values=[{
                "type": "execution_pause",
                "progress": {"plan": {"todos": []}, "completed_todos": {}, "current_phase": 0},
            }],
        )
        await _graph_runner_with_resume(
            "u1", "c1", "t1", {"resume_only": True}, _agent=agent,
        )

    await run_once()
    # 첫 호출 완료 후 unregister 됐는지 확인 — 현재 코드는 _graph_runner_with_resume 에서
    # unregister 하지 않음 (run_turn.finally 에서만 함)
    listeners_after_first = len(cbm._listeners.get("t1", []))

    await run_once()
    listeners_after_second = len(cbm._listeners.get("t1", []))

    # 수정 후 기대: unregister-then-register 패턴으로 listener 는 항상 1개 유지
    print(f"[RO-11 결과] 1회 후 listener={listeners_after_first}, 2회 후={listeners_after_second}")
    assert listeners_after_first == 1, "1회 호출 후 listener 1개여야 함"
    assert listeners_after_second == 1, "2회 호출 후에도 listener 1개 — 중복 누적 방지"


# ══════════════════════════════════════════════════════════════════
# RO-12 resume_only=True + execution_pause + 이미 progress 존재 → restore 재호출 안함
# ══════════════════════════════════════════════════════════════════

async def test_RO12_resume_only_keeps_existing_progress(mock_ws_u1, fresh_hitl):
    """싱글톤에 이미 progress 있으면 restore_progress 호출 안 되어야 함 (값 보존)."""
    from api_v2.ws_agent import _graph_runner_with_resume

    # 미리 progress 세팅
    fresh_hitl.restore_progress("t1", {
        "plan": {"todos": [{"id": "a"}, {"id": "b"}]},
        "completed_results": {"a": {"status": "ok", "preexisting": True}},
        "current_phase": 1,
        "status": "paused",
    })
    preexisting_progress = fresh_hitl.get_progress("t1")
    assert "a" in preexisting_progress.completed_todos

    fresh_hitl.signal_resume("t1", {"action": "continue"})

    # Checkpoint payload는 완전히 다른 내용
    agent = MockAgent(
        streams=[[{"unk": {}}]],
        pending_sequence=[True, False],
        intr_values=[{
            "type": "execution_pause",
            "progress": {
                "plan": {"todos": [{"id": "z"}]},
                "completed_results": {"z": {"status": "different"}},
                "current_phase": 99,
                "status": "running",
            },
        }],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1",
        {"resume_only": True},
        _agent=agent,
    )

    # 기존 progress 가 유지되어야 (restore_progress 재호출 안됨)
    p = fresh_hitl.get_progress("t1")
    assert "a" in p.completed_todos, "기존 progress의 'a'가 유지되어야 함"
    assert "z" not in p.completed_todos, "Checkpoint의 'z'로 덮어쓰지 않아야 함"


# ══════════════════════════════════════════════════════════════════
# RO-13 resume_only=True + plan_review + action=modify → modified plan 적용
# ══════════════════════════════════════════════════════════════════

async def test_RO13_resume_only_plan_review_modify(mock_ws_u1, fresh_hitl):
    """plan_review 복원 상태에서 사용자가 modify 액션 전송 — 정상 처리."""
    from api_v2.ws_agent import _graph_runner_with_resume

    modified_plan = {"todos": [{"id": "new_todo"}], "teams_selected": ["m"]}
    fresh_hitl.signal_resume("t1", {"action": "modify", "value": modified_plan})

    agent = MockAgent(
        streams=[[{"response": {"text": "after modify"}}]],
        pending_sequence=[True, False],
        intr_values=[{
            "type": "plan_review",
            "plan": {"todos": [{"id": "old"}], "teams_selected": ["o"]},
            "message": "approve?",
        }],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1",
        {"resume_only": True},
        _agent=agent,
    )

    # agent.resume_values 에 modify action 이 들어갔는지 확인
    assert agent.resume_values == [{"action": "modify", "value": modified_plan}]
    assert _types(mock_ws_u1.sent)[-1] == "complete"
