import logging
import os
from typing import Any, Callable

from askui.models.anthropic.claude_android_agent import ClaudeAndroidAgent
from askui.tools.askui.askui_android_controller import AskUiAndroidControllerClient

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
        max_edge_size: int = 1200,
    ):
        load_dotenv()
        configure_logging(level=log_level)
        self.report = None
        if enable_report:
            self.report = SimpleReportGenerator(report_callback=report_callback)
        self.client = AskUiAndroidControllerClient(self.report)
        self.client.connect()
        self.tools = AgentToolbox(os_controller=self.client)
        self.max_edge_size = max_edge_size

    def act(self, goal: str, model_name=None) -> None:
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
        if self.report is not None:
            self.report.add_message("User", f'act: "{goal}"')
        logger.debug(
            "VisionAgent received instruction to act towards the goal '%s'", goal
        )
        if os.getenv("ANTHROPIC_API_KEY") is None:
            raise Exception(
                '"ANTHROPIC_API_KEY" not set. Please set it in your environment variables.'
            )
        agent = ClaudeAndroidAgent(self.client, self.report, self.max_edge_size)
        return agent.run(goal)

    def close(self):
        if self.client:
            self.client.disconnect()

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        self.close()
        if self.report is not None:
            self.report.generate_report()
