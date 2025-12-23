from pathlib import Path

from pydantic import ConfigDict, validate_call
from typing_extensions import override

from askui.models.shared.settings import (
    COMPUTER_USE_20250124_BETA_FLAG,
    ActSettings,
    MessageSettings,
)
from askui.prompts.system import TESTING_AGENT_SYSTEM_PROMPT
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

from .reporting import Reporter
from .retry import Retry


class WebTestingAgent(WebVisionAgent):
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        reporters: list[Reporter] | None = None,
        model_name: str | None = None,
        retry: Retry | None = None,
    ) -> None:
        base_dir = Path.cwd() / "chat" / "testing"
        base_dir.mkdir(parents=True, exist_ok=True)
        super().__init__(
            reporters=reporters,
            model_name=model_name,
            retry=retry,
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
    def _get_default_settings_for_act(self) -> ActSettings:
        return ActSettings(
            messages=MessageSettings(
                system=TESTING_AGENT_SYSTEM_PROMPT,
                betas=[COMPUTER_USE_20250124_BETA_FLAG],
                thinking={"type": "enabled", "budget_tokens": 2048},
            ),
        )
