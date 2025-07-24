from askui.models.shared.tools import Tool
from askui.tools.agent_os import AgentOs, Coordinate


class CursorPositionTool(Tool):
    """
    Tool to get the current mouse cursor position.
    """

    def __init__(self, agent_os: AgentOs):
        super().__init__(
            name="get_cursor_position",
            description=
                """
                Gets the current position of the mouse cursor.
                Returns a JSON string with 'x' and 'y' coordinates, e.g. {"x": 100, "y": 200}.
                """
        )
        self._agent_os: AgentOs = agent_os

    def __call__(self) -> str:
        """
        Gets the current mouse cursor position.

        Returns:
            str: A JSON string with 'x' and 'y' coordinates of the cursor, e.g. {"x": 100, "y": 200}.
        """
        point: Coordinate = self._agent_os.get_mouse_position()
        return point.model_dump_json()
