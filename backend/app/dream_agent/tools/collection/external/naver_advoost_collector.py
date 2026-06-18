"""C:LUMI #15 naver_advoost collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import ExternalRawCollectorBase


class NaverAdvoostCollector(ExternalRawCollectorBase):
    FILE_NO = 15
    PRODUCES_KEY = "naver_advoost_raw"
