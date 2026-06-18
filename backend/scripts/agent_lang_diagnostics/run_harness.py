"""③ 에이전트 언어 진단 하니스 — cognitive+planning 헤드리스 실행 → 유형별 진단 (2026-06-06).

사용자 요청: ~100 쿼리 날려보고 결과로 에이전트 언어 방향 설정. 기본 범위 = cognitive+planning
(실행 단계는 202MB·데이터 이슈로 제외 — 언어 방향엔 cognitive+planning 이 핵심).

쿼리당 수집: raw / cleaned(①) / intent / tasks / plan.todos / plan.gaps(②) / error.
+ **결정론 자동분류**(유형 태그 vs 실제 산출 비교, 추가 LLM 0): provenance_op_absent /
  multi_intent_collapsed / period_gap_caught|missed / diagnose_degraded|not / ambiguous_flagged|not …

실행 (backend/ 에서):
    python -m scripts.agent_lang_diagnostics.run_harness            # 전체
    python -m scripts.agent_lang_diagnostics.run_harness --limit 3  # smoke
결과: docs/_claude/4layer_system/diag_results/ (gitignored) 에 json + md.

★ LLM 호출함 (쿼리당 cognitive 1 + planning 3) — 비용·키 필요. POC 라 허용([[project_llm_heavy_initial]]).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import yaml

# backend/ 를 path 에 (스크립트 직접 실행 대비)
_BACKEND = Path(__file__).resolve().parents[2]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# Windows: 일부 async 클라이언트 호환 (run_server_v2 와 동일 정책)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.dream_agent.cognitive.cognitive_stage import cognitive_stage  # noqa: E402
from app.dream_agent.planning.planner import Planner  # noqa: E402
from app.dream_agent.schemas.structured_query import StructuredQuery  # noqa: E402

_HERE = Path(__file__).resolve().parent
_CORPUS = _HERE / "corpus.yaml"
_OUT = _BACKEND.parent / "docs" / "_claude" / "4layer_system" / "diag_results"

DEGRADE_OPS = {"diagnose", "forecast", "attribute"}


async def _run_one(q: str, client: str) -> dict:
    """cognitive → planning 헤드리스. 쿼리당 진단 레코드 반환 (예외는 record 에 담음)."""
    rec: dict = {"q": q, "error": None}
    state = {
        "user_input": q, "language": "ko", "client_id": client,
        "session_id": "harness", "conversation_history": [], "history_limit": 5,
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
    intent = sq.intent
    sub = list(intent.sub_intents) if intent else []
    rec.update({
        "cleaned": sq.meta.cleaned,
        "operation": intent.operation if intent else None,
        "domain": intent.domain if intent else [],
        "metric": intent.metric if intent else [],
        "dimensions": intent.dimensions if intent else [],
        "tasks": [t.id.value for t in sq.tasks],
        "ambiguous": sq.meta.ambiguity.is_ambiguous,
        "n_sub": len(sub),                                   # S1 씨앗: 잡힌 다의도 수
        "sub_ops": [si.operation for si in sub],             # 각 sub_intent 의 operation
    })

    # ── planning ──
    try:
        plan, issues = await Planner().plan(sq)
    except Exception as e:  # noqa: BLE001
        rec["error"] = f"planning raised: {e}"
        return rec
    if plan is None:
        rec["error"] = f"planning returned None (issues={issues})"
        return rec
    todo_detail = [
        {"id": t.id, "tool": t.tool, "deps": list(t.depends_on), "why": t.rationale}
        for t in plan.todos
    ]
    deps_map = {td["id"]: td["deps"] for td in todo_detail}
    rec.update({
        "n_todos": len(plan.todos),
        "todos": [t.tool for t in plan.todos],
        "todo_detail": todo_detail,
        "dag": dict(plan.dag),
        "has_dep": any(td["deps"] for td in todo_detail),   # 직렬 의존 형성?
        "max_chain": _max_chain(deps_map),                  # 가장 긴 의존 사슬(직렬 깊이)
        "gaps": list(plan.gaps),
        "plan_issues": issues,
    })
    return rec


def _max_chain(deps_map: dict[str, list[str]]) -> int:
    """가장 긴 의존 사슬 길이(직렬 깊이). deps_map[id]=이 todo 가 의존하는 id 들. acyclic 가정."""
    memo: dict[str, int] = {}

    def depth(n: str, seen: frozenset[str]) -> int:
        if n in memo:
            return memo[n]
        if n in seen:                       # 안전: 순환 시 종단
            return 0
        deps = deps_map.get(n, [])
        d = 1 + max((depth(x, seen | {n}) for x in deps), default=0)
        memo[n] = d
        return d

    return max((depth(n, frozenset()) for n in deps_map), default=0)


def _classify(rec: dict, qtype: str) -> str:
    """결정론 자동분류 — 유형 태그 대비 실제 산출이 기대대로인가 (LLM 무관)."""
    if rec.get("error"):
        return f"ERROR:{rec['error'][:40]}"
    op = rec.get("operation")
    tasks = rec.get("tasks") or []
    gaps = rec.get("gaps") or []

    if qtype == "provenance":
        # 언어에 explain/provenance op 자체가 없음 → 항상 measure 등으로 떨어짐
        return "provenance_op_absent" if op != "explain" else "provenance_captured"
    if qtype == "period_missing":
        return "period_gap_caught" if any("period" in g for g in gaps) else "period_gap_MISSED"
    if qtype == "multi_intent":
        return "multi_intent_collapsed" if len(tasks) <= 1 else f"multi_kept({len(tasks)})"
    if qtype == "quantifier":
        return "quantifier_present_in_intent" if op else "quantifier_unclear"
    if qtype in ("diagnose", "forecast", "attribute"):
        return "degraded_ok" if not tasks else "NOT_degraded"
    if qtype == "ambiguous":
        return "ambiguity_flagged" if rec.get("ambiguous") else "ambiguity_NOT_flagged"
    if qtype == "reference":
        # 대시보드/이전턴 참조를 cognitive 가 받을 길 없음 → 단일 쿼리로 오해 예상
        return "ref_unresolved_singleturn"
    if qtype.startswith("compound"):
        # 복합 천장 측정 — op(스칼라 1) / sub(S1 씨앗이 잡은 다의도 수) / task·todo·의존·직렬깊이.
        n = rec.get("n_todos", 0)
        dep = "Y" if rec.get("has_dep") else "N"
        return (f"op={op or '-'} sub={rec.get('n_sub', 0)} tasks={len(tasks)} "
                f"todos={n} dep={dep} chain={rec.get('max_chain', 0)}")
    return "ok"


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="앞 N 개만 (smoke). 0=전체")
    ap.add_argument("--corpus", type=str, default="corpus.yaml",
                    help="코퍼스 파일명 (스크립트 디렉토리 기준). 기본 corpus.yaml")
    args = ap.parse_args()

    corpus_path = _HERE / args.corpus
    corpus = yaml.safe_load(corpus_path.read_text(encoding="utf-8"))
    client = corpus.get("client", "clumi")
    stem = corpus_path.stem  # 출력 파일명 = 코퍼스 stem 별 (기존 결과 clobber 방지)
    queries = corpus["queries"]
    if args.limit:
        queries = queries[: args.limit]

    print(f"[harness] {len(queries)} queries, client={client}", flush=True)
    results: list[dict] = []
    for i, item in enumerate(queries, 1):
        q, qtype = item["q"], item.get("type", "?")
        rec = await _run_one(q, client)
        rec["type"] = qtype
        rec["note"] = item.get("note", "")
        rec["verdict"] = _classify(rec, qtype)
        results.append(rec)
        print(f"  [{i}/{len(queries)}] {qtype:16} | {rec['verdict']:28} | {q[:42]}", flush=True)

    # 집계
    from collections import Counter
    by_type_verdict = Counter((r["type"], r["verdict"]) for r in results)

    _OUT.mkdir(parents=True, exist_ok=True)
    base = "results" if stem == "corpus" else f"{stem}_results"
    report_name = "report" if stem == "corpus" else f"{stem}_report"
    (_OUT / f"{base}.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # markdown 리포트
    md = ["# 에이전트 언어 진단 결과 (③ 하니스)", "",
          f"- 쿼리 {len(results)} · client={client} · corpus={args.corpus}", "",
          "## 유형 × 판정 집계", "", "| 유형 | 판정 | 수 |", "|---|---|---|"]
    for (t, v), n in sorted(by_type_verdict.items()):
        md.append(f"| {t} | {v} | {n} |")
    md += ["", "## 쿼리별 상세 (op=대표 operation / sub=S1 다의도 수 / tasks·todos / dep=의존 / chain=직렬깊이)", "",
           "| 유형 | raw | op | sub | sub_ops | tasks | n_todos | dep | chain | todos(앞) | gaps |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        md.append(
            f"| {r['type']} | {r['q'][:34]} | {r.get('operation') or '-'} | "
            f"{r.get('n_sub', 0)} | {','.join(r.get('sub_ops') or []) or '-'} | "
            f"{','.join(r.get('tasks') or []) or '-'} | "
            f"{r.get('n_todos', '-')} | "
            f"{'Y' if r.get('has_dep') else 'N'} | {r.get('max_chain', '-')} | "
            f"{','.join(r.get('todos') or [])[:48] or '-'} | "
            f"{len(r.get('gaps') or [])} |"
        )
    (_OUT / f"{report_name}.md").write_text("\n".join(md), encoding="utf-8")

    print(f"\n[harness] done → {_OUT}", flush=True)
    print("[harness] 집계:", flush=True)
    for (t, v), n in sorted(by_type_verdict.items()):
        print(f"    {t:16} {v:30} {n}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
