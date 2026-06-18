"""LLM Configuration"""

from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class LLMConfig:
    """LLM 설정"""

    # Provider
    provider: Literal["openai", "anthropic"] = "openai"

    # Model
    model: str = "gpt-4o"

    # Generation params
    temperature: float = 0.3
    max_tokens: int = 4096
    top_p: float = 1.0

    # Timeout
    timeout_sec: int = 60

    # Retry
    max_retries: int = 3
    retry_delay_sec: float = 1.0


@dataclass
class PromptConfig:
    """프롬프트 설정"""

    # System prompt
    system_prompt: str = ""

    # User template
    user_template: str = ""

    # LLM config override
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


# Layer별 기본 설정 (Sprint 9: gpt-4o → GPT-5.4 nano/mini 전환)
LAYER_CONFIGS: dict[str, LLMConfig] = {
    "cognitive": LLMConfig(
        model="gpt-5.4-mini",       # 의도 분류 + StructuredQuery 생성 (복잡 쿼리 대응 위해 mini)
        temperature=0.1,
        max_tokens=2500,
    ),
    "planning": LLMConfig(
        model="gpt-5.4-mini",       # Team/Agent/Tool 매핑 + DAG 생성 (품질 중요)
        temperature=0.1,
        max_tokens=12000,           # F1(2026-06-06): 2500→12000. 복합 plan(todo 8+) 출력 truncation
                                    # 크래시 해결(stage3_truncation_rootcause §5). stage1/2 출력은 작아 무영향.
    ),
    "execution": LLMConfig(
        model="gpt-5.4-mini",       # insight_extractor, report_writer 등 LLM 호출
        temperature=0.3,
        max_tokens=2048,
    ),
    "response": LLMConfig(
        model="gpt-5.4-nano",       # 포맷팅 + 요약 (단순 태스크, 최경량)
        temperature=0.3,
        max_tokens=1500,
    ),
}
