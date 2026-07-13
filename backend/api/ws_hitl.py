"""WebSocket HITL 엔드포인트.

/ws/hitl — 사용자의 HITL 응답(approve/reject/modify)을 수신하는 채널.
/ws/agent와 분리: agent는 이벤트 발송, hitl은 사용자 명령 수신.

메시지 타입:
  수신 (브라우저 → 서버):
    - hitl_response: Plan 승인/거부/수정 응답 (request_id 기반)
    - pause:         Execution 중 일시중단 요청
    - resume:        Execution 재개 요청
    - todo_modify:   Plan review / Execution pause 중 Todo 수정
    - todo_delete:   Todo 삭제
    - todo_add:      Todo 추가 (Execution pause 중만)
    - ping:          keepalive

  발신 (서버 → 브라우저):
    - connected:     연결 확인
    - hitl_ack:      응답 처리 확인
    - error:         에러
    - pong:          keepalive 응답
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from api.connection_manager import conn_manager
from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


async def _safe_send(websocket: WebSocket, message: dict[str, Any]) -> None:
    text = json.dumps(message, ensure_ascii=False, default=str)
    await websocket.send_text(text)


async def _check_turn_active(
    websocket: WebSocket,
    data: dict,
    action: str,
) -> tuple[bool, str]:
    """Sprint 14 A3 B1 / FR-13c — is_turn_active 가드 DRY 헬퍼.

    Status: complete — Sprint 14 A3 Phase 2 B1.

    4종 핸들러 (hitl_response + A1) + 4종 핸들러 (A3 todo_modify/delete/add/edit_nl)
    공통 가드. 비활성 turn 은 `hitl_ack accepted:false, reason:turn_not_active` 로 거부.

    Returns:
        (is_active, turn_id). is_active=False 면 이미 ack 전송했으니 호출자는 return.
    """
    from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager

    payload = data.get("data", {})
    turn_id = payload.get("turn_id") or payload.get("session_id") or ""
    hitl = get_hitl_manager()
    if not turn_id:
        return True, ""  # turn_id 없으면 가드 우회 (다른 검증에서 catch)
    if not hitl.is_turn_active(turn_id):
        logger.warning(
            "hitl request for inactive turn",
            turn_id=turn_id, action=action,
        )
        await _safe_send(websocket, {
            "type": "hitl_ack",
            "timestamp": _iso_now(),
            "data": {
                "action": action,
                "session_id": turn_id,
                "accepted": False,
                "reason": "turn_not_active",
            },
        })
        return False, turn_id
    return True, turn_id


@router.websocket("/ws/hitl")
async def hitl_endpoint(
    websocket: WebSocket,
    user_id: str | None = Query(default=None),
) -> None:
    """HITL 명령 채널 (Sprint 13 I9).

    사용자가 Plan 승인/거부/수정 등 HITL 응답을 보내는 전용 WebSocket.
    Sprint 13: conn_manager 등록 + hitl.signal_resume 라우팅.
    """
    await websocket.accept()

    uid = user_id or settings.DEFAULT_USER_ID
    if not await conn_manager.connect(uid, "hitl", websocket):
        # MAX_WS_CONNECTIONS 초과 — connect 내부에서 close(1008) 완료
        return

    await _safe_send(websocket, {
        "type": "connected",
        "channel": "hitl",
        "user_id": uid,
        "timestamp": _iso_now(),
    })
    logger.info("ws_hitl connected", user_id=uid)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "hitl_response":
                await _handle_hitl_response(websocket, data)

            elif msg_type == "todo_modify":
                await _handle_todo_modify(websocket, data)

            elif msg_type == "todo_delete":
                await _handle_todo_delete(websocket, data)

            elif msg_type == "todo_add":
                await _handle_todo_add(websocket, data)

            elif msg_type == "todo_edit_nl":
                await _handle_todo_edit_nl(websocket, data)

            elif msg_type == "pause":
                await _handle_pause(websocket, data)

            elif msg_type == "resume":
                await _handle_resume(websocket, data)

            elif msg_type == "cancel":
                await _handle_cancel(websocket, data)

            elif msg_type == "ping":
                await _safe_send(websocket, {"type": "pong", "timestamp": _iso_now()})

            else:
                logger.warning("ws_hitl unknown type", type=msg_type)

    except WebSocketDisconnect:
        logger.info("ws_hitl disconnected", user_id=uid)
        await conn_manager.disconnect(uid, "hitl", websocket)
    except Exception as e:
        logger.exception("ws_hitl error", error=str(e))
        await _safe_send(websocket, {
            "type": "error",
            "timestamp": _iso_now(),
            "data": {"message": str(e)},
        })
        await conn_manager.disconnect(uid, "hitl", websocket)


async def _handle_hitl_response(websocket: WebSocket, data: dict) -> None:
    """hitl_response 처리 — signal_resume(Queue) 으로 run_turn 재개.

    (2026-06-11) Sprint 12 장부 트랙(hitl.submit_response) 호출 폐기.
    _run_agent 폐기(533a632, 05-31)가 장부 기입자(create_request)만 지우고 이 호출을
    남겨, 빈 장부 조회로 hitl_ack.accepted 가 매번 False 로 나가던 거짓 신호 수정.
    accepted = "재개 신호가 실제 전달됐는가" (활성 turn 가드 통과 + signal_resume put).
    """
    from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager

    payload = data.get("data", {})
    request_id = payload.get("request_id")
    action = payload.get("action")  # "approve" / "reject" / "modify"
    value = payload.get("value")

    if not request_id or not action:
        await _safe_send(websocket, {
            "type": "error",
            "timestamp": _iso_now(),
            "data": {"message": "request_id와 action은 필수입니다."},
        })
        return

    hitl = get_hitl_manager()

    # Sprint 14 A1 — 활성 turn 가드 (FR-13b 4종 가드 중 hitl_response)
    # timeout 된 turn 에 승인/거부 날아오면 signal_resume 차단 (Queue leak 방지).
    turn_id = payload.get("turn_id") or payload.get("session_id") or ""
    if turn_id and not hitl.is_turn_active(turn_id):
        logger.warning(
            "hitl request for inactive turn",
            turn_id=turn_id, action="hitl_response", submitted_action=action,
        )
        await _safe_send(websocket, {
            "type": "hitl_ack",
            "timestamp": _iso_now(),
            "data": {
                "action": action,
                "session_id": turn_id,
                "accepted": False,
                "reason": "turn_not_active",
            },
        })
        return

    # Sprint 13 I9: run_turn task 깨우기 — 재개의 유일한 실제 메커니즘 (Queue 트랙).
    accepted = False
    if turn_id:
        # Sprint 14 A3 Phase 5 (2026-04-24): "hitl=pause 같은 개념" 확정.
        # plan_review 에서 편집된 임시 progress 가 있으면 approve → modify 로 변환 전달.
        # planning_stage L88-92 의 modify 분기가 value 로 plan 교체.
        # reject 는 원래대로 (편집 무시), approve 만 변환.
        resume_payload = {"action": action, "value": value}
        if action == "approve":
            progress = hitl.get_progress(turn_id)
            if progress is not None:
                hitl.request_resume(turn_id)  # status="running" 복귀
                resume_payload = {"action": "modify", "value": progress.plan}
        hitl.signal_resume(turn_id, resume_payload)
        accepted = True

    ack_data: dict = {
        "request_id": request_id,
        "action": action,
        "accepted": accepted,
    }
    if not accepted:
        ack_data["reason"] = "missing_turn_id"
    await _safe_send(websocket, {
        "type": "hitl_ack",
        "timestamp": _iso_now(),
        "data": ack_data,
    })
    logger.info(
        "ws_hitl response routed",
        request_id=request_id, action=action, accepted=accepted,
    )


async def _handle_todo_modify(websocket: WebSocket, data: dict) -> None:
    """todo_modify 처리 (Sprint 14 A3 Phase 5 — 통합 편집 경로).

    Status: complete — Sprint 14 A3 Phase 5 (2026-04-24, "hitl=pause 같은 개념" 반영).

    단일 경로: plan_review / execution_pause 모두 `_progress[turn_id]` 기반 처리.
    plan_review 시 `_graph_runner_with_resume` 가 임시 progress 생성 (status="paused").

    가드:
      1) B1 is_turn_active (헬퍼 `_check_turn_active`)
      2) B5 입력 검증 (session_id / todo_id / changes 필수)
      3) L1 per-session Lock (D9)
    """
    from app.core.error_codes import ErrorCodes
    from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager

    # B1: is_turn_active 가드 (FR-13c)
    is_active, turn_id = await _check_turn_active(websocket, data, "todo_modify")
    if not is_active:
        return

    payload = data.get("data", {})
    session_id = payload.get("session_id") or turn_id
    todo_id = payload.get("todo_id")
    changes = payload.get("changes", {})

    # B5: 입력 검증
    if not todo_id or not session_id:
        await _safe_send(websocket, {
            "type": "error",
            "timestamp": _iso_now(),
            **ErrorCodes.INVALID_MESSAGE,
            "message": "session_id와 todo_id는 필수입니다.",
        })
        return
    if not isinstance(changes, dict) or not changes:
        await _safe_send(websocket, {
            "type": "error",
            "timestamp": _iso_now(),
            **ErrorCodes.INVALID_MESSAGE,
            "message": "changes 는 비어있지 않은 dict 여야 합니다.",
        })
        return

    hitl = get_hitl_manager()

    # L1: per-session Lock + 단일 편집 경로
    async with hitl._get_lock(session_id):
        progress = hitl.get_progress(session_id)
        if not progress or progress.status != "paused":
            await _safe_send(websocket, {
                "type": "hitl_ack",
                "timestamp": _iso_now(),
                "data": {
                    "action": "todo_modify",
                    "session_id": session_id,
                    "accepted": False,
                    "reason": "편집하려면 일시정지 상태가 필요합니다.",
                    "code": ErrorCodes.TODO_EDIT_NOT_PAUSED["code"],
                },
            })
            return

        result = hitl.handle_todo_edit(session_id, todo_id, changes)
        await _safe_send(websocket, {
            "type": "hitl_ack",
            "timestamp": _iso_now(),
            "data": {
                "action": "todo_modify",
                "session_id": session_id,
                "todo_id": todo_id,
                "accepted": "error" not in result,
                **({"reason": result["error"], "code": ErrorCodes.TODO_EDIT_NOT_PAUSED["code"]}
                   if "error" in result else {}),
                **{k: v for k, v in result.items() if k != "error"},
                "plan": progress.plan,
            },
        })


async def _handle_todo_delete(websocket: WebSocket, data: dict) -> None:
    """todo_delete — Sprint 14 A3 Phase 5 (통합 편집 경로).

    Status: complete — Sprint 14 A3 Phase 5 (2026-04-24, "hitl=pause 같은 개념" 반영).
    단일 경로: plan_review / execution_pause 모두 `_progress[turn_id]` 기반.
    """
    from app.core.error_codes import ErrorCodes
    from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager

    is_active, turn_id = await _check_turn_active(websocket, data, "todo_delete")
    if not is_active:
        return

    payload = data.get("data", {})
    session_id = payload.get("session_id") or turn_id
    todo_id = payload.get("todo_id")

    if not todo_id or not session_id:
        await _safe_send(websocket, {
            "type": "error",
            "timestamp": _iso_now(),
            **ErrorCodes.INVALID_MESSAGE,
            "message": "session_id와 todo_id는 필수입니다.",
        })
        return

    hitl = get_hitl_manager()

    async with hitl._get_lock(session_id):
        progress = hitl.get_progress(session_id)
        if not progress or progress.status != "paused":
            await _safe_send(websocket, {
                "type": "hitl_ack",
                "timestamp": _iso_now(),
                "data": {
                    "action": "todo_delete",
                    "session_id": session_id,
                    "accepted": False,
                    "reason": "편집하려면 일시정지 상태가 필요합니다.",
                    "code": ErrorCodes.TODO_EDIT_NOT_PAUSED["code"],
                },
            })
            return

        result = hitl.handle_todo_delete(session_id, todo_id)
        await _safe_send(websocket, {
            "type": "hitl_ack",
            "timestamp": _iso_now(),
            "data": {
                "action": "todo_delete",
                "session_id": session_id,
                "todo_id": todo_id,
                "accepted": "error" not in result,
                **({"reason": result["error"], "code": ErrorCodes.TODO_EDIT_NOT_PAUSED["code"]}
                   if "error" in result else {}),
                **{k: v for k, v in result.items() if k != "error"},
                "plan": progress.plan,
            },
        })


async def _handle_todo_add(websocket: WebSocket, data: dict) -> None:
    """todo_add — Sprint 14 A3 Phase 2. Execution pause 중에만 지원.

    Status: complete — Sprint 14 A3 Phase 2.
    """
    from app.core.error_codes import ErrorCodes
    from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager

    is_active, turn_id = await _check_turn_active(websocket, data, "todo_add")
    if not is_active:
        return

    payload = data.get("data", {})
    session_id = payload.get("session_id") or turn_id
    new_todo = payload.get("new_todo", {})
    after_todo_id = payload.get("after_todo_id")

    if not session_id or not new_todo:
        await _safe_send(websocket, {
            "type": "error",
            "timestamp": _iso_now(),
            **ErrorCodes.INVALID_MESSAGE,
            "message": "session_id와 new_todo는 필수입니다.",
        })
        return
    if not isinstance(new_todo, dict) or not new_todo.get("agent") or not new_todo.get("task"):
        await _safe_send(websocket, {
            "type": "error",
            "timestamp": _iso_now(),
            **ErrorCodes.INVALID_MESSAGE,
            "message": "new_todo 는 agent / task 필수.",
        })
        return

    hitl = get_hitl_manager()
    async with hitl._get_lock(session_id):
        progress = hitl.get_progress(session_id)
        if not progress or progress.status != "paused":
            await _safe_send(websocket, {
                "type": "hitl_ack",
                "timestamp": _iso_now(),
                "data": {
                    "action": "todo_add",
                    "session_id": session_id,
                    "accepted": False,
                    "reason": "편집하려면 일시정지 상태가 필요합니다.",
                    "code": ErrorCodes.TODO_EDIT_NOT_PAUSED["code"],
                },
            })
            return

        result = hitl.handle_todo_add(session_id, new_todo, after_todo_id=after_todo_id)
        await _safe_send(websocket, {
            "type": "hitl_ack",
            "timestamp": _iso_now(),
            "data": {
                "action": "todo_add",
                "session_id": session_id,
                "accepted": "error" not in result,
                **{k: v for k, v in result.items() if k != "error"},
                "plan": progress.plan,
            },
        })


async def _handle_todo_edit_nl(websocket: WebSocket, data: dict) -> None:
    """todo_edit_nl — Y-a 자연어 Todo 편집 (Sprint 14 A3 Phase 3).

    Status: complete — Sprint 14 A3 Phase 3.

    흐름:
      1. B1 is_turn_active 가드
      2. 입력 검증 (session_id, instruction)
      3. L1 per-session Lock
      4. pause 상태 확인
      5. plan_editor.parse_instruction (LLM 호출) — 실패 시 NL_INTENT_UNCLEAR
      6. validate_edit (DAG 무결성)
      7. apply_edit — Pydantic Plan 기반
      8. Pydantic Plan → dict 변환 후 progress.plan 교체 + cascade 재계산
      9. hitl_ack 응답 (accepted + cascade + 신규 plan)

    D7=A- 의 free-form reason:
      - NL_LLM_UNAVAILABLE / NL_TIMEOUT / NL_CONTEXT_TOO_LARGE → free-form
      - REORDER_INVALID_DAG → free-form
      - 고유 enum: TODO_EDIT_NOT_PAUSED, INVALID_DAG, NL_INTENT_UNCLEAR
    """
    from app.core.error_codes import ErrorCodes
    from app.dream_agent.planning.planner import Plan as PlannerPlan
    from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager
    from app.dream_agent.workflow_managers.hitl_manager.plan_editor import PlanEditor
    from app.dream_agent.workflow_managers.todo_manager import get_todo_manager

    # B1: is_turn_active 가드 (FR-13c — NL 경로도 포함)
    is_active, turn_id = await _check_turn_active(websocket, data, "todo_edit_nl")
    if not is_active:
        return

    payload = data.get("data", {})
    session_id = payload.get("session_id") or turn_id
    instruction = payload.get("instruction", "")

    if not session_id or not isinstance(instruction, str) or not instruction.strip():
        await _safe_send(websocket, {
            "type": "error",
            "timestamp": _iso_now(),
            **ErrorCodes.INVALID_MESSAGE,
            "message": "session_id 와 instruction 는 필수입니다.",
        })
        return

    hitl = get_hitl_manager()

    async with hitl._get_lock(session_id):
        progress = hitl.get_progress(session_id)
        if not progress or progress.status != "paused":
            await _safe_send(websocket, {
                "type": "hitl_ack",
                "timestamp": _iso_now(),
                "data": {
                    "action": "todo_edit_nl",
                    "session_id": session_id,
                    "accepted": False,
                    "reason": "편집하려면 일시정지 상태가 필요합니다.",
                    "code": ErrorCodes.TODO_EDIT_NOT_PAUSED["code"],
                },
            })
            return

        # dict (progress.plan) → planner.Plan 직접 변환 (Sprint 14 A3 D 통일)
        try:
            plan_pydantic = PlannerPlan.model_validate(progress.plan)
        except Exception as e:
            logger.warning("plan dict → planner.Plan 변환 실패", error=str(e))
            await _safe_send(websocket, {
                "type": "hitl_ack",
                "timestamp": _iso_now(),
                "data": {
                    "action": "todo_edit_nl",
                    "session_id": session_id,
                    "accepted": False,
                    "reason": f"Plan 변환 실패: {e}",
                },
            })
            return

        editor = PlanEditor()
        try:
            parsed = await editor.parse_instruction(instruction, plan_pydantic)
        except Exception as e:
            # NL_LLM_UNAVAILABLE 은 free-form (D7=A-)
            logger.warning("plan_editor.parse_instruction 실패", error=str(e))
            await _safe_send(websocket, {
                "type": "hitl_ack",
                "timestamp": _iso_now(),
                "data": {
                    "action": "todo_edit_nl",
                    "session_id": session_id,
                    "accepted": False,
                    "reason": f"자연어 처리 중 오류: {e}",
                },
            })
            return

        # 의도 불명확 → NL_INTENT_UNCLEAR (enum)
        if parsed.get("action") == "unknown":
            await _safe_send(websocket, {
                "type": "hitl_ack",
                "timestamp": _iso_now(),
                "data": {
                    "action": "todo_edit_nl",
                    "session_id": session_id,
                    "accepted": False,
                    "reason": parsed.get("reason") or ErrorCodes.NL_INTENT_UNCLEAR["message"],
                    "code": ErrorCodes.NL_INTENT_UNCLEAR["code"],
                },
            })
            return

        # validate_edit (DAG 무결성)
        valid, val_errors = await editor.validate_edit(plan_pydantic, parsed)
        if not valid:
            await _safe_send(websocket, {
                "type": "hitl_ack",
                "timestamp": _iso_now(),
                "data": {
                    "action": "todo_edit_nl",
                    "session_id": session_id,
                    "accepted": False,
                    "reason": "; ".join(val_errors),
                    "code": ErrorCodes.INVALID_DAG["code"],
                },
            })
            return

        # apply_edit — planner.Plan → new planner.Plan (Sprint 14 A3 D 통일, PlanChange 폐기)
        try:
            new_plan_pydantic = await editor.apply_edit(
                plan_pydantic, parsed, instruction
            )
        except Exception as e:
            logger.error("plan_editor.apply_edit 실패", error=str(e))
            await _safe_send(websocket, {
                "type": "hitl_ack",
                "timestamp": _iso_now(),
                "data": {
                    "action": "todo_edit_nl",
                    "session_id": session_id,
                    "accepted": False,
                    "reason": f"편집 적용 실패: {e}",
                },
            })
            return

        # planner.Plan → dict + progress 교체 + cascade 재계산 (Sprint 14 A3 D 통일)
        new_plan_dict = new_plan_pydantic.model_dump(mode="json")
        # dag 키 보장 (todo_manager.modify_todo 등이 쓰는 형식 유지)
        tm = get_todo_manager()
        new_plan_dict = tm._rebuild_dag(new_plan_dict)

        # cascade 계산 — 영향 받은 Todo (parsed.target_todo_ids) 중 첫 번째 기준
        invalidated_all: list[str] = []
        restart_from = None
        preserved_list: list[str] = []
        for tid in parsed.get("target_todo_ids", []):
            cascade = tm.calculate_cascade(tid, progress.completed_todos, new_plan_dict)
            for inv in cascade.invalidated_todos:
                if inv not in invalidated_all:
                    invalidated_all.append(inv)
            if restart_from is None:
                restart_from = cascade.restart_from
            for pid in cascade.preserved_results:
                if pid not in preserved_list:
                    preserved_list.append(pid)

        # progress 적용: plan 교체 + completed_todos 무효화 제거 + phases 재구성
        progress.plan = new_plan_dict
        for inv in invalidated_all:
            progress.completed_todos.pop(inv, None)
        progress.phases = tm._build_phases_from_plan(new_plan_dict)
        issues = tm.validate(new_plan_dict)

        logger.info(
            "todo_edit_nl applied",
            session_id=session_id,
            action=parsed.get("action"),
            invalidated=invalidated_all,
        )
        await _safe_send(websocket, {
            "type": "hitl_ack",
            "timestamp": _iso_now(),
            "data": {
                "action": "todo_edit_nl",
                "session_id": session_id,
                "accepted": True,
                "nl_action": parsed.get("action"),
                "invalidated": invalidated_all,
                "restart_from": restart_from,
                "preserved": preserved_list,
                "issues": issues,
                "plan": new_plan_dict,
            },
        })


async def _handle_pause(websocket: WebSocket, data: dict) -> None:
    """pause — hitl_manager.request_pause. execution_stage가 다음 Phase 전에 감지."""
    from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager

    payload = data.get("data", {})
    session_id = payload.get("session_id", "") or payload.get("turn_id", "")
    turn_id = payload.get("turn_id") or session_id   # alias 폴백

    hitl = get_hitl_manager()

    # Sprint 14 A1 — 활성 turn 가드 (FR-13b)
    if not hitl.is_turn_active(turn_id):
        logger.warning("hitl request for inactive turn", turn_id=turn_id, action="pause")
        await _safe_send(websocket, {
            "type": "hitl_ack",
            "timestamp": _iso_now(),
            "data": {
                "action": "pause",
                "session_id": session_id,
                "accepted": False,
                "reason": "turn_not_active",
            },
        })
        return

    hitl.request_pause(session_id, reason="user_request")

    await _safe_send(websocket, {
        "type": "hitl_ack",
        "timestamp": _iso_now(),
        "data": {"action": "pause", "session_id": session_id, "accepted": True},
    })


async def _handle_resume(websocket: WebSocket, data: dict) -> None:
    """resume — hitl_manager.request_resume + signal_resume (Sprint 13 I9)."""
    from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager

    payload = data.get("data", {})
    session_id = payload.get("session_id", "") or payload.get("turn_id", "")
    turn_id = payload.get("turn_id") or session_id   # alias 폴백

    hitl = get_hitl_manager()

    # Sprint 14 A1 — 활성 turn 가드 (FR-13b)
    if not hitl.is_turn_active(turn_id):
        logger.warning("hitl request for inactive turn", turn_id=turn_id, action="resume")
        await _safe_send(websocket, {
            "type": "hitl_ack",
            "timestamp": _iso_now(),
            "data": {
                "action": "resume",
                "session_id": session_id,
                "accepted": False,
                "reason": "turn_not_active",
            },
        })
        return

    hitl.request_resume(session_id)                  # Sprint 12: _paused 해제
    hitl.signal_resume(turn_id, {"action": "continue"})   # I9: Queue에 signal

    await _safe_send(websocket, {
        "type": "hitl_ack",
        "timestamp": _iso_now(),
        "data": {"action": "resume", "session_id": session_id, "accepted": True},
    })


async def _handle_cancel(websocket: WebSocket, data: dict) -> None:
    """cancel — hitl_manager.request_cancel + signal_resume (Sprint 13 I9 신규 타입).

    run_turn task가 `wait_for_resume`에서 `{"action": "cancel"}` 받으면 루프 탈출.
    """
    from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager

    payload = data.get("data", {})
    session_id = payload.get("session_id", "") or payload.get("turn_id", "")
    turn_id = payload.get("turn_id") or session_id

    hitl = get_hitl_manager()

    # Sprint 14 A1 — 활성 turn 가드 (FR-13b)
    if not hitl.is_turn_active(turn_id):
        logger.warning("hitl request for inactive turn", turn_id=turn_id, action="cancel")
        await _safe_send(websocket, {
            "type": "hitl_ack",
            "timestamp": _iso_now(),
            "data": {
                "action": "cancel",
                "session_id": session_id,
                "accepted": False,
                "reason": "turn_not_active",
            },
        })
        return

    hitl.request_cancel(session_id)
    hitl.signal_resume(turn_id, {"action": "cancel"})

    await _safe_send(websocket, {
        "type": "hitl_ack",
        "timestamp": _iso_now(),
        "data": {"action": "cancel", "session_id": session_id, "accepted": True},
    })
