"""Tool that returns the current time in the local timezone."""

from datetime import datetime

from askui.models.shared.tools import Tool


class GetCurrentTimeTool(Tool):
    """
    Returns the current date and time in the local timezone.
    """

    def __init__(self) -> None:
        super().__init__(
            name="get_current_time_utc_tool",
            description=(
                "Returns the current date and time in the local timezone."
                " Use when you need to know the current time."
            ),
            input_schema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )

    def __call__(self) -> str:
        now = datetime.now().astimezone()
        date_str = now.strftime("%B %d, %Y")
        time_str = now.strftime("%H:%M:%S")
        tz_str = now.strftime("%Z") or now.strftime("%z")
        return f"Today is {date_str} and currently it is {time_str} {tz_str}"
