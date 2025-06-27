from typing import TYPE_CHECKING, cast

from anthropic import NOT_GIVEN, Anthropic, NotGiven
from anthropic.types import AnthropicBetaParam
from anthropic.types.beta import BetaTextBlockParam
from typing_extensions import override

from askui.models.anthropic.settings import ClaudeComputerAgentSettings
from askui.models.models import ANTHROPIC_MODEL_NAME_MAPPING, ModelName
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_settings import (
    COMPUTER_USE_20241022_BETA_FLAG,
    COMPUTER_USE_20250124_BETA_FLAG,
)
from askui.models.shared.messages_api import MessagesApi
from askui.models.shared.tools import ToolCollection

if TYPE_CHECKING:
    from anthropic.types.beta import BetaMessageParam, BetaThinkingConfigParam


class AnthropicMessagesApi(MessagesApi):
    """Anthropic API implementation for message creation."""

    def __init__(
        self,
        settings: ClaudeComputerAgentSettings,
        tool_collection: ToolCollection,
        system_prompt: str,
    ) -> None:
        """Initialize the Anthropic message creator.

        Args:
            settings (ClaudeComputerAgentSettings): The settings for the agent.
            tool_collection (ToolCollection): The tools for the agent.
            system_prompt (str): The system prompt for the agent.
        """
        self._settings = settings
        self._tool_collection = tool_collection
        self._system = BetaTextBlockParam(
            type="text",
            text=system_prompt,
        )
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
    def create_message(
        self, messages: list[MessageParam], model_choice: str
    ) -> MessageParam:
        """Create a message using the Anthropic API.

        Args:
            messages (list[MessageParam]): The message history.
            model_choice (str): The model to use for message creation.

        Returns:
            MessageParam: The created message.
        """
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
