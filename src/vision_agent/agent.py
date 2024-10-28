import subprocess
from typing import Literal
from .tools.askui_controller import AskUiControllerClient, AskUiControllerServer
from .brains.claude import ClaudeHandler
from .brains.claude_agent import ClaudeComputerAgent


PC_KEY = Literal['backspace', 'delete', 'enter', 'tab', 'escape', 'up', 'down', 'right', 'left', 'home', 'end', 'pageup', 'pagedown', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', 'space', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~']


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

    def get(self, instruction: str):
        raise NotImplementedError("get is not implemented yet")

    def act(self, goal: str):
        agent = ClaudeComputerAgent(self.client)
        agent.run(goal)
    
    def keyboard(self, key: PC_KEY):
        self.client.keyboard_pressed(key)
        self.client.keyboard_release(key)
    
    def cli(self, command: str):
        subprocess.run(command.split(" "))

    def close(self):
        self.client.disconnect()
        self.controller.stop(True)
