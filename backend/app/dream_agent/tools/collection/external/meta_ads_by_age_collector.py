"""C:LUMI #2 meta_ads_by_age collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import ExternalRawCollectorBase


class MetaAdsByAgeCollector(ExternalRawCollectorBase):
    FILE_NO = 2
    PRODUCES_KEY = "meta_ads_by_age_raw"
