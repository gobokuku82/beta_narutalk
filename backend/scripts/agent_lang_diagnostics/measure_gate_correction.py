"""게이트 교정량 측정 — LLM raw 출력(게이트 전) vs 게이트 교정 후 (2026-06-10).

목적(기준점 박기): "LLM 의 뇌가 멀쩡한데 게이트가 가리나 / 뇌(프롬프트·컨텍스트)가 문제인가"를
*추론이 아니라 측정*으로 판별. 게이트가 LLM plan 을 *얼마나* 다시 쓰는지가 LLM raw 품질의 직접 지표:
  - 게이트가 거의 안 건드림 → LLM 멀쩡, 게이트=안전망 → 프롬프트 OK
  - 게이트가 대거 다시 씀 → LLM 이 나쁜 workflow → 프롬프트·컨텍스트가 진짜 문제

단계별 스냅샷(plan() L534-546 순서 그대로, 단 raw 를 *주제필터 전*에 잡음):
  raw(Stage3 LLM 직후) → +subject_filter(drop) → +dataflow_chain(insert) → +temporal(bind)

실행 (backend/ 에서):
    python -m scripts.agent_lang_diagnostics.measure_gate_correction --corpus corpus_compound.yaml
    python -m scripts.agent_lang_diagnostics.measure_gate_correction --limit 3   # smoke
결과: docs/_claude/4layer_system/diag_results/gatemeasure_<stem>.json + .md

★ LLM 호출함 (쿼리당 cognitive 1 + planning 3). 비용·키 필요. POC 허용.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import yaml

_BACKEND = Path(__file__).resolve().parents[2]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.dream_agent.cognitive.cognitive_stage import cognitive_stage  # noqa: E402
from app.dream_agent.planning.planner import (  # noqa: E402
    Plan,
    Planner,
    _build_prompt,
    _build_tool_index,
    _get_agent_tools,
    _load_stage_prompt,
    apply_subject_coherence_filter,
    bind_temporal_params,
    complete_dataflow_chain,
)
from app.dream_agent.schemas.structured_query import StructuredQuery  # noqa: E402

_HERE = Path(__file__).resolve().parent
_OUT = _BACKEND.parent / "docs" / "_claude" / "4layer_system" / "diag_results"


def _tools(plan: Plan) -> list[str]:
    return [t.tool for t in plan.todos]


def _params_count(plan: Plan) -> int:
    return sum(len(t.tool_params) for t in plan.todos)


async def _run_one(q: str, client: str, review_names: set[str], catalog: dict) -> dict:
    rec: dict = {"q": q, "error": None}
    state = {
        "user_input": q, "language": "ko", "client_id": client,
        "session_id": "gatemeasure", "conversation_history": [], "history_limit": 5,
    }
    # ── cognitive ──
    try:
        cmd = await cognitive_stage(state)
        upd = getattr(cmd, "update", None) or {}
    except Exception as e:  # noqa: BLE001
        rec["error"] = f"cognitive raised: {e}"
        return rec
    if "error" in upd or "structured_query" not in upd:
        rec["error"] = upd.get("error", "cognitive: no structured_query")
        return rec

    sq = StructuredQuery.model_validate(upd["structured_query"])
    planner = Planner()
    sq_json = json.dumps(sq.model_dump(mode="json"), ensure_ascii=False, indent=2)
    allow_text = planner._has_text_intent(sq)
    rec["allow_text"] = allow_text

    # ── Stage 1·2 ──
    try:
        teams = await planner._select_teams(sq_json)
        if not teams:
            rec.update({"raw": [], "final": [], "note": "no teams (degrade)"})
            return rec
        agents = await planner._select_agents(sq_json, teams)
        if not agents:
            rec.update({"raw": [], "final": [], "note": "no agents (degrade)"})
            return rec
    except Exception as e:  # noqa: BLE001
        rec["error"] = f"stage1/2 raised: {e}"
        return rec

    # ── Stage 3 RAW (게이트 *전* — _build_todos 의 LLM 호출부만 복제, 주제필터 미적용) ──
    try:
        config = _load_stage_prompt("planning_stage3_todo.yaml")
        agent_tools = _get_agent_tools(catalog, agents, allow_text=allow_text)
        system_prompt, user_prompt = _build_prompt(config, {
            "structured_query_json": sq_json,
            "agent_tools_json": json.dumps(agent_tools, ensure_ascii=False, indent=2),
        })
        result = await planner.client.generate_json(prompt=user_prompt, system_prompt=system_prompt)
        raw_plan = Plan.model_validate(result)
    except Exception as e:  # noqa: BLE001
        rec["error"] = f"stage3 raw raised: {e}"
        return rec

    raw_tools = _tools(raw_plan)

    # ── 게이트 단계별 적용 (plan() 순서) ──
    p = raw_plan.model_copy(deep=True)
    p = apply_subject_coherence_filter(p, review_names, allow_text)
    after_filter = _tools(p)

    p = complete_dataflow_chain(p, catalog)
    after_dataflow = _tools(p)
    params_before_temporal = _params_count(p)

    tool_index = _build_tool_index(catalog)
    p = bind_temporal_params(p, sq, tool_index)
    params_after_temporal = _params_count(p)

    final_tools = _tools(p)

    # ── 델타 ──
    dropped = sorted(set(raw_tools) - set(after_filter))
    inserted = sorted(set(after_dataflow) - set(after_filter))
    temporal_bound = params_after_temporal - params_before_temporal
    review_in_raw = sorted(t for t in raw_tools if t in review_names)
    review_in_final = sorted(t for t in final_tools if t in review_names)
    gate_touched = bool(dropped or inserted or temporal_bound)

    rec.update({
        "operation": (sq.intent.operation if sq.intent else None),
        "raw": raw_tools,
        "n_raw": len(raw_tools),
        "after_filter": after_filter,
        "after_dataflow": after_dataflow,
        "final": final_tools,
        "n_final": len(final_tools),
        "filter_dropped": dropped,
        "n_dropped": len(dropped),
        "dataflow_inserted": inserted,
        "n_inserted": len(inserted),
        "temporal_bound": temporal_bound,
        "review_in_raw": review_in_raw,
        "review_in_final": review_in_final,
        "gate_touched": gate_touched,
        # ★ 핵심 지표: 게이트가 raw 대비 plan 을 얼마나 바꿨나 (drop+insert)
        "rewrite_n": len(dropped) + len(inserted),
        "rewrite_ratio": round((len(dropped) + len(inserted)) / max(1, len(raw_tools)), 2),
    })
    return rec


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--corpus", type=str, default="corpus_compound.yaml")
    args = ap.parse_args()

    corpus_path = _HERE / args.corpus
    corpus = yaml.safe_load(corpus_path.read_text(encoding="utf-8"))
    client = corpus.get("client", "clumi")
    stem = corpus_path.stem
    queries = corpus["queries"]
    if args.limit:
        queries = queries[: args.limit]

    # 카탈로그·리뷰집합 1회 로드
    _p0 = Planner()
    catalog, review_names = _p0._catalog, _p0._review_tool_names

    print(f"[gatemeasure] {len(queries)} queries, client={client}", flush=True)
    results: list[dict] = []
    for i, item in enumerate(queries, 1):
        q, qtype = item["q"], item.get("type", "?")
        rec = await _run_one(q, client, review_names, catalog)
        rec["type"] = qtype
        results.append(rec)
        if rec.get("error"):
            print(f"  [{i}/{len(queries)}] ERROR {rec['error'][:50]} | {q[:40]}", flush=True)
        else:
            print(f"  [{i}/{len(queries)}] raw={rec.get('n_raw','-'):>2} "
                  f"drop={rec.get('n_dropped',0)} ins={rec.get('n_inserted',0)} "
                  f"rewrite={rec.get('rewrite_n',0)}({rec.get('rewrite_ratio',0)}) "
                  f"touched={'Y' if rec.get('gate_touched') else 'N'} | {q[:38]}", flush=True)

    # ── 집계 ──
    ok = [r for r in results if not r.get("error") and "raw" in r and r.get("n_raw") is not None]
    n = len(ok)
    touched = sum(1 for r in ok if r.get("gate_touched"))
    total_raw = sum(r.get("n_raw", 0) for r in ok)
    total_drop = sum(r.get("n_dropped", 0) for r in ok)
    total_ins = sum(r.get("n_inserted", 0) for r in ok)
    review_leak = [r for r in ok if r.get("review_in_final") and not r.get("review_in_raw")]
    review_in_raw_q = [r for r in ok if r.get("review_in_raw")]

    summary = {
        "corpus": args.corpus, "n_queries": len(results), "n_ok": n,
        "gate_touched_n": touched,
        "gate_touched_pct": round(100 * touched / max(1, n), 1),
        "total_raw_tools": total_raw,
        "total_dropped": total_drop,
        "total_inserted": total_ins,
        "rewrite_total": total_drop + total_ins,
        "rewrite_per_query": round((total_drop + total_ins) / max(1, n), 2),
        "review_leak_queries_n": len(review_leak),   # raw 엔 리뷰 없는데 게이트가 주입(CP#1)
        "review_in_raw_queries_n": len(review_in_raw_q),  # LLM 이 raw 로 리뷰 tool 낸 쿼리
    }

    _OUT.mkdir(parents=True, exist_ok=True)
    (_OUT / f"gatemeasure_{stem}.json").write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    md = ["# 게이트 교정량 측정", "",
          f"corpus={args.corpus} · ok {n}/{len(results)}", "",
          "## 집계", "", "| 지표 | 값 |", "|---|---|"]
    for k, v in summary.items():
        md.append(f"| {k} | {v} |")
    md += ["", "## 쿼리별 (raw=LLM 직출력 tool수 / drop=주제필터 / ins=dataflow / rewrite=drop+ins)", "",
           "| 유형 | raw | drop | ins | rewrite | ratio | touched | review(raw→final) | q |",
           "|---|---|---|---|---|---|---|---|---|"]
    for r in ok:
        md.append(
            f"| {r['type']} | {r.get('n_raw',0)} | {r.get('n_dropped',0)} | "
            f"{r.get('n_inserted',0)} | {r.get('rewrite_n',0)} | {r.get('rewrite_ratio',0)} | "
            f"{'Y' if r.get('gate_touched') else 'N'} | "
            f"{len(r.get('review_in_raw') or [])}→{len(r.get('review_in_final') or [])} | {r['q'][:30]} |"
        )
    for r in results:
        if r.get("error"):
            md.append(f"| {r['type']} | ERROR | | | | | | | {r['q'][:30]} ({r['error'][:30]}) |")
    (_OUT / f"gatemeasure_{stem}.md").write_text("\n".join(md), encoding="utf-8")

    print(f"\n[gatemeasure] done → {_OUT}/gatemeasure_{stem}.*", flush=True)
    print("[gatemeasure] 집계:", flush=True)
    for k, v in summary.items():
        print(f"    {k:26} {v}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
