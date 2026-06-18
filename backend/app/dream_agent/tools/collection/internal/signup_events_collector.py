"""C:LUMI #9 signup_events collector — thin wrapper."""
from __future__ import annotations
from app.dream_agent.tools.collection._base import InternalRawCollectorBase


class SignupEventsCollector(InternalRawCollectorBase):
    FILE_NO = 9
    PRODUCES_KEY = "signup_raw"
