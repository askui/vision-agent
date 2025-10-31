from abc import ABC, abstractmethod

from anthropic import Omit, omit
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
        tools: ToolCollection | Omit = omit,
        max_tokens: int | Omit = omit,
        betas: list[AnthropicBetaParam] | Omit = omit,
        system: str | list[BetaTextBlockParam] | Omit = omit,
        thinking: BetaThinkingConfigParam | Omit = omit,
        tool_choice: BetaToolChoiceParam | Omit = omit,
        temperature: float | Omit = omit,
    ) -> MessageParam:
        """Create a message using the Anthropic API.

        Args:
            messages (list[MessageParam]): The messages to create a message.
            model (str): The model to use.
            tools (ToolCollection | Omit): The tools to use.
            max_tokens (int | Omit): The maximum number of tokens to generate.
            betas (list[AnthropicBetaParam] | Omit): The betas to use.
            system (str | list[BetaTextBlockParam] | Omit): The system to use.
            thinking (BetaThinkingConfigParam | Omit): The thinking to use.
            tool_choice (BetaToolChoiceParam | Omit): The tool choice to use.
            temperature (float | Omit): The temperature to use.

        Returns:
            MessageParam: The created message.
        """
        raise NotImplementedError
