"""
LLM Manager - 중앙화된 LLM 호출 관리
싱글톤 패턴으로 구현하여 전역적으로 하나의 인스턴스만 사용
"""

import os
import hashlib
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class LLMManager:
    """중앙 LLM 관리자 - 싱글톤 패턴"""
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialize()
            self._initialized = True

    def _initialize(self):
        """LLM 클라이언트 초기화"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        # 용도별 클라이언트 설정
        self.clients = {
            # 일반 대화용 (창의적)
            "openai": ChatOpenAI(
                model="gpt-4o",
                temperature=0.7,
                api_key=api_key,
                max_retries=3
            ),
            # SQL, 규정 검토용 (정확성)
            "openai_strict": ChatOpenAI(
                model="gpt-4o",
                temperature=0,
                api_key=api_key,
                max_retries=3
            ),
            # 빠른 응답용 (의도분석, 간단한 작업)
            "openai_mini": ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                api_key=api_key,
                max_retries=3
            ),
            # 문서 생성용 (균형잡힌 창의성)
            "openai_doc": ChatOpenAI(
                model="gpt-4o",
                temperature=0.5,
                api_key=api_key,
                max_retries=3
            )
        }

        # 캐시 설정 (TTL: 15분)
        self.cache = {}
        self.cache_ttl = timedelta(minutes=15)

        # 토큰 사용량 추적
        self.token_usage = {
            "total": 0,
            "by_model": {},
            "by_category": {}
        }

        logger.info("LLMManager initialized with multiple client configurations")

    async def generate(
        self,
        prompt: str,
        model: str = "openai",
        system_prompt: Optional[str] = None,
        category: Optional[str] = None,
        use_cache: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        LLM 응답 생성

        Args:
            prompt: 사용자 프롬프트
            model: 사용할 모델 클라이언트 키
            system_prompt: 시스템 프롬프트 (선택)
            category: 호출 카테고리 (추적용)
            use_cache: 캐시 사용 여부
            **kwargs: 추가 파라미터

        Returns:
            응답 딕셔너리
        """
        # 캐시 확인
        if use_cache:
            cache_key = self._get_cache_key(prompt, model, system_prompt)
            cached = self._get_from_cache(cache_key)
            if cached:
                logger.debug(f"Cache hit for category: {category}")
                return cached

        # LLM 호출
        try:
            client = self.clients.get(model, self.clients["openai"])

            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))

            # 비동기 호출
            response = await client.ainvoke(messages, **kwargs)

            # 결과 구성
            result = {
                "content": response.content,
                "model": model,
                "category": category,
                "timestamp": datetime.now().isoformat(),
                "usage": {
                    "prompt_tokens": response.response_metadata.get("token_usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": response.response_metadata.get("token_usage", {}).get("completion_tokens", 0),
                    "total_tokens": response.response_metadata.get("token_usage", {}).get("total_tokens", 0)
                }
            }

            # 토큰 사용량 추적
            self._track_usage(result["usage"], model, category)

            # 캐시 저장
            if use_cache:
                self._save_to_cache(cache_key, result)

            logger.info(f"Generated response for category: {category}, tokens: {result['usage']['total_tokens']}")
            return result

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Fallback 처리
            return self._handle_error(e, prompt, category)

    async def generate_batch(
        self,
        prompts: List[Dict[str, Any]],
        concurrent_limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        여러 프롬프트 병렬 처리

        Args:
            prompts: 프롬프트 딕셔너리 리스트
            concurrent_limit: 동시 실행 제한

        Returns:
            응답 리스트
        """
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def process_with_limit(prompt_data):
            async with semaphore:
                return await self.generate(**prompt_data)

        tasks = [process_with_limit(p) for p in prompts]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def _get_cache_key(self, prompt: str, model: str, system_prompt: Optional[str]) -> str:
        """캐시 키 생성"""
        content = f"{model}:{system_prompt or ''}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """캐시에서 가져오기"""
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() - entry["cached_at"] < self.cache_ttl:
                return entry["data"]
            else:
                del self.cache[key]
        return None

    def _save_to_cache(self, key: str, data: Dict[str, Any]):
        """캐시에 저장"""
        self.cache[key] = {
            "data": data,
            "cached_at": datetime.now()
        }

    def _track_usage(self, usage: Dict[str, int], model: str, category: Optional[str]):
        """토큰 사용량 추적"""
        total = usage.get("total_tokens", 0)

        self.token_usage["total"] += total

        if model not in self.token_usage["by_model"]:
            self.token_usage["by_model"][model] = 0
        self.token_usage["by_model"][model] += total

        if category:
            if category not in self.token_usage["by_category"]:
                self.token_usage["by_category"][category] = 0
            self.token_usage["by_category"][category] += total

    def _handle_error(self, error: Exception, prompt: str, category: Optional[str]) -> Dict[str, Any]:
        """에러 처리 및 fallback"""
        logger.error(f"LLM error in {category}: {error}")

        # 기본 응답 반환
        return {
            "content": "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            "model": "error",
            "category": category,
            "error": str(error),
            "timestamp": datetime.now().isoformat(),
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }

    def get_usage_stats(self) -> Dict[str, Any]:
        """사용량 통계 반환"""
        return {
            "total_tokens": self.token_usage["total"],
            "by_model": self.token_usage["by_model"],
            "by_category": self.token_usage["by_category"],
            "cache_size": len(self.cache),
            "estimated_cost": self._estimate_cost()
        }

    def _estimate_cost(self) -> Dict[str, float]:
        """예상 비용 계산 (대략적인 추정)"""
        # GPT-4o 가격 기준 (1K tokens)
        prices = {
            "gpt-4o": {"input": 0.0025, "output": 0.01},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006}
        }

        total_cost = 0.0
        for model, tokens in self.token_usage["by_model"].items():
            if "mini" in model:
                # 간단히 평균으로 계산
                cost = (tokens / 1000) * ((prices["gpt-4o-mini"]["input"] + prices["gpt-4o-mini"]["output"]) / 2)
            else:
                cost = (tokens / 1000) * ((prices["gpt-4o"]["input"] + prices["gpt-4o"]["output"]) / 2)
            total_cost += cost

        return {"estimated_usd": round(total_cost, 4)}

    def clear_cache(self):
        """캐시 클리어"""
        self.cache.clear()
        logger.info("LLM cache cleared")