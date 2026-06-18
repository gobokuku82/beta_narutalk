"""C:LUMI #14 instagram_engagement collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import ExternalRawCollectorBase


class InstagramEngagementCollector(ExternalRawCollectorBase):
    FILE_NO = 14
    PRODUCES_KEY = "instagram_raw"
