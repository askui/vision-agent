from typing import cast

from anthropic import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    Omit,
    omit,
)
from anthropic.types import AnthropicBetaParam
from anthropic.types.beta import (
    BetaMessageParam,
    BetaThinkingConfigParam,
    BetaToolChoiceParam,
)
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
from typing_extensions import override

from askui.locators.serializers import VlmLocatorSerializer
from askui.models.anthropic.factory import AnthropicApiClient
from askui.models.askui.retry_utils import (
    RETRYABLE_HTTP_STATUS_CODES,
    wait_for_retry_after_header,
)
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.messages_api import MessagesApi
from askui.models.shared.prompts import SystemPrompt
from askui.models.shared.tools import ToolCollection


def _is_retryable_error(exception: BaseException) -> bool:
    """Check if the exception is a retryable error."""
    if isinstance(exception, APIStatusError):
        return exception.status_code in RETRYABLE_HTTP_STATUS_CODES
    return isinstance(exception, (APIConnectionError, APITimeoutError, APIError))


class AnthropicMessagesApi(MessagesApi):
    def __init__(
        self,
        client: AnthropicApiClient,
        locator_serializer: VlmLocatorSerializer,
    ) -> None:
        self._client = client
        self._locator_serializer = locator_serializer

    @override
    @retry(
        stop=stop_after_attempt(4),  # 3 retries
        wait=wait_for_retry_after_header(
            wait_exponential(multiplier=30, min=30, max=120)
        ),  # retry after or as a fallback 30s, 60s, 120s
        retry=retry_if_exception(_is_retryable_error),
        reraise=True,
    )
    def create_message(
        self,
        messages: list[MessageParam],
        model: str,
        tools: ToolCollection | Omit = omit,
        max_tokens: int | Omit = omit,
        betas: list[AnthropicBetaParam] | Omit = omit,
        system: SystemPrompt | None = None,
        thinking: BetaThinkingConfigParam | Omit = omit,
        tool_choice: BetaToolChoiceParam | Omit = omit,
        temperature: float | Omit = omit,
    ) -> MessageParam:
        _messages = [
            cast("BetaMessageParam", message.model_dump(exclude={"stop_reason"}))
            for message in messages
        ]
        _system: str | Omit = omit if system is None else str(system)

        response = self._client.beta.messages.create(  # type: ignore[misc]
            messages=_messages,
            max_tokens=max_tokens or 4096,
            model=model,
            tools=tools.to_params() if not isinstance(tools, Omit) else omit,
            betas=betas,
            system=_system,
            thinking=thinking,
            tool_choice=tool_choice,
            temperature=temperature,
            timeout=300.0,
        )
        return MessageParam.model_validate(response.model_dump())
