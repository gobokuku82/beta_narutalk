"""Tool 공통 헬퍼.

- find_in_previous: 이전 Todo 결과에서 특정 produces 키 탐색 (data_gate + tool 공용)

참고: load_mock_csv + MOCK_DATA_DIR 死코드는 활성 호출자 0 으로 이미 폐기됨.
(2026-07-02) CHANNEL_MAP·SENTIMENT_MAP·normalize_channel·normalize_sentiment·parse_percent
제거 — 구 마케팅 도메인 잔재 + 호출자 0. 죽은 코드는 즉시 폐기한다.
"""

from __future__ import annotations

from typing import Any, Optional


def find_in_previous(
    previous_results: dict[str, Any],
    produces_key: str,
) -> Optional[Any]:
    """이전 Todo 결과들에서 특정 produces 키를 탐색해 반환.

    ExecutionContext.previous_results 구조:
        { todo_id: {"data": {...}, "status": "success", ...}, ... }
    또는
        { todo_id: {...tool_output...}, ... }

    Args:
        previous_results: 이전 Todo 실행 결과 딕셔너리
        produces_key: 찾을 키 (예: "raw_records", "normalized_records")

    Returns:
        첫 번째로 발견된 값. 없으면 None.
    """
    if not previous_results:
        return None

    for result in previous_results.values():
        if not isinstance(result, dict):
            continue
        # 1) result["data"][key] 형태
        data = result.get("data")
        if isinstance(data, dict) and produces_key in data:
            return data[produces_key]
        # 2) result[key] 형태 (flat)
        if produces_key in result:
            return result[produces_key]

    return None


__all__ = [
    "find_in_previous",
]
