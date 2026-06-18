"""C2 A/B — ②축 의미배선 인과 측정 (반증③, 2026-06-18).

LLM 분석기 4종(insight_extractor·diagnoser·forecaster·summary_generator)을 *동일* ②축-자극 입력으로
실 LLM 호출하되, 의미 전달 *방식*을 6 조건으로 토글 → 산출물의 단위오독·날조를 LLM 판정기로 측정.
  · off = 사전 없음(벌거벗은 숫자, S1-S3 이전 상태)
  · v1  = 손코딩 COL_DESC 별도 블록 (S1-S3)
  · v2  = contract 파생 별도 블록 (provenance, a9538e7)
  · v3  = v2 내용 + ★강제형 — 블록을 "반드시 준수" 헤더로 감싸고 system_prompt(상위 권위)에 단위 메타규칙 주입
  · v4  = ★인라인 단위 동봉 — 별도 블록 제거, 값에 단위 붙여 전달(`tacos_pct: 22.37` → `"22.37 (%)"`)
  · v5  = v2 블록 + v4 인라인 (둘 다 — 블록 제거가 해가 되는지 분리)
측정 질문: OFF vs ON = 의미배선이 ②축 할루시를 줄이나 / v2 vs (v3·v4·v5) = LLM이 *무시 못 하게* 만들면 더 주나.

★공정성: v3 강제형·v4 인라인의 단위·의미는 전부 SSOT(contract semantic_contract)에서 파생.
  정답(TRUTH)을 프롬프트에 주입하지 않는다(teaching-to-test 금지). 조건 차이는 *전달 방식*만.

토글 = 소스/모듈 전역 패치 — 4 tool 이 호출 시 참조하는 build_data_glossary·SYSTEM_PROMPT·
  COL_DESC·describe 를 조건별로 갈아끼움. 전역 가변상태라 *직렬* 실행(병렬 금지).
사용: uv run python scripts/c2_ab_glossary.py [N]   (N=조건당 반복, 기본 1)
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import app.dream_agent.tools.shared.col_dictionary as cd_mod          # noqa: E402
import app.dream_agent.tools.shared.semantic_contract as sc_mod       # noqa: E402
import app.dream_agent.tools.analysis.llm.insight_extractor as ie_mod  # noqa: E402
import app.dream_agent.tools.analysis.llm.diagnoser as dg_mod         # noqa: E402
import app.dream_agent.tools.analysis.llm.forecaster as fc_mod        # noqa: E402
import app.dream_agent.tools.report.summary_generator as sg_mod       # noqa: E402
from app.dream_agent.llm_manager.client import get_llm_client          # noqa: E402
from app.dream_agent.models import ExecutionContext                    # noqa: E402
from types import SimpleNamespace                                      # noqa: E402

_ORIG_DESCRIBE = sc_mod.describe
_ORIG_COL_DESC = dict(cd_mod.COL_DESC)
_REAL_BDG = cd_mod.build_data_glossary               # 4 tool 이 import 한 동일 함수 객체
_TOOL_MODS = [ie_mod, dg_mod, fc_mod, sg_mod]
_ORIG_SYS = {m: m.SYSTEM_PROMPT for m in _TOOL_MODS}

# v3 강제형 — 일반 메타규칙(특정 값 미포함 = teaching-to-test 아님).
_IMP_HEADER = "[데이터 단위 — 반드시 이 단위로만 서술. 배수↔%↔비율↔원 절대 혼동 금지]\n"
_IMP_SYS = ("\n\n[단위 규칙 — 최우선·절대 준수]\n"
            "데이터에 단위가 명시된 지표는 그 단위로만 서술하라. 단위를 임의로 바꾸면 치명적 오답이다"
            "(배수↔%↔비율↔원 혼동 금지). 단위가 불명확하면 추측하지 말고 단위를 생략하라.")


def _v3_glossary(inputs, cid=None):
    """v2 블록(SSOT 파생) 그대로 + 강제형 헤더."""
    return _IMP_HEADER + _REAL_BDG(inputs, cid)


def _empty_glossary(*_a, **_k) -> str:
    """v4 — 별도 사전 블록 제거(인라인만 의존)."""
    return ""


# ②축-자극 입력: ★하드 케이스 — LLM이 학습지식으로 *모를* 비자명 지표(이름만으론 단위 추측 어려움).
#   easy(roas/cac)는 LLM이 이미 알아 glossary 무효였음(1차 A/B). 진짜 ②축 가치는 비자명 키에서 갈림.
_INNER = {
    "tacos_pct": 22.37,         # TACoS = 광고비/매출 (%) — roas와 헷갈리기 쉬움
    "msg_roi_pct": 35.0,        # 메시징 ROI (%) — ROAS(배수)와 다른 축, 혼동 위험
    "impression_frequency": 1.8,  # 노출/도달 (비율) — 구 frequency_ratio 개명(2026-06-19, 3차 결과 반영)
    "promotion_roas": 1.62,     # 프로모션 ROAS (배수) — 분모가 전사 총마케팅비(함정)
    "cpc_krw": 1850,            # CPC (원)
}
PAYLOAD = {"m": {"data": dict(_INNER)}}


def _annotate_inline(d: dict) -> dict:
    """값에 단위 토큰 동봉 (v4/v5). 단위 소스 = contract(SSOT). 미해결 키는 원값 유지."""
    out = {}
    for k, v in d.items():
        tok = sc_mod.unit_token(k)
        out[k] = f"{v} ({tok})" if tok else v
    return out


PAYLOAD_INLINE = {"m": {"data": _annotate_inline(_INNER)}}

# 정답(판정기 ground truth) — 측정 전용. 프롬프트엔 절대 주입 안 함.
# ★frequency 절은 이름-무관·의미기반(v6/v7 개명 조건서 키 이름이 바뀌어도 동일 지표로 판정).
TRUTH = ("tacos_pct=22.37(★%, 광고비÷매출), msg_roi_pct=35(★%, ROI — ROAS 배수와 다른 축), "
         "노출빈도 지표=1.8(★노출÷도달=한 사람이 평균 본 광고 횟수, 비율. '구매빈도/구매횟수' 등 "
         "고객 구매행동 지표가 절대 아님), promotion_roas=1.62(★배수, %아님), cpc_krw=1,850(원)")

# v6/v7 개명 가설(3차, freq mode) — frequency_ratio 의 *이름*이 LLM 의 '구매빈도(RFM)' prior 와 충돌하는지.
#   정의는 (구매빈도 경고 없는) 깨끗한 노출빈도 정의로 *고정* → 정보가 적은데도 오독 줄면 이름이 원인.
#   ★결과(freq_misread v2 7→v6 0→v7 2) = 이름이 원인 확정 → 캐논키 impression_frequency 로 실개명(2026-06-19).
#   본 freq mode 는 그 3차 실험 보존(결과 JSON+dossier §11). 개명 후 canonical 이미 impression_frequency.
_RENAME = {"v6": "impression_frequency", "v7": "exposures_per_reach"}
_FREQ_CLEAN_DEF = "광고 노출빈도 = 노출수 ÷ 도달수. 한 이용자가 평균 본 광고 횟수(예 1.8 = 평균 1.8회). 단위 = 비율."

# v8 (roas mode, 4차) — promotion_roas 단위(배수vs%) 오독이 *접미사 컨벤션 결손* 탓인지.
#   meta.unit_suffix._x = ratio(배수). roas_x 는 _x 라 0오류(easy). promotion_roas 는 _x 없음.
#   promotion_roas → promotion_roas_x 개명(정의 고정·이름만) → 단위오독 줄면 '_x 접미사'가 이름 신호.
#   msg_roi_pct(ROI≠ROAS 축혼동)는 _pct 이미 맞음 — 동음이의 아닌 개념혼동이라 관찰만(이름 가설 아님).
_PROAS_OLD, _PROAS_NEW = "promotion_roas", "promotion_roas_x"
_ROAS_CONDS = ["v2", "v8"]

TOOLS = [("insight_extractor", ie_mod.InsightExtractor, "insights"),
         ("diagnoser", dg_mod.Diagnoser, "diagnosis"),
         ("forecaster", fc_mod.Forecaster, "forecast"),
         ("summary_generator", sg_mod.SummaryGenerator, "summary")]
_FULL_CONDS = ["off", "v1", "v2", "v3", "v4", "v5"]   # 전달 *방식* (1·2차)
_FREQ_CONDS = ["v2", "v6", "v7"]                        # ★개명 가설 (v2=통제, v6/v7=개명)
_INLINE_CONDS = {"v4", "v5"}


def _renamed_payload(new_name: str) -> dict:
    """현 빈도 키를 new_name 으로 개명(값 동일). 의미 충돌이 *이름* 탓인지 분리.
    이름 무관 tolerant — 캐논 개명(impression_frequency) 전/후 모두 동작."""
    inner = dict(_INNER)
    cur = next((k for k in ("frequency_ratio", "impression_frequency") if k in inner), None)
    if cur:
        inner[new_name] = inner.pop(cur)
    return {"m": {"data": inner}}


def _rename_in_payload(old: str, new: str) -> dict:
    """_INNER 의 old 키를 new 로 개명(값 동일). 정의 고정·이름만 — roas mode."""
    inner = dict(_INNER)
    if old in inner:
        inner[new] = inner.pop(old)
    return {"m": {"data": inner}}


def _payload_for(cond: str) -> dict:
    if cond in _RENAME:
        return _renamed_payload(_RENAME[cond])
    if cond == "v8":
        return _rename_in_payload(_PROAS_OLD, _PROAS_NEW)
    if cond in _INLINE_CONDS:
        return PAYLOAD_INLINE
    return PAYLOAD


def _make_rename_describe(new_name: str):
    """개명 키엔 깨끗한 노출빈도 정의(구매빈도 경고 *없음*) — 나머지는 v2 그대로."""
    def _d(k):
        if k == new_name:
            return _FREQ_CLEAN_DEF
        return _ORIG_DESCRIBE(k)
    return _d


def _make_alias_describe(new_name: str, src_key: str):
    """new_name 에 src_key 의 정의를 그대로(정의 고정·이름만 변수) — 나머지는 v2."""
    def _d(k):
        if k == new_name:
            return _ORIG_DESCRIBE(src_key)
        return _ORIG_DESCRIBE(k)
    return _d


def _restore() -> None:
    """전 모듈 전역을 v2(정상 baseline)로 복원."""
    sc_mod.describe = _ORIG_DESCRIBE
    cd_mod.COL_DESC = dict(_ORIG_COL_DESC)
    for m in _TOOL_MODS:
        m.SYSTEM_PROMPT = _ORIG_SYS[m]
        m.build_data_glossary = _REAL_BDG


def _set_condition(cond: str) -> None:
    _restore()                                       # 항상 v2 baseline 에서 출발
    if cond == "off":
        sc_mod.describe = lambda k: None
        cd_mod.COL_DESC = {}                          # 사전 비움 → '(데이터 사전 없음)' fallback
    elif cond == "v1":
        sc_mod.describe = lambda k: None              # contract off → COL_DESC fallback
    elif cond == "v2":
        pass                                          # baseline 그대로
    elif cond == "v3":                                # 강제형 헤더 + system_prompt 단위 규칙
        for m in _TOOL_MODS:
            m.SYSTEM_PROMPT = _ORIG_SYS[m] + _IMP_SYS
            m.build_data_glossary = _v3_glossary
    elif cond == "v4":                                # 블록 제거(인라인만 — payload쪽에서 동봉)
        for m in _TOOL_MODS:
            m.build_data_glossary = _empty_glossary
    elif cond == "v5":                                # v2 블록 + 인라인 동봉
        pass
    elif cond in _RENAME:                             # v6/v7 — frequency 키 개명(payload쪽) + 깨끗한 정의
        sc_mod.describe = _make_rename_describe(_RENAME[cond])
    elif cond == "v8":                                # promotion_roas → promotion_roas_x (정의 고정, 이름만)
        sc_mod.describe = _make_alias_describe(_PROAS_NEW, _PROAS_OLD)


def _ctx(payload: dict) -> ExecutionContext:
    return ExecutionContext(session_id="ab", plan_id="ab", client_id="clumi", previous_results=payload)


def _mk(tool_cls, name):
    t = object.__new__(tool_cls)
    t.spec = SimpleNamespace(name=name, parameters=[])
    return t


def _output_text(out: dict, key: str) -> str:
    v = out.get(key)
    if key == "summary":
        return str(v or "")
    return json.dumps(v or [], ensure_ascii=False)


async def _judge(tool: str, text: str) -> dict:
    prompt = (
        f"마케팅 지표 산출물의 *단위·의미 정확성*을 판정하라. 정답 사실:\n{TRUTH}\n\n"
        f"[{tool} 산출물]\n{text[:1500]}\n\n"
        "다음 JSON만 출력: {{\"unit_error\": bool(roas/mer를 %로 또는 cac를 배수/%로 등 단위 틀림), "
        "\"fabrication\": bool(정답에 없는 수치를 지어냄), "
        "\"freq_misread\": bool(값 1.8인 *노출빈도* 지표를 '구매빈도/구매횟수/방문횟수' 등 고객 구매행동으로 오독 — "
        "산출물에 그 지표 언급이 없으면 false), "
        "\"proas_unit_err\": bool(값 1.62인 *프로모션 ROAS* 를 배수(×)가 아닌 %/비율/금액으로 오독 — 언급 없으면 false), "
        "\"msgroi_axis_err\": bool(값 35인 *메시징 ROI(%)* 를 ROAS(배수)와 같은 축으로 혼동하거나 배수로 오독 — 언급 없으면 false), "
        "\"detail\": \"근거 한 줄\"}}"
    )
    client = get_llm_client("execution")
    r = await client.generate_json(prompt=prompt, system_prompt="너는 엄격한 단위·의미 검증기다. 산출물에 단위 언급이 아예 없으면 unit_error=false.")
    return r if isinstance(r, dict) else {"unit_error": None, "fabrication": None, "freq_misread": None,
                                          "proas_unit_err": None, "msgroi_axis_err": None, "detail": "judge 실패"}


async def main() -> None:
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    mode = sys.argv[2] if len(sys.argv) > 2 else "full"
    conds = {"freq": _FREQ_CONDS, "roas": _ROAS_CONDS}.get(mode, _FULL_CONDS)
    out_name = f"c2_ab_glossary_{mode}.json" if mode in ("freq", "roas") else "c2_ab_glossary.json"
    results = []
    for cond in conds:
        payload = _payload_for(cond)
        for name, cls, out_key in TOOLS:
            for i in range(reps):
                _set_condition(cond)
                try:
                    out = await _mk(cls, name).execute({}, _ctx(payload))
                except Exception as e:  # noqa: BLE001
                    results.append({"cond": cond, "tool": name, "error": f"{type(e).__name__}: {e}"})
                    continue
                _set_condition("v2")  # judge는 정상 조건에서
                text = _output_text(out, out_key)
                verdict = await _judge(name, text)
                results.append({"cond": cond, "tool": name, "rep": i,
                                "unit_error": verdict.get("unit_error"),
                                "fabrication": verdict.get("fabrication"),
                                "freq_misread": verdict.get("freq_misread"),
                                "proas_unit_err": verdict.get("proas_unit_err"),
                                "msgroi_axis_err": verdict.get("msgroi_axis_err"),
                                "detail": verdict.get("detail"), "out": text[:300]})
                if mode == "roas":
                    print(f"[{cond:3s}] {name:18s} proas_unit_err={verdict.get('proas_unit_err')} "
                          f"msgroi_axis_err={verdict.get('msgroi_axis_err')} unit_err={verdict.get('unit_error')} "
                          f":: {str(verdict.get('detail'))[:80]}")
                else:
                    print(f"[{cond:3s}] {name:18s} unit_err={verdict.get('unit_error')} "
                          f"freq_misread={verdict.get('freq_misread')} fab={verdict.get('fabrication')} "
                          f":: {str(verdict.get('detail'))[:80]}")
    _restore()

    # 집계
    from collections import defaultdict
    tally = defaultdict(lambda: {"n": 0, "unit_err": 0, "freq_misread": 0, "proas_unit_err": 0, "msgroi_axis_err": 0, "fab": 0})
    for r in results:
        if "error" in r:
            continue
        t = tally[r["cond"]]
        t["n"] += 1
        t["unit_err"] += 1 if r.get("unit_error") else 0
        t["freq_misread"] += 1 if r.get("freq_misread") else 0
        t["proas_unit_err"] += 1 if r.get("proas_unit_err") else 0
        t["msgroi_axis_err"] += 1 if r.get("msgroi_axis_err") else 0
        t["fab"] += 1 if r.get("fabrication") else 0
    print(f"\n=== ②축 A/B 요약 (mode={mode}) ===")
    for cond in conds:
        t = tally[cond]
        if mode == "roas":
            print(f"  {cond:3s}: n={t['n']}  proas_unit_err={t['proas_unit_err']}  msgroi_axis_err={t['msgroi_axis_err']}  unit_error={t['unit_err']}")
        else:
            print(f"  {cond:3s}: n={t['n']}  unit_error={t['unit_err']}  freq_misread={t['freq_misread']}  fabrication={t['fab']}")
    if mode == "freq":
        print("\n해석: v2(frequency_ratio) vs v6(impression_frequency) vs v7(exposures_per_reach)")
        print("      freq_misread↓ 면 이름이 '구매빈도' prior 와 충돌(개명이 floor 깸).")
    elif mode == "roas":
        print("\n해석: v2(promotion_roas) vs v8(promotion_roas_x). proas_unit_err↓ 면 '_x 접미사 컨벤션'이 단위 신호(개명 대상).")
        print("      msgroi_axis_err 는 두 조건서 동일(이름 가설 아님 — 변하면 noise). 안 줄면 ROI≠ROAS 는 semantic 바닥.")
    else:
        print("\n해석: OFF vs ON = 의미배선이 ②축↓ / v2 vs (v3강제형·v4인라인·v5둘다) = 무시 못 하게 하면 더↓")

    out_dir = _BACKEND.parent / "docs" / "_claude" / "4layer_system" / "diag_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / out_name).write_text(
        json.dumps({"results": results, "tally": {k: dict(v) for k, v in tally.items()}},
                   ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\n저장: {out_dir / out_name}")


if __name__ == "__main__":
    asyncio.run(main())
