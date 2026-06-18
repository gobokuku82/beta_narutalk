"""C:LUMI #10 customer_rfm collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import InternalRawCollectorBase


class CustomerRfmCollector(InternalRawCollectorBase):
    FILE_NO = 10
    PRODUCES_KEY = "rfm_raw"
