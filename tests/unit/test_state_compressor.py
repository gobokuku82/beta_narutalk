"""
State Compressor 단위 테스트
Phase 2: State 압축 시스템
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, List
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.service.supervisor.state_compressor import StateCompressor, CompressionStrategy
from tests.fixtures.test_data import LARGE_STATE


class TestStateCompressor:
    """State 압축 테스트"""

    @pytest.fixture
    def compressor(self):
        """StateCompressor 인스턴스"""
        return StateCompressor(max_tokens=4000)

    @pytest.mark.asyncio
    async def test_token_counting(self, compressor):
        """토큰 카운팅 테스트"""
        # 작은 State
        small_state = {"query": "테스트 쿼리", "messages": ["메시지1", "메시지2"]}
        tokens = await compressor.count_tokens(small_state)
        assert tokens > 0
        assert tokens < 100

        # 큰 State
        tokens_large = await compressor.count_tokens(LARGE_STATE)
        assert tokens_large > tokens

    @pytest.mark.asyncio
    async def test_compression_needed(self, compressor):
        """압축 필요 여부 판단 테스트"""
        # 작은 State (압축 불필요)
        small_state = {"query": "짧은 쿼리"}
        needs_compression = await compressor.needs_compression(small_state)
        assert needs_compression is False

        # 큰 State (압축 필요)
        needs_compression = await compressor.needs_compression(LARGE_STATE)
        assert needs_compression is True

    @pytest.mark.asyncio
    async def test_message_compression(self, compressor):
        """메시지 압축 테스트"""
        messages = [f"메시지 {i}: 이것은 매우 긴 메시지입니다. " * 10 for i in range(50)]

        compressed = await compressor.compress_messages(messages, max_messages=20)

        # 압축 후 메시지 수가 줄어야 함
        assert len(compressed) <= 20
        # 최신 메시지가 유지되어야 함
        assert "메시지 49" in compressed[-1]

    @pytest.mark.asyncio
    async def test_result_compression(self, compressor):
        """중간 결과 압축 테스트"""
        results = {
            f"step_{i}": {
                "data": f"결과 데이터 {i} " * 100,
                "metadata": {"index": i}
            } for i in range(30)
        }

        compressed = await compressor.compress_intermediate_results(results, max_results=10)

        # 압축 후 결과 수가 줄어야 함
        assert len(compressed) <= 10

    @pytest.mark.asyncio
    async def test_essential_fields_preservation(self, compressor):
        """필수 필드 보존 테스트"""
        state = {
            "query": "중요한 쿼리",
            "current_agent": "sql_analysis",
            "execution_plan": {"steps": ["step1", "step2"]},
            "large_data": "x" * 10000,
            "metadata": {"not_essential": "data"}
        }

        compressed = await compressor.compress_state(state)

        # 필수 필드는 유지되어야 함
        assert compressed["query"] == state["query"]
        assert compressed["current_agent"] == state["current_agent"]
        assert compressed["execution_plan"] == state["execution_plan"]

    @pytest.mark.asyncio
    async def test_compression_strategies(self, compressor):
        """다양한 압축 전략 테스트"""
        # 요약 전략
        state_for_summary = {
            "messages": [f"긴 메시지 {i}" * 50 for i in range(100)]
        }

        compressed_summary = await compressor.compress_state(
            state_for_summary,
            strategy=CompressionStrategy.SUMMARIZE
        )

        # 요약되었는지 확인
        assert "messages" in compressed_summary
        if "summary" in compressed_summary:
            assert len(compressed_summary["summary"]) < len(str(state_for_summary["messages"]))

        # 자르기 전략
        compressed_truncate = await compressor.compress_state(
            LARGE_STATE,
            strategy=CompressionStrategy.TRUNCATE
        )

        # 크기가 줄었는지 확인
        original_tokens = await compressor.count_tokens(LARGE_STATE)
        compressed_tokens = await compressor.count_tokens(compressed_truncate)
        assert compressed_tokens < original_tokens

    @pytest.mark.asyncio
    async def test_compression_with_target_tokens(self, compressor):
        """목표 토큰 수로 압축 테스트"""
        target_tokens = 1000

        compressed = await compressor.compress_state(
            LARGE_STATE,
            target_tokens=target_tokens
        )

        # 압축 후 토큰 수가 목표 이하여야 함
        final_tokens = await compressor.count_tokens(compressed)
        assert final_tokens <= target_tokens + 100  # 약간의 오차 허용

    @pytest.mark.asyncio
    async def test_context_preservation(self, compressor):
        """컨텍스트 보존 테스트"""
        state = {
            "messages": [
                {"role": "system", "content": "시스템 메시지"},
                {"role": "user", "content": "사용자 질문 1"},
                {"role": "assistant", "content": "응답 1"},
            ] * 20,
            "context": {
                "user_id": "test_user",
                "session_id": "test_session"
            }
        }

        compressed = await compressor.compress_state(state)

        # 시스템 메시지와 컨텍스트는 유지되어야 함
        assert "context" in compressed
        assert compressed["context"]["user_id"] == "test_user"

        if "messages" in compressed:
            system_messages = [m for m in compressed["messages"]
                             if isinstance(m, dict) and m.get("role") == "system"]
            assert len(system_messages) > 0

    @pytest.mark.asyncio
    async def test_incremental_compression(self, compressor):
        """점진적 압축 테스트"""
        state = LARGE_STATE.copy()

        # 첫 번째 압축
        compressed_once = await compressor.compress_state(state, target_tokens=3000)
        tokens_once = await compressor.count_tokens(compressed_once)

        # 두 번째 압축 (더 작게)
        compressed_twice = await compressor.compress_state(
            compressed_once,
            target_tokens=2000
        )
        tokens_twice = await compressor.count_tokens(compressed_twice)

        # 점진적으로 작아져야 함
        assert tokens_twice < tokens_once

    @pytest.mark.asyncio
    async def test_compression_metadata(self, compressor):
        """압축 메타데이터 테스트"""
        compressed = await compressor.compress_state(LARGE_STATE)

        # 압축 메타데이터가 있어야 함
        if "_compression_metadata" in compressed:
            metadata = compressed["_compression_metadata"]
            assert "original_tokens" in metadata
            assert "compressed_tokens" in metadata
            assert "compression_ratio" in metadata
            assert "strategy_used" in metadata

    @pytest.mark.asyncio
    async def test_empty_state_handling(self, compressor):
        """빈 State 처리 테스트"""
        empty_state = {}
        compressed = await compressor.compress_state(empty_state)

        # 빈 State도 처리되어야 함
        assert compressed == empty_state

    @pytest.mark.asyncio
    async def test_compression_consistency(self, compressor):
        """압축 일관성 테스트"""
        state = {
            "query": "테스트 쿼리",
            "data": "중요한 데이터",
            "messages": ["메시지1", "메시지2"]
        }

        # 여러 번 압축해도 필수 데이터는 유지되어야 함
        compressed1 = await compressor.compress_state(state)
        compressed2 = await compressor.compress_state(state)

        assert compressed1["query"] == compressed2["query"]
        assert compressed1["data"] == compressed2["data"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])