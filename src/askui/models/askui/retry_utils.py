from anthropic import APIStatusError
from google.genai.errors import APIError
from tenacity import RetryCallState
from tenacity.wait import wait_base

from askui.utils.http_utils import parse_retry_after_header


class wait_for_retry_after_header(wait_base):
    """Wait strategy that tries to wait for the length specified by
    the Retry-After header, or the underlying wait strategy if not.
    See RFC 6585 § 4.

    Otherwise, wait according to the fallback strategy.
    """

    def __init__(self, fallback: wait_base) -> None:
        """Initialize the wait strategy with a fallback strategy.

        Args:
            fallback (wait_base): The fallback wait strategy to use when
                Retry-After header is not available or invalid.
        """
        self._fallback = fallback

    def __call__(self, retry_state: RetryCallState) -> float:
        """Calculate the wait time based on Retry-After header or fallback.

        Args:
            retry_state (RetryCallState): The retry state containing the
                exception information.

        Returns:
            float: The wait time in seconds.
        """
        if outcome := retry_state.outcome:
            exc = outcome.exception()
            if isinstance(exc, (APIError, APIStatusError)):
                retry_after: str | None = exc.response.headers.get("Retry-After")
                if retry_after:
                    try:
                        return parse_retry_after_header(retry_after)
                    except ValueError:
                        pass
        return self._fallback(retry_state)


RETRYABLE_HTTP_STATUS_CODES = (408, 413, 429, 500, 502, 503, 504, 521, 522, 524, 529)
