"""C:LUMI #13 naver_interest_alert collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import ExternalRawCollectorBase


class NaverInterestAlertCollector(ExternalRawCollectorBase):
    FILE_NO = 13
    PRODUCES_KEY = "naver_alert_raw"
