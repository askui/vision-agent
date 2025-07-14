import logging
from typing import Annotated, overload

from pydantic import ConfigDict, Field, validate_call
from typing_extensions import override

from askui.agent_base import AgentBase
from askui.container import telemetry
from askui.locators.locators import Locator
from askui.models.shared.settings import ActSettings, MessageSettings
from askui.tools.android.agent_os import ANDROID_KEY
from askui.tools.android.agent_os_facade import AndroidAgentOsFacade
from askui.tools.android.ppadb_agent_os import PpadbAgentOs
from askui.tools.android.tools import (
    AndroidDragAndDropTool,
    AndroidKeyCombinationTool,
    AndroidKeyTapEventTool,
    AndroidScreenshotTool,
    AndroidShellTool,
    AndroidSwipeTool,
    AndroidTapTool,
    AndroidTypeTool,
)
from askui.tools.exception_tool import ExceptionTool

from .logger import logger
from .models import ModelComposition
from .models.models import ModelChoice, ModelName, ModelRegistry, Point
from .reporting import CompositeReporter, Reporter
from .retry import Retry

_SYSTEM_PROMPT = """
You are an autonomous Android device control agent operating via ADB on a test device with full system access.
Your primary goal is to execute tasks efficiently and reliably while maintaining system stability.

<CORE PRINCIPLES>
* Autonomy: Operate independently and make informed decisions without requiring user input.
* Never ask for other tasks to be done, only do the task you are given.
* Reliability: Ensure actions are repeatable and maintain system stability.
* Efficiency: Optimize operations to minimize latency and resource usage.
* Safety: Always verify actions before execution, even with full system access.
</CORE PRINCIPLES>

<OPERATIONAL GUIDELINES>
1. Tool Usage:
   * Verify tool availability before starting any operation
   * Use the most direct and efficient tool for each task
   * Combine tools strategically for complex operations
   * Prefer built-in tools over shell commands when possible

2. Error Handling:
   * Assess failures systematically: check tool availability, permissions, and device state
   * Implement retry logic with exponential backoff for transient failures
   * Use fallback strategies when primary approaches fail
   * Provide clear, actionable error messages with diagnostic information

3. Performance Optimization:
   * Use one-liner shell commands with inline filtering (grep, cut, awk, jq) for efficiency
   * Minimize screen captures and coordinate calculations
   * Cache device state information when appropriate
   * Batch related operations when possible

4. Screen Interaction:
   * Ensure all coordinates are integers and within screen bounds
   * Implement smart scrolling for off-screen elements
   * Use appropriate gestures (tap, swipe, drag) based on context
   * Verify element visibility before interaction

5. System Access:
   * Leverage full system access responsibly
   * Use shell commands for system-level operations
   * Monitor system state and resource usage
   * Maintain system stability during operations

6. Recovery Strategies:
   * If an element is not visible, try:
     - Scrolling in different directions
     - Adjusting view parameters
     - Using alternative interaction methods
   * If a tool fails:
     - Check device connection and state
     - Verify tool availability and permissions
     - Try alternative tools or approaches
   * If stuck:
     - Provide clear diagnostic information
     - Suggest potential solutions
     - Request user intervention only if necessary

7. Best Practices:
   * Document all significant operations
   * Maintain operation logs for debugging
   * Implement proper cleanup after operations
   * Follow Android best practices for UI interaction

<IMPORTANT NOTES>
* This is a test device with full system access - use this capability responsibly
* Always verify the success of critical operations
* Maintain system stability as the highest priority
* Provide clear, actionable feedback for all operations
* Use the most efficient method for each task
</IMPORTANT NOTES>
"""

_ANTHROPIC__CLAUDE__3_5__SONNET__20241022__ACT_SETTINGS = ActSettings(
    messages=MessageSettings(
        model=ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022.value,
        system=_SYSTEM_PROMPT,
        betas=[],
    ),
)

_CLAUDE__SONNET__4__20250514__ACT_SETTINGS = ActSettings(
    messages=MessageSettings(
        model=ModelName.CLAUDE__SONNET__4__20250514.value,
        system=_SYSTEM_PROMPT,
        thinking={"type": "enabled", "budget_tokens": 2048},
        betas=[],
    ),
)


class AndroidVisionAgent(AgentBase):
    @telemetry.record_call(exclude={"model_router", "reporters", "tools"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        log_level: int | str = logging.INFO,
        reporters: list[Reporter] | None = None,
        model: ModelChoice | ModelComposition | str | None = None,
        retry: Retry | None = None,
        models: ModelRegistry | None = None,
    ) -> None:
        self.os = PpadbAgentOs()
        reporter = CompositeReporter(reporters=reporters)
        act_agent_os_facade = AndroidAgentOsFacade(self.os, reporter)
        super().__init__(
            log_level=log_level,
            reporter=reporter,
            model=model,
            retry=retry,
            models=models,
            tools=[
                AndroidScreenshotTool(act_agent_os_facade),
                AndroidTapTool(act_agent_os_facade),
                AndroidTypeTool(act_agent_os_facade),
                AndroidDragAndDropTool(act_agent_os_facade),
                AndroidKeyTapEventTool(act_agent_os_facade),
                AndroidSwipeTool(act_agent_os_facade),
                AndroidKeyCombinationTool(act_agent_os_facade),
                AndroidShellTool(act_agent_os_facade),
                ExceptionTool(),
            ],
            agent_os=self.os,
        )

    @overload
    def tap(
        self,
        target: str | Locator,
        model: ModelComposition | str | None = None,
    ) -> None: ...

    @overload
    def tap(
        self,
        target: Point,
        model: ModelComposition | str | None = None,
    ) -> None: ...

    @telemetry.record_call(exclude={"locator"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def tap(
        self,
        target: str | Locator | tuple[int, int],
        model: ModelComposition | str | None = None,
    ) -> None:
        """
        Taps on the specified target.

        Args:
            target (str | Locator | Point): The target to tap on. Can be a locator, a point, or a string.
            model (ModelComposition | str | None, optional): The composition or name of the model(s) to be used for tapping on the target.

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.tap("Submit button")
                agent.tap((100, 100))
        """
        msg = "tap"
        if isinstance(target, tuple):
            msg += f" at ({target[0]}, {target[1]})"
            self._reporter.add_message("User", msg)
            self.os.tap(target[0], target[1])
        else:
            msg += f" on {target}"
            self._reporter.add_message("User", msg)
            logger.debug("VisionAgent received instruction to click on %s", target)
            point = self._locate(locator=target, model=model)
            self.os.tap(point[0], point[1])

    @telemetry.record_call(exclude={"text"})
    @validate_call
    def type(
        self,
        text: Annotated[str, Field(min_length=1)],
    ) -> None:
        """
        Types the specified text as if it were entered on a keyboard.

        Args:
            text (str): The text to be typed. Must be at least `1` character long.
            Only ASCII printable characters are supported. other characters will raise an error.

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.type("Hello, world!")  # Types "Hello, world!"
                agent.type("user@example.com")  # Types an email address
                agent.type("password123")  # Types a password
            ```
        """
        self._reporter.add_message("User", f'type: "{text}"')
        logger.debug("VisionAgent received instruction to type '%s'", text)
        self.os.type(text)

    @telemetry.record_call()
    @validate_call
    def key_tap(
        self,
        key: ANDROID_KEY,
    ) -> None:
        """
        Taps the specified key on the Android device.

        Args:
            key (ANDROID_KEY): The key to tap.

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.key_tap("HOME")  # Taps the home key
                agent.key_tap("BACK")  # Taps the back key
            ```
        """
        self.os.key_tap(key)

    @telemetry.record_call()
    @validate_call
    def key_combination(
        self,
        keys: Annotated[list[ANDROID_KEY], Field(min_length=2)],
        duration_in_ms: int = 100,
    ) -> None:
        """
        Taps the specified keys on the Android device.

        Args:
            keys (list[ANDROID_KEY]): The keys to tap.
            duration_in_ms (int, optional): The duration in milliseconds to hold the key combination. Default is 100ms.

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.key_combination(["HOME", "BACK"])  # Taps the home key and then the back key
                agent.key_combination(["HOME", "BACK"], duration_in_ms=200)  # Taps the home key and then the back key for 200ms.
            ```
        """
        self.os.key_combination(keys, duration_in_ms)

    @telemetry.record_call()
    @validate_call
    def shell(
        self,
        command: str,
    ) -> str:
        """
        Executes a shell command on the Android device.

        Args:
            command (str): The shell command to execute.

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.shell("pm list packages")  # Lists all installed packages
                agent.shell("dumpsys battery")  # Displays battery information
            ```
        """
        return self.os.shell(command)

    @telemetry.record_call()
    @validate_call
    def drag_and_drop(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration_in_ms: int = 1000,
    ) -> None:
        """
        Drags and drops the specified target.

        Args:
            x1 (int): The x-coordinate of the starting point.
            y1 (int): The y-coordinate of the starting point.
            x2 (int): The x-coordinate of the ending point.
            y2 (int): The y-coordinate of the ending point.
            duration_in_ms (int, optional): The duration in milliseconds to hold the drag and drop. Default is 1000ms.

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.drag_and_drop(100, 100, 200, 200)  # Drags and drops from (100, 100) to (200, 200)
                agent.drag_and_drop(100, 100, 200, 200, duration_in_ms=2000)  # Drags and drops from (100, 100) to (200, 200) with a 2000ms duration
        """
        self.os.drag_and_drop(x1, y1, x2, y2, duration_in_ms)

    @telemetry.record_call()
    @validate_call
    def swipe(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration_in_ms: int = 1000,
    ) -> None:
        """
        Swipes the specified target.

        Args:
            x1 (int): The x-coordinate of the starting point.
            y1 (int): The y-coordinate of the starting point.
            x2 (int): The x-coordinate of the ending point.
            y2 (int): The y-coordinate of the ending point.
            duration_in_ms (int, optional): The duration in milliseconds to hold the swipe. Default is 1000ms.

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.swipe(100, 100, 200, 200)  # Swipes from (100, 100) to (200, 200)
                agent.swipe(100, 100, 200, 200, duration_in_ms=2000)  # Swipes from (100, 100) to (200, 200) with a 2000ms duration
        """
        self.os.swipe(x1, y1, x2, y2, duration_in_ms)

    @telemetry.record_call(
        exclude={"device_sn"},
    )
    @validate_call
    def set_device_by_serial_number(
        self,
        device_sn: str,
    ) -> None:
        """
        Sets the active device for screen interactions by name.

        Args:
            device_sn (str): The serial number of the device to set as active.

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.set_device_by_serial_number("Pixel 6")  # Sets the active device to the Pixel 6
        """
        self.os.set_device_by_serial_number(device_sn)

    @override
    def _get_default_settings_for_act(self, model_choice: str) -> ActSettings:
        match model_choice:
            case ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022:
                return _ANTHROPIC__CLAUDE__3_5__SONNET__20241022__ACT_SETTINGS
            case ModelName.CLAUDE__SONNET__4__20250514 | ModelName.ASKUI:
                return _CLAUDE__SONNET__4__20250514__ACT_SETTINGS
            case _:
                return ActSettings()
