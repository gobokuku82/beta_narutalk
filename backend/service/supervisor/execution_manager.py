"""
Parallel Execution Manager for Medical Supervisor
병렬/순차 실행 관리 및 에러 핸들링
"""

from typing import Dict, Any, List, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import logging
from enum import Enum
from collections import defaultdict
import traceback

from langgraph.types import Command
from langchain_core.messages import AIMessage, SystemMessage

from .state import MedicalSupervisorState, ExecutionState, merge_agent_state

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class TaskExecution:
    """작업 실행 정보"""

    task_id: str
    agent_name: str
    status: TaskStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    result: Optional[Any] = None
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    timeout: float = 60.0


@dataclass
class ExecutionMetrics:
    """실행 메트릭"""

    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    retried_tasks: int = 0
    cancelled_tasks: int = 0
    total_execution_time: float = 0.0
    average_task_time: float = 0.0
    parallel_efficiency: float = 0.0


class ParallelExecutionManager:
    """
    병렬 실행 관리자
    - 병렬/순차 실행 조정
    - 재시도 로직
    - 에러 핸들링
    - 타임아웃 관리
    """

    def __init__(self, max_parallel_tasks: int = 3):
        """
        Initialize Parallel Execution Manager

        Args:
            max_parallel_tasks: 최대 동시 실행 작업 수
        """

        self.max_parallel_tasks = max_parallel_tasks
        self.active_tasks: Dict[str, TaskExecution] = {}
        self.completed_tasks: Dict[str, TaskExecution] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.execution_metrics = ExecutionMetrics()
        self.error_handlers: Dict[str, Callable] = {}
        self.retry_strategies: Dict[str, Dict[str, Any]] = {}

    async def execute(
        self,
        state: MedicalSupervisorState,
        execution_plan: List[List[str]],
        agent_executors: Dict[str, Callable]
    ) -> Dict[str, Any]:
        """
        실행 계획에 따라 작업 실행

        Args:
            state: 현재 상태
            execution_plan: 실행 계획 (병렬 그룹 리스트)
            agent_executors: 에이전트 실행 함수 맵

        Returns:
            실행 결과
        """

        start_time = datetime.now()
        all_results = {}
        execution_errors = []

        try:
            # 각 실행 단계별 처리
            for phase_idx, phase_tasks in enumerate(execution_plan):
                logger.info(f"Executing phase {phase_idx + 1}/{len(execution_plan)}")

                # 병렬 실행 여부 결정
                if len(phase_tasks) > 1 and self._can_run_parallel(phase_tasks, state):
                    # 병렬 실행
                    phase_results = await self._execute_parallel(
                        phase_tasks,
                        state,
                        agent_executors
                    )
                else:
                    # 순차 실행
                    phase_results = await self._execute_sequential(
                        phase_tasks,
                        state,
                        agent_executors
                    )

                # 결과 병합
                all_results.update(phase_results)

                # 상태 업데이트
                state = self._update_state_with_results(state, phase_results)

                # 에러 확인
                phase_errors = self._check_phase_errors(phase_results)
                if phase_errors:
                    execution_errors.extend(phase_errors)

                    # 치명적 에러 확인
                    if self._has_critical_error(phase_errors):
                        logger.error(f"Critical error in phase {phase_idx + 1}")
                        break

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            execution_errors.append({
                "phase": "execution",
                "error": str(e),
                "traceback": traceback.format_exc()
            })

        # 실행 메트릭 업데이트
        execution_time = (datetime.now() - start_time).total_seconds()
        self._update_metrics(execution_time)

        # 실행 상태 생성
        execution_state = ExecutionState(
            current_step=len(execution_plan),
            total_steps=len(execution_plan),
            execution_progress=1.0 if not execution_errors else 0.8,
            active_tasks=[],
            completed_tasks=list(self.completed_tasks.values()),
            pending_tasks=[],
            task_results=all_results,
            execution_errors=execution_errors,
            retry_attempts={
                task_id: task.retry_count
                for task_id, task in self.completed_tasks.items()
            }
        )

        return {
            "execution_state": execution_state,
            "results": all_results,
            "metrics": self.execution_metrics.__dict__,
            "errors": execution_errors
        }

    def _can_run_parallel(self, tasks: List[str], state: MedicalSupervisorState) -> bool:
        """
        병렬 실행 가능 여부 확인
        """

        # 규정 검토는 순차 실행
        if any("compliance" in task for task in tasks):
            return False

        # 문서 생성은 순차 실행
        if any("doc_generation" in task for task in tasks):
            return False

        # 리소스 제한 확인
        if len(tasks) > self.max_parallel_tasks:
            return False

        return True

    async def _execute_parallel(
        self,
        task_ids: List[str],
        state: MedicalSupervisorState,
        agent_executors: Dict[str, Callable]
    ) -> Dict[str, Any]:
        """
        병렬 실행
        """

        tasks = []
        results = {}

        for task_id in task_ids:
            # 작업 정보 추출
            task_info = self._get_task_info(task_id, state)
            if not task_info:
                continue

            agent_name = task_info["agent"]
            executor = agent_executors.get(agent_name)

            if not executor:
                logger.warning(f"No executor for agent: {agent_name}")
                continue

            # 작업 실행 객체 생성
            task_exec = TaskExecution(
                task_id=task_id,
                agent_name=agent_name,
                status=TaskStatus.PENDING,
                timeout=task_info.get("timeout", 60.0)
            )

            # 비동기 작업 생성
            task = asyncio.create_task(
                self._execute_single_task(task_exec, executor, state)
            )
            tasks.append((task_id, task))

        # 모든 작업 완료 대기
        if tasks:
            task_results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )

            for (task_id, _), result in zip(tasks, task_results):
                if isinstance(result, Exception):
                    results[task_id] = {
                        "status": "failed",
                        "error": str(result)
                    }
                else:
                    results[task_id] = result

        return results

    async def _execute_sequential(
        self,
        task_ids: List[str],
        state: MedicalSupervisorState,
        agent_executors: Dict[str, Callable]
    ) -> Dict[str, Any]:
        """
        순차 실행
        """

        results = {}

        for task_id in task_ids:
            # 작업 정보 추출
            task_info = self._get_task_info(task_id, state)
            if not task_info:
                continue

            agent_name = task_info["agent"]
            executor = agent_executors.get(agent_name)

            if not executor:
                logger.warning(f"No executor for agent: {agent_name}")
                continue

            # 작업 실행 객체 생성
            task_exec = TaskExecution(
                task_id=task_id,
                agent_name=agent_name,
                status=TaskStatus.PENDING,
                timeout=task_info.get("timeout", 60.0)
            )

            # 작업 실행
            try:
                result = await self._execute_single_task(task_exec, executor, state)
                results[task_id] = result

                # 이전 작업 실패 시 중단 옵션
                if result.get("status") == "failed" and task_info.get("critical", False):
                    logger.error(f"Critical task {task_id} failed, stopping execution")
                    break

            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}")
                results[task_id] = {
                    "status": "failed",
                    "error": str(e)
                }

        return results

    async def _execute_single_task(
        self,
        task_exec: TaskExecution,
        executor: Callable,
        state: MedicalSupervisorState
    ) -> Dict[str, Any]:
        """
        단일 작업 실행 (재시도 로직 포함)
        """

        task_exec.status = TaskStatus.RUNNING
        task_exec.started_at = datetime.now()
        self.active_tasks[task_exec.task_id] = task_exec

        result = None
        last_error = None

        # 재시도 루프
        while task_exec.retry_count <= task_exec.max_retries:
            try:
                # 타임아웃 적용 실행
                result = await asyncio.wait_for(
                    executor(state),
                    timeout=task_exec.timeout
                )

                # 성공
                task_exec.status = TaskStatus.COMPLETED
                task_exec.result = result
                break

            except asyncio.TimeoutError:
                last_error = f"Task timed out after {task_exec.timeout}s"
                logger.warning(f"Task {task_exec.task_id} timeout (attempt {task_exec.retry_count + 1})")

            except Exception as e:
                last_error = str(e)
                logger.error(f"Task {task_exec.task_id} failed: {e}")

                # 에러 핸들러 실행
                if task_exec.agent_name in self.error_handlers:
                    try:
                        handled = await self.error_handlers[task_exec.agent_name](e, state)
                        if handled:
                            result = handled
                            task_exec.status = TaskStatus.COMPLETED
                            break
                    except:
                        pass

            # 재시도 필요 여부 확인
            if task_exec.retry_count < task_exec.max_retries:
                task_exec.retry_count += 1
                task_exec.status = TaskStatus.RETRYING

                # 재시도 전략 적용
                retry_strategy = self.retry_strategies.get(
                    task_exec.agent_name,
                    {"delay": 2.0, "backoff": 1.5}
                )

                delay = retry_strategy["delay"] * (retry_strategy["backoff"] ** task_exec.retry_count)
                logger.info(f"Retrying task {task_exec.task_id} after {delay:.1f}s")
                await asyncio.sleep(delay)
            else:
                # 최대 재시도 초과
                task_exec.status = TaskStatus.FAILED
                task_exec.error = last_error
                result = {
                    "status": "failed",
                    "error": last_error,
                    "retry_count": task_exec.retry_count
                }
                break

        # 완료 처리
        task_exec.completed_at = datetime.now()
        del self.active_tasks[task_exec.task_id]
        self.completed_tasks[task_exec.task_id] = task_exec

        return result or {"status": "failed", "error": "Unknown error"}

    def _get_task_info(self, task_id: str, state: MedicalSupervisorState) -> Optional[Dict[str, Any]]:
        """
        작업 정보 추출
        """

        # 실행 계획에서 작업 정보 찾기
        if state.get("execution_plan"):
            for task in state["execution_plan"]:
                if task.get("task_id") == task_id:
                    return task

        # 기본 작업 정보 생성
        if "agent" in task_id:
            agent_name = task_id.split("_")[0] + "_agent"
            return {
                "task_id": task_id,
                "agent": agent_name,
                "timeout": 60.0
            }

        return None

    def _update_state_with_results(
        self,
        state: MedicalSupervisorState,
        results: Dict[str, Any]
    ) -> MedicalSupervisorState:
        """
        결과로 상태 업데이트
        """

        for task_id, result in results.items():
            if "agent" in result:
                agent_name = result["agent"]
                state = merge_agent_state(state, agent_name, result)

        return state

    def _check_phase_errors(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        단계별 에러 확인
        """

        errors = []

        for task_id, result in results.items():
            if result.get("status") == "failed":
                errors.append({
                    "task_id": task_id,
                    "error": result.get("error", "Unknown error"),
                    "retry_count": result.get("retry_count", 0)
                })

        return errors

    def _has_critical_error(self, errors: List[Dict[str, Any]]) -> bool:
        """
        치명적 에러 확인
        """

        critical_keywords = ["database", "connection", "authentication", "permission"]

        for error in errors:
            error_msg = error.get("error", "").lower()
            if any(keyword in error_msg for keyword in critical_keywords):
                return True

        return False

    def _update_metrics(self, execution_time: float):
        """
        실행 메트릭 업데이트
        """

        self.execution_metrics.total_tasks = len(self.completed_tasks)
        self.execution_metrics.completed_tasks = sum(
            1 for task in self.completed_tasks.values()
            if task.status == TaskStatus.COMPLETED
        )
        self.execution_metrics.failed_tasks = sum(
            1 for task in self.completed_tasks.values()
            if task.status == TaskStatus.FAILED
        )
        self.execution_metrics.retried_tasks = sum(
            1 for task in self.completed_tasks.values()
            if task.retry_count > 0
        )
        self.execution_metrics.total_execution_time = execution_time

        if self.execution_metrics.total_tasks > 0:
            self.execution_metrics.average_task_time = (
                execution_time / self.execution_metrics.total_tasks
            )

            # 병렬 효율성 계산
            sequential_time = sum(
                (task.completed_at - task.started_at).total_seconds()
                for task in self.completed_tasks.values()
                if task.completed_at and task.started_at
            )
            if sequential_time > 0:
                self.execution_metrics.parallel_efficiency = (
                    sequential_time / execution_time
                )

    def register_error_handler(self, agent_name: str, handler: Callable):
        """
        에이전트별 에러 핸들러 등록
        """

        self.error_handlers[agent_name] = handler

    def set_retry_strategy(self, agent_name: str, strategy: Dict[str, Any]):
        """
        에이전트별 재시도 전략 설정

        Args:
            agent_name: 에이전트 이름
            strategy: 재시도 전략 (delay, backoff, max_retries 등)
        """

        self.retry_strategies[agent_name] = strategy

    async def cancel_active_tasks(self):
        """
        활성 작업 취소
        """

        for task_id, task_exec in self.active_tasks.items():
            task_exec.status = TaskStatus.CANCELLED
            logger.info(f"Cancelled task: {task_id}")

        self.active_tasks.clear()

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        실행 요약 반환
        """

        return {
            "metrics": self.execution_metrics.__dict__,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "success_rate": (
                self.execution_metrics.completed_tasks / self.execution_metrics.total_tasks
                if self.execution_metrics.total_tasks > 0
                else 0.0
            ),
            "average_retry_count": (
                sum(task.retry_count for task in self.completed_tasks.values()) /
                len(self.completed_tasks)
                if self.completed_tasks
                else 0.0
            )
        }


async def execution_node(state: MedicalSupervisorState) -> Dict[str, Any]:
    """
    Graph node for execution
    """

    manager = ParallelExecutionManager(max_parallel_tasks=3)

    # 에이전트 실행 함수 맵 생성 (실제 구현에서는 실제 에이전트 연결)
    agent_executors = {
        "sql_analysis_agent": lambda s: {"status": "completed", "result": "data"},
        "information_retrieval_agent": lambda s: {"status": "completed", "result": "info"},
        "document_generation_agent": lambda s: {"status": "completed", "result": "doc"},
        "compliance_validation_agent": lambda s: {"status": "completed", "result": "compliant"}
    }

    # 실행 계획 추출
    execution_plan = state.get("parallel_groups", [])

    # 실행
    execution_result = await manager.execute(state, execution_plan, agent_executors)

    # 상태 업데이트
    return {
        "execution_state": execution_result["execution_state"],
        "agent_results": execution_result["results"],
        "execution_time": execution_result["metrics"]["total_execution_time"],
        "current_phase": "completed"
    }