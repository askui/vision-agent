from .tools.askui_controller import AskUiControllerClient, AskUiControllerServer
from .brains.claude import ClaudeHandler


class VisionAgent:
    def __init__(self):
        self.controller = AskUiControllerServer()
        self.controller.start(True)
        self.client = AskUiControllerClient()
        self.client.connect()
        self.claude = ClaudeHandler()

    def click(self, instruction: str):
        screenshot = self.client.screenshot()
        x, y = self.claude.click_inference(screenshot, instruction)
        self.client.mouse(x, y)
        self.client.click("left")

    def type(self, text: str):
        self.client.type(text)

    def get(instruction: str):
        raise NotImplementedError("get is not implemented yet")

    def act(goal: str):
        raise NotImplementedError("act is not implemented yet")

    def close(self):
        self.client.disconnect()
        self.controller.stop(True)
