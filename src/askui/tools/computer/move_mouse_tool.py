from askui.models.shared import ComputerBaseTool, ToolTags
from askui.tools.computer_agent_os_facade import ComputerAgentOsFacade


class ComputerMoveMouseTool(ComputerBaseTool):
    """Computer Mouse Move Tool"""

    def __init__(self, agent_os: ComputerAgentOsFacade | None = None) -> None:
        super().__init__(
            name="move_mouse",
            description="Move the mouse to a specific position.",
            input_schema={
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": "The x coordinate of the mouse position as int.",
                    },
                    "y": {
                        "type": "integer",
                        "description": "The y coordinate of the mouse position as int.",
                    },
                },
                "required": ["x", "y"],
            },
            agent_os=agent_os,
            required_tags=[ToolTags.SCALED_AGENT_OS.value],
        )
        self.is_cacheable = True

    def __call__(self, x: int, y: int) -> str:
        # The agent occasionally passes coordinates incorrectly:
        # 1. As strings instead of ints (e.g., x="330", y="182")
        # 2. Both coords as a single comma-separated string in x
        #    (e.g., x="330, 182" or x="330, ")
        # We handle both cases here.
        if isinstance(x, str) and "," in x:  # type: ignore[unreachable]
            parts = [p.strip() for p in x.split(",") if p.strip()]  # type: ignore[unreachable]
            x = parts[0]
            if len(parts) > 1:
                y = parts[1]
        x, y = int(x), int(y)
        self.agent_os.mouse_move(x, y)
        return f"Mouse was moved to position ({x}, {y})."
