import httpx
import pyperclip
import webbrowser
from askui.tools.agent_os import AgentOs
from askui.tools.askui.askui_hub import AskUIHub


class AgentToolbox:
    def __init__(self, agent_os: AgentOs):
        self.webbrowser = webbrowser
        self.clipboard: pyperclip = pyperclip
        self.agent_os = agent_os
        self._hub = AskUIHub()
        self.httpx = httpx
    
    @property
    def hub(self) -> AskUIHub:
        if self._hub.disabled:
            raise ValueError("AskUI Hub is disabled. Please, set ASKUI_WORKSPACE_ID and ASKUI_TOKEN environment variables to enable it.")
        return self._hub
