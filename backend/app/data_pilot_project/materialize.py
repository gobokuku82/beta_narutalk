"""materialize.py — normalized(cleaned)/computed/crosswalk 산출물을 파일로 저장.

data/clumi/_canonical/{cleaned,computed,crosswalk}/ + _schema. (data/ gitignore=local)
이 materialized 산출물에서 normalized/computed ERD/metadata/desc 생성 (raw 처럼).
신뢰 = 각 cleaned 값에 lineage 동반.
"""
from __future__ import annotations

import json
from pathlib import Path

import pipeline
import compute
import crosswalk

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "clumi" / "_canonical"


def _write(subdir, name, obj, schema):
    d = OUT / subdir
    (d / "_schema").mkdir(parents=True, exist_ok=True)
    (d / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    (d / "_schema" / f"{name}.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")


def materialize() -> dict:
    norm = pipeline.run_normalize()

    # cleaned: 채널별 canonical measures + lineage
    for ch, r in norm.items():
        schema = {"layer": "cleaned", "channel": ch, "period": pipeline.PERIOD,
                  "measures": list(r["measures"].keys()), "rows_source": r["rows"],
                  "lineage": "각 measure 값 ← 원본 raw (lineage_sample)"}
        _write("cleaned", f"{ch}_2026-04",
               {"measures": r["measures"], "lineage_sample": r["lineage_sample"], "rows": r["rows"]}, schema)

    # computed: metrics
    cmp = compute.compute(norm)
    _write("computed", "ad_metrics_2026-04", cmp,
           {"layer": "computed", "metrics": list(cmp.keys()),
            "formula": "contract metrics; mer = total_order_revenue / total_ad_cost"})

    # crosswalk (dimension)
    cw = crosswalk.build_crosswalk()
    _write("crosswalk", "campaign_crosswalk", cw,
           {"layer": "dimension", "purpose": "campaign_id 채널 네임스페이스 매핑(C5)",
            "groups": cw["canonical_groups"], "cross_channel": cw["cross_channel_groups"]})

    return {"norm": norm, "computed": cmp, "crosswalk": cw, "out": str(OUT)}


if __name__ == "__main__":
    res = materialize()
    print(f"materialized → {res['out']}")
    print(f"  cleaned: {len(res['norm'])} 채널")
    print(f"  computed: ad_metrics (mer={res['computed']['mer']})")
    print(f"  crosswalk: {res['crosswalk']['canonical_groups']} canonical / {res['crosswalk']['cross_channel_groups']} cross-channel / {res['crosswalk']['unlinked']} unlinked")
