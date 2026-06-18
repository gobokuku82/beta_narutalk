"""C:LUMI #12 category_sales collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import InternalRawCollectorBase


class CategorySalesCollector(InternalRawCollectorBase):
    FILE_NO = 12
    PRODUCES_KEY = "category_sales_raw"
