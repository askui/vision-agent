import sys
import platform
from datetime import datetime

from askui.models.anthropic.claude_agent import ClaudeAgent
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
    AndroidShellTool,
    AndroidGetCursorPositionTool,
    DebugDrawTool,
)
from askui.tools.anthropic.file_tools import FileWriteTool, FileReadTool
from askui.tools.askui.askui_android_controller import AskUiAndroidControllerClient
from askui.utils import ANDROID_KEY


ANDROID_SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are operating on an Android device via ADB.
* Architecture: {platform.machine()} (host: {sys.platform}).
* You can simulate gestures (tap, swipe), key events ({', '.join(ANDROID_KEY.__args__)}), interact with UI, take screenshots, retrieve logs, and dump the UI hierarchy.
* Use ADB shell commands efficiently—combine related commands into one line when possible and parse the needed result in a single step.
* Confirm available tools (e.g. input, screencap, uiautomator, logcat, file access) before using them.
* Date: {datetime.today().strftime('%A, %B %d, %Y').replace(' 0', ' ')}.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* Always verify tool availability first.
* Use screenshots or UI dumps to analyze screen state before interacting.
* Be autonomous—do not rely on user input unless absolutely necessary.
* On failure: assess, determine root cause, and adapt (retry, fallback, escalate, or gracefully exit).
* Prefer one-liner shell commands with inline filtering (e.g. `grep`, `cut`, `awk`, `jq`) to minimize latency.
* Ensure all coordinates are **integers** and **within screen bounds**.
* If an expected element is not visible, try scrolling or use coordinate-based input as a fallback.
* If tools are missing or return errors (e.g. permission denied, device offline), evaluate and recover or raise an exception with a clear reason.
* If stuck, apologize briefly and raise a structured exception with diagnostic info.
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
