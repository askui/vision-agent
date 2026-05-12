from PIL import Image

from askui.models.shared import ComputerBaseTool, ToolTags
from askui.tools.computer_agent_os_facade import ComputerAgentOsFacade


class ComputerScreenshotTool(ComputerBaseTool):
    """Computer Screenshot Tool"""

    def __init__(self, agent_os: ComputerAgentOsFacade | None = None) -> None:
        super().__init__(
            name="screenshot",
            description=(
                "Take a screenshot of the current screen on the currently active "
                "Agent OS server. The accompanying message is prefixed with the "
                "active Agent OS server session GUID so it is clear which server "
                "the screenshot was taken on."
            ),
            agent_os=agent_os,
            required_tags=[ToolTags.SCALED_AGENT_OS.value],
        )
        self.is_cacheable = True

    def __call__(self) -> tuple[str, Image.Image]:
        server = self.agent_os.get_active_agent_os_server(report=False)
        screenshot = self.agent_os.screenshot()
        return (
            f"[Server with id '{server.computer_id}']: Screenshot was taken.",
            screenshot,
        )
