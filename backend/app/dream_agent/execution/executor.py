"""Executor — DAG 기반 Todo 병렬 실행 엔진

입력: Plan (Todo[] + DAG)
출력: ExecutionResult (todo_id → TodoResult)

Sprint 10 Phase 2: EventBus callback으로 todo_start/todo_complete/progress 실시간 전달.

Reference: docs/agent_specs/10_system_architecture_v1.9.md
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.execution.agent_pool import get_agent_pool
from app.dream_agent.execution.data_gate import check_consume_sufficiency
from app.dream_agent.models import ExecutionContext
from app.dream_agent.planning.planner import PlannedTodo
from app.dream_agent.schemas.execution_result import (
    TodoResult,
    TodoStatus,
)
from app.dream_agent.schemas.structured_query import SCOPE_PARAMS, validate_scope_value
from app.dream_agent.tools.shared.display import resolve as _resolve_display

logger = get_logger(__name__)


# (2026-06-12 정리 전환 Sprint) build_phases(Pydantic Plan 판) 삭제 — 호출처 0.
# 활성 phase 계산 = todo_manager._build_phases_from_plan (dict 판, 동일 로직).
# 이중 유지보수 위험 해소. 복원은 git 히스토리.


# ────────────────────────────────────────────────────────
# Tool 결과 1줄 요약
# ────────────────────────────────────────────────────────

def _generate_summary(tool_name: str, data: dict, is_mock: bool, status: str) -> str:
    """Tool 결과에서 UI용 1줄 요약 — tool 카탈로그의 display.summary_template 로 디스패치 (2026-07-02).

    과거엔 tool 이름별 if/elif(collector/sentiment_analyzer/... 마케팅 도메인)로 하드코딩됐다.
    이제 도메인이 tool 에 `display.summary_template` 을 선언하면 그 템플릿을 data 로 채운다
    (누락 키는 '?'). 미선언/미주입 tool = 일반 '완료' (비-load-bearing 화면 요약, 환각 아님).
    """
    if status == "failed":
        return "실패"
    if status == "skipped":
        return "건너뜀"

    mock_tag = " (mock)" if is_mock else ""

    template = _resolve_display(tool_name).summary_template
    if template:
        class _D(dict):
            def __missing__(self, key):  # noqa: D401 — 템플릿 누락 키 안전 치환
                return "?"
        try:
            return template.format_map(_D(data if isinstance(data, dict) else {})) + mock_tag
        except Exception:
            pass   # 잘못된 템플릿이 UI 요약(비-load-bearing) 때문에 실행을 멈추면 안 됨

    return f"완료{mock_tag}" if is_mock else "완료"


# ────────────────────────────────────────────────────────
# 단일 Todo 실행
# ────────────────────────────────────────────────────────

def _json_safe(obj: Any) -> Any:
    """직렬화 안전 변환 — DataFrame 등 비직렬 값은 None 으로 제거.

    TodoResult.data 는 (a) chaining(previous_results) + (b) model_dump(mode="json")
    양쪽에 쓰인다. tool 이 raw pandas.DataFrame 을 반환하면 (b) 에서
    PydanticSerializationError → agent turn 크래시 (2026-06-02 F1).
    chaining 소비자는 list/dict 키만 읽으므로(검증 완료) DataFrame 드롭이 안전.

    runner.json_safe / ws_agent._json_safe 와 동일 convention (직렬화 경계 정화).
    """
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return None  # DataFrame · set · 기타 비직렬 — 드롭


# ────────────────────────────────────────────────────────
# 슬라이스 1 (헌법 19 D2·D3) — param 경계: 위반 = 거부(정직 SKIPPED), coerce 금지
# 스코프 param 형식검증은 schemas.validate_scope_value 로 위임 (2026-07-02) — 도메인이
# scope_params.yaml 에 선언한 format(예 year_month)만 검사. 미선언 param = 항상 통과(inert).
# ────────────────────────────────────────────────────────

def _param_boundary_issue(
    meta: dict | None,
    tool_inst: Any,
    params: dict[str, Any],
) -> dict[str, str] | None:
    """실행 전 param 경계 검사 — 위반 시 SKIPPED 사유 dict, 통과 시 None (전부 결정론).

      1. 카탈로그 params_required 누락 — detect_plan_gaps(plan 자가평가)와 같은 진실을
         실행 경계에서도 강제 (gap 이 새어 들어와도 거짓 실행 안 함).
      2. 스코프 param(SCOPE_PARAMS) 형식 — validate_scope_value(도메인 선언 format)로 검사.
         'all' 이 흘러들어 startswith('all') 0건 → 거짓 COMPLETED 가 되던 G2 경로 차단.
         미선언(빈 scope_params.yaml) = SCOPE_PARAMS 공집합 → 이 루프 0회(inert).
      3. ToolSpec.validate_params — required + type (per-tool yaml 계약. ⑷ 2026-06-01
         "Executor 가 execute 전 호출" 설계가 미배선이었음 — 슬라이스 1-④에서 배선).
    """
    required = (meta or {}).get("params_required") or []
    for p in required:
        if params.get(p) in (None, ""):
            return {"reason": "missing_param", "param": p,
                    "detail": f"필수 param '{p}' 미바인딩 — 쿼리에서 채워지지 않음"}
    for p in SCOPE_PARAMS:
        v = params.get(p)
        if v is None:
            continue
        norm = "/".join(seg.strip() for seg in str(v).split("/"))
        if norm != v:
            params[p] = norm   # 공백 표기 정리(의미 불변 — coerce 아님). tool 도 이 정규화 값을 받는다.
        if not validate_scope_value(p, norm):
            return {"reason": "invalid_param", "param": p, "value": norm,
                    "detail": f"'{p}'={norm!r} — 선언된 스코프 형식 아님"}
    valid, errors = tool_inst.validate_params(params)
    if not valid:
        return {"reason": "invalid_param", "param": "", "detail": "; ".join(errors)}
    return None


async def _run_single_todo(
    todo: PlannedTodo,
    context: ExecutionContext,
    previous_results: dict[str, TodoResult],
) -> TodoResult:
    pool = get_agent_pool()
    agent_name = todo.agent or ""
    tool_name = todo.tool or ""
    started = time.time()

    if not tool_name:
        return TodoResult(
            todo_id=todo.id, task_type=todo.task_type, tool=None,
            agent=agent_name or None, status=TodoStatus.SKIPPED,
            data={"reason": "no tool assigned"}, is_mock=False,
            started_at=started, ended_at=started, duration_ms=0.0,
        )

    is_implemented = pool.is_tool_implemented(agent_name, tool_name)

    ctx = context.model_copy(
        update={
            "previous_results": {
                **(context.previous_results or {}),
                # COMPLETED 만 — SKIP/FAILED 의 사유 dict({reason, param, ...})가 LLM tool
                # payload·게이트 조회에 데이터인 척 유입 방지 (적대 리뷰 R-8). _inject 와 같은 기준.
                **{tid: r.data for tid, r in previous_results.items()
                   if r.status == TodoStatus.COMPLETED},
            }
        }
    )

    # ── B2.1 데이터 게이트: consumes artifact 가 충분히 도착했나 (silent-0 방지) ──
    # 완성 함수(311fb0f)는 "파이프 연결"을, 게이트는 "물 흐름"(받은 데이터 충분성)을 보장.
    # 불충분(0건/부재)이면 거짓 COMPLETED 대신 SKIPPED + 정밀 사유 → 하류 자연 cascade.
    # ctx.previous_results 로 검사 = tool 이 실제로 읽는 것과 동일 (find_in_previous).
    meta = pool.get_tool_meta(agent_name, tool_name) or {}
    insufficient = check_consume_sufficiency(
        meta.get("consumes") or [], ctx.previous_results or {}
    )
    if insufficient is not None:
        logger.info(
            "Todo skipped — 소비 데이터 불충분",
            todo_id=todo.id, tool=tool_name, artifact=insufficient["artifact"],
        )
        return TodoResult(
            todo_id=todo.id, task_type=todo.task_type, tool=tool_name,
            agent=agent_name, status=TodoStatus.SKIPPED,
            data=insufficient, is_mock=False,
            started_at=started, ended_at=started, duration_ms=0.0,
        )

    try:
        if is_implemented:
            tool_inst = pool.get_real_tool(tool_name)
            if tool_inst is None:
                raise RuntimeError(f"Real tool '{tool_name}' load failed")
            params = _inject_prev_outputs(todo.tool_params, previous_results)
            issue = _param_boundary_issue(meta, tool_inst, params)
            if issue is not None:
                ended = time.time()
                logger.info(
                    "Todo skipped — param 경계 위반",
                    todo_id=todo.id, tool=tool_name,
                    reason=issue.get("reason"), param=issue.get("param"),
                )
                return TodoResult(
                    todo_id=todo.id, task_type=todo.task_type, tool=tool_name,
                    agent=agent_name, status=TodoStatus.SKIPPED,
                    data=issue, is_mock=False,
                    started_at=started, ended_at=ended,
                    duration_ms=(ended - started) * 1000,
                )
            data = await tool_inst.execute(params, ctx)
        else:
            # (2026-06-12 stub 0) mock_result "되는 척" 경로 폐기 — "구현하면서 줄이자"
            # 원칙의 완결. 비구현 tool 이 카탈로그에 다시 들어오면 조용한 mock 대신
            # 시끄러운 실패 (헌법 I1). mock_tools.py 삭제 — 복원은 git 히스토리.
            raise RuntimeError(
                f"Tool '{tool_name}' under agent '{agent_name}' is not implemented "
                "(stub/mock 경로는 2026-06-12 폐지)"
            )

        ended = time.time()
        safe_data = _json_safe(data if isinstance(data, dict) else {"result": data})
        # silent-0 전파(stage2 ⒞): LLMTool 빈입력 가드가 {reason: data_insufficient} 반환 시
        # COMPLETED 로 조용히 흐르지 않게 SKIPPED 로 표시(data_gate 와 동일 convention) → 관측·정직 degrade.
        status = (
            TodoStatus.SKIPPED
            if isinstance(safe_data, dict) and safe_data.get("reason") == "data_insufficient"
            else TodoStatus.COMPLETED
        )
        return TodoResult(
            todo_id=todo.id, task_type=todo.task_type, tool=tool_name,
            agent=agent_name, status=status,
            data=safe_data,
            is_mock=False, started_at=started, ended_at=ended,
            duration_ms=(ended - started) * 1000,
        )

    except Exception as e:
        ended = time.time()
        logger.error("Todo execution failed", todo_id=todo.id, tool=tool_name, error=str(e))
        return TodoResult(
            todo_id=todo.id, task_type=todo.task_type, tool=tool_name,
            agent=agent_name, status=TodoStatus.FAILED, data={},
            error=f"{type(e).__name__}: {e}", is_mock=False,
            started_at=started, ended_at=ended,
            duration_ms=(ended - started) * 1000,
        )


def _inject_prev_outputs(
    params: dict[str, Any],
    previous_results: dict[str, TodoResult],
) -> dict[str, Any]:
    """상류 COMPLETED 산출을 미바인딩 param 에 주입 (artifact 체이닝).

    SCOPE_PARAMS(period 류)는 주입 금지 (슬라이스 1, 헌법 D3·R2) — 시간 스코프는
    쿼리에서만 온다. 상류의 'all'/라벨 값이 param 으로 흘러 startswith 0건
    silent-0 을 만들던 오염 경로 차단. 누락 시 경계가 SKIPPED → "기간을 알려주세요".
    """
    merged = dict(params)
    for r in previous_results.values():
        if r.status != TodoStatus.COMPLETED:
            continue
        if not isinstance(r.data, dict):
            continue
        for k, v in r.data.items():
            if k.startswith("_") or k in SCOPE_PARAMS:
                continue
            merged.setdefault(k, v)
    return merged


# ────────────────────────────────────────────────────────
# Phase 실행 (HITL PM 구조 — hitl_manager 지시용)
# ────────────────────────────────────────────────────────

async def execute_phase(
    todos: list[PlannedTodo],
    context: ExecutionContext,
    previous_results: dict[str, TodoResult] | None = None,
) -> list[TodoResult]:
    """Phase 단위 병렬 실행 — 결과만 반환.

    hitl_manager가 execution_stage 경유로 호출.
    상태 관리/이벤트 emit 없음 (그건 execution_stage + callback_manager의 역할).

    Args:
        todos: 이 Phase에서 실행할 Todo 리스트 (Pydantic PlannedTodo)
        context: ExecutionContext (session_id, plan_id)
        previous_results: 이전 Phase 결과 (Todo 간 데이터 체인용)

    Returns:
        list[TodoResult] — 실행 결과 (FAILED도 포함)
    """
    if not todos:
        return []

    previous_results = previous_results or {}
    results = await asyncio.gather(
        *[_run_single_todo(t, context, previous_results) for t in todos],
        return_exceptions=False,
    )
    return results


# ────────────────────────────────────────────────────────
# (작업 ⑬, 2026-05-31) Executor 클래스 폐기 — 死코드
# 활성 entry = execute_phase 함수 (위, line 226).
# 폐기 사유: Grep 결과 활성 `Executor()` 인스턴스화 0 hit (_old/_domains 만 매치).
# [死코드 즉시 폐기] 원칙 정합.
# ────────────────────────────────────────────────────────
