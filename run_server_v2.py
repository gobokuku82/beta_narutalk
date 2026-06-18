"""ADALLPIN v2 서버 실행 (Sandbox).

기존 run_server.py는 그대로 두고, 이 스크립트는 api_v2/를 port 8001로 띄움.
Phase 3 Gate 통과 후 run_server.py로 rename + api_v2 → api 이관.

사용법:
    uv run python run_server_v2.py
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

V2_PORT = settings.PORT + 1  # 8000 → 8001

if __name__ == "__main__":
    print(f"\n  ADALLPIN v2 server starting at http://localhost:{V2_PORT}")
    print(f"  (Sandbox — 기존 api/ 와 동시 실행 가능)")
    print(f"  Backend path: {backend_path}\n")
    uvicorn.run(
        "api_v2.main:app",
        host=settings.HOST,
        port=V2_PORT,
        reload=settings.DEBUG,
        reload_dirs=[str(backend_path)] if settings.DEBUG else None,
        log_level="debug",
    )
