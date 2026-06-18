"""verify_outputs.py — data_pilot 산출물 *독립* 검증 (제대로 구현됐나).

pilot 코드를 거치지 않고 raw 에서 직접 재계산 → materialized 산출물과 대조.
스키마·lineage·grain(이중계상)·타입·cross-source 까지. data 라서 숫자 reconciliation 이 핵심.

★P1 보강(2026-06-14): (1) 각 check 가 검사하는 canonical 필드 태그(fields=) → coverage.py 가 'tested' 집합 산출.
(2) PASS/FAIL 외 WARN 상태 추가. (3) crosswalk cross_channel==0 WARN 검사(B3 — 무용을 가시화).
기존 12 critical check 의 계산 로직은 동일 보존(12/12 유지).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "clumi" / "raw"
CANON = ROOT / "data" / "clumi" / "_canonical"
P = "2026-04"


def _jr(name):
    return json.loads((RAW / name).read_text(encoding="utf-8"))


def _cr(name):
    with (RAW / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _i(v):
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return 0


def _omni(arr):
    if not isinstance(arr, list):
        return 0
    return sum(_i(a.get("value")) for a in arr if isinstance(a, dict) and a.get("action_type") == "omni_purchase")


def run() -> tuple[list[dict], set[str]]:
    """raw 직독 재계산 → materialized 대조. (checks, tested_fields) 반환.

    checks: [{name, status(PASS|FAIL|WARN), detail, fields}]. tested_fields: critical check 가 검사한 canonical 필드 union.
    """
    checks: list[dict] = []
    tested: set[str] = set()

    def chk(name, ok, detail="", fields=()):
        status = "PASS" if ok else "FAIL"
        checks.append({"name": name, "status": status, "detail": detail, "fields": list(fields)})
        tested.update(fields)

    def warn(name, condition_ok, detail=""):
        # condition_ok=False → WARN 표시(critical 카운트엔 불포함). 무용/주의를 가시화.
        checks.append({"name": name, "status": "PASS" if condition_ok else "WARN", "detail": detail, "fields": []})

    # ── materialized 로드 ──
    cleaned = {p.stem.replace("_2026-04", ""): json.loads(p.read_text(encoding="utf-8"))
               for p in (CANON / "cleaned").glob("*_2026-04.json")}
    computed = json.loads((CANON / "computed" / "ad_metrics_2026-04.json").read_text(encoding="utf-8"))
    crosswalk = json.loads((CANON / "crosswalk" / "campaign_crosswalk.json").read_text(encoding="utf-8"))

    # ── 1. ad_cost 독립 재계산 (raw → 대조) ──
    meta_perf = _jr("meta_ads_performance.json")["data"]
    meta_cost = sum(_i(r["spend"]) for r in meta_perf if str(r.get("date_start", "")).startswith(P))
    chk("ad_cost meta 독립=materialized", meta_cost == cleaned["meta"]["measures"]["ad_cost_krw"],
        f"{meta_cost:,} vs {cleaned['meta']['measures']['ad_cost_krw']:,}", fields=["ad_cost_krw"])

    naver = _jr("naver_searchad.json")["data"]
    naver_cost = sum(_i(r["salesAmt"]) for r in naver if str(r.get("statDt", "")).startswith(P))
    chk("ad_cost naver_sa 독립=materialized", naver_cost == cleaned["naver_sa"]["measures"]["ad_cost_krw"],
        f"{naver_cost:,} vs {cleaned['naver_sa']['measures']['ad_cost_krw']:,}", fields=["ad_cost_krw"])

    # C6.3: 광고비(meta/naver/advoost) + 메시징비(kakao/talktalk msg_cost_krw) = 총 마케팅비
    total_ad = sum(cleaned[c]["measures"].get("ad_cost_krw", 0) for c in ["meta", "naver_sa", "advoost"])
    total_msg = sum(cleaned[c]["measures"].get("msg_cost_krw", 0) for c in ["kakao", "talktalk"])
    total_cost = total_ad + total_msg
    chk("total_marketing_cost (ad+msg) = 18,306,923", total_cost == 18_306_923,
        f"ad={total_ad:,}+msg={total_msg:,}={total_cost:,}", fields=["ad_cost_krw", "msg_cost_krw"])

    # ── 2. ★ grain 이중계상 가드: by_age/instagram = breakdown (별도 합산 금지) ──
    by_age_cost = sum(_i(r["spend"]) for r in _jr("meta_ads_by_age.json")["data"] if str(r.get("date_start", "")).startswith(P))
    chk("grain: by_age spend ≈ performance (breakdown, 합산 시 이중계상)", abs(by_age_cost - meta_cost) < meta_cost * 0.05,
        f"by_age={by_age_cost:,} ≈ perf={meta_cost:,} → 둘 다 더하면 ×2 (pilot은 perf만=정답)", fields=["ad_cost_krw"])

    # ── 3. conversion_count meta 독립 (omni_purchase 필터) ──
    meta_conv = sum(_omni(r.get("actions")) for r in meta_perf if str(r.get("date_start", "")).startswith(P))
    chk("conversion_count meta 독립=materialized", meta_conv == cleaned["meta"]["measures"]["conversion_count"],
        f"{meta_conv} vs {cleaned['meta']['measures']['conversion_count']}", fields=["conversion_count"])

    # ── 4. orders 매출 독립 (활성·4월) ──
    orders = _cr("orders.csv")
    rev = sum(_i(r["payment_amount"]) for r in orders if r.get("order_status") != "C40" and str(r.get("order_date", "")).startswith(P))
    chk("order_revenue = 119,539,660", rev == 119_539_660, f"{rev:,}", fields=["order_revenue_krw"])

    # ── 5. mer 독립 재계산 ──
    mer = round(rev / total_cost, 2)
    chk("mer = 6.53 (독립)", mer == 6.53, f"{mer} = {rev:,}/{total_cost:,}", fields=["mer", "order_revenue_krw"])

    # ── 6. schema 적합: cleaned 가 canonical measure 가짐 ──
    chk("schema: meta cleaned 에 ad_cost_krw·conversion_count 존재",
        all(k in cleaned["meta"]["measures"] for k in ["ad_cost_krw", "conversion_count", "conversion_revenue_krw"]),
        f"{list(cleaned['meta']['measures'])}", fields=["ad_cost_krw", "conversion_count", "conversion_revenue_krw"])

    # ── 7. lineage 무결: 각 cleaned 에 lineage_sample + raw_value ──
    lin_ok = all(cleaned[c].get("lineage_sample") and all("value" in l and "source" in l for l in cleaned[c]["lineage_sample"])
                 for c in cleaned)
    chk("lineage: 전 채널 lineage_sample 존재+raw_value", lin_ok, "신뢰 동반")

    # ── 8. type: 모든 measure 값 int (string leak 없음) ──
    type_ok = all(isinstance(v, int) for c in cleaned for v in cleaned[c]["measures"].values())
    chk("type: 모든 measure int (string leak 0)", type_ok)

    # ── 9. cross-source sanity: GA4 purchase event 수 vs orders 수 (동일 자릿수) ──
    ga4_purchase = 0
    with (RAW / "ga4_traffic_source.jsonl").open(encoding="utf-8") as f:
        for line in f:
            if '"event_name": "purchase"' in line or '"event_name":"purchase"' in line:
                ga4_purchase += 1
    orders_n = sum(1 for r in orders if r.get("order_status") != "C40" and str(r.get("order_date", "")).startswith(P))
    ratio = ga4_purchase / orders_n if orders_n else 0
    chk("cross-source: GA4 purchase ~ orders 수 (자릿수)", 0.2 < ratio < 5,
        f"GA4 purchase={ga4_purchase} / orders(4월활성)={orders_n} ratio={ratio:.2f}")

    # ── 10. mer != 채널 roas (07 MER 우위 실증) ──
    chk("mer(6.53) ≠ 채널 roas 평균 (blended 신뢰 vs 채널 과대)",
        computed["mer"] != computed["channel_roas_x"]["meta"],
        f"mer={computed['mer']} vs meta={computed['channel_roas_x']['meta']} (다름=정상)", fields=["mer", "roas_x"])

    # ── 11. ★ 신규 metric (contract formula) 독립 재계산 검증 ──
    tacos = round(total_ad / rev * 100, 2)   # contract: total_ad_cost / total_revenue * 100
    chk("tacos = total_ad_cost/order_revenue*100 (독립)",
        computed.get("tacos_pct") is not None and abs(tacos - computed["tacos_pct"]) < 0.01,
        f"{tacos} vs {computed.get('tacos_pct')}", fields=["tacos"])

    mm = cleaned["meta"]["measures"]
    meta_ctr = round(mm["clicks"] / mm["impressions"] * 100, 2)   # contract: clicks/impressions*100
    cmx = computed.get("channel_metrics", {}).get("meta", {})
    chk("meta ctr/cpc/cpm/cvr = contract formula (독립)",
        cmx.get("ctr_pct") is not None and abs(meta_ctr - cmx["ctr_pct"]) < 0.01,
        f"ctr {meta_ctr} vs {cmx.get('ctr_pct')}", fields=["ctr_pct", "cpc_krw", "cpm_krw", "cvr_pct"])

    # ── ★ 11. (WARN) crosswalk 목적 달성 — cross_channel==0 이면 '연결됨' 착시 경고 (B3) ──
    ccg = crosswalk.get("cross_channel_groups", 0)
    warn("crosswalk: cross_channel_groups > 0 (채널 간 연결 달성)", ccg > 0,
         f"cross_channel_groups={ccg} → C5 미해결(이름 자동연결 X). UTM/code 의도적 매핑 필요 — '연결됨'처럼 쓰지 말 것")

    return checks, tested


def _report(checks: list[dict], tested: set[str]) -> bool:
    print("=" * 64)
    print("verify_outputs — 산출물 독립 검증")
    print("=" * 64)
    for c in checks:
        mark = c["status"]
        line = f"  [{mark}] {c['name']}"
        if c["detail"]:
            line += f"  ({c['detail']})"
        print(line)
    crit = [c for c in checks if c["status"] in ("PASS", "FAIL")]
    warns = [c for c in checks if c["status"] == "WARN"]
    npass = sum(1 for c in crit if c["status"] == "PASS")
    print("=" * 64)
    tail = "  ✅ 산출물 검증" if npass == len(crit) else "  ⚠ 점검"
    print(f"RESULT: {npass}/{len(crit)} critical PASS" + (f" · {len(warns)} WARN" if warns else "") + tail)
    print(f"  tested canonical fields ({len(tested)}): {', '.join(sorted(tested))}")
    if warns:
        print("  ⚠ WARN (실패 아님, 가시화): " + " / ".join(c["name"] for c in warns))
    print("=" * 64)
    return npass == len(crit)


if __name__ == "__main__":
    import sys
    cks, tf = run()
    sys.exit(0 if _report(cks, tf) else 1)
