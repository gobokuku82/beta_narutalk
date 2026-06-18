"""full-graph 측정 — 쿼리가 인식→계획→실행→표시 4단을 *실제로* 통과하는가 (2026-06-10 → M0 확장 2026-06-12).

원형(stage-1): 종류별 단일 쿼리를 full graph 로 돌려 REAL/DEGRADE/EMPTY 판정 (1회 스냅샷).
M0 확장(T2~T4, 계획_멀티쿼리 §2 — 제품 코드 무수정):
  - --corpus 인자화 (corpus_compound.yaml 등) + corpus 키 type/kind 호환
  - --runs 멀티런 (LLM 비결정 → 단발 스냅샷 금지, baseline_compound 와 동일 철학)
  - ①단 인식: structured_query.intent.sub_intents → n_sub·sub_ops 수집
  - ②단 계획: --judge 시 score_coverage LLM-judge + _reconcile_judge 교정 (coverage)
  - ③단 실행: judges.judge_attribution — 의도→todo 결정론 join → 의도별 완주율 (T4)
  - ④단 표시: judges.judge_display — corpus expect_display keyword 판정 (T3)
  - 출력 = {stem}_{run-id}.{json,md} 비파괴 (T1 동일 — 기존 stage1_coverage.* 보존)

실행 (backend/):
    python -m scripts.agent_lang_diagnostics.measure_stage1_coverage                       # 원형 (stage1 corpus, 1런)
    python -m scripts.agent_lang_diagnostics.measure_stage1_coverage \
        --corpus corpus_compound.yaml --runs 3 --judge                                     # M0 e2e
★ LLM 호출함: 쿼리당 full graph (cognitive+planning+execution+response) ×runs (+ --judge 시 judge 1).

Status: complete — M0 측정기 정비 T2 (T3·T4 는 judges.py 소비).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import yaml

_BACKEND = Path(__file__).resolve().parents[2]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.dream_agent.system_graph.builder import build_graph  # noqa: E402
from scripts.agent_lang_diagnostics.judges import (  # noqa: E402
    display_blob, judge_attribution, judge_display,
)

_HERE = Path(__file__).resolve().parent
_OUT = _BACKEND.parent / "docs" / "_claude" / "4layer_system" / "diag_results"
_FALLBACK = "분석을 완료했습니다."


def _verdict(text: str | None, meta: dict, statuses: list[str]) -> str:
    """REAL(실제 답) / DEGRADE(정직 기능없음) / EMPTY(빈 fallback)."""
    if meta.get("degraded") or meta.get("details"):
        return "DEGRADE"
    if text and text.strip() and text.strip() != _FALLBACK:
        return "REAL"
    return "EMPTY"


async def _run_one(graph, q: str, client: str, sid: str) -> dict:
    state = {
        "user_input": q, "language": "ko", "client_id": client,
        "session_id": sid, "conversation_history": [], "history_limit": 5,
        "require_review": False,
    }
    try:
        out = await graph.ainvoke(state)
    except Exception as e:  # noqa: BLE001
        return {"q": q, "error": f"{type(e).__name__}: {e}"}

    sq = out.get("structured_query") or {}
    intent = sq.get("intent") or {}
    subs = intent.get("sub_intents") or []
    tasks = [t.get("id") for t in sq.get("tasks", [])]
    plan = out.get("plan") or {}
    plan_todos = plan.get("todos") or []
    tools = [t.get("tool") for t in plan_todos]
    er = out.get("execution_result") or {}
    exec_todos = er.get("todos") or {}
    statuses = [r.get("status") for r in exec_todos.values()]
    payload = out.get("response") or {}
    text = payload.get("text") if isinstance(payload, dict) else None
    meta = payload.get("meta") or {} if isinstance(payload, dict) else {}

    return {
        "q": q,
        "operation": intent.get("operation"),
        "domain": intent.get("domain"),
        # ①단 인식 (T2): 복합 의도 분해 신호
        "n_sub": len(subs),
        "sub_ops": [s.get("operation") for s in subs],
        "tasks": tasks,
        "tools": tools,
        # ③·②단 재료 — 판정기/judge 가 소비
        "plan_todos": [{"id": t.get("id"), "tool": t.get("tool"), "why": t.get("why", "")}
                       for t in plan_todos],
        "exec_todos": {tid: {"status": (tr or {}).get("status"), "tool": (tr or {}).get("tool")}
                       for tid, tr in exec_todos.items()},
        "n_completed": sum(1 for s in statuses if s == "completed"),
        "n_skipped": sum(1 for s in statuses if s == "skipped"),
        "n_failed": sum(1 for s in statuses if s == "failed"),
        "verdict": _verdict(text, meta if isinstance(meta, dict) else {}, statuses),
        "payload": payload if isinstance(payload, dict) else {},
        "text": (text or "")[:200],
        "error": None,
    }


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="corpus_stage1_coverage.yaml")
    ap.add_argument("--runs", type=int, default=1, help="반복 횟수 (M0 e2e = 3)")
    ap.add_argument("--limit", type=int, default=0, help="앞 N 쿼리만 (smoke)")
    ap.add_argument("--judge", action="store_true",
                    help="LLM judge 로 ②계획 coverage + ③의도 귀속 판정 (M0 e2e 모드)")
    args = ap.parse_args()

    corpus = yaml.safe_load((_HERE / args.corpus).read_text(encoding="utf-8"))
    client = corpus.get("client", "clumi")
    items = corpus["queries"]
    if args.limit:
        items = items[: args.limit]

    judge = None
    if args.judge:
        from app.dream_agent.llm_manager.client import LLMClient
        from app.dream_agent.llm_manager.config import LAYER_CONFIGS
        judge = LLMClient(LAYER_CONFIGS["planning"])

    graph = build_graph()
    print(f"[fullgraph] {args.runs} runs × {len(items)} queries, client={client}, "
          f"judge={'on' if judge else 'off'}", flush=True)

    all_runs: list[list[dict]] = []
    for run_idx in range(1, args.runs + 1):
        rows: list[dict] = []
        for i, item in enumerate(items, 1):
            q = item["q"]
            kind = item.get("kind") or item.get("type", "?")   # corpus 키 호환 (T2)
            rec = await _run_one(graph, q, client, sid=f"fg_r{run_idx}_{i}")
            rec["kind"] = kind

            if not rec.get("error"):
                # ④단 표시 (T3) — expect_display 있는 corpus 만
                blob = display_blob(rec.pop("payload"))
                rec["display"] = judge_display(item.get("expect_display"), blob)
                # ②단 계획 + ③단 귀속 (T4) — --judge 모드만
                if judge is not None:
                    from scripts.agent_lang_diagnostics.baseline_compound import _reconcile_judge
                    from scripts.agent_lang_diagnostics.score_coverage import _score_one
                    sc = await _score_one(judge, q, {"todo_detail": rec["plan_todos"], "error": None})
                    sc = _reconcile_judge(sc, set(t["tool"] for t in rec["plan_todos"] if t.get("tool")))
                    rec["coverage"] = sc.get("coverage")
                    rec["judge_error"] = sc.get("error")
                    rec["attribution"] = judge_attribution(
                        sc.get("requested"), rec["plan_todos"], rec["exec_todos"])
            else:
                rec["display"] = None

            rows.append(rec)
            if rec.get("error"):
                print(f"  r{run_idx} [{i:>2}/{len(items)}] ERROR {rec['error'][:48]} | {kind}", flush=True)
            else:
                disp = rec.get("display") or {}
                att = rec.get("attribution") or {}
                d_str = (f" disp={disp['n_displayed']}/{disp['n_expect']}"
                         if disp.get("n_expect") else "")
                a_str = (f" attr={att['n_completed']}/{att['n_attributed']}"
                         f"(lost {len(att['lost'])})" if att else "")
                print(f"  r{run_idx} [{i:>2}/{len(items)}] {rec['verdict']:<7} n_sub={rec['n_sub']} "
                      f"comp={rec['n_completed']} skip={rec['n_skipped']} fail={rec['n_failed']}"
                      f"{d_str}{a_str} | {kind:<14} | {rec['text'][:40]}", flush=True)
        all_runs.append(rows)

    # ── 쿼리별 멀티런 집계 ──
    per_q: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for rows in all_runs:
        for rec in rows:
            per_q[(rec["kind"], rec["q"])].append(rec)

    def _mean(vals: list[float]) -> float | None:
        return round(statistics.mean(vals), 2) if vals else None

    q_summary: list[dict] = []
    for (kind, q), recs in per_q.items():
        ok = [r for r in recs if not r.get("error")]
        verdicts = Counter(r["verdict"] for r in ok)
        disp_rates = [r["display"]["display_rate"] for r in ok
                      if r.get("display") and r["display"]["display_rate"] is not None]
        attrs = [r["attribution"] for r in ok if r.get("attribution")]
        comp_rates = [a["completion_rate"] for a in attrs if a["completion_rate"] is not None]
        q_summary.append({
            "kind": kind, "q": q, "runs": len(recs), "errors": len(recs) - len(ok),
            "verdicts": dict(verdicts),
            "n_sub_values": sorted({r["n_sub"] for r in ok}),          # ① 인식 안정성
            "coverage_mean": _mean([r["coverage"] for r in ok
                                    if r.get("coverage") is not None]),  # ② 계획
            "completion_mean": _mean(comp_rates),                        # ③ 실행 (의도 완주)
            "lost_union": sorted({i for a in attrs for i in a["lost"] if i}),
            "broken_union": sorted({i for a in attrs for i in a["broken"] if i}),
            "display_mean": _mean(disp_rates),                           # ④ 표시
            "missing_union": sorted({m for r in ok if r.get("display")
                                     for m in r["display"]["missing"]}),
        })

    # ── 저장 (T1 동일 — 비파괴) ──
    stem = Path(args.corpus).stem.removeprefix("corpus_")
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_base = f"fullgraph_{stem}_{run_id}"
    _OUT.mkdir(parents=True, exist_ok=True)
    (_OUT / f"{out_base}.json").write_text(
        json.dumps({"corpus": args.corpus, "runs": args.runs, "client": client,
                    "judge": bool(judge), "per_query": q_summary, "raw_runs": all_runs},
                   ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    md = [f"# full-graph 4단 측정 — {args.corpus}", "",
          f"- {args.runs} runs × {len(items)} 쿼리 · client={client} · judge={'on' if judge else 'off'} · {run_id}",
          "- ① 인식=n_sub(변동 시 ⚠) / ② 계획=coverage / ③ 실행=의도 완주율(lost=계획 소실·broken=실행 깨짐) / ④ 표시=표출률",
          "",
          "| 종류 | verdicts | ①n_sub | ②cov | ③완주 | lost | broken | ④표출 | 미표출 | raw |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for s in sorted(q_summary, key=lambda x: (x["kind"], x["q"])):
        v = "/".join(f"{k}{n}" for k, n in sorted(s["verdicts"].items())) or "ERR"
        nsub = ",".join(str(x) for x in s["n_sub_values"])
        nsub += " ⚠" if len(s["n_sub_values"]) > 1 else ""
        fmt = lambda x: f"{x:.0%}" if x is not None else "-"  # noqa: E731
        md.append(f"| {s['kind']} | {v} | {nsub} | {fmt(s['coverage_mean'])} | "
                  f"{fmt(s['completion_mean'])} | {'; '.join(s['lost_union'])[:40] or '-'} | "
                  f"{'; '.join(s['broken_union'])[:40] or '-'} | {fmt(s['display_mean'])} | "
                  f"{'; '.join(s['missing_union'])[:40] or '-'} | {s['q'][:30]} |")
    (_OUT / f"{out_base}.md").write_text("\n".join(md), encoding="utf-8")

    print(f"\n[fullgraph] done → {_OUT / out_base}.{{json,md}}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
