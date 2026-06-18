"""Data Gate (B2.1) — tool 경계 non-empty 소비 계약 검사.

완성 함수(complete_dataflow_chain, 311fb0f)가 "파이프 연결"(올바른 tool 이 체인에
있음)을 보장한 위에, 이 게이트는 "물 흐름"(받은 데이터가 충분함)을 검사한다.

각 tool 은 카탈로그에 선언한 `consumes` artifact 를 **존재 + non-empty** 로 받아야
실행이 의미 있다. 위반 시 executor 가 silent-0 거짓 성공(0건인데 COMPLETED) 대신
SKIPPED + 정밀 사유(어느 artifact 가 0건/부재)로 만들어, 하류 무의미 계산을 생략하고
정직 응답으로 전파한다.

설계 원칙:
  - 결정론 검사 (LLM 눈치 의존 X). 순수 함수.
  - 조회는 find_in_previous 를 그대로 써서 "게이트가 검사한 것 = tool 이 실제로
    읽는 것" 을 보장 (tools/shared/helpers).
  - consumes 미선언 tool 은 무검사 → false positive 0, 점진 확대.
  - non-empty 만 (B2.1). shape(필드)·semantic 은 B2.2/B2.3 별도 phase.

Status: complete — B2.1 non-empty 계약 게이트.
Reference: docs/_claude/4layer_system/b2_data_sufficiency_intent_and_plan_260605_v2.md §5
"""

from __future__ import annotations

from typing import Any

from app.dream_agent.tools.shared.helpers import find_in_previous


def _is_empty(value: Any) -> bool:
    """artifact 값이 '불충분(0건/부재)' 인가.

    None = 부재. list/dict/str 은 길이 0 이면 빈. 숫자/bool 은 '값 있음'(0 도 값) —
    consumes 는 보통 컬렉션이지만 스칼라가 와도 over-block 하지 않는다.
    """
    if value is None:
        return True
    if isinstance(value, (list, dict, str)):
        return len(value) == 0
    return False


def check_consume_sufficiency(
    consumes: list[str],
    previous: dict[str, Any],
) -> dict[str, str] | None:
    """tool 의 consumes artifact 가 previous_results 에 존재 + non-empty 인지 검사.

    Args:
        consumes: tool 이 카탈로그에 선언한 소비 artifact 이름들.
        previous: 이전 Todo 결과 (executor 가 넘기는 {todo_id: data} 또는
            {todo_id: {"data": ...}} 형태 — find_in_previous 가 양쪽 처리).

    Returns:
        충분하면 None. 부족하면 첫 불충분 artifact 의
        {"reason": "data_insufficient", "artifact": <이름>, "detail": "<이름> 0건/부재"}.
    """
    for art in consumes:
        value = find_in_previous(previous, art)
        if isinstance(value, dict) and value.get("_dataref"):
            # L4 참조 스텁(collector 데이터셋 비탑재 정책, 85ef5de) — 스텁 dict 는 항상
            # truthy 라 존재성 검사를 통과하므로 실데이터 양은 count 로 판정.
            # 근본원인 보고서 §9.3-1: 이게 없으면 0건 수집이 게이트를 지나 silent-0 재발.
            if not value.get("count"):
                return {
                    "reason": "data_insufficient",
                    "artifact": art,
                    "detail": f"{art} 0건 (dataref — 수집 결과 없음)",
                }
            continue
        if _is_empty(value):
            kind = "부재" if value is None else "0건"
            return {
                "reason": "data_insufficient",
                "artifact": art,
                "detail": f"{art} {kind}",
            }
    return None


__all__ = ["check_consume_sufficiency"]
