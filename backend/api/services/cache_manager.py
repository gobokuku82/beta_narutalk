"""
SQLite Memory Cache Manager
SQLite 메모리 모드를 활용한 고성능 캐싱 시스템
"""

import sqlite3
import json
import time
import hashlib
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import asyncio
import pickle

logger = logging.getLogger(__name__)


class SQLiteMemoryCache:
    """
    SQLite 메모리 기반 캐시 매니저
    - TTL 지원
    - 패턴 매칭 무효화
    - 통계 수집
    """

    def __init__(self, default_ttl: int = 300, max_size: int = 10000):
        """
        Initialize SQLite memory cache

        Args:
            default_ttl: 기본 TTL (초)
            max_size: 최대 캐시 항목 수
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.conn = None
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0
        }

        # 초기화
        self._init_connection()
        self._init_schema()

        # 정리 작업 스케줄링
        self.cleanup_task = None
        self._start_cleanup_task()

    def _init_connection(self):
        """SQLite 메모리 연결 초기화"""
        self.conn = sqlite3.connect(':memory:', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")

    def _init_schema(self):
        """캐시 테이블 스키마 생성"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value BLOB,
                created_at REAL,
                expires_at REAL,
                hit_count INTEGER DEFAULT 0,
                last_accessed REAL,
                size INTEGER
            )
        """)

        # 인덱스 생성
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_accessed ON cache(last_accessed)")

        # 메타데이터 테이블
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_metadata (
                total_hits INTEGER DEFAULT 0,
                total_misses INTEGER DEFAULT 0,
                total_sets INTEGER DEFAULT 0,
                total_evictions INTEGER DEFAULT 0,
                created_at REAL
            )
        """)

        # 초기 메타데이터
        self.conn.execute("""
            INSERT INTO cache_metadata (created_at)
            VALUES (?)
        """, (time.time(),))

        self.conn.commit()

    def _get_cache_key(self, key: str) -> str:
        """캐시 키 해싱"""
        if len(key) > 250:  # SQLite 키 길이 제한
            return hashlib.sha256(key.encode()).hexdigest()
        return key

    def _serialize(self, value: Any) -> bytes:
        """값 직렬화"""
        try:
            # JSON으로 시도
            return json.dumps(value).encode('utf-8')
        except (TypeError, ValueError):
            # 실패시 pickle 사용
            return pickle.dumps(value)

    def _deserialize(self, data: bytes) -> Any:
        """값 역직렬화"""
        try:
            # JSON으로 시도
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # 실패시 pickle 사용
            return pickle.loads(data)

    async def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값 조회

        Args:
            key: 캐시 키

        Returns:
            캐시된 값 또는 None
        """
        cache_key = self._get_cache_key(key)
        current_time = time.time()

        try:
            cursor = self.conn.execute("""
                SELECT value, expires_at, hit_count
                FROM cache
                WHERE key = ? AND expires_at > ?
            """, (cache_key, current_time))

            row = cursor.fetchone()

            if row:
                # 히트 카운트 및 최근 접근 시간 업데이트
                self.conn.execute("""
                    UPDATE cache
                    SET hit_count = hit_count + 1,
                        last_accessed = ?
                    WHERE key = ?
                """, (current_time, cache_key))

                self.stats["hits"] += 1
                logger.debug(f"Cache hit for key: {key[:50]}...")

                return self._deserialize(row['value'])
            else:
                self.stats["misses"] += 1
                logger.debug(f"Cache miss for key: {key[:50]}...")
                return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        캐시에 값 저장

        Args:
            key: 캐시 키
            value: 저장할 값
            ttl: TTL (초)

        Returns:
            성공 여부
        """
        cache_key = self._get_cache_key(key)
        current_time = time.time()
        ttl = ttl or self.default_ttl
        expires_at = current_time + ttl

        try:
            serialized = self._serialize(value)
            size = len(serialized)

            # 크기 제한 체크
            await self._ensure_capacity(size)

            # UPSERT
            self.conn.execute("""
                INSERT OR REPLACE INTO cache
                (key, value, created_at, expires_at, hit_count, last_accessed, size)
                VALUES (?, ?, ?, ?, 0, ?, ?)
            """, (cache_key, serialized, current_time, expires_at, current_time, size))

            self.conn.commit()
            self.stats["sets"] += 1

            logger.debug(f"Cache set for key: {key[:50]}... (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """캐시에서 키 삭제"""
        cache_key = self._get_cache_key(key)

        try:
            cursor = self.conn.execute("""
                DELETE FROM cache WHERE key = ?
            """, (cache_key,))

            self.conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def invalidate(self, pattern: str) -> int:
        """
        패턴 매칭으로 캐시 무효화

        Args:
            pattern: SQL LIKE 패턴 (예: 'user_%')

        Returns:
            삭제된 항목 수
        """
        try:
            cursor = self.conn.execute("""
                DELETE FROM cache WHERE key LIKE ?
            """, (pattern,))

            self.conn.commit()
            deleted = cursor.rowcount

            if deleted > 0:
                logger.info(f"Invalidated {deleted} cache entries with pattern: {pattern}")

            return deleted

        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
            return 0

    async def _ensure_capacity(self, required_size: int):
        """캐시 용량 확보"""
        cursor = self.conn.execute("""
            SELECT COUNT(*) as count, SUM(size) as total_size
            FROM cache
        """)

        row = cursor.fetchone()
        count = row['count'] or 0

        # 항목 수 제한 체크
        if count >= self.max_size:
            # LRU 방식으로 오래된 항목 제거
            deleted = self.conn.execute("""
                DELETE FROM cache
                WHERE key IN (
                    SELECT key FROM cache
                    ORDER BY last_accessed ASC
                    LIMIT ?
                )
            """, (max(1, count - self.max_size + 1),))

            self.stats["evictions"] += deleted.rowcount
            logger.info(f"Evicted {deleted.rowcount} cache entries (LRU)")

    async def cleanup(self):
        """만료된 캐시 항목 정리"""
        try:
            current_time = time.time()
            cursor = self.conn.execute("""
                DELETE FROM cache WHERE expires_at <= ?
            """, (current_time,))

            self.conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"Cleaned up {cursor.rowcount} expired cache entries")

        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")

    def _start_cleanup_task(self):
        """정리 작업 스케줄링"""
        async def cleanup_loop():
            while True:
                await asyncio.sleep(60)  # 1분마다
                await self.cleanup()

        # 이벤트 루프가 있으면 태스크 생성
        try:
            loop = asyncio.get_event_loop()
            self.cleanup_task = loop.create_task(cleanup_loop())
        except RuntimeError:
            # 이벤트 루프가 없으면 패스
            pass

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        cursor = self.conn.execute("""
            SELECT
                COUNT(*) as total_entries,
                SUM(size) as total_size,
                SUM(hit_count) as total_hits,
                AVG(hit_count) as avg_hits,
                MIN(created_at) as oldest_entry,
                MAX(created_at) as newest_entry
            FROM cache
        """)

        row = cursor.fetchone()

        hit_rate = 0
        if self.stats["hits"] + self.stats["misses"] > 0:
            hit_rate = self.stats["hits"] / (self.stats["hits"] + self.stats["misses"]) * 100

        return {
            "total_entries": row['total_entries'] or 0,
            "total_size": row['total_size'] or 0,
            "total_hits": self.stats["hits"],
            "total_misses": self.stats["misses"],
            "total_sets": self.stats["sets"],
            "total_evictions": self.stats["evictions"],
            "hit_rate": f"{hit_rate:.2f}%",
            "avg_hits_per_entry": row['avg_hits'] or 0,
            "oldest_entry_age": time.time() - (row['oldest_entry'] or time.time()),
            "newest_entry_age": time.time() - (row['newest_entry'] or time.time())
        }

    def clear(self):
        """캐시 전체 초기화"""
        try:
            self.conn.execute("DELETE FROM cache")
            self.conn.commit()

            # 통계 리셋
            self.stats = {
                "hits": 0,
                "misses": 0,
                "sets": 0,
                "evictions": 0
            }

            logger.info("Cache cleared")

        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    def close(self):
        """캐시 종료"""
        if self.cleanup_task:
            self.cleanup_task.cancel()

        if self.conn:
            self.conn.close()

        logger.info("Cache closed")

    async def __aenter__(self):
        """컨텍스트 매니저 진입"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.close()


# 싱글톤 인스턴스
_cache_instance = None

def get_cache() -> SQLiteMemoryCache:
    """캐시 인스턴스 반환 (싱글톤)"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SQLiteMemoryCache()
    return _cache_instance


# 사용 예시
async def example_usage():
    """캐시 사용 예시"""
    cache = get_cache()

    # 값 저장
    await cache.set("user:123", {"name": "김철수", "dept": "영업1팀"}, ttl=600)

    # 값 조회
    user = await cache.get("user:123")
    print(f"User: {user}")

    # 패턴 무효화
    await cache.invalidate("user:%")

    # 통계 확인
    stats = cache.get_stats()
    print(f"Cache stats: {stats}")


if __name__ == "__main__":
    asyncio.run(example_usage())