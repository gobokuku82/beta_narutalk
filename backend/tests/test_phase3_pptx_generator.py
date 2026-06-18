"""Phase 3 — pptx_generator 실구현 (python-pptx 슬라이드) (2026-06-09).

dispatcher(2c)가 pptx_file_path 를 attachment(kind=ppt) 로 분류 → 실 tool 이 .pptx 생성.
ToolCategory.RENDERING + tools/rendering/pptx_generator.py + catalog/rendering yaml.

P3p-1 report_markdown(한국어) → 유효 .pptx(PK zip 헤더) + 슬라이드 수
P3p-2 빈 입력 → data_insufficient
P3p-3 registry 가 pptx_generator → PptxGenerator 동적 resolve
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.rendering.pptx_generator import PptxGenerator


def _tool() -> PptxGenerator:
    t = object.__new__(PptxGenerator)
    t.spec = SimpleNamespace(name="pptx_generator", parameters=[])
    return t


def test_p3p_1_renders_korean_markdown_to_valid_pptx(tmp_path):
    md = "# 4월 분석 보고서\n\n## 핵심 성과\n- 매출 1.2억원\n- 재구매율 상승\n\n## 채널\n- naver 우위\n"
    ctx = ExecutionContext(
        session_id="s", plan_id="p", client_id="clumi",
        previous_results={"t1": {"report_markdown": md}},
    )

    result = asyncio.run(_tool().execute({"output_dir": str(tmp_path)}, ctx))

    path = result.get("pptx_file_path")
    assert path, "pptx_file_path 반환돼야"
    p = Path(path)
    assert p.exists() and p.stat().st_size > 0, "실제 .pptx 파일 생성"
    assert p.read_bytes()[:2] == b"PK", "유효한 pptx(zip PK 시그니처)"
    assert result.get("slide_count", 0) >= 3, "타이틀 + ## 섹션 2개 = 3 슬라이드"


def test_p3p_2_empty_input_is_data_insufficient():
    ctx = ExecutionContext(session_id="s", plan_id="p", client_id="clumi", previous_results={})
    result = asyncio.run(_tool().execute({}, ctx))
    assert result.get("pptx_file_path") is None
    assert result.get("reason") == "data_insufficient"


def test_p3p_3_registry_resolves_pptx_generator():
    from app.dream_agent.tools.registry import get_registry

    reg = get_registry()
    assert reg.exists("pptx_generator"), "registry 가 pptx_generator(catalog/rendering yaml) 로드"
    cls = reg.import_tool("pptx_generator")
    assert cls is PptxGenerator
    assert reg.get("pptx_generator").category.value == "rendering"
