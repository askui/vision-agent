import httpx
from anthropic.types.beta import (
    BetaTextBlockParam,
    BetaToolChoiceParam,
    BetaToolUnionParam,
)
from pydantic import BaseModel, ConfigDict
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
from typing_extensions import override

from askui.models.askui.settings import AskUiAgentSettings
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_settings import ThinkingConfigParam
from askui.models.shared.messages_api import MessagesApi
from askui.models.shared.tools import ToolCollection

from ...logger import logger


class RequestBody(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    max_tokens: int
    messages: list[MessageParam]
    model: str
    tools: list[BetaToolUnionParam]
    betas: list[str]
    system: list[BetaTextBlockParam]
    thinking: ThinkingConfigParam
    tool_choice: BetaToolChoiceParam


def _is_retryable_error(exception: BaseException) -> bool:
    """Check if the exception is a retryable error (status codes 429 or 529)."""
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code in (429, 529)
    return False


class AskUiMessagesApi(MessagesApi):
    """AskUI API implementation for message creation."""

    def __init__(
        self,
        settings: AskUiAgentSettings,
        tool_collection: ToolCollection,
        system_prompt: str,
    ) -> None:
        """Initialize the AskUI message creator.

        Args:
            settings (AskUiAgentSettings): The settings for the agent.
            tool_collection (ToolCollection): The tools for the agent.
            system_prompt (str): The system prompt for the agent.
        """
        self._settings = settings
        self._tool_collection = tool_collection
        self._system = BetaTextBlockParam(
            type="text",
            text=system_prompt,
        )
        self._client = httpx.Client(
            base_url=f"{self._settings.askui.base_url}",
            headers={
                "Content-Type": "application/json",
                "Authorization": self._settings.askui.authorization_header,
            },
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=30, max=240),
        retry=retry_if_exception(_is_retryable_error),
        reraise=True,
    )
    @override
    def create_message(
        self,
        messages: list[MessageParam],
        model_choice: str,  # noqa: ARG002
    ) -> MessageParam:
        """Create a message using the AskUI API.

        Args:
            messages (list[MessageParam]): The message history.
            model_choice (str): The model to use for message creation.

        Returns:
            MessageParam: The created message.
        """
        try:
            request_body = RequestBody(
                max_tokens=self._settings.max_tokens,
                messages=messages,
                model=self._settings.model,
                tools=self._tool_collection.to_params(),
                betas=self._settings.betas,
                system=[self._system],
                tool_choice=self._settings.tool_choice,
                thinking=self._settings.thinking,
            )
            response = self._client.post(
                "/act/inference",
                json=request_body.model_dump(
                    mode="json", exclude={"messages": {"stop_reason"}}
                ),
                timeout=300.0,
            )
            response.raise_for_status()
            return MessageParam.model_validate_json(response.text)
        except Exception as e:  # noqa: BLE001
            if _is_retryable_error(e):
                logger.debug(e)
            if (
                isinstance(e, httpx.HTTPStatusError)
                and 400 <= e.response.status_code < 500
            ):
                raise ValueError(e.response.json()) from e
            raise
