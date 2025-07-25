from askui.models.shared.tools import Tool
from askui.tools.agent_os import AgentOs, GetDisplayInformationResponse


class ListDisplayTool(Tool):
    """
    Tool to list all the available displays.
    """

    def __init__(self, agent_os: AgentOs) -> None:
        super().__init__(
            name="list_display",
            description="""
            This tool is useful for listing all the available displays.
            This is useful when the agent is not able to find the information on the current display.
            """,
        )
        self._agent_os: AgentOs = agent_os

    def __call__(self) -> GetDisplayInformationResponse:
        return self._agent_os.get_display_information()
