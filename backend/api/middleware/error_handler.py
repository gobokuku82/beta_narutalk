"""Error Handler Middleware — 전역 HTTP 에러 핸들링.

(2026-06-12 정리 전환 Sprint) AgentError(E1xxx, core/errors.py) 트랙 폐기 —
raise 하는 코드가 backend 전체에 0곳이라 관련 분기(_get_status_code 세분 매핑,
agent_error_handler)는 전부 도달 불가 死경로였음. 살아있는 경로만 유지:
  - ErrorHandlerMiddleware: 미처리 Exception → 500/E5003
  - ValueError → 400/E1001, generic Exception → 500/E5003 (exception_handler)
WS 에러 계약(실사용)은 app/core/error_codes.py(ErrorCodes)가 단일 진실 소스.

Reference: docs/agent_specs/22_error_codes_v1.1.md
"""

from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """전역 에러 핸들러 미들웨어 — 미처리 예외를 500/E5003 으로."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        if request.scope.get("type") == "websocket":
            return await call_next(request)

        try:
            return await call_next(request)

        except Exception as e:
            logger.exception(
                "Unexpected error",
                path=request.url.path,
                error=str(e),
            )

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "E5003",
                        "message": "Internal server error",
                        "details": {"error": str(e)} if logger.isEnabledFor(10) else {},
                    },
                },
            )


def setup_error_handlers(app: FastAPI) -> None:
    """에러 핸들러 설정.

    Args:
        app: FastAPI 앱
    """
    app.add_middleware(ErrorHandlerMiddleware)

    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request,
        exc: ValueError,
    ) -> JSONResponse:
        """ValueError 핸들러"""
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": "E1001",
                    "message": str(exc),
                },
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """일반 예외 핸들러"""
        logger.exception("Unhandled exception", error=str(exc))

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "E5003",
                    "message": "Internal server error",
                },
            },
        )
