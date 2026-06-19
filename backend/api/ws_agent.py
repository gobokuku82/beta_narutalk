"""WebSocket 스트림 엔드포인트.

명세 §2 `/ws/agent`:
- user_id 쿼리 받음 (POC: demo 기본값)
- 클라에서 `{"type":"query", ...}` 수신 (Sprint 13+ 신 경로) / `resume_query` / `ping`
- conversation_id + turn_id 클라 생성 (UUID)
- 이벤트: connected / node_event / layer_* / hitl_request / paused / resumed / complete / error

Sprint 5: 4-Layer v2 그래프 전환 (Cognitive→Planning→Execution→Response, StructuredQuery 기반).
Sprint 13 I10: query/resume_query 경로 + ConnectionManager fan-out.
작업 ⑬ (2026-05-31): legacy 'start' 분기 + _run_agent 폐기 (frontend type:'start' 0 hit).
"""

from __future__ import annotations

import asyncio
import json
import math
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.dream_agent.system_graph.builder import build_graph

router = APIRouter()
logger = get_logger(__name__)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_safe(obj):
    """재귀적으로 JSON 직렬화 가능한 형태로 변환.

    pandas NaN/Infinity는 표준 JSON이 아니므로 None으로 치환 (브라우저 JSON.parse 호환).
    """
    if obj is None:
        return None
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, (str, int)):
        return obj
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_json_safe(item) for item in obj]
    if hasattr(obj, "model_dump"):
        try:
            return _json_safe(obj.model_dump(mode="json"))
        except Exception:
            pass
    return str(obj)


async def _safe_send(websocket: WebSocket, message: dict) -> None:
    """NaN-safe 송신. allow_nan=False로 엄격 JSON (브라우저 호환)."""
    safe_message = _json_safe(message)
    text = json.dumps(safe_message, ensure_ascii=False, allow_nan=False)
    await websocket.send_text(text)


def _chunk_to_event(chunk: dict, conversation_id: str, turn_id: str) -> dict | None:
    """LangGraph astream chunk → WS 이벤트 (Sprint 13 I10c + I11-a).

    chunk 형태:
        - 노드: {"cognitive": {...update...}}
        - interrupt: {"__interrupt__": [Interrupt(value=...)]}
        - 종료: {"__end__": ...}
        - 빈 dict: {}

    Returns:
        - 노드 → {"type": "node_event", "node", "conversation_id", "turn_id", "data"}
        - __interrupt__ / __end__ → None (I11-a: __end__ 필터 추가)
        - 빈 → None
    """
    if not chunk:
        return None
    for node_name, node_state in chunk.items():
        if node_name in ("__interrupt__", "__end__"):
            return None
        return {
            "type": "node_event",
            "node": node_name,
            "conversation_id": conversation_id,
            "turn_id": turn_id,
            "data": _json_safe(node_state),
        }
    return None


def _extract_interrupt_value(graph_state) -> dict:
    """LangGraph state의 pending interrupt payload 추출 (Sprint 13 I11-a).

    Sprint 12 _run_agent L493~502 포팅.

    Returns:
        첫 번째 interrupt의 value (dict). 없으면 빈 dict.
    """
    if not graph_state.tasks:
        return {}
    for task in graph_state.tasks:
        if hasattr(task, "interrupts") and task.interrupts:
            val = task.interrupts[0].value
            if isinstance(val, dict):
                return val
    return {}


def _build_hitl_request_data(intr_value: dict, final_state: dict) -> dict:
    """hitl_request 이벤트 payload 구성 (Sprint 12 포맷 호환)."""
    plan = intr_value.get("plan") or final_state.get("plan") or {}
    todo_count = len(plan.get("todos", []))
    default_msg = f"{todo_count}개 Todo 실행 계획이 생성되었습니다. 승인하시겠습니까?"
    return {
        "request_id": f"req_{uuid.uuid4().hex[:8]}",
        "plan": _json_safe(plan),
        "options": ["approve", "reject", "modify"],
        "message": intr_value.get("message") or default_msg,
    }


def _build_paused_data(intr_value: dict) -> dict:
    """paused 이벤트 payload (Sprint 12 L451~462 포맷 호환)."""
    progress = intr_value.get("progress") or {}
    plan_todos = progress.get("plan", {}).get("todos", []) if isinstance(progress.get("plan"), dict) else []
    completed_raw = progress.get("completed_todos", {})
    completed_list = (
        list(completed_raw.keys()) if isinstance(completed_raw, dict)
        else completed_raw if isinstance(completed_raw, list)
        else []
    )
    return {
        "request_id": f"req_{uuid.uuid4().hex[:8]}",
        "completed": completed_list,
        "total": len(plan_todos),
        "current_phase": progress.get("current_phase", 0),
        "progress": _json_safe(progress),
    }


async def _graph_runner(
    user_id: str,
    conv_id: str,
    turn_id: str,
    payload: dict,
    *,
    _agent=None,
) -> None:
    """graph astream 1차 실행 + chunk broadcast (Sprint 13 I10c).

    run_turn의 _runner로 주입되는 함수.
    I10c 범위: 1차 astream만. Interrupt resume 루프는 I10d.
    """
    from api.connection_manager import conn_manager
    from api.thread_id import make_thread_id
    from app.dream_agent.states.agent_state import init_agent_state

    # state 빌드 (Sprint 13 필드 포함)
    state = init_agent_state(
        user_input=payload.get("user_input", ""),
        conversation_id=conv_id,
        turn_id=turn_id,
        user_id=user_id,
        client_id=payload.get("client_id"),
        language=payload.get("language", "ko"),
        conversation_history=payload.get("conversation_history"),
        history_limit=payload.get("history_limit"),
        require_review=payload.get("require_review"),
    )
    thread_id = make_thread_id(conv_id, turn_id)
    config = {"configurable": {"thread_id": thread_id}}

    agent = _agent if _agent is not None else _get_graph()
    async for chunk in agent.astream(state, config=config):
        event = _chunk_to_event(chunk, conv_id, turn_id)
        if event:
            await conn_manager.broadcast_to_user(user_id, "agent", event)


def _has_pending_interrupts(gs) -> bool:
    """LangGraph state에 pending interrupt가 있는지 판별 (Sprint 13 I10d).

    .next가 비어있어도 tasks[].interrupts가 있으면 처리 필요.
    """
    if getattr(gs, "next", None):
        return True
    tasks = getattr(gs, "tasks", None)
    if tasks:
        for t in tasks:
            if getattr(t, "interrupts", None):
                return True
    return False


async def _graph_runner_with_resume(
    user_id: str,
    conv_id: str,
    turn_id: str,
    payload: dict,
    *,
    _agent=None,
    _app=None,
) -> None:
    """graph astream + interrupt resume 루프 + layer guard + 이벤트 보강 (Sprint 13 I11-a).

    emit 이벤트:
      - node_event (각 노드 완료 시)
      - error (layer guard fatal/warning)
      - hitl_request (plan_review interrupt)
      - paused (execution_pause interrupt)
      - resumed (wait_for_resume 반환)
      - complete (정상 종료 / rejected / cancelled / aborted)

    I11-a 추가:
      - layer_guard.inspect_layer_output + append_guard_log
      - auto-approve (pause 예약 상태에서 plan_review 자동 승인)
      - reject 조기 종료
      - restore_progress (서버 재시작 대응)
    """
    from api.connection_manager import conn_manager
    from app.dream_agent.system_graph.layer_inspector import (
        append_guard_log, inspect_layer_output, summarize_state,
    )
    from api.thread_id import make_thread_id
    from app.dream_agent.states.agent_state import init_agent_state
    from app.dream_agent.workflow_managers.callback_manager import get_callback_manager
    from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager
    from langgraph.types import Command as LGCommand

    state = init_agent_state(
        user_input=payload.get("user_input", ""),
        conversation_id=conv_id,
        turn_id=turn_id,
        user_id=user_id,
        client_id=payload.get("client_id"),
        language=payload.get("language", "ko"),
        conversation_history=payload.get("conversation_history"),
        history_limit=payload.get("history_limit"),
        require_review=payload.get("require_review"),
    )
    thread_id = make_thread_id(conv_id, turn_id)
    config = {"configurable": {"thread_id": thread_id}}

    agent = _agent if _agent is not None else _get_graph(app=_app)
    hitl = get_hitl_manager()

    # resume_only: 서버 재시작 복원 시 초기 astream skip → resume 루프로 직행
    resume_only = bool(payload.get("resume_only"))

    final_state: dict = {}
    guard_warnings: list[dict] = []

    # CallbackManager bridge 등록 (Sprint 13 I11-b2 fix):
    # execution_stage가 emit하는 todo_start/todo_complete/progress/layer_start 이벤트를
    # conn_manager로 fan-out. session_id == turn_id (alias). turn_id 키로 등록.
    cb_manager = get_callback_manager()

    async def _callback_bridge(evt: dict) -> None:
        # conv_id/turn_id 보강 + dashboard conv 필터 통과 위해 필드 주입
        enriched = dict(evt)
        enriched.setdefault("conversation_id", conv_id)
        enriched.setdefault("turn_id", turn_id)
        try:
            await conn_manager.broadcast_to_user(user_id, "agent", enriched)
        except Exception as e:
            logger.exception("callback bridge failed", turn_id=turn_id, error=str(e))

    # 중복 register 방지 (R-9 리스크 RO-11): 같은 turn_id로 재진입 시
    # 이전 listener 제거 후 새로 등록 — 이벤트 중복 fan-out 차단
    cb_manager.unregister(turn_id)
    cb_manager.register(turn_id, _callback_bridge)

    async def _emit_complete(status: str, *, reason: str | None = None) -> None:
        data = {"status": status, "guard_warnings": guard_warnings}
        if reason:
            data["reason"] = reason
        if status == "success":
            data.update({
                "response": final_state.get("response", {}),
                "execution_result": final_state.get("execution_result", {}),
                "structured_query": final_state.get("structured_query", {}),
                "plan": final_state.get("plan", {}),
            })
        elif status == "rejected":
            data["message"] = "실행 계획이 거부되었습니다."
        await conn_manager.broadcast_to_user(user_id, "agent", {
            "type": "complete",
            "conversation_id": conv_id,
            "turn_id": turn_id,
            "data": _json_safe(data),
        })

    async def _broadcast_chunks(stream) -> str | None:
        """astream 소비 + node_event + layer guard. abort 시 code 반환."""
        async for chunk in stream:
            event = _chunk_to_event(chunk, conv_id, turn_id)
            if not event:
                continue
            await conn_manager.broadcast_to_user(user_id, "agent", event)
            for _, node_state in chunk.items():
                if isinstance(node_state, dict):
                    final_state.update(node_state)

            errs = inspect_layer_output(event["node"], event["data"] or {})
            abort_code: str | None = None
            for err in errs:
                err_event = {
                    "type": "error",
                    "code": err["code"],
                    "layer": err["layer"],
                    "severity": err["severity"],
                    "message": err["message"],
                    "detail": err.get("detail", {}),
                    "conversation_id": conv_id,
                    "turn_id": turn_id,
                }
                await conn_manager.broadcast_to_user(user_id, "agent", err_event)
                append_guard_log({
                    "ts": _iso_now(),
                    "conv_id": conv_id, "turn_id": turn_id, "user_id": user_id,
                    **err,
                    "state_summary": summarize_state(final_state),
                })
                if err["severity"] == "fatal":
                    abort_code = err["code"]
                else:
                    guard_warnings.append({
                        "layer": err["layer"], "code": err["code"],
                    })
            if abort_code:
                return abort_code
        return None

    # 1차 astream (resume_only=True 면 skip — Checkpoint 복원 경로)
    if not resume_only:
        abort_reason = await _broadcast_chunks(agent.astream(state, config=config))
        if abort_reason:
            await _emit_complete("aborted", reason=abort_reason)
            return

    # resume loop
    first_iter = True
    while True:
        gs = await agent.aget_state(config)
        if not _has_pending_interrupts(gs):
            if resume_only and first_iter:
                # 복원 요청했는데 pending interrupt 없음 — 이미 끝났거나 thread_id 오류
                logger.warning("resume_query: no pending interrupt", turn_id=turn_id)
                from app.core.error_codes import ErrorCodes
                await conn_manager.broadcast_to_user(user_id, "agent", {
                    "type": "error",
                    **ErrorCodes.INVALID_MESSAGE,
                    "message": "해당 turn에 대기 중인 interrupt가 없습니다 (이미 완료되었거나 thread_id 불일치).",
                    "conversation_id": conv_id, "turn_id": turn_id,
                })
                return
            break
        first_iter = False
        intr_value = _extract_interrupt_value(gs)
        intr_type = intr_value.get("type", "plan_review")

        # auto-approve: 사용자가 cognitive/planning 중 pause 요청 시 plan_review 자동 승인
        if intr_type == "plan_review" and hitl.is_paused(turn_id):
            logger.info("plan_review auto-approved due to pause request", turn_id=turn_id)
            abort_reason = await _broadcast_chunks(
                agent.astream(LGCommand(resume={"action": "approve"}), config=config)
            )
            if abort_reason:
                await _emit_complete("aborted", reason=abort_reason)
                return
            continue   # 다음 interrupt (execution_pause) 처리

        # interrupt 타입별 이벤트 emit
        # Sprint 14 A3 Phase 4 (2026-04-23): data 에도 turn_id 를 일관 포함
        # (클라이언트가 fallback 없이 단일 경로로 읽을 수 있도록 — POC 시나리오 100% 보장)
        if intr_type == "plan_review":
            # Sprint 14 A3 Phase 5 (2026-04-24): 사용자 §9.1 P1 "hitl=pause 같은 개념".
            # plan_review 진입 시 편집 가능한 임시 progress 생성 → ws_hitl 이 pause 분기로 단일 처리.
            # planning_stage L88-92 modify 분기가 승인 시 value 로 plan 교체.
            plan_dict = intr_value.get("plan") or final_state.get("plan") or {}
            if plan_dict and not hitl.get_progress(turn_id):
                temp = hitl.create_progress(turn_id, plan_dict)
                temp.status = "paused"
            await conn_manager.broadcast_to_user(user_id, "agent", {
                "type": "hitl_request",
                "conversation_id": conv_id, "turn_id": turn_id,
                "data": {
                    **_build_hitl_request_data(intr_value, final_state),
                    "turn_id": turn_id,
                    "conversation_id": conv_id,
                },
            })
        elif intr_type == "execution_pause":
            # 서버 재시작 대응: 싱글톤에 progress 없으면 Checkpoint에서 복원
            progress_snap = intr_value.get("progress", {})
            if not hitl.get_progress(turn_id):
                hitl.restore_progress(turn_id, progress_snap)
                logger.info("progress restored from checkpoint", turn_id=turn_id)
            await conn_manager.broadcast_to_user(user_id, "agent", {
                "type": "paused",
                "conversation_id": conv_id, "turn_id": turn_id,
                "data": {
                    **_build_paused_data(intr_value),
                    "turn_id": turn_id,
                    "conversation_id": conv_id,
                },
            })

        # 사용자 응답 대기 (I7 Queue) — Sprint 14 A1: timeout 인자 추가
        from app.core.config import settings as _settings
        action = await hitl.wait_for_resume(
            turn_id,
            timeout=_settings.HITL_RESUME_TIMEOUT_SEC,
        )
        user_action = action.get("action")

        # Sprint 14 A1 — timeout 분기 선처리 (G-11: intr_type 별 reject/cancel)
        if user_action == "timeout":
            # plan_review: planning_stage 는 cancel 미처리 → reject 로 END
            # execution_pause: execution_stage 는 cancel 로 END
            timeout_action = "reject" if intr_type == "plan_review" else "cancel"
            logger.warning(
                "hitl timeout aborted turn",
                user_id=user_id,
                conv_id=conv_id,
                turn_id=turn_id,
                intr_type=intr_type,
                timeout_sec=_settings.HITL_RESUME_TIMEOUT_SEC,
            )
            async for _ in agent.astream(
                LGCommand(resume={"action": timeout_action}), config=config
            ):
                pass
            await _emit_complete("aborted", reason="hitl_timeout")
            return

        # timeout 아닌 경우만 resumed 이벤트 emit (C-7)
        await conn_manager.broadcast_to_user(user_id, "agent", {
            "type": "resumed",
            "conversation_id": conv_id, "turn_id": turn_id,
            "data": {"action": user_action},
        })

        if user_action == "cancel":
            # 잔여 astream silent drain (graph 정리)
            async for _ in agent.astream(LGCommand(resume=action), config=config):
                pass
            await _emit_complete("cancelled")
            return
        if user_action == "reject":
            # Sprint 12 L571~584 포팅: silent drain + rejected 종료
            async for _ in agent.astream(LGCommand(resume=action), config=config):
                pass
            await _emit_complete("rejected")
            return

        # approve / modify / continue 등 — 정상 재실행
        abort_reason = await _broadcast_chunks(
            agent.astream(LGCommand(resume=action), config=config)
        )
        if abort_reason:
            await _emit_complete("aborted", reason=abort_reason)
            return

    # 정상 종료 — 단, stage 가 Command(update={"error": ...}, goto=END) 로 끝났으면
    # 성공이 아니다 (2026-06-11 정직화). 과거엔 cognitive/planning 실패가
    # complete(status=success) + 빈 화면(무언의 성공)으로 나갔음.
    if final_state.get("error") and not final_state.get("response"):
        from app.core.error_codes import ErrorCodes
        await conn_manager.broadcast_to_user(user_id, "agent", {
            "type": "error",
            **{**ErrorCodes.LAYER_ERROR, "message": str(final_state.get("error"))},
            "conversation_id": conv_id,
            "turn_id": turn_id,
        })
        await _emit_complete("aborted", reason="LAYER_ERROR")
        return
    await _emit_complete("success")


async def run_turn(
    user_id: str,
    conversation_id: str,
    turn_id: str,
    payload: dict,
    *,
    _runner=None,
    app=None,
) -> None:
    """쿼리 1회 실행 — WS 연결과 독립된 async task (Sprint 13 I10b).

    I10b 범위: 슬롯 관리 + 에러 broadcast.
    I10c~e에서 graph astream, resume 루프, 예외 처리 확장.

    Args:
        user_id: 유저 식별자
        conversation_id: 대화 ID
        turn_id: 쿼리 ID
        payload: user_input/language/history_limit 등
        _runner: 테스트용 DI. None이면 no-op (I10c 이후 graph 실행으로 교체)
    """
    from api.connection_manager import conn_manager
    from app.dream_agent.workflow_managers.concurrency_manager import concurrency
    from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager

    # 1. 동시 실행 슬롯 획득
    if not concurrency.try_acquire(user_id, turn_id):
        from app.core.error_codes import ErrorCodes
        await conn_manager.broadcast_to_user(user_id, "agent", {
            "type": "error",
            **ErrorCodes.CONCURRENT_LIMIT_EXCEEDED,
            "conversation_id": conversation_id,
            "turn_id": turn_id,
        })
        return

    runner = _runner if _runner is not None else _graph_runner_with_resume
    try:
        # Sprint 14 A1 — 활성 turn 레지스트리 등록 (FR-13b stale guard 용).
        # try 블록 내부 첫 줄 — exception 발생해도 finally 가 cleanup_turn 호출.
        get_hitl_manager().register_turn(turn_id)

        if _runner is not None:
            await runner(user_id, conversation_id, turn_id, payload)
        else:
            await runner(user_id, conversation_id, turn_id, payload, _app=app)
    except Exception as e:
        logger.exception("run_turn error", turn_id=turn_id, user_id=user_id)
        from app.core.error_codes import ErrorCodes
        spec = dict(ErrorCodes.EXECUTION_ERROR)
        spec["message"] = str(e)
        await conn_manager.broadcast_to_user(user_id, "agent", {
            "type": "error",
            **spec,
            "conversation_id": conversation_id,
            "turn_id": turn_id,
        })
    finally:
        concurrency.release(user_id, turn_id)
        get_hitl_manager().cleanup_turn(turn_id)
        # CallbackManager bridge 정리 (I11-b2 — _graph_runner_with_resume 에서 등록됨)
        from app.dream_agent.workflow_managers.callback_manager import get_callback_manager
        get_callback_manager().unregister(turn_id)


def _parse_query_message(msg: dict) -> dict:
    """쿼리 메시지 검증 + 정규화 (Sprint 13 I10a, D-3/D-4 정책).

    Returns:
        - 정상: {"conversation_id": str, "turn_id": str, "payload": dict}
        - 실패: {"error": {"type": "error", "code": "INVALID_MESSAGE", "message": str}}

    검증 규칙:
        - conversation_id 누락/빈 문자열 → INVALID_MESSAGE
        - turn_id 누락/빈 문자열 → INVALID_MESSAGE
        - user_input 누락 → INVALID_MESSAGE (빈 문자열은 허용)
        - 나머지(language, history_limit)는 payload로 전달
    """
    from app.core.error_codes import ErrorCodes

    conv_id = msg.get("conversation_id")
    turn_id = msg.get("turn_id")
    user_input = msg.get("user_input")

    def _invalid(msg_detail: str) -> dict:
        spec = dict(ErrorCodes.INVALID_MESSAGE)
        spec["message"] = msg_detail
        return {"error": {"type": "error", **spec}}

    if not conv_id:
        return _invalid("conversation_id is required (non-empty)")
    if not turn_id:
        return _invalid("turn_id is required (non-empty)")
    if user_input is None:
        return _invalid("user_input is required")

    payload = {k: v for k, v in msg.items() if k not in ("type", "conversation_id", "turn_id")}
    # user_input은 payload 안에 포함 (이미 msg에서 왔음)
    payload["user_input"] = user_input
    return {
        "conversation_id": conv_id,
        "turn_id": turn_id,
        "payload": payload,
    }


def _get_graph(app=None):
    """lifespan에서 초기화된 그래프 반환. 없으면 in-memory fallback (테스트용)."""
    if app and hasattr(app, "state") and hasattr(app.state, "graph"):
        return app.state.graph
    # fallback: Sprint 테스트 스크립트 등에서 app 없이 호출 시
    logger.warning("Graph without checkpointer (fallback)")
    return build_graph()


@router.websocket("/ws/agent")
async def stream_endpoint(
    websocket: WebSocket,
    user_id: str = Query("demo"),
) -> None:
    """스트림 채널 (명세 §2 간소화).

    흐름:
      1. accept + `connected` 전송
      2. 클라 메시지 수신 loop
      3. `{"type":"query", ...}` (Sprint 13+) 또는 `resume_query` 시 run_turn task 스폰
      4. astream으로 노드별 `node_event`·`layer_start` 송신
      5. 종료 시 `complete`, 예외 시 `error`
    """
    from api.connection_manager import conn_manager

    await websocket.accept()
    session_id = f"sess_{uuid.uuid4().hex[:8]}"

    # Sprint 13: conn_manager 등록 (query 경로 broadcast 대상)
    if not await conn_manager.connect(user_id, "agent", websocket):
        # MAX_WS_CONNECTIONS 초과 — connect 내부에서 close(1008) 완료
        return

    await _safe_send(websocket, {
        "type": "connected",
        "session_id": session_id,
        "user_id": user_id,
        "timestamp": _iso_now(),
    })
    logger.info("ws_agent connected", user_id=user_id, session_id=session_id)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "query":
                # Sprint 13 신 경로
                parsed = _parse_query_message(data)
                if "error" in parsed:
                    await _safe_send(websocket, parsed["error"])
                    continue
                asyncio.create_task(run_turn(
                    user_id,
                    parsed["conversation_id"],
                    parsed["turn_id"],
                    parsed["payload"],
                    app=websocket.app,
                ))
            elif msg_type == "resume_query":
                # 서버 재시작 복원: conv_id/turn_id 로 Checkpoint에 저장된 pending interrupt 재emit
                conv_id = data.get("conversation_id")
                turn_id = data.get("turn_id")
                if not conv_id or not turn_id:
                    from app.core.error_codes import ErrorCodes
                    spec = dict(ErrorCodes.INVALID_MESSAGE)
                    spec["message"] = "resume_query requires conversation_id and turn_id"
                    await _safe_send(websocket, {"type": "error", **spec})
                    continue
                asyncio.create_task(run_turn(
                    user_id, conv_id, turn_id,
                    {"resume_only": True},
                    app=websocket.app,
                ))
            elif msg_type == "ping":
                await _safe_send(websocket, {"type": "pong", "timestamp": _iso_now()})
            else:
                logger.warning("ws_agent unknown type", type=msg_type, session_id=session_id)

    except WebSocketDisconnect:
        logger.info("ws_agent disconnected", user_id=user_id)
        await conn_manager.disconnect(user_id, "agent", websocket)
    except Exception as e:
        logger.exception("ws_agent error", user_id=user_id, session_id=session_id)
        try:
            await _safe_send(websocket, {
                "type": "error",
                "session_id": session_id,
                "timestamp": _iso_now(),
                "data": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e),
                },
            })
        except Exception:
            pass
        await conn_manager.disconnect(user_id, "agent", websocket)


# (작업 ⑬, 2026-05-31) _run_agent 폐기 — 死코드 (351 줄)
# 폐기 사유:
#   - frontend api/ws.ts 에 `type: 'start'` 송신 0 hit (Grep 재확인)
#   - legacy Sprint 12 진입점, Sprint 13 query/resume_query 경로로 대체됨
#   - 사용자 원칙 [死코드 즉시 폐기] 정합
# 활성 진입점 = _graph_runner_with_resume + run_turn (line 478+)
