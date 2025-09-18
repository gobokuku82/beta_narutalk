"""
Dynamic Agent Loader 단위 테스트
Phase 2: 동적 에이전트 로딩
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.service.supervisor.agent_loader import DynamicAgentLoader, AgentType


class TestDynamicAgentLoader:
    """동적 에이전트 로더 테스트"""

    @pytest.fixture
    def loader(self):
        """DynamicAgentLoader 인스턴스"""
        return DynamicAgentLoader()

    @pytest.mark.asyncio
    async def test_agent_registration(self, loader):
        """에이전트 등록 테스트"""
        # Mock 에이전트 생성
        mock_agent = Mock()
        mock_agent.name = "test_agent"
        mock_agent.execute = AsyncMock(return_value={"result": "success"})

        # 에이전트 등록
        loader.register_agent("test_agent", mock_agent)

        # 등록 확인
        assert "test_agent" in loader.list_available_agents()

    @pytest.mark.asyncio
    async def test_lazy_loading(self, loader):
        """지연 로딩 테스트"""
        # 초기 상태: 로드된 에이전트 없음
        assert len(loader._loaded_agents) == 0

        # 에이전트 요청 시 로드
        agent = await loader.get_agent(AgentType.SQL_ANALYSIS)

        # 로드 확인
        assert agent is not None
        assert AgentType.SQL_ANALYSIS in loader._loaded_agents

    @pytest.mark.asyncio
    async def test_agent_caching(self, loader):
        """에이전트 캐싱 테스트"""
        # 첫 번째 요청
        agent1 = await loader.get_agent(AgentType.SQL_ANALYSIS)

        # 두 번째 요청 (캐시에서 반환)
        agent2 = await loader.get_agent(AgentType.SQL_ANALYSIS)

        # 같은 인스턴스여야 함
        assert agent1 is agent2

    @pytest.mark.asyncio
    async def test_agent_configuration(self, loader):
        """에이전트 설정 테스트"""
        config = {
            "temperature": 0.5,
            "max_tokens": 1000,
            "custom_param": "value"
        }

        # 설정과 함께 에이전트 로드
        agent = await loader.get_agent(
            AgentType.SQL_ANALYSIS,
            config=config
        )

        assert agent is not None
        # 설정이 적용되었는지 확인 (실제 구현에 따라 다름)

    @pytest.mark.asyncio
    async def test_concurrent_loading(self, loader):
        """동시 로딩 테스트"""
        async def load_agent(agent_type):
            return await loader.get_agent(agent_type)

        # 동시에 여러 에이전트 로드
        tasks = [
            load_agent(AgentType.SQL_ANALYSIS),
            load_agent(AgentType.INFORMATION_RETRIEVAL),
            load_agent(AgentType.DOCUMENT_GENERATION)
        ]

        agents = await asyncio.gather(*tasks)

        # 모든 에이전트가 로드되어야 함
        assert all(agent is not None for agent in agents)
        assert len(loader._loaded_agents) >= 3

    @pytest.mark.asyncio
    async def test_agent_unloading(self, loader):
        """에이전트 언로드 테스트"""
        # 에이전트 로드
        await loader.get_agent(AgentType.SQL_ANALYSIS)
        assert AgentType.SQL_ANALYSIS in loader._loaded_agents

        # 언로드
        await loader.unload_agent(AgentType.SQL_ANALYSIS)
        assert AgentType.SQL_ANALYSIS not in loader._loaded_agents

    @pytest.mark.asyncio
    async def test_memory_management(self, loader):
        """메모리 관리 테스트"""
        # 여러 에이전트 로드
        for agent_type in [AgentType.SQL_ANALYSIS, AgentType.INFORMATION_RETRIEVAL]:
            await loader.get_agent(agent_type)

        # 메모리 사용량 확인
        memory_usage = loader.get_memory_usage()
        assert memory_usage > 0

        # 메모리 정리
        await loader.cleanup_unused_agents()

        # 메모리 사용량 감소 확인
        memory_usage_after = loader.get_memory_usage()
        assert memory_usage_after <= memory_usage

    @pytest.mark.asyncio
    async def test_agent_lifecycle_hooks(self, loader):
        """에이전트 라이프사이클 훅 테스트"""
        # Mock 에이전트 with 라이프사이클 메서드
        mock_agent = Mock()
        mock_agent.initialize = AsyncMock()
        mock_agent.shutdown = AsyncMock()

        loader.register_agent("lifecycle_test", mock_agent)

        # 에이전트 로드 (initialize 호출)
        agent = await loader.get_agent("lifecycle_test")
        if hasattr(agent, 'initialize'):
            agent.initialize.assert_called_once()

        # 에이전트 언로드 (shutdown 호출)
        await loader.unload_agent("lifecycle_test")
        if hasattr(mock_agent, 'shutdown'):
            mock_agent.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_not_found(self, loader):
        """존재하지 않는 에이전트 테스트"""
        with pytest.raises(ValueError) as exc:
            await loader.get_agent("non_existent_agent")

        assert "not found" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_agent_loading_error(self, loader):
        """에이전트 로딩 오류 테스트"""
        # 오류를 발생시키는 Mock 에이전트
        def error_factory():
            raise RuntimeError("Loading failed")

        loader._agent_factories["error_agent"] = error_factory

        with pytest.raises(RuntimeError):
            await loader.get_agent("error_agent")

    @pytest.mark.asyncio
    async def test_agent_statistics(self, loader):
        """에이전트 통계 테스트"""
        # 여러 에이전트 로드 및 사용
        agent1 = await loader.get_agent(AgentType.SQL_ANALYSIS)
        agent2 = await loader.get_agent(AgentType.INFORMATION_RETRIEVAL)

        # 통계 조회
        stats = loader.get_statistics()

        assert "loaded_agents" in stats
        assert "total_loads" in stats
        assert "cache_hits" in stats
        assert stats["loaded_agents"] == 2

    @pytest.mark.asyncio
    async def test_agent_preloading(self, loader):
        """에이전트 사전 로딩 테스트"""
        # 자주 사용하는 에이전트 사전 로드
        preload_list = [
            AgentType.SQL_ANALYSIS,
            AgentType.INFORMATION_RETRIEVAL
        ]

        await loader.preload_agents(preload_list)

        # 사전 로드 확인
        for agent_type in preload_list:
            assert agent_type in loader._loaded_agents

    @pytest.mark.asyncio
    async def test_dynamic_import(self, loader):
        """동적 임포트 테스트"""
        # 실제 에이전트 모듈 동적 임포트
        agent = await loader.get_agent(AgentType.SQL_ANALYSIS)

        # 에이전트가 올바른 메서드를 가지고 있는지 확인
        assert hasattr(agent, 'execute') or hasattr(agent, 'ainvoke')

    @pytest.mark.asyncio
    async def test_agent_priority_loading(self, loader):
        """우선순위 기반 로딩 테스트"""
        # 우선순위 설정
        loader.set_priority(AgentType.SQL_ANALYSIS, priority=1)
        loader.set_priority(AgentType.DOCUMENT_GENERATION, priority=2)

        # 메모리 제한 상황에서 우선순위 높은 에이전트 유지
        await loader.enforce_memory_limit(max_agents=1)

        # 우선순위가 높은 에이전트가 유지되어야 함
        assert AgentType.SQL_ANALYSIS in loader._loaded_agents


if __name__ == "__main__":
    pytest.main([__file__, "-v"])