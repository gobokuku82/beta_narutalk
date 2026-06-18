"""Trace Logger

실행 트레이스 로깅

Status: planned — Sprint 15 wiring 예정. 현 프로덕션 적용처 0 (학습 페어 미수집 중).
선행 조건: wiring 전 date.replace(day=...) 월경계 버그 수정 (2026-06-11 재분석 검증).

Reference: docs/specs/LEARNING_SPEC.md
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TraceLog(BaseModel):
    """트레이스 로그 모델"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    layer: str
    action: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float
    success: bool
    error: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TraceLogger:
    """트레이스 로거

    실행 정보를 파일/DB에 기록
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        buffer_size: int = 100,
    ):
        self.output_dir = output_dir or Path("logs/traces")
        self.buffer_size = buffer_size
        self._buffer: list[TraceLog] = []
        self._current_session_id: Optional[str] = None

        # 출력 디렉토리 생성
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def set_session(self, session_id: str) -> None:
        """세션 ID 설정"""
        self._current_session_id = session_id

    def log(
        self,
        layer: str,
        action: str,
        input_data: Optional[dict[str, Any]] = None,
        output_data: Optional[dict[str, Any]] = None,
        duration_ms: float = 0.0,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """트레이스 로그 기록

        Args:
            layer: 레이어 이름
            action: 액션 이름
            input_data: 입력 데이터
            output_data: 출력 데이터
            duration_ms: 실행 시간 (ms)
            success: 성공 여부
            error: 에러 메시지
            metadata: 추가 메타데이터
        """
        trace = TraceLog(
            session_id=self._current_session_id,
            layer=layer,
            action=action,
            input_data=input_data or {},
            output_data=output_data or {},
            duration_ms=duration_ms,
            success=success,
            error=error,
            metadata=metadata or {},
        )

        self._buffer.append(trace)

        # 버퍼가 가득 차면 flush
        if len(self._buffer) >= self.buffer_size:
            self.flush()

        # 디버그 로깅
        logger.debug(
            "Trace logged",
            layer=layer,
            action=action,
            duration_ms=round(duration_ms, 2),
            success=success,
        )

    def flush(self) -> None:
        """버퍼 내용을 파일에 기록"""
        if not self._buffer:
            return

        # 날짜별 파일
        today = datetime.utcnow().strftime("%Y-%m-%d")
        output_file = self.output_dir / f"trace_{today}.jsonl"

        try:
            with open(output_file, "a", encoding="utf-8") as f:
                for trace in self._buffer:
                    line = trace.model_dump_json()
                    f.write(line + "\n")

            logger.debug(
                "Trace buffer flushed",
                count=len(self._buffer),
                file=str(output_file),
            )

        except Exception as e:
            logger.error("Failed to flush trace buffer", error=str(e))

        finally:
            self._buffer.clear()

    def get_session_traces(
        self,
        session_id: str,
        limit: int = 100,
    ) -> list[TraceLog]:
        """세션의 트레이스 조회

        Args:
            session_id: 세션 ID
            limit: 최대 조회 수

        Returns:
            트레이스 목록
        """
        traces: list[TraceLog] = []

        # 버퍼에서 조회
        for trace in self._buffer:
            if trace.session_id == session_id:
                traces.append(trace)
                if len(traces) >= limit:
                    return traces

        # 파일에서 조회 (최근 7일)
        for days_ago in range(7):
            date = datetime.utcnow()
            date = date.replace(
                day=date.day - days_ago if date.day > days_ago else 1
            )
            date_str = date.strftime("%Y-%m-%d")
            trace_file = self.output_dir / f"trace_{date_str}.jsonl"

            if not trace_file.exists():
                continue

            try:
                with open(trace_file, "r", encoding="utf-8") as f:
                    for line in f:
                        data = json.loads(line)
                        if data.get("session_id") == session_id:
                            traces.append(TraceLog(**data))
                            if len(traces) >= limit:
                                return traces
            except Exception as e:
                logger.error("Failed to read trace file", error=str(e))

        return traces

    def get_layer_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict[str, dict[str, Any]]:
        """레이어별 통계

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            레이어별 통계 {layer: {count, avg_duration, success_rate}}
        """
        stats: dict[str, dict[str, Any]] = {}

        # 버퍼의 통계
        for trace in self._buffer:
            layer = trace.layer
            if layer not in stats:
                stats[layer] = {
                    "count": 0,
                    "total_duration": 0.0,
                    "success_count": 0,
                }

            stats[layer]["count"] += 1
            stats[layer]["total_duration"] += trace.duration_ms
            if trace.success:
                stats[layer]["success_count"] += 1

        # 통계 계산
        for layer, data in stats.items():
            count = data["count"]
            data["avg_duration_ms"] = (
                data["total_duration"] / count if count > 0 else 0
            )
            data["success_rate"] = (
                data["success_count"] / count if count > 0 else 0
            )
            del data["total_duration"]

        return stats

    def cleanup_old_files(self, days: int = 30) -> int:
        """오래된 트레이스 파일 삭제

        Args:
            days: 보관 일수

        Returns:
            삭제된 파일 수
        """
        deleted = 0
        cutoff = datetime.utcnow()
        cutoff = cutoff.replace(day=cutoff.day - days if cutoff.day > days else 1)

        for trace_file in self.output_dir.glob("trace_*.jsonl"):
            try:
                # 파일명에서 날짜 추출
                date_str = trace_file.stem.replace("trace_", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                if file_date < cutoff:
                    trace_file.unlink()
                    deleted += 1
                    logger.info("Old trace file deleted", file=trace_file.name)

            except Exception as e:
                logger.error(
                    "Failed to cleanup trace file",
                    file=trace_file.name,
                    error=str(e),
                )

        return deleted

    def __del__(self) -> None:
        """소멸자 - 버퍼 flush"""
        self.flush()


# 싱글톤
_trace_logger: Optional[TraceLogger] = None


def get_trace_logger() -> TraceLogger:
    """TraceLogger 싱글톤 반환"""
    global _trace_logger
    if _trace_logger is None:
        _trace_logger = TraceLogger()
    return _trace_logger
