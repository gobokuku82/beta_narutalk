"""C:LUMI #16 kakao_bizmessage collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import ExternalRawCollectorBase


class KakaoBizmessageCollector(ExternalRawCollectorBase):
    FILE_NO = 16
    PRODUCES_KEY = "kakao_raw"
