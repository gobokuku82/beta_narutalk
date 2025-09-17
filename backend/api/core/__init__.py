"""
Core module for API configuration and dependencies
"""

from .config import settings
from .dependencies import (
    get_supervisor_service,
    get_cache_manager,
    get_database_client
)

__all__ = [
    "settings",
    "get_supervisor_service",
    "get_cache_manager",
    "get_database_client"
]