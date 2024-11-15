import pyperclip
import webbrowser
from askui.tools.askui.askui_controller import AskUiControllerClient


class AgentToolbox:
    def __init__(self, os_controller):
        self.webbrowser: webbrowser = webbrowser
        self.clipboard: pyperclip = pyperclip
        self.os: AskUiControllerClient = os_controller

    def list_tools(self):
        return self.__dict__
