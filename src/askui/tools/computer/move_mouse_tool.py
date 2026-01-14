from askui.models.shared import ComputerBaseTool, ToolTags
from askui.tools.computer_agent_os_facade import ComputerAgentOsFacade


class ComputerMoveMouseTool(ComputerBaseTool):
    """Computer Mouse Move Tool"""

    def __init__(self, agent_os: ComputerAgentOsFacade | None = None) -> None:
        super().__init__(
            name="computer_move_mouse",
            description="Move the mouse to a specific position.",
            input_schema={
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": "The x coordinate of the mouse position.",
                    },
                    "y": {
                        "type": "integer",
                        "description": "The y coordinate of the mouse position.",
                    },
                },
                "required": ["x", "y"],
            },
            agent_os=agent_os,
            required_tags=[ToolTags.SCALED_AGENT_OS.value],
        )

    def __call__(self, x: int, y: int) -> str:
        self.agent_os.mouse_move(x, y)
        return f"Mouse was moved to position ({x}, {y})."
