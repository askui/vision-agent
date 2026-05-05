import time
from typing import get_args

from askui.models.shared import ComputerBaseTool
from askui.tools.agent_os import AgentOs, MouseButton


class ComputerMousePressHoldReleaseTool(ComputerBaseTool):
    """Computer Mouse Press Hold Release Tool"""

    def __init__(self, agent_os: AgentOs | None = None) -> None:
        super().__init__(
            name="mouse_press_hold_release",
            description=(
                "Press down the mouse button at the current position and hold"
                " it down for the specified time, then release it."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "mouse_button": {
                        "type": "string",
                        "description": "The mouse button to hold down.",
                        "enum": get_args(MouseButton),
                    },
                    "hold_time": {
                        "type": "integer",
                        "description": (
                            "The number of seconds the button is pressed."
                            " Must be an integer, e.g. 5 for 5 seconds."
                        ),
                    },
                },
                "required": ["mouse_button", "hold_time"],
            },
            agent_os=agent_os,
        )
        self.is_cacheable = True

    def __call__(self, mouse_button: MouseButton, hold_time: int) -> str:
        self.agent_os.mouse_down(mouse_button)
        time.sleep(hold_time)
        self.agent_os.mouse_up(mouse_button)
        return f"Mouse button {mouse_button} was pressed for {hold_time} seconds."
