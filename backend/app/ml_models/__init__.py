"""ml_models — ML 추론 어댑터 (ADR-027 5 주체 중 ml_model).

Tool 이 MlModel ABC 타입으로 의존 → 구현체 swap (DI):
    poc      → MockMlModel       (data/ml_mock/* fixture)
    poc_llm  → LlmMlModel        (현 LLM 인프라)
    production → ProductionMlModel (MVP+ — 미구현)

진입점:
    from app.ml_models import build_ml_model, get_default_ml_model, MlModel
"""
from __future__ import annotations

import os
from typing import Optional

from app.ml_models.base import (
    AiAxesResult,
    FatigueResult,
    KeywordsResult,
    MlModel,
    RecommendationResult,
    SentimentResult,
)
from app.ml_models.llm import LlmMlModel
from app.ml_models.mock import MockMlModel


def build_ml_model(env: str = "poc") -> MlModel:
    """env 별 ml_model 구현체 (ADR-027 §3.2 DI factory)."""
    if env == "poc":
        return MockMlModel()
    if env == "poc_llm":
        return LlmMlModel()
    if env == "production":
        raise NotImplementedError(
            "ProductionMlModel = MVP+ 신설 예정 (ADR-027 §3.2). 현재 poc/poc_llm 만."
        )
    raise ValueError(f"unknown ml_model env: {env!r} (poc|poc_llm|production)")


_default: Optional[MlModel] = None


def get_default_ml_model() -> MlModel:
    """전역 default — env var OCTOR_ML_ENV (기본 poc=Mock)."""
    global _default
    if _default is None:
        _default = build_ml_model(os.getenv("OCTOR_ML_ENV", "poc"))
    return _default


def set_ml_model(model: MlModel) -> None:
    """테스트/DI override."""
    global _default
    _default = model


def reset_ml_model() -> None:
    global _default
    _default = None


__all__ = [
    "MlModel",
    "MockMlModel",
    "LlmMlModel",
    "build_ml_model",
    "get_default_ml_model",
    "set_ml_model",
    "reset_ml_model",
    "SentimentResult",
    "KeywordsResult",
    "AiAxesResult",
    "FatigueResult",
    "RecommendationResult",
]
