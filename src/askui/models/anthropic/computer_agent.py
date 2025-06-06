from typing import TYPE_CHECKING, cast

from anthropic import Anthropic
from typing_extensions import override

from askui.models.anthropic.settings import ClaudeComputerAgentSettings
from askui.models.models import ANTHROPIC_MODEL_NAME_MAPPING, ModelName
from askui.models.shared.computer_agent import ComputerAgent
from askui.models.shared.computer_agent_message_param import MessageParam
from askui.reporting import Reporter
from askui.tools.agent_os import AgentOs

if TYPE_CHECKING:
    from anthropic.types.beta import BetaMessageParam


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
        self, messages: list[MessageParam], model_choice: str
    ) -> MessageParam:
        response = self._client.beta.messages.with_raw_response.create(
            max_tokens=self._settings.max_tokens,
            messages=[
                cast("BetaMessageParam", message.model_dump(mode="json"))
                for message in messages
            ],
            model=ANTHROPIC_MODEL_NAME_MAPPING[ModelName(model_choice)],
            system=[self._system],
            tools=self._tool_collection.to_params(),
            betas=self._settings.betas,
        )
        parsed_response = response.parse()
        return MessageParam.model_validate(parsed_response.model_dump())
