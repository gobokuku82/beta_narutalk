"""PDF Renderer — 마크다운 보고서 → PDF (Phase3, 2026-06-09).

reportlab 내장 한국어 CID 폰트(HYSMyeongJo-Medium) 사용 — 폰트파일 불요.
출력 단계 tool(ToolCategory.OUTPUT). report_markdown 을 받아 PDF 파일 생성 → pdf_file_path 반환.
빈 입력(report_markdown 부재)은 data_insufficient (게이트 consumes=[report_markdown] 와 2겹).
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.helpers import find_in_previous

logger = get_logger(__name__)

# pdf_renderer.py → output(0) tools(1) dream_agent(2) app(3) backend(4) repo(5)
_REPO_ROOT = Path(__file__).resolve().parents[5]
_FONT = "HYSMyeongJo-Medium"  # reportlab 내장 한국어 CID 폰트


def _esc(s: str) -> str:
    """reportlab Paragraph(mini-HTML)용 XML 특수문자 이스케이프."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _render_pdf(markdown_text: str, out_path: Path) -> int:
    """마크다운을 PDF로 렌더 — 헤더(#/##)·불릿·굵게 기본 처리. flowable 수 반환."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    pdfmetrics.registerFont(UnicodeCIDFont(_FONT))
    body = ParagraphStyle("body", fontName=_FONT, fontSize=11, leading=17)
    h1 = ParagraphStyle("h1", fontName=_FONT, fontSize=18, leading=24, spaceBefore=8, spaceAfter=10)
    h2 = ParagraphStyle("h2", fontName=_FONT, fontSize=14, leading=20, spaceBefore=6, spaceAfter=8)

    flow: list = []
    for raw in markdown_text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flow.append(Spacer(1, 6))
            continue
        if line.startswith("## "):
            flow.append(Paragraph(_esc(line[3:]), h2))
        elif line.startswith("# "):
            flow.append(Paragraph(_esc(line[2:]), h1))
        else:
            text = re.sub(r"^\s*[-*]\s+", "• ", line)   # 불릿
            text = _esc(text)
            text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)  # 굵게
            flow.append(Paragraph(text, body))

    n = len(flow)  # build()가 flow 를 소비(pop)하므로 미리 카운트
    SimpleDocTemplate(str(out_path), pagesize=A4, title="분석 보고서").build(flow)
    return n


class PdfRenderer(BaseTool):
    """report_markdown → PDF 파일. 출력 단계(ToolCategory.OUTPUT)."""

    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        previous = context.previous_results or {}
        markdown = (
            find_in_previous(previous, "report_markdown")
            or params.get("report_markdown")
            or ""
        )
        if not markdown:
            logger.info("pdf_renderer skipped — report_markdown 부재(data_insufficient)",
                        session_id=context.session_id)
            return {"pdf_file_path": None, "reason": "data_insufficient",
                    "detail": "report_markdown 0건/부재"}

        out_dir = Path(
            params.get("output_dir")
            or (_REPO_ROOT / "data" / (context.client_id or "default") / "outputs")
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        blocks = _render_pdf(markdown, out_path)
        logger.info("pdf_renderer completed", path=str(out_path), blocks=blocks)
        return {"pdf_file_path": str(out_path), "block_count": blocks}
