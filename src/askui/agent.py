import logging
import platform
import sys
from datetime import datetime, timezone
from typing import Annotated, Literal, Optional

from pydantic import ConfigDict, Field, validate_call
from typing_extensions import override

from askui.agent_base import AgentBase
from askui.container import telemetry
from askui.locators.locators import Locator
from askui.models.shared.settings import (
    COMPUTER_USE_20241022_BETA_FLAG,
    COMPUTER_USE_20250124_BETA_FLAG,
    ActSettings,
    MessageSettings,
)
from askui.models.shared.tools import Tool
from askui.tools.computer import Computer20241022Tool, Computer20250124Tool
from askui.tools.exception_tool import ExceptionTool

from .logger import logger
from .models import ModelComposition
from .models.models import ModelChoice, ModelName, ModelRegistry
from .reporting import CompositeReporter, Reporter
from .retry import Retry
from .tools import AgentToolbox, ModifierKey, PcKey
from .tools.askui import AskUiControllerClient

_SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are utilising a {sys.platform} machine using {platform.machine()} architecture with internet access.
* When asked to perform web tasks try to open the browser (firefox, chrome, safari, ...) if not already open. Often you can find the browser icons in the toolbars of the operating systems.
* When viewing a page it can be helpful to zoom out so that you can see everything on the page.  Either that, or make sure you scroll down to see everything before deciding something isn't available.
* When using your function calls, they take a while to run and send back to you.  Where possible/feasible, try to chain multiple of these calls all into one function calls request.
* The current date and time is {datetime.now(timezone.utc).strftime("%A, %B %d, %Y %H:%M:%S %z")}.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* When using Firefox, if a startup wizard appears, IGNORE IT.  Do not even click "skip this step".  Instead, click on the address bar where it says "Search or enter address", and enter the appropriate search term or URL there.
* If the item you are looking at is a pdf, if after taking a single screenshot of the pdf it seems that you want to read the entire document instead of trying to continue to read the pdf from your screenshots + navigation, determine the URL, use curl to download the pdf, install and use pdftotext to convert it to a text file, and then read that text file directly with your StrReplaceEditTool.
</IMPORTANT>"""  # noqa: DTZ002, E501


_ANTHROPIC__CLAUDE__3_5__SONNET__20241022__ACT_SETTINGS = ActSettings(
    messages=MessageSettings(
        model=ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022.value,
        system=_SYSTEM_PROMPT,
        betas=[COMPUTER_USE_20241022_BETA_FLAG],
    ),
)

_CLAUDE__SONNET__4__20250514__ACT_SETTINGS = ActSettings(
    messages=MessageSettings(
        model=ModelName.CLAUDE__SONNET__4__20250514.value,
        system=_SYSTEM_PROMPT,
        betas=[COMPUTER_USE_20250124_BETA_FLAG],
        thinking={"type": "enabled", "budget_tokens": 2048},
    ),
)


class VisionAgent(AgentBase):
    """
    A vision-based agent that can interact with user interfaces through computer vision and AI.

    This agent can perform various UI interactions like clicking, typing, scrolling, and more.
    It uses computer vision models to locate UI elements and execute actions on them.

    Args:
        log_level (int | str, optional): The logging level to use. Defaults to `logging.INFO`.
        display (int, optional): The display number to use for screen interactions. Defaults to `1`.
        reporters (list[Reporter] | None, optional): List of reporter instances for logging and reporting. If `None`, an empty list is used.
        tools (AgentToolbox | None, optional): Custom toolbox instance. If `None`, a default one will be created with `AskUiControllerClient`.
        model (ModelChoice | ModelComposition | str | None, optional): The default choice or name of the model(s) to be used for vision tasks. Can be overridden by the `model` parameter in the `click()`, `get()`, `act()` etc. methods.
        retry (Retry, optional): The retry instance to use for retrying failed actions. Defaults to `ConfigurableRetry` with exponential backoff. Currently only supported for `locate()` method.
        models (ModelRegistry | None, optional): A registry of models to make available to the `VisionAgent` so that they can be selected using the `model` parameter of `VisionAgent` or the `model` parameter of its `click()`, `get()`, `act()` etc. methods. Entries in the registry override entries in the default model registry.

    Example:
        ```python
        from askui import VisionAgent

        with VisionAgent() as agent:
            agent.click("Submit button")
            agent.type("Hello World")
            agent.act("Open settings menu")
        ```
    """

    @telemetry.record_call(exclude={"model_router", "reporters", "tools", "act_tools"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        log_level: int | str = logging.INFO,
        display: Annotated[int, Field(ge=1)] = 1,
        reporters: list[Reporter] | None = None,
        tools: AgentToolbox | None = None,
        model: ModelChoice | ModelComposition | str | None = None,
        retry: Retry | None = None,
        models: ModelRegistry | None = None,
        act_tools: list[Tool] | None = None,
    ) -> None:
        reporter = CompositeReporter(reporters=reporters)
        self.tools = tools or AgentToolbox(
            agent_os=AskUiControllerClient(
                display=display,
                reporter=reporter,
            )
        )
        super().__init__(
            log_level=log_level,
            reporter=reporter,
            model=model,
            retry=retry,
            models=models,
            tools=[
                ExceptionTool(),
            ]
            + (act_tools or []),
            agent_os=self.tools.os,
        )

    @telemetry.record_call(exclude={"locator"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def click(
        self,
        locator: Optional[str | Locator] = None,
        button: Literal["left", "middle", "right"] = "left",
        repeat: Annotated[int, Field(gt=0)] = 1,
        model: ModelComposition | str | None = None,
    ) -> None:
        """
        Simulates a mouse click on the user interface element identified by the provided locator.

        Args:
            locator (str | Locator | None, optional): The identifier or description of the element to click. If `None`, clicks at current position.
            button ('left' | 'middle' | 'right', optional): Specifies which mouse button to click. Defaults to `'left'`.
            repeat (int, optional): The number of times to click. Must be greater than `0`. Defaults to `1`.
            model (ModelComposition | str | None, optional): The composition or name of the model(s) to be used for locating the element to click on using the `locator`.

        Example:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                agent.click()              # Left click on current position
                agent.click("Edit")        # Left click on text "Edit"
                agent.click("Edit", button="right")  # Right click on text "Edit"
                agent.click(repeat=2)      # Double left click on current position
                agent.click("Edit", button="middle", repeat=4)   # 4x middle click on text "Edit"
            ```
        """
        msg = "click"
        if button != "left":
            msg = f"{button} " + msg
        if repeat > 1:
            msg += f" {repeat}x times"
        if locator is not None:
            msg += f" on {locator}"
        logger.debug("VisionAgent received instruction to %s", msg)
        self._reporter.add_message("User", msg)
        self._click(locator, button, repeat, model)

    def _click(
        self,
        locator: Optional[str | Locator],
        button: Literal["left", "middle", "right"],
        repeat: int,
        model: ModelComposition | str | None,
    ) -> None:
        if locator is not None:
            self._mouse_move(locator, model)
        self.tools.os.click(button, repeat)

    def _mouse_move(
        self, locator: str | Locator, model: ModelComposition | str | None = None
    ) -> None:
        point = self._locate(locator=locator, model=model)
        self.tools.os.mouse_move(point[0], point[1])

    @telemetry.record_call(exclude={"locator"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def mouse_move(
        self,
        locator: str | Locator,
        model: ModelComposition | str | None = None,
    ) -> None:
        """
        Moves the mouse cursor to the UI element identified by the provided locator.

        Args:
            locator (str | Locator): The identifier or description of the element to move to.
            model (ModelComposition | str | None, optional): The composition or name of the model(s) to be used for locating the element to move the mouse to using the `locator`.

        Example:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                agent.mouse_move("Submit button")  # Moves cursor to submit button
                agent.mouse_move("Close")  # Moves cursor to close element
                agent.mouse_move("Profile picture", model="custom_model")  # Uses specific model
            ```
        """
        self._reporter.add_message("User", f"mouse_move: {locator}")
        logger.debug("VisionAgent received instruction to mouse_move to %s", locator)
        self._mouse_move(locator, model)

    @telemetry.record_call()
    @validate_call
    def mouse_scroll(
        self,
        x: int,
        y: int,
    ) -> None:
        """
        Simulates scrolling the mouse wheel by the specified horizontal and vertical amounts.

        Args:
            x (int): The horizontal scroll amount. Positive values typically scroll right, negative values scroll left.
            y (int): The vertical scroll amount. Positive values typically scroll down, negative values scroll up.

        Note:
            The actual scroll direction depends on the operating system's configuration.
            Some systems may have "natural scrolling" enabled, which reverses the traditional direction.

            The meaning of scroll units varies across operating systems and applications.
            A scroll value of `10` might result in different distances depending on the application and system settings.

        Example:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                agent.mouse_scroll(0, 10)  # Usually scrolls down 10 units
                agent.mouse_scroll(0, -5)  # Usually scrolls up 5 units
                agent.mouse_scroll(3, 0)   # Usually scrolls right 3 units
            ```
        """
        self._reporter.add_message("User", f'mouse_scroll: "{x}", "{y}"')
        self.tools.os.mouse_scroll(x, y)

    @telemetry.record_call(exclude={"text", "locator"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def type(
        self,
        text: Annotated[str, Field(min_length=1)],
        locator: str | Locator | None = None,
        model: ModelComposition | str | None = None,
        clear: bool = True,
    ) -> None:
        """
        Types the specified text as if it were entered on a keyboard.

        If `locator` is provided, it will first click on the element to give it focus before typing.
        If `clear` is `True` (default), it will triple click on the element to select the current text (in multi-line inputs like textareas the current line or paragraph) before typing.

        **IMPORTANT:** `clear` only works if a `locator` is provided.

        Args:
            text (str): The text to be typed. Must be at least `1` character long.
            locator (str | Locator | None, optional): The identifier or description of the element (e.g., input field) to type into. If `None`, types at the current focus.
            model (ModelComposition | str | None, optional): The composition or name of the model(s) to be used for locating the element, i.e., input field, to type into using the `locator`.
            clear (bool, optional): Whether to triple click on the element to give it focus and select the current text before typing. Defaults to `True`.

        Example:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                agent.type("Hello, world!")  # Types "Hello, world!" at current focus
                agent.type("user@example.com", locator="Email")  # Clicks on "Email" input, then types
                agent.type("password123", locator="Password field", model="custom_model")  # Uses specific model
                agent.type("Hello, world!", locator="Textarea", clear=False)  # Types "Hello, world!" into textarea without clearing
            ```
        """
        msg = f'type "{text}"'
        if locator is not None:
            msg += f" into {locator}"
            if clear:
                repeat = 3
                msg += " clearing the current content (line/paragraph) of input field"
            else:
                repeat = 1
            self._click(locator=locator, button="left", repeat=repeat, model=model)
        logger.debug("VisionAgent received instruction to %s", msg)
        self._reporter.add_message("User", msg)
        self.tools.os.type(text)

    @telemetry.record_call()
    @validate_call
    def key_up(
        self,
        key: PcKey | ModifierKey,
    ) -> None:
        """
        Simulates the release of a key.

        Args:
            key (PcKey | ModifierKey): The key to be released.

        Example:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                agent.key_up('a')  # Release the 'a' key
                agent.key_up('shift')  # Release the 'Shift' key
            ```
        """
        self._reporter.add_message("User", f'key_up "{key}"')
        logger.debug("VisionAgent received in key_up '%s'", key)
        self.tools.os.keyboard_release(key)

    @telemetry.record_call()
    @validate_call
    def key_down(
        self,
        key: PcKey | ModifierKey,
    ) -> None:
        """
        Simulates the pressing of a key.

        Args:
            key (PcKey | ModifierKey): The key to be pressed.

        Example:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                agent.key_down('a')  # Press the 'a' key
                agent.key_down('shift')  # Press the 'Shift' key
            ```
        """
        self._reporter.add_message("User", f'key_down "{key}"')
        logger.debug("VisionAgent received in key_down '%s'", key)
        self.tools.os.keyboard_pressed(key)

    @telemetry.record_call()
    @validate_call
    def mouse_up(
        self,
        button: Literal["left", "middle", "right"] = "left",
    ) -> None:
        """
        Simulates the release of a mouse button.

        Args:
            button ('left' | 'middle' | 'right', optional): The mouse button to be released. Defaults to `'left'`.

        Example:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                agent.mouse_up()  # Release the left mouse button
                agent.mouse_up('right')  # Release the right mouse button
                agent.mouse_up('middle')  # Release the middle mouse button
            ```
        """
        self._reporter.add_message("User", f'mouse_up "{button}"')
        logger.debug("VisionAgent received instruction to mouse_up '%s'", button)
        self.tools.os.mouse_up(button)

    @telemetry.record_call()
    @validate_call
    def mouse_down(
        self,
        button: Literal["left", "middle", "right"] = "left",
    ) -> None:
        """
        Simulates the pressing of a mouse button.

        Args:
            button ('left' | 'middle' | 'right', optional): The mouse button to be pressed. Defaults to `'left'`.

        Example:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                agent.mouse_down()  # Press the left mouse button
                agent.mouse_down('right')  # Press the right mouse button
                agent.mouse_down('middle')  # Press the middle mouse button
            ```
        """
        self._reporter.add_message("User", f'mouse_down "{button}"')
        logger.debug("VisionAgent received instruction to mouse_down '%s'", button)
        self.tools.os.mouse_down(button)

    @override
    def _get_default_settings_for_act(self, model_choice: str) -> ActSettings:
        match model_choice:
            case ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022:
                return _ANTHROPIC__CLAUDE__3_5__SONNET__20241022__ACT_SETTINGS
            case ModelName.CLAUDE__SONNET__4__20250514 | ModelName.ASKUI:
                return _CLAUDE__SONNET__4__20250514__ACT_SETTINGS
            case _:
                return ActSettings()

    @override
    def _get_default_tools_for_act(self, model_choice: str) -> list[Tool]:
        match model_choice:
            case ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022:
                return self._tools + [Computer20241022Tool(agent_os=self.tools.os)]
            case ModelName.CLAUDE__SONNET__4__20250514 | ModelName.ASKUI:
                return self._tools + [Computer20250124Tool(agent_os=self.tools.os)]
            case _:
                return self._tools

    @telemetry.record_call()
    @validate_call
    def keyboard(
        self,
        key: PcKey | ModifierKey,
        modifier_keys: Optional[list[ModifierKey]] = None,
        repeat: Annotated[int, Field(gt=0)] = 1,
    ) -> None:
        """
        Simulates pressing (and releasing) a key or key combination on the keyboard.

        Args:
            key (PcKey | ModifierKey): The main key to press. This can be a letter, number, special character, or function key.
            modifier_keys (list[ModifierKey] | None, optional): List of modifier keys to press along with the main key. Common modifier keys include `'ctrl'`, `'alt'`, `'shift'`.
            repeat (int, optional): The number of times to press (and release) the key. Must be greater than `0`. Defaults to `1`.

        Example:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                agent.keyboard('a')  # Press 'a' key
                agent.keyboard('enter')  # Press 'Enter' key
                agent.keyboard('v', ['control'])  # Press Ctrl+V (paste)
                agent.keyboard('s', ['control', 'shift'])  # Press Ctrl+Shift+S
                agent.keyboard('a', repeat=2)  # Press 'a' key twice
            ```
        """
        msg = f"press and release key '{key}'"
        if modifier_keys is not None:
            modifier_keys_str = " + ".join(f"'{key}'" for key in modifier_keys)
            msg += f" with modifiers key{'s' if len(modifier_keys) > 1 else ''} {modifier_keys_str}"
        if repeat > 1:
            msg += f" {repeat}x times"
        self._reporter.add_message("User", msg)
        logger.debug("VisionAgent received instruction to press '%s'", key)
        self.tools.os.keyboard_tap(key, modifier_keys, count=repeat)

    @telemetry.record_call(exclude={"command"})
    @validate_call
    def cli(
        self,
        command: Annotated[str, Field(min_length=1)],
    ) -> None:
        """
        Executes a command on the command line interface.

        This method allows running shell commands directly from the agent. The command
        is split on spaces and executed as a subprocess.

        Args:
            command (str): The command to execute on the command line.

        Example:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                # Use for Windows
                agent.cli(fr'start "" "C:\Program Files\VideoLAN\VLC\vlc.exe"') # Start in VLC non-blocking
                agent.cli(fr'"C:\Program Files\VideoLAN\VLC\vlc.exe"') # Start in VLC blocking

                # Mac
                agent.cli("open -a chrome")  # Open Chrome non-blocking for mac
                agent.cli("chrome")  # Open Chrome blocking for linux
                agent.cli("echo Hello World")  # Prints "Hello World"
                agent.cli("python --version")  # Displays Python version

                # Linux
                agent.cli("nohub chrome")  # Open Chrome non-blocking for linux
                agent.cli("chrome")  # Open Chrome blocking for linux
                agent.cli("echo Hello World")  # Prints "Hello World"
                agent.cli("python --version")  # Displays Python version

            ```
        """
        logger.debug("VisionAgent received instruction to execute '%s' on cli", command)
        self.tools.os.run_command(command)
