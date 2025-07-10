from abc import ABC, abstractmethod

from anthropic import NOT_GIVEN, NotGiven
from anthropic.types import AnthropicBetaParam
from anthropic.types.beta import (
    BetaTextBlockParam,
    BetaThinkingConfigParam,
    BetaToolChoiceParam,
)

from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.tools import ToolCollection


class MessagesApi(ABC):
    """Interface for creating messages using different APIs."""

    @abstractmethod
    def create_message(
        self,
        messages: list[MessageParam],
        model: str,
        tools: ToolCollection | NotGiven = NOT_GIVEN,
        max_tokens: int | NotGiven = NOT_GIVEN,
        betas: list[AnthropicBetaParam] | NotGiven = NOT_GIVEN,
        system: str | list[BetaTextBlockParam] | NotGiven = NOT_GIVEN,
        thinking: BetaThinkingConfigParam | NotGiven = NOT_GIVEN,
        tool_choice: BetaToolChoiceParam | NotGiven = NOT_GIVEN,
    ) -> MessageParam:
        """Create a message using the Anthropic API.

        Args:
            messages (list[MessageParam]): The messages to create a message.
            model (str): The model to use.
            tools (ToolCollection | NotGiven): The tools to use.
            max_tokens (int | NotGiven): The maximum number of tokens to generate.
            betas (list[AnthropicBetaParam] | NotGiven): The betas to use.
            system (str | list[BetaTextBlockParam] | NotGiven): The system to use.
            thinking (BetaThinkingConfigParam | NotGiven): The thinking to use.
            tool_choice (BetaToolChoiceParam | NotGiven): The tool choice to use.

        Returns:
            MessageParam: The created message.
        """
        raise NotImplementedError
