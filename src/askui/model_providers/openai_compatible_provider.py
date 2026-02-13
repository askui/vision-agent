"""OpenAICompatibleProvider — VLM access via any OpenAI-compatible endpoint."""

from functools import cached_property

from openai import OpenAI
from typing_extensions import override

from askui.model_providers.vlm_provider import VlmProvider
from askui.models.openai.messages_api import OpenAICompatibleMessagesApi
from askui.models.shared.agent_message_param import (
    MessageParam,
    ThinkingConfigParam,
    ToolChoiceParam,
)
from askui.models.shared.prompts import SystemPrompt
from askui.models.shared.tools import ToolCollection


class OpenAICompatibleProvider(VlmProvider):
    """VLM provider for any OpenAI-compatible chat completions endpoint.

    Converts the internal Anthropic-style message format to OpenAI's chat
    completions format, including tool-calling. Use this to connect to any
    model server that implements the OpenAI API (e.g. vLLM, Ollama, LM Studio,
    Azure OpenAI, or OpenRouter).

    Args:
        endpoint (str): Base URL of the OpenAI-compatible API
            (e.g. ``\"https://api.openai.com/v1\"``).
        api_key (str): API key for the endpoint.
        model_id (str): Model identifier sent as-is to the endpoint.
        auth_token (str | None, optional): Authorization token for custom
            authentication. Added as an `Authorization` header.
        client (OpenAI | None, optional): Pre-configured OpenAI client.
            If provided, other connection parameters are ignored.

    Example:
        ```python
        from askui import AgentSettings, ComputerAgent
        from askui.model_providers import OpenAICompatibleProvider

        agent = ComputerAgent(settings=AgentSettings(
            vlm_provider=OpenAICompatibleProvider(
                endpoint=\"https://my-llm.example.com/v1\",
                api_key=\"sk-...\",
                model_id=\"my-model-v2\",
            )
        ))
        ```
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        model_id: str,
        auth_token: str | None = None,
        client: OpenAI | None = None,
    ) -> None:
        self._model_id_value = model_id
        if client is not None:
            self.client = client
        else:
            default_headers = {"Authorization": auth_token} if auth_token else None
            self.client = OpenAI(
                api_key=api_key,
                base_url=endpoint,
                default_headers=default_headers,
            )

    @property
    @override
    def model_id(self) -> str:
        return self._model_id_value

    @cached_property
    def _messages_api(self) -> OpenAICompatibleMessagesApi:
        return OpenAICompatibleMessagesApi(client=self.client)

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
        return self._messages_api.create_message(
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
