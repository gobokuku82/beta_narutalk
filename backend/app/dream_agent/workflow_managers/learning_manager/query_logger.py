"""Query Logger

쿼리 패턴 로깅

Status: planned — Sprint 15 wiring 예정. 현 프로덕션 적용처 0 (학습 페어 미수집 중).
선행 조건: wiring 전 date.replace(day=...) 월경계 버그 수정 (2026-06-11 재분석 검증).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class QueryLog(BaseModel):
    """쿼리 로그 모델"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    query: str
    language: str = "ko"
    intent_domain: Optional[str] = None
    intent_category: Optional[str] = None
    entities: list[dict[str, Any]] = Field(default_factory=list)
    response_format: Optional[str] = None
    success: bool = True
    user_satisfaction: Optional[int] = None  # 1-5
    metadata: dict[str, Any] = Field(default_factory=dict)


class QueryLogger:
    """쿼리 로거

    사용자 쿼리 패턴 로깅
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        buffer_size: int = 50,
    ):
        self.output_dir = output_dir or Path("logs/queries")
        self.buffer_size = buffer_size
        self._buffer: list[QueryLog] = []

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        query: str,
        session_id: Optional[str] = None,
        language: str = "ko",
        intent_domain: Optional[str] = None,
        intent_category: Optional[str] = None,
        entities: Optional[list[dict[str, Any]]] = None,
        response_format: Optional[str] = None,
        success: bool = True,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """쿼리 로그 기록

        Args:
            query: 사용자 쿼리
            session_id: 세션 ID
            language: 언어
            intent_domain: 의도 도메인
            intent_category: 의도 카테고리
            entities: 추출된 엔티티
            response_format: 응답 포맷
            success: 성공 여부
            metadata: 추가 메타데이터
        """
        query_log = QueryLog(
            query=query,
            session_id=session_id,
            language=language,
            intent_domain=intent_domain,
            intent_category=intent_category,
            entities=entities or [],
            response_format=response_format,
            success=success,
            metadata=metadata or {},
        )

        self._buffer.append(query_log)

        if len(self._buffer) >= self.buffer_size:
            self.flush()

        logger.debug(
            "Query logged",
            query_length=len(query),
            intent_domain=intent_domain,
        )

    def flush(self) -> None:
        """버퍼 내용을 파일에 기록"""
        if not self._buffer:
            return

        today = datetime.utcnow().strftime("%Y-%m-%d")
        output_file = self.output_dir / f"query_{today}.jsonl"

        try:
            with open(output_file, "a", encoding="utf-8") as f:
                for query_log in self._buffer:
                    line = query_log.model_dump_json()
                    f.write(line + "\n")

            logger.debug(
                "Query buffer flushed",
                count=len(self._buffer),
            )

        except Exception as e:
            logger.error("Failed to flush query buffer", error=str(e))

        finally:
            self._buffer.clear()

    def get_popular_queries(
        self,
        limit: int = 10,
        days: int = 7,
    ) -> list[dict[str, Any]]:
        """인기 쿼리 조회

        Args:
            limit: 최대 조회 수
            days: 조회 기간 (일)

        Returns:
            인기 쿼리 목록 [{query, count, last_seen}]
        """
        query_counts: dict[str, dict[str, Any]] = {}

        # 파일에서 조회
        for days_ago in range(days):
            date = datetime.utcnow()
            date = date.replace(
                day=date.day - days_ago if date.day > days_ago else 1
            )
            date_str = date.strftime("%Y-%m-%d")
            query_file = self.output_dir / f"query_{date_str}.jsonl"

            if not query_file.exists():
                continue

            try:
                with open(query_file, "r", encoding="utf-8") as f:
                    for line in f:
                        data = json.loads(line)
                        query = data.get("query", "")
                        normalized = query.strip().lower()

                        if normalized not in query_counts:
                            query_counts[normalized] = {
                                "query": query,
                                "count": 0,
                                "last_seen": data.get("timestamp"),
                            }

                        query_counts[normalized]["count"] += 1

            except Exception as e:
                logger.error("Failed to read query file", error=str(e))

        # 정렬 및 반환
        sorted_queries = sorted(
            query_counts.values(),
            key=lambda x: x["count"],
            reverse=True,
        )

        return sorted_queries[:limit]

    def get_intent_distribution(
        self,
        days: int = 7,
    ) -> dict[str, int]:
        """의도 분포 조회

        Args:
            days: 조회 기간 (일)

        Returns:
            의도별 카운트 {domain: count}
        """
        distribution: dict[str, int] = {}

        for days_ago in range(days):
            date = datetime.utcnow()
            date = date.replace(
                day=date.day - days_ago if date.day > days_ago else 1
            )
            date_str = date.strftime("%Y-%m-%d")
            query_file = self.output_dir / f"query_{date_str}.jsonl"

            if not query_file.exists():
                continue

            try:
                with open(query_file, "r", encoding="utf-8") as f:
                    for line in f:
                        data = json.loads(line)
                        domain = data.get("intent_domain", "unknown")
                        distribution[domain] = distribution.get(domain, 0) + 1

            except Exception as e:
                logger.error("Failed to read query file", error=str(e))

        return distribution

    def __del__(self) -> None:
        """소멸자 - 버퍼 flush"""
        self.flush()


# 싱글톤
_query_logger: Optional[QueryLogger] = None


def get_query_logger() -> QueryLogger:
    """QueryLogger 싱글톤 반환"""
    global _query_logger
    if _query_logger is None:
        _query_logger = QueryLogger()
    return _query_logger
