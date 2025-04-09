import logging
import subprocess
from typing import Annotated, Any, Literal, Optional, Callable

from pydantic import Field, validate_call

from .tools.askui.askui_controller import (
    AskUiControllerClient,
    AskUiControllerServer,
    PC_AND_MODIFIER_KEY,
    MODIFIER_KEY,
)
from .logging import logger, configure_logging
from .tools.toolbox import AgentToolbox
from .models.router import ModelRouter
from .reporting.report import SimpleReportGenerator
import time
from dotenv import load_dotenv
from PIL import Image

class InvalidParameterError(Exception):
    pass


class VisionAgent:
    def __init__(
        self,
        log_level=logging.INFO,
        display: int = 1,
        enable_report: bool = False,
        enable_askui_controller: bool = True,
        report_callback: Callable[[str | dict[str, Any]], None] | None = None,
    ):
        load_dotenv()
        configure_logging(level=log_level)
        self.report = None
        if enable_report:
            self.report = SimpleReportGenerator(report_callback=report_callback)
        self.controller = None
        self.client = None
        if enable_askui_controller:
            self.controller = AskUiControllerServer()
            self.controller.start(True, (logger.level == logging.DEBUG))
            time.sleep(0.5)
            self.client = AskUiControllerClient(display, self.report)
            self.client.connect()
            self.client.set_display(display)
        self.model_router = ModelRouter(log_level, self.report)
        self.tools = AgentToolbox(os_controller=self.client)

    def _check_askui_controller_enabled(self) -> None:
        if not self.client:
            raise ValueError(
                "AskUI Controller is not initialized. Please, set `enable_askui_controller` to `True` when initializing the `VisionAgent`."
            )


    def click(self, instruction: Optional[str] = None, button: Literal['left', 'middle', 'right'] = 'left', repeat: int = 1, model_name: Optional[str] = None) -> None:
        """
        Simulates a mouse click on the user interface element identified by the provided instruction.

        Parameters:
            instruction (str | None): The identifier or description of the element to click.
            button ('left' | 'middle' | 'right'): Specifies which mouse button to click. Defaults to 'left'.
            repeat (int): The number of times to click. Must be greater than 0. Defaults to 1.
            model_name (str | None): The model name to be used for element detection. Optional.

        Raises:
            InvalidParameterError: If the 'repeat' parameter is less than 1.

        Example:
        ```python
        with VisionAgent() as agent:
            agent.click()              # Left click on current position
            agent.click("Edit")        # Left click on text "Edit"
            agent.click("Edit", button="right")  # Right click on text "Edit"
            agent.click(repeat=2)      # Double left click on current position
            agent.click("Edit", button="middle", repeat=4)   # 4x middle click on text "Edit"
        ```
        """
        if repeat < 1:
            raise InvalidParameterError("InvalidParameterError! The parameter 'repeat' needs to be greater than 0.")
        self._check_askui_controller_enabled()
        if self.report is not None:
            msg = 'click'
            if button != 'left':
                msg = f'{button} ' + msg 
            if repeat > 1:
                msg += f' {repeat}x times'
            if instruction is not None:
                msg += f' on "{instruction}"'
            self.report.add_message("User", msg)
        if instruction is not None:
            logger.debug("VisionAgent received instruction to click '%s'", instruction)
            self.__mouse_move(instruction, model_name)
        self.client.click(button, repeat) # type: ignore

    def __mouse_move(self, instruction: str, model_name: Optional[str] = None) -> None:
        self._check_askui_controller_enabled()
        screenshot = self.client.screenshot() # type: ignore
        x, y = self.model_router.locate(screenshot, instruction, model_name)
        if self.report is not None:
            self.report.add_message("ModelRouter", f"locate: ({x}, {y})")
        self.client.mouse(x, y) # type: ignore

    def mouse_move(self, instruction: str, model_name: Optional[str] = None) -> None:
        """
        Moves the mouse cursor to the UI element identified by the provided instruction.

        Parameters:
            instruction (str): The identifier or description of the element to move to.
            model_name (str | None): The model name to be used for element detection. Optional.

        Example:
        ```python
        with VisionAgent() as agent:
            agent.mouse_move("Submit button")  # Moves cursor to submit button
            agent.mouse_move("Close")  # Moves cursor to close element
            agent.mouse_move("Profile picture", model_name="custom_model")  # Uses specific model
        ```
        """
        if self.report is not None:
            self.report.add_message("User", f'mouse_move: "{instruction}"')
        logger.debug("VisionAgent received instruction to mouse_move '%s'", instruction)
        self.__mouse_move(instruction, model_name)

    def mouse_scroll(self, x: int, y: int) -> None:
        """
        Simulates scrolling the mouse wheel by the specified horizontal and vertical amounts.

        Parameters:
            x (int): The horizontal scroll amount. Positive values typically scroll right, negative values scroll left.
            y (int): The vertical scroll amount. Positive values typically scroll down, negative values scroll up.

        Note:
            The actual `scroll direction` depends on the operating system's configuration.
            Some systems may have "natural scrolling" enabled, which reverses the traditional direction.
            
            The meaning of scroll `units` varies` acro`ss oper`ating` systems and applications.
            A scroll value of 10 might result in different distances depending on the application and system settings.

        Example:
        ```python
        with VisionAgent() as agent:
            agent.mouse_scroll(0, 10)  # Usually scrolls down 10 units
            agent.mouse_scroll(0, -5)  # Usually scrolls up 5 units
            agent.mouse_scroll(3, 0)   # Usually scrolls right 3 units
        ```
        """
        self._check_askui_controller_enabled()
        if self.report is not None:
            self.report.add_message("User", f'mouse_scroll: "{x}", "{y}"')
        self.client.mouse_scroll(x, y)

    def type(self, text: str) -> None:
        """
        Types the specified text as if it were entered on a keyboard.

        Parameters:
            text (str): The text to be typed.

        Example:
        ```python
        with VisionAgent() as agent:
            agent.type("Hello, world!")  # Types "Hello, world!"
            agent.type("user@example.com")  # Types an email address
            agent.type("password123")  # Types a password
        ```
        """
        self._check_askui_controller_enabled()
        if self.report is not None:
            self.report.add_message("User", f'type: "{text}"')
        logger.debug("VisionAgent received instruction to type '%s'", text)
        self.client.type(text) # type: ignore

    def get(self, instruction: str, model_name: Optional[str] = None, screenshot: Optional[Image.Image] = None) -> str:
        """
        Retrieves text or information from the screen based on the provided instruction.

        Parameters:
            instruction (str): The instruction describing what information to retrieve.
            model_name (str | None): The model name to be used for information extraction. Optional.

        Returns:
            str: The extracted text or information.

        Example:
        ```python
        with VisionAgent() as agent:
            price = agent.get("What is the price displayed?")
            username = agent.get("What is the username shown in the profile?")
            error_message = agent.get("What does the error message say?")
        ```
        """
        self._check_askui_controller_enabled()
        if self.report is not None:
            self.report.add_message("User", f'get: "{instruction}"')
        logger.debug("VisionAgent received instruction to get '%s'", instruction)
        if screenshot is None:
            screenshot = self.client.screenshot() # type: ignore
        response = self.model_router.get_inference(screenshot, instruction, model_name)
        if self.report is not None:
            self.report.add_message("Agent", response)
        return response
    
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

    def key_up(self, key: PC_AND_MODIFIER_KEY):
        """
        Simulates the release of a key.

        Parameters:
            key (PC_AND_MODIFIER_KEY): The key to be released.

        Example:
        ```python
        with VisionAgent() as agent:
            agent.key_up('a')  # Release the 'a' key
            agent.key_up('shift')  # Release the 'Shift' key
        ```
        """
        self._check_askui_controller_enabled()
        if self.report is not None:
            self.report.add_message("User", f'key_up "{key}"')
        logger.debug("VisionAgent received in key_up '%s'", key)
        self.client.keyboard_release(key)

    def key_down(self, key: PC_AND_MODIFIER_KEY):
        """
        Simulates the pressing of a key.

        Parameters:
            key (PC_AND_MODIFIER_KEY): The key to be pressed.

        Example:
        ```python
        with VisionAgent() as agent:
            agent.key_down('a')  # Press the 'a' key
            agent.key_down('shift')  # Press the 'Shift' key
        ```
        """
        self._check_askui_controller_enabled()
        if self.report is not None:
            self.report.add_message("User", f'key_down "{key}"')
        logger.debug("VisionAgent received in key_down '%s'", key)
        self.client.keyboard_pressed(key)

    def act(self, goal: str, model_name: Optional[str] = None) -> None:
        """
        Instructs the agent to achieve a specified goal through autonomous actions.

        The agent will analyze the screen, determine necessary steps, and perform actions
        to accomplish the goal. This may include clicking, typing, scrolling, and other
        interface interactions.

        Parameters:
            goal (str): A description of what the agent should achieve.
            model_name (str | None): The specific model to use for vision analysis.
                If None, uses the default model.

        Example:
        ```python
        with VisionAgent() as agent:
            agent.act("Open the settings menu")
            agent.act("Search for 'printer' in the search box")
            agent.act("Log in with username 'admin' and password '1234'")
        ```
        """
        self._check_askui_controller_enabled()
        if self.report is not None:
            self.report.add_message("User", f'act: "{goal}"')
        logger.debug(
            "VisionAgent received instruction to act towards the goal '%s'", goal
        )
        self.model_router.act(self.client, goal, model_name)

    def keyboard(
        self, key: PC_AND_MODIFIER_KEY, modifier_keys: list[MODIFIER_KEY] | None = None
    ) -> None:
        """
        Simulates pressing a key or key combination on the keyboard.

        Parameters:
            key (PC_AND_MODIFIER_KEY): The main key to press. This can be a letter, number, 
                special character, or function key.
            modifier_keys (list[MODIFIER_KEY] | None): Optional list of modifier keys to press 
                along with the main key. Common modifier keys include 'ctrl', 'alt', 'shift'.

        Example:
        ```python
        with VisionAgent() as agent:
            agent.keyboard('a')  # Press 'a' key
            agent.keyboard('enter')  # Press 'Enter' key
            agent.keyboard('v', ['control'])  # Press Ctrl+V (paste)
            agent.keyboard('s', ['control', 'shift'])  # Press Ctrl+Shift+S
        ```
        """
        self._check_askui_controller_enabled()
        logger.debug("VisionAgent received instruction to press '%s'", key)
        self.client.keyboard_tap(key, modifier_keys)  # type: ignore

    def cli(self, command: str) -> None:
        """
        Executes a command on the command line interface.

        This method allows running shell commands directly from the agent. The command
        is split on spaces and executed as a subprocess.

        Parameters:
            command (str): The command to execute on the command line.

        Example:
        ```python
        with VisionAgent() as agent:
            agent.cli("echo Hello World")  # Prints "Hello World"
            agent.cli("ls -la")  # Lists files in current directory with details
            agent.cli("python --version")  # Displays Python version
        ```
        """
        logger.debug("VisionAgent received instruction to execute '%s' on cli", command)
        subprocess.run(command.split(" "))

    def close(self):
        if self.client:
            self.client.disconnect()
        if self.controller:
            self.controller.stop(True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        if self.report is not None:
            self.report.generate_report()
