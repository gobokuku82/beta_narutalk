"""MockMlModel — POC v1 구현체. `data/ml_mock/{domain}/{client}.json` fixture 반환.

ADR-028 §5: B2b ml_mock = ML 결과 자리의 mock. MVP+ 시 ProductionMlModel 로 swap.
fixture 부재 시 입력 기반 trivial fallback (테스트·신규 client 안전).

Status: complete — Phase 1 M3 (2026-05-28).
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Optional

from app.core.logging import get_logger
from app.ml_models.base import (
    AiAxesResult,
    FatigueItem,
    FatigueResult,
    KeywordItem,
    KeywordsResult,
    MlModel,
    RecommendationResult,
    SentimentResult,
)

logger = get_logger(__name__)

# backend/app/ml_models/mock.py → parents: ml_models(0) app(1) backend(2) repo(3)
_REPO_ROOT = Path(__file__).resolve().parents[3]


class MockMlModel(MlModel):
    """fixture 기반 mock 추론. fixtures_dir 기본 = data/ml_mock/."""

    def __init__(self, fixtures_dir: Optional[Path] = None):
        self.fixtures_dir = fixtures_dir or (_REPO_ROOT / "data" / "ml_mock")

    def _load(self, domain: str, client: str) -> Optional[dict[str, Any]]:
        path = self.fixtures_dir / domain / f"{client}.json"
        if not path.exists():
            logger.info("ml_mock fixture 부재 → fallback", domain=domain, client=client,
                        path=str(path))
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    async def analyze_sentiment(self, texts, *, client) -> SentimentResult:
        data = self._load("sentiment", client)
        if data is not None:
            return SentimentResult.model_validate(data)
        # fallback: 60/25/15 결정적 분배
        n = len(texts)
        pos = round(n * 0.6)
        neg = round(n * 0.15)
        return SentimentResult(positive=pos, negative=neg, neutral=n - pos - neg)

    async def extract_keywords(self, texts, *, client, top_n=10) -> KeywordsResult:
        data = self._load("keywords", client)
        if data is not None:
            kr = KeywordsResult.model_validate(data)
            kr.keywords = kr.keywords[:top_n]
            return kr
        # fallback: 단순 공백 토큰 빈도
        counter: Counter[str] = Counter()
        for t in texts:
            for tok in str(t).split():
                if len(tok) >= 2:
                    counter[tok] += 1
        return KeywordsResult(
            keywords=[KeywordItem(keyword=k, count=c) for k, c in counter.most_common(top_n)]
        )

    async def score_ai_axes(self, creatives, *, client) -> AiAxesResult:
        data = self._load("ai_axes", client)
        if data is not None:
            return AiAxesResult.model_validate(data)
        return AiAxesResult(ai_sales=50, ai_short=50, ai_clear=50, ai_visual=50, ai_benefit=50)

    async def diagnose_fatigue(self, creatives, *, client) -> FatigueResult:
        data = self._load("fatigue", client)
        if data is not None:
            return FatigueResult.model_validate(data)
        items = [
            FatigueItem(
                creative_id=str(c.get("creative_id") or c.get("id") or i),
                is_fatigue=bool(c.get("is_fatigue", False)),
                score=float(c.get("fatigue_score", 0.0)),
            )
            for i, c in enumerate(creatives)
        ]
        return FatigueResult(items=items)

    async def generate_recommendation(self, context, *, client) -> RecommendationResult:
        data = self._load("recommendations", client)
        if data is not None:
            return RecommendationResult.model_validate(data)
        return RecommendationResult(recommendations=[])


__all__ = ["MockMlModel"]
