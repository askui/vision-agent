from abc import ABC, abstractmethod

from askui.models.shared.agent_message_param import (
    MessageParam,
    ThinkingConfigParam,
    ToolChoiceParam,
)
from askui.models.shared.prompts import SystemPrompt
from askui.models.shared.tools import ToolCollection


class MessagesApi(ABC):
    """Interface for creating messages using different APIs."""

    @abstractmethod
    def create_message(
        self,
        messages: list[MessageParam],
        model_id: str,
        tools: ToolCollection | None = None,
        max_tokens: int | None = None,
        betas: list[str] | None = None,
        system: SystemPrompt | None = None,
        thinking: ThinkingConfigParam | None = None,
        tool_choice: ToolChoiceParam | None = None,
        temperature: float | None = None,
    ) -> MessageParam:
        """Create a message using a Messages API (provider-agnostic).

        Args:
            messages (list[MessageParam]): The message history.
            model_id (str): The model identifier to use.
            tools (ToolCollection | None): The tools available to the model.
            max_tokens (int | None): The maximum number of tokens to generate.
            betas (list[str] | None): Beta features to enable (provider-specific).
            system (SystemPrompt | None): The system prompt.
            thinking (ThinkingConfigParam | None): Thinking configuration (provider-specific).
            tool_choice (ToolChoiceParam | None): Tool choice configuration (provider-specific).
            temperature (float | None): The sampling temperature (0-1).

        Returns:
            MessageParam: The created message from the model.

        Note:
            The `thinking` and `tool_choice` parameters are provider-specific
            dictionaries. See the specific MessagesApi implementation for details.
            For Anthropic: see anthropic.types.beta.BetaThinkingConfigParam and
            BetaToolChoiceParam.
        """
        raise NotImplementedError
