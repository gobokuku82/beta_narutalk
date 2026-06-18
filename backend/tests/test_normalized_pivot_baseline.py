# -*- coding: utf-8 -*-
"""test_normalized_pivot_baseline.py — normalized tool 피봇 *계획서* 검증 베이스라인.

계획서: docs/_claude/plans/normalized_tool_pivot_계획서_2026-06-15.md
성격: "계획"이 아니라 "계획이 의존하는 **현재-상태 사실**"을 박제한다 (characterization).
      피봇 구현(P1~) 전·중 이 사실이 silently drift 하면 즉시 빨강 → 계획 재검토 트리거.

두 묶음 —
  A. TestCrossWorldEquivalence  ★피봇 중심 명제 (§2·§6):
     World A(data_pilot canonical, contract translator) 와
     World B(production ad_cost_total, A3 canonical 전환) 가 동일 raw 에서
     채널별·합 26,806,923 으로 일치 (가 결정 A-5.2 google 포함; 종전 5매체 18,306,923).
     두 독립 canonical 경로의 일관성 검증. (옛 ad_cost_helper World-B 는 A-5.1 폐기.)

  B. TestPivotPlanInvariants    계획 결정의 근거 박제:
     - D4  format_normalizer 폐기 완료 (A-5.3 — canonical_translator 대체, dormant tripwire 제거)
     - P3/P4 ad_cost_helper 소비처 = 정확히 5 tool                → load-bearing 폭발반경
     - P1  Workspace Layer == (raw, cleaned, computed)            → normalized 변경점 tripwire
     - tool catalog 수 == 93 (P2 canonical_translator +1)        → 임팩트맵 분모 baseline

실행: cd backend && uv run pytest tests/test_normalized_pivot_baseline.py -v
"""
from __future__ import annotations

import asyncio
import re
import sys
import typing
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]          # .../backend
REPO = BACKEND.parent                                  # repo root
TOOLS = BACKEND / "app" / "dream_agent" / "tools"
CATALOG = TOOLS / "catalog"

# data_pilot_project 는 bare import(import pipeline) 구조 → 디렉토리를 path 에 추가
_DP = BACKEND / "app" / "data_pilot_project"
if str(_DP) not in sys.path:
    sys.path.insert(0, str(_DP))


# 2026-04 mock 재계산 정답 (run_pilot.EXPECT · ad_cost_helper docstring · methodology §S003 공유)
# 가 결정 A-5.2(2026-06-17): google 광고 매체 포함 re-baseline (18.3M/6.53 → 26.8M/4.46).
EXPECT_CHANNEL = {
    "meta": 9_235_826,
    "naver_sa": 5_999_627,
    "advoost": 3_000_000,
    "google": 8_500_000,
    "kakao": 59_020,
    "talktalk": 12_450,
}
EXPECT_TOTAL = 26_806_923
EXPECT_MER = 4.46
AD_CHANNELS = ("meta", "naver_sa", "advoost", "google")   # compute.AD_CHANNELS
MSG_CHANNELS = ("kakao", "talktalk")              # compute.MSG_CHANNELS


# ════════════════════════════════════════════════════════════════════════
#  A. 교차 세계 동치 — ★피봇 중심 명제
# ════════════════════════════════════════════════════════════════════════
class TestCrossWorldEquivalence:
    """World A(canonical) 가 World B(production) 정답을 재현하는가."""

    @pytest.fixture(scope="class")
    def world_a(self):
        """World A: data_pilot contract translator → compute. (raw 파일 직독)"""
        import pipeline as dp_pipeline
        import compute as dp_compute
        norm = dp_pipeline.run_normalize()
        cmp = dp_compute.compute(norm)
        return {"norm": norm, "computed": cmp}

    @pytest.fixture(scope="class")
    def world_b(self):
        """World B: production ad_cost_total tool (A3 canonical 소비 경로)."""
        from app.dream_agent.models import ExecutionContext
        from app.dream_agent.tools.metrics.ad_cost_total import AdCostTotal
        from app.dream_agent.tools.registry import get_registry
        from app.dream_agent.tools.shared.storage import FileStorage, reset_storage, set_storage
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            set_storage(FileStorage(Path(tmp)))
            try:
                tool = AdCostTotal(get_registry().get("ad_cost_total"))
                ctx = ExecutionContext(session_id="t", plan_id="t", client_id="clumi")
                r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
            finally:
                reset_storage()
        return r

    # ── World B 정답 자체 (회귀 — 기존 test_ad_cost_total 와 중복이나 동치 비교의 닻) ──
    def test_world_b_total_is_canonical_answer(self, world_b):
        assert world_b["total_cost"] == EXPECT_TOTAL, (
            f"World B total {world_b['total_cost']:,} != {EXPECT_TOTAL:,}"
        )

    # ── World A 정답 자체 (live compute — gate stage1 을 코드로 재핀) ──
    def test_world_a_total_marketing_cost(self, world_a):
        assert world_a["computed"]["total_marketing_cost_krw"] == EXPECT_TOTAL

    def test_world_a_mer(self, world_a):
        assert abs(world_a["computed"]["mer"] - EXPECT_MER) <= 0.05

    # ── ★핵심: 채널별 교차 동치 (독립 경로, 동일 raw) ──
    def test_ad_channels_equivalent(self, world_a, world_b):
        """World A ad_cost_by_channel == World B by_channel (광고 3매체)."""
        a = world_a["computed"]["ad_cost_by_channel"]
        b = world_b["by_channel"]
        for c in AD_CHANNELS:
            assert a[c] == b[c] == EXPECT_CHANNEL[c], (
                f"{c}: World A={a[c]:,} World B={b[c]:,} expect={EXPECT_CHANNEL[c]:,}"
            )

    def test_msg_channels_equivalent(self, world_a, world_b):
        """World A msg_cost_by_channel == World B by_channel (메시징 2매체, C6.3 분리)."""
        a = world_a["computed"]["msg_cost_by_channel"]
        b = world_b["by_channel"]
        for c in MSG_CHANNELS:
            assert a[c] == b[c] == EXPECT_CHANNEL[c], (
                f"{c}: World A={a[c]:,} World B={b[c]:,} expect={EXPECT_CHANNEL[c]:,}"
            )

    def test_total_equivalent_both_worlds(self, world_a, world_b):
        """양 세계 총 마케팅비 합이 동일 (피봇 후 대시보드 정답 불변의 토대)."""
        assert world_a["computed"]["total_marketing_cost_krw"] == world_b["total_cost"]


# ════════════════════════════════════════════════════════════════════════
#  B. 계획 결정 근거 invariant
# ════════════════════════════════════════════════════════════════════════
def _modules_importing(token: str, search_dir: Path, exclude_stem: str) -> set[str]:
    """search_dir 하위 .py 중 `token` 을 *import* 하는 모듈 stem 집합 (문자열 언급 제외)."""
    pat = re.compile(rf"(?:from|import)\s+[\w.]*{re.escape(token)}\b")
    found: set[str] = set()
    for p in search_dir.rglob("*.py"):
        if p.stem == exclude_stem:
            continue
        if pat.search(p.read_text(encoding="utf-8")):
            found.add(p.stem)
    return found


class TestPivotPlanInvariants:

    # test_format_normalizer_is_dormant 제거 (A-5.3, 2026-06-18): format_normalizer 폐기 완료
    # (canonical_translator 대체). dormant tripwire 명제 소멸 → 테스트 제거.

    def test_ad_cost_helper_consumer_set(self):
        """P3 진행 추적: ad_cost_helper 소비처 (전환할수록 줄어듦 → 0이면 A4 제거 가능).

        A3 P3 (2026-06-17): 5 tool 전부 canonical 전환 완료 → 소비처 **0**.
        ✅ ad_cost_total·roas_overall·cac_overall·promotion_roas·channel_cac_compare.
        → ad_cost_helper는 이제 tool import 0 = **A4에서 폐기 안전**(H1/H2 단위테스트만 직접 참조).
        """
        importers = _modules_importing("ad_cost_helper", TOOLS, exclude_stem="ad_cost_helper")
        expected: set[str] = set()      # 전부 canonical 전환 — A4 ad_cost_helper 폐기 가능
        assert importers == expected, (
            f"ad_cost_helper 소비처 = {importers} (기대 0). 0이면 A4(폐기) 안전. "
            "0 아니면 미전환 tool 있음 — P3 마저."
        )

    def test_workspace_layer_is_pre_pivot_tripwire(self):
        """P1 tripwire: 현 Workspace Layer == (raw, normalized, computed) — 피봇 P1 rename 완료.

        ★피봇 P1 에서 'cleaned' → 'normalized' 로 바꾸는 순간 이 테스트가 *의도적으로* 빨강.
        그때: 본 assert 를 ("raw","normalized","computed") 로 갱신 + 계획서 §14 반영 확인.
        """
        from app.workspace.base import Layer
        assert typing.get_args(Layer) == ("raw", "normalized", "computed", "blended"), (
            "Workspace Layer 변경 감지 — 피봇 P1(normalized 신설)이 시작된 것으로 보임. "
            "계획서 §14 와 정합 확인 후 본 tripwire 갱신."
        )

    def test_tool_catalog_count_baseline(self):
        """tool catalog 수 baseline (임팩트맵 분모).

        92 → 93: P2 격리 canonical_translator 신설(2026-06-16).
        93 → 92: A-5.3 format_normalizer.yaml 폐기(2026-06-18, canonical_translator 대체).
        잔여 REPLACE(channel_attribution·grade·utm·kst normalizer) 폐기는 P5 dimension 트랙.
        """
        yamls = [p for p in CATALOG.rglob("*.yaml") if p.name != "_schema.yaml"]
        assert len(yamls) == 92, (
            f"tool catalog 수 {len(yamls)} != 92 — 계획서 임팩트맵 분모 재산정 필요 "
            "(A-5.3 format_normalizer 폐기 반영 / P5 dimension normalizer 폐기 시 갱신)."
        )
