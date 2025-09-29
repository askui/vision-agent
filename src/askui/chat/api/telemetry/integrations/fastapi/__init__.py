from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from starlette_context.middleware import RawContextMiddleware

from askui.chat.api.telemetry.integrations.fastapi.settings import TelemetrySettings
from askui.chat.api.telemetry.logs import propagate_logs_up, setup_logging, silence_logs

from .fastapi_middleware import (
    AccessLoggingMiddleware,
    ExceptionHandlingMiddleware,
    ProcessTimingMiddleware,
    TracingMiddleware,
)
from .structlog_processors import merge_starlette_contextvars


def instrument(
    app: FastAPI,
    settings: TelemetrySettings | None = None,
) -> None:
    _settings = settings or TelemetrySettings()
    setup_logging(
        _settings.log,
        pre_processors=[merge_starlette_contextvars],
    )
    silence_logs(["uvicorn.access"])
    propagate_logs_up(["uvicorn", "uvicorn.error"])
    app.add_middleware(ExceptionHandlingMiddleware)
    app.add_middleware(TracingMiddleware)
    app.add_middleware(ProcessTimingMiddleware)
    app.add_middleware(AccessLoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(RawContextMiddleware)
    Instrumentator().instrument(app).expose(app)
