from askui.models.shared import ComputerBaseTool
from askui.tools.agent_os import AgentOs


class ComputerListAgentOsServersTool(ComputerBaseTool):
    def __init__(self, agent_os: AgentOs | None = None) -> None:
        super().__init__(
            name="list_agent_os_servers",
            description="""
                List all the registered Agent OS servers that the agent can route
                actions to. Each server has a unique session GUID that can be used
                to switch between them.
            """,
            agent_os=agent_os,
        )

    def __call__(self) -> str:
        servers = self.agent_os.list_agent_os_servers()
        return ",".join(repr(s) for s in servers)
