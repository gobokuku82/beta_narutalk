"""Phase 3 — 렌더 산출물 다운로드 (엔드포인트 + dispatcher url) (2026-06-09).

사용자 개념: 생성(만들어줘) + 다운로드(파일경로+링크). 후자 = GET /api/files/download +
응답 attachment.url. 보안: data/{client}/outputs/ 한정, raw/cleaned·traversal 차단.

D-1 outputs/ 파일 서빙 (200 + 내용)
D-2 traversal·非outputs·없는 파일 차단 (403/403/404)
D-3 dispatcher 가 file attachment 에 다운로드 url 부여
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dream_agent.response.responder import build_display_payload
from app.dream_agent.schemas.execution_result import ExecutionResult, TodoResult, TodoStatus
from app.dream_agent.schemas.structured_query import StructuredQuery


def _client(monkeypatch, data_root: Path) -> TestClient:
    from api_v2.routes import files as files_mod

    monkeypatch.setattr(files_mod, "_DATA", Path(data_root).resolve())
    app = FastAPI()
    app.include_router(files_mod.router)
    return TestClient(app)


# ── D-1: outputs 파일 서빙 ──

def test_d1_serves_outputs_file(tmp_path, monkeypatch):
    out = tmp_path / "clumi" / "outputs"
    out.mkdir(parents=True)
    (out / "report.pdf").write_bytes(b"%PDF-1.4 hello")

    c = _client(monkeypatch, tmp_path)
    r = c.get("/api/files/download", params={"p": "clumi/outputs/report.pdf"})
    assert r.status_code == 200
    assert r.content.startswith(b"%PDF")


# ── D-2: 보안 차단 (traversal / 非outputs / 없음) ──

def test_d2_blocks_traversal_nonoutputs_missing(tmp_path, monkeypatch):
    (tmp_path / "clumi" / "raw").mkdir(parents=True)
    (tmp_path / "clumi" / "raw" / "secret.csv").write_text("x")
    c = _client(monkeypatch, tmp_path)

    # 非outputs(raw) → 403 (파일 있어도 차단)
    assert c.get("/api/files/download", params={"p": "clumi/raw/secret.csv"}).status_code == 403
    # traversal → 403
    assert c.get("/api/files/download", params={"p": "../../etc/passwd"}).status_code == 403
    # outputs 인데 없는 파일 → 404
    assert c.get("/api/files/download", params={"p": "clumi/outputs/none.pdf"}).status_code == 404


# ── D-3: dispatcher 가 다운로드 url 부여 ──

def test_d3_dispatcher_sets_download_url():
    er = ExecutionResult(todos={"t1": TodoResult(
        todo_id="t1", task_type="x", tool="pdf_renderer", status=TodoStatus.COMPLETED,
        data={"pdf_file_path": "/abs/repo/data/clumi/outputs/report_x.pdf"},
        started_at=0.0, ended_at=0.0, duration_ms=0.0,
    )})
    sq = StructuredQuery.model_validate(
        {"targets": {}, "goal": {"type": "report", "output_format": "pdf"}, "meta": {}}
    )

    payload = build_display_payload(sq, er)
    pdf = next(a for a in payload.attachments if a.kind == "pdf")
    assert pdf.url and pdf.url.startswith("/api/files/download?p=")
    assert "clumi/outputs/report_x.pdf" in pdf.url, "data/ 하위 상대경로가 다운로드 링크에 포함"
