"""Tool that returns the current time in UTC."""

from datetime import datetime, timezone

from askui.models.shared.tools import Tool


class GetCurrentTimeTool(Tool):
    """
    Returns the current date and time in UTC (Coordinated Universal Time).
    """

    def __init__(self) -> None:
        super().__init__(
            name="get_current_time_utc_tool",
            description=(
                "Returns the current date and time in UTC (Coordinated Universal Time)."
                " Use when you need to know the current time."
            ),
            input_schema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )

    def __call__(self) -> str:
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%d %H:%M:%S UTC")
