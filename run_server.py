"""DreamAgent 서버 실행.

api.main:app 을 port 8001 로 띄운다 (프론트 기본 연결 = 127.0.0.1:8001).

사용법:
    uv run python run_server.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Windows PowerShell 버퍼링 방지
os.environ.setdefault("PYTHONUNBUFFERED", "1")
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

from app.core.config import settings

SERVER_PORT = settings.PORT + 1  # 8001 (프론트 기본 연결 포트)

if __name__ == "__main__":
    print(f"\n  {settings.APP_NAME} server starting at http://localhost:{SERVER_PORT}\n")
    print(f"  Backend path: {backend_path}\n")
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=SERVER_PORT,
        reload=settings.DEBUG,
        reload_dirs=[str(backend_path)] if settings.DEBUG else None,
        log_level="debug",
    )
