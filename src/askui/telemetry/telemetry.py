import inspect
import os
import platform
import time
from functools import cached_property, wraps
from typing import Any, Callable
import uuid

import machineid
from pydantic import BaseModel, Field

from askui.logger import logger
from askui.telemetry.context import (
    CallStack,
    TelemetryContext,
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
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="The session ID of the user. This is used to identify the current user session (process).",
    )
    enabled: bool = True

    @cached_property
    def context_base(self) -> TelemetryContext:
        context_base = TelemetryContext(
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
            session_id=self.session_id,
        )
        if self.group_id:
            context_base["group_id"] = self.group_id
        return context_base


class Telemetry:
    _EXCLUDE_MASK = "masked"

    def __init__(self, settings: TelemetrySettings) -> None:
        self._settings = settings
        self._processors: list[TelemetryProcessor] = []
        self._user_identification: UserIdentification | None = None
        if not self._settings.enabled:
            logger.info("Telemetry is disabled")
            return

        logger.info(
            "Telemetry is enabled. To disable it, set the `ASKUI__VA__TELEMETRY__ENABLED` environment variable to `False`."
        )
        if self._settings.user_identification:
            self._user_identification = UserIdentification(
                settings=self._settings.user_identification
            )
        self._call_stack = CallStack()
        self._context = self._settings.context_base

    def add_processor(self, processor: TelemetryProcessor) -> None:
        """Add a telemetry processor that will be called in order of addition"""
        self._processors.append(processor)

    def identify(self) -> None:
        """Identify the user with AskUI if AskUI token is set

        This method only needs to be called once per process, ideally as early as possible to correlate all following events with the user.
        """
        if self._user_identification:
            self._user_identification.identify(
                anonymous_id=self._settings.context_base["anonymous_id"],
            )

    def record_call(
        self,
        exclude: set[str] | None = None,
        exclude_first_arg: bool = True,
        exclude_response: bool = True,
        exclude_exception: bool = False,
        exclude_start: bool = True,
    ) -> Callable:
        """Decorator to record calls to functions and methods

        Args:
            exclude: Set of parameters whose values are to be excluded from tracking (masked to retain structure of the call)
            exclude_first_arg: Whether to exclude the first argument, e.g., self or cls for instance and class methods. Defaults to `True`, for functions and static methods, it should be set to `False`
            exclude_response: Whether to exclude the response of the function in the telemetry event. Defaults to `True`
            exclude_exception: Whether to exclude the exception if one is raised in the telemetry event. Defaults to `False`
            exclude_start: Whether to exclude the start of the function call as a telemetry event. Defaults to `True`
        """

        _exclude = exclude or set()

        def decorator(func: Callable) -> Callable:
            param_names_sorted = list(inspect.signature(func).parameters.keys())

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if not self._settings.enabled:
                    return func(*args, **kwargs)

                self._call_stack.push_call()
                module = func.__module__
                fn_name = func.__qualname__
                logger.debug(
                    f"Record call\tfn_name={fn_name} module={module}"
                )
                processed_args: tuple[Any, ...] = tuple(
                    arg if param_names_sorted[i] not in _exclude else self._EXCLUDE_MASK
                    for i, arg in enumerate(args)
                )
                if exclude_first_arg:
                    processed_args = processed_args[1:] if processed_args else ()
                processed_kwargs = {
                    k: v if k not in _exclude else self._EXCLUDE_MASK
                    for k, v in kwargs.items()
                }
                attributes: dict[str, Any] = {
                    "module": module,
                    "fn_name": fn_name,
                    "args": processed_args,
                    "kwargs": processed_kwargs,
                    "call_id": self._call_stack.current[-1], 
                }
                self._context["call_stack"] = self._call_stack.current
                if not exclude_start:
                    for processor in self._processors:
                        processor.record_event(
                            name="Function call started",
                            attributes=attributes,
                            context=self._context,
                        )
                start_time = time.time()
                try:
                    response = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    attributes["duration_ms"] = duration_ms
                    if not exclude_response:
                        attributes["response"] = response
                    for processor in self._processors:
                        processor.record_event(
                            name="Function called",
                            attributes=attributes,
                            context=self._context,
                        )
                    return response
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    attributes["duration_ms"] = duration_ms
                    if not exclude_exception:
                        attributes["exception"] = {
                            "type": type(e).__name__,
                            "message": str(e),
                        }
                    for processor in self._processors:
                        processor.record_event(
                            name="Function called",
                            attributes=attributes,
                            context=self._context,
                        )
                    raise
                finally:
                    self._call_stack.pop_call()

            return wrapper

        return decorator

    def flush(self) -> None:
        """Flush the telemetry data to the backend"""
        for processor in self._processors:
            processor.flush()
