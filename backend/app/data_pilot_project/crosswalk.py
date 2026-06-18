"""crosswalk.py — campaign_id 채널 네임스페이스 매핑 (C5 join불가 해소).

채널별 campaign ID 공간이 전부 달라(Meta 17자리 / Naver nccCampaignId / advoost GFA / kakao CMP_KKO / int)
직접 join 불가. campaign_name 정규화로 canonical_campaign 묶음 시도 — 연결 가능/불가 명시.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "clumi" / "raw"


def _json(name):
    return json.loads((RAW / name).read_text(encoding="utf-8"))


def _csv(name):
    with (RAW / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _norm_name(s):
    if not s:
        return None
    return re.sub(r"[\s_\-]+", "", str(s).lower())


def build_crosswalk() -> dict:
    """채널별 (campaign_id, name) 수집 → name 정규화 canonical 그룹."""
    raw_rows = []  # {channel, campaign_id, campaign_name}

    def add(channel, cid, name):
        if cid is None:
            return
        raw_rows.append({"channel": channel, "campaign_id": str(cid), "campaign_name": name})

    seen = set()
    # meta
    for r in _json("meta_ads_performance.json").get("data", []):
        key = ("meta", r.get("campaign_id"))
        if key not in seen:
            seen.add(key); add("meta", r.get("campaign_id"), r.get("campaign_name"))
    # naver_sa (native id, 캠페인명 raw 부재 -> None)
    for r in _json("naver_searchad.json").get("data", []):
        key = ("naver_sa", r.get("nccCampaignId"))
        if key not in seen:
            seen.add(key); add("naver_sa", r.get("nccCampaignId"), None)
    # advoost
    for r in _csv("naver_advoost.csv"):
        key = ("advoost", r.get("campaign_id"))
        if key not in seen:
            seen.add(key); add("advoost", r.get("campaign_id"), r.get("campaign_name"))
    # kakao / talktalk
    for ch, fn in (("kakao", "kakao_bizmessage.json"), ("talktalk", "naver_talktalk.json")):
        for c in _json(fn).get("campaigns", []):
            add(ch, c.get("campaign_id"), c.get("campaign_name"))
    # internal master
    for r in _csv("campaigns.csv"):
        add("internal", r.get("campaign_id"), r.get("name"))

    # canonical 그룹: name 정규화 매칭 (없으면 그룹 불가)
    by_name: dict[str, list] = {}
    unlinked = []
    for row in raw_rows:
        nn = _norm_name(row["campaign_name"])
        if nn:
            by_name.setdefault(nn, []).append(row)
        else:
            unlinked.append(row)

    canonical = []
    for i, (nn, members) in enumerate(sorted(by_name.items()), 1):
        canonical.append({
            "canonical_campaign_id": f"CC{i:03d}",
            "norm_name": nn,
            "channels": sorted(set(m["channel"] for m in members)),
            "members": [{"channel": m["channel"], "campaign_id": m["campaign_id"], "name": m["campaign_name"]} for m in members],
            "cross_channel": len(set(m["channel"] for m in members)) > 1,
        })

    return {
        "total_campaigns": len(raw_rows),
        "id_spaces": sorted(set(r["channel"] for r in raw_rows)),
        "canonical_groups": len(canonical),
        "cross_channel_groups": sum(1 for c in canonical if c["cross_channel"]),
        "unlinked": len(unlinked),
        "unlinked_detail": unlinked,
        "canonical": canonical,
        "note": "직접 ID join 불가(C5). name 정규화 매칭만. naver_sa는 raw에 campaign_name 부재 → 전부 unlinked.",
    }
