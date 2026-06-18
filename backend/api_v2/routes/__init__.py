"""api_v2 라우터 모음."""

from api_v2.routes.admin import router as admin_router
from api_v2.routes.canonical import router as canonical_router
from api_v2.routes.conversations import router as conversations_router
from api_v2.routes.dashboard1 import router as dashboard1_router
from api_v2.routes.data_console import router as data_console_router
from api_v2.routes.system_console import router as system_console_router
from api_v2.routes.files import router as files_router
from api_v2.routes.health import router as health_router
from api_v2.routes.pipelines import router as pipelines_router

__all__ = [
    "admin_router",
    "canonical_router",
    "conversations_router",
    "dashboard1_router",
    "data_console_router",
    "system_console_router",
    "files_router",
    "health_router",
    "pipelines_router",
]
