"""주문 데이터 공통 helper — cleaning + metrics 가 공유하는 활성주문·기간 필터.

배경:
    cleaning/active_orders_filter 와 metrics 의 *모든 매출/주문 집계* tool 이
    동일한 활성주문 필터 (order_status != 'C40') + 기간 필터 (order_date YYYY-MM prefix)
    를 반복. methodology §정제 1 의 정의 그대로.

이 helper 가 단일 진실원 — methodology 정의 변경 시 본 파일 1곳만 수정.

Status: complete — 2026-05-23 metrics 진입 시 추출.
"""
from __future__ import annotations

import pandas as pd

# methodology_cleaning §정제 1 — 활성주문 정의 단일 SSOT (ADR-032 D3, 2026-06-17: C40만 → C계열 전체 제외)
CANCELLED_PREFIX = "C"          # 취소 코드군(Cafe24 C계열: C00·C40 등) 전체
CANCELLED_STATUS = "C40"        # deprecated alias(후방호환) — is_active_order/CANCELLED_PREFIX 사용 권장


def is_active_order(status) -> bool:
    """활성주문 판정 = 취소(C계열) 전체 제외 (ADR-032 D3). 단일 술어 — 전 tool이 이걸 참조.

    ⚠ N00(입금전)은 N계열이라 *포함*(=매출 인정). 결제완료만 인정하려면 별도 변경 = 오너/UX 영역.
    None/빈값/키누락 → str()로 graceful(활성 취급, 크래시 없음).
    """
    return not str(status).startswith(CANCELLED_PREFIX)


def filter_active_orders(df: pd.DataFrame, period: str | None = None) -> pd.DataFrame:
    """활성 주문 필터 + 선택적 기간 필터.

    Args:
        df: orders raw DataFrame (self.fetch("orders", context))
        period: None=전체, 'YYYY-MM'=단월, 'YYYY-MM/YYYY-MM'=구간

    Returns:
        활성 주문 (order_status != 'C40') 의 DataFrame
        + period 가 주어지면 order_date YYYY-MM prefix 매치
    """
    df_active = df[df["order_status"].map(is_active_order)]
    if period is None:
        return df_active
    if "/" in period:
        start, end = period.split("/")
        return df_active[df_active["order_date"].str[:7].between(start, end)]
    return df_active[df_active["order_date"].str.startswith(period)]


def filter_period(df: pd.DataFrame, period: str, date_col: str = "order_date") -> pd.DataFrame:
    """단순 기간 필터 (활성 무관). date_col 의 YYYY-MM prefix 매치.

    metrics tool 이 *전체 주문* (취소 포함) 분석할 때 사용.
    """
    if "/" in period:
        start, end = period.split("/")
        return df[df[date_col].str[:7].between(start, end)]
    return df[df[date_col].str.startswith(period)]


__all__ = ["CANCELLED_PREFIX", "CANCELLED_STATUS", "is_active_order", "filter_active_orders", "filter_period"]
