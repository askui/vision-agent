from pydantic import ConfigDict, validate_call
from typing_extensions import override

from askui.agent import VisionAgent
from askui.models.shared.settings import (
    COMPUTER_USE_20250124_BETA_FLAG,
    ActSettings,
    MessageSettings,
)
from askui.models.shared.tools import Tool
from askui.prompts.system import WEB_AGENT_SYSTEM_PROMPT
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
    ) -> None:
        agent_os = PlaywrightAgentOs()
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

    @override
    def _get_default_settings_for_act(self, model: str) -> ActSettings:
        return ActSettings(
            messages=MessageSettings(
                system=WEB_AGENT_SYSTEM_PROMPT,
                betas=[COMPUTER_USE_20250124_BETA_FLAG],
                thinking={"type": "enabled", "budget_tokens": 2048},
            ),
        )
