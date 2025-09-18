"""
Database Connection Pool for LangGraph AsyncSqliteSaver
LangGraph 0.6.x 최적화된 연결 풀 관리
"""

from typing import Optional, List, Dict, Any
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import asyncio
import logging
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import os

logger = logging.getLogger(__name__)


class CheckpointerPool:
    """
    AsyncSqliteSaver 연결 풀 관리자
    - 싱글톤 패턴으로 전역 인스턴스 관리
    - 연결 재사용을 통한 성능 최적화
    - 연결 수명 주기 관리
    """

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls, *args, **kwargs):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        db_path: str = "database/checkpointer/checkpoint.db",
        max_connections: int = 5,
        connection_timeout: int = 30,
        idle_timeout: int = 300  # 5분
    ):
        """
        Initialize CheckpointerPool

        Args:
            db_path: SQLite 데이터베이스 경로
            max_connections: 최대 연결 수
            connection_timeout: 연결 타임아웃 (초)
            idle_timeout: 유휴 연결 타임아웃 (초)
        """

        # 이미 초기화되었으면 스킵
        if hasattr(self, '_initialized'):
            return

        self.db_path = db_path
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.idle_timeout = idle_timeout

        # 연결 풀
        self._available_connections: List[Dict[str, Any]] = []
        self._in_use_connections: List[Dict[str, Any]] = []

        # 통계
        self.stats = {
            "total_connections_created": 0,
            "current_active_connections": 0,
            "total_requests": 0,
            "pool_hits": 0,
            "pool_misses": 0,
            "average_wait_time": 0.0,
            "last_cleanup": datetime.now()
        }

        # DB 디렉토리 생성
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        self._initialized = True
        self._cleanup_task = None

        logger.info(f"CheckpointerPool initialized with max_connections={max_connections}")

    async def start_cleanup_task(self):
        """백그라운드 정리 작업 시작"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup_task(self):
        """백그라운드 정리 작업 중지"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_loop(self):
        """주기적으로 유휴 연결 정리"""
        while True:
            try:
                await asyncio.sleep(60)  # 1분마다 체크
                await self._cleanup_idle_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _cleanup_idle_connections(self):
        """유휴 시간이 초과된 연결 정리"""
        async with self._lock:
            now = datetime.now()
            expired_connections = []

            for conn_info in self._available_connections:
                if (now - conn_info["last_used"]).total_seconds() > self.idle_timeout:
                    expired_connections.append(conn_info)

            # 만료된 연결 제거
            for conn_info in expired_connections:
                try:
                    await conn_info["connection"].close()
                    self._available_connections.remove(conn_info)
                    logger.debug(f"Closed idle connection (idle for {(now - conn_info['last_used']).total_seconds():.1f}s)")
                except Exception as e:
                    logger.error(f"Error closing idle connection: {e}")

            self.stats["last_cleanup"] = now
            if expired_connections:
                logger.info(f"Cleaned up {len(expired_connections)} idle connections")

    async def get_connection(self) -> AsyncSqliteSaver:
        """
        연결 풀에서 연결 가져오기

        Returns:
            AsyncSqliteSaver 인스턴스
        """
        start_time = datetime.now()
        self.stats["total_requests"] += 1

        async with self._lock:
            # 사용 가능한 연결이 있으면 재사용
            if self._available_connections:
                conn_info = self._available_connections.pop(0)
                conn_info["last_used"] = datetime.now()
                self._in_use_connections.append(conn_info)

                self.stats["pool_hits"] += 1
                self.stats["current_active_connections"] = len(self._in_use_connections)

                wait_time = (datetime.now() - start_time).total_seconds()
                self._update_average_wait_time(wait_time)

                logger.debug(f"Reused connection from pool (pool hits: {self.stats['pool_hits']})")
                return conn_info["connection"]

            # 새 연결 생성 (최대 연결 수 제한 체크)
            if len(self._in_use_connections) >= self.max_connections:
                # 최대 연결 수에 도달했으면 대기
                logger.warning(f"Connection pool at max capacity ({self.max_connections}), waiting...")

                # 연결이 반환될 때까지 대기 (타임아웃 적용)
                timeout_time = datetime.now() + timedelta(seconds=self.connection_timeout)
                while datetime.now() < timeout_time:
                    await asyncio.sleep(0.1)
                    if self._available_connections:
                        return await self.get_connection()  # 재귀 호출

                raise TimeoutError(f"Failed to get connection within {self.connection_timeout} seconds")

            # 새 연결 생성
            self.stats["pool_misses"] += 1
            self.stats["total_connections_created"] += 1

            try:
                connection = await AsyncSqliteSaver.from_conn_string(self.db_path)
                conn_info = {
                    "connection": connection,
                    "created": datetime.now(),
                    "last_used": datetime.now(),
                    "id": self.stats["total_connections_created"]
                }
                self._in_use_connections.append(conn_info)

                self.stats["current_active_connections"] = len(self._in_use_connections)

                wait_time = (datetime.now() - start_time).total_seconds()
                self._update_average_wait_time(wait_time)

                logger.debug(f"Created new connection #{conn_info['id']} (total: {self.stats['total_connections_created']})")
                return connection

            except Exception as e:
                logger.error(f"Failed to create new connection: {e}")
                raise

    async def release_connection(self, connection: AsyncSqliteSaver):
        """
        연결을 풀로 반환

        Args:
            connection: 반환할 AsyncSqliteSaver 인스턴스
        """
        async with self._lock:
            # in_use에서 연결 찾기
            conn_info = None
            for info in self._in_use_connections:
                if info["connection"] == connection:
                    conn_info = info
                    break

            if conn_info:
                self._in_use_connections.remove(conn_info)

                # 풀 크기가 최대치 미만이면 풀에 추가
                if len(self._available_connections) < self.max_connections:
                    conn_info["last_used"] = datetime.now()
                    self._available_connections.append(conn_info)
                    logger.debug(f"Released connection #{conn_info['id']} back to pool")
                else:
                    # 풀이 가득차면 연결 닫기
                    try:
                        await connection.close()
                        logger.debug(f"Closed connection #{conn_info['id']} (pool full)")
                    except Exception as e:
                        logger.error(f"Error closing connection: {e}")

                self.stats["current_active_connections"] = len(self._in_use_connections)
            else:
                logger.warning("Attempted to release unknown connection")

    @asynccontextmanager
    async def get_connection_context(self):
        """
        컨텍스트 매니저로 연결 관리

        Usage:
            async with pool.get_connection_context() as connection:
                # use connection
        """
        connection = None
        try:
            connection = await self.get_connection()
            yield connection
        finally:
            if connection:
                await self.release_connection(connection)

    def _update_average_wait_time(self, wait_time: float):
        """평균 대기 시간 업데이트"""
        current_avg = self.stats["average_wait_time"]
        total_requests = self.stats["total_requests"]

        # 이동 평균 계산
        if total_requests == 1:
            self.stats["average_wait_time"] = wait_time
        else:
            self.stats["average_wait_time"] = (
                (current_avg * (total_requests - 1) + wait_time) / total_requests
            )

    async def close_all(self):
        """모든 연결 닫기"""
        async with self._lock:
            all_connections = self._available_connections + self._in_use_connections

            for conn_info in all_connections:
                try:
                    await conn_info["connection"].close()
                    logger.debug(f"Closed connection #{conn_info['id']}")
                except Exception as e:
                    logger.error(f"Error closing connection #{conn_info['id']}: {e}")

            self._available_connections.clear()
            self._in_use_connections.clear()
            self.stats["current_active_connections"] = 0

            logger.info(f"Closed all connections (total closed: {len(all_connections)})")

    def get_stats(self) -> Dict[str, Any]:
        """풀 통계 반환"""
        return {
            **self.stats,
            "available_connections": len(self._available_connections),
            "in_use_connections": len(self._in_use_connections),
            "pool_efficiency": (
                self.stats["pool_hits"] / self.stats["total_requests"] * 100
                if self.stats["total_requests"] > 0 else 0
            )
        }

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self.start_cleanup_task()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.stop_cleanup_task()
        await self.close_all()


# 전역 풀 인스턴스 생성 함수
_global_pool: Optional[CheckpointerPool] = None


def get_checkpointer_pool(
    db_path: str = "database/checkpointer/checkpoint.db",
    max_connections: int = 5
) -> CheckpointerPool:
    """
    전역 CheckpointerPool 인스턴스 반환

    Args:
        db_path: SQLite 데이터베이스 경로
        max_connections: 최대 연결 수

    Returns:
        CheckpointerPool 인스턴스
    """
    global _global_pool

    if _global_pool is None:
        _global_pool = CheckpointerPool(
            db_path=db_path,
            max_connections=max_connections
        )

    return _global_pool