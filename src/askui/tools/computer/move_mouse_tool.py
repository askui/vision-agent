import re

from askui.models.shared import ComputerBaseTool, ToolTags
from askui.tools.computer_agent_os_facade import ComputerAgentOsFacade


class ComputerMoveMouseTool(ComputerBaseTool):
    """Computer Mouse Move Tool"""

    def __init__(self, agent_os: ComputerAgentOsFacade | None = None) -> None:
        super().__init__(
            name="move_mouse",
            description="""Move the mouse to a specific position.
              Pass x and y as separate integer values, not as a combined string.""",
            input_schema={
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": """The x (horizontal) pixel coordinate.
                          Must be a single integer, e.g. 330.""",
                    },
                    "y": {
                        "type": "integer",
                        "description": """The y (vertical) pixel coordinate.
                          Must be a single integer, e.g. 182.""",
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
        # We extract all numbers from the string representations to handle both cases.
        if not (isinstance(x, int) and isinstance(y, int)):
            x, y = self._parse_coordinates(x, y)  # type: ignore[unreachable]
        self.agent_os.mouse_move(x, y)
        return f"Mouse was moved to position ({x}, {y})."

    @staticmethod
    def _parse_coordinates(x: float | str, y: float | str) -> tuple[int, int]:
        _NUMBER_PATTERN = re.compile(r"-?\d+")
        combined = f"{x},{y}"
        numbers = _NUMBER_PATTERN.findall(combined)
        if not len(numbers) == 2:
            error_msg = f"""Could not parse mouse_move coordinates from provided
              parameters x={x}, y={y}. The parameters x and y must be passed as separate
              integer values!"""
            raise ValueError(error_msg)
        return int(numbers[0]), int(numbers[1])
