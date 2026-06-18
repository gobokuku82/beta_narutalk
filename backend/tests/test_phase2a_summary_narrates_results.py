"""Phase 2a — summary_generator 가 일반 실행결과(metric 포함)를 서술 (2026-06-08).

계획: docs/_claude/4layer_system/출력표시레이어_분류_계획_260608_v1.md (Phase 2)
사용자 모델: "서술해줄 tool" = D4 에서 재정의한 summary_generator. 단 현재는 4개 키
(sentiment/keywords/insights/report_markdown)만 수집 → metric-only 쿼리("4월 매출?")는
빈입력 가드에 걸려 서술 0. 2a 는 _collect_payload 를 확장해 일반 결과(metric 등)도 서술하게 함.

→ Phase 2c(response 결정론 표시)의 전제: 텍스트 산출자(서술 tool)가 숫자도 말로 바꿔줘야
response 가 LLM 없이 표시만 해도 빈답이 안 난다.

RED → GREEN:
  2a-1 metric-only 결과 → summary 서술 (현재: 4키 미수집 → data_insufficient)
  2a-2 구조 노이즈(count/_meta/file_no) 는 서술 payload 에서 제외
  2a-3 진짜 빈 입력은 여전히 data_insufficient (과수집 아님 — 회귀 가드)
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.report import summary_generator as sg_mod
from app.dream_agent.tools.report.summary_generator import SummaryGenerator


def _sg() -> SummaryGenerator:
    sg = object.__new__(SummaryGenerator)
    sg.spec = SimpleNamespace(name="summary_generator", parameters=[])
    return sg


# ── 2a-1: metric-only 결과를 서술 ──

def test_2a_1_summary_narrates_metric_only_result(monkeypatch):
    captured = {"prompt": ""}

    class _Fake:
        async def generate(self, prompt, system_prompt=None, **kw):  # noqa: ANN001
            captured["prompt"] = prompt
            return "4월 매출은 1.2억원입니다"

    monkeypatch.setattr(sg_mod, "get_llm_client", lambda layer: _Fake())
    ctx = ExecutionContext(
        session_id="s", plan_id="p",
        previous_results={"t1": {"revenue_total": 120000000, "count": 1, "_meta": {"x": 1}}},
    )

    result = asyncio.run(_sg().execute({}, ctx))

    assert result.get("summary"), "metric-only 결과도 서술돼야(빈입력 가드 안 걸림)"
    assert "120000000" in captured["prompt"], "수집 payload 에 metric 값(revenue_total) 포함돼 LLM 에 전달"


# ── 2a-2: 구조 노이즈는 서술 payload 에서 제외 ──

def test_2a_2_structural_noise_excluded_from_payload():
    payload = SummaryGenerator._collect_payload(
        {"t1": {"revenue_total": 120000000, "count": 1, "file_no": 5,
                "is_mock": False, "_meta": {"a": 1}}}
    )
    assert "revenue_total" in payload, "실제 산출(revenue_total)은 수집"
    for noise in ("count", "file_no", "is_mock", "_meta"):
        assert noise not in payload, f"구조 노이즈 {noise} 는 서술 대상 아님 — 제외"


# ── 2a-3: 진짜 빈 입력은 여전히 data_insufficient (과수집 회귀 가드) ──

def test_2a_3_truly_empty_still_insufficient(monkeypatch):
    calls = {"n": 0}

    class _Fake:
        async def generate(self, prompt, system_prompt=None, **kw):  # noqa: ANN001
            calls["n"] += 1
            return "지어낸 요약"

    monkeypatch.setattr(sg_mod, "get_llm_client", lambda layer: _Fake())
    ctx = ExecutionContext(session_id="s", plan_id="p", previous_results={})

    result = asyncio.run(_sg().execute({}, ctx))

    assert calls["n"] == 0, "빈 입력엔 LLM 호출 0 (LLMTool 가드 유지)"
    assert result.get("reason") == "data_insufficient", "진짜 빈 입력은 정직 degrade 신호 유지"
