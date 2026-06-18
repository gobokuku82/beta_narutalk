"""LLM Client

Provider-agnostic LLM 클라이언트
"""

import json
from typing import Any, Optional

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.core.config import settings
from app.core.logging import get_logger
from app.dream_agent.llm_manager.config import LAYER_CONFIGS, LLMConfig

logger = get_logger(__name__)


class LLMClient:
    """LLM 클라이언트"""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._openai: Optional[AsyncOpenAI] = None
        self._anthropic: Optional[AsyncAnthropic] = None

    @property
    def openai(self) -> AsyncOpenAI:
        if self._openai is None:
            self._openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai

    @property
    def anthropic(self) -> AsyncAnthropic:
        if self._anthropic is None:
            self._anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._anthropic

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        """텍스트 생성

        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트
            response_format: 응답 형식 (JSON 스키마)
            **kwargs: 추가 파라미터

        Returns:
            생성된 텍스트
        """
        config = self.config
        provider = kwargs.get("provider", config.provider)

        logger.debug(
            "LLM generate",
            provider=provider,
            model=config.model,
            prompt_length=len(prompt),
        )

        if provider == "openai":
            return await self._generate_openai(
                prompt, system_prompt, response_format, **kwargs
            )
        elif provider == "anthropic":
            return await self._generate_anthropic(
                prompt, system_prompt, **kwargs
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        """OpenAI 생성"""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        model = kwargs.get("model", self.config.model)
        max_tok = kwargs.get("max_tokens", self.config.max_tokens)

        params: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
        }

        # GPT-5+ 모델은 max_tokens 대신 max_completion_tokens 사용
        if model.startswith("gpt-5") or model.startswith("o"):
            params["max_completion_tokens"] = max_tok
        else:
            params["max_tokens"] = max_tok

        if response_format:
            params["response_format"] = response_format

        response = await self.openai.chat.completions.create(**params)

        return response.choices[0].message.content or ""

    async def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Anthropic 생성"""
        params: dict[str, Any] = {
            "model": kwargs.get("model", "claude-3-5-sonnet-20241022"),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            params["system"] = system_prompt

        response = await self.anthropic.messages.create(**params)

        return response.content[0].text

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """JSON 생성

        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트
            schema: JSON 스키마
            **kwargs: 추가 파라미터

        Returns:
            생성된 JSON
        """
        # JSON 요청 프롬프트 추가
        json_prompt = prompt + "\n\nRespond with valid JSON only."

        if schema:
            json_prompt += f"\n\nExpected schema:\n```json\n{json.dumps(schema, indent=2)}\n```"

        response_format = {"type": "json_object"} if self.config.provider == "openai" else None

        result = await self.generate(
            json_prompt,
            system_prompt=system_prompt,
            response_format=response_format,
            **kwargs,
        )

        # JSON 파싱
        try:
            # JSON 블록 추출
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]

            return json.loads(result.strip())
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", error=str(e), response=result[:200])
            raise ValueError(f"Invalid JSON response: {e}")


# Layer별 클라이언트 팩토리
def get_llm_client(layer: str) -> LLMClient:
    """레이어별 LLM 클라이언트 반환"""
    config = LAYER_CONFIGS.get(layer, LLMConfig())
    return LLMClient(config)


# 기본 클라이언트
default_client = LLMClient()
