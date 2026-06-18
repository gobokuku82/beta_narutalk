"""C:LUMI #20 ad_change_history collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import ExternalRawCollectorBase


class AdChangeHistoryCollector(ExternalRawCollectorBase):
    FILE_NO = 20
    PRODUCES_KEY = "ad_change_raw"
