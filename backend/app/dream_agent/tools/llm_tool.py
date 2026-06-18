"""LLMTool — LLM 호출 tool 의 공통 부모 (silent-0 축2, 2026-06-08).

선례: collection/_base.py RawCollectorBase(BaseTool) 와 같은 '카테고리 중간 부모' 패턴.

목적: 빈 입력에 LLM 을 불러 환각(거짓 보고서/인사이트/요약)을 만드는 silent-0 를
  *구조적으로* 차단한다. execute() 가 collect_inputs → [전부 빔 검사] → run_llm 순서를
  base 에서 소유하므로, subclass 는 빈입력 가드를 건너뛸 수 없다(새 LLM tool 자동 안전).

R1(report_writer.py)이 인라인으로 하던 빈가드를 여기로 끌어올린 것. 게이트(consumes)와
  2겹 방어:
    - 게이트(executor B2.1) = 실행 *전* 1차 차단(consumes 선언 시). 상류서 미리 SKIP.
    - 본 가드 = 방어심층 — 직접 호출 / consumes 미선언 / OR-입력(아무거나) 대비.
  의미(OR): collect_inputs 가 돌려준 값이 *전부* 0건/부재일 때만 degrade(하나라도 값 있으면
  실행). report_writer 의 기존 `not a and not b and not c` 와 동일.

Status: complete — Template Method 빈입력 가드.
Reference: docs/reports/silent0_복구_데이터흐름맵_2026-06-08.md §4·8
"""
from __future__ import annotations

from abc import abstractmethod
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool

logger = get_logger(__name__)


def _is_empty(value: Any) -> bool:
    """'불충분(0건/부재)' 인가. data_gate._is_empty 와 동일 의미(검사한 것 = 막는 것 일치).

    None=부재. list/dict/str 은 길이 0 이면 빈. 숫자/bool=값있음(0 도 값).
    """
    if value is None:
        return True
    if isinstance(value, (list, dict, str)):
        return len(value) == 0
    return False


class LLMTool(BaseTool):
    """LLM 호출 tool 공통 부모. subclass 는 collect_inputs + run_llm 만 정의.

    execute() 가 빈입력 가드를 소유 → 새 LLM tool 이 가드를 자동 상속(못 건너뜀).
    """

    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        inputs = self.collect_inputs(params, context)

        # 빈입력 가드(silent-0 축2): LLM 입력이 *전부* 0건/부재면 LLM 호출 *전* 정직 degrade.
        # 거짓 산출(환각) 대신 구조화된 data_insufficient 신호 반환 → 게이트/responder 가 소비.
        if all(_is_empty(v) for v in inputs.values()):
            # spec 미설정(직접 호출/테스트 object.__new__) 대비 tolerant.
            tool_name = getattr(getattr(self, "spec", None), "name", None) or "llm_tool"
            logger.info(
                "llm_tool skipped — 입력 전부 빔(data_insufficient)",
                tool=tool_name,
                session_id=context.session_id,
            )
            keys = ", ".join(inputs.keys()) or "(입력 키 없음)"
            return {
                "reason": "data_insufficient",
                "detail": f"{tool_name} LLM 입력 전부 0건/부재 ({keys})",
            }

        return await self.run_llm(inputs, params, context)

    @abstractmethod
    def collect_inputs(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        """LLM 에 먹일 입력을 {이름: 값} 으로 수집. 전부 빔 → 가드 발동(LLM 미호출).

        값이 *전부* 0건/부재면 insufficient. 하나라도 값 있으면 run_llm 진행(OR 의미).
        """

    @abstractmethod
    async def run_llm(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        """가드 통과 후 실제 LLM 호출 + 출력 shaping. (get_llm_client 는 subclass 모듈에서.)"""


__all__ = ["LLMTool"]
