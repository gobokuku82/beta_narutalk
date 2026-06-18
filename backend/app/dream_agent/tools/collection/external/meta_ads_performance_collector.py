"""C:LUMI #1 meta_ads_performance collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import ExternalRawCollectorBase


class MetaAdsPerformanceCollector(ExternalRawCollectorBase):
    FILE_NO = 1
    PRODUCES_KEY = "meta_ads_raw"
