import base64
import httpx
import pyperclip
import webbrowser
from askui.tools.askui.askui_controller import AskUiControllerClient
from askui.tools.askui.extractor import Extractor
from askui.tools.askui.files import AskUiFilesService
from askui.tools.askui.hub import Hub
from askui.tools.askui.hub import HubSettings


class AgentToolbox:
    def __init__(self, hub_settings: HubSettings, os_controller: AskUiControllerClient | None = None, extractor: Extractor | None = None):
        self.webbrowser = webbrowser
        self.clipboard: pyperclip = pyperclip
        self._os = os_controller
        self._extractor = extractor
        self.files = AskUiFilesService(
            base_url=f"{hub_settings.host}/api/v1/files",
            headers={"Authorization": f"Basic {base64.b64encode(hub_settings.access_token.encode()).decode()}"}
        )
        self.hub = Hub(settings=hub_settings)
        self.httpx = httpx


    def list_tools(self):
        return self.__dict__
    
    @property
    def extractor(self) -> Extractor:
        if self._extractor is None:
            raise ValueError("Extractor is not initialized. Please, provide a `chat_model` when initializing the `VisionAgent`.")
        return self._extractor
    
    @property
    def os(self) -> AskUiControllerClient:
        if self._os is None:
            raise ValueError("OS controller is not initialized. Please, provide a `os_controller` when initializing the `VisionAgent`.")
        return self._os
