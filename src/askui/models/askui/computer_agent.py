import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
from typing_extensions import override

from askui.models.askui.settings import AskUiComputerAgentSettings
from askui.models.shared.computer_agent import ComputerAgent
from askui.models.shared.computer_agent_message_param import MessageParam
from askui.reporting import Reporter
from askui.tools.agent_os import AgentOs

from ...logger import logger


def is_retryable_error(exception: BaseException) -> bool:
    """Check if the exception is a retryable error (status codes 429 or 529)."""
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code in (429, 529)
    return False


class AskUiComputerAgent(ComputerAgent[AskUiComputerAgentSettings]):
    def __init__(
        self,
        agent_os: AgentOs,
        reporter: Reporter,
        settings: AskUiComputerAgentSettings,
    ) -> None:
        super().__init__(settings, agent_os, reporter)
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
            request_body = {
                "max_tokens": self._settings.max_tokens,
                "messages": [msg.model_dump(mode="json") for msg in messages],
                "model": self._settings.model,
                "tools": self._tool_collection.to_params(),
                "betas": self._settings.betas,
                "system": [self._system],
            }
            response = self._client.post(
                "/act/inference", json=request_body, timeout=300.0
            )
            response.raise_for_status()
            response_data = response.json()
            return MessageParam.model_validate(response_data)
        except Exception as e:  # noqa: BLE001
            if is_retryable_error(e):
                logger.debug(e)
            raise
