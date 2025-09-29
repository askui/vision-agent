import logging
from typing import Awaitable, Callable

import structlog
from asgi_correlation_id.context import correlation_id
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from askui.chat.api.telemetry.integrations.fastapi.models import AccessLogLine, TimeSpan

from . import structlog_context
from .utils import compact

access_logger = structlog.stdlib.get_logger("api.access")
error_logger = structlog.stdlib.get_logger("api.error")


EVENT = "API Accessed"


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        try:
            return await call_next(request)
        except Exception:  # noqa: BLE001
            error_message = "Uncaught exception raised handling request"
            error_logger.exception(error_message)
            return Response("Internal Server Error", status_code=500)


class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = correlation_id.get()
        structlog_context.bind(request_id=request_id)
        return await call_next(request)


class ProcessTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        time_span = TimeSpan()

        response = await call_next(request)
        time_span.end()
        response.headers.append("x-process-time", str(time_span.in_s))
        structlog_context.bind(time_ms=time_span.in_ms)
        return response


class AccessLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    def determine_log_level(self, request: Request) -> int:  # noqa: ARG002
        return logging.INFO

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        access_log_line = AccessLogLine(
            level=self.determine_log_level(request),
            event=EVENT,
            method=request.method,
            path=request.url.path,
            query=request.url.query,
            status=response.status_code,
            http_version=request.scope["http_version"],
            ip=request.client.host if request.client else None,
            port=request.client.port if request.client else None,
        )
        await access_logger.alog(
            **compact({**access_log_line, **structlog_context.get()})
        )
        return response
