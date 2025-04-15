import logging
import subprocess
from typing import Annotated, Literal, Optional, Type
from pydantic import Field, validate_call

from askui.container import telemetry
from askui.locators.locators import Locator
from askui.utils.image_utils import ImageSource

from .tools.askui.askui_controller import (
    AskUiControllerClient,
    AskUiControllerServer,
    ModifierKey,
    PcKey,
)
from .models.anthropic.claude import ClaudeHandler
from .logger import logger, configure_logging
from .tools.toolbox import AgentToolbox
from .models.router import ModelRouter, Point
from .reporting import CompositeReporter, Reporter
import time
from dotenv import load_dotenv
from PIL import Image
from .models.types import JsonSchema


class InvalidParameterError(Exception):
    pass


class VisionAgent:
    @telemetry.record_call(exclude={"model_router", "reporters", "tools"})
    def __init__(
        self,
        log_level=logging.INFO,
        display: int = 1,
        model_router: ModelRouter | None = None,
        reporters: list[Reporter] | None = None,
        tools: AgentToolbox | None = None,
    ) -> None:
        load_dotenv()
        configure_logging(level=log_level)
        self._reporter = CompositeReporter(reports=reporters or [])
        self.model_router = (
            ModelRouter(log_level=log_level, reporter=self._reporter)
            if model_router is None
            else model_router
        )
        self.claude = ClaudeHandler(log_level=log_level)
        self.tools = tools or AgentToolbox(os=AskUiControllerClient(display=display, reporter=self._reporter))
        self._controller = AskUiControllerServer()

    @telemetry.record_call(exclude={"locator"})
    def click(self, locator: Optional[str | Locator] = None, button: Literal['left', 'middle', 'right'] = 'left', repeat: int = 1, model_name: Optional[str] = None) -> None:
        """
        Simulates a mouse click on the user interface element identified by the provided locator.

        Parameters:
            locator (str | Locator | None): The identifier or description of the element to click.
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
        msg = 'click'
        if button != 'left':
            msg = f'{button} ' + msg 
        if repeat > 1:
            msg += f' {repeat}x times'
        if locator is not None:
            msg += f' on {locator}'
        self._reporter.add_message("User", msg)
        if locator is not None:
            logger.debug("VisionAgent received instruction to click on %s", locator)
            self._mouse_move(locator, model_name)
        self.tools.os.click(button, repeat) # type: ignore
    
    def _locate(self, locator: str | Locator, screenshot: Optional[Image.Image] = None, model_name: Optional[str] = None) -> Point:
        if screenshot is None:
            screenshot = self.tools.os.screenshot() # type: ignore
        point = self.model_router.locate(screenshot, locator, model_name)
        self._reporter.add_message("ModelRouter", f"locate: ({point[0]}, {point[1]})")
        return point
    
    def locate(self, locator: str | Locator, screenshot: Optional[Image.Image] = None, model_name: Optional[str] = None) -> Point:
        self._reporter.add_message("User", f"locate {locator}")
        logger.debug("VisionAgent received instruction to locate %s", locator)
        return self._locate(locator, screenshot, model_name)

    def _mouse_move(self, locator: str | Locator, model_name: Optional[str] = None) -> None:
        point = self._locate(locator=locator, model_name=model_name)
        self.tools.os.mouse(point[0], point[1]) # type: ignore

    @telemetry.record_call(exclude={"locator"})
    def mouse_move(self, locator: str | Locator, model_name: Optional[str] = None) -> None:
        """
        Moves the mouse cursor to the UI element identified by the provided locator.

        Parameters:
            locator (str | Locator): The identifier or description of the element to move to.
            model_name (str | None): The model name to be used for element detection. Optional.

        Example:
        ```python
        with VisionAgent() as agent:
            agent.mouse_move("Submit button")  # Moves cursor to submit button
            agent.mouse_move("Close")  # Moves cursor to close element
            agent.mouse_move("Profile picture", model_name="custom_model")  # Uses specific model
        ```
        """
        self._reporter.add_message("User", f'mouse_move: {locator}')
        logger.debug("VisionAgent received instruction to mouse_move to %s", locator)
        self._mouse_move(locator, model_name)

    @telemetry.record_call()
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
        self._reporter.add_message("User", f'mouse_scroll: "{x}", "{y}"')
        self.tools.os.mouse_scroll(x, y)

    @telemetry.record_call(exclude={"text"})
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
        self._reporter.add_message("User", f'type: "{text}"')
        logger.debug("VisionAgent received instruction to type '%s'", text)
        self.tools.os.type(text) # type: ignore

    @telemetry.record_call(exclude={"query", "image", "response_schema"})
    def get(
        self,
        query: str,
        image: Optional[ImageSource] = None,
        response_schema: Type[JsonSchema] | None = None,
        model_name: Optional[str] = None,
    ) -> JsonSchema | str:
        """
        Retrieves information from an image (defaults to a screenshot of the current screen) based on the provided query.

        Parameters:
            query (str): 
                The query describing what information to retrieve.
            image (ImageSource | None): 
                The image to extract information from. Optional. Defaults to a screenshot of the current screen.
            response_schema (type[ResponseSchema] | None): 
                A Pydantic model class that defines the response schema. Optional. If not provided, returns a string.
            model_name (str | None):
                The model name to be used for information extraction. Optional.
                Note: response_schema is only supported with models that support JSON output (like the default askui model).

        Returns:
            ResponseSchema | str: The extracted information, either as a Pydantic model instance or a string.

        Limitations:
            - Nested Pydantic schemas are not currently supported
            - Schema support is only available with "askui" model (default model if `ASKUI_WORKSPACE_ID` and `ASKUI_TOKEN` are set) at the moment

        Example:
        ```python
        from askui import JsonSchemaBase

        class UrlResponse(JsonSchemaBase):
            url: str

        with VisionAgent() as agent:
            # Get URL as string
            url = agent.get("What is the current url shown in the url bar?")
            
            # Get URL as Pydantic model
            response = agent.get(
                "What is the current url shown in the url bar?",
                response_schema=UrlResponse
            )
            print(response.url)
        ```
        """
        self._reporter.add_message("User", f'get: "{query}"')
        logger.debug("VisionAgent received instruction to get '%s'", query)
        if image is None:
            image = ImageSource(self.tools.os.screenshot()) # type: ignore
        response = self.model_router.get_inference(
            image=image,
            query=query,
            model_name=model_name,
            response_schema=response_schema,
        )
        if self._reporter is not None:
            message_content = response if isinstance(response, str) else response.model_dump()
            self._reporter.add_message("Agent", message_content)
        return response
    
    @telemetry.record_call()
    @validate_call
    def wait(self, sec: Annotated[float, Field(gt=0)]) -> None:
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

    @telemetry.record_call()
    def key_up(self, key: PcKey | ModifierKey) -> None:
        """
        Simulates the release of a key.

        Parameters:
            key (PcKey | ModifierKey): The key to be released.

        Example:
        ```python
        with VisionAgent() as agent:
            agent.key_up('a')  # Release the 'a' key
            agent.key_up('shift')  # Release the 'Shift' key
        ```
        """
        self._reporter.add_message("User", f'key_up "{key}"')
        logger.debug("VisionAgent received in key_up '%s'", key)
        self.tools.os.keyboard_release(key)

    @telemetry.record_call()
    def key_down(self, key: PcKey | ModifierKey) -> None:
        """
        Simulates the pressing of a key.

        Parameters:
            key (PcKey | ModifierKey): The key to be pressed.

        Example:
        ```python
        with VisionAgent() as agent:
            agent.key_down('a')  # Press the 'a' key
            agent.key_down('shift')  # Press the 'Shift' key
        ```
        """
        self._reporter.add_message("User", f'key_down "{key}"')
        logger.debug("VisionAgent received in key_down '%s'", key)
        self.tools.os.keyboard_pressed(key)

    @telemetry.record_call(exclude={"goal"})
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
        self._reporter.add_message("User", f'act: "{goal}"')
        logger.debug(
            "VisionAgent received instruction to act towards the goal '%s'", goal
        )
        self.model_router.act(self.tools.os, goal, model_name)

    @telemetry.record_call()
    def keyboard(
        self, key: PcKey | ModifierKey, modifier_keys: list[ModifierKey] | None = None
    ) -> None:
        """
        Simulates pressing a key or key combination on the keyboard.

        Parameters:
            key (PcKey | ModifierKey): The main key to press. This can be a letter, number, 
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
        logger.debug("VisionAgent received instruction to press '%s'", key)
        self.tools.os.keyboard_tap(key, modifier_keys)  # type: ignore

    @telemetry.record_call(exclude={"command"})
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

    @telemetry.record_call(flush=True)
    def close(self) -> None:
        self.tools.os.disconnect()
        if self._controller:
            self._controller.stop(True)
        self._reporter.generate()
            
    @telemetry.record_call()
    def open(self) -> None:
        self._controller.start(True)
        self.tools.os.connect()

    @telemetry.record_call()
    def __enter__(self) -> "VisionAgent":
        self.open()
        return self

    @telemetry.record_call(exclude={"exc_value", "traceback"})
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
