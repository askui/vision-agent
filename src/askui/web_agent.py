import logging
from datetime import datetime, timezone

from pydantic import ConfigDict, validate_call
from typing_extensions import override

from askui.agent import VisionAgent
from askui.container import telemetry
from askui.models.shared.settings import (
    COMPUTER_USE_20241022_BETA_FLAG,
    COMPUTER_USE_20250124_BETA_FLAG,
    ActSettings,
    MessageSettings,
)
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
from .models.models import ModelChoice, ModelName, ModelRegistry
from .reporting import Reporter
from .retry import Retry

_SYSTEM_PROMPT = f"""
<SYSTEM_CAPABILITY>
* You are utilizing a webbrowser in full-screen mode. So you are only seeing the content of the currently opened webpage (tab).
* It can be helpful to zoom in/out or scroll down/up so that you can see everything on the page. Make sure to that before deciding something isn't available.
* When using your function calls, they take a while to run and send back to you.  Where possible/feasible, try to chain multiple of these calls all into one function calls request.
* The current date and time is {datetime.now(timezone.utc).strftime("%A, %B %d, %Y %H:%M:%S %z")}.
</SYSTEM_CAPABILITY>
"""

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


class WebVisionAgent(VisionAgent):
    @telemetry.record_call(exclude={"model_router", "reporters", "tools"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        log_level: int | str = logging.INFO,
        reporters: list[Reporter] | None = None,
        model: ModelChoice | ModelComposition | str | None = None,
        retry: Retry | None = None,
        models: ModelRegistry | None = None,
    ) -> None:
        agent_os = PlaywrightAgentOs()
        tools = AgentToolbox(
            agent_os=agent_os,
        )
        super().__init__(
            log_level=log_level,
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
            ],
        )

    @override
    def _get_default_settings_for_act(self, model_choice: str) -> ActSettings:
        match model_choice:
            case ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022:
                return _ANTHROPIC__CLAUDE__3_5__SONNET__20241022__ACT_SETTINGS
            case ModelName.CLAUDE__SONNET__4__20250514 | ModelName.ASKUI:
                return _CLAUDE__SONNET__4__20250514__ACT_SETTINGS
            case _:
                return ActSettings()
