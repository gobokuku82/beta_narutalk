"""C:LUMI #3 meta_instagram_inapp collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import ExternalRawCollectorBase


class MetaInstagramInappCollector(ExternalRawCollectorBase):
    FILE_NO = 3
    PRODUCES_KEY = "meta_inapp_raw"
