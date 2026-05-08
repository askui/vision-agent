from askui.models.shared import ComputerBaseTool
from askui.tools.agent_os import AgentOs


class ComputerListTargetComputersTool(ComputerBaseTool):
    def __init__(self, agent_os: AgentOs | None = None) -> None:
        super().__init__(
            name="list_target_computers",
            description="""
                List all the registered target computers (controller servers)
                that the agent can connect to. Each target has a unique session
                GUID that can be used to switch between them.
            """,
            agent_os=agent_os,
        )

    def __call__(self) -> str:
        targets = self.agent_os.list_target_computers()
        return ",".join(repr(t) for t in targets)
