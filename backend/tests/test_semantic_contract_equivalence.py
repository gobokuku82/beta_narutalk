# -*- coding: utf-8 -*-
"""첫 슬라이스 동치 테스트 — contract 파생 의미 ↔ 현 COL_DESC (② 가설 핵심 전제 검증).

가설(docs/_claude/plans/②의미전달_구조가설_검증계획_2026-06-18.md): 흩어진 의미(COL_DESC·
canonical_translator._m_*·clumi.yaml)가 octorad_canonical_contract 한 SSOT 에서 파생 가능하다.
- green = 전제 확인(SSOT 승격 가능) / red(단위 모순·핵심 canonical 미파생) = 반증① 신호.
- ★본 슬라이스 동작변경 0 — COL_DESC·build_data_glossary·6 tool 무변경, 이 테스트만 신설.
"""
from __future__ import annotations

from app.dream_agent.tools.shared.col_dictionary import COL_DESC
from app.dream_agent.tools.shared import semantic_contract as sc


def _unit_consistent(contract_unit, desc: str) -> bool:
    """contract unit ↔ COL_DESC desc 텍스트가 *모순 아닌가* (SSOT 승격이 의미 안 바꿈)."""
    if not contract_unit:
        return True                       # dimension 등 unit 없음 → 검사 제외
    u = str(contract_unit)
    if "KRW" in u:
        return "원" in desc
    if "배수" in u:                       # ratio(배수) — roas_x·mer: 배수 지표
        return "배" in desc
    if "ratio" in u:                       # 일반 ratio(비율) — impression_frequency 등 (배수 아님)
        return ("비율" in desc) or ("배" in desc)
    if "percent" in u:
        return "%" in desc
    if "count" in u or "정수" in u:
        return ("정수" in desc) or ("수" in desc)
    return True


def test_contract_loads_and_has_sections():
    c = sc.load_contract()
    assert c.get("measures") and c.get("metrics") and c.get("dimensions"), "contract 섹션 부재"
    assert sc.term("ad_cost_krw") and sc.term("roas_x") and sc.term("mer"), "핵심 canonical 미파생"


def test_core_canonical_keys_derive_with_consistent_unit():
    """핵심 canonical 키(+짧은 별칭)가 contract 에서 unit 일관되게 파생."""
    core = [
        "ad_cost_krw", "impressions", "clicks", "conversion_count", "conversion_revenue_krw",
        "roas_x", "ctr_pct", "cvr_pct", "cpc_krw", "mer", "member_id", "campaign_id",
        # tool 산출 짧은 별칭 (suffix 규약 흡수)
        "roas", "ctr", "ad_cost", "conversions",
    ]
    for k in core:
        e = sc.term(k)
        assert e is not None, f"core canonical '{k}' contract 미파생 (★반증① 신호)"
        if k in COL_DESC:
            assert _unit_consistent(e.unit, COL_DESC[k]), \
                f"'{k}': contract unit={e.unit} ↔ COL_DESC '{COL_DESC[k]}' 단위 모순"


def test_added_metrics_now_covered():
    """2026-06-18 추가 지표(cac/cpa/aov/promotion_roas/promotion_share_pct)가 contract서 파생·단위일관.

    이전엔 _RESIDUAL(손코딩 COL_DESC에만)이던 것을 contract metrics에 추가 → 회귀 가드.
    blended_platform_roas_x는 프로덕션 tool 부재로 추가 안 함(여전히 미파생 = 의도).
    """
    expect = {"cac": "원", "cpa": "원", "aov": "원",
              "promotion_roas": "배", "promotion_share_pct": "%"}
    for k, unit_tok in expect.items():
        e = sc.term(k)
        assert e is not None, f"추가 지표 '{k}' contract 미파생"
        if k in COL_DESC:
            assert _unit_consistent(e.unit, COL_DESC[k]), \
                f"'{k}': contract unit={e.unit} ↔ COL_DESC '{COL_DESC[k]}' 단위 모순"
    # cpa_krw 별칭도 cpa로 해소
    assert sc.term("cpa_krw") is not None and sc.term("cpa_krw").key == "cpa"
    # blended_platform_roas_x는 의도적 미추가(tool 없음)
    assert sc.term("blended_platform_roas_x") is None


def test_traps_derive_from_contract():
    """salesAmt=비용·convAmt=매출 함정이 contract semantic 에서 파생 (손복제 불요 입증)."""
    ad = sc.term("ad_cost_krw")
    assert ad.trap and "salesAmt" in (ad.semantic or ""), "ad_cost_krw salesAmt 함정 미파생"
    rev = sc.term("conversion_revenue_krw")
    assert "convAmt" in (rev.semantic or ""), "conversion_revenue_krw convAmt 의미 미파생"


def test_no_unit_contradiction_across_col_desc():
    """COL_DESC 전 키 중 contract 에 있는 것은 단위 모순 0 (SSOT 승격이 기존 의미 안 뒤집음)."""
    contradictions = []
    for k, desc in COL_DESC.items():
        if k.startswith("_"):
            continue
        e = sc.term(k)
        if e and not _unit_consistent(e.unit, desc):
            contradictions.append(f"{k}: contract={e.unit} vs '{desc[:40]}'")
    assert not contradictions, f"단위 모순(SSOT 승격 위험): {contradictions}"


def test_unit_token_inline_grade():
    """unit_token = 값에 동봉할 단위 토큰만 (인라인 단위 동봉 v4 의 단위 소스, contract 파생).

    describe()가 한 줄 설명이면 unit_token 은 단위만 — `roas: 4.46` → `4.46 (배수, %아님)`.
    핵심: %↔배수↔비율↔원이 토큰 수준에서 구분돼야 LLM 이 값과 함께 단위를 못 놓침.
    """
    expect = {  # 키 → 토큰에 반드시 포함될 문자열
        "roas": "배수", "mer": "배수", "promotion_roas": "배수",
        "tacos_pct": "%", "msg_roi_pct": "%", "ctr_pct": "%",
        "impression_frequency": "비율", "cpc_krw": "원", "cac": "원", "aov": "원",
    }
    for k, tok in expect.items():
        got = sc.unit_token(k)
        assert got is not None, f"unit_token('{k}') None — contract 단위 미파생"
        assert tok in got, f"unit_token('{k}')='{got}' 에 '{tok}' 없음 (단위 토큰 구분 실패)"
    # 배수 지표는 '%아님' 경고를 토큰에 동봉 (값 옆에서 %오독 차단)
    assert "%아님" in (sc.unit_token("roas") or ""), "roas 토큰에 '%아님' 경고 없음"
    # contract 밖(_RESIDUAL) 키는 None
    assert sc.unit_token("by_channel") is None


def test_report_residual_coverage(capsys):
    """진단 보고(assert는 보고용 최소) — COL_DESC 키 중 contract 파생 비율 + _RESIDUAL.

    _RESIDUAL = tool 산출 합성키(total_*·by_channel 등)·contract 갭(cac/cpa/aov)이면 정상.
    canonical *칼럼*이 대량 residual 이면 반증①. 비율 해석은 사람이(보고서).
    """
    keys = [k for k in COL_DESC if not k.startswith("_")]
    covered = sorted(k for k in keys if sc.term(k))
    residual = sorted(k for k in keys if not sc.term(k))
    rate = len(covered) / len(keys) * 100 if keys else 0
    with capsys.disabled():
        print(f"\n[contract 파생 coverage] {len(covered)}/{len(keys)} = {rate:.0f}%")
        print(f"[covered {len(covered)}] {covered}")
        print(f"[_RESIDUAL {len(residual)}] {residual}")
    assert covered, "covered 0 — contract 가 COL_DESC 를 전혀 재현 못 함(반증①)"
