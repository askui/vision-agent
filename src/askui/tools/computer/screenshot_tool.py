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
                "target computer. The accompanying message is prefixed with the "
                "active target computer session GUID so it is clear which target "
                "the screenshot was taken on."
            ),
            agent_os=agent_os,
            required_tags=[ToolTags.SCALED_AGENT_OS.value],
        )
        self.is_cacheable = True

    def __call__(self) -> tuple[str, Image.Image]:
        target = self.agent_os.get_active_target_computer(report=False)
        screenshot = self.agent_os.screenshot()
        return f"[target {target.session_guid}]: Screenshot was taken.", screenshot
