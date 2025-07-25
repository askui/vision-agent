from askui.models.shared.tools import Tool
from askui.tools.agent_os import AgentOs


class SetDisplayTool(Tool):
    """
    Tool to set the display.
    """

    def __init__(self, agent_os: AgentOs) -> None:
        super().__init__(
            name="set_display",
            description="""
            This tool is useful for setting the default display screen.
            This is useful when the agent is not able to find the information on the current display.
            """,
        )
        self._agent_os: AgentOs = agent_os

    def __call__(self, display_id: int) -> None:
        self._agent_os.set_display(display_id)
