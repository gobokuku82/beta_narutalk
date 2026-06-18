"""복합쿼리 coverage 점수표 — "복합지시가 planning까지 올바르게 전달+compose 되는가"를 숫자로 판단 (2026-06-10).

각 query: cognitive→planning(_run_one) → **LLM-judge**가 (요청 의도 vs plan tools)를 대조 →
  요청 의도별 covered/missing + noise(요청 안 한 tool) → lv별 coverage% + noise율 집계.

천장 측정(run_harness)은 plan '크기/gap'만 봤다. 본 스크립트는 plan이 *요청한 모든 의도를 빠짐없이*
담았나(coverage)와 *안 시킨 게 끼었나*(noise)를 채점 — "전달+compose 충실도"의 엄밀판.

실행 (backend/ 에서):
    python -m scripts.agent_lang_diagnostics.score_coverage --corpus corpus_compound.yaml
    python -m scripts.agent_lang_diagnostics.score_coverage --limit 3   # smoke

★ LLM 호출 (쿼리당 cognitive 1 + planning 3 + judge 1). 비결정 — 1회 스냅샷이라 lv별 경향으로 읽을 것.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml

_BACKEND = Path(__file__).resolve().parents[2]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.dream_agent.llm_manager.client import LLMClient  # noqa: E402
from app.dream_agent.llm_manager.config import LAYER_CONFIGS  # noqa: E402
from scripts.agent_lang_diagnostics.run_harness import _run_one  # noqa: E402  (cognitive→planning)

_HERE = Path(__file__).resolve().parent
_OUT = _BACKEND.parent / "docs" / "_claude" / "4layer_system" / "diag_results"

_JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "requested": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "intent": {"type": "string"},
                    "covered": {"type": "boolean"},
                    "evidence_tool": {"type": "string"},
                },
            },
        },
        "noise_tools": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"},
    },
}

_SYS = (
    "너는 분석 에이전트의 plan 채점관이다. 각 tool 에는 planning 이 적은 *목적(why)* 이 있으니 그걸 보고 판정한다. "
    "사용자 요청의 *구별되는 분석 의도/산출*만 세고(수집·정규화·정제는 필수 인프라라 의도도 noise 도 아님), "
    "plan 이 각 의도를 다루는지(why 로 판단), 그리고 요청 안 한 *분석/산출* tool 이 끼었는지(noise) 본다."
)


def _judge_prompt(q: str, detail: list[dict]) -> str:
    lines = "\n".join(f"  - {d.get('tool')}: {d.get('why', '')}" for d in detail)
    return (
        f'사용자 요청: "{q}"\n\n'
        f"planning 이 짠 tool (각 tool 의 목적):\n{lines}\n\n"
        "판정:\n"
        "1. requested[]: 사용자가 요청한 *구별되는 분석 의도/산출* 각각 = {intent(한국어 한 구절), "
        'covered(plan 이 다루나, 위 why 로 판단), evidence_tool(다루는 tool 이름 또는 "")}.\n'
        "   - 수집/정규화/정제 단계는 의도가 아니라 필수 인프라 → requested 에 넣지 말 것.\n"
        "2. noise_tools[]: tool 의 목적이 *어떤 요청 의도와도 무관* 할 때만 (예: 리뷰 요청 없는데 sentiment_analyzer/"
        "review_collector). 요청 의도를 *어설프게/부분적으로* 다루는 건 noise 아님(그건 coverage 미흡으로). "
        "수집/정규화/정제 인프라도 noise 아님.\n"
        "3. notes: 한 줄 총평."
    )


async def _score_one(judge: LLMClient, q: str, rec: dict) -> dict:
    if rec.get("error") or not rec.get("todo_detail"):
        return {"q": q, "error": rec.get("error") or "no plan", "n_req": 0, "n_cov": 0,
                "coverage": 0.0, "requested": [], "noise_tools": []}
    detail = rec.get("todo_detail") or []
    try:
        j = await judge.generate_json(_judge_prompt(q, detail), system_prompt=_SYS, schema=_JUDGE_SCHEMA)
    except Exception as e:  # noqa: BLE001
        return {"q": q, "error": f"judge: {e}", "n_req": 0, "n_cov": 0,
                "coverage": 0.0, "requested": [], "noise_tools": []}
    req = j.get("requested") or []
    cov = sum(1 for r in req if r.get("covered"))
    coverage = round(cov / len(req), 2) if req else 1.0
    return {
        "q": q, "error": None, "requested": req, "n_req": len(req), "n_cov": cov,
        "coverage": coverage, "noise_tools": j.get("noise_tools") or [], "notes": j.get("notes", ""),
    }


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="corpus_compound.yaml")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    corpus = yaml.safe_load((_HERE / args.corpus).read_text(encoding="utf-8"))
    client_id = corpus.get("client", "clumi")
    queries = corpus["queries"]
    if args.limit:
        queries = queries[: args.limit]

    judge = LLMClient(LAYER_CONFIGS["planning"])
    print(f"[coverage] {len(queries)} queries, client={client_id}", flush=True)

    rows: list[dict] = []
    for i, item in enumerate(queries, 1):
        q, qtype = item["q"], item.get("type", "?")
        rec = await _run_one(q, client_id)
        sc = await _score_one(judge, q, rec)
        sc["type"] = qtype
        sc["todos"] = rec.get("todos") or []
        rows.append(sc)
        miss = [r["intent"] for r in sc["requested"] if not r.get("covered")]
        tag = f"ERR={sc['error'][:30]}" if sc.get("error") else ""
        print(f"  [{i}/{len(queries)}] {qtype:13} cov={sc['coverage']:.0%} "
              f"({sc.get('n_cov', 0)}/{sc.get('n_req', 0)}) noise={len(sc['noise_tools'])} "
              f"miss={miss} {tag} | {q[:24]}", flush=True)

    # ── 집계 by level ──
    by_lv: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_lv[r["type"]].append(r)

    def _avg(rs, key):
        vals = [x[key] for x in rs if x.get("n_req")]
        return round(sum(vals) / len(vals), 2) if vals else 1.0

    _OUT.mkdir(parents=True, exist_ok=True)
    (_OUT / "coverage_results.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    md = ["# 복합쿼리 coverage 점수표 (전달+compose 충실도)", "",
          f"- {len(rows)} 쿼리 · client={client_id} · 1회 스냅샷(LLM 비결정)", "",
          "## 등급별 집계", "", "| 등급 | 평균 coverage | 누락 의도 | noise tool |", "|---|---|---|---|"]
    for lv in sorted(by_lv):
        rs = by_lv[lv]
        miss_total = sum(r["n_req"] - r["n_cov"] for r in rs)
        noise_total = sum(len(r["noise_tools"]) for r in rs)
        md.append(f"| {lv} | {_avg(rs, 'coverage'):.0%} | {miss_total} | {noise_total} |")

    md += ["", "## 쿼리별", "", "| 등급 | cov | 요청 | 누락 의도 | noise | raw |", "|---|---|---|---|---|---|"]
    for r in rows:
        miss = "; ".join(x["intent"] for x in r["requested"] if not x.get("covered")) or "-"
        md.append(f"| {r['type']} | {r['coverage']:.0%} | {r.get('n_req', 0)} | {miss} | "
                  f"{len(r['noise_tools'])} | {r['q'][:30]} |")
    (_OUT / "coverage_report.md").write_text("\n".join(md), encoding="utf-8")

    overall = _avg([r for r in rows if r.get("n_req")], "coverage")
    miss_all = sum(r["n_req"] - r["n_cov"] for r in rows)
    noise_all = sum(len(r["noise_tools"]) for r in rows)
    print(f"\n[coverage] done → {_OUT}", flush=True)
    print(f"[coverage] 전체 평균 coverage={overall:.0%} · 누락 의도 {miss_all} · noise {noise_all}", flush=True)
    for lv in sorted(by_lv):
        rs = by_lv[lv]
        print(f"    {lv:13} cov={_avg(rs, 'coverage'):.0%} "
              f"miss={sum(r['n_req'] - r['n_cov'] for r in rs)} "
              f"noise={sum(len(r['noise_tools']) for r in rs)}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
