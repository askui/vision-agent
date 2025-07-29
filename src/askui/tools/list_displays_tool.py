from askui.models.shared.tools import Tool
from askui.tools.agent_os import AgentOs


class ListDisplaysTool(Tool):
    def __init__(self, agent_os: AgentOs) -> None:
        super().__init__(
            name="list_displays",
            description="""
                List all the available displays.
            """,
        )
        self._agent_os: AgentOs = agent_os

    def __call__(self) -> str:
        return self._agent_os.list_displays().model_dump_json(
            exclude={"data": {"__all__": {"size"}}},
        )
