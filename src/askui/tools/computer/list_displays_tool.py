from askui.models.shared import ComputerBaseTool
from askui.tools.agent_os import AgentOs


class ComputerListDisplaysTool(ComputerBaseTool):
    def __init__(self, agent_os: AgentOs | None = None) -> None:
        super().__init__(
            name="list_displays",
            description="""
                List all the available displays on the currently active target
                computer. The result is prefixed with the active target computer
                session GUID so it is clear which target the displays belong to.
            """,
            agent_os=agent_os,
        )
        self.is_cacheable = True

    def __call__(self) -> str:
        target = self.agent_os.get_active_target_computer()
        displays_json = self.agent_os.list_displays().model_dump_json(
            exclude={"data": {"__all__": {"size"}}},
        )
        return f"[target {target.session_guid}]: {displays_json}"
