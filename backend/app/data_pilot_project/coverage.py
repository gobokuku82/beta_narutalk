"""coverage.py — canonical contract 필드 vs materialized 산출물 *정직* 매니페스트 (P1 / C1·C2·C3).

문제(검증 리포트 ①): contract 44필드 중 ~13만 materialize·7만 tested 인데 'verify 8/8·12/12 PASS'가
contract-complete 처럼 읽힘(vacuously green). 미구현 ~31필드는 검사항목에 없어 구조적으로 fail 불가.

이 스크립트: contract 전 필드를 enumerate → 각 필드 status(materialized/blocked/not_attempted)·tested 여부 산정 →
coverage.json 매니페스트 + 배지 'N/44 materialized, M tested' + 게이트(미정당화 not_attempted=FAIL,
materialized-untested=WARN). 'full PASS' 착시 제거가 목적.

실행: python backend/app/data_pilot_project/coverage.py
입력: octorad_canonical_contract_v0.1.yaml + data/clumi/_canonical/ + verify_outputs.run()(tested 집합).
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

import verify_outputs as vo

ROOT = Path(__file__).resolve().parents[3]
ERD = ROOT / "docs" / "agent_specs" / "ERD"
CANON = ROOT / "data" / "clumi" / "_canonical"
CONTRACT = ERD / "octorad_canonical_contract_v0.1.yaml"

# not_attempted 필드의 *정당화 사유*(미정당화=FAIL). 검증 리포트 §⑤ P2/P3 출처.
# 사유 없는 not_attempted 가 생기면 게이트 FAIL → silent gap 차단.
DEFERRAL = {
    # measures
    "link_clicks": "P2/C4: raw inline_link_clicks 존재, 미추출(link_ctr 분자). 후속",
    "vt_conversion_count": "P2/B4: advoost view_through_conversions(mock=0), VT>0 회귀 선행. 후속",
    "paid_reach": "P3: meta reach 미추출. 후속",
    "impression_frequency": "P3: meta frequency 미추출. 후속",
    "msg_target_count": "P2/C2: kakao/talktalk summary.target_* 존재, 미추출. 후속",
    "msg_open_count": "P2/C2: summary.open_count 존재, 미추출. 후속",
    "msg_click_count": "P2/C2: summary.click_count 존재, 미추출. 후속",
    # metrics
    "ctr_pct": "P2/C4: measure(clicks/impressions) 완비, compute 미구현(formula 확정). 후속",
    "link_ctr_pct": "P2/C4: link_clicks 미추출 선행. 후속",
    "cpc_krw": "P2/C4: measure 완비, compute 미구현. 후속",
    "cpm_krw": "P2/C4: measure 완비, compute 미구현. 후속",
    "cvr_pct": "P2/C4: measure 완비, compute 미구현. 후속",
    "acquisition_mer": "P3: new_customer_revenue measure 부재. 후속",
    "tacos": "P2: total_ad_cost/total_revenue 즉시 가능, 미구현. 후속",
    "msg_avg_order_value_krw": "P3: summary.avg_order_value 존재, 미추출. 후속",
    # 2026-06-18 contract 추가 지표(d29a582) — production tool 산출, pilot compute 미구현(미materialize)
    "cac": "P3: cac_overall tool 산출(월별 총마케팅비÷신규회원), pilot compute 미구현. 후속",
    "cpa": "P2/C4: channel_aggregate 산출(ad_cost÷conversions), pilot compute 미구현. 후속",
    "aov": "P3: aov_monthly tool 산출(매출÷주문수), pilot compute 미구현. 후속",
    "promotion_roas": "P3: promotion tool 산출(프로모션매출÷총마케팅비), pilot compute 미구현. 후속",
    "promotion_share_pct": "P3: promotion tool 산출(프로모션매출 비중), pilot compute 미구현. 후속",
    # dimensions (aggregate-only slice — C3)
    "_dimensions_all": "C3: 현 산출=channel×month 집계 스칼라. dimensional grain(report_date+campaign_id) 미materialize. 후속",
    # time
    "_time_all": "C3: per-row date/ts 미출력(집계 스칼라). 후속",
}


def _measure_keys_materialized() -> set[str]:
    """cleaned 산출물 전 채널 measures 키 union."""
    keys: set[str] = set()
    for p in (CANON / "cleaned").glob("*_2026-04.json"):
        keys.update(json.loads(p.read_text(encoding="utf-8")).get("measures", {}).keys())
    return keys


def _metric_keys_materialized() -> set[str]:
    """computed 산출물에서 contract metric 이름으로 환원되는 키."""
    cmp = json.loads((CANON / "computed" / "ad_metrics_2026-04.json").read_text(encoding="utf-8"))
    out: set[str] = set()
    if "channel_roas_x" in cmp:
        out.add("roas_x")           # 채널별 roas_x = contract roas_x
    if cmp.get("mer") is not None:
        out.add("mer")
    if "msg_roi_pct" in cmp:
        out.add("msg_roi_pct")
    if cmp.get("tacos_pct") is not None:
        out.add("tacos")            # contract metric 명 = tacos
    if "channel_metrics" in cmp:    # ctr/cpc/cpm/cvr (contract formula, 채널별)
        any_ch = next(iter(cmp["channel_metrics"].values()), {})
        for k in ("ctr_pct", "cpc_krw", "cpm_krw", "cvr_pct"):
            if k in any_ch:
                out.add(k)
    return out


def _campaign_id_materialized() -> bool:
    return (CANON / "crosswalk" / "campaign_crosswalk.json").exists()


def build() -> dict:
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    blocked = set(contract.get("meta", {}).get("blocked", []))
    _, tested = vo.run()

    mat_measures = _measure_keys_materialized()
    mat_metrics = _metric_keys_materialized()
    cid_mat = _campaign_id_materialized()

    fields: list[dict] = []

    def add(name, layer, materialized, reason=""):
        status = "blocked" if name in blocked else ("materialized" if materialized else "not_attempted")
        fields.append({"field": name, "layer": layer, "status": status,
                       "tested": name in tested, "reason": reason})

    for name in contract.get("measures", {}):
        add(name, "measure", name in mat_measures)
    for name in contract.get("metrics", {}):
        add(name, "metric", name in mat_metrics)
    for name in contract.get("dimensions", {}):
        # campaign_id 만 crosswalk 로 부분 materialize, 나머지 미시도
        add(name, "dimension", name == "campaign_id" and cid_mat,
            "" if name == "campaign_id" else DEFERRAL["_dimensions_all"])
    for name in contract.get("time", {}):
        add(name, "time", False, DEFERRAL["_time_all"])
    # meta.blocked 4 건 — contract measures/metrics 에 미정의(외부 블로커 declared). 별도 등재.
    for name in blocked:
        if not any(f["field"] == name for f in fields):
            fields.append({"field": name, "layer": "blocked_declared", "status": "blocked",
                           "tested": False, "reason": "Kakao 대행사 공식 doc 필요(06 PARTIAL) — declared blocker"})

    # not_attempted 사유 채우기 + 게이트 판정
    unjustified: list[str] = []
    for f in fields:
        if f["status"] == "not_attempted" and not f["reason"]:
            f["reason"] = DEFERRAL.get(f["field"], "")
            if not f["reason"]:
                unjustified.append(f["field"])
    mat_untested = [f["field"] for f in fields if f["status"] == "materialized" and not f["tested"]]

    defined = [f for f in fields if f["layer"] != "blocked_declared"]
    n_def = len(defined)
    n_mat = sum(1 for f in defined if f["status"] == "materialized")
    n_block = sum(1 for f in fields if f["status"] == "blocked")
    n_na = sum(1 for f in defined if f["status"] == "not_attempted")
    n_tested = sum(1 for f in defined if f["tested"])

    return {
        "badge": f"{n_mat}/{n_def} materialized · {n_tested} tested · {n_block} blocked · {n_na} not_attempted",
        "summary": {"defined_fields": n_def, "materialized": n_mat, "tested": n_tested,
                    "blocked": n_block, "not_attempted": n_na,
                    "materialized_untested": mat_untested, "unjustified_not_attempted": unjustified},
        "honesty_note": ("verify_outputs 12/12 critical PASS 는 아래 materialized∩tested 슬라이스 한정. "
                         "not_attempted 다수는 검사항목 부재로 vacuously green — 본 매니페스트가 그 gap 을 가시화."),
        "fields": sorted(fields, key=lambda f: (f["layer"], f["field"])),
    }


def main() -> bool:
    cov = build()
    s = cov["summary"]
    print("=" * 70)
    print("coverage manifest — canonical contract 필드 정직 표기 (P1/C1·C2·C3)")
    print("=" * 70)
    print(f"  배지: {cov['badge']}")
    print(f"  {cov['honesty_note']}")
    print("-" * 70)
    # 레이어별 분포
    by_layer: dict[str, list[dict]] = {}
    for f in cov["fields"]:
        by_layer.setdefault(f["layer"], []).append(f)
    for layer, fs in by_layer.items():
        mat = sum(1 for f in fs if f["status"] == "materialized")
        print(f"  [{layer:16s}] {mat}/{len(fs)} materialized  "
              + ", ".join(f"{f['field']}{'✓' if f['tested'] else ''}"
                          + ("" if f["status"] == "materialized" else f"({f['status'][:4]})") for f in fs))
    print("-" * 70)
    if s["materialized_untested"]:
        print(f"  ⚠ WARN — materialized 인데 untested {len(s['materialized_untested'])}: {', '.join(s['materialized_untested'])}")
    if s["unjustified_not_attempted"]:
        print(f"  ✗ FAIL — 사유 없는 not_attempted {len(s['unjustified_not_attempted'])}: {', '.join(s['unjustified_not_attempted'])}")
    else:
        print("  ✓ 모든 not_attempted 사유 명시(deferred). silent gap 0.")

    out = CANON / "coverage.json"
    out.write_text(json.dumps(cov, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  → {out}")
    print("=" * 70)
    return not s["unjustified_not_attempted"]


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
