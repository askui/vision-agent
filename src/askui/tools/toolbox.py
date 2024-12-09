import pyperclip
import webbrowser
from askui.tools.askui.askui_controller import AskUiControllerClient
from askui.tools.askui.hub import Hub


class AgentToolbox:
    def __init__(self, os_controller: AskUiControllerClient, hub: Hub | None = None):
        self.webbrowser: webbrowser = webbrowser
        self.clipboard: pyperclip = pyperclip
        self.os: AskUiControllerClient = os_controller
        self._hub = hub

    def list_tools(self):
        return self.__dict__
    
    @property
    def hub(self) -> Hub:
        if self._hub is None:
            raise ValueError("Hub is not initialized. Please, provide a `chat_model` when initializing the `VisionAgent`.")
        return self._hub
