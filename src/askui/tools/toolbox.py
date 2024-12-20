import httpx
import pyperclip
import webbrowser
from askui.tools.askui.askui_controller import AskUiControllerClient
from askui.tools.askui.askui_hub import AskUIHub


class AgentToolbox:
    def __init__(self, os_controller: AskUiControllerClient | None = None):
        self.webbrowser = webbrowser
        self.clipboard: pyperclip = pyperclip
        self._os = os_controller
        self._hub = AskUIHub()
        self.httpx = httpx
    
    @property
    def hub(self) -> AskUIHub:
        if self._hub.disabled:
            raise ValueError("AskUI Hub is disabled. Please, set ASKUI_WORKSPACE_ID and ASKUI_TOKEN environment variables to enable it.")
        return self._hub
    
    @property
    def os(self) -> AskUiControllerClient:
        if self._os is None:
            raise ValueError("OS controller is not initialized. Please, provide a `os_controller` when initializing the `AgentToolbox`.")
        return self._os
