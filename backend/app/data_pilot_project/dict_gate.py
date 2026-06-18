"""dict_gate.py — 데이터사전 ↔ raw 실헤더 ↔ contract 컬럼 *자동 diff 게이트* (P1 / 클러스터3 A1·A2).

문제(검증 리포트 클러스터3): deterministic 값검증은 '구현이 contract대로 raw를 처리했나'만 본다 →
사전·contract *자체*가 raw 와 어긋난 정의 drift(사전 stat_dt/camp_id/convCnt 가 raw 에 부재, ccnt 의미 역전,
campaign_id 자릿수)를 *구조적으로* 못 잡는다. 값은 맞는데 정의가 틀린 침묵 오류.

이 게이트(탐지 전용): raw 실헤더를 직독 → (1) contract source 컬럼이 raw 에 실재하나(CRITICAL),
(2) 사전 컬럼이 raw 에 실재하나(DRIFT), (3) raw 컬럼이 사전에 있나(사전 누락) 자동 대조.

⚠ **사전의 *계산내용*(description·formula·의미) 수정은 오너 영역**(memory project_data_viz_work_division).
본 게이트는 *이름 존재성*만 기계 판정하고 drift 를 *보고*만 한다 — 사전을 고치지 않는다.

실행: python backend/app/data_pilot_project/dict_gate.py
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "clumi" / "raw"
DICT = ROOT / "data" / "clumi" / "description" / "clumi_data_dictionary.csv"
CONTRACT = ROOT / "docs" / "agent_specs" / "ERD" / "octorad_canonical_contract_v0.1.yaml"

# 채널 → (raw 파일, 추출방식, 사전 filename 매칭 stem, contract source 키)
PILOT = [
    ("meta",     "meta_ads_performance.json", "json_data",               "meta_ads_performance"),
    ("naver_sa", "naver_searchad.json",       "json_data",               "naver_searchad"),
    ("advoost",  "naver_advoost.csv",         "csv",                     "naver_advoost"),
    ("kakao",    "kakao_bizmessage.json",     "json_campaigns_summary",  "kakao_bizmessage"),
    ("talktalk", "naver_talktalk.json",       "json_campaigns_summary",  "naver_talktalk"),
    ("orders",   "orders.csv",                "csv",                     "orders"),
]


def _leaf(col: str) -> str:
    """contract/사전 컬럼 표기 → leaf 이름. 'data[].salesAmt'→'salesAmt', 'summary.open_count'→'open_count'.
    contract dimension source 는 'data[].campaign_id(18자리 — 주석)' 같은 자유텍스트 → 괄호 주석 제거 후 leaf."""
    s = re.sub(r"\(.*", "", str(col))                         # 인라인 주석('(...') 제거 — 거짓경보 방지
    s = s.replace("data[].", "").replace("campaigns[].", "").replace("[]", "")
    return s.split(".")[-1].strip()


def _collect_leaves(obj, out: set[str]) -> None:
    """raw 문서 전체를 재귀로 훑어 모든 dict 키(leaf 이름) 수집.
    배열은 첫 원소만 descend(스키마 추출). 중첩 섹션(results_sample[]·friend_summary·message_blocks[])까지 포함 →
    'raw 에 실재하나 중첩이라 안 보임' 거짓양성 제거."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.add(k)
            _collect_leaves(v, out)
    elif isinstance(obj, list) and obj:
        _collect_leaves(obj[0], out)


def raw_leaves(rawfile: str, kind: str) -> set[str]:
    """raw 파일 실제 컬럼 leaf 집합 (탐지 기준 = 진실). CSV=헤더 / JSON=전체 재귀 leaf."""
    fp = RAW / rawfile
    if kind == "csv":
        with fp.open(encoding="utf-8-sig", newline="") as f:
            return set(next(csv.reader(f)))
    out: set[str] = set()
    _collect_leaves(json.loads(fp.read_text(encoding="utf-8")), out)
    return out


def dict_leaves(stem: str) -> set[str]:
    """사전에서 해당 파일 행의 column_name leaf 집합."""
    out: set[str] = set()
    with DICT.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if stem in (row.get("filename") or ""):
                col = row.get("column_name")
                if col:
                    out.add(_leaf(col))
    return out


def contract_source_leaves(contract: dict, channel: str) -> set[str]:
    """contract measures/dims/time 의 해당 채널 source 컬럼 leaf 집합."""
    out: set[str] = set()

    def scan(section):
        for d in section.values():
            if not isinstance(d, dict):
                continue
            src = d.get("sources", {})
            if channel in src:
                v = src[channel]
                col = v.get("column") if isinstance(v, dict) else v
                if col:
                    out.add(_leaf(col))
    scan(contract.get("measures", {}))
    scan(contract.get("dimensions", {}))
    scan(contract.get("time", {}))
    return out


def run() -> dict:
    import yaml
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    findings = {"critical": [], "drift": [], "missing_in_dict": []}
    per_file = []

    for channel, rawfile, kind, stem in PILOT:
        rl = raw_leaves(rawfile, kind)
        dl = dict_leaves(stem)
        cl = contract_source_leaves(contract, channel)

        # (1) CRITICAL: contract 가 참조하는 컬럼이 raw 에 없음 → contract 오기 (P0 후 ~0 기대)
        contract_bad = sorted(c for c in cl if c not in rl)
        # (2) DRIFT: 사전이 선언한 컬럼이 raw 에 없음 → 사전 오기 (owner 영역)
        dict_bad = sorted(d for d in dl if d not in rl)
        # (3) raw 에 있으나 사전에 없음 → 사전 누락
        miss = sorted(r for r in rl if r not in dl)

        for c in contract_bad:
            findings["critical"].append(f"{channel}/{rawfile}: contract source '{c}' raw 에 부재")
        for d in dict_bad:
            findings["drift"].append(f"{channel}/{rawfile}: 사전 컬럼 '{d}' raw 에 부재 (사전 오기 — owner 영역)")
        for m in miss:
            findings["missing_in_dict"].append(f"{channel}/{rawfile}: raw '{m}' 사전 미기재")
        per_file.append({"channel": channel, "raw": rawfile, "raw_cols": len(rl),
                         "dict_cols": len(dl), "contract_bad": contract_bad,
                         "dict_bad": dict_bad, "missing_in_dict": miss})

    # (4) 특정 자산: meta campaign_id 자릿수 (A2) — 사전/contract 명시값 vs raw 실측
    meta = json.loads((RAW / "meta_ads_performance.json").read_text(encoding="utf-8")).get("data", [])
    cid = str(meta[0].get("campaign_id", "")) if meta else ""
    cid_len = len(cid)
    cid_note = f"raw meta campaign_id 실측 {cid_len}자리({cid}). 사전 '(17자리)' 표기 → {'일치' if cid_len == 17 else 'DRIFT(사전 오기)'}. contract '(18자리)'."
    if cid_len != 17:
        findings["drift"].append(f"meta/campaign_id: 사전 '(17자리)' vs raw 실측 {cid_len}자리 — 사전 오기(A2)")

    return {"findings": findings, "per_file": per_file, "campaign_id_check": cid_note}


def main() -> bool:
    r = run()
    f = r["findings"]
    print("=" * 72)
    print("dict_gate — 사전 ↔ raw ↔ contract 컬럼 자동 diff (탐지 전용)")
    print("=" * 72)
    for pf in r["per_file"]:
        print(f"  {pf['channel']:9s} raw {pf['raw_cols']:>2} cols / 사전 {pf['dict_cols']:>2} cols"
              + (f"  · contract_bad={pf['contract_bad']}" if pf["contract_bad"] else "")
              + (f"  · 사전drift={pf['dict_bad']}" if pf["dict_bad"] else ""))
    print("-" * 72)
    print(f"  campaign_id: {r['campaign_id_check']}")
    print("-" * 72)
    nc, nd, nm = len(f["critical"]), len(f["drift"]), len(f["missing_in_dict"])
    if f["critical"]:
        print(f"  ✗ CRITICAL {nc} (contract↔raw 오기 — 즉시 수정):")
        for x in f["critical"]:
            print(f"      - {x}")
    else:
        print("  ✓ CRITICAL 0 — contract source 전부 raw 에 실재 (P0 정합 유지)")
    if f["drift"]:
        print(f"  ⚠ DRIFT {nd} (사전↔raw 오기 — ★사전 수정은 오너 영역, 보고만):")
        for x in f["drift"]:
            print(f"      - {x}")
    print(f"  ℹ 사전 누락 {nm} (raw 에 있으나 사전 미기재) — 상세는 dict_gate.json")
    out = ROOT / "data" / "clumi" / "_canonical" / "dict_gate.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  → {out}")
    print("=" * 72)
    # 게이트 판정: CRITICAL(contract 오기)만 FAIL. DRIFT(사전)는 owner 영역이라 WARN(비차단).
    return nc == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
