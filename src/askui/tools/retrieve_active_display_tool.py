from askui.models.shared.tools import Tool
from askui.tools.agent_os import AgentOs


class RetrieveActiveDisplayTool(Tool):
    def __init__(self, agent_os: AgentOs) -> None:
        super().__init__(
            name="retrieve_active_display",
            description="""
                Retrieve the currently active display/screen.
            """,
        )
        self._agent_os: AgentOs = agent_os

    def __call__(self) -> str:
        return str(
            self._agent_os.retrieve_active_display().model_dump_json(exclude={"size"})
        )
