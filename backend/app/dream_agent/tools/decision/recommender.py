"""recommender — 의사결정 카테고리 단일 tool: 추천 (2026-06-10).

데이터/분석 → 행동 제안. `ml_model.generate_recommendation` 재사용
(POC=MockMlModel → data/ml_mock/recommendations/<client>.json, MVP+=LlmMlModel swap, DI 1줄).
ai_recommendation(대시보드 O05 카드)과 같은 ml 백엔드 — 로직은 ml_models 단일 소스
(중복 아님: 카드 vs 대화 에이전트 두 surface 가 같은 ml 메서드 위임).

Status: complete — 단일 추천. 옵션·시뮬은 추후, 승인=stage3(의사결정_설계서_260610.md §2·§7).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.ml_models import get_default_ml_model

logger = get_logger(__name__)

_PRIORITY_KR = {"high": "높음", "medium": "보통", "low": "낮음"}


def _format_text(rows: list[dict[str, Any]]) -> str:
    """추천 rows → 표시용 텍스트 (responder 가 display)."""
    if not rows:
        return ""
    lines = ["추천 (우선순위순):"]
    for i, r in enumerate(rows, 1):
        pri = _PRIORITY_KR.get(r.get("priority", "medium"), r.get("priority", ""))
        lines.append(f"{i}. [{pri}] {r.get('title', '')} — {r.get('detail', '')}")
    return "\n".join(lines)


class Recommender(BaseTool):
    """추천 — ml_model(mock) 기반. 분석 산출(context)을 받아 행동 제안.

    mock 은 context 무시·fixture 반환 → 상류 분석 없어도 작동(큰틀 구동). 실모델 swap 시 소비.
    """

    async def execute(
        self, params: dict[str, Any], context: ExecutionContext
    ) -> dict[str, Any]:
        merged = self.merge_params(params)
        ctx_summary: dict[str, Any] = {
            "client": context.client_id,
            "previous": context.previous_results,   # 분석 산출 흡수 가능(POC mock 은 무시)
            "methodology": merged.get("methodology", "데이터 기반 행동 추천"),
        }
        ml = get_default_ml_model()
        result = await ml.generate_recommendation(ctx_summary, client=context.client_id)

        rows = [
            {"priority": r.priority, "title": r.title, "detail": r.detail}
            for r in result.recommendations
        ]
        logger.info("recommender completed", count=len(rows))
        return {
            "recommendations": rows,
            "count": len(rows),
            "recommendation_text": _format_text(rows),
        }
