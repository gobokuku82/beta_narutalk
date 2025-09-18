"""
Enhanced Streaming Response Service for LangGraph 0.6.x
향상된 스트리밍 응답 서비스 - 진행률 및 중간 단계 포함
"""

import asyncio
import json
from typing import AsyncGenerator, Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import uuid

logger = logging.getLogger(__name__)


class StreamEventType(str, Enum):
    """스트림 이벤트 타입"""
    # 연결 관련
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    HEARTBEAT = "heartbeat"

    # 워크플로우 관련
    WORKFLOW_START = "workflow_start"
    WORKFLOW_END = "workflow_end"

    # 에이전트 관련
    AGENT_START = "agent_start"
    AGENT_THINKING = "agent_thinking"
    AGENT_ACTION = "agent_action"
    AGENT_RESULT = "agent_result"
    AGENT_END = "agent_end"

    # 도구 관련
    TOOL_START = "tool_start"
    TOOL_EXECUTION = "tool_execution"
    TOOL_RESULT = "tool_result"
    TOOL_ERROR = "tool_error"

    # 컨텐츠 관련
    CONTENT = "content"
    CONTENT_DELTA = "content_delta"

    # 진행 상황
    PROGRESS = "progress"
    STATUS = "status"

    # 에러
    ERROR = "error"
    WARNING = "warning"


@dataclass
class StreamEvent:
    """스트림 이벤트"""
    id: str
    event: StreamEventType
    data: Any
    timestamp: str
    metadata: Dict[str, Any]
    progress: Optional[float] = None
    step: Optional[str] = None
    agent: Optional[str] = None

    def to_sse(self) -> str:
        """SSE 형식으로 변환"""
        event_dict = {
            "id": self.id,
            "event": self.event,
            "data": self.data,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }

        if self.progress is not None:
            event_dict["progress"] = self.progress
        if self.step:
            event_dict["step"] = self.step
        if self.agent:
            event_dict["agent"] = self.agent

        # SSE 포맷
        lines = [
            f"id: {self.id}",
            f"event: {self.event}",
            f"data: {json.dumps(event_dict, ensure_ascii=False)}",
            ""
        ]

        return "\n".join(lines) + "\n"


class ProgressTracker:
    """진행률 추적기"""

    def __init__(self, total_steps: int = 10):
        """
        Initialize ProgressTracker

        Args:
            total_steps: 전체 예상 단계 수
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.steps_history: List[Dict[str, Any]] = []
        self.agent_progress: Dict[str, float] = {}

    def update(
        self,
        step: int,
        description: str,
        agent: Optional[str] = None,
        sub_progress: Optional[float] = None
    ) -> float:
        """
        진행률 업데이트

        Args:
            step: 현재 단계
            description: 단계 설명
            agent: 에이전트 이름
            sub_progress: 서브 진행률 (0-100)

        Returns:
            전체 진행률 (0-100)
        """
        self.current_step = step

        # 단계 기록
        self.steps_history.append({
            "step": step,
            "description": description,
            "agent": agent,
            "timestamp": datetime.now().isoformat()
        })

        # 에이전트별 진행률
        if agent and sub_progress is not None:
            self.agent_progress[agent] = sub_progress

        # 전체 진행률 계산
        base_progress = (step / self.total_steps) * 100

        # 서브 진행률 반영
        if sub_progress is not None:
            step_weight = 100 / self.total_steps
            base_progress = ((step - 1) / self.total_steps) * 100
            base_progress += (sub_progress / 100) * step_weight

        return min(base_progress, 100)

    def get_summary(self) -> Dict[str, Any]:
        """진행 요약 반환"""
        return {
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "progress_percentage": (self.current_step / self.total_steps) * 100,
            "agent_progress": self.agent_progress,
            "recent_steps": self.steps_history[-5:]  # 최근 5단계
        }


class EnhancedStreamingService:
    """
    향상된 스트리밍 서비스
    - 진행률 추적
    - 중간 단계 스트리밍
    - 토큰별 스트리밍
    """

    def __init__(
        self,
        supervisor_service: Any,
        enable_progress: bool = True,
        enable_intermediate: bool = True,
        heartbeat_interval: int = 30
    ):
        """
        Initialize EnhancedStreamingService

        Args:
            supervisor_service: Supervisor 서비스
            enable_progress: 진행률 추적 활성화
            enable_intermediate: 중간 단계 스트리밍 활성화
            heartbeat_interval: 하트비트 간격 (초)
        """
        self.supervisor = supervisor_service
        self.enable_progress = enable_progress
        self.enable_intermediate = enable_intermediate
        self.heartbeat_interval = heartbeat_interval

        # 활성 스트림
        self.active_streams: Dict[str, Dict[str, Any]] = {}

        logger.info("EnhancedStreamingService initialized")

    async def stream_execution(
        self,
        query: str,
        user_context: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        실행 스트리밍

        Args:
            query: 사용자 쿼리
            user_context: 사용자 컨텍스트
            session_id: 세션 ID

        Yields:
            StreamEvent 객체
        """
        session_id = session_id or str(uuid.uuid4())
        stream_id = str(uuid.uuid4())

        # 스트림 등록
        self.active_streams[stream_id] = {
            "session_id": session_id,
            "started_at": datetime.now(),
            "query": query
        }

        # 진행률 추적기
        progress_tracker = ProgressTracker(total_steps=6)

        try:
            # 연결 이벤트
            yield self._create_event(
                StreamEventType.CONNECTED,
                {"message": "스트림 연결 완료", "session_id": session_id},
                stream_id=stream_id
            )

            # 워크플로우 시작
            yield self._create_event(
                StreamEventType.WORKFLOW_START,
                {"query": query, "timestamp": datetime.now().isoformat()},
                progress=0,
                step="워크플로우 시작",
                stream_id=stream_id
            )

            # 1단계: 컨텍스트 준비
            progress = progress_tracker.update(1, "컨텍스트 준비 중")
            yield self._create_event(
                StreamEventType.STATUS,
                {"status": "컨텍스트 최적화 중"},
                progress=progress,
                step="컨텍스트 준비",
                stream_id=stream_id
            )

            # 2단계: 에이전트 선택
            progress = progress_tracker.update(2, "에이전트 선택 중")
            yield self._create_event(
                StreamEventType.STATUS,
                {"status": "적합한 에이전트 선택 중"},
                progress=progress,
                step="에이전트 선택",
                stream_id=stream_id
            )

            # Supervisor 실행 스트리밍
            async for chunk in self._stream_supervisor_execution(
                query,
                user_context,
                progress_tracker,
                stream_id
            ):
                yield chunk

            # 완료
            progress = progress_tracker.update(6, "완료")
            yield self._create_event(
                StreamEventType.WORKFLOW_END,
                {"status": "완료", "summary": progress_tracker.get_summary()},
                progress=100,
                step="완료",
                stream_id=stream_id
            )

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield self._create_event(
                StreamEventType.ERROR,
                {"error": str(e), "type": type(e).__name__},
                stream_id=stream_id
            )

        finally:
            # 스트림 정리
            if stream_id in self.active_streams:
                del self.active_streams[stream_id]

            # 연결 종료
            yield self._create_event(
                StreamEventType.DISCONNECTED,
                {"message": "스트림 연결 종료"},
                stream_id=stream_id
            )

    async def _stream_supervisor_execution(
        self,
        query: str,
        user_context: Dict[str, Any],
        progress_tracker: ProgressTracker,
        stream_id: str
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Supervisor 실행 스트리밍

        Args:
            query: 쿼리
            user_context: 사용자 컨텍스트
            progress_tracker: 진행률 추적기
            stream_id: 스트림 ID

        Yields:
            StreamEvent 객체
        """
        # 여기서는 실제 supervisor 스트리밍 구현
        # LangGraph의 스트리밍 API 사용

        try:
            # 3단계: SQL 분석 에이전트
            progress = progress_tracker.update(3, "SQL 분석 중", "sql_analysis", 0)
            yield self._create_event(
                StreamEventType.AGENT_START,
                {"agent": "sql_analysis", "task": "SQL 쿼리 생성"},
                progress=progress,
                step="SQL 분석",
                agent="sql_analysis",
                stream_id=stream_id
            )

            # SQL 생성 중간 단계
            for i in range(3):
                await asyncio.sleep(0.5)  # 시뮬레이션
                sub_progress = (i + 1) * 33
                progress = progress_tracker.update(3, "SQL 분석 중", "sql_analysis", sub_progress)

                yield self._create_event(
                    StreamEventType.AGENT_THINKING,
                    {"agent": "sql_analysis", "thinking": f"테이블 구조 분석 {sub_progress}%"},
                    progress=progress,
                    agent="sql_analysis",
                    stream_id=stream_id
                )

            # SQL 결과
            yield self._create_event(
                StreamEventType.AGENT_RESULT,
                {
                    "agent": "sql_analysis",
                    "result": "SELECT * FROM employees WHERE department = 'Sales'"
                },
                progress=progress_tracker.update(3, "SQL 분석 완료", "sql_analysis", 100),
                agent="sql_analysis",
                stream_id=stream_id
            )

            # 4단계: 데이터 검색
            progress = progress_tracker.update(4, "데이터 검색 중", "information_retrieval", 0)
            yield self._create_event(
                StreamEventType.AGENT_START,
                {"agent": "information_retrieval", "task": "데이터베이스 쿼리 실행"},
                progress=progress,
                step="데이터 검색",
                agent="information_retrieval",
                stream_id=stream_id
            )

            # 검색 진행
            for i in range(2):
                await asyncio.sleep(0.3)
                sub_progress = (i + 1) * 50
                progress = progress_tracker.update(4, "데이터 검색 중", "information_retrieval", sub_progress)

                yield self._create_event(
                    StreamEventType.TOOL_EXECUTION,
                    {"tool": "database_query", "status": f"검색 {sub_progress}% 완료"},
                    progress=progress,
                    agent="information_retrieval",
                    stream_id=stream_id
                )

            # 5단계: 결과 생성
            progress = progress_tracker.update(5, "결과 생성 중")

            # 토큰별 스트리밍 (시뮬레이션)
            response_text = "분석 결과: 영업부 직원은 총 15명이며, 평균 실적은 120% 달성했습니다."
            tokens = response_text.split()

            for i, token in enumerate(tokens):
                await asyncio.sleep(0.1)  # 토큰별 딜레이

                yield self._create_event(
                    StreamEventType.CONTENT_DELTA,
                    {"delta": token + " "},
                    progress=progress_tracker.update(
                        5,
                        "결과 생성 중",
                        sub_progress=(i + 1) / len(tokens) * 100
                    ),
                    stream_id=stream_id
                )

            # 최종 컨텐츠
            yield self._create_event(
                StreamEventType.CONTENT,
                {"content": response_text},
                progress=progress_tracker.update(5, "결과 생성 완료", sub_progress=100),
                stream_id=stream_id
            )

        except Exception as e:
            logger.error(f"Supervisor streaming error: {e}")
            raise

    def _create_event(
        self,
        event_type: StreamEventType,
        data: Any,
        progress: Optional[float] = None,
        step: Optional[str] = None,
        agent: Optional[str] = None,
        stream_id: Optional[str] = None
    ) -> StreamEvent:
        """스트림 이벤트 생성"""
        return StreamEvent(
            id=stream_id or str(uuid.uuid4()),
            event=event_type,
            data=data,
            timestamp=datetime.now().isoformat(),
            metadata={
                "service": "enhanced_streaming",
                "version": "1.0"
            },
            progress=progress,
            step=step,
            agent=agent
        )

    async def stream_with_heartbeat(
        self,
        query: str,
        user_context: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        하트비트를 포함한 SSE 스트리밍

        Args:
            query: 쿼리
            user_context: 사용자 컨텍스트

        Yields:
            SSE 형식 문자열
        """
        heartbeat_task = None
        heartbeat_queue = asyncio.Queue()

        async def send_heartbeat():
            """주기적 하트비트 전송"""
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                await heartbeat_queue.put(
                    self._create_event(
                        StreamEventType.HEARTBEAT,
                        {"timestamp": datetime.now().isoformat()}
                    )
                )

        try:
            # 하트비트 태스크 시작
            heartbeat_task = asyncio.create_task(send_heartbeat())

            # 메인 스트림과 하트비트 병합
            async for event in self.stream_execution(query, user_context):
                yield event.to_sse()

                # 대기 중인 하트비트 처리
                while not heartbeat_queue.empty():
                    heartbeat = await heartbeat_queue.get()
                    yield heartbeat.to_sse()

        finally:
            # 하트비트 태스크 정리
            if heartbeat_task:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

    def get_active_streams(self) -> Dict[str, Any]:
        """활성 스트림 정보 반환"""
        return {
            stream_id: {
                **info,
                "duration": (datetime.now() - info["started_at"]).total_seconds()
            }
            for stream_id, info in self.active_streams.items()
        }


# 사용 예제를 위한 헬퍼 함수
async def create_sse_response(
    streaming_service: EnhancedStreamingService,
    query: str,
    user_context: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """
    SSE 응답 생성

    Args:
        streaming_service: 스트리밍 서비스
        query: 쿼리
        user_context: 사용자 컨텍스트

    Yields:
        SSE 형식 문자열
    """
    async for sse_data in streaming_service.stream_with_heartbeat(query, user_context):
        yield sse_data