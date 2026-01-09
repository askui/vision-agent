from askui.models.shared import ComputerBaseTool
from askui.tools.computer_agent_os_facade import ComputerAgentOsFacade


class ComputerMouseScrollTool(ComputerBaseTool):
    """Computer Mouse Scroll Tool"""

    def __init__(self, agent_os: ComputerAgentOsFacade | None = None) -> None:
        super().__init__(
            name="computer_mouse_scroll",
            description="Scroll the mouse wheel at the current position.",
            input_schema={
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": (
                            "The horizontal scroll amount. "
                            "Positive values scroll right, negative values scroll left."
                        ),
                    },
                    "y": {
                        "type": "integer",
                        "description": (
                            "The vertical scroll amount. "
                            "Positive values scroll down, negative values scroll up."
                        ),
                    },
                },
                "required": ["x", "y"],
            },
            agent_os=agent_os,
            required_tags=["agent_os_facade"],
        )

    def __call__(self, x: int, y: int) -> str:
        self.agent_os.mouse_scroll(x, y)
        return f"Mouse was scrolled by ({x}, {y})."
