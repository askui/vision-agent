import logging
from functools import cached_property
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from askui.models.askui.inference_api_settings import AskUiInferenceApiSettings
from askui.models.askui.retry_utils import (
    RETRYABLE_HTTP_STATUS_CODES,
    wait_for_retry_after_header,
)

logger = logging.getLogger(__name__)


def _is_retryable_error(exception: BaseException) -> bool:
    """Check if the exception is a retryable error."""
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code in RETRYABLE_HTTP_STATUS_CODES
    return False


class AskUiInferenceApi:
    def __init__(
        self,
        settings: AskUiInferenceApiSettings,
    ) -> None:
        self._settings = settings

    @cached_property
    def _http_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=f"{self._settings.base_url}",
            headers={
                "Content-Type": "application/json",
                "Authorization": self._settings.authorization_header,
            },
        )

    @retry(
        stop=stop_after_attempt(4),  # 3 retries
        wait=wait_for_retry_after_header(
            wait_exponential(multiplier=30, min=30, max=120)
        ),  # retry after or as a fallback 30s, 60s, 120s
        retry=retry_if_exception(_is_retryable_error),
        reraise=True,
    )
    def post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> httpx.Response:
        try:
            response = self._http_client.post(
                path,
                json=json,
                timeout=timeout,
            )
            response.raise_for_status()
        except Exception as e:  # noqa: BLE001
            if (
                isinstance(e, httpx.HTTPStatusError)
                and 400 <= e.response.status_code < 500
            ):
                raise ValueError(e.response.text) from e
            if _is_retryable_error(e):
                logger.debug("Retryable error", extra={"error": str(e)})
            raise
        else:
            return response
