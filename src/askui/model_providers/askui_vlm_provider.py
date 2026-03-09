"""AskUIVlmProvider — VLM access via AskUI's hosted Anthropic proxy."""

import os
from functools import cached_property
from typing import Any

from anthropic import Anthropic
from typing_extensions import override

from askui.model_providers.vlm_provider import VlmProvider
from askui.models.anthropic.messages_api import AnthropicMessagesApi
from askui.models.askui.inference_api_settings import AskUiInferenceApiSettings
from askui.models.shared.agent_message_param import (
    MessageParam,
    ThinkingConfigParam,
    ToolChoiceParam,
)
from askui.models.shared.prompts import SystemPrompt
from askui.models.shared.tools import ToolCollection
from askui.utils.model_pricing import ModelPricing, resolve_default_pricing

_DEFAULT_MODEL_ID = "claude-sonnet-4-6"


class AskUIVlmProvider(VlmProvider):
    """VLM provider that routes requests through AskUI's hosted Anthropic proxy.

    Supports Claude 4.x generation models. Credentials are read from environment
    variables (`ASKUI_WORKSPACE_ID`, `ASKUI_TOKEN`) lazily — validation happens
    on the first API call, not at construction time.

    Args:
        workspace_id (str | None, optional): AskUI workspace ID. Reads
            `ASKUI_WORKSPACE_ID` from the environment if not provided.
        token (str | None, optional): AskUI API token. Reads `ASKUI_TOKEN`
            from the environment if not provided.
        model_id (str, optional): Claude model to use. Defaults to
            `"claude-sonnet-4-6"`.
        client (Anthropic | None, optional): Pre-configured Anthropic client.
            If provided, `workspace_id` and `token` are ignored.
        input_cost_per_million_tokens (float | None, optional): Override
            cost in USD per 1M input tokens. Both cost params must be set
            to override the built-in defaults.
        output_cost_per_million_tokens (float | None, optional): Override
            cost in USD per 1M output tokens.

    Example:
        ```python
        from askui import AgentSettings, ComputerAgent
        from askui.model_providers import AskUIVlmProvider

        agent = ComputerAgent(settings=AgentSettings(
            vlm_provider=AskUIVlmProvider(
                workspace_id="my-workspace",
                token="my-token",
                model_id="claude-opus-4-6-20260401",
            )
        ))
        ```
    """

    def __init__(
        self,
        askui_settings: AskUiInferenceApiSettings | None = None,
        model_id: str | None = None,
        client: Anthropic | None = None,
        input_cost_per_million_tokens: float | None = None,
        output_cost_per_million_tokens: float | None = None,
    ) -> None:
        self._askui_settings = askui_settings or AskUiInferenceApiSettings()
        self._model_id_value = (
            model_id or os.environ.get("VLM_PROVIDER_MODEL_ID") or _DEFAULT_MODEL_ID
        )
        self._injected_client = client
        self._pricing: ModelPricing | None
        if (
            input_cost_per_million_tokens is not None
            and output_cost_per_million_tokens is not None
        ):
            self._pricing = ModelPricing(
                input_cost_per_million_tokens=input_cost_per_million_tokens,
                output_cost_per_million_tokens=output_cost_per_million_tokens,
            )
        else:
            self._pricing = resolve_default_pricing(self._model_id_value)

    @property
    @override
    def model_id(self) -> str:
        return self._model_id_value

    @property
    @override
    def pricing(self) -> ModelPricing | None:
        return self._pricing

    @cached_property
    def _messages_api(self) -> AnthropicMessagesApi:
        """Lazily initialise the AnthropicMessagesApi on first use."""
        if self._injected_client is not None:
            return AnthropicMessagesApi(client=self._injected_client)

        # TODO askui_settings.verify_ssl are not considered! #noqa
        # if self._askui_settings.verify_ssl:
        # ...
        # http_client = ...
        client = Anthropic(
            api_key="DummyValueRequiredByAnthropicClient",
            base_url=f"{self._askui_settings.base_url}/proxy/anthropic",
            default_headers={
                "Authorization": self._askui_settings.authorization_header
            },
        )
        return AnthropicMessagesApi(client=client)

    @override
    def create_message(
        self,
        messages: list[MessageParam],
        tools: ToolCollection | None = None,
        max_tokens: int | None = None,
        system: SystemPrompt | None = None,
        thinking: ThinkingConfigParam | None = None,
        tool_choice: ToolChoiceParam | None = None,
        temperature: float | None = None,
        provider_options: dict[str, Any] | None = None,
    ) -> MessageParam:
        result: MessageParam = self._messages_api.create_message(
            messages=messages,
            model_id=self._model_id_value,
            tools=tools,
            max_tokens=max_tokens,
            system=system,
            thinking=thinking,
            tool_choice=tool_choice,
            temperature=temperature,
            provider_options=provider_options,
        )
        return result
