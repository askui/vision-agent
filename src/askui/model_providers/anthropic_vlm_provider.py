"""AnthropicVlmProvider — VLM access via direct Anthropic API."""

from functools import cached_property

from anthropic import Anthropic
from typing_extensions import override

from askui.model_providers.vlm_provider import VlmProvider
from askui.models.anthropic.messages_api import AnthropicMessagesApi
from askui.models.shared.agent_message_param import (
    MessageParam,
    ThinkingConfigParam,
    ToolChoiceParam,
)
from askui.models.shared.prompts import SystemPrompt
from askui.models.shared.tools import ToolCollection

_DEFAULT_MODEL_ID = "claude-sonnet-4-5-20251101"


class AnthropicVlmProvider(VlmProvider):
    """VLM provider that routes requests directly to the Anthropic API.

    Supports Claude 4.x generation models. The API key is read from the
    `ANTHROPIC_API_KEY` environment variable lazily — validation happens on
    the first API call, not at construction time.

    Args:
        api_key (str | None, optional): Anthropic API key. Reads
            `ANTHROPIC_API_KEY` from the environment if not provided.
        base_url (str | None, optional): Base URL for the Anthropic API.
            Useful for proxies or custom endpoints.
        auth_token (str | None, optional): Authorization token for custom
            authentication. Added as an `Authorization` header.
        model_id (str, optional): Claude model to use. Defaults to
            `\"claude-sonnet-4-5-20251101\"`.
        client (Anthropic | None, optional): Pre-configured Anthropic client.
            If provided, other connection parameters are ignored.

    Example:
        ```python
        from askui import AgentSettings, ComputerAgent
        from askui.model_providers import AnthropicVlmProvider

        agent = ComputerAgent(settings=AgentSettings(
            vlm_provider=AnthropicVlmProvider(
                api_key=\"sk-ant-...\",
                model_id=\"claude-opus-4-5-20251101\",
            )
        ))
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        auth_token: str | None = None,
        model_id: str = _DEFAULT_MODEL_ID,
        client: Anthropic | None = None,
    ) -> None:
        self._model_id_value = model_id
        if client is not None:
            self.client = client
        else:
            self.client = Anthropic(
                api_key=api_key,
                base_url=base_url,
                auth_token=auth_token,
            )

    @property
    @override
    def model_id(self) -> str:
        return self._model_id_value

    @cached_property
    def _messages_api(self) -> AnthropicMessagesApi:
        """Lazily initialise the AnthropicMessagesApi on first use."""
        return AnthropicMessagesApi(client=self.client)

    @override
    def create_message(
        self,
        messages: list[MessageParam],
        tools: ToolCollection | None = None,
        max_tokens: int | None = None,
        betas: list[str] | None = None,
        system: SystemPrompt | None = None,
        thinking: ThinkingConfigParam | None = None,
        tool_choice: ToolChoiceParam | None = None,
        temperature: float | None = None,
    ) -> MessageParam:
        result: MessageParam = self._messages_api.create_message(
            messages=messages,
            model_id=self._model_id_value,
            tools=tools,
            max_tokens=max_tokens,
            betas=betas,
            system=system,
            thinking=thinking,
            tool_choice=tool_choice,
            temperature=temperature,
        )
        return result
