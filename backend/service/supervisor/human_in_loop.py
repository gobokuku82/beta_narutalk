"""
Human-in-the-Loop System for LangGraph 0.6.x
Human-in-the-loop 시스템 - 사람 개입 및 승인 메커니즘
"""

from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
import asyncio
import logging
import json
from collections import deque
import uuid

logger = logging.getLogger(__name__)


class InterventionType(str, Enum):
    """개입 타입"""
    APPROVAL = "approval"           # 승인 요청
    REVIEW = "review"              # 검토 요청
    CORRECTION = "correction"       # 수정 요청
    DECISION = "decision"          # 의사결정 요청
    VALIDATION = "validation"       # 검증 요청
    ESCALATION = "escalation"      # 에스컬레이션


class InterventionPriority(str, Enum):
    """개입 우선순위"""
    URGENT = "urgent"         # 긴급 (즉시 필요)
    HIGH = "high"            # 높음 (1시간 내)
    NORMAL = "normal"         # 일반 (24시간 내)
    LOW = "low"              # 낮음 (일주일 내)


class InterventionStatus(str, Enum):
    """개입 상태"""
    PENDING = "pending"       # 대기 중
    IN_REVIEW = "in_review"   # 검토 중
    APPROVED = "approved"     # 승인됨
    REJECTED = "rejected"     # 거부됨
    MODIFIED = "modified"     # 수정됨
    EXPIRED = "expired"       # 만료됨


@dataclass
class InterventionRequest:
    """개입 요청"""
    id: str
    type: InterventionType
    priority: InterventionPriority
    status: InterventionStatus
    agent_name: str
    task_context: Dict[str, Any]
    reason: str
    options: List[Dict[str, Any]]
    created_at: datetime
    deadline: Optional[datetime] = None
    assigned_to: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """만료 여부 확인"""
        if self.deadline:
            return datetime.now() > self.deadline
        return False

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            **asdict(self),
            "created_at": self.created_at.isoformat(),
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "is_expired": self.is_expired()
        }


@dataclass
class InterventionResponse:
    """개입 응답"""
    request_id: str
    decision: str
    reasoning: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None
    responder: Optional[str] = None
    responded_at: datetime = field(default_factory=datetime.now)
    response_time: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            **asdict(self),
            "responded_at": self.responded_at.isoformat()
        }


class HumanInLoopManager:
    """
    Human-in-the-Loop 관리자
    - 개입 요청 관리
    - 승인 워크플로우
    - 타임아웃 처리
    """

    def __init__(
        self,
        auto_approve_threshold: float = 0.8,
        default_timeout_hours: int = 24,
        enable_notifications: bool = True
    ):
        """
        Initialize HumanInLoopManager

        Args:
            auto_approve_threshold: 자동 승인 임계값
            default_timeout_hours: 기본 타임아웃 (시간)
            enable_notifications: 알림 활성화
        """
        self.auto_approve_threshold = auto_approve_threshold
        self.default_timeout_hours = default_timeout_hours
        self.enable_notifications = enable_notifications

        # 개입 요청 큐
        self.pending_requests: Dict[str, InterventionRequest] = {}
        self.completed_requests: List[Tuple[InterventionRequest, InterventionResponse]] = []

        # 승인 규칙
        self.approval_rules: Dict[str, Callable] = {}
        self.auto_approval_patterns: List[Dict[str, Any]] = []

        # 콜백
        self.intervention_callbacks: Dict[str, List[Callable]] = {
            "on_request": [],
            "on_response": [],
            "on_timeout": [],
            "on_auto_approve": []
        }

        # 통계
        self.stats = {
            "total_requests": 0,
            "approved": 0,
            "rejected": 0,
            "modified": 0,
            "auto_approved": 0,
            "expired": 0,
            "average_response_time": 0.0
        }

        # 백그라운드 태스크
        self._monitor_task = None
        self._start_monitoring()

        logger.info("HumanInLoopManager initialized")

    def _start_monitoring(self):
        """모니터링 태스크 시작"""
        async def monitor_loop():
            while True:
                try:
                    await asyncio.sleep(60)  # 1분마다
                    await self._check_expired_requests()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")

        self._monitor_task = asyncio.create_task(monitor_loop())

    async def request_intervention(
        self,
        agent_name: str,
        type: InterventionType,
        task_context: Dict[str, Any],
        reason: str,
        options: List[Dict[str, Any]],
        priority: InterventionPriority = InterventionPriority.NORMAL,
        timeout_hours: Optional[int] = None,
        assigned_to: Optional[str] = None
    ) -> InterventionRequest:
        """
        개입 요청 생성

        Args:
            agent_name: 에이전트 이름
            type: 개입 타입
            task_context: 작업 컨텍스트
            reason: 개입 이유
            options: 선택 옵션
            priority: 우선순위
            timeout_hours: 타임아웃 시간
            assigned_to: 담당자

        Returns:
            개입 요청
        """
        request_id = f"{agent_name}_{type}_{uuid.uuid4().hex[:8]}"
        timeout_hours = timeout_hours or self.default_timeout_hours

        request = InterventionRequest(
            id=request_id,
            type=type,
            priority=priority,
            status=InterventionStatus.PENDING,
            agent_name=agent_name,
            task_context=task_context,
            reason=reason,
            options=options,
            created_at=datetime.now(),
            deadline=datetime.now() + timedelta(hours=timeout_hours),
            assigned_to=assigned_to
        )

        # 자동 승인 체크
        if await self._check_auto_approval(request):
            return await self._auto_approve(request)

        # 요청 저장
        self.pending_requests[request_id] = request
        self.stats["total_requests"] += 1

        # 콜백 실행
        await self._trigger_callbacks("on_request", request)

        # 알림 발송
        if self.enable_notifications:
            await self._send_notification(request)

        logger.info(f"Intervention requested: {request_id}")
        return request

    async def respond_to_intervention(
        self,
        request_id: str,
        decision: str,
        reasoning: Optional[str] = None,
        modifications: Optional[Dict[str, Any]] = None,
        responder: Optional[str] = None
    ) -> InterventionResponse:
        """
        개입 응답

        Args:
            request_id: 요청 ID
            decision: 결정 (approve/reject/modify)
            reasoning: 이유
            modifications: 수정사항
            responder: 응답자

        Returns:
            개입 응답
        """
        if request_id not in self.pending_requests:
            raise ValueError(f"Request {request_id} not found")

        request = self.pending_requests[request_id]
        response_time = (datetime.now() - request.created_at).total_seconds()

        response = InterventionResponse(
            request_id=request_id,
            decision=decision,
            reasoning=reasoning,
            modifications=modifications,
            responder=responder,
            response_time=response_time
        )

        # 상태 업데이트
        if decision == "approve":
            request.status = InterventionStatus.APPROVED
            self.stats["approved"] += 1
        elif decision == "reject":
            request.status = InterventionStatus.REJECTED
            self.stats["rejected"] += 1
        elif decision == "modify":
            request.status = InterventionStatus.MODIFIED
            self.stats["modified"] += 1

        # 완료 처리
        del self.pending_requests[request_id]
        self.completed_requests.append((request, response))

        # 통계 업데이트
        self._update_response_time(response_time)

        # 콜백 실행
        await self._trigger_callbacks("on_response", request, response)

        logger.info(f"Intervention responded: {request_id} -> {decision}")
        return response

    async def _check_auto_approval(self, request: InterventionRequest) -> bool:
        """자동 승인 체크"""
        # 자동 승인 패턴 확인
        for pattern in self.auto_approval_patterns:
            if self._match_pattern(request, pattern):
                return True

        # 승인 규칙 확인
        for rule_name, rule_func in self.approval_rules.items():
            try:
                if rule_func(request):
                    logger.info(f"Auto-approval by rule: {rule_name}")
                    return True
            except Exception as e:
                logger.error(f"Error in approval rule {rule_name}: {e}")

        return False

    async def _auto_approve(self, request: InterventionRequest) -> InterventionRequest:
        """자동 승인 처리"""
        request.status = InterventionStatus.APPROVED
        self.stats["auto_approved"] += 1

        response = InterventionResponse(
            request_id=request.id,
            decision="approve",
            reasoning="Auto-approved by rules",
            responder="system"
        )

        self.completed_requests.append((request, response))

        # 콜백 실행
        await self._trigger_callbacks("on_auto_approve", request, response)

        logger.info(f"Auto-approved: {request.id}")
        return request

    def _match_pattern(
        self,
        request: InterventionRequest,
        pattern: Dict[str, Any]
    ) -> bool:
        """패턴 매칭"""
        for key, value in pattern.items():
            if key not in ["type", "agent_name", "priority"]:
                continue

            request_value = getattr(request, key, None)
            if request_value != value:
                return False

        return True

    async def _check_expired_requests(self):
        """만료 요청 체크"""
        expired = []

        for request_id, request in self.pending_requests.items():
            if request.is_expired():
                expired.append(request_id)

        for request_id in expired:
            request = self.pending_requests.pop(request_id)
            request.status = InterventionStatus.EXPIRED
            self.stats["expired"] += 1

            # 콜백 실행
            await self._trigger_callbacks("on_timeout", request)

            logger.warning(f"Request expired: {request_id}")

    def add_approval_rule(
        self,
        name: str,
        rule_func: Callable[[InterventionRequest], bool]
    ):
        """
        승인 규칙 추가

        Args:
            name: 규칙 이름
            rule_func: 규칙 함수
        """
        self.approval_rules[name] = rule_func
        logger.info(f"Added approval rule: {name}")

    def add_auto_approval_pattern(self, pattern: Dict[str, Any]):
        """
        자동 승인 패턴 추가

        Args:
            pattern: 패턴 딕셔너리
        """
        self.auto_approval_patterns.append(pattern)
        logger.info(f"Added auto-approval pattern: {pattern}")

    def register_callback(
        self,
        event: str,
        callback: Callable
    ):
        """
        콜백 등록

        Args:
            event: 이벤트 타입
            callback: 콜백 함수
        """
        if event in self.intervention_callbacks:
            self.intervention_callbacks[event].append(callback)

    async def _trigger_callbacks(self, event: str, *args):
        """콜백 실행"""
        if event not in self.intervention_callbacks:
            return

        for callback in self.intervention_callbacks[event]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args)
                else:
                    callback(*args)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    async def _send_notification(self, request: InterventionRequest):
        """알림 발송"""
        # 실제 구현시 이메일, 슬랙 등 활용
        logger.info(f"Notification sent for request: {request.id}")

    def _update_response_time(self, response_time: float):
        """응답 시간 통계 업데이트"""
        total_responses = (
            self.stats["approved"] +
            self.stats["rejected"] +
            self.stats["modified"]
        )

        if total_responses > 0:
            current_avg = self.stats["average_response_time"]
            new_avg = (
                (current_avg * (total_responses - 1) + response_time) /
                total_responses
            )
            self.stats["average_response_time"] = new_avg

    def get_pending_requests(
        self,
        priority: Optional[InterventionPriority] = None,
        type: Optional[InterventionType] = None
    ) -> List[InterventionRequest]:
        """
        대기 중인 요청 조회

        Args:
            priority: 우선순위 필터
            type: 타입 필터

        Returns:
            요청 목록
        """
        requests = list(self.pending_requests.values())

        if priority:
            requests = [r for r in requests if r.priority == priority]

        if type:
            requests = [r for r in requests if r.type == type]

        # 우선순위 정렬
        priority_order = {
            InterventionPriority.URGENT: 0,
            InterventionPriority.HIGH: 1,
            InterventionPriority.NORMAL: 2,
            InterventionPriority.LOW: 3
        }

        requests.sort(key=lambda x: priority_order[x.priority])

        return requests

    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        total_completed = (
            self.stats["approved"] +
            self.stats["rejected"] +
            self.stats["modified"] +
            self.stats["auto_approved"]
        )

        return {
            **self.stats,
            "pending_requests": len(self.pending_requests),
            "completion_rate": (
                total_completed / self.stats["total_requests"] * 100
                if self.stats["total_requests"] > 0 else 0
            ),
            "auto_approval_rate": (
                self.stats["auto_approved"] / self.stats["total_requests"] * 100
                if self.stats["total_requests"] > 0 else 0
            )
        }


class InterventionInterface:
    """
    개입 인터페이스
    - UI/API 통합
    - 실시간 업데이트
    """

    def __init__(self, manager: HumanInLoopManager):
        """
        Initialize InterventionInterface

        Args:
            manager: HumanInLoopManager 인스턴스
        """
        self.manager = manager
        self.active_sessions: Dict[str, Any] = {}

        logger.info("InterventionInterface initialized")

    async def create_review_session(
        self,
        request: InterventionRequest,
        reviewer: str
    ) -> str:
        """
        리뷰 세션 생성

        Args:
            request: 개입 요청
            reviewer: 리뷰어

        Returns:
            세션 ID
        """
        session_id = f"session_{uuid.uuid4().hex[:8]}"

        self.active_sessions[session_id] = {
            "request": request,
            "reviewer": reviewer,
            "started_at": datetime.now(),
            "actions": []
        }

        request.status = InterventionStatus.IN_REVIEW

        logger.info(f"Review session created: {session_id}")
        return session_id

    async def submit_review(
        self,
        session_id: str,
        decision: str,
        reasoning: str,
        modifications: Optional[Dict[str, Any]] = None
    ) -> InterventionResponse:
        """
        리뷰 제출

        Args:
            session_id: 세션 ID
            decision: 결정
            reasoning: 이유
            modifications: 수정사항

        Returns:
            개입 응답
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        request = session["request"]

        response = await self.manager.respond_to_intervention(
            request.id,
            decision,
            reasoning,
            modifications,
            session["reviewer"]
        )

        # 세션 종료
        del self.active_sessions[session_id]

        return response

    def get_review_dashboard(self) -> Dict[str, Any]:
        """리뷰 대시보드 데이터"""
        pending = self.manager.get_pending_requests()

        # 우선순위별 그룹핑
        by_priority = {}
        for request in pending:
            priority = request.priority
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(request.to_dict())

        return {
            "total_pending": len(pending),
            "by_priority": by_priority,
            "active_sessions": len(self.active_sessions),
            "stats": self.manager.get_stats()
        }


# 전역 인스턴스
_global_hilm: Optional[HumanInLoopManager] = None


def get_human_in_loop_manager() -> HumanInLoopManager:
    """전역 Human-in-Loop 매니저 반환"""
    global _global_hilm
    if _global_hilm is None:
        _global_hilm = HumanInLoopManager()

        # 기본 자동 승인 규칙
        _global_hilm.add_approval_rule(
            "low_risk",
            lambda req: req.task_context.get("risk_level", "high") == "low"
        )

        _global_hilm.add_approval_rule(
            "trusted_agent",
            lambda req: req.agent_name in ["information_retrieval"]
        )

    return _global_hilm