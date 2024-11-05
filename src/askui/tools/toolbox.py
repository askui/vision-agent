import webbrowser


class AgentToolbox:
    def __init__(self):
        self.webbrowser: webbrowser = webbrowser

    def list_tools(self):
        return self.__dict__
