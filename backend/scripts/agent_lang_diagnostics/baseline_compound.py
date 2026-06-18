"""복합쿼리 재현가능 베이스라인 — score_coverage 를 N회 돌려 평균±분산 + 쿼리별 안정성(flip) 측정 (2026-06-11).

단발 score_coverage 는 1회 LLM 스냅샷(쿼리당 cognitive1+planning3+judge1=5 LLM, 전부 비결정)이라
"복합쿼리 ~96%"가 *진짜 수준*인지, 실패가 *체계적*(always-fail)인지 *변동*(flaky)인지 구분 못 한다.
본 스크립트는 동일 corpus 를 N회 반복해 그 구분을 만든다:

  - 등급별(lv1~lv5) coverage 평균 / min / max (분산 폭) + noise 평균.
  - 쿼리별 coverage 분포 → 안정성 분류:
      stable-full   = 매 런 100% (안정 정상)
      systematic    = 매 런 < 100% (체계적 깨짐 → 결정론 fix·R2 후보)
      flaky         = 런마다 출렁 (비결정 → ⒝ Stage3 프롬프트 후보)
  - n_req(요청 의도 수) 변동 = cognitive/judge 가 같은 쿼리를 매번 다르게 분해하는가(상류 불안정 신호).

이 베이스라인이 ⒝(프롬프트)·R2(sub_intents 본배선) 어느 쪽을 골라도 *회귀 판정 기준선*이 된다.
single-run 의 clobber 와 달리 런별 raw 를 모두 보존하고 집계 요약을 남긴다.

실행 (backend/ 에서):
    python -m scripts.agent_lang_diagnostics.baseline_compound --runs 5
    python -m scripts.agent_lang_diagnostics.baseline_compound --runs 3 --limit 4   # smoke

★ LLM 호출 큼: runs × queries × 5. POC 라 허용([[project_llm_heavy_initial]], 테스트 리소스 제약 없음).
결과: docs/_claude/4layer_system/diag_results/baseline_{corpus-stem}_{run-id}.{json,md} (gitignored)
      — T1(M0, 2026-06-12): run-id 로 비파괴. 구 회귀 기준선 baseline_compound.{json,md} 는 보존됨.
"""
from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import yaml

_BACKEND = Path(__file__).resolve().parents[2]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import json  # noqa: E402

from app.dream_agent.llm_manager.client import LLMClient  # noqa: E402
from app.dream_agent.llm_manager.config import LAYER_CONFIGS  # noqa: E402
from scripts.agent_lang_diagnostics.run_harness import _run_one  # noqa: E402  (cognitive→planning)
from scripts.agent_lang_diagnostics.score_coverage import _score_one  # noqa: E402  (LLM-judge coverage)

_HERE = Path(__file__).resolve().parent
_OUT = _BACKEND.parent / "docs" / "_claude" / "4layer_system" / "diag_results"

# coverage==1.0(요청 의도 전부 충족)을 "pass" 로 본다 — 부분충족은 불합격.
_PASS = 1.0


def _reconcile_judge(sc: dict, plan_tools: set[str]) -> dict:
    """judge 자기모순 결정론 교정 — 측정 noise 차단.

    관찰(smoke): judge 가 covered=False 라 하면서 evidence_tool 로 *실제 plan 에 있는* tool 을
    지목하는 모순이 비결정적으로 발생(lv2 "ROAS랑 매출": evid=roas_overall·revenue_total 인데 covered=False).
    evidence_tool 이 plan todos 에 실재한다는 건 "그 의도를 다루는 tool 이 plan 에 있다"는 *결정론적 사실*
    → judge 의 boolean noise 보다 우선. covered 를 True 로 교정하고 교정 횟수를 투명 보고한다.
    (evidence_tool='' 인 진짜 미커버[lv1 "채널별 ROAS" 채널분해 tool 부재]는 건드리지 않음 = 실제 plan 변동 보존.)
    """
    req = sc.get("requested") or []
    corrected = 0
    for r in req:
        ev = (r.get("evidence_tool") or "").strip()
        if not r.get("covered") and ev and ev in plan_tools:
            r["covered"] = True
            r["_judge_corrected"] = True
            corrected += 1
    if req:
        n_cov = sum(1 for r in req if r.get("covered"))
        sc["n_cov"] = n_cov
        sc["coverage"] = round(n_cov / len(req), 2)
    sc["judge_corrections"] = corrected
    return sc


def _classify_stability(covs: list[float], errs: int) -> str:
    """쿼리의 런별 coverage 분포 → 안정성 라벨. covs = 유효(n_req>0·무에러) 런들의 coverage."""
    if not covs:
        return "no-intent" if errs == 0 else "all-error"
    passes = sum(1 for c in covs if c >= _PASS)
    if passes == len(covs):
        return "stable-full"
    if passes == 0:
        return "systematic"   # 매 런 미달 → 체계적 깨짐
    return "flaky"            # 출렁 → 비결정


async def _one_run(queries: list[dict], client_id: str, judge: LLMClient,
                   run_idx: int, n_runs: int) -> list[dict]:
    """corpus 1회 통과 — 쿼리별 coverage 레코드."""
    rows: list[dict] = []
    for i, item in enumerate(queries, 1):
        q, qtype = item["q"], item.get("type", "?")
        rec = await _run_one(q, client_id)
        sc = await _score_one(judge, q, rec)
        sc = _reconcile_judge(sc, set(rec.get("todos") or []))   # judge 자기모순 결정론 교정
        sc["type"] = qtype
        sc["n_todos"] = len(rec.get("todos") or [])
        rows.append(sc)
        fix = f" fix={sc['judge_corrections']}" if sc.get("judge_corrections") else ""
        tag = f"ERR={sc['error'][:24]}" if sc.get("error") else ""
        print(f"  run{run_idx}/{n_runs} [{i}/{len(queries)}] {qtype:13} "
              f"cov={sc['coverage']:.0%} ({sc.get('n_cov',0)}/{sc.get('n_req',0)}) "
              f"noise={len(sc['noise_tools'])}{fix} {tag} | {q[:22]}", flush=True)
    return rows


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5, help="반복 횟수 (기본 5)")
    ap.add_argument("--corpus", default="corpus_compound.yaml")
    ap.add_argument("--limit", type=int, default=0, help="앞 N 쿼리만 (smoke)")
    args = ap.parse_args()

    corpus = yaml.safe_load((_HERE / args.corpus).read_text(encoding="utf-8"))
    client_id = corpus.get("client", "clumi")
    queries = corpus["queries"]
    if args.limit:
        queries = queries[: args.limit]

    judge = LLMClient(LAYER_CONFIGS["planning"])
    print(f"[baseline] {args.runs} runs × {len(queries)} queries, client={client_id}", flush=True)

    # ── N 회 실행 ──
    all_runs: list[list[dict]] = []
    for r in range(1, args.runs + 1):
        rows = await _one_run(queries, client_id, judge, r, args.runs)
        all_runs.append(rows)

    # ── 쿼리별 집계 (런 축으로) ──
    # key = (type, q) → 런별 레코드
    per_q: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for rows in all_runs:
        for sc in rows:
            per_q[(sc["type"], sc["q"])].append(sc)

    q_summary: list[dict] = []
    for (qtype, q), recs in per_q.items():
        errs = sum(1 for r in recs if r.get("error"))
        valid = [r for r in recs if not r.get("error") and r.get("n_req")]
        covs = [r["coverage"] for r in valid]
        n_reqs = [r["n_req"] for r in recs if not r.get("error")]
        noises = [len(r["noise_tools"]) for r in recs if not r.get("error")]
        corrections = sum(r.get("judge_corrections", 0) for r in recs)
        q_summary.append({
            "type": qtype, "q": q,
            "runs": len(recs), "errors": errs, "judge_corrections": corrections,
            "cov_mean": round(statistics.mean(covs), 3) if covs else None,
            "cov_min": min(covs) if covs else None,
            "cov_max": max(covs) if covs else None,
            "cov_spread": round(max(covs) - min(covs), 3) if covs else None,
            "noise_mean": round(statistics.mean(noises), 2) if noises else 0,
            "n_req_values": sorted(set(n_reqs)),         # 변동하면 상류 분해 불안정
            "n_req_unstable": len(set(n_reqs)) > 1,
            "stability": _classify_stability(covs, errs),
            "covs": covs,
        })

    # ── 등급별 집계 ──
    by_lv: dict[str, list[dict]] = defaultdict(list)
    for qs in q_summary:
        by_lv[qs["type"]].append(qs)

    def _lv_cov(rs: list[dict]) -> tuple[float | None, float | None, float | None]:
        flat = [c for qs in rs for c in qs["covs"]]
        if not flat:
            return None, None, None
        return round(statistics.mean(flat), 3), min(flat), max(flat)

    # ── 전체 ──
    all_covs = [c for qs in q_summary for c in qs["covs"]]
    overall_mean = round(statistics.mean(all_covs), 3) if all_covs else None
    overall_stdev = round(statistics.pstdev(all_covs), 3) if len(all_covs) > 1 else 0.0
    total_corrections = sum(qs["judge_corrections"] for qs in q_summary)

    # ── 저장 — T1(M0): corpus stem + run-id 로 비파괴 (기존 회귀 기준선 clobber 방지) ──
    stem = Path(args.corpus).stem.removeprefix("corpus_")
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_base = f"baseline_{stem}_{run_id}"
    _OUT.mkdir(parents=True, exist_ok=True)
    (_OUT / f"{out_base}.json").write_text(
        json.dumps({"runs": args.runs, "corpus": args.corpus, "client": client_id,
                    "overall_mean": overall_mean, "overall_stdev": overall_stdev,
                    "per_query": q_summary, "raw_runs": all_runs},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # ── markdown 요약 ──
    md = ["# 복합쿼리 재현가능 베이스라인 (multi-run)", "",
          f"- {args.runs} runs × {len(queries)} 쿼리 · client={client_id} · corpus={args.corpus}",
          f"- **전체 평균 coverage = {overall_mean:.1%}** (런·쿼리 합산, σ={overall_stdev:.1%})"
          if overall_mean is not None else "- (유효 데이터 없음)",
          f"- judge 자기모순 결정론 교정 = **{total_corrections}건** (evidence_tool 이 plan 에 실재하나 covered=False 였던 noise; 교정 후 수치)",
          "",
          "## 등급별 (평균 / min / max coverage)", "",
          "| 등급 | 평균 | min | max | 쿼리수 |", "|---|---|---|---|---|"]
    for lv in sorted(by_lv):
        mean, lo, hi = _lv_cov(by_lv[lv])
        cnt = len(by_lv[lv])
        if mean is None:
            md.append(f"| {lv} | n/a | n/a | n/a | {cnt} |")
        else:
            md.append(f"| {lv} | {mean:.0%} | {lo:.0%} | {hi:.0%} | {cnt} |")

    # 안정성 분류 카운트
    from collections import Counter
    stab = Counter(qs["stability"] for qs in q_summary)
    md += ["", "## 안정성 분류", "",
           "| 분류 | 수 | 의미 |", "|---|---|---|",
           f"| stable-full | {stab.get('stable-full',0)} | 매 런 100% (안정 정상) |",
           f"| systematic | {stab.get('systematic',0)} | 매 런 <100% (체계 깨짐 → 결정론 fix·R2 후보) |",
           f"| flaky | {stab.get('flaky',0)} | 런마다 출렁 (비결정 → ⒝ Stage3 프롬프트 후보) |",
           f"| no-intent | {stab.get('no-intent',0)} | judge 가 요청 의도 0 판정 |",
           f"| all-error | {stab.get('all-error',0)} | 매 런 에러 |"]

    md += ["", "## 쿼리별 상세 (mean·spread·안정성)", "",
           "| 등급 | 안정성 | mean | min~max | n_req | n_req변동 | noise | raw |",
           "|---|---|---|---|---|---|---|---|"]
    for qs in sorted(q_summary, key=lambda x: (x["type"], x["q"])):
        cov_str = f"{qs['cov_mean']:.0%}" if qs["cov_mean"] is not None else "n/a"
        rng = (f"{qs['cov_min']:.0%}~{qs['cov_max']:.0%}"
               if qs["cov_min"] is not None else "n/a")
        nreq = ",".join(str(x) for x in qs["n_req_values"]) or "-"
        unst = "⚠" if qs["n_req_unstable"] else ""
        md.append(f"| {qs['type']} | {qs['stability']} | {cov_str} | {rng} | "
                  f"{nreq} | {unst} | {qs['noise_mean']} | {qs['q'][:26]} |")

    md += ["", "## 해석 가이드", "",
           "- **systematic** 쿼리 = 매 런 일관 미달 → *결정론적 깨짐*. R2(sub_intents 본배선)·게이트로 고칠 후보. broad·multi-run 없이 검증 가능.",
           "- **flaky** 쿼리 = 런마다 출렁 → *비결정 깨짐*. ⒝ Stage3 프롬프트 정밀화 후보. 고친 뒤엔 반드시 multi-run 재측정.",
           "- **n_req 변동(⚠)** = cognitive/judge 가 같은 쿼리를 매번 다르게 분해 → 상류(인지) 불안정. 측정 자체의 noise 원이므로 해석 시 감안.",
           "- 이 표가 ⒝/R2 적용 후 **회귀 기준선**. 동일 명령으로 재측정해 mean·안정성 비교."]
    (_OUT / f"{out_base}.md").write_text("\n".join(md), encoding="utf-8")

    # ── 콘솔 요약 ──
    print(f"\n[baseline] done → {_OUT / out_base}.{{json,md}}", flush=True)
    if overall_mean is not None:
        print(f"[baseline] 전체 평균 coverage={overall_mean:.1%} (σ={overall_stdev:.1%}) "
              f"· judge 교정 {total_corrections}건", flush=True)
    for lv in sorted(by_lv):
        mean, lo, hi = _lv_cov(by_lv[lv])
        if mean is not None:
            print(f"    {lv:13} mean={mean:.0%} min={lo:.0%} max={hi:.0%}", flush=True)
    print(f"[baseline] 안정성: stable-full={stab.get('stable-full',0)} "
          f"systematic={stab.get('systematic',0)} flaky={stab.get('flaky',0)} "
          f"no-intent={stab.get('no-intent',0)} all-error={stab.get('all-error',0)}", flush=True)
    syst = [qs["q"][:30] for qs in q_summary if qs["stability"] == "systematic"]
    flak = [qs["q"][:30] for qs in q_summary if qs["stability"] == "flaky"]
    if syst:
        print(f"[baseline] systematic(체계 깨짐): {syst}", flush=True)
    if flak:
        print(f"[baseline] flaky(비결정): {flak}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
