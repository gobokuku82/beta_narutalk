"""파일 다운로드 — 렌더 산출물(pdf/pptx/...) 서빙 (Phase3 download, 2026-06-09).

렌더 tool 이 생성한 산출물은 data/{client}/outputs/ 에 저장된다. 본 엔드포인트가
다운로드 링크(생성 ↔ 다운로드 2단계의 후자)를 제공한다.
보안: data/ 하위 + outputs/ 안의 파일만 서빙. 경로 traversal 차단.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/files", tags=["Files"])

# files.py → routes(0) api_v2(1) backend(2) repo(3) ; data = repo/data
_DATA = (Path(__file__).resolve().parents[3] / "data").resolve()


@router.get("/download", summary="렌더 산출물 다운로드 (data/{client}/outputs/ 한정)")
def download(
    p: str = Query(..., description="data/ 하위 상대경로 (예: clumi/outputs/report_x.pdf)"),
) -> FileResponse:
    target = (_DATA / p).resolve()
    # 보안 1: data/ 범위 안 (traversal 차단)
    try:
        rel = target.relative_to(_DATA)
    except ValueError:
        raise HTTPException(status_code=403, detail="경로 범위 밖")
    # 보안 2: outputs/ 산출물만 (raw/cleaned/computed 등 차단)
    if "outputs" not in rel.parts:
        raise HTTPException(status_code=403, detail="outputs 산출물만 다운로드 가능")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="파일 없음")
    return FileResponse(str(target), filename=target.name)
