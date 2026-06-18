"""ML 추론 어댑터 ABC + 결과 모델 (ADR-027 §3 + ADR-028 §6).

5 주체 중 ml_model — Tool 이 ABC 타입으로 의존, 구현체(Mock·Llm·Production) swap.
Tool = production 영구 / ml_model 구현체만 교체 (DI 1 줄).

ML 영역 5 (ADR-028 §5·§6):
    sentiment   — 리뷰 감성 분포 (C08)
    keywords    — 키워드 추출 랭킹 (C12)
    ai_axes     — 소재 AI 5축 점수 (C11)
    fatigue     — 소재 피로 진단 (K21)
    recommendation — AI 추천 (O05) — LlmMlModel 첫 모범

Status: complete — Phase 1 M3 (2026-05-28). 구현체: mock.py / llm.py. Production = MVP+.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel, Field

Sentiment = Literal["positive", "neutral", "negative"]


# ─────────────────────────────────────────────────────────────────
# 결과 모델 (ml_model 산출 — Tool 이 그대로 output schema 로 흡수 가능)
# ─────────────────────────────────────────────────────────────────


class SentimentResult(BaseModel):
    """감성 분포 (C08 도넛)."""

    positive: int = 0
    neutral: int = 0
    negative: int = 0

    @property
    def total(self) -> int:
        return self.positive + self.neutral + self.negative

    def distribution(self) -> dict[str, float]:
        t = self.total or 1
        return {
            "positive": round(self.positive / t, 4),
            "neutral": round(self.neutral / t, 4),
            "negative": round(self.negative / t, 4),
        }


class KeywordItem(BaseModel):
    keyword: str
    count: int


class KeywordsResult(BaseModel):
    """키워드 랭킹 (C12)."""

    keywords: list[KeywordItem] = Field(default_factory=list)


class AiAxesResult(BaseModel):
    """소재 AI 5축 점수 0~100 (C11 radar). 축명 = normalizers/{client}.yaml 표준."""

    ai_sales: float = 0.0
    ai_short: float = 0.0
    ai_clear: float = 0.0
    ai_visual: float = 0.0
    ai_benefit: float = 0.0

    def as_axes(self) -> dict[str, float]:
        return self.model_dump()


class FatigueItem(BaseModel):
    creative_id: str
    is_fatigue: bool
    score: float = 0.0


class FatigueResult(BaseModel):
    """소재 피로 진단 (K21)."""

    items: list[FatigueItem] = Field(default_factory=list)

    @property
    def fatigue_count(self) -> int:
        return sum(1 for i in self.items if i.is_fatigue)

    @property
    def total(self) -> int:
        return len(self.items)


class RecommendationItem(BaseModel):
    title: str
    detail: str = ""
    priority: Literal["high", "medium", "low"] = "medium"


class RecommendationResult(BaseModel):
    """AI 추천 (O05 — 베타 0.001). LlmMlModel 이 생성."""

    recommendations: list[RecommendationItem] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────
# ABC — 영구 (POC v1 부터 production 인터페이스)
# ─────────────────────────────────────────────────────────────────


class MlModel(ABC):
    """ML 추론 추상 인터페이스. 구현체 swap (Mock·Llm·Production)."""

    @abstractmethod
    async def analyze_sentiment(
        self, texts: list[str], *, client: str
    ) -> SentimentResult: ...

    @abstractmethod
    async def extract_keywords(
        self, texts: list[str], *, client: str, top_n: int = 10
    ) -> KeywordsResult: ...

    @abstractmethod
    async def score_ai_axes(
        self, creatives: list[dict[str, Any]], *, client: str
    ) -> AiAxesResult: ...

    @abstractmethod
    async def diagnose_fatigue(
        self, creatives: list[dict[str, Any]], *, client: str
    ) -> FatigueResult: ...

    @abstractmethod
    async def generate_recommendation(
        self, context: dict[str, Any], *, client: str
    ) -> RecommendationResult: ...


__all__ = [
    "Sentiment",
    "SentimentResult",
    "KeywordItem",
    "KeywordsResult",
    "AiAxesResult",
    "FatigueItem",
    "FatigueResult",
    "RecommendationItem",
    "RecommendationResult",
    "MlModel",
]
