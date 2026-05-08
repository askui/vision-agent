from askui.models.shared import ComputerBaseTool
from askui.tools.agent_os import AgentOs


class ComputerRetrieveActiveDisplayTool(ComputerBaseTool):
    def __init__(self, agent_os: AgentOs | None = None) -> None:
        super().__init__(
            name="retrieve_active_display",
            description="""
                Retrieve the currently active display on the currently active target
                computer. The display is used to take screenshots and perform
                actions. The result is prefixed with the active target computer
                session GUID so it is clear which target the display belongs to.
            """,
            agent_os=agent_os,
        )
        self.is_cacheable = True

    def __call__(self) -> str:
        target = self.agent_os.get_active_target_computer(report=False)
        display_json = self.agent_os.retrieve_active_display().model_dump_json(
            exclude={"size"}
        )
        return f"[target {target.session_guid}]: {display_json}"
