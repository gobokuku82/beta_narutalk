"""C:LUMI #5 orders collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import InternalRawCollectorBase


class OrdersCollector(InternalRawCollectorBase):
    FILE_NO = 5
    PRODUCES_KEY = "orders_raw"
