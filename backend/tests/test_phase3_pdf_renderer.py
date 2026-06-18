"""Phase 3 — pdf_renderer 실구현 (reportlab 한국어 PDF) (2026-06-09).

출력/표시 레이어 Phase 3. dispatcher(2c)가 pdf_file_path 를 attachment 로 분류하므로,
실 tool 이 report_markdown → 진짜 PDF 파일을 만들면 그 포맷 e2e 가 증명된다.
ToolCategory.OUTPUT 신설 + tools/output/pdf_renderer.py + catalog/output/pdf_renderer.yaml.

P3-1 report_markdown(한국어) → 유효 PDF 파일 생성(%PDF 헤더)
P3-2 빈 입력 → data_insufficient (게이트 consumes 와 2겹 가드)
P3-3 registry 가 pdf_renderer → PdfRenderer 동적 resolve (배선 정합)
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.rendering.pdf_renderer import PdfRenderer


def _tool() -> PdfRenderer:
    t = object.__new__(PdfRenderer)
    t.spec = SimpleNamespace(name="pdf_renderer", parameters=[])
    return t


# ── P3-1: 한국어 마크다운 → 유효 PDF ──

def test_p3_1_renders_korean_markdown_to_valid_pdf(tmp_path):
    md = "# 4월 분석 보고서\n\n## 핵심\n- 매출은 **1.2억원**입니다.\n- 재구매율이 상승했습니다.\n"
    ctx = ExecutionContext(
        session_id="s", plan_id="p", client_id="clumi",
        previous_results={"t1": {"report_markdown": md}},
    )

    result = asyncio.run(_tool().execute({"output_dir": str(tmp_path)}, ctx))

    path = result.get("pdf_file_path")
    assert path, "pdf_file_path 반환돼야"
    p = Path(path)
    assert p.exists() and p.stat().st_size > 0, "실제 PDF 파일이 생성돼야"
    assert p.read_bytes()[:4] == b"%PDF", "유효한 PDF 시그니처(%PDF)"
    assert result.get("block_count", 0) >= 3, "마크다운 블록 렌더(헤더+불릿)"


# ── P3-2: 빈 입력 → data_insufficient ──

def test_p3_2_empty_input_is_data_insufficient():
    ctx = ExecutionContext(session_id="s", plan_id="p", client_id="clumi", previous_results={})
    result = asyncio.run(_tool().execute({}, ctx))
    assert result.get("pdf_file_path") is None
    assert result.get("reason") == "data_insufficient", "report_markdown 부재 → 정직 신호"


# ── P3-3: registry 배선 — pdf_renderer → PdfRenderer ──

def test_p3_3_registry_resolves_pdf_renderer():
    from app.dream_agent.tools.registry import get_registry

    reg = get_registry()
    assert reg.exists("pdf_renderer"), "registry 가 pdf_renderer(catalog/output yaml) 를 로드해야"
    cls = reg.import_tool("pdf_renderer")
    assert cls is PdfRenderer, "컨벤션 import: catalog/rendering/pdf_renderer.yaml → tools.rendering.pdf_renderer.PdfRenderer"
    assert reg.get("pdf_renderer").category.value == "rendering", "category=rendering(신설)"
