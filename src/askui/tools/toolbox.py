import pyperclip
import webbrowser


class AgentToolbox:
    def __init__(self):
        self.webbrowser: webbrowser = webbrowser
        self.clipboard: pyperclip = pyperclip

    def list_tools(self):
        return self.__dict__
