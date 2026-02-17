import logging
from typing import Literal

from pydantic import ConfigDict, validate_call

from askui.agent import VisionAgent
from askui.models.shared.settings import (
    ActSettings,
    MessageSettings,
)
from askui.models.shared.tools import Tool
from askui.prompts.act_prompts import create_web_agent_prompt
from askui.tools.exception_tool import ExceptionTool
from askui.tools.playwright.agent_os import PlaywrightAgentOs
from askui.tools.playwright.tools import (
    PlaywrightBackTool,
    PlaywrightForwardTool,
    PlaywrightGetPageTitleTool,
    PlaywrightGetPageUrlTool,
    PlaywrightGotoTool,
)
from askui.tools.toolbox import AgentToolbox

from .models import ModelComposition
from .models.models import ModelChoice, ModelRegistry
from .reporting import Reporter
from .retry import Retry

logger = logging.getLogger(__name__)


class WebVisionAgent(VisionAgent):
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        reporters: list[Reporter] | None = None,
        model: ModelChoice | ModelComposition | str | None = None,
        retry: Retry | None = None,
        models: ModelRegistry | None = None,
        act_tools: list[Tool] | None = None,
        model_provider: str | None = None,
        headless: bool = False,
        browser_type: Literal["chromium", "firefox", "webkit"] = "chromium",
        slow_mo: int = 0,
    ) -> None:
        agent_os = PlaywrightAgentOs(
            headless=headless,
            browser_type=browser_type,
            slow_mo=slow_mo,
        )
        tools = AgentToolbox(
            agent_os=agent_os,
        )
        super().__init__(
            reporters=reporters,
            model=model,
            retry=retry,
            models=models,
            tools=tools,
            act_tools=[
                PlaywrightGotoTool(agent_os=agent_os),
                PlaywrightBackTool(agent_os=agent_os),
                PlaywrightForwardTool(agent_os=agent_os),
                PlaywrightGetPageTitleTool(agent_os=agent_os),
                PlaywrightGetPageUrlTool(agent_os=agent_os),
                ExceptionTool(),
            ]
            + (act_tools or []),
            model_provider=model_provider,
        )
        self.act_settings = ActSettings(
            messages=MessageSettings(
                system=create_web_agent_prompt(),
                thinking={"type": "enabled", "budget_tokens": 2048},
            ),
        )

    def solve_common_hurdles(self) -> None:
        """
        Attempts to solve common web hurdles like cookie banners, popups, and overlays
        using heuristic reasoning. This is called automatically during complex tasks
        or can be invoked manually to clear the workspace.
        """
        logger.info("Invoking heuristic recovery to clear common web hurdles...")
        self.act(
            "Look for any cookie banners, popups, newsletter signups, or other overlays "
            "that might be obstructing the main content or preventing interactions. "
            "If found, close them by clicking the 'X', 'Close', 'Accept', or 'Decline' "
            "buttons as appropriate. If no hurdles are detected, do nothing."
        )
