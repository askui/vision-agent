from askui.models.shared import ComputerBaseTool
from askui.tools.agent_os import AgentOs


class ComputerGetActiveAgentOsServerTool(ComputerBaseTool):
    def __init__(self, agent_os: AgentOs | None = None) -> None:
        super().__init__(
            name="get_active_agent_os_server",
            description="""
                Return the currently active Agent OS server that agent-os actions
                are routed to.
            """,
            agent_os=agent_os,
        )
        self.is_cacheable = False

    def __call__(self) -> str:
        return repr(self.agent_os.get_active_agent_os_server())
