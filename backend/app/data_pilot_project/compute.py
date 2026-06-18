"""compute.py — cleaned → computed metrics (파생 *재계산*).

★검증 역반영(C6.3): 광고(ad)와 메시징(msg)을 분리. 채널 roas/blended는 ad만.
MER 분모 = 총 마케팅비(ad+msg = 18,306,923, 2026-04 mock 재계산) → 6.53.
07 업계: 채널 roas 는 attribution 과대 → 의사결정은 mer.
"""
from __future__ import annotations

AD_CHANNELS = ["meta", "naver_sa", "advoost", "google"]   # 광고 매체 (C6.3: kakao/talktalk=메시징 분리 / 가 결정: google 포함)
MSG_CHANNELS = ["kakao", "talktalk"]


def compute(normalized: dict) -> dict:
    ad = {c: normalized[c]["measures"] for c in AD_CHANNELS}
    msg = {c: normalized[c]["measures"] for c in MSG_CHANNELS}

    total_ad_cost = sum(m.get("ad_cost_krw", 0) for m in ad.values())
    total_msg_cost = sum(m.get("msg_cost_krw", 0) for m in msg.values())
    total_marketing_cost = total_ad_cost + total_msg_cost   # MER 분모 (= 18,306,923)

    # 채널별 roas_x = conversion_revenue / ad_cost (광고 매체만 — 메시징 제외)
    channel_roas_x = {}
    for c in AD_CHANNELS:
        cost = ad[c].get("ad_cost_krw", 0)
        rev = ad[c].get("conversion_revenue_krw", 0)
        channel_roas_x[c] = round(rev / cost, 2) if cost else None

    # blended 플랫폼 roas (광고 매체 보고매출 합 / 광고비) — mer 대비용(과대)
    total_platform_rev = sum(m.get("conversion_revenue_krw", 0) for m in ad.values())
    blended_platform_roas = round(total_platform_rev / total_ad_cost, 2) if total_ad_cost else None

    # 메시징 ROI (광고 ROAS와 분리, C6.3). ROI%=(매출/비용-1)*100
    msg_roi_pct = {}
    for c in MSG_CHANNELS:
        cost = msg[c].get("msg_cost_krw", 0)
        rev = msg[c].get("msg_conversion_revenue_krw", 0)
        msg_roi_pct[c] = round((rev / cost - 1) * 100, 1) if cost else None

    # 채널별 효율 지표 — contract formula 적용 (input 완비분만: ctr/cpc/cpm/cvr). grain=채널(channel_roas_x와 동일).
    # link_ctr_pct 는 link_clicks 미materialize 라 제외(contract status=blocked).
    channel_metrics = {}
    for c in AD_CHANNELS:
        m = ad[c]
        imp, clk = m.get("impressions", 0), m.get("clicks", 0)
        cost, conv = m.get("ad_cost_krw", 0), m.get("conversion_count", 0)
        channel_metrics[c] = {
            "ctr_pct": round(clk / imp * 100, 2) if imp else None,   # clicks / impressions * 100
            "cpc_krw": round(cost / clk) if clk else None,           # ad_cost_krw / clicks
            "cpm_krw": round(cost / imp * 1000) if imp else None,    # ad_cost_krw / impressions * 1000
            "cvr_pct": round(conv / clk * 100, 2) if clk else None,  # conversion_count / clicks * 100
        }

    # ★ MER = orders 매출 / 총 마케팅비(ad+msg)
    total_revenue = normalized["orders"]["measures"].get("order_revenue_krw", 0)
    mer = round(total_revenue / total_marketing_cost, 2) if total_marketing_cost else None
    tacos_pct = round(total_ad_cost / total_revenue * 100, 2) if total_revenue else None   # 총광고비/매출*100 (전사)

    return {
        "ad_cost_by_channel": {c: ad[c].get("ad_cost_krw", 0) for c in AD_CHANNELS},
        "msg_cost_by_channel": {c: msg[c].get("msg_cost_krw", 0) for c in MSG_CHANNELS},
        "total_ad_cost_krw": total_ad_cost,
        "total_msg_cost_krw": total_msg_cost,
        "total_marketing_cost_krw": total_marketing_cost,
        "channel_roas_x": channel_roas_x,           # 광고 매체만 (과대)
        "blended_platform_roas_x": blended_platform_roas,
        "msg_roi_pct": msg_roi_pct,                  # 메시징 (ROI≠ROAS, C6.3)
        "channel_metrics": channel_metrics,          # ctr/cpc/cpm/cvr (contract formula, 채널별)
        "tacos_pct": tacos_pct,                       # 총광고비/매출 (전사)
        "total_order_revenue_krw": total_revenue,
        "mer": mer,                                  # 전사 ROAS (신뢰)
    }
