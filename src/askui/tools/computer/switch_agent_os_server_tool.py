from askui.models.shared import ComputerBaseTool
from askui.tools.agent_os import AgentOs


class ComputerSwitchAgentOsServerTool(ComputerBaseTool):
    def __init__(self, agent_os: AgentOs | None = None) -> None:
        super().__init__(
            name="switch_agent_os_server",
            description="""
                Switch the active Agent OS server by its `computer_id`. Future
                agent-os actions are routed to the newly selected server. Use
                `list_agent_os_servers` to discover the available computer ids.
            """,
            input_schema={
                "type": "object",
                "properties": {
                    "computer_id": {
                        "type": "string",
                    },
                },
                "required": ["computer_id"],
            },
            agent_os=agent_os,
        )

    def __call__(self, computer_id: str) -> str:
        return repr(self.agent_os.switch_agent_os_server(computer_id))
