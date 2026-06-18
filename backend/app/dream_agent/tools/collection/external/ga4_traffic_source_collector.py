"""C:LUMI #7 ga4_traffic_source collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import ExternalRawCollectorBase


class Ga4TrafficSourceCollector(ExternalRawCollectorBase):
    FILE_NO = 7
    PRODUCES_KEY = "clumi_ga4_traffic_raw"
