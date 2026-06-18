"""Dashboard1 Standalone — dashboard1_router 만 단독 서빙 (회귀 전용).

main.py 의 PostgreSQL lifespan (Checkpointer + LangGraph) 우회. dashboard1_router 만
단독으로 띄워 28 요소 정답값을 라이브 uvicorn 으로 검증.

실행:
    cd backend && uvicorn api_v2.dashboard1_standalone:app --host 127.0.0.1 --port 8765

Rename history (2026-05-27):
  clumi_standalone.py → dashboard1_standalone.py (path 가 회사 이름 박힘 정정)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_v2.routes.admin import router as admin_router
from api_v2.routes.dashboard1 import router as dashboard1_router

app = FastAPI(title="Dashboard1 Standalone (회귀)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(dashboard1_router)
app.include_router(admin_router)
