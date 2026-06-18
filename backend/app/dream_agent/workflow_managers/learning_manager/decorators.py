"""Learning 데코레이터 — trace_log.

core(foundation)에서 이전 (2026-06-05, spec 16 §4 V1): trace_log 는 TraceLogger(learning)에
의존하므로 foundation 이 아니라 learning_manager 에 속한다. 이전으로 core↔workflow_managers
논리 순환(최하위↔최상위) 해소 — 이제 같은 패키지의 .trace_logger 를 top-level import (순환 없음).

Status: planned — 정의됨, @trace_log 적용처 0 (Sprint 15 learning 경로에서 stage 함수 적용 예정).
Reference: docs/agent_specs/16_layer_dependency_architecture_v1.0.md §4 V1
"""

from __future__ import annotations

import asyncio
import time
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from app.core.logging import get_logger

from .trace_logger import get_trace_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def trace_log(
    layer: str,
    action: str,
    include_input: bool = True,
    include_output: bool = True,
) -> Callable[[F], F]:
    """트레이스 로깅 데코레이터 — 실행 정보를 TraceLogger 에 기록.

    Args:
        layer: 레이어 이름 (cognitive, planning, execution, response)
        action: 액션 이름 (classify_intent, generate_plan, ...)
        include_input: 입력 로깅 여부
        include_output: 출력 로깅 여부

    Example:
        @trace_log(layer="cognitive", action="classify_intent")
        async def classify_intent(user_input: str) -> dict:
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            trace_logger = get_trace_logger()
            start_time = time.time()
            success = True
            error_msg: Optional[str] = None
            result = None

            # 입력 데이터 추출
            input_data: dict[str, Any] = {}
            if include_input:
                if args:
                    input_data["args"] = [str(arg)[:500] for arg in args]  # 최대 500자
                if kwargs:
                    input_data["kwargs"] = {k: str(v)[:500] for k, v in kwargs.items()}

            try:
                result = await func(*args, **kwargs)
                return result

            except Exception as e:
                success = False
                error_msg = str(e)
                raise

            finally:
                duration_ms = (time.time() - start_time) * 1000

                # 출력 데이터 추출
                output_data: dict[str, Any] = {}
                if include_output and result is not None:
                    try:
                        if hasattr(result, "model_dump"):
                            output_data = result.model_dump()
                        elif isinstance(result, dict):
                            output_data = result
                        else:
                            output_data = {"value": str(result)[:1000]}
                    except Exception:
                        output_data = {"value": str(result)[:1000]}

                trace_logger.log(
                    layer=layer,
                    action=action,
                    input_data=input_data,
                    output_data=output_data,
                    duration_ms=duration_ms,
                    success=success,
                    error=error_msg,
                )

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            trace_logger = get_trace_logger()
            start_time = time.time()
            success = True
            error_msg: Optional[str] = None
            result = None

            input_data: dict[str, Any] = {}
            if include_input:
                if args:
                    input_data["args"] = [str(arg)[:500] for arg in args]
                if kwargs:
                    input_data["kwargs"] = {k: str(v)[:500] for k, v in kwargs.items()}

            try:
                result = func(*args, **kwargs)
                return result

            except Exception as e:
                success = False
                error_msg = str(e)
                raise

            finally:
                duration_ms = (time.time() - start_time) * 1000

                output_data: dict[str, Any] = {}
                if include_output and result is not None:
                    try:
                        if hasattr(result, "model_dump"):
                            output_data = result.model_dump()
                        elif isinstance(result, dict):
                            output_data = result
                        else:
                            output_data = {"value": str(result)[:1000]}
                    except Exception:
                        output_data = {"value": str(result)[:1000]}

                trace_logger.log(
                    layer=layer,
                    action=action,
                    input_data=input_data,
                    output_data=output_data,
                    duration_ms=duration_ms,
                    success=success,
                    error=error_msg,
                )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator
