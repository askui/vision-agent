from anthropic import Anthropic
from anthropic.types.beta import BetaMessage, BetaMessageParam
from typing_extensions import override

from askui.models.anthropic.settings import ClaudeComputerAgentSettings
from askui.models.models import ANTHROPIC_MODEL_NAME_MAPPING, ModelName
from askui.models.shared.computer_agent import ComputerAgent
from askui.reporting import Reporter
from askui.tools.agent_os import AgentOs


class ClaudeComputerAgent(ComputerAgent[ClaudeComputerAgentSettings]):
    def __init__(
        self,
        agent_os: AgentOs,
        reporter: Reporter,
        settings: ClaudeComputerAgentSettings,
    ) -> None:
        super().__init__(settings, agent_os, reporter)
        self._client = Anthropic(
            api_key=self._settings.anthropic.api_key.get_secret_value()
        )

    @override
    def _create_message(
        self, messages: list[BetaMessageParam], model_choice: str
    ) -> BetaMessage:
        response = self._client.beta.messages.with_raw_response.create(
            max_tokens=self._settings.max_tokens,
            messages=messages,
            model=ANTHROPIC_MODEL_NAME_MAPPING[ModelName(model_choice)],
            system=[self._system],
            tools=self._tool_collection.to_params(),
            betas=self._settings.betas,
        )
        return response.parse()
