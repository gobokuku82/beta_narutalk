"""C:LUMI #4 naver_searchad collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import ExternalRawCollectorBase


class NaverSearchadCollector(ExternalRawCollectorBase):
    FILE_NO = 4
    PRODUCES_KEY = "naver_sa_raw"
