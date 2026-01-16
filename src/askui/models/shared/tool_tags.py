from enum import Enum


class ToolTags(str, Enum):
    """Default tool tags."""

    ANDROID = "android"
    ASKUI_CONTROLLER = "askui_controller"
    COMPUTER = "computer"
    SCALED_AGENT_OS = "scaled_agent_os"
