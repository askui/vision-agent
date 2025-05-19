import webbrowser

import httpx
import pyperclip

from askui.tools.agent_os import AgentOs
from askui.tools.askui.askui_hub import AskUIHub


class AgentToolbox:
    """
    Toolbox for agent.

    Provides access to OS-level actions, clipboard, web browser, HTTP client etc.

    Args:
        agent_os (AgentOs): The OS interface implementation to use for agent actions.

    Attributes:
        webbrowser: Python's built-in `webbrowser` module for opening URLs.
        clipboard: `pyperclip` module for clipboard access.
        agent_os (AgentOs): The OS interface for mouse, keyboard, and screen actions.
        httpx: HTTPX client for HTTP requests.
        hub (AskUIHub): Internal AskUI Hub instance.
    """

    def __init__(self, agent_os: AgentOs):
        self.webbrowser = webbrowser
        self.clipboard = pyperclip
        self.os = agent_os
        self._hub = AskUIHub()
        self.httpx = httpx

    @property
    def hub(self) -> AskUIHub:
        if self._hub.disabled:
            error_msg = (
                "AskUI Hub is disabled. Please, set ASKUI_WORKSPACE_ID and "
                "ASKUI_TOKEN environment variables to enable it."
            )
            raise ValueError(error_msg)
        return self._hub
