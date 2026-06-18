"""LlmMlModel — POC v1+ 구현체. 현 LLM 인프라(llm_manager)로 분석 (ADR-028 §6).

LLM 분석 = ml_model 의 한 구현체 (별 layer 아님). O05 추천 첫 모범.
실패 시 안전 기본값 반환 (POC pipeline step hard-fail 회피).

Status: complete — Phase 1 M3 (2026-05-28). 실 LLM 호출 → 테스트는 client 주입 mock.
"""
from __future__ import annotations

from typing import Any, Optional

from app.core.logging import get_logger
from app.dream_agent.llm_manager.client import LLMClient, get_llm_client
from app.ml_models.base import (
    AiAxesResult,
    FatigueItem,
    FatigueResult,
    KeywordItem,
    KeywordsResult,
    MlModel,
    RecommendationItem,
    RecommendationResult,
    SentimentResult,
)

logger = get_logger(__name__)

_MAX_ITEMS = 80  # 프롬프트 폭주 방지


class LlmMlModel(MlModel):
    """LLM 기반 추론. client 주입 (기본 = analysis layer)."""

    def __init__(self, client: Optional[LLMClient] = None):
        self.llm = client or get_llm_client("analysis")

    async def _json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        return await self.llm.generate_json(prompt, schema=schema)

    async def analyze_sentiment(self, texts, *, client) -> SentimentResult:
        sample = list(texts)[:_MAX_ITEMS]
        try:
            data = await self._json(
                "다음 리뷰들의 감성을 분류해 positive·neutral·negative 각 개수를 세라.\n"
                + "\n".join(f"- {t}" for t in sample),
                {"positive": "int", "neutral": "int", "negative": "int"},
            )
            return SentimentResult.model_validate(data)
        except Exception as e:  # noqa: BLE001
            logger.error("LlmMlModel.analyze_sentiment 실패 → 기본값", error=str(e))
            return SentimentResult()

    async def extract_keywords(self, texts, *, client, top_n=10) -> KeywordsResult:
        sample = list(texts)[:_MAX_ITEMS]
        try:
            data = await self._json(
                f"다음 텍스트에서 상위 {top_n} 키워드와 빈도를 추출하라.\n"
                + "\n".join(f"- {t}" for t in sample),
                {"keywords": [{"keyword": "str", "count": "int"}]},
            )
            kr = KeywordsResult.model_validate(data)
            kr.keywords = kr.keywords[:top_n]
            return kr
        except Exception as e:  # noqa: BLE001
            logger.error("LlmMlModel.extract_keywords 실패 → 빈 결과", error=str(e))
            return KeywordsResult()

    async def score_ai_axes(self, creatives, *, client) -> AiAxesResult:
        sample = list(creatives)[:_MAX_ITEMS]
        try:
            data = await self._json(
                "다음 광고 소재들의 평균 점수를 5축(ai_sales·ai_short·ai_clear·ai_visual·"
                "ai_benefit) 각 0~100 으로 평가하라.\n" + str(sample),
                {k: "float 0~100" for k in
                 ["ai_sales", "ai_short", "ai_clear", "ai_visual", "ai_benefit"]},
            )
            return AiAxesResult.model_validate(data)
        except Exception as e:  # noqa: BLE001
            logger.error("LlmMlModel.score_ai_axes 실패 → 기본값", error=str(e))
            return AiAxesResult()

    async def diagnose_fatigue(self, creatives, *, client) -> FatigueResult:
        sample = list(creatives)[:_MAX_ITEMS]
        try:
            data = await self._json(
                "다음 소재들의 피로(반복 노출 성과 저하)를 진단해 creative_id·is_fatigue·"
                "score(0~1) 를 매겨라.\n" + str(sample),
                {"items": [{"creative_id": "str", "is_fatigue": "bool", "score": "float"}]},
            )
            return FatigueResult.model_validate(data)
        except Exception as e:  # noqa: BLE001
            logger.error("LlmMlModel.diagnose_fatigue 실패 → 기본값", error=str(e))
            return FatigueResult(items=[
                FatigueItem(creative_id=str(c.get("creative_id") or i), is_fatigue=False)
                for i, c in enumerate(sample)
            ])

    async def generate_recommendation(self, context, *, client) -> RecommendationResult:
        try:
            data = await self._json(
                "다음 광고 성과 요약을 보고 개선 추천을 title·detail·priority(high/medium/low) "
                "목록으로 제시하라.\n" + str(context),
                {"recommendations": [{"title": "str", "detail": "str", "priority": "str"}]},
            )
            return RecommendationResult.model_validate(data)
        except Exception as e:  # noqa: BLE001
            logger.error("LlmMlModel.generate_recommendation 실패 → 빈 결과", error=str(e))
            return RecommendationResult(recommendations=[
                RecommendationItem(title="추천 생성 실패", detail=str(e), priority="low")
            ])


__all__ = ["LlmMlModel"]
