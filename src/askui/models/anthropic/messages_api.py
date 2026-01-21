from typing import Tuple, cast

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
    BetaToolUnionParam,
)
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
from typing_extensions import override

from askui.locators.serializers import VlmLocatorSerializer
from askui.models.anthropic.factory import AnthropicApiClient
from askui.models.askui.retry_utils import (
    RETRYABLE_HTTP_STATUS_CODES,
    wait_for_retry_after_header,
)
from askui.models.shared.agent_message_param import (
    MessageParam,
    ThinkingConfigParam,
    ToolChoiceParam,
)
from askui.models.shared.messages_api import MessagesApi
from askui.models.shared.prompts import SystemPrompt
from askui.models.shared.tools import ToolCollection


def _is_retryable_error(exception: BaseException) -> bool:
    """Check if the exception is a retryable error."""
    if isinstance(exception, APIStatusError):
        return exception.status_code in RETRYABLE_HTTP_STATUS_CODES
    return isinstance(exception, (APIConnectionError, APITimeoutError, APIError))


def _parse_to_anthropic_types(
    tools: ToolCollection | None,
    betas: list[str] | None = None,
    system: SystemPrompt | None = None,
    thinking: ThinkingConfigParam | None = None,
    tool_choice: ToolChoiceParam | None = None,
    temperature: float | None = None,
) -> Tuple[
    list[BetaToolUnionParam] | Omit,
    list[AnthropicBetaParam] | Omit,
    str | Omit,
    BetaThinkingConfigParam | Omit,
    BetaToolChoiceParam | Omit,
    float | Omit,
]:
    """Convert provider-agnostic types to Anthropic-specific types.

    This function bridges the gap between the generic MessagesApi interface
    and Anthropic's specific type requirements. The input dicts should match
    Anthropic's expected structure (see Anthropic SDK documentation).
    """
    _tools = (
        cast("list[BetaToolUnionParam]", tools.to_params())
        if tools is not None
        else omit
    )
    _betas = cast("list[AnthropicBetaParam]", betas) or omit
    _system: str | Omit = omit if system is None else str(system)
    # Cast dicts to Anthropic's TypedDict types
    # Runtime validation happens in Anthropic SDK
    _thinking = (
        cast("BetaThinkingConfigParam", thinking) if thinking is not None else omit
    )
    _tool_choice = (
        cast("BetaToolChoiceParam", tool_choice) if tool_choice is not None else omit
    )
    _temperature = temperature or omit

    return (_tools, _betas, _system, _thinking, _tool_choice, _temperature)


class AnthropicMessagesApi(MessagesApi):
    def __init__(
        self,
        client: AnthropicApiClient,
        locator_serializer: VlmLocatorSerializer,
    ) -> None:
        self._client = client
        self._locator_serializer = locator_serializer

    @retry(
        stop=stop_after_attempt(4),  # 3 retries
        wait=wait_for_retry_after_header(
            wait_exponential(multiplier=30, min=30, max=120)
        ),  # retry after or as a fallback 30s, 60s, 120s
        retry=retry_if_exception(_is_retryable_error),
        reraise=True,
    )
    @override
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
        _messages = [
            cast("BetaMessageParam", message.model_dump(exclude={"stop_reason"}))
            for message in messages
        ]

        _tools, _betas, _system, _thinking, _tool_choice, _temperature = (
            _parse_to_anthropic_types(
                tools, betas, system, thinking, tool_choice, temperature
            )
        )

        response = self._client.beta.messages.create(  # type: ignore[misc]
            messages=_messages,
            max_tokens=max_tokens or 8192,
            model=model_id,
            tools=_tools,
            betas=_betas,
            system=_system,
            thinking=_thinking,
            tool_choice=_tool_choice,
            temperature=_temperature,
            timeout=300.0,
        )
        return MessageParam.model_validate(response.model_dump())
