import time
from functools import wraps
from typing import Any, Callable, Optional

import machineid
from pydantic import BaseModel, Field, SecretStr
from segment import analytics

from askui.logger import logger


MACHINE_ID_HASHING_SALT = "askui"


class SegmentSettings(BaseModel):
    """Settings for Segment telemetry"""

    api_url: str = "https://tracking.askui.com/v1"
    write_key: SecretStr = SecretStr("Iae4oWbOo509Acu5ZeEb2ihqSpemjnhY")
    enabled: bool = True
    app_name: str = "askui-vision-agent"


class TelemetrySettings(BaseModel):
    """Settings for telemetry configuration"""

    segment: SegmentSettings | None = SegmentSettings()
    machine_id: str = Field(
        default_factory=lambda: machineid.hashed_id(app_id=MACHINE_ID_HASHING_SALT),
        description=(
            "The machine ID of the host machine. "
            "This is used to identify the machine and the user (if anynomous) across AskUI components. "
            "We hash it with an AskUI specific salt to avoid user tracking across (non-AskUI) applications or "
            "exposing the actual machine ID. This is the trade-off we chose for now to protect user privacy while "
            "still being able to improve the UX across components."
        ),
    )
    enabled: bool = True


# TODO Add analytics context


class Telemetry:
    def __init__(self, settings: TelemetrySettings) -> None:
        self._settings = settings
        self._segment_enabled = False
        if not self._settings.enabled:
            logger.info("Telemetry is disabled")  # TODO Better logging, structured with Segment
            return
        else:
            logger.info("Telemetry is enabled")

        if self._settings.segment and self._settings.segment.enabled:
            self._segment_enabled = True
            analytics.write_key = self._settings.segment.write_key.get_secret_value()
            logger.info("Segment is enabled")
        else:
            logger.info("Segment is disabled")

    @property
    def _anonymous_user_id(self) -> str:
        """Get the anonymous user ID"""
        return self._settings.machine_id

    def _track_method(
        self,
        method_name: str,
        args: tuple[Any],
        kwargs: dict[str, Any],
        duration_ms: float,
    ) -> None:
        if not self._segment_enabled:
            return

        try:
            analytics.track(  # TODO Configure properly
                event=f"method_called_{method_name}",
                properties={"args": args, "kwargs": kwargs, "duration_ms": duration_ms},
                anonymous_id=self._anonymous_user_id,
            )
            logger.debug(f"Tracked method {method_name} with duration {duration_ms}ms")
        except Exception as e:
            logger.debug(f"Failed to track method {method_name}: {e}")

    def _track_error(
        self, error: Exception, context: Optional[dict[str, Any]] = None
    ) -> None:
        """Track errors in both Segment and Sentry"""
        if self._segment_enabled:
            try:
                analytics.track(  # TODO Configure properly
                    event="error_occurred",
                    properties={
                        "error_type": type(error).__name__,
                        "error_message": str(error),
                        **(context or {}),
                    },
                    anonymous_id=self._anonymous_user_id,
                )
                logger.debug(f"Tracked error {error} with context {context}")
            except Exception as e:
                logger.debug(f"Failed to track error in Segment: {e}")

    def track_method_call(self) -> Callable:
        """Decorator to track method calls, performance and errors"""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                logger.debug(
                    f"Tracking method call {func.__name__} with args {args} and kwargs {kwargs}"
                )
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000

                    # Track successful call
                    # Maybe track before the actual call? Are there default values in Segment?
                    self._track_method(
                        func.__name__, args=args, kwargs=kwargs, duration_ms=duration_ms
                    )

                    return result
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    # Track error
                    self._track_error(
                        e,
                        context={
                            "method": func.__name__,
                            "args": args,
                            "kwargs": kwargs,
                            "duration_ms": duration_ms,
                        },
                    )
                    raise

            return wrapper

        return decorator
