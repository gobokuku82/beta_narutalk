"""결측값 처리 공통 helper — cleaning tool 의 NaN/None/빈문자열 정규화 utility.

배경:
    pandas DataFrame 의 비어있는 셀은 object dtype 에서도 `float('nan')` 으로 들어옴.
    `bool(NaN) = True` / `str(NaN) = 'nan'` 이라 단순 `if v:` / `str(v)` 비교가
    false positive 양산 (member_metrics_validator 디버그 시 6,333건 발견).

설계:
    - is_missing(v): None · NaN · 빈문자열 통일 판정
    - safe_int(v, default=0): 결측 → default, 아니면 int(float(v))
    - safe_float(v, default=0.0)
    - safe_str(v, default=""): NaN → "", 아니면 str(v).strip()
    - null_stats(df): 컬럼별 결측 통계 (null_count·null_rate·dtype)
    - classify_missing(col_name, df, semantic_nulls): 의미있는 NaN vs 데이터 누락 분류

사용:
    from app.dream_agent.tools.shared.missing_helper import safe_int, safe_str, is_missing

Status: complete — 2026-05-23 cleaning 3 누적 시 추출 + 정제 1/3 의 NaN 처리 통합.
"""
from __future__ import annotations

import math
from typing import Any

import pandas as pd


def is_missing(v: Any) -> bool:
    """None · float NaN · 빈문자열 · pandas NA 통일 판정."""
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    if isinstance(v, str) and v.strip() == "":
        return True
    try:
        # pandas.NA / NaT 도 처리
        return bool(pd.isna(v))
    except (TypeError, ValueError):
        return False


def safe_int(v: Any, default: int = 0) -> int:
    """결측 → default, 아니면 int(float(v))."""
    if is_missing(v):
        return default
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return default


def safe_float(v: Any, default: float = 0.0) -> float:
    """결측 → default, 아니면 float(v)."""
    if is_missing(v):
        return default
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


def safe_str(v: Any, default: str = "") -> str:
    """결측 → default, 아니면 str(v).strip()."""
    if is_missing(v):
        return default
    return str(v).strip()


def null_stats(df: pd.DataFrame) -> list[dict]:
    """DataFrame 의 컬럼별 결측 통계.

    Returns:
        [{column, dtype, total, null_count, null_rate}, ...]
    """
    total = len(df)
    out = []
    for col in df.columns:
        # is_missing 의 의미와 일치하는 카운트 (NaN + 빈문자열)
        ser = df[col]
        null_count = 0
        for v in ser:
            if is_missing(v):
                null_count += 1
        out.append({
            "column": col,
            "dtype": str(ser.dtype),
            "total": total,
            "null_count": null_count,
            "null_rate": round(null_count / total, 4) if total else 0.0,
        })
    return out


def classify_missing(
    column_stats: list[dict],
    semantic_nulls: dict[str, str] | None = None,
) -> list[dict]:
    """결측을 '의미있는 NaN' vs '데이터 누락' 으로 분류.

    semantic_nulls 예: {
        "last_order_date": "비주문 회원 → NaN 은 의미있음",
        "member_id": "비회원 주문 → 빈값 의미있음",
    }

    Returns: column_stats 에 classification·reason 필드 추가.
    """
    semantic = semantic_nulls or {}
    out = []
    for s in column_stats:
        col = s["column"]
        rate = s["null_rate"]
        if rate == 0:
            classification, reason = "complete", "no nulls"
        elif col in semantic:
            classification, reason = "semantic", semantic[col]
        elif rate < 0.05:
            classification, reason = "minor_gap", f"{rate*100:.1f}% 누락 — 무시 가능"
        elif rate < 0.5:
            classification, reason = "partial_gap", f"{rate*100:.1f}% 누락 — 검토 필요"
        else:
            classification, reason = "major_gap", f"{rate*100:.1f}% 누락 — 데이터 품질 이슈 가능"
        out.append({**s, "classification": classification, "reason": reason})
    return out


__all__ = [
    "is_missing",
    "safe_int",
    "safe_float",
    "safe_str",
    "null_stats",
    "classify_missing",
]
