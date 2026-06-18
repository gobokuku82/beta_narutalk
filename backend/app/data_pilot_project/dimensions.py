"""dimensions.py — 프로토타입 canonical *dimension* translator (Step3, 2026-06-16).

목적: contract 의 dimension(channel_group·membership_grade·utm_source/medium)을
config-driven(dimension_maps.yaml) 으로 raw→정규화. production 하드코딩 normalizer 3종
(channel_attribution_normalizer·grade_system_unifier·utm_normalizer)을 **단일 contract-driven
translator 가 흡수**할 수 있음을 실증 — 측정값(pipeline.py)에 이은 차원/시간 확장 프로토타입.

검증: test_dimension_normalizer_prototype.py 가 본 산출 == production normalizer 산출(교차세계 동치).
값 매핑 = dimension_maps.yaml (외부화, 코드 하드코딩 0).
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "clumi" / "raw"
CFG = yaml.safe_load((Path(__file__).parent / "dimension_maps.yaml").read_text(encoding="utf-8"))
PERIOD = "2026-04"


def _csv(name):
    with (RAW / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _active_orders(period=PERIOD):
    """활성주문(order_status != C40) + period(order_date prefix). production filter_active_orders 미러."""
    return [r for r in _csv("orders.csv")
            if r.get("order_status") != "C40"
            and (not period or str(r.get("order_date", "")).startswith(period))]


def channel_group(period=PERIOD) -> dict:
    """orders.channel_attribution → channel_group (config map). production by_group 미러."""
    cfg = CFG["channel_group"]
    m, default, col = cfg["map"], cfg["default"], cfg["source"]["column"]
    dist: Counter = Counter()
    for r in _active_orders(period):
        raw = (r.get(col) or "").strip() or "(empty)"
        dist[m.get(raw, default)] += 1
    return dict(dist.most_common())


def membership_grade() -> dict:
    """customers.member_grade → 표준등급 분포 (config order). production standard_grade_dist 미러."""
    cfg = CFG["membership_grade"]
    order, col = cfg["order"], cfg["source"]["column"]
    dist: Counter = Counter((r.get(col) or "").strip() for r in _csv("customers.csv"))
    dist.pop("", None)
    return {g: dist.get(g, 0) for g in order}


def _norm_utm(v, rules) -> str:
    s = (v or "").strip()
    return rules.get(s, s)


def utm(period=PERIOD) -> dict:
    """orders.utm_source/utm_medium → 정규화 분포 (config rules). production source_dist/medium_dist 미러."""
    cfg = CFG["utm"]
    rules, cols = cfg["rules"], cfg["source"]["columns"]
    src: Counter = Counter()
    med: Counter = Counter()
    for r in _active_orders(period):
        s = _norm_utm(r.get(cols[0]), rules)
        mv = _norm_utm(r.get(cols[1]), rules)
        src[s or "(empty)"] += 1
        med[mv or "(empty)"] += 1
    return {"source": dict(src.most_common()), "medium": dict(med.most_common())}


def run_dimensions(period=PERIOD) -> dict:
    """전 차원 정규화 — contract-driven translator 의 dimension 출력."""
    return {
        "channel_group": channel_group(period),
        "membership_grade": membership_grade(),
        "utm": utm(period),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run_dimensions(), ensure_ascii=False, indent=2))
