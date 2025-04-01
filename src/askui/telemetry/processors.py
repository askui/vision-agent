import abc

from datetime import datetime, timezone
from typing import Any, TypedDict

from pydantic import BaseModel, HttpUrl
from askui.logger import logger
from askui.telemetry.context import TelemetryContext


class TelemetryProcessor(abc.ABC):
    @abc.abstractmethod
    def record_event(
        self,
        name: str,
        attributes: dict[str, Any],
        context: TelemetryContext,
    ) -> None: ...


class TelemetryEvent(TypedDict):
    name: str
    attributes: dict[str, Any]
    context: TelemetryContext
    timestamp: datetime


class SegmentSettings(BaseModel):
    api_url: HttpUrl = HttpUrl("https://tracking.askui.com/v1")
    write_key: str = "Iae4oWbOo509Acu5ZeEb2ihqSpemjnhY"


class Segment(TelemetryProcessor):
    def __init__(self, settings: SegmentSettings) -> None:
        self._settings = settings

        from segment import analytics

        self._analytics = analytics
        self._analytics.write_key = settings.write_key

    def record_event(
        self,
        name: str,
        attributes: dict[str, Any],
        context: TelemetryContext,
    ) -> None:
        try:
            self._analytics.track(
                event=name,
                properties=attributes,
                anonymous_id=context["anonymous_id"],
                context=context,
                timestamp=datetime.now(tz=timezone.utc),
            )
        except Exception as e:
            logger.debug(f"Failed to track event \"{name}\" using Segment: {e}")


class InMemoryProcessor(TelemetryProcessor):
    def __init__(self) -> None:
        self._events: list[TelemetryEvent] = []

    def record_event(
        self,
        name: str,
        attributes: dict[str, Any],
        context: TelemetryContext,
    ) -> None:
        event: TelemetryEvent = {
            "name": name,
            "attributes": attributes,
            "context": context,
            "timestamp": datetime.now(tz=timezone.utc),
        }
        self._events.append(event)

    def get_events(self) -> list[TelemetryEvent]:
        return self._events.copy()

    def clear(self) -> None:
        self._events.clear()
