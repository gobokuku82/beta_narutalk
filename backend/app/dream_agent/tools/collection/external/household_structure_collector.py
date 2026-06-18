"""C:LUMI #19 household_structure collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import ExternalRawCollectorBase


class HouseholdStructureCollector(ExternalRawCollectorBase):
    FILE_NO = 19
    PRODUCES_KEY = "household_raw"
