"""POC Tool 공통 헬퍼.

- find_in_previous: 이전 Todo 결과에서 특정 produces 키 탐색
- normalize_channel: 매체명 정규화 (네이버→naver 등)
- normalize_sentiment: 감성 라벨 정규화
- parse_percent: "12.3%" 문자열 → 12.3 float

작업 ⑫ 후속 (2026-06-01): load_mock_csv + MOCK_DATA_DIR 死코드 폐기.
사유: broken 6 collector (작업 ⑫.A·B) 폐기 후 활성 호출자 0.
data/mock/ 디렉토리도 2026-05-28 이미 폐기. 사용자 [死코드 즉시 폐기] 원칙.
"""

from __future__ import annotations

from typing import Any, Optional


CHANNEL_MAP: dict[str, str] = {
    # 한글
    "네이버": "naver",
    "카카오": "kakao",
    "메타": "meta",
    "페이스북": "meta",
    "인스타": "meta",
    "인스타그램": "meta",
    "구글": "google",
    "유튜브": "youtube",
    "쿠팡": "coupang",
    "올리브영": "oliveyoung",
    # 영문 (이미 정규화됨 or 변형)
    "naver": "naver",
    "kakao": "kakao",
    "meta": "meta",
    "facebook": "meta",
    "instagram": "meta",
    "google": "google",
    "youtube": "youtube",
    "coupang": "coupang",
    "oliveyoung": "oliveyoung",
}


SENTIMENT_MAP: dict[str, str] = {
    "긍정": "positive",
    "중립": "neutral",
    "부정": "negative",
    "positive": "positive",
    "neutral": "neutral",
    "negative": "negative",
}


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
        produces_key: 찾을 키 (예: "raw_reviews", "normalized_reviews")

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


def normalize_channel(value: Optional[str]) -> Optional[str]:
    """매체명을 정규화된 영문 키로 변환.

    예: "네이버" → "naver", "Meta" → "meta", "unknown" → "unknown" (lower).
    """
    if value is None:
        return None
    key = str(value).strip()
    return CHANNEL_MAP.get(key, key.lower())


def normalize_sentiment(value: Optional[str]) -> Optional[str]:
    """감성 라벨을 정규화: 긍정/중립/부정 → positive/neutral/negative."""
    if value is None:
        return None
    return SENTIMENT_MAP.get(str(value).strip(), value)


def parse_percent(value: Any) -> Optional[float]:
    """\"12.3%\" / \"12.3\" / 12.3 → 12.3 (float). 실패 시 None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        s = str(value).strip().rstrip("%").strip()
        return float(s)
    except (ValueError, AttributeError):
        return None


__all__ = [
    "CHANNEL_MAP",
    "SENTIMENT_MAP",
    "find_in_previous",
    "normalize_channel",
    "normalize_sentiment",
    "parse_percent",
]
