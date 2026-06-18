"""C:LUMI #6 customers collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import InternalRawCollectorBase


class CustomersCollector(InternalRawCollectorBase):
    FILE_NO = 6
    PRODUCES_KEY = "customers_raw"
