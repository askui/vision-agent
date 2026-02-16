"""Simple wait tool: wait for a given time without progress bar."""

import time

from askui.models.shared.tools import Tool


class WaitTool(Tool):
    """
    Waits for a specified number of seconds without displaying a progress bar.
    Use when a short, silent wait is needed (e.g. brief pause between actions).
    """

    def __init__(self, max_wait_time: int = 60 * 60) -> None:
        if max_wait_time < 0:
            msg = "Max wait time must be at least 0.1"
            raise ValueError(msg)
        super().__init__(
            name="wait_tool",
            description=(
                "Waits for a specified number of seconds without any console output. "
                "Use for short, silent waits (e.g. brief pause between actions)."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "wait_duration": {
                        "type": "integer",
                        "description": (
                            "Duration of the wait in seconds "
                            "(must be an integer, e.g. 5 for 5 seconds)"
                        ),
                        "minimum": 1,
                        "maximum": max_wait_time,
                    },
                },
                "required": ["wait_duration"],
            },
        )
        self._max_wait_time = max_wait_time

    def __call__(self, wait_duration: int) -> str:
        if wait_duration < 0:
            msg = "Wait duration must be at least 0"
            raise ValueError(msg)
        if wait_duration > self._max_wait_time:
            msg = f"Wait duration must not exceed {self._max_wait_time}"
            raise ValueError(msg)
        time.sleep(wait_duration)
        return f"Finished waiting for {wait_duration:.1f} seconds."
