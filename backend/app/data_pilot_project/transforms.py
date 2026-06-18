"""transforms.py — conversion config 의 변환 op 구현 (값 mapping 실행기).

octorad_conversion_config_v0.1.yaml 의 transform primitive 를 코드로. 값 변환(mapping)을
이름 매핑(contract)과 분리한다(리서치 ⓓ). 각 함수 = raw 값 → canonical 값.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))


def cast_int(v):
    if v is None or v == "":
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def cast_float2(v):
    if v is None or v == "":
        return None
    try:
        return round(float(v), 2)
    except (ValueError, TypeError):
        return None


def pct_to_ratio(v):
    """percent → 배수 (Naver ror, advoost roas). C1.1."""
    f = cast_float2(v)
    return round(f / 100, 4) if f is not None else None


def yyyymmdd_to_date(v):
    """int/str yyyymmdd → 'YYYY-MM-DD' (Naver statDt). C4.1."""
    s = str(v).strip()
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if len(s) == 8 and s.isdigit() else None


def utc_date_to_kst(v):
    """GA4 event_date(YYYYMMDD, UTC) → KST date. 자정경계 +/-1일 — 단순 파일럿은 날짜만."""
    return yyyymmdd_to_date(v)  # 파일럿: 일자 단위라 shift 생략(실구현은 시각까지 필요)


def micros_epoch_to_kst(v):
    """GA4 event_timestamp(마이크로초 epoch) → KST ISO8601. C3.1."""
    try:
        return datetime.fromtimestamp(int(v) / 1_000_000, KST).isoformat()
    except (ValueError, TypeError):
        return None


def sec_epoch_to_kst(v):
    try:
        return datetime.fromtimestamp(int(v), KST).isoformat()
    except (ValueError, TypeError):
        return None


def make_currency_to_krw(currency_rates):
    """config currency_rates(effective date 테이블) → 변환 함수. C2.2."""
    table = {r["currency"]: r["to_krw"] for r in currency_rates}

    def convert(v, currency="KRW"):
        amt = cast_int(v)
        if amt is None:
            return None
        return int(amt * table.get(currency, 1.0))

    return convert


def meta_action_extract(actions, action_type="omni_purchase"):
    """Meta actions[]/action_values[]/purchase_roas[] = [{action_type, value}] 에서
    action_type 필터 → value. 미필터 추출 시 silent-0 (C6.2). 없으면 0.
    """
    if not isinstance(actions, list):
        return 0
    for a in actions:
        if isinstance(a, dict) and a.get("action_type") == action_type:
            return cast_int(a.get("value")) or 0
    return 0


def meta_roas_extract(purchase_roas):
    """purchase_roas[] 에서 omni_purchase value(배수) → float. ÷100 없음(Meta=배수)."""
    if not isinstance(purchase_roas, list):
        return None
    for a in purchase_roas:
        if isinstance(a, dict) and a.get("action_type") == "omni_purchase":
            return cast_float2(a.get("value"))
    return None


# rule_id → callable (config 참조). currency 는 런타임 바인딩.
REGISTRY = {
    "cast_int": cast_int,
    "cast_float2": cast_float2,
    "pct_to_ratio": pct_to_ratio,
    "yyyymmdd_to_date": yyyymmdd_to_date,
    "utc_date_to_kst": utc_date_to_kst,
    "micros_epoch_to_kst": micros_epoch_to_kst,
    "sec_epoch_to_kst": sec_epoch_to_kst,
    "meta_action_extract": meta_action_extract,
    "meta_roas_extract": meta_roas_extract,
}
