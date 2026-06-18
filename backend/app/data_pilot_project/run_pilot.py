"""run_pilot.py — raw → normalized(cleaned) → computed 오케스트레이터 + 정답 검증.

실행: python backend/app/data_pilot_project/run_pilot.py
검증: ad_cost 채널별·합 · orders 매출 · mer=6.53 (2026-04 mock 재계산 기준값 대조).
"""
from __future__ import annotations

import pipeline
import compute

# 알려진 정답 (2026-04 mock 재계산 기준값 — raw 산술서 양세계 공유)
# ★ 가 결정(A-5.2): google 광고 매체 포함 → re-baseline 18.3M/6.53 → 26.8M/4.46.
EXPECT = {
    "ad_cost": {"meta": 9_235_826, "naver_sa": 5_999_627, "advoost": 3_000_000, "google": 8_500_000},   # 광고 매체
    "msg_cost": {"kakao": 59_020, "talktalk": 12_450},                              # 메시징 (C6.3 분리)
    "total_marketing_cost": 26_806_923,   # ad(26,735,453)+msg(71,470) (MER 분모) — google 포함
    "order_revenue": 119_539_660,         # 주문 매출 불변 (google 추가 무관)
    "mer": 4.46,                          # 119,539,660 / 26,806,923
}


def _chk(label, got, exp, tol=0):
    ok = abs((got or 0) - exp) <= tol
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {label}: got={got:,} expect={exp:,}" if isinstance(got, int)
          else f"  [{mark}] {label}: got={got} expect={exp}")
    return ok


def main():
    print("=" * 64)
    print("data_pilot — raw → cleaned(normalize) → computed")
    print("=" * 64)

    # 1) NORMALIZE: raw → cleaned canonical measures + lineage
    norm = pipeline.run_normalize()
    print("\n[1] CLEANED (정규화 canonical measures, 채널별)")
    for ch, r in norm.items():
        ms = ", ".join(f"{k}={v:,}" for k, v in sorted(r["measures"].items()))
        print(f"  {ch:9s} rows={r['rows']:>5}  {ms}")
        if r.get("note"):
            print(f"            └ {r['note']}")

    print("\n[1b] LINEAGE 샘플 (정규화값 ← 원본, 신뢰)")
    for ch, r in norm.items():
        for l in r["lineage_sample"][:2]:
            print(f"  {l['channel']:9s} {l['canonical']:24s} ← {str(l['source'])[:18]:18s} = {l['value']:>12,}  [{l['transform']}]")

    # 2) COMPUTE: cleaned → computed (파생 재계산)
    cmp = compute.compute(norm)
    print("\n[2] COMPUTED (파생 재계산)")
    print(f"  total_ad_cost_krw    = {cmp['total_ad_cost_krw']:,}  (광고 매체 meta/naver/advoost)")
    print(f"  total_msg_cost_krw   = {cmp['total_msg_cost_krw']:,}  (메시징 kakao/talktalk, C6.3 분리)")
    print(f"  total_marketing_cost = {cmp['total_marketing_cost_krw']:,}  (= MER 분모)")
    print(f"  channel_roas_x  = {cmp['channel_roas_x']}   (광고 매체만, 과대)")
    print(f"  blended_platform_roas_x = {cmp['blended_platform_roas_x']}")
    print(f"  msg_roi_pct     = {cmp['msg_roi_pct']}   (메시징, ROI≠ROAS)")
    print(f"  total_order_revenue_krw = {cmp['total_order_revenue_krw']:,}")
    print(f"  ★ mer (전사 ROAS, 신뢰) = {cmp['mer']}")

    # 3) VERIFY: 정답 대조
    print("\n[3] VERIFY (기준값 대조)")
    oks = []
    for c, exp in EXPECT["ad_cost"].items():
        oks.append(_chk(f"ad_cost[{c}]", cmp["ad_cost_by_channel"][c], exp))
    for c, exp in EXPECT["msg_cost"].items():
        oks.append(_chk(f"msg_cost[{c}]", cmp["msg_cost_by_channel"][c], exp))
    oks.append(_chk("total_marketing_cost (ad+msg)", cmp["total_marketing_cost_krw"], EXPECT["total_marketing_cost"]))
    oks.append(_chk("order_revenue", cmp["total_order_revenue_krw"], EXPECT["order_revenue"]))
    oks.append(_chk("mer", cmp["mer"], EXPECT["mer"], tol=0.05))

    print("\n" + "=" * 64)
    print(f"RESULT: {sum(oks)}/{len(oks)} PASS" + ("  ✅ SPEC 검증" if all(oks) else "  ⚠ 불일치 — 조정 필요"))
    print("=" * 64)
    return all(oks)


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
