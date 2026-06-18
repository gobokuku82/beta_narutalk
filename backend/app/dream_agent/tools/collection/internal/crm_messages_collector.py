"""C:LUMI #18 crm_messages collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import InternalRawCollectorBase


class CrmMessagesCollector(InternalRawCollectorBase):
    FILE_NO = 18
    PRODUCES_KEY = "crm_raw"
