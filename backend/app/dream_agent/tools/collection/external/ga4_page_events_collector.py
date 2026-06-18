"""C:LUMI #8 ga4_page_events collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import ExternalRawCollectorBase


class Ga4PageEventsCollector(ExternalRawCollectorBase):
    FILE_NO = 8
    PRODUCES_KEY = "clumi_ga4_page_raw"
