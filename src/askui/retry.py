from typing import Annotated, Callable, Literal, Tuple, Type, TypeVar

from pydantic import Field
from tenacity import (
    RetryCallState,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
    wait_incrementing,
)

from askui.logger import logger


class Retry:
    """A utility class for implementing retry mechanisms with configurable strategies.

    This class provides a flexible way to retry operations that may fail temporarily,
    supporting different retry strategies (Exponential, Fixed, Linear) and configurable
    parameters for delay and retry count.

    Args:
        on_exception_types (Tuple[Type[Exception]]): Tuple of exception types that should trigger a retry
        strategy (Literal["Exponential", "Fixed", "Linear"]): The retry strategy to use:
            - "Exponential": Delay increases exponentially between retries
            - "Fixed": Constant delay between retries
            - "Linear": Delay increases linearly between retries
        base_delay (int, optional): Base delay in milliseconds between retries.
        retry_count (int, optional): Maximum number of retry attempts.

    Example:
        ```python
        retry = Retry(
            on_exception_types=(ConnectionError, TimeoutError),
            strategy="Exponential",
            base_delay=1000,
            retry_count=3
        )
        result = retry.attempt(some_function)
        ```
    """  # noqa: E501

    def __init__(
        self,
        on_exception_types: Tuple[Type[Exception]],
        strategy: Literal["Exponential", "Fixed", "Linear"],
        base_delay: Annotated[int, Field(gt=0)] = 1000,
        retry_count: Annotated[int, Field(gt=0)] = 3,
    ):
        self._strategy = strategy
        self._base_delay = base_delay
        self._retry_count = retry_count
        self._on_exception_types = on_exception_types

    def _get_retry_wait_strategy(self):
        """Get the appropriate wait strategy based on the configured retry strategy."""
        if self._strategy == "Fixed":
            return wait_fixed(self._base_delay / 1000)
        if self._strategy == "Linear":
            return wait_incrementing(self._base_delay / 1000)
        return wait_exponential(multiplier=self._base_delay / 1000)

    def my_before_sleep(self, retry_state: RetryCallState):
        logger.info(
            "Retrying %s: attempt %s ended with: %s",
            retry_state.fn,
            retry_state.attempt_number,
            retry_state.outcome,
        )

    R = TypeVar("R")

    def attempt(self, func: Callable[..., R]) -> R:
        retryer = Retrying(
            stop=stop_after_attempt(self._retry_count),
            wait=self._get_retry_wait_strategy(),
            reraise=True,
            after=self.my_before_sleep,
            retry=retry_if_exception_type(self._on_exception_types),
        )
        return retryer(func)
