"""pipeline.py — 채널 translator: raw → cleaned canonical measures + lineage.

채널 spec(canonical contract 미러) + transforms(conversion config). matching(이름)=spec /
mapping(값)=transforms 분리. 출력 = 채널별 canonical measure 합 + lineage 샘플.
grain: meta ad_cost 는 performance 만(by_age/instagram = breakdown, 이중계상 방지).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml

import transforms as T

ROOT = Path(__file__).resolve().parents[3]     # repo root
RAW = ROOT / "data" / "clumi" / "raw"
PERIOD = "2026-04"

# 값변환 config(외부화) — currency rate table 을 코드 아닌 config 에서 (matching≠mapping, 리서치 ⓓ)
_CONFIG = yaml.safe_load((ROOT / "docs" / "agent_specs" / "ERD" / "octorad_conversion_config_v0.1.yaml").read_text(encoding="utf-8"))
CUR = T.make_currency_to_krw(_CONFIG["currency_rates"])   # (v, currency)→KRW. config effective-date rate (C2.2)


def _load(fp: Path):
    if fp.suffix == ".json":
        return json.loads(fp.read_text(encoding="utf-8"))
    with fp.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _rows(data, path):
    if path is None:
        return data if isinstance(data, list) else []
    return data.get(path, []) if isinstance(data, dict) else []


# ── 채널별 measure 추출 (row → {canonical: (raw_value, canonical_value, transform)}) ──
# canonical contract sources 미러. 의미함정·배열필터를 코드로 박제.

def m_meta(row):
    cur = row.get("account_currency", "KRW")   # ★통화 quirk: 실 USD 가능 → config rate table 로 KRW 환산(C2.2). mock=KRW(identity)
    return {
        "ad_cost_krw":            (row.get("spend"),         CUR(row.get("spend"), cur),           f"cast_int+currency_to_krw({cur})"),
        "impressions":            (row.get("impressions"),   T.cast_int(row.get("impressions")),   "cast_int"),
        "clicks":                 (row.get("clicks"),        T.cast_int(row.get("clicks")),        "cast_int"),
        "conversion_count":       ("actions[omni_purchase]", T.meta_action_extract(row.get("actions")),                     "meta_action_extract"),
        "conversion_revenue_krw": ("action_values[omni]",    CUR(T.meta_action_extract(row.get("action_values")), cur),     f"meta_action_extract+currency_to_krw({cur})"),
    }


def m_naver_sa(row):
    return {
        "ad_cost_krw":            (row.get("salesAmt"), T.cast_int(row.get("salesAmt")), "cast_int (salesAmt=비용)"),
        "conversion_revenue_krw": (row.get("convAmt"),  T.cast_int(row.get("convAmt")),  "cast_int (convAmt=매출)"),
        "conversion_count":       (row.get("ccnt"),     T.cast_int(row.get("ccnt")),     "cast_int (ccnt=전환수)"),
        "impressions":            (row.get("impCnt"),   T.cast_int(row.get("impCnt")),   "cast_int"),
        "clicks":                 (row.get("clkCnt"),   T.cast_int(row.get("clkCnt")),   "cast_int"),
    }


def m_advoost(row):
    return {
        "ad_cost_krw":            (row.get("cost"),                      T.cast_int(row.get("cost")),                      "cast_int"),
        "conversion_revenue_krw": (row.get("conversion_value"),         T.cast_int(row.get("conversion_value")),         "cast_int"),
        "conversion_count":       (row.get("click_through_conversions"), T.cast_int(row.get("click_through_conversions")), "cast_int (CT only)"),
        "impressions":            (row.get("impressions"),              T.cast_int(row.get("impressions")),              "cast_int"),
        "clicks":                 (row.get("clicks"),                   T.cast_int(row.get("clicks")),                   "cast_int"),
    }


def m_google(row):
    # google_ads_performance.csv — flat CSV, 값 KRW(mock). advoost 와 동형(광고 매체).
    return {
        "ad_cost_krw":            (row.get("cost"),             T.cast_int(row.get("cost")),             "cast_int"),
        "conversion_revenue_krw": (row.get("conversion_value"), T.cast_int(row.get("conversion_value")), "cast_int"),
        "conversion_count":       (row.get("conversions"),      T.cast_int(row.get("conversions")),      "cast_int"),
        "impressions":            (row.get("impressions"),      T.cast_int(row.get("impressions")),      "cast_int"),
        "clicks":                 (row.get("clicks"),           T.cast_int(row.get("clicks")),           "cast_int"),
    }


def _summary(row):
    return row.get("summary", {}) if isinstance(row, dict) else {}


def m_kakao(row):
    s = _summary(row)
    # ★C6.3: 메시징은 msg_ measure (광고 ad_cost/conversion 과 분리)
    return {
        "msg_cost_krw":               (s.get("total_cost_krw"),        T.cast_int(s.get("total_cost_krw")),        "cast_int (메시징비, C6.3 ad 분리)"),
        "msg_conversion_revenue_krw": (s.get("conversion_amount_krw"), T.cast_int(s.get("conversion_amount_krw")), "cast_int"),
        "msg_conversion_count":       (s.get("conversion_count"),      T.cast_int(s.get("conversion_count")),      "cast_int"),
    }


m_talktalk = m_kakao   # 동일 구조


def m_orders(row):
    return {"order_revenue_krw": (row.get("payment_amount"), T.cast_int(row.get("payment_amount")), "cast_int")}


CHANNELS = [
    {"channel": "meta",     "file": "meta_ads_performance.json", "rows_path": "data", "period": ("date_start", "2026-04"), "measures": m_meta,
     "note": "performance 만 (by_age/instagram_inapp=breakdown 제외, 이중계상 방지)"},
    {"channel": "naver_sa", "file": "naver_searchad.json",       "rows_path": "data", "period": ("statDt", "2026-04"),     "measures": m_naver_sa,
     "note": "★PILOT 적발: statDt=ISO '2026-04-01' (사전/SPEC yyyymmdd 오기). config statDt transform 정정 필요"},
    {"channel": "advoost",  "file": "naver_advoost.csv",         "rows_path": None,   "period": ("report_date", "2026-04"), "measures": m_advoost},
    {"channel": "google",   "file": "google_ads_performance.csv", "rows_path": None,   "period": ("report_date", "2026-04"), "measures": m_google,
     "note": "가 결정 — google 광고 매체 포함(re-baseline 26.8M/4.46). flat CSV·KRW."},
    {"channel": "kakao",    "file": "kakao_bizmessage.json",     "rows_path": "campaigns", "period": None,                  "measures": m_kakao, "note": "summary 단위(기간 분리 X)"},
    {"channel": "talktalk", "file": "naver_talktalk.json",       "rows_path": "campaigns", "period": None,                  "measures": m_talktalk},
]

# orders = 매출(mer 분자). 활성주문(C40 제외) + 4월.
ORDERS = {"channel": "orders", "file": "orders.csv", "rows_path": None, "period": ("order_date", "2026-04"),
          "row_filter": lambda r: r.get("order_status") != "C40", "measures": m_orders}


def translate(ch: dict) -> dict:
    """채널 raw → cleaned canonical measures(합) + lineage 샘플."""
    data = _load(RAW / ch["file"])
    rows = _rows(data, ch.get("rows_path"))
    pf = ch.get("period")
    rfilt = ch.get("row_filter")
    sums: dict[str, int] = {}
    lineage: list[dict] = []
    n = 0
    for row in rows:
        if pf and not str(row.get(pf[0], "")).startswith(pf[1]):
            continue
        if rfilt and not rfilt(row):
            continue
        n += 1
        for canon, (raw, val, tname) in ch["measures"](row).items():
            if val is None:
                continue
            sums[canon] = sums.get(canon, 0) + val
            if len([l for l in lineage if l["canonical"] == canon]) < 1:   # canonical 당 1 샘플
                lineage.append({"channel": ch["channel"], "canonical": canon,
                                "source": raw, "value": val, "transform": tname})
    return {"channel": ch["channel"], "rows": n, "measures": sums,
            "lineage_sample": lineage, "note": ch.get("note")}


def run_normalize() -> dict:
    """raw → cleaned: 전 채널 translate. {channel: result}."""
    out = {ch["channel"]: translate(ch) for ch in CHANNELS}
    out["orders"] = translate(ORDERS)
    return out
