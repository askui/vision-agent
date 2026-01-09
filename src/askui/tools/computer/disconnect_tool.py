from askui.models.shared import ComputerBaseTool
from askui.tools.computer_agent_os_facade import ComputerAgentOsFacade


class ComputerDisconnectTool(ComputerBaseTool):
    """Computer Disconnect Tool"""

    def __init__(self, agent_os: ComputerAgentOsFacade | None = None) -> None:
        super().__init__(
            name="computer_disconnect",
            description=(
                "Disconnect from the agent OS controller. "
                "Needs to be used once you are done with the task and want to stop"
                " the agent OS controller from running. and clean up resources."
            ),
            agent_os=agent_os,
        )

    def __call__(self) -> str:
        self.agent_os.disconnect()
        return "Agent OS controller was disconnected."
