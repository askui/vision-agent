from typing import TYPE_CHECKING, cast

from anthropic import NOT_GIVEN, Anthropic, NotGiven
from anthropic.types import AnthropicBetaParam
from typing_extensions import override

from askui.models.anthropic.settings import ClaudeComputerAgentSettings
from askui.models.models import ANTHROPIC_MODEL_NAME_MAPPING, ModelName
from askui.models.shared.computer_agent import (
    COMPUTER_USE_20241022_BETA_FLAG,
    COMPUTER_USE_20250124_BETA_FLAG,
    ComputerAgent,
)
from askui.models.shared.computer_agent_message_param import MessageParam
from askui.models.shared.tools import ToolCollection
from askui.reporting import Reporter

if TYPE_CHECKING:
    from anthropic.types.beta import BetaMessageParam, BetaThinkingConfigParam


class ClaudeComputerAgent(ComputerAgent[ClaudeComputerAgentSettings]):
    def __init__(
        self,
        tool_collection: ToolCollection,
        reporter: Reporter,
        settings: ClaudeComputerAgentSettings,
    ) -> None:
        super().__init__(settings, tool_collection, reporter)
        self._client = Anthropic(
            api_key=self._settings.anthropic.api_key.get_secret_value()
        )

    def _get_betas(self, model_choice: str) -> list[AnthropicBetaParam] | NotGiven:
        if model_choice == ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022:
            return self._settings.betas + [COMPUTER_USE_20241022_BETA_FLAG]
        if model_choice == ModelName.CLAUDE__SONNET__4__20250514:
            return self._settings.betas + [COMPUTER_USE_20250124_BETA_FLAG]
        return NOT_GIVEN

    @override
    def _create_message(
        self, messages: list[MessageParam], model_choice: str
    ) -> MessageParam:
        response = self._client.beta.messages.with_raw_response.create(
            max_tokens=self._settings.max_tokens,
            messages=[
                cast("BetaMessageParam", message.model_dump(exclude={"stop_reason"}))
                for message in messages
            ],
            model=ANTHROPIC_MODEL_NAME_MAPPING[ModelName(model_choice)],
            system=[self._system],
            tools=self._tool_collection.to_params(),
            betas=self._get_betas(model_choice),
            thinking=cast(
                "BetaThinkingConfigParam", self._settings.thinking.model_dump()
            ),
            tool_choice=self._settings.tool_choice,
        )
        parsed_response = response.parse()
        return MessageParam.model_validate(parsed_response.model_dump())
