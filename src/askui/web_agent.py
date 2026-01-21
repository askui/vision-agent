from pydantic import ConfigDict, validate_call

from askui.agent import VisionAgent
from askui.models.models import ActModel, GetModel, LocateModel
from askui.models.shared.settings import (
    ActSettings,
    MessageSettings,
)
from askui.models.shared.tools import Tool
from askui.prompts.act_prompts import WEB_AGENT_SYSTEM_PROMPT
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


class WebVisionAgent(VisionAgent):
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        reporters: list[Reporter] | None = None,
        act_model: ActModel | None = None,
        get_model: GetModel | None = None,
        locate_model: LocateModel | None = None,
        retry: Retry | None = None,
        act_tools: list[Tool] | None = None,
    ) -> None:
        agent_os = PlaywrightAgentOs()
        tools = AgentToolbox(
            agent_os=agent_os,
        )
        super().__init__(
            reporters=reporters,
            act_model=act_model,
            get_model=get_model,
            locate_model=locate_model,
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
                system=WEB_AGENT_SYSTEM_PROMPT,
                thinking={"type": "enabled", "budget_tokens": 2048},
            ),
        )
