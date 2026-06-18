"""C:LUMI #21 customer_grade_history collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import InternalRawCollectorBase


class CustomerGradeHistoryCollector(InternalRawCollectorBase):
    FILE_NO = 21
    PRODUCES_KEY = "grade_history_raw"
