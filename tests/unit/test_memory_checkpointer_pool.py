"""
MemoryCheckpointerPool 단위 테스트
메모리 기반 체크포인터 풀 테스트
"""

import pytest
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.service.supervisor.memory_checkpointer_pool import (
    MemoryCheckpointerPool,
    get_memory_checkpointer_pool
)


class TestMemoryCheckpointerPool:
    """MemoryCheckpointerPool 테스트"""

    @pytest.fixture
    async def pool(self):
        """테스트용 MemoryCheckpointerPool 인스턴스"""
        pool = MemoryCheckpointerPool(max_connections=3)
        yield pool
        await pool.close_all()

    @pytest.mark.asyncio
    async def test_connection_creation(self, pool):
        """연결 생성 테스트"""
        # 첫 번째 연결
        async with pool.get_connection_context() as conn:
            assert conn is not None
            assert pool.active_connections == 1

        # 연결이 반환되면 active가 0이어야 함
        assert pool.active_connections == 0

    @pytest.mark.asyncio
    async def test_connection_reuse(self, pool):
        """연결 재사용 테스트"""
        conn_id1 = None
        conn_id2 = None

        # 첫 번째 연결 사용
        async with pool.get_connection_context() as conn1:
            conn_id1 = id(conn1)

        # 두 번째 연결 요청 (재사용되어야 함)
        async with pool.get_connection_context() as conn2:
            conn_id2 = id(conn2)

        # 같은 연결 객체여야 함
        assert conn_id1 == conn_id2

    @pytest.mark.asyncio
    async def test_max_connections_limit(self, pool):
        """최대 연결 수 제한 테스트"""
        connections = []

        # 최대 연결 수만큼 생성
        for i in range(pool.max_connections):
            conn = await pool.get_connection()
            connections.append(conn)

        assert pool.active_connections == pool.max_connections
        assert pool.total_connections == pool.max_connections

        # 연결 반환
        for conn in connections:
            await pool.release_connection(conn)

        assert pool.active_connections == 0

    @pytest.mark.asyncio
    async def test_concurrent_access(self, pool):
        """동시 접근 테스트"""
        async def use_connection(pool, duration):
            async with pool.get_connection_context() as conn:
                await asyncio.sleep(duration)
                return id(conn)

        # 동시에 여러 연결 요청
        tasks = [
            use_connection(pool, 0.01) for _ in range(5)
        ]

        results = await asyncio.gather(*tasks)

        # 연결들이 재사용되었는지 확인
        unique_connections = set(results)
        assert len(unique_connections) <= pool.max_connections

    @pytest.mark.asyncio
    async def test_connection_health_check(self, pool):
        """연결 상태 체크 테스트"""
        async with pool.get_connection_context() as conn:
            # 연결이 살아있는지 확인
            is_healthy = await pool.check_connection_health(conn)
            assert is_healthy is True

    @pytest.mark.asyncio
    async def test_pool_statistics(self, pool):
        """풀 통계 테스트"""
        # 초기 상태
        stats = pool.get_statistics()
        assert stats["total_connections"] == 0
        assert stats["active_connections"] == 0
        assert stats["total_requests"] == 0

        # 연결 사용 후
        async with pool.get_connection_context() as conn:
            stats = pool.get_statistics()
            assert stats["active_connections"] == 1
            assert stats["total_requests"] >= 1

        # 연결 반환 후
        stats = pool.get_statistics()
        assert stats["active_connections"] == 0

    @pytest.mark.asyncio
    async def test_connection_timeout(self, pool):
        """연결 타임아웃 테스트"""
        # 타임아웃을 짧게 설정
        pool.connection_timeout = 1

        # 모든 연결 사용
        connections = []
        for i in range(pool.max_connections):
            conn = await pool.get_connection()
            connections.append(conn)

        # 타임아웃 설정하여 추가 연결 시도
        try:
            await asyncio.wait_for(
                pool.get_connection(),
                timeout=2
            )
            assert False, "Should have timed out"
        except asyncio.TimeoutError:
            assert True

        # 연결 반환
        for conn in connections:
            await pool.release_connection(conn)

    @pytest.mark.asyncio
    async def test_close_all_connections(self, pool):
        """모든 연결 종료 테스트"""
        # 여러 연결 생성
        async with pool.get_connection_context() as conn1:
            pass
        async with pool.get_connection_context() as conn2:
            pass

        # 모든 연결 종료
        await pool.close_all()

        # 통계 확인
        stats = pool.get_statistics()
        assert stats["total_connections"] == 0
        assert stats["active_connections"] == 0

    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        """싱글톤 패턴 테스트"""
        pool1 = get_memory_checkpointer_pool()
        pool2 = get_memory_checkpointer_pool()

        # 같은 인스턴스여야 함
        assert pool1 is pool2

        await pool1.close_all()

    @pytest.mark.asyncio
    async def test_error_handling(self, pool):
        """에러 처리 테스트"""
        # 잘못된 연결 반환 시도
        from langgraph.checkpoint.memory import MemorySaver
        fake_connection = MemorySaver()

        with pytest.raises(ValueError):
            await pool.release_connection(fake_connection)

    @pytest.mark.asyncio
    async def test_context_manager_exception(self, pool):
        """Context Manager 예외 처리 테스트"""
        try:
            async with pool.get_connection_context() as conn:
                # 예외 발생
                raise ValueError("Test exception")
        except ValueError:
            pass

        # 연결이 제대로 반환되었는지 확인
        assert pool.active_connections == 0

        # 다시 연결을 가져올 수 있어야 함
        async with pool.get_connection_context() as conn:
            assert conn is not None

    @pytest.mark.asyncio
    async def test_pool_hits_and_misses(self, pool):
        """풀 히트/미스 통계 테스트"""
        # 첫 번째 연결 (미스)
        conn1 = await pool.get_connection()
        stats = pool.get_statistics()
        assert stats["pool_misses"] == 1
        assert stats["pool_hits"] == 0

        # 연결 반환
        await pool.release_connection(conn1)

        # 두 번째 연결 (히트)
        conn2 = await pool.get_connection()
        stats = pool.get_statistics()
        assert stats["pool_hits"] == 1

        await pool.release_connection(conn2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])