import logging
import subprocess

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

    def click(self, instruction: str, model_name: str | None = None) -> None:
        self._check_askui_controller_enabled()
        if self.report is not None:
            self.report.add_message("User", f'click: "{instruction}"')
        logger.debug("VisionAgent received instruction to click '%s'", instruction)
        screenshot = self.client.screenshot() # type: ignore
        x, y = self.model_router.click(screenshot, instruction, model_name)
        if self.report is not None:
            self.report.add_message("ModelRouter", f"click: ({x}, {y})")
        self.client.mouse(x, y) # type: ignore
        self.client.click("left") # type: ignore

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
