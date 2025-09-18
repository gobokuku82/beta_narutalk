"""
State Compression and Optimization for LangGraph 0.6.x
State 압축 및 최적화 시스템 - 토큰 제한 관리
"""

import json
import hashlib
import pickle
import zlib
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import tiktoken
import logging
from collections import deque
from dataclasses import dataclass, asdict
import numpy as np
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

logger = logging.getLogger(__name__)


@dataclass
class CompressionStats:
    """압축 통계"""
    original_size: int
    compressed_size: int
    token_count_before: int
    token_count_after: int
    compression_ratio: float
    compression_time: float
    method_used: str


class StateCompressor:
    """
    LangGraph State 압축 및 최적화
    - 토큰 수 제한 관리 (4000 토큰 미만)
    - 중복 제거 및 요약
    - 효율적인 직렬화
    """

    def __init__(
        self,
        max_tokens: int = 4000,
        max_history_items: int = 5,
        enable_summarization: bool = True,
        compression_level: int = 6  # zlib 압축 레벨 (0-9)
    ):
        """
        Initialize StateCompressor

        Args:
            max_tokens: 최대 토큰 수
            max_history_items: 유지할 최대 히스토리 항목 수
            enable_summarization: 요약 활성화 여부
            compression_level: 압축 레벨
        """
        self.max_tokens = max_tokens
        self.max_history_items = max_history_items
        self.enable_summarization = enable_summarization
        self.compression_level = compression_level

        # 토큰 카운터 (GPT-4 기준)
        self.encoder = tiktoken.encoding_for_model("gpt-4")

        # 압축 캐시
        self._compression_cache: Dict[str, bytes] = {}
        self._cache_size_limit = 100  # 최대 캐시 항목 수

        # 통계
        self.stats = {
            "total_compressions": 0,
            "total_bytes_saved": 0,
            "total_tokens_saved": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }

        logger.info(f"StateCompressor initialized with max_tokens={max_tokens}")

    def count_tokens(self, text: str) -> int:
        """
        토큰 수 계산

        Args:
            text: 텍스트

        Returns:
            토큰 수
        """
        try:
            return len(self.encoder.encode(text))
        except:
            # 대략적인 추정 (평균 4자 = 1토큰)
            return len(text) // 4

    async def compress_state(
        self,
        state: Dict[str, Any],
        target_tokens: Optional[int] = None
    ) -> Tuple[Dict[str, Any], CompressionStats]:
        """
        State 압축

        Args:
            state: 원본 State
            target_tokens: 목표 토큰 수 (기본값: max_tokens)

        Returns:
            압축된 State와 통계
        """
        import time
        start_time = time.time()

        target_tokens = target_tokens or self.max_tokens
        self.stats["total_compressions"] += 1

        # 원본 크기 측정
        original_str = json.dumps(state, ensure_ascii=False, default=str)
        original_size = len(original_str.encode('utf-8'))
        original_tokens = self.count_tokens(original_str)

        # 이미 목표 이하인 경우
        if original_tokens <= target_tokens:
            stats = CompressionStats(
                original_size=original_size,
                compressed_size=original_size,
                token_count_before=original_tokens,
                token_count_after=original_tokens,
                compression_ratio=1.0,
                compression_time=time.time() - start_time,
                method_used="none"
            )
            return state, stats

        # 압축 전략 적용
        compressed_state = state.copy()

        # 1. 중복 제거
        compressed_state = self._remove_duplicates(compressed_state)

        # 2. 히스토리 트리밍
        if "history" in compressed_state:
            compressed_state["history"] = self._trim_history(
                compressed_state["history"],
                self.max_history_items
            )

        # 3. 메시지 압축
        if "messages" in compressed_state:
            compressed_state["messages"] = await self._compress_messages(
                compressed_state["messages"]
            )

        # 4. 긴 텍스트 요약
        if self.enable_summarization:
            compressed_state = await self._summarize_long_texts(compressed_state)

        # 5. 불필요한 필드 제거
        compressed_state = self._remove_unnecessary_fields(compressed_state)

        # 6. 데이터 타입 최적화
        compressed_state = self._optimize_data_types(compressed_state)

        # 압축 후 크기 측정
        compressed_str = json.dumps(compressed_state, ensure_ascii=False, default=str)
        compressed_size = len(compressed_str.encode('utf-8'))
        compressed_tokens = self.count_tokens(compressed_str)

        # 통계 업데이트
        bytes_saved = original_size - compressed_size
        tokens_saved = original_tokens - compressed_tokens
        self.stats["total_bytes_saved"] += bytes_saved
        self.stats["total_tokens_saved"] += tokens_saved

        stats = CompressionStats(
            original_size=original_size,
            compressed_size=compressed_size,
            token_count_before=original_tokens,
            token_count_after=compressed_tokens,
            compression_ratio=compressed_size / original_size if original_size > 0 else 1.0,
            compression_time=time.time() - start_time,
            method_used="multi-strategy"
        )

        logger.info(
            f"State compressed: {original_tokens} -> {compressed_tokens} tokens "
            f"({stats.compression_ratio:.1%} of original)"
        )

        return compressed_state, stats

    def _remove_duplicates(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        중복 데이터 제거

        Args:
            state: State 딕셔너리

        Returns:
            중복 제거된 State
        """
        seen_hashes = set()
        cleaned = {}

        for key, value in state.items():
            # 값의 해시 계산
            value_str = json.dumps(value, sort_keys=True, default=str)
            value_hash = hashlib.md5(value_str.encode()).hexdigest()

            # 중복이 아닌 경우만 포함
            if value_hash not in seen_hashes:
                seen_hashes.add(value_hash)
                cleaned[key] = value

        return cleaned

    def _trim_history(
        self,
        history: List[Any],
        max_items: int
    ) -> List[Any]:
        """
        히스토리 트리밍

        Args:
            history: 히스토리 리스트
            max_items: 최대 항목 수

        Returns:
            트리밍된 히스토리
        """
        if len(history) <= max_items:
            return history

        # 최근 항목 우선 유지
        return history[-max_items:]

    async def _compress_messages(
        self,
        messages: List[BaseMessage]
    ) -> List[BaseMessage]:
        """
        메시지 압축

        Args:
            messages: 메시지 리스트

        Returns:
            압축된 메시지 리스트
        """
        if len(messages) <= 3:
            return messages

        compressed = []

        # 시스템 메시지는 항상 유지
        system_messages = [m for m in messages if isinstance(m, SystemMessage)]
        compressed.extend(system_messages)

        # 최근 대화 유지
        recent_messages = [m for m in messages if not isinstance(m, SystemMessage)][-3:]

        # 중간 메시지들 요약
        middle_messages = [m for m in messages if not isinstance(m, SystemMessage)][:-3]
        if middle_messages and self.enable_summarization:
            summary = await self._summarize_messages(middle_messages)
            compressed.append(AIMessage(content=f"[이전 대화 요약: {summary}]"))

        compressed.extend(recent_messages)
        return compressed

    async def _summarize_messages(
        self,
        messages: List[BaseMessage]
    ) -> str:
        """
        메시지 요약

        Args:
            messages: 메시지 리스트

        Returns:
            요약된 텍스트
        """
        # 간단한 요약 구현 (실제로는 LLM 사용 권장)
        total_messages = len(messages)
        topics = set()

        for msg in messages:
            # 키워드 추출 (간단한 구현)
            content = msg.content.lower()
            if "sql" in content or "쿼리" in content:
                topics.add("SQL 분석")
            if "hr" in content or "인사" in content:
                topics.add("HR 정보")
            if "규정" in content or "compliance" in content:
                topics.add("규정 검토")

        summary = f"{total_messages}개 메시지 교환"
        if topics:
            summary += f" (주제: {', '.join(topics)})"

        return summary

    async def _summarize_long_texts(
        self,
        state: Dict[str, Any],
        max_length: int = 500
    ) -> Dict[str, Any]:
        """
        긴 텍스트 요약

        Args:
            state: State 딕셔너리
            max_length: 최대 텍스트 길이

        Returns:
            요약 적용된 State
        """
        compressed = {}

        for key, value in state.items():
            if isinstance(value, str) and len(value) > max_length:
                # 긴 텍스트 요약
                compressed[key] = value[:max_length] + "... [요약됨]"
            elif isinstance(value, dict):
                # 재귀적 적용
                compressed[key] = await self._summarize_long_texts(value, max_length)
            elif isinstance(value, list):
                # 리스트 항목에 적용
                compressed[key] = [
                    await self._summarize_long_texts(item, max_length)
                    if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                compressed[key] = value

        return compressed

    def _remove_unnecessary_fields(
        self,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        불필요한 필드 제거

        Args:
            state: State 딕셔너리

        Returns:
            정리된 State
        """
        # 제거할 필드 패턴
        unnecessary_patterns = [
            "_raw",
            "_debug",
            "_internal",
            "temp_",
            "cache_"
        ]

        cleaned = {}
        for key, value in state.items():
            # 불필요한 패턴 체크
            should_remove = any(
                pattern in key.lower()
                for pattern in unnecessary_patterns
            )

            # None 값 제거
            if value is None:
                should_remove = True

            # 빈 컨테이너 제거
            if isinstance(value, (list, dict, str)) and not value:
                should_remove = True

            if not should_remove:
                cleaned[key] = value

        return cleaned

    def _optimize_data_types(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        데이터 타입 최적화

        Args:
            state: State 딕셔너리

        Returns:
            최적화된 State
        """
        optimized = {}

        for key, value in state.items():
            if isinstance(value, float):
                # 소수점 2자리로 제한
                optimized[key] = round(value, 2)
            elif isinstance(value, datetime):
                # ISO 형식 문자열로 변환
                optimized[key] = value.isoformat()
            elif isinstance(value, np.ndarray):
                # NumPy 배열을 리스트로 변환
                optimized[key] = value.tolist()
            elif isinstance(value, dict):
                # 재귀적 적용
                optimized[key] = self._optimize_data_types(value)
            else:
                optimized[key] = value

        return optimized

    def compress_binary(self, data: Any) -> bytes:
        """
        바이너리 압축 (체크포인터용)

        Args:
            data: 압축할 데이터

        Returns:
            압축된 바이너리
        """
        # 캐시 키 생성
        cache_key = hashlib.md5(
            pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        ).hexdigest()

        # 캐시 확인
        if cache_key in self._compression_cache:
            self.stats["cache_hits"] += 1
            return self._compression_cache[cache_key]

        self.stats["cache_misses"] += 1

        # 직렬화 및 압축
        serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        compressed = zlib.compress(serialized, level=self.compression_level)

        # 캐시 저장 (크기 제한)
        if len(self._compression_cache) < self._cache_size_limit:
            self._compression_cache[cache_key] = compressed

        return compressed

    def decompress_binary(self, data: bytes) -> Any:
        """
        바이너리 압축 해제

        Args:
            data: 압축된 바이너리

        Returns:
            원본 데이터
        """
        decompressed = zlib.decompress(data)
        return pickle.loads(decompressed)

    def estimate_compression_ratio(self, state: Dict[str, Any]) -> float:
        """
        압축률 추정

        Args:
            state: State 딕셔너리

        Returns:
            예상 압축률 (0.0 ~ 1.0)
        """
        # 간단한 휴리스틱 기반 추정
        state_str = json.dumps(state, ensure_ascii=False, default=str)

        # 중복 문자열 비율 계산
        unique_chars = len(set(state_str))
        total_chars = len(state_str)
        uniqueness_ratio = unique_chars / total_chars if total_chars > 0 else 1.0

        # 압축 가능성 추정
        if uniqueness_ratio < 0.3:
            return 0.3  # 높은 중복 = 좋은 압축
        elif uniqueness_ratio < 0.5:
            return 0.5  # 중간 중복
        else:
            return 0.7  # 낮은 중복 = 낮은 압축

    def get_compression_stats(self) -> Dict[str, Any]:
        """압축 통계 반환"""
        return {
            **self.stats,
            "cache_hit_rate": (
                self.stats["cache_hits"] /
                (self.stats["cache_hits"] + self.stats["cache_misses"]) * 100
                if (self.stats["cache_hits"] + self.stats["cache_misses"]) > 0
                else 0
            ),
            "average_tokens_saved": (
                self.stats["total_tokens_saved"] / self.stats["total_compressions"]
                if self.stats["total_compressions"] > 0
                else 0
            ),
            "average_bytes_saved": (
                self.stats["total_bytes_saved"] / self.stats["total_compressions"]
                if self.stats["total_compressions"] > 0
                else 0
            )
        }


# 전역 압축기 인스턴스
_global_compressor: Optional[StateCompressor] = None


def get_state_compressor(max_tokens: int = 4000) -> StateCompressor:
    """전역 State 압축기 인스턴스 반환"""
    global _global_compressor
    if _global_compressor is None:
        _global_compressor = StateCompressor(max_tokens=max_tokens)
    return _global_compressor