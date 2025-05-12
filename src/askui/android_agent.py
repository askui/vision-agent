import logging
import os
import time
from typing import Annotated, Any, Callable, List
from PIL import Image
from pydantic import Field, validate_call

from askui.models.anthropic.claude_android_agent import ClaudeAndroidAgent
from askui.tools.askui.askui_android_controller import (
    AndroidDisplay,
    AskUiAndroidControllerClient,
)

from .logging import logger, configure_logging
from .tools.toolbox import AgentToolbox
from .reporting.report import SimpleReportGenerator
from dotenv import load_dotenv


class InvalidParameterError(Exception):
    pass


class AndroidVisionAgent:
    def __init__(
        self,
        log_level=logging.INFO,
        enable_report: bool = False,
        report_callback: Callable[[str | dict[str, Any]], None] | None = None,
        file_tool_base_dir_path: str | None = None,
    ):
        load_dotenv()
        configure_logging(level=log_level)
        self.report = None
        if enable_report:
            self.report = SimpleReportGenerator(report_callback=report_callback)
        self.client = AskUiAndroidControllerClient(self.report)
        self.client.connect()
        self.tools = AgentToolbox(os_controller=self.client)
        self.claudeAgent = ClaudeAndroidAgent(
            self.client, self.report, file_tool_base_dir_path
        )

    def act(self, goal: str) -> None:
        """
        Instructs the agent to achieve a specified goal through autonomous actions.

        The agent will analyze the screen, determine necessary steps, and perform actions
        to accomplish the goal. This may include clicking, typing, scrolling, and other
        interface interactions.

        Parameters:
            goal (str): A description of what the agent should achieve.

        Example:
        ```python
        with AndroidVisionAgent() as agent:
            agent.act("Open the settings menu")
            agent.act("Search for 'printer' in the search box")
            agent.act("Log in with username 'admin' and password '1234'")
        ```
        """
        if self.report is not None:
            self.report.add_message("User", f'act: "{goal}"')
        logger.debug(
            "VisionAgent received instruction to act towards the goal '%s'", goal
        )
        if os.getenv("ANTHROPIC_API_KEY") is None:
            raise Exception(
                '"ANTHROPIC_API_KEY" not set. Please set it in your environment variables.'
            )
        return self.claudeAgent.run(goal)

    def close(self):
        if self.client:
            self.client.disconnect()

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        self.close()
        if self.report is not None:
            self.report.generate_report()

    def screenshot(self, report: bool = True) -> Image.Image:
        """
        Take a screenshot from the currently connected Android device.
        Args:
            report (bool): Whether to add the screenshot to the report. Default is True.
        Returns:
            Image.Image: The screenshot image.
        """
        return self.client.screenshot(report=report)

    def tap(self, x: int, y: int) -> None:
        """
        Simulate a tap (touch) gesture at the given (x, y) coordinates on the Android device screen.
        Args:
            x (int): The X coordinate.
            y (int): The Y coordinate.
        """
        return self.client.tap(x, y)

    def swipe(
        self, x1: int, y1: int, x2: int, y2: int, duration_in_ms: int = 1000
    ) -> None:
        """
        Simulate a swipe gesture on the Android screen from point (x1, y1) to (x2, y2).
        Args:
            x1 (int): Start X position.
            y1 (int): Start Y position.
            x2 (int): End X position.
            y2 (int): End Y position.
            duration_in_ms (int): Duration of swipe in milliseconds. Default is 1000.
        """
        return self.client.swipe(x1, y1, x2, y2, duration_in_ms)

    def drag_and_drop(
        self, x1: int, y1: int, x2: int, y2: int, duration_in_ms: int = 1000
    ) -> None:
        """
        Simulate a drag-and-drop gesture on the Android device from (x1, y1) to (x2, y2).
        Args:
            x1 (int): Start X coordinate.
            y1 (int): Start Y coordinate.
            x2 (int): End X coordinate.
            y2 (int): End Y coordinate.
            duration_in_ms (int): Duration of drag in milliseconds. Default is 1000.
        """
        return self.client.drag_and_drop(x1, y1, x2, y2, duration_in_ms)

    def move_mouse(self, x: int, y: int) -> None:
        """
        Move the virtual mouse to the given coordinates on the Android screen.
        Args:
            x (int): Target X coordinate.
            y (int): Target Y coordinate.
        """
        return self.client.move_mouse(x, y)

    def roll(self, dx: int, dy: int) -> None:
        """
        Simulate a mouse scroll (roll) action by the given dx, dy deltas.
        Args:
            dx (int): Scroll delta along X-axis.
            dy (int): Scroll delta along Y-axis.
        """
        return self.client.roll(dx, dy)

    def shell(self, command: str) -> str:
        """
        Execute a raw shell command on the Android device using ADB and return the output.
        Args:
            command (str): A valid shell command string to run on the Android device.
        Returns:
            str: The output of the shell command.
        """
        return self.client.shell(command)

    def get_cursor_position(self) -> tuple[int, int]:
        """
        Returns the current internal mouse position (as tracked by the controller) on the Android device.
        Returns:
            tuple[int, int]: The current mouse position (x, y).
        """
        return self.client.get_cursor_position()

    def get_connected_displays(self) -> List[AndroidDisplay]:
        """
        Returns a list of connected displays on the Android device.
        Returns:
            list: List of AndroidDisplay objects.
        """
        return self.client.get_connected_displays()

    def set_display_by_index(self, displayNumber: int = 0) -> None:
        """
        Select a specific display on the Android device by index.
        Args:
            displayNumber (int): The index of the display to select. Starts from 0.
        """
        return self.client.set_display_by_index(displayNumber)

    def set_display_by_id(self, display_id: int) -> None:
        """
        Select a specific display on the Android device by unique display ID.
        Args:
            display_id (int): The unique display ID.
        """
        return self.client.set_display_by_id(display_id)

    def set_display_by_name(self, display_name: str) -> None:
        """
        Select a specific display on the Android device by display name.
        Args:
            display_name (str): The name of the display to select.
        """
        return self.client.set_display_by_name(display_name)

    def set_device_by_index(self, displayNumber: int = 1) -> None:
        """
        Select a specific device by its index.
        Args:
            displayNumber (int): The index of the device to select. Starts from 1.
        """
        return self.client.set_device_by_index(displayNumber)

    def set_device_by_name(self, displayName: str) -> None:
        """
        Select a specific device by its serial name.
        Args:
            displayName (str): The serial name of the device to select.
        """
        return self.client.set_device_by_name(displayName)

    @validate_call
    def wait(self, sec: Annotated[float, Field(gt=0)]):
        """
        Pauses the execution of the program for the specified number of seconds.

        Parameters:
            sec (float): The number of seconds to wait. Must be greater than 0.

        Raises:
            ValueError: If the provided `sec` is negative.

        Example:
        ```python
        with VisionAgent() as agent:
            agent.wait(5)  # Pauses execution for 5 seconds
            agent.wait(0.5)  # Pauses execution for 500 milliseconds
        ```
        """
        time.sleep(sec)
