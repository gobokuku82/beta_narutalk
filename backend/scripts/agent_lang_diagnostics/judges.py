"""M0 측정 전용 판정기 — T3 표시(다중 산출 표출) · T4 귀속(의도→todo 완주) (2026-06-12).

계획_멀티쿼리_복합의도_수직슬라이스 §2: ④단(의도별 표출)·③단(의도별 완주율)을 정량화하는
측정기가 없어 신설. **제품 코드 무수정** — 전부 측정 쪽에서 결정론 join/keyword 판정.

순수 함수만 (LLM·DB·graph 불요) → tests/test_m0_judges.py 가 단위 박제.
소비자: measure_stage1_coverage.py (full-graph 멀티런 측정, --judge 모드).

Status: complete — M0 측정기 정비 4건 중 T3·T4.
"""
from __future__ import annotations

import json


def display_blob(payload: dict | None) -> str:
    """ResponsePayload dict → 표시 판정 대상 문자열 (text + summary + error + attachments).

    next_actions·meta 는 제외 — "추천 후속 작업" 같은 상투구가 '추천' 의도 키워드를
    거짓 충족시키는 오염원이라서 (T3 의 보수성 유지).
    """
    if not isinstance(payload, dict):
        return ""
    parts = [payload.get("text") or "", payload.get("summary") or "", payload.get("error") or ""]
    att = payload.get("attachments") or []
    if att:
        try:
            parts.append(json.dumps(att, ensure_ascii=False, default=str))
        except (TypeError, ValueError):
            parts.append(str(att))
    return "\n".join(p for p in parts if p)


def judge_display(expect_display: list[dict] | None, blob: str) -> dict:
    """T3 — 의도별 산출이 응답 표면에 보이는가 (결정론 keyword 판정, ④단).

    expect_display 항목: {label, any: [kw...]} / {label, all: [kw...]} (둘 다 가능 — AND).
      any = 하나라도 blob 에 있으면 충족 · all = 전부 있어야 충족.
      all 의 원소가 list 면 그 안에서 any-of (예: all: [["채널","channel"], ["ROAS","roas"]]
      — 분해 렌더가 영문 데이터 키를 쓰는 현실 보정, T3-2 2026-06-12).

    한계(v1, 계획서 박제): keyword 존재 판정이라 "X 는 실패했습니다(사유)" 정직 고지도
    표출로 센다 — 그게 맞다 (G8 의 기대 = 부재의 침묵 금지). 거짓 서사 여부는
    ③단 귀속(judge_attribution)과 교차해 읽는다: 표출⭕+완주❌ = 정직 고지 or 거짓 서사 후보.
    """
    rows = []
    for it in expect_display or []:
        any_kw = it.get("any") or []
        all_kw = it.get("all") or []
        if any_kw or all_kw:
            ok_any = any(k in blob for k in any_kw) if any_kw else True
            ok_all = all(
                (any(x in blob for x in k) if isinstance(k, list) else k in blob)
                for k in all_kw
            ) if all_kw else True
            displayed: bool | None = ok_any and ok_all
        else:
            displayed = None   # 판정 기준 미기재 — 분모에서 제외 (False 로 오판하지 않음)
        rows.append({"label": it.get("label", "?"), "displayed": displayed})

    judged = [r for r in rows if r["displayed"] is not None]
    n_disp = sum(1 for r in judged if r["displayed"])
    return {
        "items": rows,
        "n_expect": len(judged),
        "n_displayed": n_disp,
        "display_rate": round(n_disp / len(judged), 2) if judged else None,
        "missing": [r["label"] for r in judged if not r["displayed"]],
    }


def judge_attribution(requested: list[dict] | None, plan_todos: list[dict] | None,
                      exec_todos: dict | None) -> dict:
    """T4 — 의도→todo 결정론 join → 의도별 완주율 (③단, 측정 전용).

    requested  = score_coverage LLM-judge 의 의도 행 (intent / covered / evidence_tool)
                 — _reconcile_judge 교정 *후* 를 넣을 것 (judge 자기모순 noise 차단).
    plan_todos = plan["todos"] ({id, tool, ...})
    exec_todos = execution_result["todos"] ({todo_id: {status, tool?, ...}})

    join: evidence_tool == 실행 todo 의 tool(TodoResult.tool) — 없으면 plan id→tool 경유.
    같은 tool 의 todo 가 여럿이면 전부 그 의도에 귀속. completed = 귀속분 중 completed ≥1.

    산출 어휘:
      lost   = evidence_tool 자체가 없거나 어느 todo 와도 join 안 됨 (계획/judge 단계 소실)
      broken = 귀속은 됐는데 completed 0 (실행 단계 깨짐 — skip/fail)
    """
    plan_tool_by_id = {t.get("id"): t.get("tool") for t in (plan_todos or [])}
    rows = []
    for r in requested or []:
        ev = (r.get("evidence_tool") or "").strip()
        statuses: list[str | None] = []
        if ev:
            for tid, tr in (exec_todos or {}).items():
                tool = (tr or {}).get("tool") or plan_tool_by_id.get(tid)
                if tool == ev:
                    statuses.append((tr or {}).get("status"))
        completed = any(s == "completed" for s in statuses)
        rows.append({
            "intent": r.get("intent"), "evidence_tool": ev or None,
            "covered": bool(r.get("covered")), "statuses": statuses,
            "attributed": bool(statuses), "completed": completed,
        })

    attributed = [r for r in rows if r["attributed"]]
    n_done = sum(1 for r in attributed if r["completed"])
    return {
        "items": rows,
        "n_intents": len(rows),
        "n_attributed": len(attributed),
        "n_completed": n_done,
        "completion_rate": round(n_done / len(attributed), 2) if attributed else None,
        "lost": [r["intent"] for r in rows if not r["attributed"]],
        "broken": [r["intent"] for r in attributed if not r["completed"]],
    }
