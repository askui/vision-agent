import sys
import platform
from datetime import datetime
from typing import Callable

from askui.models.anthropic.claude_agent import ClaudeAgent
from askui.models.utils import scale_coordinates_back
from askui.reporting.report import SimpleReportGenerator
from askui.tools.anthropic.android import (
    AndroidScreenshotTool,
    AndroidTapTool,
    AndroidSwipeTool,
    AndroidDragAndDropTool,
    AndroidRollTool,
    AndroidMoveMouseTool,
    AndroidKeyEventTool,
    AndroidShellTool,
    AndroidGetCursorPositionTool,
    DebugDrawTool,
)
from askui.utils import ANDROID_KEY


ANDROID_SYSTEM_PROMPT: Callable[[tuple[int, int]], str] = (
    lambda screen_resolution: f"""<SYSTEM_CAPABILITY>
* You are operating on an Android device via ADB.
* Your available architecture is {platform.machine()} connected from a {sys.platform} host.
* You can simulate touch gestures (tap, swipe), key events (like {', '.join(ANDROID_KEY.__args__)}), interact with the UI, capture screenshots, and retrieve logs or dump UI hierarchy.
* Use ADB shell commands to gather system state or perform actions. 
* Before taking any action, check which tools (input simulation, screen, file access, etc.) are available and determine the most reliable course of action.
* Validate the UI state using `uiautomator` or `dumpsys window` to ensure the correct context before taking further steps.
* The current date is {datetime.today().strftime('%A, %B %d, %Y').replace(' 0', ' ')}.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* Always check whether a tool is available before using it.
* Screenshot resolution is {screen_resolution[0]}x{screen_resolution[1]}.
* Use the screenshot tool to capture the screen and analyze the UI state before taking any action that requires UI interaction.
* Be independent and creative in your approach. Reduce dependencies on the user Don't ask for help unless absolutely necessary.
* If you encounter an error, analyze the situation and determine the best course of action.
* If a tool is not available, consider using another tool or method to achieve the same goal.
* All coordinates  must be integers and within the screen bounds. Integers means only numbers are allowed.
* If an expected UI element is not visible, consider scrolling or rechecking using a different strategy like coordinate-based taps.
* If a tool fails, analyze the error message and determine the root cause.
* If an unexpected error occurs (e.g. permission denied, device offline), briefly report the problem, analyze root cause, and decide whether retrying, rebooting, or notifying the user is necessary.
* If you are unable to complete an action after analysis, encounter an unexpected situation, or get stuck for any reason—briefly apologize, then use the exception tool to throw an appropriate exception.
</IMPORTANT>
"""
)


class ClaudeAndroidAgent(ClaudeAgent):
    def __init__(
        self,
        controller_client,
        report: SimpleReportGenerator | None = None,
        rescaled_resolution: tuple[int, int] = (553, 1200),
    ) -> None:
        original_resolution = controller_client.get_screen_resolution()
        rescale_function: Callable[[int, int], tuple[int, int]] = (
            lambda x, y: scale_coordinates_back(
                x,
                y,
                original_resolution[0],
                original_resolution[1],
                rescaled_resolution[0],
                rescaled_resolution[1],
            )
        )

        tools = [
            AndroidScreenshotTool(controller_client, rescaled_resolution),
            AndroidTapTool(controller_client, rescale_function=rescale_function),
            AndroidSwipeTool(controller_client, rescale_function=rescale_function),
            AndroidDragAndDropTool(
                controller_client, rescale_function=rescale_function
            ),
            AndroidRollTool(controller_client, rescale_function=rescale_function),
            AndroidMoveMouseTool(controller_client, rescale_function=rescale_function),
            DebugDrawTool(controller_client, rescale_function=rescale_function),
            AndroidKeyEventTool(controller_client),
            AndroidShellTool(controller_client),
            AndroidGetCursorPositionTool(controller_client),
        ]
        super().__init__(
            tools=tools,
            system_prompt=ANDROID_SYSTEM_PROMPT(rescaled_resolution),
            report=report,
        )
