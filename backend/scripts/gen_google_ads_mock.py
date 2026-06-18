"""gen_google_ads_mock.py — clumi_mock_18 google_ads_performance.csv 생성 (결정론).

A1 결정(2026-06-16): google = canonical 18번째 유료 광고 벤더소스.
실 Google Ads 성과 리포트 스키마 + advoost 템플릿 결. 일별 × 캠페인, 2026-04 전월.
스케일 ~8.5M/월(canonical 메이저 채널 수준) · 타깃 지향 roas~4.0·cpa~14000.

출력: data/clumi/raw/google_ads_performance.csv
재현: random.seed 고정. 컬럼 = contract ad_cost_krw/impressions/clicks/conversion_count/conversion_revenue_krw 의 google source.
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(20260416)  # 결정론 (재생성 동일)

ROOT = Path(__file__).resolve().parents[1].parent  # repo root
OUT = ROOT / "data" / "clumi" / "raw" / "google_ads_performance.csv"

# 캠페인 (실 Google Ads 유형) — cost_share(of ~8.5M) + 채널별 현실 rate
# roas=배수, cpc=KRW, cvr=비율, ctr=비율
CAMPAIGNS = [
    {"id": "GADS2026040001", "name": "CLUMI_SEARCH_BRAND",     "type": "SEARCH",   "network": "SEARCH",  "cost": 1_500_000, "roas": 6.0, "cpc": 320, "cvr": 0.055, "ctr": 0.072},
    {"id": "GADS2026040002", "name": "CLUMI_SEARCH_GENERIC",   "type": "SEARCH",   "network": "SEARCH",  "cost": 2_000_000, "roas": 2.8, "cpc": 680, "cvr": 0.032, "ctr": 0.041},
    {"id": "GADS2026040003", "name": "CLUMI_PMAX_PROSPECT",    "type": "PMAX",     "network": "DISPLAY", "cost": 2_200_000, "roas": 4.2, "cpc": 520, "cvr": 0.040, "ctr": 0.029},
    {"id": "GADS2026040004", "name": "CLUMI_SHOPPING_FEED",    "type": "SHOPPING", "network": "SEARCH",  "cost": 1_500_000, "roas": 5.0, "cpc": 430, "cvr": 0.045, "ctr": 0.031},
    {"id": "GADS2026040005", "name": "CLUMI_DISPLAY_RT",       "type": "DISPLAY",  "network": "DISPLAY", "cost":   800_000, "roas": 4.0, "cpc": 240, "cvr": 0.030, "ctr": 0.018},
    {"id": "GADS2026040006", "name": "CLUMI_VIDEO_AWARENESS",  "type": "VIDEO",    "network": "YOUTUBE", "cost":   500_000, "roas": 1.6, "cpc": 130, "cvr": 0.012, "ctr": 0.022},
]

DAYS = [date(2026, 4, 1) + timedelta(d) for d in range(30)]  # 2026-04 전월


def _noise(p=0.15):
    return 1 + random.uniform(-p, p)


def _split_cost(total: int, n: int) -> list[int]:
    """월 cost 를 n일에 분배 (평일 가중 + 노이즈, 합 보존)."""
    raw = []
    for d in DAYS:
        wf = 1.12 if d.weekday() < 5 else 0.78  # 평일↑ 주말↓
        raw.append(max(0.05, wf * _noise(0.22)))
    s = sum(raw)
    out = [round(total * r / s) for r in raw]
    out[-1] += total - sum(out)  # 합 정확 보존
    return out


rows = []
for c in CAMPAIGNS:
    daily = _split_cost(c["cost"], len(DAYS))
    for d, cost in zip(DAYS, daily):
        if cost <= 0:
            continue
        cpc = c["cpc"] * _noise(0.18)
        clicks = max(1, round(cost / cpc))
        ctr = c["ctr"] * _noise(0.18)
        impressions = max(clicks, round(clicks / ctr))
        cvr = c["cvr"] * _noise(0.20)
        conversions = round(clicks * cvr)
        conv_value = round(cost * c["roas"] * _noise(0.20))
        rows.append({
            "report_date": d.isoformat(),
            "campaign_id": c["id"],
            "campaign_name": c["name"],
            "campaign_type": c["type"],
            "network": c["network"],
            "impressions": impressions,
            "clicks": clicks,
            "ctr": round(clicks / impressions * 100, 2),
            "avg_cpc": round(cost / clicks),
            "cost": cost,
            "conversions": conversions,
            "conversion_value": conv_value,
            "cost_per_conversion": round(cost / conversions) if conversions else 0,
            "conversion_rate": round(conversions / clicks * 100, 2),
            "search_impression_share": round(random.uniform(58, 88), 1) if c["network"] == "SEARCH" else "",
            "video_views": round(impressions * random.uniform(0.25, 0.45)) if c["type"] == "VIDEO" else 0,
        })

COLS = ["report_date", "campaign_id", "campaign_name", "campaign_type", "network",
        "impressions", "clicks", "ctr", "avg_cpc", "cost", "conversions",
        "conversion_value", "cost_per_conversion", "conversion_rate",
        "search_impression_share", "video_views"]

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)

# ── 검증 집계 (타깃 대조) ──
tc = sum(r["cost"] for r in rows)
tv = sum(r["conversion_value"] for r in rows)
tk = sum(r["clicks"] for r in rows)
ti = sum(r["impressions"] for r in rows)
tn = sum(r["conversions"] for r in rows)
print(f"생성: {OUT.name} — {len(rows)}행 ({len(CAMPAIGNS)}캠페인 × {len(DAYS)}일)")
print(f"  cost={tc:,} (타깃 ~8,500,000) · conversion_value={tv:,}")
print(f"  roas={tv/tc:.2f} (타깃 4.0) · cpa={tc/tn:,.0f} (타깃 14,000) · cpc={tc/tk:,.0f} · cvr={tn/tk*100:.2f}% · ctr={tk/ti*100:.2f}%")
print(f"  conversions={tn:,} · clicks={tk:,} · impressions={ti:,}")
