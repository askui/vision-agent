import httpx
from anthropic.types.beta import (
    BetaTextBlockParam,
    BetaToolChoiceParam,
    BetaToolUnionParam,
)
from pydantic import BaseModel, ConfigDict
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
from typing_extensions import override

from askui.models.askui.settings import AskUiComputerAgentSettings
from askui.models.shared.computer_agent import ComputerAgent, ThinkingConfigParam
from askui.models.shared.computer_agent_message_param import MessageParam
from askui.models.shared.tools import ToolCollection
from askui.reporting import Reporter

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


def is_retryable_error(exception: BaseException) -> bool:
    """Check if the exception is a retryable error (status codes 429 or 529)."""
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code in (429, 529)
    return False


class AskUiComputerAgent(ComputerAgent[AskUiComputerAgentSettings]):
    def __init__(
        self,
        tool_collection: ToolCollection,
        reporter: Reporter,
        settings: AskUiComputerAgentSettings,
    ) -> None:
        super().__init__(settings, tool_collection, reporter)
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
        retry=retry_if_exception(is_retryable_error),
        reraise=True,
    )
    @override
    def _create_message(
        self,
        messages: list[MessageParam],
        model_choice: str,  # noqa: ARG002
    ) -> MessageParam:
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
            if is_retryable_error(e):
                logger.debug(e)
            if (
                isinstance(e, httpx.HTTPStatusError)
                and 400 <= e.response.status_code < 500
            ):
                raise ValueError(e.response.json()) from e
            raise
