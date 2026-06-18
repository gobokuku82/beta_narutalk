"""semantic_contract.py — canonical contract YAML 을 런타임 의미 SSOT 로 읽는 얇은 어댑터 (2026-06-18).

★ 가설([[②의미전달_구조가설_검증계획]]): 단위·함정·정의가 COL_DESC·canonical_translator._m_*·clumi.yaml
3곳에 손복제돼 있으나, 이미 완전 구조화된 docs/agent_specs/ERD/octorad_canonical_contract_v0.1.yaml
("이 SPEC=단일 권위" 명문, 그러나 런타임 read 0건 죽은 문서)이 진짜 SSOT 다. 본 모듈이 그 contract 를
읽어 canonical 키의 의미(unit·trap·semantic)를 노출한다.

리더 패턴 = data_pilot_project/dict_gate.py(safe_load·_leaf 검증됨) 재사용. ★본 슬라이스 = *읽기만* —
기존 COL_DESC·build_data_glossary·6 tool 무변경. import 0(아직 아무도 안 씀). 동치 테스트가 가설 전제 검증.

Status: partial — 첫 슬라이스(read-only adapter). build_data_glossary 위임·조립 어셈블러는 후속(planned).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

# shared/ → parents[5] = beta_v001 (repo 루트). contract 는 repo docs/ 아래.
_CONTRACT = (Path(__file__).resolve().parents[5]
             / "docs" / "agent_specs" / "ERD" / "octorad_canonical_contract_v0.1.yaml")

# canonical 정본 키의 짧은/변형 별칭 → contract 키 (suffix 규약·tool 산출 평탄화 키 흡수).
# (정본에서 파생하는 alias 맵 — COL_DESC 가 roas/roas_x 양쪽 수동등재하던 것을 1소스로.)
_ALIAS = {
    "roas": "roas_x", "ctr": "ctr_pct", "cvr": "cvr_pct", "link_ctr": "link_ctr_pct",
    "cpc": "cpc_krw", "cpm": "cpm_krw", "tacos_pct": "tacos", "cpa_krw": "cpa",
    "ad_cost": "ad_cost_krw", "conversion_revenue": "conversion_revenue_krw",
    "conversions": "conversion_count", "date": "report_date",
}


@dataclass(frozen=True)
class SemanticEntry:
    key: str
    layer: str            # measure | metric | dimension | time
    unit: str | None      # 명시 unit 또는 meta.unit_suffix 파생
    type: str | None
    semantic: str | None  # 의미 (⚠ 함정 라벨 포함)
    trap: str | None      # semantic 에서 추출한 ⚠ 함정 절
    formula: str | None   # metric 만


@lru_cache(maxsize=1)
def load_contract() -> dict:
    """contract YAML 적재 (1회 캐시). 죽은 문서를 런타임이 처음 read."""
    return yaml.safe_load(_CONTRACT.read_text(encoding="utf-8")) or {}


def _trap(semantic: str | None) -> str | None:
    """semantic 텍스트에서 ⚠ 함정 절만 추출 (★ 절 전까지)."""
    if not semantic or "⚠" not in semantic:
        return None
    seg = semantic.split("⚠", 1)[1].split("★", 1)[0]
    return ("⚠" + seg).strip()


@lru_cache(maxsize=1)
def _entries() -> dict[str, SemanticEntry]:
    c = load_contract()
    suffix = (c.get("meta") or {}).get("unit_suffix") or {}
    out: dict[str, SemanticEntry] = {}
    for layer in ("measures", "metrics", "dimensions", "time"):
        for key, d in (c.get(layer) or {}).items():
            if not isinstance(d, dict):
                continue
            unit = d.get("unit")
            if unit is None:                       # 명시 없으면 suffix 규약에서 파생
                for suf, u in suffix.items():
                    if key.endswith(suf):
                        unit = u
                        break
            sem = d.get("semantic")
            out[key] = SemanticEntry(
                key=key,
                layer="time" if layer == "time" else layer.rstrip("s"),
                unit=unit, type=d.get("type"), semantic=sem,
                trap=_trap(sem), formula=d.get("formula"),
            )
    return out


def term(key: str) -> SemanticEntry | None:
    """canonical 키(또는 짧은 별칭)의 의미 엔트리. 없으면 None (_RESIDUAL = contract 밖)."""
    e = _entries()
    return e.get(key) or e.get(_ALIAS.get(key, ""))


# 단위 → LLM-grade 단위 토큰 (semantic에 단위가 안 적혔을 때 동봉 — ②축 단위 오독 방지 핵심)
_UNIT_PHRASE = {
    "KRW": "원", "percent": "%", "ratio(배수)": "배수, %아님", "ratio": "비율",
    "count": "정수", "count_unique": "정수(고유)", "정수건수": "정수",
}


def describe(key: str) -> str | None:
    """canonical 키의 LLM-grade 한 줄 설명 (contract SSOT 파생). _RESIDUAL이면 None.

    semantic(함정·해석 포함 LLM-grade)이 있으면 그것을, 없으면 formula+단위로 파생.
    단위 토큰(원/배수/%)이 텍스트에 없으면 동봉 — 손코딩 COL_DESC를 대체하는 provenance 경로.
    """
    e = term(key)
    if e is None:
        return None
    unit_tok = _UNIT_PHRASE.get(str(e.unit or ""), str(e.unit or ""))
    head = unit_tok.split(",")[0].strip() if unit_tok else ""
    if e.semantic:
        s = e.semantic.strip()
        return s if (not head or head in s) else f"{s} (단위: {unit_tok})"
    if e.formula:
        return f"{e.formula} (단위: {unit_tok})" if unit_tok else e.formula
    if unit_tok:
        return f"(단위: {unit_tok})"
    return None   # semantic·formula·unit 다 없음 → 호출측 COL_DESC fallback


def unit_token(key: str) -> str | None:
    """canonical 키의 LLM-grade 단위 토큰만 (원 / 배수,%아님 / % / 비율 / 정수). 없으면 None.

    describe()가 한 줄 *설명*이라면 이쪽은 *단위만* — 값에 바로 동봉하는 용도
    (인라인 단위 동봉: `roas: 4.46` → `roas: 4.46 (배수, %아님)`). 단위가 값과 동행해
    별도 사전 블록을 건너뛰어도 LLM이 단위를 못 놓치게 한다. 소스 = contract(SSOT).
    """
    e = term(key)
    if e is None or e.unit is None:
        return None
    return _UNIT_PHRASE.get(str(e.unit), str(e.unit))


def all_keys() -> set[str]:
    """contract 가 정의한 canonical 키 전체 (별칭 제외)."""
    return set(_entries())


__all__ = ["SemanticEntry", "load_contract", "term", "all_keys", "describe", "unit_token"]
