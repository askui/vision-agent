from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional, Protocol

from pydantic import BaseModel, HttpUrl, SecretStr
from askui.logger import logger
from askui.telemetry.analytics import AnalyticsContext


class TelemetryProcessor(Protocol):
    def record_call_start(
        self,
        method_name: str,
        args: tuple[Any],
        kwargs: dict[str, Any],
        context: AnalyticsContext,
    ) -> None: ...

    def record_call_end(
        self,
        method_name: str,
        args: tuple[Any],
        kwargs: dict[str, Any],
        response: Any,
        duration_ms: float,
        context: AnalyticsContext,
    ) -> None: ...

    def record_exception(
        self,
        error: Exception,
        context: Optional[dict[str, Any]],
        analytics_context: AnalyticsContext,
    ) -> None: ...


class SegmentSettings(BaseModel):
    api_url: HttpUrl = HttpUrl("https://tracking.askui.com/v1")
    write_key: SecretStr = SecretStr("Iae4oWbOo509Acu5ZeEb2ihqSpemjnhY")
    enabled: bool = True  # TODO Exclude from here


class Segment:
    def __init__(self, settings: SegmentSettings) -> None:
        self._settings = settings

        from segment import analytics

        self._analytics = analytics
        self._analytics.write_key = settings.write_key.get_secret_value()

    def record_call_start(
        self,
        method_name: str,
        args: tuple[Any],
        kwargs: dict[str, Any],
        context: AnalyticsContext,
    ) -> None:
        try:
            self._analytics.track(
                event="method_started",
                properties={
                    "method_name": method_name,
                    "args": args,
                    "kwargs": kwargs,
                },
                anonymous_id=context["anonymous_id"],
                context=context,
            )
            logger.debug(f"Tracked method start {method_name}")
        except Exception as e:
            logger.debug(f"Failed to track method start {method_name}: {e}")

    def record_call_end(
        self,
        method_name: str,
        args: tuple[Any],
        kwargs: dict[str, Any],
        response: Any,
        duration_ms: float,
        context: AnalyticsContext,
    ) -> None:
        try:
            self._analytics.track(
                event="method_ended",
                properties={
                    "method_name": method_name,
                    "args": args,
                    "kwargs": kwargs,
                    "response": response,
                    "duration_ms": duration_ms,
                },
                anonymous_id=context["anonymous_id"],
                context=context,
            )
            logger.debug(
                f"Tracked method end {method_name} with duration {duration_ms}ms"
            )
        except Exception as e:
            logger.debug(f"Failed to track method end {method_name}: {e}")

    def record_exception(
        self,
        error: Exception,
        context: Optional[dict[str, Any]],
        analytics_context: AnalyticsContext,
    ) -> None:
        try:
            self._analytics.track(
                event="error_occurred",
                properties={
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    **(context or {}),
                },
                anonymous_id=analytics_context["anonymous_id"],
                context=analytics_context,
            )
            logger.debug(f"Tracked error {error} with context {context}")
        except Exception as e:
            logger.debug(f"Failed to track error in Segment: {e}")


@dataclass
class TelemetryEvent:
    timestamp: datetime
    event_type: str
    method_name: str
    args: tuple[Any]
    kwargs: dict[str, Any]
    response: Optional[Any] = None
    duration_ms: Optional[float] = None
    error: Optional[Exception] = None
    error_context: Optional[dict[str, Any]] = None


class InMemoryProcessor:
    def __init__(self) -> None:
        self._events: List[TelemetryEvent] = []

    def record_call_start(
        self,
        method_name: str,
        args: tuple[Any],
        kwargs: dict[str, Any],
        context: AnalyticsContext,
    ) -> None:
        self._events.append(
            TelemetryEvent(
                timestamp=datetime.now(),
                event_type="method_started",
                method_name=method_name,
                args=args,
                kwargs=kwargs,
            )
        )

    def record_call_end(
        self,
        method_name: str,
        args: tuple[Any],
        kwargs: dict[str, Any],
        response: Any,
        duration_ms: float,
        context: AnalyticsContext,
    ) -> None:
        self._events.append(
            TelemetryEvent(
                timestamp=datetime.now(),  # TODO
                event_type="method_ended",
                method_name=method_name,
                args=args,
                kwargs=kwargs,
                response=response,
                duration_ms=duration_ms,
            )
        )

    def record_exception(
        self,
        error: Exception,
        context: Optional[dict[str, Any]],
        analytics_context: AnalyticsContext,
    ) -> None:
        self._events.append(
            TelemetryEvent(
                timestamp=datetime.now(),
                event_type="error_occurred",
                method_name=context.get("method", "unknown") if context else "unknown",
                args=context.get("args", ()) if context else (),  # TODO
                kwargs=context.get("kwargs", {}) if context else {},
                error=error,
                error_context=context,
            )
        )

    def get_events(self) -> List[TelemetryEvent]:
        return self._events.copy()

    def clear(self) -> None:
        self._events.clear()
