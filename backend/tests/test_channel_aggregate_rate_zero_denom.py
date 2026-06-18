# -*- coding: utf-8 -*-
"""channel_aggregate._rate 0분모 규약 — CPA/CPC(비용지표)는 None, ctr/cvr/roas는 0.0 (2026-06-18).

검증 wb7456v44: 0분모(전환=0·클릭=0)를 0.0으로 반환하면 '낮을수록 좋은' CPA/CPC가 '0=최고'로 위장 →
순위·target_cpa 비교 오독(객관적 버그). canonical_translator의 'X if denom else None' 규약과 정합화.
현 2026-04 실데이터엔 전 채널 전환>0이라 미발현(잠재버그)이나 신규 client/기간 대비 선제 수정.
"""
from __future__ import annotations

from app.dream_agent.tools.metrics.channel_aggregate import _rate


def test_cost_metric_zero_denom_returns_none():
    """cpa/cpc 호출 패턴(zero=None): 분모0이면 None (0.0 위장 아님)."""
    assert _rate(9_235_826, 0, zero=None) is None      # 비용 있고 전환 0 → 정의불가
    assert _rate(0, 0, zero=None) is None
    # 정상 분모는 그대로 계산
    assert _rate(9_235_826, 302, zero=None) == 30_582.21


def test_ratio_metric_zero_denom_stays_zero():
    """ctr/cvr/roas(기본 zero=0.0): 분모0이면 0.0 (높을수록 좋음 — 0은 '데이터 없음'이지 위장 아님)."""
    assert _rate(0, 0) == 0.0                            # ctr/cvr/roas 기본
    assert _rate(10, 0, pct=True) == 0.0
    assert _rate(50, 1000, pct=True) == 5.0             # 정상 계산 불변
