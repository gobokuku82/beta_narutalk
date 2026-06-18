"""Sentiment Analyzer — 감성 분석.

POC 전략: format_normalizer가 이미 정규화한 sentiment 라벨이 있으면 그걸 사용,
없으면 간단한 규칙 기반 폴백. MVP에서 KoBERT 교체 예정.

입력: cleaned_texts
출력: sentiment_distribution (0~100 %), sentiment_items
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.helpers import find_in_previous

logger = get_logger(__name__)

POS_KW = ["좋", "만족", "추천", "최고", "훌륭", "촉촉", "가성비", "재구매", "효과"]
NEG_KW = ["별로", "실망", "안 좋", "후회", "불만", "최악", "별점", "자극", "트러블"]


class SentimentAnalyzer(BaseTool):
    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        texts = find_in_previous(context.previous_results, "cleaned_texts") or []

        items: list[dict] = []
        pos = neu = neg = 0

        for t in texts:
            label = t.get("sentiment") or self._classify(t["cleaned_text"])
            if label not in ("positive", "neutral", "negative"):
                label = "neutral"

            items.append({
                "text_id": t["text_id"],
                "text": t["cleaned_text"],
                "sentiment": label,
                "confidence": None,
            })

            if label == "positive":
                pos += 1
            elif label == "negative":
                neg += 1
            else:
                neu += 1

        total = len(items) or 1
        distribution = {
            "positive": round(pos / total * 100, 1),
            "neutral": round(neu / total * 100, 1),
            "negative": round(neg / total * 100, 1),
            "total_count": len(items),
        }

        logger.info("sentiment_analyzer completed", **distribution)

        return {
            "sentiment_distribution": distribution,
            "sentiment_items": items,
            "total_count": len(items),
        }

    @staticmethod
    def _classify(text: str) -> str:
        p = sum(1 for k in POS_KW if k in text)
        n = sum(1 for k in NEG_KW if k in text)
        if p > n:
            return "positive"
        if n > p:
            return "negative"
        return "neutral"
