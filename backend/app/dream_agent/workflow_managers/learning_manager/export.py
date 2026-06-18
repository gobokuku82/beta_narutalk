"""Learning Data Export

학습 데이터 JSONL 익스포트

Status: planned — Sprint 15 wiring 예정. 수집기 미배선이라 export 대상도 현재 0.

Reference: docs/specs/LEARNING_SPEC.md
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Literal, Optional

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class ExportConfig(BaseModel):
    """익스포트 설정"""

    output_dir: Path = Path("exports")
    format: Literal["jsonl", "json"] = "jsonl"
    include_metadata: bool = True
    max_records: Optional[int] = None


class LearningDataExporter:
    """학습 데이터 익스포터

    트레이스, 쿼리, 피드백 데이터를 학습용 포맷으로 익스포트
    """

    def __init__(
        self,
        trace_dir: Optional[Path] = None,
        query_dir: Optional[Path] = None,
        feedback_dir: Optional[Path] = None,
    ):
        self.trace_dir = trace_dir or Path("logs/traces")
        self.query_dir = query_dir or Path("logs/queries")
        self.feedback_dir = feedback_dir or Path("logs/feedback")

    def export_traces(
        self,
        config: ExportConfig,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Path:
        """트레이스 데이터 익스포트

        Args:
            config: 익스포트 설정
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            출력 파일 경로
        """
        config.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = config.output_dir / f"traces_{timestamp}.jsonl"

        count = 0
        with open(output_file, "w", encoding="utf-8") as f:
            for record in self._read_trace_files(start_date, end_date):
                if config.max_records and count >= config.max_records:
                    break

                if not config.include_metadata:
                    record.pop("metadata", None)

                f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
                count += 1

        logger.info("Traces exported", count=count, file=str(output_file))
        return output_file

    def export_queries(
        self,
        config: ExportConfig,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Path:
        """쿼리 데이터 익스포트

        Args:
            config: 익스포트 설정
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            출력 파일 경로
        """
        config.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = config.output_dir / f"queries_{timestamp}.jsonl"

        count = 0
        with open(output_file, "w", encoding="utf-8") as f:
            for record in self._read_query_files(start_date, end_date):
                if config.max_records and count >= config.max_records:
                    break

                if not config.include_metadata:
                    record.pop("metadata", None)

                f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
                count += 1

        logger.info("Queries exported", count=count, file=str(output_file))
        return output_file

    def export_feedback(
        self,
        config: ExportConfig,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Path:
        """피드백 데이터 익스포트

        Args:
            config: 익스포트 설정
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            출력 파일 경로
        """
        config.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = config.output_dir / f"feedback_{timestamp}.jsonl"

        count = 0
        with open(output_file, "w", encoding="utf-8") as f:
            for record in self._read_feedback_files(start_date, end_date):
                if config.max_records and count >= config.max_records:
                    break

                if not config.include_metadata:
                    record.pop("context", None)

                f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
                count += 1

        logger.info("Feedback exported", count=count, file=str(output_file))
        return output_file

    def export_training_pairs(
        self,
        config: ExportConfig,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Path:
        """학습용 입출력 쌍 익스포트

        쿼리-응답-피드백을 결합하여 SFT/RLHF용 데이터 생성

        Args:
            config: 익스포트 설정
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            출력 파일 경로
        """
        config.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = config.output_dir / f"training_pairs_{timestamp}.jsonl"

        # 피드백 데이터를 세션별로 그룹화
        feedback_by_session: dict[str, list[dict]] = {}
        for record in self._read_feedback_files(start_date, end_date):
            session_id = record.get("session_id")
            if session_id:
                if session_id not in feedback_by_session:
                    feedback_by_session[session_id] = []
                feedback_by_session[session_id].append(record)

        count = 0
        with open(output_file, "w", encoding="utf-8") as f:
            for feedback_list in feedback_by_session.values():
                if config.max_records and count >= config.max_records:
                    break

                for feedback in feedback_list:
                    training_pair = self._create_training_pair(feedback)
                    if training_pair:
                        f.write(
                            json.dumps(training_pair, ensure_ascii=False, default=str)
                            + "\n"
                        )
                        count += 1

        logger.info("Training pairs exported", count=count, file=str(output_file))
        return output_file

    def _create_training_pair(self, feedback: dict[str, Any]) -> Optional[dict[str, Any]]:
        """피드백에서 학습용 쌍 생성"""
        feedback_type = feedback.get("feedback_type")

        if feedback_type == "correction":
            return {
                "input": feedback.get("query", ""),
                "output": feedback.get("correction", ""),
                "original_output": feedback.get("response", ""),
                "type": "correction",
            }

        elif feedback_type == "preference":
            return {
                "input": feedback.get("query", ""),
                "output": feedback.get("preferred_response", ""),
                "rejected_output": feedback.get("response", ""),
                "type": "preference",
            }

        elif feedback_type == "rating":
            rating = feedback.get("rating", 0)
            if rating >= 4:  # 높은 평점만 positive sample로
                return {
                    "input": feedback.get("query", ""),
                    "output": feedback.get("response", ""),
                    "rating": rating,
                    "type": "positive",
                }

        return None

    def _read_trace_files(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> Iterator[dict[str, Any]]:
        """트레이스 파일 읽기"""
        yield from self._read_jsonl_files(
            self.trace_dir, "trace_", start_date, end_date
        )

    def _read_query_files(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> Iterator[dict[str, Any]]:
        """쿼리 파일 읽기"""
        yield from self._read_jsonl_files(
            self.query_dir, "query_", start_date, end_date
        )

    def _read_feedback_files(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> Iterator[dict[str, Any]]:
        """피드백 파일 읽기"""
        yield from self._read_jsonl_files(
            self.feedback_dir, "feedback_", start_date, end_date
        )

    def _read_jsonl_files(
        self,
        directory: Path,
        prefix: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> Iterator[dict[str, Any]]:
        """JSONL 파일들 읽기"""
        if not directory.exists():
            return

        for file_path in sorted(directory.glob(f"{prefix}*.jsonl")):
            try:
                # 파일명에서 날짜 추출
                date_str = file_path.stem.replace(prefix, "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                # 날짜 필터링
                if start_date and file_date < start_date:
                    continue
                if end_date and file_date > end_date:
                    continue

                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            continue

            except Exception as e:
                logger.error("Failed to read file", file=str(file_path), error=str(e))


def get_exporter() -> LearningDataExporter:
    """LearningDataExporter 인스턴스 반환"""
    return LearningDataExporter()
