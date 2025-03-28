import os
import platform
import time
from functools import cached_property, wraps
from typing import Any, Callable, Optional

import machineid
from pydantic import BaseModel, Field, HttpUrl, SecretStr
from segment import analytics

from askui.logger import logger
from askui.telemetry.analytics import AnalyticsContext, AppContext, OSContext, PlatformContext
from askui.telemetry.pkg_version import get_pkg_version
from askui.telemetry.user_identification import (
    UserIdentification,
    UserIdentificationSettings,
)


class SegmentSettings(BaseModel):
    """Settings for Segment telemetry"""

    api_url: HttpUrl = HttpUrl("https://tracking.askui.com/v1")
    write_key: SecretStr = SecretStr("Iae4oWbOo509Acu5ZeEb2ihqSpemjnhY")
    enabled: bool = True


class TelemetrySettings(BaseModel):
    """Settings for telemetry configuration"""

    user_identification: UserIdentificationSettings | None = (
        UserIdentificationSettings()
    )
    segment: SegmentSettings | None = SegmentSettings()
    app_name: str = "askui-vision-agent"
    app_version: str = get_pkg_version()
    group_id: str | None = Field(
        default=os.environ.get("ASKUI_WORKSPACE_ID"),
        description='The group ID of the user. Defaults to the "ASKUI_WORKSPACE_ID" environment variable if set, otherwise None.',
    )
    machine_id: str = Field(
        default_factory=lambda: machineid.hashed_id(app_id="askui"),
        description=(
            "The machine ID of the host machine. "
            "This is used to identify the machine and the user (if anynomous) across AskUI components. "
            'We hash it with an AskUI specific salt ("askui") to avoid user tracking across (non-AskUI) '
            "applications or exposing the actual machine ID. This is the trade-off we chose for now to "
            "protect user privacy while still being able to improve the UX across components."
        ),
    )
    enabled: bool = True

    @cached_property
    def analytics_context(self) -> AnalyticsContext:
        analytics_context = AnalyticsContext(
            app=AppContext(name=self.app_name, version=self.app_version),
            os=OSContext(
                name=platform.system(),
                version=platform.version(),
                release=platform.release(),
            ),
            platform=PlatformContext(
                arch=platform.machine(),
                python_version=platform.python_version(),
            ),
        )
        if self.group_id:
            analytics_context["group_id"] = self.group_id
        return analytics_context


class Telemetry:
    def __init__(self, settings: TelemetrySettings) -> None:
        self._settings = settings
        self._segment_enabled = False
        self._user_identification: UserIdentification | None = None
        if not self._settings.enabled:
            logger.info(
                "Telemetry is disabled"
            )
            return
        else:
            logger.info("Telemetry is enabled")

        if self._settings.segment and self._settings.segment.enabled:
            self._segment_enabled = True
            analytics.write_key = self._settings.segment.write_key.get_secret_value()
            logger.info("Segment is enabled")
        else:
            logger.info("Segment is disabled")

        if (
            self._settings.user_identification
            and self._settings.user_identification.enabled
        ):
            self._user_identification = UserIdentification(
                settings=self._settings.user_identification
            )
            logger.info("User identification is enabled")
        else:
            logger.info("User identification is disabled")

    def identify(self) -> None:
        """Identify the user with AskUI if AskUI token is set

        This method only needs to be called once per process, ideally as early as possible to correlate all following events with the user.
        """
        if self._user_identification:
            self._user_identification.identify(
                anonymous_id=self._anonymous_user_id,
            )

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
                context=self._settings.analytics_context,
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
                    context=self._settings.analytics_context,
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
