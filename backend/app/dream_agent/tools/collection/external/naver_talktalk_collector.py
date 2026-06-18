"""C:LUMI #17 naver_talktalk collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import ExternalRawCollectorBase


class NaverTalktalkCollector(ExternalRawCollectorBase):
    FILE_NO = 17
    PRODUCES_KEY = "talktalk_raw"
