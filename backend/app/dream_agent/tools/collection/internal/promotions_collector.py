"""C:LUMI #11 promotions collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import InternalRawCollectorBase


class PromotionsCollector(InternalRawCollectorBase):
    FILE_NO = 11
    PRODUCES_KEY = "promotions_raw"
