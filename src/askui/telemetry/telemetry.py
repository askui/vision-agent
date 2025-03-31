import os
import platform
import time
from functools import cached_property, wraps
from typing import Any, Callable

import machineid
from pydantic import BaseModel, Field

from askui.logger import logger
from askui.telemetry.analytics import (
    AnalyticsContext,
    AppContext,
    OSContext,
    PlatformContext,
)
from askui.telemetry.pkg_version import get_pkg_version
from askui.telemetry.processors import SegmentSettings, TelemetryProcessor
from askui.telemetry.user_identification import (
    UserIdentification,
    UserIdentificationSettings,
)


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
            anonymous_id=self.machine_id,
        )
        if self.group_id:
            analytics_context["group_id"] = self.group_id
        return analytics_context


class Telemetry:
    def __init__(self, settings: TelemetrySettings) -> None:
        self._settings = settings
        self._processors: list[TelemetryProcessor] = []
        self._user_identification: UserIdentification | None = None
        
        if not self._settings.enabled:
            logger.info("Telemetry is disabled")
            return
        else:
            logger.info("Telemetry is enabled")

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

    def add_processor(self, processor: TelemetryProcessor) -> None:
        """Add a telemetry processor that will be called in order of addition"""
        self._processors.append(processor)

    # TODO Make sure this is available in Segment as well / move to Segment
    def identify(self) -> None:
        """Identify the user with AskUI if AskUI token is set

        This method only needs to be called once per process, ideally as early as possible to correlate all following events with the user.
        """
        if self._user_identification:
            self._user_identification.identify(
                anonymous_id=self._settings.analytics_context["anonymous_id"],
            )

    def track_call(self) -> Callable:
        """Decorator to track method calls, performance and errors"""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if not self._settings.enabled:
                    return func(*args, **kwargs)
                
                fn_name = f"{func.__module__}.{func.__qualname__}"
                logger.debug(
                    f"Tracking method call {fn_name} with args {args} and kwargs {kwargs}"
                )
                for processor in self._processors:
                    processor.record_call_start(
                        fn_name,
                        args=args,
                        kwargs=kwargs,
                        context=self._settings.analytics_context,
                    )
                start_time = time.time()
                try:
                    response = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    for processor in self._processors:
                        processor.record_call_end(
                            fn_name,
                            args=args,
                            kwargs=kwargs,
                            response=response,
                            duration_ms=duration_ms,
                            context=self._settings.analytics_context,
                        )
                    return response
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    # TODO Type this fully
                    context = {
                        "method": fn_name,
                        "args": args,
                        "kwargs": kwargs,
                        "duration_ms": duration_ms,
                    }
                    for processor in self._processors:
                        processor.record_exception(
                            e,
                            context=context,
                            analytics_context=self._settings.analytics_context,
                        )
                    raise
            return wrapper

        return decorator
