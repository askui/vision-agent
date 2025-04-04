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

    @abc.abstractmethod
    def flush(self) -> None: ...


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
                user_id=context.get("user_id"),
                anonymous_id=context["anonymous_id"],
                event=name,
                properties={
                    "attributes": attributes,
                    # Special context as Segment only supports predefined context keys
                    # (see https://segment.com/docs/connections/spec/track/#context)
                    "context": {
                        "os": context["os"],
                        "platform": context["platform"],
                        "session_id": context["session_id"],
                        "call_stack": context["call_stack"],
                    }
                },
                context={
                    "app": context["app"],
                    "groupId": context.get("group_id"),
                    "os": {
                        "name": context["os"]["name"],
                        "version": context["os"]["version"],
                    },
                    "device": context.get("device"),
                },
                timestamp=datetime.now(tz=timezone.utc),
            )
        except Exception as e:
            logger.debug(f'Failed to track event "{name}" using Segment: {e}')
    
    def flush(self) -> None:
        self._analytics.flush()


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

    def flush(self) -> None:
        pass
