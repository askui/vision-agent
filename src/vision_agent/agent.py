from .tools.askui_controller import AskUiControllerClient, AskUiControllerServer


class VisionAgent:
    def __init__(self):
        self.controller = AskUiControllerServer()
        self.controller.start(True)
        self.client = AskUiControllerClient()
        self.client.connect()

    def click(self, instruction: str):
        self.client.mouse(10, 10)
        self.client.click("left")

    def type(text: str):
        raise NotImplementedError("type is not implemented yet")

    def get(instruction: str):
        raise NotImplementedError("get is not implemented yet")

    def act(goal: str):
        raise NotImplementedError("act is not implemented yet")

    def close(self):
        self.client.disconnect()
        self.controller.stop(True)
