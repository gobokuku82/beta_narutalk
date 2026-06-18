"""State Guard (L3) — 제어 평면(state/checkpoint) 입구 크기 게이트.

근본원인 (docs/reports/근본원인_execution_state_raw누수_2026-06-11.md):
  collector 가 raw 데이터셋(GA4 38,319행=104MB)을 결과로 반환 → execution_result 채널
  → checkpoint 155MB·WS ~312MB·복원 5.5s. 소비자 전수 감사 결과 그 raw 를 state 에서
  읽는 곳 0 (downstream 은 data 레이어 직접 조회).

본질: 성능 패치가 아니라 **두 평면의 경계 강제** —
  - 데이터 평면(창고, data 레이어) = 데이터셋이 사는 곳 (raw/cleaned/computed + save/get)
  - 제어 평면(state/checkpoint)    = 오케스트레이션 기록 (요약·참조·소형 산출만)
  tool 반환값이 프레임워크에 의해 *암묵 저장*되므로, 각 tool 의 컨벤션 준수 기대가 아니라
  경계에서 결정론 게이트로 강제한다 (게이트 > 컨벤션 — doc 39 §5 교훈과 동형).

적용 지점: execution_stage._build_execution_result 출력 (state 진입 직전, 단 1곳).
불변식: **in-memory 체이닝(hitl completed_todos → previous_results)은 불변** —
  슬림은 state 사본에만. 리뷰 체인·데이터 게이트(consumes)·resume 무영향 (계획 §2.1·§3).

Status: complete — L3 임계치 슬림. L3b(pause snapshot)·L4(collector 참조 반환)는 후속.
계획: docs/reports/계획_state경계게이트_L3L5_2026-06-11.md
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

# 임계치 — 이 크기를 넘는 *값*은 state 에 못 들어온다 (참조 스텁으로 치환).
# responder 가 읽는 정당 산출(metric 스칼라·summary/report 문자열·파일경로)은 전부 이보다
# 한참 작고, 데이터셋(수만 행)은 한참 크다 — 감사 §7.2-4. settings 로 override 가능.
_DEFAULT_MAX = 256 * 1024


def _max_bytes() -> int:
    try:
        from app.core.config import settings
        return int(getattr(settings, "STATE_VALUE_MAX_BYTES", _DEFAULT_MAX))
    except Exception:
        return _DEFAULT_MAX


# 모듈 상수 (테스트·문서 참조용 기본값)
STATE_VALUE_MAX_BYTES = _DEFAULT_MAX


def approx_json_size(value: Any, budget: int) -> int:
    """JSON 직렬화 크기 *추정* — budget 초과 시 조기탈출 (104MB 를 dumps 하지 않는다).

    정확도보다 자릿수: 게이트 판정엔 "256KB 근방인가 vs 100MB 인가"면 충분.
    반환값이 budget 을 넘으면 "초과" 의미 (정확한 총량 아님 — 탐색 중단 시점의 누적치).
    """
    stack: list[Any] = [value]
    total = 0
    while stack:
        if total > budget:
            return total  # 조기탈출 — 전량 순회 금지
        v = stack.pop()
        if v is None or isinstance(v, bool):
            total += 5
        elif isinstance(v, (int, float)):
            total += 12
        elif isinstance(v, str):
            total += len(v) + 2
        elif isinstance(v, dict):
            total += 2
            for k, item in v.items():
                total += len(str(k)) + 4
                stack.append(item)
        elif isinstance(v, (list, tuple, set)):
            total += 2 + len(v)
            stack.extend(v)
        else:
            total += len(str(v)) + 2
    return total


def _stub(key: str, size: int) -> dict[str, Any]:
    """치환 스텁 — 무엇이 왜 빠졌고 원본이 어디 사는지."""
    return {
        "_state_guard": "slimmed",
        "key": key,
        "size_bytes_approx": size,
        "where": "data 레이어(창고)에서 직접 조회 — 대용량 값은 state/checkpoint 비저장 정책",
    }


def slim_execution_result(er: dict[str, Any]) -> dict[str, Any]:
    """execution_result dict 의 todos[*].data top-level 값 중 임계치 초과분을 스텁 치환.

    - 새 dict 반환 (원본·hitl completed_todos 불변 — in-memory 체이닝 보존).
    - data 의 top-level 키 단위로만 판정 (tool 반환 계약 단위 = produces key).
    - 슬림 발생 시 warning 로그 → 다음 누수는 미스터리가 아니라 로그 한 줄.
    """
    if not isinstance(er, dict):
        return er
    todos = er.get("todos")
    if not isinstance(todos, dict) or not todos:
        return er

    limit = _max_bytes()
    new_todos: dict[str, Any] = {}
    changed = False
    for tid, todo in todos.items():
        data = todo.get("data") if isinstance(todo, dict) else None
        if not isinstance(data, dict) or not data:
            new_todos[tid] = todo
            continue
        new_data: dict[str, Any] = {}
        for k, v in data.items():
            size = approx_json_size(v, budget=limit)
            if size > limit:
                new_data[k] = _stub(k, size)
                changed = True
                logger.warning(
                    "state_guard slimmed — 대용량 값이 state 진입 차단됨",
                    todo_id=tid,
                    tool=todo.get("tool"),
                    key=k,
                    size_bytes_approx=size,
                    limit=limit,
                )
            else:
                new_data[k] = v
        new_todos[tid] = {**todo, "data": new_data} if isinstance(todo, dict) else todo

    if not changed:
        return er
    return {**er, "todos": new_todos}


__all__ = ["STATE_VALUE_MAX_BYTES", "approx_json_size", "slim_execution_result"]
