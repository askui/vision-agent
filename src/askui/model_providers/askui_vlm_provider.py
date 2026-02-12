"""AskUIVlmProvider — VLM access via AskUI's hosted Anthropic proxy."""

from functools import cached_property

from typing_extensions import override

from askui.model_providers.vlm_provider import VlmProvider
from askui.models.shared.agent_message_param import (
    MessageParam,
    ThinkingConfigParam,
    ToolChoiceParam,
)
from askui.models.shared.prompts import SystemPrompt
from askui.models.shared.tools import ToolCollection

_DEFAULT_MODEL_ID = "claude-sonnet-4-5-20251101"


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
            `"claude-sonnet-4-5-20251101"`.

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
        workspace_id: str | None = None,
        token: str | None = None,
        model_id: str = _DEFAULT_MODEL_ID,
    ) -> None:
        self._workspace_id = workspace_id
        self._token = token
        self._model_id_value = model_id

    @property
    @override
    def model_id(self) -> str:
        return self._model_id_value

    @cached_property
    def _messages_api(self):  # type: ignore[no-untyped-def]
        """Lazily initialise the AnthropicMessagesApi on first use."""
        import os

        from askui.models.anthropic.factory import create_api_client
        from askui.models.anthropic.messages_api import AnthropicMessagesApi
        from askui.models.askui.inference_api_settings import AskUiInferenceApiSettings

        if self._workspace_id is not None:
            os.environ.setdefault("ASKUI_WORKSPACE_ID", self._workspace_id)
        if self._token is not None:
            os.environ.setdefault("ASKUI_TOKEN", self._token)

        settings = AskUiInferenceApiSettings()
        client = create_api_client(api_provider="askui")
        del client  # we re-create with correct settings below

        from anthropic import Anthropic

        api_client = Anthropic(
            api_key="DummyValueRequiredByAnthropicClient",
            base_url=f"{settings.base_url}/proxy/anthropic",
            default_headers={"Authorization": settings.authorization_header},
        )
        return AnthropicMessagesApi(client=api_client)

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
