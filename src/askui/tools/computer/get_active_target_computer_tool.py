from askui.models.shared import ComputerBaseTool
from askui.tools.agent_os import AgentOs


class ComputerGetActiveTargetComputerTool(ComputerBaseTool):
    def __init__(self, agent_os: AgentOs | None = None) -> None:
        super().__init__(
            name="get_active_target_computer",
            description="""
                Return the currently active target computer (controller server)
                that agent-os actions are routed to.
            """,
            agent_os=agent_os,
        )
        self.is_cacheable = False

    def __call__(self) -> str:
        return repr(self.agent_os.get_active_target_computer())
