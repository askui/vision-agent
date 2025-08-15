import logging
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ConfigDict, validate_call
from typing_extensions import override

from askui.models.shared.settings import (
    COMPUTER_USE_20241022_BETA_FLAG,
    COMPUTER_USE_20250124_BETA_FLAG,
    ActSettings,
    MessageSettings,
)
from askui.tools.testing.execution_tools import (
    CreateExecutionTool,
    DeleteExecutionTool,
    ListExecutionTool,
    ModifyExecutionTool,
    RetrieveExecutionTool,
)
from askui.tools.testing.feature_tools import (
    CreateFeatureTool,
    DeleteFeatureTool,
    ListFeatureTool,
    ModifyFeatureTool,
    RetrieveFeatureTool,
)
from askui.tools.testing.scenario_tools import (
    CreateScenarioTool,
    DeleteScenarioTool,
    ListScenarioTool,
    ModifyScenarioTool,
    RetrieveScenarioTool,
)
from askui.web_agent import WebVisionAgent

from .models.models import ModelChoice, ModelComposition, ModelName, ModelRegistry
from .reporting import Reporter
from .retry import Retry

_TESTING_SYSTEM_PROMPT = f"""
<SYSTEM_CAPABILITY>
* You are an autonomous exploratory web testing agent. Your job is to:
  - Analyze the application under test (AUT) at the given URL.
  - Use the provided user instructions to guide your testing focus.
  - Discover features and scenarios of the AUT, create and update test features and
    scenarios as you explore.
  - Execute scenarios and create/update test executions, recording results.
  - Identify gaps in feature/scenario coverage and prioritize the next most important
    feature/scenario for testing.
  - Use all available tools to create, retrieve, list, modify, and delete features,
    scenarios, and executions.
  - Use browser navigation and information tools to explore the AUT.
  - Be thorough, systematic, and creative in your exploration. Prioritize critical
    paths and user flows.
* You are utilizing a webbrowser in full-screen mode. So you are only seeing the
  content of the currently opened webpage (tab).
* It can be helpful to zoom in/out or scroll down/up so that you can see everything
  on the page. Make sure to that before deciding something isn't available.
* When using your function calls, they take a while to run and send back to you.
  Where possible/feasible, try to chain multiple of these calls all into one function
  calls request.
* The current date and time is \
  {datetime.now(timezone.utc).strftime("%A, %B %d, %Y %H:%M:%S %z")}.
</SYSTEM_CAPABILITY>
"""

_ANTHROPIC__CLAUDE__3_5__SONNET__20241022__ACT_SETTINGS = ActSettings(
    messages=MessageSettings(
        model=ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022,
        system=_TESTING_SYSTEM_PROMPT,
        betas=[COMPUTER_USE_20241022_BETA_FLAG],
    ),
)

_CLAUDE__SONNET__4__20250514__ACT_SETTINGS = ActSettings(
    messages=MessageSettings(
        model=ModelName.CLAUDE__SONNET__4__20250514,
        system=_TESTING_SYSTEM_PROMPT,
        betas=[COMPUTER_USE_20250124_BETA_FLAG],
        thinking={"type": "enabled", "budget_tokens": 2048},
    ),
)


class WebTestingAgent(WebVisionAgent):
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        log_level: int | str = logging.INFO,
        reporters: list[Reporter] | None = None,
        model: ModelChoice | ModelComposition | str | None = None,
        retry: Retry | None = None,
        models: ModelRegistry | None = None,
    ) -> None:
        base_dir = Path.cwd() / "chat" / "testing"
        base_dir.mkdir(parents=True, exist_ok=True)
        super().__init__(
            log_level=log_level,
            reporters=reporters,
            model=model,
            retry=retry,
            models=models,
            act_tools=[
                CreateFeatureTool(base_dir),
                RetrieveFeatureTool(base_dir),
                ListFeatureTool(base_dir),
                ModifyFeatureTool(base_dir),
                DeleteFeatureTool(base_dir),
                CreateScenarioTool(base_dir),
                RetrieveScenarioTool(base_dir),
                ListScenarioTool(base_dir),
                ModifyScenarioTool(base_dir),
                DeleteScenarioTool(base_dir),
                CreateExecutionTool(base_dir),
                RetrieveExecutionTool(base_dir),
                ListExecutionTool(base_dir),
                ModifyExecutionTool(base_dir),
                DeleteExecutionTool(base_dir),
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
