"""col_dictionary — tool-output 키 의미 describer (canonical 의미 = contract SSOT 파생).

S1(2026-06-18)은 손코딩 COL_DESC 사전을 SSOT로 뒀으나, 그 canonical 항목들은
semantic_contract(octorad_canonical_contract YAML)의 *사본*이었다 → 드리프트 위험.
COL_DESC 폐기(2026-06-19): canonical 의미는 contract(`semantic_contract.describe`)가 단일 진실.
이 모듈엔 contract 밖 **tool-output 합성키**(total_*·by_channel·funnel% 등)만 남는다 —
대부분 규칙(접두사)으로 contract 기반서 파생, 단일 canonical이 아닌 합성 개념만 최소 어휘(_SYNTH).

★ 핵심: LLM이 숫자만 보고 단위를 추측하던 ②축 할루시를 막는다(단위 동봉). 캐논 의미는 contract가,
  tool 집계키는 본 describe_or_synth가 책임. 손복제 canonical 사전(49키)은 제거(이미 describe에 shadowed).

Status: complete — COL_DESC 폐기, contract-파생 + tool-output 합성 describer (2026-06-19).
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml

# client 프로필(metric_glossary) 경로. shared/col_dictionary.py → parents[2]=dream_agent.
# (★주의: qa_responder 가 parents[2]=tools 로 오계산해 glossary 가 빈 채 돌던 버그를 본 SSOT 가 흡수.)
_CLIENTS_DIR = Path(__file__).resolve().parents[2] / "llm_manager" / "prompts" / "clients"

# ── tool-output 합성키 최소 어휘 (contract 밖 = 단일 canonical 파생 불가한 합성 개념만) ──
#   canonical 키(ad_cost_krw·roas_x·impression_frequency 등)는 여기 없음 — contract.describe 가 SSOT.
#   total_<canonical>·weighted_avg_<canonical>·pct_of_* 는 _AGG 규칙으로 파생(아래 describe_or_synth).
_SYNTH: dict[str, str] = {
    # 차원/식별자 (tool-output 라벨 — contract dimensions 밖)
    "channel": "광고 채널 (meta/naver_sa/advoost/google/kakao/talktalk)",
    "period": "집계 월 (YYYY-MM)",
    "order_id": "주문 식별자",
    "by_channel": "채널별 값 (보통 광고비, 원)",
    # 합성 measure/metric (단일 canonical 아닌 tool 집계 — 분모/분자가 복합)
    "new_members_count": "신규 회원수 (정수, 해당 월 가입)",
    "promotion_revenue": "프로모션 매출 (원, 쿠폰/할인코드 주문)",
    "blended_platform_roas_x": "통합 플랫폼 ROAS (배수, %아님)",
    "total_marketing_cost": "총 마케팅비 (원, = 광고비+메시징비, MER 분모)",
    "total_marketing_cost_krw": "총 마케팅비 (원, = 광고비+메시징비, MER 분모)",
    "total_cost": "총 마케팅비 (원, MER 분모)",
    "total_revenue": "총 매출 (원, MER 분자)",
    "revenue_total": "총 매출 (원, MER 분자)",
}

# 집계 접두사 → 라벨. total_<canonical>·weighted_avg_<canonical> 를 contract base 에서 파생.
_AGG_PREFIX: dict[str, str] = {"total_": "총", "weighted_avg_": "가중평균"}


def describe_or_synth(key: str) -> str | None:
    """키의 LLM-grade 한 줄 의미. canonical → contract(SSOT) describe, 아니면 tool-output 합성 규칙/어휘.

    우선순위: contract.describe (canonical SSOT) → _SYNTH 어휘 → 집계 접두사 규칙(총/가중평균) →
    퍼널% → None. canonical 의미를 손복제하지 않는다(드리프트 0).
    """
    from app.dream_agent.tools.shared import semantic_contract as _sc
    d = _sc.describe(key)
    if d:
        return d
    if key in _SYNTH:
        return _SYNTH[key]
    for pfx, label in _AGG_PREFIX.items():
        if key.startswith(pfx):
            base = key[len(pfx):]
            tok = _sc.unit_token(base)
            if tok:
                return f"{label} {base} (단위: {tok})"   # 예 total_ad_cost_krw → '총 ad_cost_krw (단위: 원)'
    if key.startswith("pct_of_"):
        return "퍼널 단계 비율 (%, 직전/최상단 대비)"
    return None


def load_client_glossary(client_id: str | None) -> str:
    """client metric_glossary → 'term: def' 텍스트. 없으면 ''(best-effort). qa_responder 패턴 일반화·공용."""
    if not client_id:
        return ""
    path = _CLIENTS_DIR / f"{client_id}.yaml"
    if not path.exists():
        return ""
    try:
        profile = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001
        return ""
    glos = profile.get("metric_glossary") or []
    return "\n".join(f"- {g.get('term')}: {g.get('def', '')}" for g in glos if g.get("term"))


def _gather_keys(data: Any, _depth: int = 3) -> set[str]:
    """입력에 등장한 키를 중첩 rows[] 행까지 수집 (G-B 2026-06-18).

    ★함정 단위 키(ctr/cpc/ad_cost 등)가 tool 산출 rows[] *안*에 중첩돼 top-level 사전을 우회하던 갭.
    dict 키 + list[dict] 행 키를 들여다본다(depth 3 = dict→list→행dict 두 컨테이너 홉).
    str 이터러블(키 목록)도 그대로 수용. value 크기 가드는 호출측 collect_inputs 책임.
    """
    out: set[str] = set()
    if isinstance(data, Mapping):
        for k, v in data.items():
            if isinstance(k, str):
                out.add(k)
            if _depth > 1:
                out |= _gather_keys(v, _depth - 1)
    elif isinstance(data, (list, tuple, set)):
        for item in data:
            if isinstance(item, str):
                out.add(item)
            elif _depth > 1:
                out |= _gather_keys(item, _depth - 1)
    return out


def build_data_glossary(data: Mapping[str, Any] | Iterable[str], client_id: str | None = None) -> str:
    """입력에 등장한 키만 골라 [칼럼 의미·단위] + [지표 정의] 합성 텍스트 (S2).

    execution 해석 LLM 프롬프트에 끼워 LLM이 단위·함정을 인지하게 한다.
    중괄호 없는 평문 — .format() 충돌 방지. dict 를 주면 rows[] 중첩 키까지 1-depth 수집(G-B).
    canonical 의미 = contract(SSOT) 파생, tool-output 합성키 = describe_or_synth 규칙/어휘.
    """
    lines: list[str] = []
    for k in sorted(_gather_keys(data)):
        if k.startswith("_"):
            continue
        desc = describe_or_synth(k)
        if desc:
            lines.append(f"- {k}: {desc}")
    parts: list[str] = []
    if lines:
        parts.append("[칼럼 의미·단위]\n" + "\n".join(lines))
    glos = load_client_glossary(client_id)
    if glos:
        parts.append("[지표 정의]\n" + glos)
    return "\n\n".join(parts) or "(데이터 사전 없음 — 키 이름으로 판단하되 단위를 추측 말 것)"


__all__ = ["describe_or_synth", "build_data_glossary", "load_client_glossary"]
