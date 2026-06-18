# -*- coding: utf-8 -*-
"""Phase 1 M3 — ml_model adapter (ADR-027 §3 + ADR-028 §6) 검증.

  L1 factory swap  — poc=Mock / poc_llm=Llm / production=NotImplemented / unknown=ValueError
  L2 Mock fixture  — data/ml_mock/blooming.json 5 도메인 로드
  L3 Mock fallback — fixture 부재 시 입력 기반 안전 산출
  L4 Llm (mock client) — generate_json 주입 → result 모델 파싱 + 실패 fallback
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.ml_models import (
    LlmMlModel,
    MockMlModel,
    build_ml_model,
    get_default_ml_model,
    reset_ml_model,
    set_ml_model,
)
from app.ml_models.base import SentimentResult


# ─────────────────────────────────────────────────────────────────
# L1 — factory
# ─────────────────────────────────────────────────────────────────


def test_factory_swap():
    assert isinstance(build_ml_model("poc"), MockMlModel)
    assert isinstance(build_ml_model("poc_llm"), LlmMlModel)
    with pytest.raises(NotImplementedError):
        build_ml_model("production")
    with pytest.raises(ValueError):
        build_ml_model("nonsense")


def test_default_set_reset():
    reset_ml_model()
    assert isinstance(get_default_ml_model(), MockMlModel)
    sentinel = MockMlModel()
    set_ml_model(sentinel)
    assert get_default_ml_model() is sentinel
    reset_ml_model()


# ─────────────────────────────────────────────────────────────────
# L2 — Mock fixture 로드 (실 data/ml_mock/blooming.json)
# ─────────────────────────────────────────────────────────────────


async def test_mock_sentiment_fixture():
    r = await MockMlModel().analyze_sentiment(["x"], client="blooming")
    assert (r.positive, r.neutral, r.negative) == (412, 168, 95)
    assert r.total == 675
    assert r.distribution()["positive"] == round(412 / 675, 4)


async def test_mock_keywords_fixture_top_n():
    r = await MockMlModel().extract_keywords(["x"], client="blooming", top_n=3)
    assert len(r.keywords) == 3
    assert r.keywords[0].keyword == "수분"


async def test_mock_ai_axes_fixture():
    r = await MockMlModel().score_ai_axes([{}], client="blooming")
    assert r.ai_clear == 82.0
    assert set(r.as_axes()) == {"ai_sales", "ai_short", "ai_clear", "ai_visual", "ai_benefit"}


async def test_mock_fatigue_fixture_count():
    r = await MockMlModel().diagnose_fatigue([{}], client="blooming")
    assert r.total == 8
    assert r.fatigue_count == 3


async def test_mock_recommendation_fixture():
    r = await MockMlModel().generate_recommendation({}, client="blooming")
    assert len(r.recommendations) == 3
    assert r.recommendations[0].priority == "high"


# ─────────────────────────────────────────────────────────────────
# L3 — Mock fallback (fixture 부재)
# ─────────────────────────────────────────────────────────────────


async def test_mock_fallback_sentiment(tmp_path: Path):
    mock = MockMlModel(fixtures_dir=tmp_path)  # 빈 디렉토리 → fallback
    r = await mock.analyze_sentiment(["t"] * 100, client="ghost")
    assert r.positive == 60 and r.negative == 15 and r.neutral == 25


async def test_mock_fallback_keywords(tmp_path: Path):
    mock = MockMlModel(fixtures_dir=tmp_path)
    r = await mock.extract_keywords(["hello world", "hello there"], client="ghost", top_n=5)
    kw = {k.keyword: k.count for k in r.keywords}
    assert kw["hello"] == 2


# ─────────────────────────────────────────────────────────────────
# L4 — Llm (client 주입 mock, live 호출 X)
# ─────────────────────────────────────────────────────────────────


class _FakeLLM:
    def __init__(self, payload=None, raise_exc=False):
        self.payload = payload
        self.raise_exc = raise_exc

    async def generate_json(self, prompt, schema=None, **kw):
        if self.raise_exc:
            raise RuntimeError("llm down")
        return self.payload


async def test_llm_sentiment_parses_injected():
    llm = LlmMlModel(client=_FakeLLM({"positive": 7, "neutral": 2, "negative": 1}))
    r = await llm.analyze_sentiment(["a", "b"], client="clumi")
    assert isinstance(r, SentimentResult)
    assert r.positive == 7 and r.total == 10


async def test_llm_failure_falls_back():
    llm = LlmMlModel(client=_FakeLLM(raise_exc=True))
    r = await llm.analyze_sentiment(["a"], client="clumi")
    assert r.total == 0  # 안전 기본값
