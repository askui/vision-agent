from pydantic import ConfigDict, validate_call

from askui.agent import ComputerAgent
from askui.agent_settings import AgentSettings
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

from .reporting import Reporter
from .retry import Retry


class WebVisionAgent(ComputerAgent):
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        reporters: list[Reporter] | None = None,
        settings: AgentSettings | None = None,
        retry: Retry | None = None,
        act_tools: list[Tool] | None = None,
    ) -> None:
        agent_os = PlaywrightAgentOs()
        tools = AgentToolbox(
            agent_os=agent_os,
        )
        super().__init__(
            reporters=reporters,
            settings=settings,
            retry=retry,
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
        )
        self.act_settings = ActSettings(
            messages=MessageSettings(
                system=create_web_agent_prompt(),
                thinking={"type": "enabled", "budget_tokens": 2048},
            ),
        )
