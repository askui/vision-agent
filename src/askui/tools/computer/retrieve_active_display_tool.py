from askui.models.shared import ComputerBaseTool
from askui.tools.agent_os import AgentOs


class ComputerRetrieveActiveDisplayTool(ComputerBaseTool):
    def __init__(self, agent_os: AgentOs | None = None) -> None:
        super().__init__(
            name="retrieve_active_display",
            description="""
                Retrieve the currently active display on the currently active Agent OS
                server. The display is used to take screenshots and perform actions.
                The result is prefixed with the active Agent OS server session GUID
                so it is clear which server the display belongs to.
            """,
            agent_os=agent_os,
        )
        self.is_cacheable = True

    def __call__(self) -> str:
        server = self.agent_os.get_active_agent_os_server(report=False)
        display_json = self.agent_os.retrieve_active_display().model_dump_json(
            exclude={"size"}
        )
        return f"[Server with id '{server.computer_id}']: {display_json}"
