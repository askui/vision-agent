from askui.models.shared.tools import Tool
from askui.tools.agent_os import AgentOs


class ActiveDisplayTool(Tool):
    """
    Tool to get the active display id.
    """

    def __init__(self, agent_os: AgentOs) -> None:
        super().__init__(
            name="active_display",
            description="""
            This tool is useful for getting the active display id.
            """,
        )
        self._agent_os: AgentOs = agent_os

    def __call__(self) -> str:
        return str(self._agent_os.get_active_display())
