"""
Multi-Level Caching System for NaruTalk
다단계 캐싱 시스템 - LangGraph 0.6.x 최적화
"""

import asyncio
import hashlib
import json
import pickle
import sqlite3
import time
from typing import Any, Dict, Optional, List, Tuple, Union
from datetime import datetime, timedelta
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CacheLevel(str, Enum):
    """캐시 레벨"""
    L1_MEMORY = "l1_memory"      # 메모리 (매우 빠름)
    L2_SQLITE = "l2_sqlite"       # SQLite (빠름)
    L3_REDIS = "l3_redis"         # Redis (중간) - 추후 구현


@dataclass
class CacheEntry:
    """캐시 엔트리"""
    key: str
    value: Any
    level: CacheLevel
    created_at: datetime
    accessed_at: datetime
    access_count: int
    ttl: int  # seconds
    size_bytes: int
    metadata: Dict[str, Any]

    def is_expired(self) -> bool:
        """만료 여부 확인"""
        if self.ttl <= 0:
            return False
        return (datetime.now() - self.created_at).total_seconds() > self.ttl

    def update_access(self):
        """접근 정보 업데이트"""
        self.accessed_at = datetime.now()
        self.access_count += 1


class LRUCache:
    """
    LRU (Least Recently Used) 메모리 캐시
    """

    def __init__(self, max_size: int = 100, max_memory_mb: int = 50):
        """
        Initialize LRUCache

        Args:
            max_size: 최대 항목 수
            max_memory_mb: 최대 메모리 사용량 (MB)
        """
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_memory_bytes = 0
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        if key not in self.cache:
            self.stats["misses"] += 1
            return None

        entry = self.cache[key]

        # 만료 체크
        if entry.is_expired():
            del self.cache[key]
            self.current_memory_bytes -= entry.size_bytes
            self.stats["misses"] += 1
            return None

        # LRU 업데이트 (최근 사용 항목을 끝으로 이동)
        self.cache.move_to_end(key)
        entry.update_access()
        self.stats["hits"] += 1

        return entry.value

    def put(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
        metadata: Optional[Dict] = None
    ):
        """캐시에 값 저장"""
        # 크기 계산
        size_bytes = self._calculate_size(value)

        # 메모리 제한 체크
        while (self.current_memory_bytes + size_bytes > self.max_memory_bytes or
               len(self.cache) >= self.max_size) and self.cache:
            # LRU 항목 제거
            self._evict_lru()

        # 새 엔트리 추가
        entry = CacheEntry(
            key=key,
            value=value,
            level=CacheLevel.L1_MEMORY,
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            access_count=0,
            ttl=ttl,
            size_bytes=size_bytes,
            metadata=metadata or {}
        )

        self.cache[key] = entry
        self.current_memory_bytes += size_bytes

    def _evict_lru(self):
        """LRU 항목 제거"""
        if self.cache:
            key, entry = self.cache.popitem(last=False)
            self.current_memory_bytes -= entry.size_bytes
            self.stats["evictions"] += 1
            logger.debug(f"Evicted cache entry: {key}")

    def _calculate_size(self, value: Any) -> int:
        """객체 크기 계산"""
        try:
            return len(pickle.dumps(value))
        except:
            return 1024  # 기본값 1KB

    def clear(self):
        """캐시 클리어"""
        self.cache.clear()
        self.current_memory_bytes = 0

    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        total = self.stats["hits"] + self.stats["misses"]
        return {
            **self.stats,
            "size": len(self.cache),
            "memory_usage_mb": self.current_memory_bytes / (1024 * 1024),
            "hit_rate": self.stats["hits"] / total * 100 if total > 0 else 0
        }


class SQLiteMemoryCache:
    """
    SQLite 기반 메모리 캐시 (L2)
    """

    def __init__(self, db_path: str = ":memory:", table_name: str = "cache"):
        """
        Initialize SQLiteMemoryCache

        Args:
            db_path: SQLite DB 경로 (":memory:"는 메모리 DB)
            table_name: 캐시 테이블명
        """
        self.db_path = db_path
        self.table_name = table_name
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_table()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "writes": 0
        }

    def _init_table(self):
        """테이블 초기화"""
        self.conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                key TEXT PRIMARY KEY,
                value BLOB,
                created_at REAL,
                accessed_at REAL,
                access_count INTEGER,
                ttl INTEGER,
                size_bytes INTEGER,
                metadata TEXT
            )
        """)
        self.conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{self.table_name}_accessed
            ON {self.table_name}(accessed_at)
        """)
        self.conn.commit()

    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        cursor = self.conn.execute(
            f"SELECT value, created_at, ttl FROM {self.table_name} WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()

        if not row:
            self.stats["misses"] += 1
            return None

        value_blob, created_at, ttl = row

        # 만료 체크
        if ttl > 0 and (time.time() - created_at) > ttl:
            self.conn.execute(f"DELETE FROM {self.table_name} WHERE key = ?", (key,))
            self.conn.commit()
            self.stats["misses"] += 1
            return None

        # 접근 정보 업데이트
        self.conn.execute(
            f"""UPDATE {self.table_name}
            SET accessed_at = ?, access_count = access_count + 1
            WHERE key = ?""",
            (time.time(), key)
        )
        self.conn.commit()

        self.stats["hits"] += 1
        return pickle.loads(value_blob)

    async def put(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
        metadata: Optional[Dict] = None
    ):
        """캐시에 값 저장"""
        value_blob = pickle.dumps(value)
        size_bytes = len(value_blob)
        metadata_json = json.dumps(metadata or {})
        now = time.time()

        self.conn.execute(
            f"""INSERT OR REPLACE INTO {self.table_name}
            (key, value, created_at, accessed_at, access_count, ttl, size_bytes, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (key, value_blob, now, now, 0, ttl, size_bytes, metadata_json)
        )
        self.conn.commit()
        self.stats["writes"] += 1

    async def delete(self, key: str):
        """캐시 항목 삭제"""
        self.conn.execute(f"DELETE FROM {self.table_name} WHERE key = ?", (key,))
        self.conn.commit()

    async def clear_expired(self):
        """만료된 항목 정리"""
        now = time.time()
        self.conn.execute(
            f"""DELETE FROM {self.table_name}
            WHERE ttl > 0 AND (? - created_at) > ttl""",
            (now,)
        )
        self.conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        cursor = self.conn.execute(
            f"""SELECT COUNT(*), SUM(size_bytes), AVG(access_count)
            FROM {self.table_name}"""
        )
        count, total_size, avg_access = cursor.fetchone()

        total = self.stats["hits"] + self.stats["misses"]
        return {
            **self.stats,
            "size": count or 0,
            "total_size_mb": (total_size or 0) / (1024 * 1024),
            "avg_access_count": avg_access or 0,
            "hit_rate": self.stats["hits"] / total * 100 if total > 0 else 0
        }

    def close(self):
        """연결 종료"""
        self.conn.close()


class MultiLevelCache:
    """
    다단계 캐싱 시스템
    - L1: 메모리 (LRU)
    - L2: SQLite
    - L3: Redis (추후 구현)
    """

    def __init__(
        self,
        l1_max_size: int = 100,
        l1_max_memory_mb: int = 50,
        l2_db_path: str = ":memory:",
        enable_l3: bool = False,
        default_ttl: int = 300
    ):
        """
        Initialize MultiLevelCache

        Args:
            l1_max_size: L1 캐시 최대 크기
            l1_max_memory_mb: L1 캐시 최대 메모리
            l2_db_path: L2 SQLite DB 경로
            enable_l3: L3 Redis 활성화
            default_ttl: 기본 TTL (초)
        """
        self.l1_cache = LRUCache(l1_max_size, l1_max_memory_mb)
        self.l2_cache = SQLiteMemoryCache(l2_db_path)
        self.l3_cache = None  # Redis 추후 구현
        self.enable_l3 = enable_l3
        self.default_ttl = default_ttl

        self.stats = {
            "total_requests": 0,
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "misses": 0,
            "writes": 0
        }

        # 백그라운드 정리 태스크
        self._cleanup_task = None
        self._start_cleanup_task()

        logger.info("MultiLevelCache initialized")

    def _start_cleanup_task(self):
        """백그라운드 정리 태스크 시작"""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(300)  # 5분마다
                    await self.l2_cache.clear_expired()
                    logger.debug("Cleared expired cache entries")
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in cache cleanup: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    def _generate_key(self, *args, **kwargs) -> str:
        """캐시 키 생성"""
        key_data = {
            "args": args,
            "kwargs": kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def get(
        self,
        key: str,
        fetch_func: Optional[callable] = None,
        ttl: Optional[int] = None
    ) -> Optional[Any]:
        """
        캐시에서 값 가져오기

        Args:
            key: 캐시 키
            fetch_func: 캐시 미스 시 실행할 함수
            ttl: TTL (초)

        Returns:
            캐시된 값 또는 None
        """
        self.stats["total_requests"] += 1
        ttl = ttl or self.default_ttl

        # L1 체크
        value = self.l1_cache.get(key)
        if value is not None:
            self.stats["l1_hits"] += 1
            logger.debug(f"L1 cache hit: {key}")
            return value

        # L2 체크
        value = await self.l2_cache.get(key)
        if value is not None:
            self.stats["l2_hits"] += 1
            # L1로 승격
            self.l1_cache.put(key, value, ttl)
            logger.debug(f"L2 cache hit: {key}")
            return value

        # L3 체크 (Redis - 추후 구현)
        if self.enable_l3 and self.l3_cache:
            # value = await self.l3_cache.get(key)
            # if value is not None:
            #     self.stats["l3_hits"] += 1
            #     # L1, L2로 승격
            #     await self._promote_to_upper_levels(key, value, ttl)
            #     return value
            pass

        # 캐시 미스
        self.stats["misses"] += 1
        logger.debug(f"Cache miss: {key}")

        # fetch_func 실행
        if fetch_func:
            try:
                if asyncio.iscoroutinefunction(fetch_func):
                    value = await fetch_func()
                else:
                    value = fetch_func()

                if value is not None:
                    await self.put(key, value, ttl)
                    return value
            except Exception as e:
                logger.error(f"Error fetching value for key {key}: {e}")

        return None

    async def put(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict] = None
    ):
        """
        모든 레벨에 값 저장

        Args:
            key: 캐시 키
            value: 저장할 값
            ttl: TTL (초)
            metadata: 메타데이터
        """
        ttl = ttl or self.default_ttl
        self.stats["writes"] += 1

        # L1에 저장
        self.l1_cache.put(key, value, ttl, metadata)

        # L2에 저장 (비동기)
        await self.l2_cache.put(key, value, ttl, metadata)

        # L3에 저장 (Redis - 추후 구현)
        if self.enable_l3 and self.l3_cache:
            # await self.l3_cache.put(key, value, ttl, metadata)
            pass

        logger.debug(f"Cached value for key: {key}")

    async def invalidate(self, key: str):
        """
        캐시 무효화

        Args:
            key: 캐시 키
        """
        # L1에서 제거
        if key in self.l1_cache.cache:
            del self.l1_cache.cache[key]

        # L2에서 제거
        await self.l2_cache.delete(key)

        # L3에서 제거 (Redis - 추후 구현)
        if self.enable_l3 and self.l3_cache:
            # await self.l3_cache.delete(key)
            pass

        logger.debug(f"Invalidated cache for key: {key}")

    async def invalidate_pattern(self, pattern: str):
        """
        패턴 기반 캐시 무효화

        Args:
            pattern: 키 패턴 (예: "user_*")
        """
        import re
        regex = re.compile(pattern.replace("*", ".*"))

        # L1 무효화
        keys_to_remove = [k for k in self.l1_cache.cache if regex.match(k)]
        for key in keys_to_remove:
            del self.l1_cache.cache[key]

        # L2 무효화 (전체 스캔 필요)
        # 실제 구현시 더 효율적인 방법 고려
        logger.info(f"Invalidated {len(keys_to_remove)} cache entries matching pattern: {pattern}")

    def cached(self, ttl: Optional[int] = None):
        """
        함수 데코레이터

        Usage:
            @cache.cached(ttl=600)
            async def expensive_function(param1, param2):
                # ... expensive computation
                return result
        """
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # 캐시 키 생성
                cache_key = f"{func.__module__}.{func.__name__}_{self._generate_key(*args, **kwargs)}"

                # 캐시에서 찾기
                result = await self.get(cache_key)
                if result is not None:
                    return result

                # 함수 실행
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # 캐시에 저장
                await self.put(cache_key, result, ttl or self.default_ttl)
                return result

            return wrapper
        return decorator

    def get_stats(self) -> Dict[str, Any]:
        """전체 통계 반환"""
        total = self.stats["total_requests"]
        total_hits = (
            self.stats["l1_hits"] +
            self.stats["l2_hits"] +
            self.stats["l3_hits"]
        )

        return {
            **self.stats,
            "l1_stats": self.l1_cache.get_stats(),
            "l2_stats": self.l2_cache.get_stats(),
            "overall_hit_rate": total_hits / total * 100 if total > 0 else 0,
            "l1_hit_rate": self.stats["l1_hits"] / total * 100 if total > 0 else 0,
            "l2_hit_rate": self.stats["l2_hits"] / total * 100 if total > 0 else 0
        }

    async def warmup(self, keys_and_funcs: List[Tuple[str, callable]]):
        """
        캐시 워밍업

        Args:
            keys_and_funcs: (키, 함수) 튜플 리스트
        """
        for key, func in keys_and_funcs:
            await self.get(key, func)
        logger.info(f"Cache warmed up with {len(keys_and_funcs)} entries")

    async def close(self):
        """리소스 정리"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        self.l2_cache.close()
        if self.l3_cache:
            # await self.l3_cache.close()
            pass


# 전역 캐시 인스턴스
_global_cache: Optional[MultiLevelCache] = None


def get_multi_level_cache() -> MultiLevelCache:
    """전역 다단계 캐시 인스턴스 반환"""
    global _global_cache
    if _global_cache is None:
        _global_cache = MultiLevelCache()
    return _global_cache