from askui.models.shared import ComputerBaseTool, ToolTags
from askui.tools.computer_agent_os_facade import ComputerAgentOsFacade


class ComputerMouseScrollTool(ComputerBaseTool):
    """Computer Mouse Scroll Tool"""

    def __init__(self, agent_os: ComputerAgentOsFacade | None = None) -> None:
        super().__init__(
            name="mouse_scroll",
            description=(
                "Scroll the mouse wheel at the current position. "
                "The scroll amount is specified in lines. "
                "For example, dy=3 scrolls down 3 lines and dy=-3 scrolls up 3 lines. "
                "Use small values (1-5) for precise scrolling and larger values (10-20) for fast scrolling. "
                "Note: The actual scroll direction may vary depending on the OS configuration "
                "(e.g., natural scrolling on macOS reverses the direction). "
                "If you observe that scrolling moves in the opposite direction than expected, "
                "invert the values (e.g., use negative instead of positive and vice versa)."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "dx": {
                        "type": "integer",
                        "description": (
                            "The horizontal scroll amount in lines. "
                            "Positive values scroll right, negative values scroll left. "
                            "Use 0 if no horizontal scrolling is needed."
                        ),
                    },
                    "dy": {
                        "type": "integer",
                        "description": (
                            "The vertical scroll amount in lines. "
                            "Positive values scroll down, negative values scroll up. "
                            "Use 0 if no vertical scrolling is needed."
                        ),
                    },
                },
                "required": ["dx", "dy"],
            },
            agent_os=agent_os,
            required_tags=[ToolTags.SCALED_AGENT_OS.value],
        )
        self.is_cacheable = True

    def __call__(self, dx: int, dy: int) -> str:
        self.agent_os.mouse_scroll(dx, dy)
        return f"Mouse was scrolled by ({dx}, {dy})."
