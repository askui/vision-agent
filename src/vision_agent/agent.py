from .tools.askui_controller import AskUiControllerClient, AskUiControllerServer


class VisionAgent:
    def __init__(self):
        controller = AskUiControllerServer()
        controller.start(True)
        client = AskUiControllerClient()
        client.connect()

    def click(self, instruction: str):
        self.client.mouse(10, 10)
        self.client.click("left")

    def type(text: str):
        pass
