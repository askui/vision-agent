from askui.models.askui.askui_computer_base_tool import AskUiComputerBaseTool
from askui.tools.askui.askui_controller import AskUiControllerClient


class ComputerGetSystemInfoTool(AskUiComputerBaseTool):
    """
    Get the system information.
    This tool returns the system information as a JSON object.
    The JSON object contains the following fields:
    - platform: The operating system platform.
    - label: The operating system label.
    - version: The operating system version.
    - architecture: The operating system architecture.
    """

    def __init__(self, agent_os: AskUiControllerClient | None = None) -> None:
        super().__init__(
            name="computer_get_system_info_tool",
            description="""
                Get the system information.
                This tool returns the system information as a JSON object.
                The JSON object contains the following fields:
                - platform: The operating system platform.
                - label: The operating system label.
                - version: The operating system version.
                - architecture: The operating system architecture.
            """,
            agent_os=agent_os,
        )

    def __call__(self) -> str:
        return str(self.agent_os.get_system_info().model_dump_json())
