"""Wait until a condition is met or max wait time is reached (poll at an interval)."""

import time
from typing import Callable

from askui.models.shared.tools import Tool
from askui.tools.utils import wait_with_progress


class WaitUntilConditionTool(Tool):
    """
    Waits up to a maximum time, checking a condition at a fixed interval.
    If the condition returns True, returns early. Otherwise returns after timeout.

    Args:
        - condition_check: Callable invoked each poll;
          returns True when the condition is met, False otherwise.
        - description: A string describing what the condition checks for.
        - max_wait_time: The maximum time to wait for the condition to
            be met in seconds (must be at least 10 seconds).
    """

    def __init__(
        self,
        condition_check: Callable[[], bool],
        description: str,
        max_wait_time: float = 60 * 60,  # 1 hour
    ) -> None:
        if max_wait_time < 10:
            msg = "Max wait time must be at least 10 seconds"
            raise ValueError(msg)
        super().__init__(
            name="wait_until_condition_tool",
            description=(
                f"Waits for: {description}. "
                "Polls a condition at a given interval up to a maximum time; "
                "returns early if the condition is met, otherwise after timeout."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "max_wait_time": {
                        "type": "number",
                        "description": "Maximum time to wait in seconds.",
                        "minimum": 10,  # 10 seconds
                        "maximum": max_wait_time,
                    },
                    "check_interval": {
                        "type": "number",
                        "description": (
                            "Interval in seconds between condition checks "
                            "(e.g. 0.5 for every half second)."
                        ),
                        "minimum": 1,  # 1 second
                        "maximum": max_wait_time,
                    },
                },
                "required": ["max_wait_time", "check_interval"],
            },
        )
        self._condition_check = condition_check
        self._max_wait_time = max_wait_time

    def __call__(self, max_wait_time: float, check_interval: float) -> str:
        if max_wait_time < 10:
            msg = "max_wait_time must be at least 10 seconds"
            raise ValueError(msg)
        if max_wait_time > self._max_wait_time:
            msg = f"max_wait_time must not exceed {self._max_wait_time}"
            raise ValueError(msg)
        if check_interval < 1:
            msg = "check_interval must be at least 1"
            raise ValueError(msg)
        if check_interval > max_wait_time:
            msg = "check_interval must not exceed max_wait_time"
            raise ValueError(msg)

        start = time.monotonic()
        num_checks = 0
        while True:
            elapsed = time.monotonic() - start
            if self._condition_check():
                return f"Condition met after {elapsed:.1f} seconds."
            if elapsed >= max_wait_time:
                return f"Timeout after {max_wait_time:.1f} seconds (condition not met)."
            sleep_for = min(check_interval, max_wait_time - elapsed)
            if sleep_for > 0:
                wait_with_progress(
                    sleep_for,
                    f"Waiting for condition to be met ({num_checks} checks so far)",
                )
                num_checks += 1
