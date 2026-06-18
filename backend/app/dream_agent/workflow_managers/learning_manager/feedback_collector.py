"""Feedback Collector

사용자 피드백 수집

Status: planned — Sprint 15 wiring 예정. 현 프로덕션 적용처 0 (학습 페어 미수집 중).
선행 조건: wiring 전 date.replace(day=...) 월경계 버그 수정 (2026-06-11 재분석 검증).

Reference: docs/specs/LEARNING_SPEC.md
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class FeedbackRecord(BaseModel):
    """피드백 레코드 모델"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    feedback_type: Literal["rating", "correction", "preference"]

    # 원본 데이터
    query: str
    response: str

    # 평가
    rating: Optional[int] = Field(None, ge=1, le=5)
    correction: Optional[str] = None
    preferred_response: Optional[str] = None

    # 메타
    context: dict[str, Any] = Field(default_factory=dict)


class FeedbackCollector:
    """피드백 수집기

    사용자 피드백 수집 및 저장
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        buffer_size: int = 20,
    ):
        self.output_dir = output_dir or Path("logs/feedback")
        self.buffer_size = buffer_size
        self._buffer: list[FeedbackRecord] = []

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def collect_rating(
        self,
        session_id: str,
        query: str,
        response: str,
        rating: int,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """평점 피드백 수집

        Args:
            session_id: 세션 ID
            query: 사용자 쿼리
            response: 시스템 응답
            rating: 평점 (1-5)
            context: 추가 컨텍스트
        """
        record = FeedbackRecord(
            session_id=session_id,
            feedback_type="rating",
            query=query,
            response=response,
            rating=rating,
            context=context or {},
        )

        self._add_record(record)
        logger.info("Rating feedback collected", session_id=session_id, rating=rating)

    def collect_correction(
        self,
        session_id: str,
        query: str,
        response: str,
        correction: str,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """정정 피드백 수집

        Args:
            session_id: 세션 ID
            query: 사용자 쿼리
            response: 시스템 응답
            correction: 사용자 정정
            context: 추가 컨텍스트
        """
        record = FeedbackRecord(
            session_id=session_id,
            feedback_type="correction",
            query=query,
            response=response,
            correction=correction,
            context=context or {},
        )

        self._add_record(record)
        logger.info("Correction feedback collected", session_id=session_id)

    def collect_preference(
        self,
        session_id: str,
        query: str,
        response: str,
        preferred_response: str,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """선호 응답 피드백 수집

        Args:
            session_id: 세션 ID
            query: 사용자 쿼리
            response: 시스템 응답
            preferred_response: 선호하는 응답
            context: 추가 컨텍스트
        """
        record = FeedbackRecord(
            session_id=session_id,
            feedback_type="preference",
            query=query,
            response=response,
            preferred_response=preferred_response,
            context=context or {},
        )

        self._add_record(record)
        logger.info("Preference feedback collected", session_id=session_id)

    def _add_record(self, record: FeedbackRecord) -> None:
        """레코드 추가"""
        self._buffer.append(record)

        if len(self._buffer) >= self.buffer_size:
            self.flush()

    def flush(self) -> None:
        """버퍼 내용을 파일에 기록"""
        if not self._buffer:
            return

        today = datetime.utcnow().strftime("%Y-%m-%d")
        output_file = self.output_dir / f"feedback_{today}.jsonl"

        try:
            with open(output_file, "a", encoding="utf-8") as f:
                for record in self._buffer:
                    line = record.model_dump_json()
                    f.write(line + "\n")

            logger.debug("Feedback buffer flushed", count=len(self._buffer))

        except Exception as e:
            logger.error("Failed to flush feedback buffer", error=str(e))

        finally:
            self._buffer.clear()

    def get_session_feedback(
        self,
        session_id: str,
    ) -> list[FeedbackRecord]:
        """세션의 피드백 조회

        Args:
            session_id: 세션 ID

        Returns:
            피드백 목록
        """
        records: list[FeedbackRecord] = []

        # 버퍼에서 조회
        for record in self._buffer:
            if record.session_id == session_id:
                records.append(record)

        # 파일에서 조회 (최근 7일)
        for days_ago in range(7):
            date = datetime.utcnow()
            date = date.replace(
                day=date.day - days_ago if date.day > days_ago else 1
            )
            date_str = date.strftime("%Y-%m-%d")
            feedback_file = self.output_dir / f"feedback_{date_str}.jsonl"

            if not feedback_file.exists():
                continue

            try:
                with open(feedback_file, "r", encoding="utf-8") as f:
                    for line in f:
                        data = json.loads(line)
                        if data.get("session_id") == session_id:
                            records.append(FeedbackRecord(**data))
            except Exception as e:
                logger.error("Failed to read feedback file", error=str(e))

        return records

    def get_average_rating(self, days: int = 7) -> float:
        """평균 평점 조회

        Args:
            days: 조회 기간 (일)

        Returns:
            평균 평점
        """
        ratings: list[int] = []

        for days_ago in range(days):
            date = datetime.utcnow()
            date = date.replace(
                day=date.day - days_ago if date.day > days_ago else 1
            )
            date_str = date.strftime("%Y-%m-%d")
            feedback_file = self.output_dir / f"feedback_{date_str}.jsonl"

            if not feedback_file.exists():
                continue

            try:
                with open(feedback_file, "r", encoding="utf-8") as f:
                    for line in f:
                        data = json.loads(line)
                        if data.get("feedback_type") == "rating":
                            rating = data.get("rating")
                            if rating:
                                ratings.append(rating)
            except Exception as e:
                logger.error("Failed to read feedback file", error=str(e))

        return sum(ratings) / len(ratings) if ratings else 0.0

    def __del__(self) -> None:
        """소멸자 - 버퍼 flush"""
        self.flush()


# 싱글톤
_feedback_collector: Optional[FeedbackCollector] = None


def get_feedback_collector() -> FeedbackCollector:
    """FeedbackCollector 싱글톤 반환"""
    global _feedback_collector
    if _feedback_collector is None:
        _feedback_collector = FeedbackCollector()
    return _feedback_collector
