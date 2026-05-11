from askui.models.shared import ComputerBaseTool
from askui.tools.agent_os import AgentOs


class ComputerGetSystemInfoTool(ComputerBaseTool):
    """
    Get the system information of the currently active Agent OS server.
    This tool returns the system information as a JSON object prefixed with
    the active Agent OS server session GUID.
    The JSON object contains the following fields:
    - platform: The operating system platform.
    - label: The operating system label.
    - version: The operating system version.
    - architecture: The operating system architecture.
    """

    def __init__(self, agent_os: AgentOs | None = None) -> None:
        super().__init__(
            name="get_system_info_tool",
            description="""
                Get the system information of the currently active Agent OS server.
                This tool returns the system information as a JSON object prefixed
                with the active Agent OS server session GUID so it is clear which
                server the info belongs to.
                The JSON object contains the following fields:
                - platform: The operating system platform.
                - label: The operating system label.
                - version: The operating system version.
                - architecture: The operating system architecture.
            """,
            agent_os=agent_os,
        )

    def __call__(self) -> str:
        server = self.agent_os.get_active_agent_os_server(report=False)
        system_info_json = self.agent_os.get_system_info().model_dump_json()
        return f"[server {server.session_guid}]: {system_info_json}"
