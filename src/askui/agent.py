import logging
import subprocess
from typing import Annotated, Literal, Optional

from pydantic import Field, validate_call

from .tools.askui.askui_controller import (
    AskUiControllerClient,
    AskUiControllerServer,
    PC_AND_MODIFIER_KEY,
    MODIFIER_KEY,
)
from .models.anthropic.claude import ClaudeHandler
from .models.anthropic.claude_agent import ClaudeComputerAgent
from .logging import logger, configure_logging
from .tools.toolbox import AgentToolbox
from .models.router import ModelRouter
from .reporting.report import SimpleReportGenerator
import time


class InvalidParameterError(Exception):
    pass

class VisionAgent:
    def __init__(
        self,
        log_level=logging.INFO,
        display: int = 1,
        enable_report: bool = False,
        enable_askui_controller: bool = True,
    ):
        configure_logging(level=log_level)
        self.report = None
        if enable_report:
            self.report = SimpleReportGenerator()
        self.controller = None
        self.client = None
        if enable_askui_controller:
            self.controller = AskUiControllerServer()
            self.controller.start(True)
            self.client = AskUiControllerClient(display, self.report)
            self.client.connect()
            self.client.set_display(display)
        self.model_router = ModelRouter(log_level)
        self.claude = ClaudeHandler(log_level=log_level)
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
            >>> with VisionAgent() as agent:
            >>>     agent.click()              # Left click on current position
            >>>     agent.click("Edit")        # Left click on text "Edit"
            >>>     agent.click("Edit", button="right")  # Right click on text "Edit"
            >>>     agent.click(repeat=2)      # Double left click on current position
            >>>     agent.click("Edit", button="middle", repeat=4)   # 4x middle click on text "edit
        """
        if repeat < 1:
            raise InvalidParameterError("InvalidParameterError! The parameter 'repeat' needs to be greater than 0.")
        self._check_askui_controller_enabled()
        if self.report is not None:
            msg = f'click'
            if button is not 'left':
                msg = f'{button} ' + msg 
            if repeat is not 1:
                msg += f' {repeat}x times'
            if instruction is not None:
                msg += f' on "{instruction}"'
            self.report.add_message("User", msg)
        if instruction is not None:
            logger.debug("VisionAgent received instruction to click '%s'", instruction)
            screenshot = self.client.screenshot() # type: ignore
            x, y = self.model_router.click(screenshot, instruction, model_name)
            if self.report is not None:
                self.report.add_message("ModelRouter", f"click: ({x}, {y})")
            self.client.mouse(x, y) # type: ignore
        self.client.click(button, repeat) # type: ignore

    def type(self, text: str) -> None:
        self._check_askui_controller_enabled()
        if self.report is not None:
            self.report.add_message("User", f'type: "{text}"')
        logger.debug("VisionAgent received instruction to type '%s'", text)
        self.client.type(text) # type: ignore

    def get(self, instruction: str) -> str:
        self._check_askui_controller_enabled()
        if self.report is not None:
            self.report.add_message("User", f'get: "{instruction}"')
        logger.debug("VisionAgent received instruction to get '%s'", instruction)
        screenshot = self.client.screenshot() # type: ignore
        response = self.claude.get_inference(screenshot, instruction)
        if self.report is not None:
            self.report.add_message("Agent", response)
        return response
    
    @validate_call
    def wait(self, sec: Annotated[float, Field(gt=0)]):
        """
        Pauses the execution of the program for the specified number of seconds.

        Args:
            sec (float): The number of seconds to wait. Must be greater than 0.

        Raises:
            ValueError: If the provided `sec` is negative.

        Example:
            >>> with VisionAgent() agent:
            >>>     agent.wait(5)  # Pauses execution for 5 seconds.
            >>>     agent.wait(0.5)  # Pauses execution for 500 milliseconds.
        """
        self._check_askui_controller_enabled()
        time.sleep(sec)

    def act(self, goal: str) -> None:
        self._check_askui_controller_enabled()
        if self.report is not None:
            self.report.add_message("User", f'act: "{goal}"')
        logger.debug(
            "VisionAgent received instruction to act towards the goal '%s'", goal
        )
        agent = ClaudeComputerAgent(self.client, self.report)
        agent.run(goal)

    def keyboard(
        self, key: PC_AND_MODIFIER_KEY, modifier_keys: list[MODIFIER_KEY] | None = None
    ) -> None:
        self._check_askui_controller_enabled()
        logger.debug("VisionAgent received instruction to press '%s'", key)
        self.client.keyboard_tap(key, modifier_keys)  # type: ignore

    def cli(self, command: str):
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
