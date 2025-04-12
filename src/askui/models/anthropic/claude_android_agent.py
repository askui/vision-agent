import sys
import platform
from datetime import datetime
from typing import Callable

from askui.models.anthropic.claude_agent import ClaudeAgent
from askui.models.utils import scale_coordinates_back
from askui.reporting.report import SimpleReportGenerator
from askui.tools.anthropic.android import (
    AndroidGetConnectedDisplaysTool,
    AndroidScreenshotTool,
    AndroidSelectDisplayTool,
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
from askui.tools.anthropic.file_tools import FileWriteTool, FileReadTool
from askui.tools.askui.askui_android_controller import AskUiAndroidControllerClient
from askui.utils import ANDROID_KEY, resize_to_max_edge


ANDROID_SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
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


class ClaudeAndroidAgent(ClaudeAgent):
    def __init__(
        self,
        controller_client: AskUiAndroidControllerClient,
        report: SimpleReportGenerator | None = None,
        file_tool_base_dir_path: str | None = None,
    ) -> None:
        self.file_writer_base_dir_path = None
        tools = [
            AndroidScreenshotTool(controller_client),
            AndroidTapTool(controller_client),
            AndroidSwipeTool(controller_client),
            AndroidDragAndDropTool(controller_client),
            AndroidRollTool(controller_client),
            AndroidMoveMouseTool(controller_client),
            DebugDrawTool(controller_client),
            AndroidKeyEventTool(controller_client),
            AndroidShellTool(controller_client),
            AndroidGetCursorPositionTool(controller_client),
            AndroidGetConnectedDisplaysTool(controller_client),
            AndroidSelectDisplayTool(controller_client),
        ]

        if file_tool_base_dir_path:
            tools.extend(
                [
                    FileWriteTool(file_tool_base_dir_path),
                    FileReadTool(file_tool_base_dir_path),
                ]
            )
        super().__init__(
            tools=tools,
            system_prompt=ANDROID_SYSTEM_PROMPT,
            report=report,
        )
