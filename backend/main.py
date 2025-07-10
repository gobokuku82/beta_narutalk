from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path
import os

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title="NaruTalk AI 챗봇",
    description="랭그래프를 활용한 AI 챗봇 시스템",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서만 사용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(api_router, prefix="/api/v1")

# 프론트엔드 디렉토리 경로 설정
frontend_dir = Path(__file__).parent.parent / "frontend"
if not frontend_dir.exists():
    frontend_dir = Path("../frontend")

# 정적 파일 서빙 (프론트엔드)
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

# 개별 파일 서빙 (CSS/JS 파일을 위한 직접 경로)
@app.get("/style.css")
async def get_style_css():
    """CSS 파일 서빙"""
    css_file = frontend_dir / "style.css"
    if css_file.exists():
        return FileResponse(css_file, media_type="text/css")
    raise HTTPException(status_code=404, detail="CSS file not found")

@app.get("/script.js")
async def get_script_js():
    """JS 파일 서빙"""
    js_file = frontend_dir / "script.js"
    if js_file.exists():
        return FileResponse(js_file, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="JS file not found")

@app.get("/", response_class=HTMLResponse)
async def root():
    """메인 페이지"""
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="""
    <html>
        <head>
            <title>NaruTalk AI 챗봇</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; margin: 50px; }
                .container { max-width: 600px; margin: 0 auto; }
                .status { padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>NaruTalk AI 챗봇</h1>
                <div class="status">
                    <p>시스템을 준비 중입니다...</p>
                    <p>프론트엔드 파일을 찾을 수 없습니다.</p>
                    <p>API 문서: <a href="/docs">/docs</a></p>
                    <p>헬스 체크: <a href="/health">/health</a></p>
                </div>
            </div>
        </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "ok", "message": "NaruTalk AI 챗봇이 정상 작동 중입니다."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 