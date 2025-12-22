from askui.models.shared.tools import Tool
from askui.tools.askui.askui_controller import AskUiControllerClient


class GetSystemInfoTool(Tool):
    """
    Get the system information.
    This tool returns the system information as a JSON object.
    The JSON object contains the following fields:
    - platform: The operating system platform.
    - label: The operating system label.
    - version: The operating system version.
    - architecture: The operating system architecture.
    """

    def __init__(self, agent_os: AskUiControllerClient):
        super().__init__(
            name="get_system_info",
            description="""
                Get the system information.
                This tool returns the system information as a JSON object.
                The JSON object contains the following fields:
                - platform: The operating system platform.
                - label: The operating system label.
                - version: The operating system version.
                - architecture: The operating system architecture.
            """,
        )
        self._agent_os: AskUiControllerClient = agent_os

    def __call__(self) -> str:
        return str(self._agent_os.get_system_info().model_dump_json())
