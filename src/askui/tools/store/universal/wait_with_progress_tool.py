"""Custom tool: wait for a given time while showing a progress bar in the console."""

from askui.models.shared.tools import Tool
from askui.tools.utils import wait_with_progress


class WaitWithProgressTool(Tool):
    """
    Waits for a specified number of seconds
        and displays a progress bar in the console during the wait.
    """

    def __init__(self, max_wait_time: int = 60 * 60) -> None:
        if max_wait_time < 1:
            msg = "Max wait time must be at least 1 second"
            raise ValueError(msg)
        super().__init__(
            name="wait_with_progress_tool",
            description=(
                "Waits for a specified number of seconds (e.g. page load, animation). "
                "Displays a progress bar in the console during the wait."
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
                    "message": {
                        "type": "string",
                        "description": (
                            "Optional short label shown next to the progress bar "
                            "(e.g. 'Waiting for page load')"
                        ),
                    },
                },
                "required": ["wait_duration", "message"],
            },
        )
        self._max_wait_time = max_wait_time

    def __call__(self, wait_duration: int, message: str) -> str:
        if wait_duration < 1:
            msg = "Wait duration must be at least 1 second"
            raise ValueError(msg)
        if wait_duration > self._max_wait_time:
            msg = f"Wait duration must not exceed {self._max_wait_time}"
            raise ValueError(msg)
        wait_with_progress(wait_duration, message)
        return f"Finished waiting for {wait_duration:.1f} seconds."
