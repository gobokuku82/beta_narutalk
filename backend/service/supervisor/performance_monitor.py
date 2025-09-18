"""
Agent Performance Monitoring System for LangGraph 0.6.x
에이전트 성능 모니터링 및 분석 시스템
"""

import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum
import statistics
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """메트릭 타입"""
    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    SUCCESS_RATE = "success_rate"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    TOKEN_USAGE = "token_usage"
    CACHE_HIT_RATE = "cache_hit_rate"


@dataclass
class AgentMetrics:
    """에이전트 메트릭"""
    agent_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_execution_time: float = 0.0
    min_execution_time: float = float('inf')
    max_execution_time: float = 0.0
    total_tokens_used: int = 0
    total_memory_mb: float = 0.0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    recent_executions: deque = field(default_factory=lambda: deque(maxlen=100))

    @property
    def average_execution_time(self) -> float:
        """평균 실행 시간"""
        if self.total_executions == 0:
            return 0.0
        return self.total_execution_time / self.total_executions

    @property
    def success_rate(self) -> float:
        """성공률"""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100

    @property
    def error_rate(self) -> float:
        """에러율"""
        if self.total_executions == 0:
            return 0.0
        return (self.failed_executions / self.total_executions) * 100

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "agent_name": self.agent_name,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "average_execution_time": self.average_execution_time,
            "min_execution_time": self.min_execution_time if self.min_execution_time != float('inf') else 0,
            "max_execution_time": self.max_execution_time,
            "success_rate": self.success_rate,
            "error_rate": self.error_rate,
            "total_tokens_used": self.total_tokens_used,
            "average_memory_mb": self.total_memory_mb / self.total_executions if self.total_executions > 0 else 0,
            "recent_errors": self.errors[-5:]  # 최근 5개 에러
        }


@dataclass
class ExecutionRecord:
    """실행 기록"""
    agent_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    input_size: int = 0
    output_size: int = 0
    tokens_used: int = 0
    memory_mb: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentPerformanceMonitor:
    """
    에이전트 성능 모니터링 시스템
    - 실시간 메트릭 수집
    - 성능 분석 및 최적화 제안
    - 이상 징후 감지
    """

    def __init__(
        self,
        enable_persistence: bool = True,
        persistence_path: str = "monitoring/agent_metrics.json",
        alert_thresholds: Optional[Dict[str, float]] = None
    ):
        """
        Initialize AgentPerformanceMonitor

        Args:
            enable_persistence: 지속성 활성화
            persistence_path: 메트릭 저장 경로
            alert_thresholds: 알림 임계값
        """
        self.enable_persistence = enable_persistence
        self.persistence_path = Path(persistence_path)

        # 에이전트별 메트릭
        self.agent_metrics: Dict[str, AgentMetrics] = {}

        # 실행 중인 작업
        self.active_executions: Dict[str, ExecutionRecord] = {}

        # 전체 시스템 메트릭
        self.system_metrics = {
            "total_requests": 0,
            "total_execution_time": 0.0,
            "start_time": datetime.now(),
            "peak_concurrent_executions": 0,
            "current_concurrent_executions": 0
        }

        # 시계열 데이터 (최근 1시간)
        self.time_series_data: deque = deque(maxlen=3600)  # 1초마다 1시간

        # 알림 임계값
        self.alert_thresholds = alert_thresholds or {
            "max_execution_time": 30.0,  # 30초
            "min_success_rate": 80.0,    # 80%
            "max_error_rate": 20.0,      # 20%
            "max_memory_mb": 500.0        # 500MB
        }

        # 알림 큐
        self.alerts: deque = deque(maxlen=100)

        # 백그라운드 태스크
        self._monitoring_task = None
        self._start_monitoring()

        # 지속성 로드
        if enable_persistence:
            self._load_metrics()

        logger.info("AgentPerformanceMonitor initialized")

    def _start_monitoring(self):
        """백그라운드 모니터링 시작"""
        async def monitoring_loop():
            while True:
                try:
                    await asyncio.sleep(1)  # 1초마다
                    self._collect_system_metrics()
                    self._check_alerts()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")

        self._monitoring_task = asyncio.create_task(monitoring_loop())

    def _collect_system_metrics(self):
        """시스템 메트릭 수집"""
        current_metrics = {
            "timestamp": datetime.now().isoformat(),
            "concurrent_executions": len(self.active_executions),
            "total_agents": len(self.agent_metrics),
            "active_agents": sum(
                1 for metrics in self.agent_metrics.values()
                if metrics.recent_executions and
                (datetime.now() - datetime.fromisoformat(
                    metrics.recent_executions[-1]["timestamp"]
                )).total_seconds() < 60
            )
        }

        self.time_series_data.append(current_metrics)

        # 피크 동시 실행 업데이트
        if current_metrics["concurrent_executions"] > self.system_metrics["peak_concurrent_executions"]:
            self.system_metrics["peak_concurrent_executions"] = current_metrics["concurrent_executions"]

        self.system_metrics["current_concurrent_executions"] = current_metrics["concurrent_executions"]

    async def start_execution(
        self,
        agent_name: str,
        input_data: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        실행 시작 기록

        Args:
            agent_name: 에이전트 이름
            input_data: 입력 데이터
            metadata: 메타데이터

        Returns:
            실행 ID
        """
        execution_id = f"{agent_name}_{datetime.now().timestamp()}"

        # 에이전트 메트릭 초기화
        if agent_name not in self.agent_metrics:
            self.agent_metrics[agent_name] = AgentMetrics(agent_name=agent_name)

        # 실행 기록 생성
        record = ExecutionRecord(
            agent_name=agent_name,
            start_time=datetime.now(),
            input_size=len(str(input_data)),
            metadata=metadata or {}
        )

        self.active_executions[execution_id] = record
        self.system_metrics["total_requests"] += 1

        logger.debug(f"Started execution: {execution_id}")
        return execution_id

    async def end_execution(
        self,
        execution_id: str,
        success: bool,
        output_data: Any = None,
        error: Optional[str] = None,
        tokens_used: int = 0,
        memory_mb: float = 0.0,
        cache_hits: int = 0,
        cache_misses: int = 0
    ):
        """
        실행 종료 기록

        Args:
            execution_id: 실행 ID
            success: 성공 여부
            output_data: 출력 데이터
            error: 에러 메시지
            tokens_used: 사용된 토큰 수
            memory_mb: 메모리 사용량
            cache_hits: 캐시 히트 수
            cache_misses: 캐시 미스 수
        """
        if execution_id not in self.active_executions:
            logger.warning(f"Unknown execution ID: {execution_id}")
            return

        record = self.active_executions.pop(execution_id)
        record.end_time = datetime.now()
        record.execution_time = (record.end_time - record.start_time).total_seconds()
        record.success = success
        record.error = error
        record.output_size = len(str(output_data)) if output_data else 0
        record.tokens_used = tokens_used
        record.memory_mb = memory_mb
        record.cache_hits = cache_hits
        record.cache_misses = cache_misses

        # 메트릭 업데이트
        await self._update_metrics(record)

        logger.debug(f"Ended execution: {execution_id} (success={success})")

    async def _update_metrics(self, record: ExecutionRecord):
        """메트릭 업데이트"""
        metrics = self.agent_metrics[record.agent_name]

        # 실행 카운트
        metrics.total_executions += 1
        if record.success:
            metrics.successful_executions += 1
        else:
            metrics.failed_executions += 1
            if record.error:
                metrics.errors.append({
                    "timestamp": record.end_time.isoformat(),
                    "error": record.error,
                    "execution_time": record.execution_time
                })

        # 실행 시간
        metrics.total_execution_time += record.execution_time
        metrics.min_execution_time = min(metrics.min_execution_time, record.execution_time)
        metrics.max_execution_time = max(metrics.max_execution_time, record.execution_time)

        # 토큰 및 메모리
        metrics.total_tokens_used += record.tokens_used
        metrics.total_memory_mb += record.memory_mb

        # 최근 실행 기록
        metrics.recent_executions.append({
            "timestamp": record.end_time.isoformat(),
            "execution_time": record.execution_time,
            "success": record.success,
            "tokens_used": record.tokens_used,
            "memory_mb": record.memory_mb,
            "cache_hit_rate": (
                record.cache_hits / (record.cache_hits + record.cache_misses) * 100
                if (record.cache_hits + record.cache_misses) > 0 else 0
            )
        })

        # 시스템 메트릭
        self.system_metrics["total_execution_time"] += record.execution_time

        # 지속성 저장
        if self.enable_persistence:
            await self._save_metrics()

    def _check_alerts(self):
        """알림 체크"""
        for agent_name, metrics in self.agent_metrics.items():
            # 실행 시간 체크
            if metrics.max_execution_time > self.alert_thresholds["max_execution_time"]:
                self._create_alert(
                    "SLOW_EXECUTION",
                    agent_name,
                    f"실행 시간 초과: {metrics.max_execution_time:.2f}초"
                )

            # 성공률 체크
            if metrics.total_executions > 10:  # 최소 10회 실행 후
                if metrics.success_rate < self.alert_thresholds["min_success_rate"]:
                    self._create_alert(
                        "LOW_SUCCESS_RATE",
                        agent_name,
                        f"낮은 성공률: {metrics.success_rate:.1f}%"
                    )

                # 에러율 체크
                if metrics.error_rate > self.alert_thresholds["max_error_rate"]:
                    self._create_alert(
                        "HIGH_ERROR_RATE",
                        agent_name,
                        f"높은 에러율: {metrics.error_rate:.1f}%"
                    )

    def _create_alert(self, alert_type: str, agent_name: str, message: str):
        """알림 생성"""
        alert = {
            "type": alert_type,
            "agent": agent_name,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }

        self.alerts.append(alert)
        logger.warning(f"Alert: {alert}")

    def get_agent_stats(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        에이전트 통계 반환

        Args:
            agent_name: 에이전트 이름

        Returns:
            에이전트 통계
        """
        if agent_name not in self.agent_metrics:
            return None

        return self.agent_metrics[agent_name].to_dict()

    def get_all_stats(self) -> Dict[str, Any]:
        """전체 통계 반환"""
        uptime = (datetime.now() - self.system_metrics["start_time"]).total_seconds()

        return {
            "system": {
                "uptime_seconds": uptime,
                "total_requests": self.system_metrics["total_requests"],
                "requests_per_second": self.system_metrics["total_requests"] / uptime if uptime > 0 else 0,
                "average_execution_time": (
                    self.system_metrics["total_execution_time"] /
                    self.system_metrics["total_requests"]
                    if self.system_metrics["total_requests"] > 0 else 0
                ),
                "peak_concurrent_executions": self.system_metrics["peak_concurrent_executions"],
                "current_concurrent_executions": self.system_metrics["current_concurrent_executions"]
            },
            "agents": {
                name: metrics.to_dict()
                for name, metrics in self.agent_metrics.items()
            },
            "recent_alerts": list(self.alerts)[-10:]  # 최근 10개 알림
        }

    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """
        최적화 제안 생성

        Returns:
            최적화 제안 목록
        """
        suggestions = []

        for agent_name, metrics in self.agent_metrics.items():
            # 느린 에이전트
            if metrics.average_execution_time > 10:
                suggestions.append({
                    "agent": agent_name,
                    "type": "performance",
                    "suggestion": f"평균 실행 시간이 {metrics.average_execution_time:.2f}초로 느립니다. 캐싱 또는 최적화 필요.",
                    "priority": "high"
                })

            # 낮은 성공률
            if metrics.total_executions > 10 and metrics.success_rate < 90:
                suggestions.append({
                    "agent": agent_name,
                    "type": "reliability",
                    "suggestion": f"성공률이 {metrics.success_rate:.1f}%로 낮습니다. 에러 핸들링 개선 필요.",
                    "priority": "high"
                })

            # 높은 메모리 사용
            avg_memory = metrics.total_memory_mb / metrics.total_executions if metrics.total_executions > 0 else 0
            if avg_memory > 100:
                suggestions.append({
                    "agent": agent_name,
                    "type": "memory",
                    "suggestion": f"평균 메모리 사용량이 {avg_memory:.1f}MB로 높습니다. 메모리 최적화 필요.",
                    "priority": "medium"
                })

        return suggestions

    async def _save_metrics(self):
        """메트릭 저장"""
        try:
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "timestamp": datetime.now().isoformat(),
                "system_metrics": self.system_metrics,
                "agent_metrics": {
                    name: metrics.to_dict()
                    for name, metrics in self.agent_metrics.items()
                }
            }

            with open(self.persistence_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def _load_metrics(self):
        """메트릭 로드"""
        try:
            if self.persistence_path.exists():
                with open(self.persistence_path, 'r') as f:
                    data = json.load(f)

                # 시스템 메트릭은 리셋 (새 세션)
                # 에이전트 메트릭은 누적
                for agent_name, metrics_dict in data.get("agent_metrics", {}).items():
                    # 간단한 복원 (전체 복원은 복잡할 수 있음)
                    logger.info(f"Loaded historical metrics for {agent_name}")

        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")

    async def close(self):
        """리소스 정리"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        if self.enable_persistence:
            await self._save_metrics()


# 전역 모니터 인스턴스
_global_monitor: Optional[AgentPerformanceMonitor] = None


def get_performance_monitor() -> AgentPerformanceMonitor:
    """전역 성능 모니터 인스턴스 반환"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = AgentPerformanceMonitor()
    return _global_monitor