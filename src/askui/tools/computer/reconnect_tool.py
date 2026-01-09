from askui.models.shared import ComputerBaseTool
from askui.tools.computer_agent_os_facade import ComputerAgentOsFacade


class ComputerReconnectTool(ComputerBaseTool):
    """Computer Reconnect Tool"""

    def __init__(self, agent_os: ComputerAgentOsFacade | None = None) -> None:
        super().__init__(
            name="computer_reconnect",
            description=(
                "Reconnect to the agent OS controller. "
                "Useful when the controller crashes or is not connected. "
                "Starts a new controller instance and connects to the agent OS. "
                "Note: All previous configuration will be lost and must be "
                "reconfigured, e.g., selecting the right target display."
            ),
            agent_os=agent_os,
        )

    def __call__(self) -> str:
        try:
            self.agent_os.disconnect()
        finally:
            self.agent_os.connect()
            return "Agent OS controller was reconnected."  # noqa: B012
