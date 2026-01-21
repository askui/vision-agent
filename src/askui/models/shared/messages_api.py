from abc import ABC, abstractmethod

from askui.models.shared.agent_message_param import MessageParam
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
        thinking: dict[str, str] | None = None,
        tool_choice: dict[str, str] | None = None,
        temperature: float | None = None,
    ) -> MessageParam:
        """Create a message using the Anthropic API.

        Args:
            messages (list[MessageParam]): The messages to create a message.
            model_id (str): The model identifier to use.
            tools (ToolCollection | None): The tools to use.
            max_tokens (int | None): The maximum number of tokens to generate.
            betas (list[str] | None): The betas to use.
            system (SystemPrompt | None): The system to use.
            thinking (dict[str, str] | None): The thinking to use.
            tool_choice (dict[str, str] | None): The tool choice to use.
            temperature (float | None): The temperature to use.

        Returns:
            MessageParam: The created message.
        """
        raise NotImplementedError
